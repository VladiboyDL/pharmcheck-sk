"""Dispensing window — the full verification pass that replaces the manual counter check.

One call runs every gate a pharmacist would run by hand:
    identity → prescription parsing → interactions → dosing → duplication → risk burden
and returns a single dispense decision with a complete audit record.
"""
from __future__ import annotations

import html
import json
import re
import logging
import os
import time
import uuid
from dataclasses import asdict
from itertools import combinations
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

from .. import clinical
from ..ai_checker import ANTHROPIC_API_KEY, check_interaction_ai
from .. import dosing_plan, intake, resolver, security, substances
from ..database import get_db
from ..patients import get_patient
from ..prescription import resolve

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dispense", tags=["dispense"])

SEVERITY_RANK = {"Závažná": 0, "Stredná": 1, "Mierna": 2}

# One identity, several clinical situations. Every profile below is plausible for a
# 36-year-old man, so the face on the camera always matches the record on screen.
DEMO_SCENARIOS: dict[str, dict] = {
    "clean": {
        "id": "clean",
        "label": "Bežný recept",
        "subtitle": "Všetky kontroly prejdú",
        "prescriber": "MUDr. Silvia Rybárová, ambulancia VLD Žilina",
        "profile": {"chronic": ["Hypotyreóza"]},
        "text": (
            "EUTHYROX 75 ug tbl        1-0-0\n"
            "AMOKSIKLAV 1 g tbl        1-0-1\n"
            "PARALEN 500 mg tbl        1-0-1"
        ),
    },
    "pain_mood": {
        "id": "pain_mood",
        "label": "Bolesť chrbta a úzkosť",
        "subtitle": "Samoliečba odhalí riziko",
        "prescriber": "MUDr. Martin Krajčí, psychiatrická ambulancia Trnava",
        "profile": {"chronic": ["Depresívna porucha", "Chronická bolesť chrbta"]},
        "text": (
            "ZOLOFT 50 mg tbl          1-0-0\n"
            "TRAMAL 100 mg cps         1-1-1\n"
            "PARALEN 500 mg tbl        2-2-2\n"
            "VOLTAREN 50 mg tbl        1-1-1"
        ),
        "suggested_intake": {"otc_pain": ["ibuprofen"], "supplements": ["st_johns_wort"]},
    },
    "anticoagulation": {
        "id": "anticoagulation",
        "label": "Po pľúcnej embólii",
        "subtitle": "Antikoagulácia a riziko krvácania",
        "prescriber": "MUDr. Eva Tóthová, interná ambulancia Bratislava-Ružinov",
        "profile": {"chronic": ["Stav po pľúcnej embólii", "Hypertenzia", "Hypercholesterolémia"]},
        "text": (
            "WARFARIN ORION 5 mg tbl   1-0-0\n"
            "HELICID 20 mg cps         1-0-0\n"
            "Simvacard 20 mg tbl       0-0-1\n"
            "HIPRES 5 mg tbl           1-0-0"
        ),
        "suggested_intake": {"otc_pain": ["ibuprofen"]},
    },
    "renal": {
        "id": "renal",
        "label": "Znížená funkcia obličiek",
        "subtitle": "Dávkovanie podľa eGFR",
        "prescriber": "MUDr. Peter Hraško, diabetologická ambulancia Košice",
        "profile": {
            "egfr": 26,
            "chronic": ["Diabetes mellitus 2. typu", "Diabetická nefropatia, CKD G4"],
        },
        "text": (
            "SIOFOR 850 mg tbl         1-0-1\n"
            "RAMIPRIL 5 mg tbl         1-0-0\n"
            "IBALGIN 400 mg tbl        1-1-1"
        ),
    },
    "methotrexate": {
        "id": "methotrexate",
        "label": "Reumatoidná artritída",
        "subtitle": "Chyba vo frekvencii podávania",
        "prescriber": "MUDr. Jana Baloghová, reumatologická ambulancia Nitra",
        "profile": {"chronic": ["Reumatoidná artritída"]},
        "text": (
            "Methotrexat Ebewe 10 mg tbl   1-0-0\n"
            "Ibalgin 400 mg tbl            1-1-1\n"
            "Prednison 20 mg tbl           1-0-0"
        ),
    },
    "allergy": {
        "id": "allergy",
        "label": "Zaznamenaná alergia",
        "subtitle": "Penicilín v karte pacienta",
        "prescriber": "MUDr. Silvia Rybárová, ambulancia VLD Žilina",
        "profile": {"allergies": ["amoxicillin"], "chronic": ["Alergia na penicilín"]},
        "text": (
            "AMOKSIKLAV 1 g tbl        1-0-1\n"
            "PARALEN 500 mg tbl        1-0-1"
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
    # Demo scenario id — overlays a clinical profile onto the same identity.
    scenario: Optional[str] = None
    # Allow the operator to override the card-derived profile during a demo.
    patient_override: Optional[dict] = None


def _resolve_components(db, substance: str) -> tuple[list[str], list[str]]:
    """Split a registry substance into interaction-data names, plus what did not resolve."""
    resolved, unknown = [], []
    for component in substances.split_components(substance):
        name, _ = substances.resolve(db, component)
        (resolved if name else unknown).append(name or component)
    return resolved, unknown


def _load_interactions(db, names: set[str]) -> dict[frozenset[str], dict]:
    """Every interaction among a set of substances, in one query.

    The pair count grows with the square of the prescription, and a query per pair
    with it. One IN-clause over the whole regimen is the same work for SQLite and a
    fraction of the round trips.
    """
    if len(names) < 2:
        return {}
    ordered = sorted(names)
    placeholders = ",".join("?" * len(ordered))
    rows = db.execute(
        f"""SELECT drug_a, drug_b, severity, mechanism, management, alternatives
            FROM interactions
            WHERE LOWER(drug_a) IN ({placeholders}) AND LOWER(drug_b) IN ({placeholders})""",
        ordered + ordered,
    ).fetchall()

    found: dict[frozenset[str], dict] = {}
    for row in rows:
        key = frozenset({row["drug_a"].lower(), row["drug_b"].lower()})
        if len(key) < 2:
            continue
        current = found.get(key)
        if current is None or SEVERITY_RANK.get(row["severity"], 9) < SEVERITY_RANK.get(
            current["severity"], 9
        ):
            found[key] = {**dict(row), "source": "db"}
    return found


def _pair_interaction(index: dict, a_names: list[str], b_names: list[str]) -> dict | None:
    """Worst interaction between two resolved substance lists, from the prefetched index."""
    best = None
    for sa in a_names:
        for sb in b_names:
            if sa == sb:
                continue
            hit = index.get(frozenset({sa, sb}))
            if hit and (
                best is None
                or SEVERITY_RANK.get(hit["severity"], 9) < SEVERITY_RANK.get(best["severity"], 9)
            ):
                best = hit
    return best


@router.get("/scenarios")
def scenarios():
    """The clinical situations available in the demo, all for the same patient.

    Each carries a readable preview built by the real parser. The kiosk shows the
    prescription before the check finishes, and "EUTHYROX 75 ug tbl 1-0-0" is the
    prescriber's shorthand — not something to put in front of a patient.
    """
    db = get_db()
    try:
        out = []
        for scenario in DEMO_SCENARIOS.values():
            items, _ = resolve(db, scenario["text"])
            out.append(
                {
                    **{k: v for k, v in scenario.items() if k != "profile"},
                    "preview": [
                        {
                            "trade_name": it["trade_name"],
                            "strength": dosing_plan.strength_text(it),
                            "schedule": dosing_plan.schedule_text(it),
                        }
                        for it in items
                    ],
                }
            )
        return {"scenarios": out}
    finally:
        db.close()


@router.get("/scenarios/{scenario_id}")
def scenario_for(scenario_id: str):
    scenario = DEMO_SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenár neexistuje")
    return scenario


@router.get("/intake")
def intake_questions(card_id: str | None = None, scenario: str | None = None):
    """The interview shown before evaluation.

    A prescription only describes what a prescriber knew about. Most harm at the
    counter comes from what is missing from it — OTC analgesics, herbal supplements,
    a second prescriber's script — so we ask before we judge.
    """
    patient = dict(get_patient(card_id) or {}) if card_id else {}
    # The scenario decides whether the patient is on chronic therapy, which decides
    # whether the adherence question is worth asking.
    sc = DEMO_SCENARIOS.get(scenario or "")
    if sc:
        patient.update(sc["profile"])
    return {"questions": intake.questions_for(patient or None)}


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
                + ". Recept je platný, výdajník ich pripraví — nálezy nižšie sú na poučenie, "
                "nie dôvod na odmietnutie.",
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
                "title": f"{ix['drug_a']} a {ix['drug_b']} sa navzájom ovplyvňujú",
                "kind": "inform",
                "ask": f"Upozorniť na súbeh {ix['drug_a']} a {ix['drug_b']}.",
                "patient": (
                    f"{ix['drug_a']} a {ix['drug_b']} sa navzájom ovplyvňujú. "
                    "Preberte to s lekárom pri najbližšej návšteve — liek preto vysadzovať netreba."
                ),
                "notify_prescriber": ix["severity"] == "Závažná",
                "patient_visible": ix["severity"] == "Závažná",
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
                    "title": _headline_for(f, item["trade_name"]),
                    "kind": "ask",
                    "ask": _ask_for(f, item["trade_name"]),
                    "patient": _patient_text_for(f, item["trade_name"]),
                    "patient_visible": f.code in PATIENT_VISIBLE_CODES,
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
                "title": _headline_for(f, ", ".join(f.drugs)),
                "kind": "ask",
                "ask": _ask_for(f, ", ".join(f.drugs)),
                "patient": _patient_text_for(f, ", ".join(f.drugs)),
                "patient_visible": f.code in PATIENT_VISIBLE_CODES,
                "say": f.action or "",
                "severity": "Upozornenie",
            }
        )

    # Twenty-one things to say is nothing said. Rank by clinical weight so the top of
    # the list is what actually gets spoken at the window.
    weight = {"Závažná": 0, "Upozornenie": 1, "Stredná": 2}
    script.sort(key=lambda line: weight.get(line.get("severity"), 3))
    return script


# Only findings a patient can act on with their own body reach the kiosk. Everything
# else is for the pharmacist: a data gap in the interaction set, or a count of how
# many medicines someone takes, tells a patient nothing and only frightens them.
# An allowlist rather than a blocklist — a new finding code stays out until someone
# has written patient-facing words for it.
PATIENT_VISIBLE_CODES = frozenset({
    "DUPLICATE",
    "BLEEDING_BURDEN",
    "SEROTONIN_BURDEN",
    "FALL_RISK",
    "GERIATRIC",
    "QT",
    "RENAL_REDUCE",
    "RENAL_CAUTION",
    "NEAR_MAX_DOSE",
})


def _patient_text_for(finding, subject: str) -> str:
    """The same finding without the clinical vocabulary.

    clinical.py writes for a pharmacist — "kumulatívne riziko krvácania",
    "hemostáza", "NSAID" — which is right for the console and wrong for the counter.
    The kiosk gets this instead; the console keeps the original.
    """
    by_code = {
        "DUPLICATE": (
            f"{subject} účinkujú rovnako. Užívať oboje nepomôže viac, ale zaťažuje žalúdok a obličky."
        ),
        "BLEEDING_BURDEN": (
            f"{subject} spolu zvyšujú sklon ku krvácaniu. Všímajte si modriny, krvácanie ďasien "
            "alebo tmavú stolicu a ozvite sa lekárovi."
        ),
        "SEROTONIN_BURDEN": (
            f"{subject} sa navzájom zosilňujú. Ak by sa objavil nepokoj, tras, potenie alebo "
            "zrýchlený pulz, kontaktujte lekára."
        ),
        "FALL_RISK": (
            f"{subject} môžu spôsobiť závrat alebo neistotu pri chôdzi. Vstávajte pomaly, "
            "hlavne v noci."
        ),
        "GERIATRIC": f"{subject} sa vo vyššom veku znáša horšie. Lekár môže zvážiť nižšiu dávku.",
        "QT": f"{subject} môžu ovplyvniť srdcový rytmus. Pri búšení srdca alebo slabosti volajte lekára.",
        "RENAL_REDUCE": "Vaše obličky pracujú pomalšie, preto liek potrebuje nižšiu dávku. Overíme to s lekárom.",
        "RENAL_CAUTION": "Vaše obličky pracujú pomalšie. Lekár by mal ich funkciu pravidelne kontrolovať.",
        "NEAR_MAX_DOSE": f"{subject} máte na hornej hranici povolenej dávky. Neprikladajte si nič navyše.",
        "POLYPHARMACY": (
            "Užívate viac liekov naraz. Oplatí sa raz za čas prejsť si ich s lekárom a vyradiť, "
            "čo už netreba."
        ),
        "UNVERIFIED": (
            "O jednej kombinácii nemáme dosť údajov, takže ju nevieme potvrdiť ani vylúčiť. "
            "Spomeňte to lekárovi."
        ),
    }
    return by_code.get(finding.code, finding.detail)


def _headline_for(finding, subject: str) -> str:
    """A short line in the patient's language — never an instruction to staff."""
    by_code = {
        "DUPLICATE": "Dva lieky s rovnakým účinkom",
        "BLEEDING_BURDEN": "Viac liekov, ktoré riedia krv",
        "SEROTONIN_BURDEN": "Lieky, ktoré sa navzájom zosilňujú",
        "FALL_RISK": "Lieky, po ktorých môžete byť neistí",
        "GERIATRIC": f"{subject} vyžaduje opatrnosť",
        "QT": "Lieky ovplyvňujúce srdcový rytmus",
        "RENAL_REDUCE": "Dávka podľa vašich obličiek",
        "RENAL_CAUTION": "Dávka podľa vašich obličiek",
        "NEAR_MAX_DOSE": f"{subject} je na hornej hranici dávky",
        "POLYPHARMACY": "Užívate viac liekov naraz",
        "UNVERIFIED": "Niečo sme nevedeli overiť",
    }
    return by_code.get(finding.code, finding.title)


def _ask_for(finding, subject: str) -> str:
    """The opening question, phrased for the specific kind of finding."""
    by_code = {
        "GERIATRIC": f"Ako {subject} znášate? Nemávate závraty alebo pocit neistoty pri chôdzi?",
        "FALL_RISK": "Nestalo sa vám v poslednom čase, že by ste zakopli alebo spadli?",
        "BLEEDING_BURDEN": "Nevšimli ste si, že sa vám ľahšie robia modriny alebo dlhšie krváca ranka?",
        "SEROTONIN_BURDEN": "Nemávate nepokoj, tras alebo nadmerné potenie?",
        "DUPLICATE": f"Upozorniť, že {subject} obsahujú podobnú účinnú látku — nemá zmysel brať oboje.",
        "RENAL_REDUCE": "Kedy ste mali naposledy kontrolu obličiek?",
        "RENAL_CAUTION": "Kedy ste mali naposledy kontrolu obličiek?",
        "NEAR_MAX_DOSE": f"Beriete {subject} presne podľa predpisu, alebo si niekedy pridáte?",
        "POLYPHARMACY": "Máte prehľad o všetkých liekoch, ktoré užívate?",
        "QT": "Nemávate búšenie srdca alebo pocit na odpadnutie?",
        "UNVERIFIED": "Užívate okrem toho ešte niečo, o čom sme sa nebavili?",
    }
    return by_code.get(finding.code, f"Upozorniť pacienta na {subject}.")


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
def verify(req: VerifyRequest, request: Request):
    security.rate_limit(request, "verify", limit=60)
    started = time.perf_counter()
    db = get_db()
    try:
        # ── Patient profile ────────────────────────────────────────────────────
        record = get_patient(req.card_id) if req.card_id else None
        profile = dict(record) if record else {}
        scenario = DEMO_SCENARIOS.get(req.scenario or "")
        if scenario:
            profile.update(scenario["profile"])
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
        resolved_names: dict[str, tuple[list[str], list[str]]] = {
            it["key"]: _resolve_components(db, it["active_substance"]) for it in items
        }
        index = _load_interactions(
            db, {n for names, _ in resolved_names.values() for n in names}
        )

        interactions = []
        unverified: list[dict] = []
        pairs_checked = 0
        ai_calls = 0
        for a, b in combinations(items, 2):
            pairs_checked += 1
            a_names, a_unknown = resolved_names[a["key"]]
            b_names, b_unknown = resolved_names[b["key"]]
            unknown = a_unknown + b_unknown
            hit = _pair_interaction(index, a_names, b_names) if a_names and b_names else None
            coverage = "checked" if not unknown and a_names and b_names else "unverified"

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
        # A ten-hex audit id is fine for a console row but far too guessable for a
        # public link to someone's medication. The QR uses this instead.
        plan_token = security.public_token()
        # Which drawer the robot loaded. Deterministic from the audit id so every
        # surface names the same one.
        compartment = f"{'ABCDEFGH'[int(uuid.uuid4().hex[:2], 16) % 8]}{int(uuid.uuid4().hex[:2], 16) % 9 + 1}"
        audit = {
            "audit_id": f"AV-{uuid.uuid4().hex[:10].upper()}",
            "plan_token": plan_token,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "operator": "AvatarAI Dispense Engine v1",
            "identity_verified": req.identity_verified,
            "card_id": profile.get("card_id"),
            "patient": profile.get("name"),
            "items": len(prescription_items),
            "checks_run": checks_run,
            "verdict": verdict,
        }
        plan = dosing_plan.build(items)
        _write_audit(db, audit, req.prescription_text, all_findings, interactions, plan)

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
            "dosing_plan": plan,
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
            "prescriber": (scenario or {}).get("prescriber"),
            "plan_token": plan_token,
            "compartment": compartment if dispensable else None,
        }
    finally:
        db.close()


def _write_audit(db, audit: dict, prescription: str, findings, interactions, plan=None) -> None:
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
                findings_json TEXT,
                plan_json TEXT,
                plan_token TEXT
            )"""
        )
        # Older databases predate plan_json; add it in place rather than migrating.
        cols = {r[1] for r in db.execute("PRAGMA table_info(dispense_log)")}
        if "plan_json" not in cols:
            db.execute("ALTER TABLE dispense_log ADD COLUMN plan_json TEXT")
        if "plan_token" not in cols:
            db.execute("ALTER TABLE dispense_log ADD COLUMN plan_token TEXT")
        db.execute(
            """INSERT OR IGNORE INTO dispense_log
               (audit_id, timestamp, card_id, patient, verdict, checks_run, prescription,
                findings_json, plan_json, plan_token)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
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
                json.dumps(plan, ensure_ascii=False),
                audit.get("plan_token"),
            ),
        )
        db.commit()
    except Exception:
        pass  # audit write must never block a dispense decision


@router.get("/log")
def dispense_log(limit: int = 50):
    """Recent dispensing decisions — the audit trail.

    Names are initials and card numbers are dropped. The console shows this to prove
    a chain of custody exists, which needs no identifying detail; returning the real
    values made an unauthenticated endpoint into a list of who collected what.
    """
    db = get_db()
    try:
        db.execute(
            """CREATE TABLE IF NOT EXISTS dispense_log (
                id INTEGER PRIMARY KEY, audit_id TEXT UNIQUE, timestamp TEXT, card_id TEXT,
                patient TEXT, verdict TEXT, checks_run INTEGER, prescription TEXT, findings_json TEXT)"""
        )
        rows = db.execute(
            """SELECT audit_id, timestamp, patient, verdict, checks_run
               FROM dispense_log ORDER BY id DESC LIMIT ?""",
            (min(limit, 100),),
        ).fetchall()
        return {
            "entries": [
                {**dict(r), "patient": security.mask_name(r["patient"])} for r in rows
            ]
        }
    finally:
        db.close()


# ── Taking the plan home ──────────────────────────────────────────────────────


class SendPlanRequest(BaseModel):
    # The token proves the caller just completed this dispense. Nothing about the
    # message body comes from the client any more.
    token: str
    email: str

    @field_validator("email")
    @classmethod
    def _plausible_address(cls, value: str) -> str:
        # A shape check, not RFC 5322 — enough to reject junk without a dependency.
        if not re.fullmatch(r"[^@\s]{1,64}@[^@\s.]+(\.[^@\s.]+)+", value.strip()):
            raise ValueError("Neplatná e-mailová adresa")
        return value.strip()


@router.post("/send-plan")
def send_plan(req: SendPlanRequest, request: Request):
    """Email the dosing plan, when a provider is configured.

    Health data over ordinary email is a GDPR problem, not a feature — a real
    deployment sends a link behind authentication, or hands over a printed slip.
    This endpoint exists so the flow is complete and so wiring a provider is one
    environment variable, but it says plainly when nothing was actually sent.
    """
    security.rate_limit(request, "send-plan", limit=5, window_secs=300)

    # Built from what we stored, not from what was posted — otherwise this endpoint
    # will send arbitrary text to an arbitrary address for anyone who finds it.
    stored = _load_plan(req.token)
    if not stored:
        raise HTTPException(status_code=404, detail="Rozpis sa nenašiel")
    body = dosing_plan.as_text(stored.get("patient") or "", stored["plan"], [])

    api_key = os.getenv("RESEND_API_KEY", "")
    sender = os.getenv("PLAN_SENDER", "")

    if not api_key or not sender:
        return {
            "sent": False,
            "simulated": True,
            "reason": "Odosielanie e-mailov nie je nakonfigurované — nastavte RESEND_API_KEY a PLAN_SENDER.",
            "preview": body,
        }

    try:
        import urllib.request

        payload = json.dumps(
            {
                "from": sender,
                "to": [req.email],
                "subject": "Rozpis vašich liekov",
                "text": body,
            }
        ).encode()
        request = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read()
        return {"sent": True, "simulated": False, "preview": body}
    except Exception as e:
        logger.warning(f"send-plan failed: {e}")
        return {
            "sent": False,
            "simulated": False,
            "reason": "E-mail sa nepodarilo odoslať.",
            "preview": body,
        }


@router.get("/plan/{token}.ics")
def plan_calendar(token: str, request: Request):
    """Daily medication reminders, as a calendar file the phone keeps."""
    security.rate_limit(request, "plan", limit=60)
    stored = _load_plan(token)
    if not stored:
        raise HTTPException(status_code=404, detail="Rozpis sa nenašiel")

    ics = dosing_plan.as_icalendar(stored["plan"], time.strftime("%Y%m%d"), stored["audit_id"])
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="lieky.ics"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/plan/{token}", response_class=HTMLResponse)
def plan_page(token: str, request: Request):
    """The page behind the QR code.

    Deliberately a plain server-rendered page: it opens on any phone, prints, and can
    be added to the home screen. Scanning plain text would have shown the plan and
    then lost it — this is something the patient can keep.
    """
    security.rate_limit(request, "plan", limit=60)
    stored = _load_plan(token)
    if not stored:
        return HTMLResponse(
            "<!doctype html><meta charset='utf-8'><title>Rozpis nenájdený</title>"
            "<p style='font:16px system-ui;padding:2rem'>Tento rozpis už nie je dostupný.</p>",
            status_code=404,
        )

    rows = []
    for entry in stored["plan"]:
        extras = "".join(
            f'<p class="note">{html.escape(text)}</p>'
            for text in (entry.get("when"), entry.get("avoid"))
            if text
        )
        rows.append(
            f'<li><h2>{html.escape(entry["trade_name"])}</h2>'
            f'<p class="when">{html.escape(entry["schedule"])}</p>{extras}</li>'
        )

    return HTMLResponse(
        PLAN_PAGE.format(
            name=html.escape(stored.get("patient") or ""),
            rows="".join(rows),
            token=html.escape(token),
        ),
        # A medication list should not sit in a shared cache or a browser history entry
        # that outlives the visit.
        headers={"Cache-Control": "no-store, max-age=0", "Referrer-Policy": "no-referrer"},
    )


PLAN_PAGE = """<!doctype html>
<html lang="sk"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rozpis liekov</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:1.5rem 1.25rem 3rem; font:16px/1.55 system-ui,-apple-system,sans-serif;
         background:#f7f8f7; color:#121a17; max-width:34rem; margin-inline:auto; }}
  @media (prefers-color-scheme: dark) {{ body {{ background:#0d1512; color:#e6edea; }} }}
  header {{ border-bottom:2px solid currentColor; padding-bottom:.9rem; margin-bottom:1.25rem; }}
  h1 {{ font-size:1.5rem; margin:0 0 .2rem; letter-spacing:-.02em; }}
  .who {{ opacity:.6; font-size:.9rem; }}
  ul {{ list-style:none; padding:0; margin:0; display:grid; gap:.85rem; }}
  li {{ border:1px solid rgba(128,128,128,.3); border-radius:12px; padding:.9rem 1rem; }}
  h2 {{ font-size:1.05rem; margin:0 0 .3rem; }}
  .when {{ margin:0; font-weight:600; color:#0f7b5a; }}
  @media (prefers-color-scheme: dark) {{ .when {{ color:#47c295; }} }}
  .note {{ margin:.35rem 0 0; font-size:.9rem; opacity:.75; }}
  .cta {{ display:block; margin:1.5rem 0 0; padding:1rem; border-radius:14px; background:#0f7b5a;
          color:#fff; text-align:center; font-weight:600; text-decoration:none; }}
  @media (prefers-color-scheme: dark) {{ .cta {{ background:#47c295; color:#08110d; }} }}
  footer {{ margin-top:2rem; font-size:.78rem; opacity:.55; }}
  @media print {{ .cta {{ display:none; }} body {{ background:#fff; color:#000; }} }}
</style></head><body>
<header><h1>Rozpis liekov</h1><p class="who">{name}</p></header>
<ul>{rows}</ul>
<a class="cta" href="/api/dispense/plan/{token}.ics">Pridať pripomienky do kalendára</a>
<footer>Vygenerované systémom AvatarAI Dispense. Nenahrádza pokyny lekára ani lekárnika.</footer>
</body></html>"""


def _load_plan(token: str) -> dict | None:
    """Look a plan up by its public token, never by the audit id."""
    if not token or len(token) < 16:
        return None
    db = get_db()
    try:
        row = db.execute(
            "SELECT audit_id, patient, plan_json FROM dispense_log WHERE plan_token = ?",
            (token,),
        ).fetchone()
        if not row or not row["plan_json"]:
            return None
        return {
            "audit_id": row["audit_id"],
            "patient": row["patient"],
            "plan": json.loads(row["plan_json"]),
        }
    except Exception:
        return None
    finally:
        db.close()


# ── Telling the prescriber ────────────────────────────────────────────────────


class NotifyPrescriberRequest(BaseModel):
    audit_id: str
    prescriber: Optional[str] = None
    patient: Optional[str] = None
    subject: str
    detail: str


@router.post("/notify-prescriber")
def notify_prescriber(req: NotifyPrescriberRequest, request: Request):
    """Send the finding back to the doctor who wrote the prescription.

    The evidence for this is better than for anything else the counter can do about
    an interaction: asynchronous, non-interruptive notifications to the prescriber
    changed the prescription within seven days in roughly a quarter of cases. Telling
    the patient to "mention it next time" changes almost nothing by comparison.

    Delivery is out of scope for the demo — production routes this over the national
    e-prescribing channel, not email. What is real here is the queue and the record.
    """
    security.rate_limit(request, "notify", limit=20)
    db = get_db()
    try:
        db.execute(
            """CREATE TABLE IF NOT EXISTS prescriber_notifications (
                id INTEGER PRIMARY KEY,
                audit_id TEXT,
                created_at TEXT,
                prescriber TEXT,
                patient TEXT,
                subject TEXT,
                detail TEXT,
                delivered INTEGER NOT NULL DEFAULT 0
            )"""
        )
        db.execute(
            """INSERT INTO prescriber_notifications
               (audit_id, created_at, prescriber, patient, subject, detail, delivered)
               VALUES (?,?,?,?,?,?,0)""",
            (
                req.audit_id,
                time.strftime("%Y-%m-%dT%H:%M:%S"),
                req.prescriber,
                req.patient,
                req.subject,
                req.detail,
            ),
        )
        db.commit()
        return {
            "queued": True,
            "delivered": False,
            "simulated": True,
            "channel": "eRecept — kanál pre správy predpisujúcemu lekárovi",
            "message": "Správa je pripravená na odoslanie lekárovi.",
        }
    finally:
        db.close()


@router.get("/prescriber-notifications")
def prescriber_notifications(limit: int = 25):
    """What has been queued back to prescribers — visible in the pharmacist console."""
    security.rate_limit(request, "notify", limit=20)
    db = get_db()
    try:
        db.execute(
            """CREATE TABLE IF NOT EXISTS prescriber_notifications (
                id INTEGER PRIMARY KEY, audit_id TEXT, created_at TEXT, prescriber TEXT,
                patient TEXT, subject TEXT, detail TEXT, delivered INTEGER NOT NULL DEFAULT 0)"""
        )
        rows = db.execute(
            """SELECT audit_id, created_at, prescriber, patient, subject, delivered
               FROM prescriber_notifications ORDER BY id DESC LIMIT ?""",
            (min(limit, 100),),
        ).fetchall()
        return {
            "notifications": [
                {**dict(r), "patient": security.mask_name(r["patient"])} for r in rows
            ]
        }
    finally:
        db.close()
