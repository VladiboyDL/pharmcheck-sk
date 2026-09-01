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
from ..ai_checker import ANTHROPIC_API_KEY, check_interaction_ai
from .. import intake, resolver, substances
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
    # Ask Claude about pairs DDInter does not know. Off by default — adds seconds.
    deep_ai: bool = False
    # Interview answers: {question_id: [option_id, ...]}
    intake: Optional[dict] = None
    # Allow the operator to override the card-derived profile during a demo.
    patient_override: Optional[dict] = None


def _interaction_row(db, sub_a: str, sub_b: str) -> tuple[dict | None, str, list[str]]:
    """Look up one pair, normalising registry salt names onto interaction-data names.

    Returns (interaction, coverage, unknown_substances). Coverage is "checked" when
    both substances exist in the interaction data — only then does the absence of a
    row mean anything. Otherwise it is "unverified" and must never read as safe.
    """
    resolved_a, unknown = [], []
    for component in substances.split_components(sub_a):
        name, status = substances.resolve(db, component)
        (resolved_a.append(name) if name else unknown.append(component))
    resolved_b = []
    for component in substances.split_components(sub_b):
        name, status = substances.resolve(db, component)
        (resolved_b.append(name) if name else unknown.append(component))

    if not resolved_a or not resolved_b:
        return None, "unverified", unknown

    best = None
    for sa in resolved_a:
        for sb in resolved_b:
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
                r["resolved_a"], r["resolved_b"] = sa, sb
                if best is None or SEVERITY_RANK.get(r["severity"], 9) < SEVERITY_RANK.get(best["severity"], 9):
                    best = r

    # A pair is only "checked" when every component resolved; a partial resolution
    # still leaves an unchecked component.
    coverage = "checked" if not unknown else "unverified"
    return best, coverage, unknown


@router.get("/scenarios/{card_id}")
def scenario_for(card_id: str):
    scenario = DEMO_PRESCRIPTIONS.get(card_id.upper())
    if not scenario:
        raise HTTPException(status_code=404, detail="Pre túto kartu nie je pripravený scenár")
    return scenario


@router.get("/intake")
def intake_questions(card_id: str | None = None):
    """The interview shown before evaluation.

    A prescription only describes what a prescriber knew about. Most harm at the
    counter comes from what is missing from it — OTC analgesics, herbal supplements,
    a second prescriber's script — so we ask before we judge.
    """
    return {"questions": intake.questions_for(get_patient(card_id) if card_id else None)}


def _item_status(item, own_findings, regimen_findings, interactions) -> tuple[str, list[str]]:
    """What the counter actually does with this item.

        dispense  hand it over, nothing to say
        counsel   hand it over and say something — the common case, including
                  interactions, which a pharmacy does not refuse a script over
        verify    telephone the prescriber first: suspected prescribing error or an
                  absolute contraindication, not merely a managed risk
        decline   only for self-medication, the one thing a pharmacy may refuse to sell

    A pharmacy has no standing to overrule a valid prescription. Getting this wrong
    is not a UX detail — it is the difference between a tool a pharmacist trusts and
    one they switch off.
    """
    name = item["trade_name"]
    from_interview = item.get("source") == "interview"
    reasons: list[str] = []
    status = "dispense"

    def raise_to(level: str, reason: str) -> None:
        nonlocal status
        reasons.append(reason)
        if _rank(level) > _rank(status):
            status = level

    for f in own_findings:
        if f.code in clinical.VERIFY_BEFORE_DISPENSING and f.severity == "critical":
            raise_to("decline" if from_interview else "verify", f.title)
        elif f.severity in ("critical", "warning"):
            raise_to("decline" if from_interview and f.severity == "critical" else "counsel", f.title)

    for f in regimen_findings:
        if name not in (f.drugs or []):
            continue
        if f.code in clinical.VERIFY_BEFORE_DISPENSING and f.severity == "critical":
            raise_to("decline" if from_interview else "verify", f.title)
        elif f.severity == "critical":
            # Self-medication is the piece the counter can act on; the prescription goes out.
            raise_to("decline" if from_interview else "counsel", f.title)
        elif f.severity == "warning":
            raise_to("counsel", f.title)

    for ix in interactions:
        if name not in (ix["drug_a"], ix["drug_b"]):
            continue
        other = ix["drug_b"] if ix["drug_a"] == name else ix["drug_a"]
        if ix["severity"] == "Závažná":
            raise_to("decline" if from_interview else "counsel", f"Závažná interakcia s {other}")
        elif ix["severity"] == "Stredná":
            raise_to("counsel", f"Stredná interakcia s {other}")

    return status, reasons


def _rank(status: str) -> int:
    return {"dispense": 0, "counsel": 1, "decline": 2, "verify": 3}.get(status, 0)


def _next_steps(items, item_findings, regimen_findings, interactions, patient_name) -> list[dict]:
    """What the counter does, in the order it does it."""
    steps: list[dict] = []

    rx = [i for i in items if i.get("source") != "interview"]
    verify = [i for i in rx if i["status"] == "verify"]
    counsel = [i for i in rx if i["status"] == "counsel"]
    declined = [i for i in items if i["status"] == "decline"]
    goes_out = [i for i in rx if i["status"] != "verify"]

    if goes_out:
        steps.append(
            {
                "kind": "dispense",
                "title": f"Vydať {len(goes_out)} z {len(rx)} položiek receptu",
                "detail": ", ".join(i["trade_name"] for i in goes_out)
                + ". Recept je platný a vydáva sa — nálezy nižšie sú na poučenie, nie dôvod na odmietnutie.",
                "drugs": [i["trade_name"] for i in goes_out],
            }
        )

    if counsel:
        steps.append(
            {
                "kind": "counsel",
                "title": f"Poučiť pacienta pri výdaji ({len(counsel)})",
                "detail": "Systém pripravil, čo presne povedať. Zaberie to pol minúty pri okienku.",
                "drugs": [i["trade_name"] for i in counsel],
                "script": _counselling_script(counsel, item_findings, regimen_findings, interactions),
            }
        )

    for item in declined:
        steps.append(
            {
                "kind": "decline",
                "title": f"Neodporúčať {item['trade_name']}",
                "detail": "Voľnopredajný prípravok, ktorý si pacient kupuje sám. Tu má lekáreň "
                          "priestor odhovoriť a ponúknuť bezpečnejšiu možnosť.",
                "drugs": [item["trade_name"]],
            }
        )

    if verify:
        steps.append(
            {
                "kind": "verify",
                "title": f"Pred výdajom overiť u lekára ({len(verify)})",
                "detail": "Nejde o interakciu, ale o podozrenie na chybu v predpise alebo absolútnu "
                          "kontraindikáciu. Tieto položky sa vydajú až po telefonáte.",
                "drugs": [i["trade_name"] for i in verify],
                "message": _prescriber_message(verify, item_findings, regimen_findings, interactions, patient_name),
            }
        )

    if not counsel and not verify and not declined:
        steps.append(
            {
                "kind": "advise",
                "title": "Vydať bez ďalšieho",
                "detail": "Žiadny nález. Pripomenúť dodržanie dávkovania a kedy sa vrátiť.",
                "drugs": [],
            }
        )

    return steps


def _counselling_script(items, item_findings, regimen_findings, interactions) -> list[dict]:
    """The sentences a pharmacist actually says, written out.

    The pharmacist we asked dispenses everything and counsels — so the useful output
    is not a verdict, it is the question to ask and the sentence to close with.
    """
    script: list[dict] = []
    seen: set[str] = set()

    for ix in interactions:
        if ix["severity"] not in ("Závažná", "Stredná"):
            continue
        key = f"{ix['drug_a']}+{ix['drug_b']}"
        if key in seen:
            continue
        seen.add(key)
        script.append(
            {
                "topic": f"{ix['drug_a']} + {ix['drug_b']}",
                "ask": f"Vie váš lekár, že užívate {ix['drug_a']} aj {ix['drug_b']} súčasne?",
                "patient": "Tieto dva lieky sa navzájom ovplyvňujú. Preberte to prosím "
                           "pri najbližšej návšteve u lekára.",
                "say": ix.get("management") or "",
                "severity": ix["severity"],
            }
        )

    for item in items:
        for f in item_findings.get(item["key"], []):
            if f.severity == "info" or f.title in seen:
                continue
            seen.add(f.title)
            script.append(
                {
                    "topic": item["trade_name"],
                    "ask": _ask_for(f, item["trade_name"]),
                    "patient": f.detail,
                    "say": f.action or "",
                    "severity": "Upozornenie",
                }
            )

    for f in regimen_findings:
        if f.severity == "info" or f.title in seen:
            continue
        seen.add(f.title)
        script.append(
            {
                "topic": ", ".join(f.drugs) if f.drugs else "Celá medikácia",
                "ask": _ask_for(f, ", ".join(f.drugs)),
                "patient": f.detail,
                "say": f.action or "",
                "severity": "Upozornenie",
            }
        )

    # Twenty-one things to say is nothing said. Rank by clinical weight so the top of
    # the list is what actually gets spoken at the window.
    weight = {"Závažná": 0, "Upozornenie": 1, "Stredná": 2}
    script.sort(key=lambda line: weight.get(line.get("severity"), 3))
    return script


def _ask_for(finding, subject: str) -> str:
    """The opening question, phrased for the specific kind of finding."""
    by_code = {
        "GERIATRIC": f"Ako {subject} znášate? Nemávate závraty alebo pocit neistoty pri chôdzi?",
        "FALL_RISK": "Nestalo sa vám v poslednom čase, že by ste zakopli alebo spadli?",
        "BLEEDING_BURDEN": "Nevšimli ste si, že sa vám ľahšie robia modriny alebo dlhšie krváca ranka?",
        "SEROTONIN_BURDEN": "Nemávate nepokoj, tras alebo nadmerné potenie?",
        "DUPLICATE": f"Viete o tom, že {subject} obsahujú podobnú účinnú látku?",
        "RENAL_REDUCE": "Kedy ste mali naposledy kontrolu obličiek?",
        "RENAL_CAUTION": "Kedy ste mali naposledy kontrolu obličiek?",
        "NEAR_MAX_DOSE": f"Beriete {subject} presne podľa predpisu, alebo si niekedy pridáte?",
        "POLYPHARMACY": "Máte prehľad o všetkých liekoch, ktoré užívate?",
        "QT": "Nemávate búšenie srdca alebo pocit na odpadnutie?",
        "UNVERIFIED": "Užívate okrem toho ešte niečo, o čom sme sa nebavili?",
    }
    return by_code.get(finding.code, f"Vie váš lekár o tom, že užívate {subject}?")


def _prescriber_message(problem_items, item_findings, regimen_findings, interactions, patient_name) -> str:
    """A ready-to-read note for the phone call, so nobody has to compose one."""
    lines = [
        f"Dobrý deň, volám z lekárne ohľadom pacienta {patient_name or '—'}.",
        "Pri kontrole receptu systém označil nasledujúce:",
    ]
    seen: set[str] = set()

    for item in problem_items:
        for f in item_findings.get(item["key"], []):
            if f.severity in ("critical", "warning") and f.title not in seen:
                seen.add(f.title)
                lines.append(f"- {f.title}. {f.detail}")

    for f in regimen_findings:
        if f.severity == "critical" and f.title not in seen:
            seen.add(f.title)
            lines.append(f"- {f.title}. {f.detail}")

    for ix in interactions:
        if ix["severity"] != "Závažná":
            continue
        key = f"{ix['drug_a']}+{ix['drug_b']}"
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- Závažná interakcia {ix['drug_a']} + {ix['drug_b']}. {ix.get('mechanism') or ''}".strip())

    lines.append("Ako mám postupovať s výdajom?")
    return "\n".join(lines)


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

        # ── 1. Prescription ────────────────────────────────────────────────────
        items, unresolved = resolve(db, req.prescription_text)
        if not items:
            raise HTTPException(status_code=400, detail="Z receptu sa nepodarilo rozpoznať žiadny liek")
        for n, it in enumerate(items):
            it["key"] = f"rx-{n}"
            it["source"] = "prescription"

        # ── 2. Interview — what the prescription does not say ──────────────────
        extra, intake_notes = intake.resolve_answers(req.intake or {})
        for n, sub in enumerate(extra):
            items.append(
                {
                    **sub,
                    "key": f"iv-{n}",
                    "id": None,
                    "atc_code": None,
                    "raw_line": f"z rozhovoru: {sub['trade_name']}",
                    "strength_mg": None,
                    "units_per_day": None,
                    "frequency_per_day": None,
                    "weekly": False,
                    "daily_dose_mg": None,
                    "weekly_dose_mg": None,
                }
            )

        checks_run = len(intake.QUESTIONS)

        # ── 3. Per-item clinical validation ────────────────────────────────────
        item_findings: dict[str, list] = {}
        for it in items:
            fs = clinical.validate_item(it, patient)
            checks_run += 8
            if fs:
                item_findings[it["key"]] = fs

        # ── 4. Regimen-level checks ────────────────────────────────────────────
        regimen_findings = clinical.validate_regimen(items, patient)
        regimen_findings += clinical.allergy_check(items, patient)
        checks_run += len(clinical.THERAPEUTIC_CLASSES) + 4

        # ── 5. Pairwise interactions ───────────────────────────────────────────
        interactions = []
        unverified: list[dict] = []
        pairs_checked = 0
        ai_calls = 0
        for a, b in combinations(items, 2):
            pairs_checked += 1
            hit, coverage, unknown = _interaction_row(db, a["active_substance"], b["active_substance"])

            # Deep AI discovery is opt-in: it costs seconds per pair, and the dispense
            # decision must stay fast and reproducible.
            if not hit and req.deep_ai and ANTHROPIC_API_KEY and ai_calls < 6:
                ai = check_interaction_ai(a["active_substance"], b["active_substance"], db)
                ai_calls += 1
                if ai and ai.get("has_interaction"):
                    hit, coverage = ai, "checked"

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
                        "from_interview": "interview" in (a.get("source"), b.get("source")),
                    }
                )
            elif coverage == "unverified":
                unverified.append(
                    {
                        "drug_a": a["trade_name"],
                        "drug_b": b["trade_name"],
                        "unknown": sorted(set(unknown)),
                    }
                )
        checks_run += pairs_checked
        interactions.sort(key=lambda i: SEVERITY_RANK.get(i["severity"], 9))

        # Absence of a record is not evidence of safety — say so explicitly.
        if unverified:
            names = sorted({u for pair in unverified for u in pair["unknown"]})
            regimen_findings.append(
                clinical.Finding(
                    code="UNVERIFIED",
                    severity="warning",
                    title=f"{len(unverified)}× dvojica sa nedala overiť",
                    detail=(
                        f"Látky {', '.join(names)} nie sú v interakčnej databáze. "
                        "Pre tieto dvojice systém nevie potvrdiť ani vylúčiť interakciu — "
                        "absencia záznamu neznamená bezpečnosť."
                    ),
                    drugs=names,
                    action="Overiť v SPC prípravku alebo konzultovať s predpisujúcim lekárom.",
                )
            )

        for note in intake_notes:
            regimen_findings.append(clinical.Finding(**note))

        # ── 6. Per-item decision ───────────────────────────────────────────────
        for it in items:
            status, reasons = _item_status(
                it, item_findings.get(it["key"], []), regimen_findings, interactions
            )
            it["status"], it["status_reasons"] = status, reasons

        prescription_items = [i for i in items if i["source"] == "prescription"]
        dispensable = sum(1 for i in prescription_items if i["status"] != "verify")

        # ── 7. Overall decision ────────────────────────────────────────────────
        all_findings = [f for fs in item_findings.values() for f in fs] + regimen_findings
        critical = sum(1 for f in all_findings if f.severity == "critical")
        warning = sum(1 for f in all_findings if f.severity == "warning")
        info = sum(1 for f in all_findings if f.severity == "info")
        major_ix = sum(1 for i in interactions if i["severity"] == "Závažná")
        moderate_ix = sum(1 for i in interactions if i["severity"] == "Stredná")

        verify_items = [i for i in prescription_items if i["status"] == "verify"]
        counsel_items = [i for i in prescription_items if i["status"] == "counsel"]
        declined_items = [i for i in items if i["status"] == "decline"]

        if not req.identity_verified:
            verdict, label = "BLOCK", "NEVYDAŤ"
            reason = "Totožnosť pacienta nebola overená."
            dispensable = 0
            for it in items:
                it["status"] = "verify"
                it["status_reasons"] = ["Neoverená totožnosť pacienta"]
            next_steps_override = [
                {
                    "kind": "verify",
                    "title": "Overiť totožnosť iným spôsobom",
                    "detail": "Vyžiadať doklad totožnosti a potvrdenie obsluhy. Bez overenia sa nevydáva "
                              "žiadna položka, vrátane voľnopredajných.",
                    "drugs": [],
                }
            ]
        elif verify_items:
            verdict, label = "VERIFY", "OVERIŤ U LEKÁRA"
            reason = (
                f"{len(verify_items)}× položka s podozrením na chybu v predpise alebo absolútnou "
                f"kontraindikáciou. Zvyšok receptu ({dispensable} z {len(prescription_items)}) sa vydáva."
            )
        elif counsel_items or declined_items:
            verdict, label = "COUNSEL", "VYDAŤ S POUČENÍM"
            bits = []
            if counsel_items:
                bits.append(f"{len(counsel_items)}× položka na poučenie")
            if declined_items:
                bits.append(f"{len(declined_items)}× voľnopredajný prípravok na odhovorenie")
            reason = "Celý recept sa vydáva. " + " a ".join(bits) + "."
        else:
            verdict, label = "DISPENSE", "VYDAŤ"
            reason = "Všetky kontroly prešli bez nálezu."

        resolutions = resolver.resolve_all(db, items, patient) if req.identity_verified else []
        next_steps = (
            next_steps_override
            if not req.identity_verified
            else _next_steps(items, item_findings, regimen_findings, interactions, profile.get("name"))
        )
        duration_ms = round((time.perf_counter() - started) * 1000, 1)

        # ── 8. Audit record ────────────────────────────────────────────────────
        audit = {
            "audit_id": f"AV-{uuid.uuid4().hex[:10].upper()}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "operator": "AvatarAI Dispense Engine v1",
            "identity_verified": req.identity_verified,
            "card_id": profile.get("card_id"),
            "patient": profile.get("name"),
            "items": len(prescription_items),
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
                {**it, "findings": [asdict(f) for f in item_findings.get(it["key"], [])]}
                for it in items
            ],
            "unresolved": unresolved,
            "interactions": interactions,
            "unverified_pairs": unverified,
            "findings": [asdict(f) for f in regimen_findings],
            "next_steps": next_steps,
            "resolutions": resolutions,
            "summary": {
                "items": len(prescription_items),
                "interview_items": len(extra),
                "dispensable": dispensable,
                "checks_run": checks_run,
                "pairs_checked": pairs_checked,
                "unverified_pairs": len(unverified),
                "critical": critical,
                "warning": warning,
                "info": info,
                "major_interactions": major_ix,
                "moderate_interactions": moderate_ix,
                "duration_ms": duration_ms,
                "ai_used": ai_calls > 0,
                "explanations_pending": sum(1 for i in interactions if not i.get("mechanism")),
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
