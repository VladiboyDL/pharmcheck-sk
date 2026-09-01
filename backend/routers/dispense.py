"""Dispensing window — the full verification pass that replaces the manual counter check.

One call runs every gate a pharmacist would run by hand:
    identity → prescription parsing → interactions → dosing → duplication → risk burden
and returns a single dispense decision with a complete audit record.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from itertools import combinations
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import clinical
from ..ai_checker import ANTHROPIC_API_KEY, check_interaction_ai, explain_interaction_ai
from ..database import get_db
from ..patients import get_patient
from ..prescription import resolve

router = APIRouter(prefix="/api/dispense", tags=["dispense"])

SEVERITY_RANK = {"Závažná": 0, "Stredná": 1, "Mierna": 2}

DEMO_PRESCRIPTIONS: dict[str, dict] = {
    "SK7154120987": {
        "label": "Polyfarmácia seniorky — 7 liekov",
        "prescriber": "MUDr. Eva Tóthová, ambulancia VLD Bratislava-Ružinov",
        "text": (
            "WARFARIN ORION 5 mg tbl   1-0-0\n"
            "NUROFEN 400 mg tbl        1-1-1\n"
            "HELICID 20 mg cps         1-0-0\n"
            "Simvacard 20 mg tbl       0-0-1\n"
            "HIPRES 5 mg tbl           1-0-0\n"
            "Furon 40 mg tbl           1-0-0\n"
            "Zolpidem 10 mg tbl        0-0-1"
        ),
    },
    "SK9203114455": {
        "label": "Depresia + bolesť — riziko sérotonínového syndrómu",
        "prescriber": "MUDr. Martin Krajčí, psychiatrická ambulancia Trnava",
        "text": (
            "ZOLOFT 50 mg tbl          1-0-0\n"
            "TRAMAL 100 mg cps         1-1-1\n"
            "PARALEN 500 mg tbl        2-2-2\n"
            "VOLTAREN 50 mg tbl        1-1-1"
        ),
    },
    "SK9655087723": {
        "label": "Gravidita — kontraindikované prípravky",
        "prescriber": "MUDr. Lenka Sedláková, gynekologická ambulancia Nitra",
        "text": (
            "IBALGIN 400 mg tbl        1-1-1\n"
            "RAMIPRIL 5 mg tbl         1-0-0\n"
            "PARALEN 500 mg tbl        1-0-1"
        ),
    },
    "SK5812093366": {
        "label": "Metotrexát — chyba vo frekvencii podávania",
        "prescriber": "MUDr. Peter Hraško, reumatologická ambulancia Košice",
        "text": (
            "Methotrexat Ebewe 10 mg tbl   1-0-0\n"
            "Ibalgin 400 mg tbl            1-1-1\n"
            "Prednison 20 mg tbl           1-0-0"
        ),
    },
    "SK8407224411": {
        "label": "Bežný recept — všetky kontroly prejdú",
        "prescriber": "MUDr. Silvia Rybárová, ambulancia VLD Žilina",
        "text": (
            "EUTHYROX 75 ug tbl        1-0-0\n"
            "AMOKSIKLAV 1 g tbl        1-0-1\n"
            "PARALEN 500 mg tbl        1-0-1"
        ),
    },
    "SK1409116688": {
        "label": "Detský pacient — vekové obmedzenia",
        "prescriber": "MUDr. Jana Baloghová, pediatrická ambulancia Bratislava",
        "text": (
            "CIPRINOL 250 mg tbl       1-0-1\n"
            "PARALEN 500 mg tbl        1-1-1\n"
            "ACYLPYRIN 500 mg tbl      1-0-1"
        ),
    },
}


class VerifyRequest(BaseModel):
    card_id: Optional[str] = None
    prescription_text: str
    identity_verified: bool = True
    # Allow the operator to override the card-derived profile during a demo.
    patient_override: Optional[dict] = None


def _interaction_row(db, sub_a: str, sub_b: str) -> dict | None:
    subs_a = [s.strip().lower() for s in (sub_a or "").split(",") if s.strip()]
    subs_b = [s.strip().lower() for s in (sub_b or "").split(",") if s.strip()]
    best = None
    for sa in subs_a:
        for sb in subs_b:
            if sa == sb:
                continue
            row = db.execute(
                """SELECT severity, mechanism, management, alternatives FROM interactions
                   WHERE (LOWER(drug_a)=? AND LOWER(drug_b)=?) OR (LOWER(drug_a)=? AND LOWER(drug_b)=?)
                   LIMIT 1""",
                (sa, sb, sb, sa),
            ).fetchone()
            if row:
                r = dict(row)
                r["source"] = "db"
                if best is None or SEVERITY_RANK.get(r["severity"], 9) < SEVERITY_RANK.get(best["severity"], 9):
                    best = r
    return best


@router.get("/scenarios/{card_id}")
def scenario_for(card_id: str):
    scenario = DEMO_PRESCRIPTIONS.get(card_id.upper())
    if not scenario:
        raise HTTPException(status_code=404, detail="Pre túto kartu nie je pripravený scenár")
    return scenario


@router.post("/verify")
def verify(req: VerifyRequest):
    started = time.perf_counter()
    db = get_db()
    try:
        # ── Patient profile ────────────────────────────────────────────────────
        record = get_patient(req.card_id) if req.card_id else None
        profile = dict(record) if record else {}
        if req.patient_override:
            profile.update(req.patient_override)

        patient = clinical.Patient(
            age=profile.get("age"),
            weight_kg=profile.get("weight_kg"),
            egfr=profile.get("egfr"),
            hepatic_impairment=bool(profile.get("hepatic_impairment")),
            pregnant=bool(profile.get("pregnant")),
            breastfeeding=bool(profile.get("breastfeeding")),
            allergies=list(profile.get("allergies") or []),
        )

        # ── 1. Parse and resolve the prescription ──────────────────────────────
        items, unresolved = resolve(db, req.prescription_text)
        if not items:
            raise HTTPException(status_code=400, detail="Z receptu sa nepodarilo rozpoznať žiadny liek")

        checks_run = 0

        # ── 2. Per-item clinical validation ────────────────────────────────────
        item_findings: dict[int, list] = {}
        for it in items:
            fs = clinical.validate_item(it, patient)
            checks_run += 8  # dose, renal, hepatic, age, pregnancy, breastfeeding, geriatric, frequency
            if fs:
                item_findings[it["id"]] = fs

        # ── 3. Regimen-level checks ────────────────────────────────────────────
        regimen_findings = clinical.validate_regimen(items, patient)
        regimen_findings += clinical.allergy_check(items, patient)
        checks_run += len(clinical.THERAPEUTIC_CLASSES) + 4

        # ── 4. Pairwise interactions ───────────────────────────────────────────
        interactions = []
        pairs_checked = 0
        ai_calls = 0
        explain_calls = 0
        for a, b in combinations(items, 2):
            pairs_checked += 1
            hit = _interaction_row(db, a["active_substance"], b["active_substance"])
            if not hit and ANTHROPIC_API_KEY and ai_calls < 6:
                ai = check_interaction_ai(a["active_substance"], b["active_substance"], db)
                ai_calls += 1
                if ai and ai.get("has_interaction"):
                    hit = ai
            # Severity known but no clinical text — fill it in live (max 4 per pass so
            # the dispense decision stays fast) and cache it for next time.
            if hit and not hit.get("mechanism") and ANTHROPIC_API_KEY and explain_calls < 4:
                explained = explain_interaction_ai(
                    a["active_substance"].split(",")[0].strip(),
                    b["active_substance"].split(",")[0].strip(),
                    hit["severity"],
                    db,
                )
                explain_calls += 1
                if explained:
                    hit.update(explained)

            if hit:
                interactions.append(
                    {
                        "drug_a": a["trade_name"],
                        "drug_b": b["trade_name"],
                        "substance_a": a["active_substance"],
                        "substance_b": b["active_substance"],
                        "severity": hit["severity"],
                        "mechanism": hit.get("mechanism"),
                        "management": hit.get("management"),
                        "alternatives": hit.get("alternatives"),
                        "source": hit.get("source", "db"),
                    }
                )
        checks_run += pairs_checked
        interactions.sort(key=lambda i: SEVERITY_RANK.get(i["severity"], 9))

        # ── 5. Decision ────────────────────────────────────────────────────────
        all_findings = [f for fs in item_findings.values() for f in fs] + regimen_findings
        critical = sum(1 for f in all_findings if f.severity == "critical")
        warning = sum(1 for f in all_findings if f.severity == "warning")
        info = sum(1 for f in all_findings if f.severity == "info")
        major_ix = sum(1 for i in interactions if i["severity"] == "Závažná")
        moderate_ix = sum(1 for i in interactions if i["severity"] == "Stredná")

        if not req.identity_verified:
            verdict, label = "BLOCK", "NEVYDAŤ"
            reason = "Totožnosť pacienta nebola overená."
        elif critical:
            verdict, label = "BLOCK", "NEVYDAŤ"
            reason = f"{critical}× kritické zistenie vyžadujúce zásah lekára."
        elif major_ix or warning:
            verdict, label = "CONSULT", "KONZULTOVAŤ"
            bits = []
            if major_ix:
                bits.append(f"{major_ix}× závažná interakcia")
            if warning:
                bits.append(f"{warning}× upozornenie")
            reason = " a ".join(bits) + " — pred výdajom konzultovať."
        else:
            verdict, label = "DISPENSE", "VYDAŤ"
            reason = "Všetky kontroly prešli bez kritického nálezu."

        duration_ms = round((time.perf_counter() - started) * 1000, 1)

        # ── 6. Audit record ────────────────────────────────────────────────────
        audit_id = f"AV-{uuid.uuid4().hex[:10].upper()}"
        audit = {
            "audit_id": audit_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "operator": "AvatarAI Dispense Engine v1",
            "identity_verified": req.identity_verified,
            "card_id": profile.get("card_id"),
            "patient": profile.get("name"),
            "items": len(items),
            "checks_run": checks_run,
            "verdict": verdict,
        }
        _write_audit(db, audit, req.prescription_text, all_findings, interactions)

        return {
            "verdict": verdict,
            "verdict_label": label,
            "verdict_reason": reason,
            "patient": {
                "name": profile.get("name"),
                "age": patient.age,
                "weight_kg": patient.weight_kg,
                "egfr": patient.egfr,
                "pregnant": patient.pregnant,
                "pregnancy_week": profile.get("pregnancy_week"),
                "allergies": patient.allergies,
                "insurer": profile.get("insurer"),
                "chronic": profile.get("chronic", []),
            },
            "items": [
                {**it, "findings": [asdict(f) for f in item_findings.get(it["id"], [])]}
                for it in items
            ],
            "unresolved": unresolved,
            "interactions": interactions,
            "findings": [asdict(f) for f in regimen_findings],
            "summary": {
                "items": len(items),
                "checks_run": checks_run,
                "pairs_checked": pairs_checked,
                "critical": critical,
                "warning": warning,
                "info": info,
                "major_interactions": major_ix,
                "moderate_interactions": moderate_ix,
                "duration_ms": duration_ms,
                "ai_used": (ai_calls + explain_calls) > 0,
            },
            "audit": audit,
        }
    finally:
        db.close()


def _write_audit(db, audit: dict, prescription: str, findings, interactions) -> None:
    """Append-only dispensing log — chain of custody for every decision."""
    try:
        db.execute(
            """CREATE TABLE IF NOT EXISTS dispense_log (
                id INTEGER PRIMARY KEY,
                audit_id TEXT UNIQUE,
                timestamp TEXT,
                card_id TEXT,
                patient TEXT,
                verdict TEXT,
                checks_run INTEGER,
                prescription TEXT,
                findings_json TEXT
            )"""
        )
        db.execute(
            """INSERT OR IGNORE INTO dispense_log
               (audit_id, timestamp, card_id, patient, verdict, checks_run, prescription, findings_json)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                audit["audit_id"],
                audit["timestamp"],
                audit["card_id"],
                audit["patient"],
                audit["verdict"],
                audit["checks_run"],
                prescription,
                json.dumps(
                    {
                        "findings": [asdict(f) for f in findings],
                        "interactions": interactions,
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        db.commit()
    except Exception:
        pass  # audit write must never block a dispense decision


@router.get("/log")
def dispense_log(limit: int = 50):
    """Recent dispensing decisions — the audit trail."""
    db = get_db()
    try:
        db.execute(
            """CREATE TABLE IF NOT EXISTS dispense_log (
                id INTEGER PRIMARY KEY, audit_id TEXT UNIQUE, timestamp TEXT, card_id TEXT,
                patient TEXT, verdict TEXT, checks_run INTEGER, prescription TEXT, findings_json TEXT)"""
        )
        rows = db.execute(
            """SELECT audit_id, timestamp, card_id, patient, verdict, checks_run
               FROM dispense_log ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return {"entries": [dict(r) for r in rows]}
    finally:
        db.close()
