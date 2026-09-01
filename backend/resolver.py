"""Finding a way forward for a drug that cannot be dispensed as written.

Two branches that must never be confused:

  Self-medication  the pharmacy may recommend a different molecule on the spot.
                   Ibuprofen against warfarin becomes paracetamol, handed over now.

  Prescribed       the pharmacy may substitute a generic of the same molecule, never
                   a different one. So the outcome is: hold the item, dispense the
                   rest, notify the prescriber, send the patient back for a new script.
                   We can still *propose* a molecule for the prescriber to consider.
"""
from __future__ import annotations

from . import clinical, substances

# Curated ladders for the self-medication a pharmacy is actually asked about.
# ATC proximity does not help here: paracetamol (N02BE01) is the standard answer to
# an unsafe ibuprofen (M01AE01), and the two sit in different ATC branches.
OTC_LADDER: dict[str, list[dict]] = {
    "ibuprofen": [
        {
            "substance": "paracetamol",
            "why": "Neovplyvňuje zrážanlivosť ani sliznicu žalúdka a je bezpečný pri väčšine chronickej liečby.",
            "caveat": "Neprekračovať 3 g denne. Pri ochorení pečene alebo pravidelnom alkohole ešte menej.",
        },
        {
            "substance": "diclofenac",
            "topical_only": True,
            "why": "Ako masť alebo gél na miesto bolesti — do krvi sa dostane zlomok dávky.",
            "caveat": "Nenanášať na poranenú kožu a nepoužívať súčasne s tabletami NSAID.",
        },
    ],
    "diclofenac": [
        {
            "substance": "paracetamol",
            "why": "Bez vplyvu na zrážanlivosť a obličky.",
            "caveat": "Neprekračovať 3 g denne.",
        },
    ],
    "naproxen": [
        {
            "substance": "paracetamol",
            "why": "Bez vplyvu na zrážanlivosť a obličky.",
            "caveat": "Neprekračovať 3 g denne.",
        },
    ],
    "acetylsalicylic acid": [
        {
            "substance": "paracetamol",
            "why": "Na bolesť a horúčku má porovnateľný účinok bez vplyvu na krvácanie.",
            "caveat": "Ak beriete aspirín na riedenie krvi podľa lekára, ten nevysadzujte — ide len o užívanie proti bolesti.",
        },
    ],
    "paracetamol": [
        {
            "substance": "ibuprofen",
            "why": "Pri zápalovej bolesti účinkuje lepšie a nezaťažuje pečeň.",
            "caveat": "Nevhodný pri antikoagulanciách, vrede žalúdka a zníženej funkcii obličiek.",
        },
    ],
}

# Supplements have no drug substitute — the answer is to stop, not to swap.
SUPPLEMENT_ADVICE: dict[str, str] = {
    "st john's wort": (
        "Ľubovník nie je neškodná bylinka — výrazne urýchľuje odbúravanie mnohých liekov "
        "a znižuje ich účinok. Náhrada neexistuje, treba ho vysadiť a o nálade sa porozprávať "
        "s lekárom."
    ),
    "ginkgo biloba": (
        "Ginkgo zvyšuje sklon ku krvácaniu. Pri súčasnej liečbe na riedenie krvi ho vysaďte, "
        "náhrada nie je potrebná."
    ),
    "omega-3 fatty acids": (
        "Rybí olej môže mierne zvyšovať krvácanie. Nemusíte ho vysadiť, ale povedzte o ňom "
        "lekárovi pri najbližšej kontrole."
    ),
}


def _interacts(db, substance_a: str, substance_b: str) -> str | None:
    """Severity of the worst interaction between two substances, or None."""
    a_names = [n for n, _ in (substances.resolve(db, c) for c in substances.split_components(substance_a)) if n]
    b_names = [n for n, _ in (substances.resolve(db, c) for c in substances.split_components(substance_b)) if n]
    rank = {"Závažná": 0, "Stredná": 1, "Mierna": 2}
    worst = None
    for sa in a_names:
        for sb in b_names:
            if sa == sb:
                continue
            row = db.execute(
                """SELECT severity FROM interactions
                   WHERE (LOWER(drug_a)=? AND LOWER(drug_b)=?) OR (LOWER(drug_a)=? AND LOWER(drug_b)=?)
                   LIMIT 1""",
                (sa, sb, sb, sa),
            ).fetchone()
            if row and (worst is None or rank.get(row["severity"], 9) < rank.get(worst, 9)):
                worst = row["severity"]
    return worst


def _classes_of(substance: str) -> set[str]:
    key = clinical.normalise(substance)
    return {
        name
        for name, spec in clinical.THERAPEUTIC_CLASSES.items()
        if key in spec["substances"]
    }


def _is_clean(db, candidate: str, regimen: list[dict], exclude_name: str, patient,
              avoid_classes: set[str] | None = None) -> tuple[bool, str]:
    """Can this substance be recommended to this patient, alongside this regimen?

    Three gates, in order of how badly each fails:

    1. We must be able to vouch for it. A substance with no rule in the engine is
       unknown, not safe — proposing dexketoprofen to a pregnant patient only looked
       fine because nothing knew it was an NSAID.
    2. It must not belong to the class that caused the problem.
    3. It must not clash with the rest of the regimen or with the patient.

    A moderate interaction does not disqualify a swap — paracetamol alongside an NSAID
    is ordinary multimodal analgesia — but it is returned as a note.
    """
    key = clinical.normalise(candidate)
    if key not in clinical.RULES:
        return False, "látka nie je v pravidlách enginu — nevieme za ňu ručiť"

    if avoid_classes and (_classes_of(candidate) & avoid_classes):
        return False, "patrí do rovnakej terapeutickej triedy ako problémový liek"

    note = ""
    for other in regimen:
        if other["trade_name"] == exclude_name:
            continue
        severity = _interacts(db, candidate, other["active_substance"])
        if severity == "Závažná":
            return False, f"závažná interakcia s {other['trade_name']}"
        if severity == "Stredná" and not note:
            note = f"Pozor na súbeh s {other['trade_name']} — sledujte znášanlivosť."

    findings = clinical.validate_item(
        {"trade_name": candidate, "active_substance": candidate, "daily_dose_mg": None}, patient
    )
    blocker = next((f for f in findings if f.severity == "critical"), None)
    if blocker:
        return False, blocker.title

    return True, note


def _product_for(db, substance: str, topical: bool = False) -> dict | None:
    """A real registry product for a substance, preferring the plainest pack."""
    form_filter = "AND LOWER(form) LIKE '%gel%' OR LOWER(form) LIKE '%mast%'" if topical else ""
    row = db.execute(
        f"""SELECT id, trade_name, active_substance, atc_code, strength, form FROM drugs
            WHERE LOWER(active_substance) = ?
            {"AND (LOWER(form) LIKE '%gél%' OR LOWER(form) LIKE '%gel%' OR LOWER(form) LIKE '%mas%')" if topical else ""}
            ORDER BY LENGTH(trade_name) LIMIT 1""",
        (substance.lower(),),
    ).fetchone()
    if not row and topical:
        return _product_for(db, substance, topical=False)
    return dict(row) if row else None


def resolve_item(db, item: dict, regimen: list[dict], patient) -> dict:
    """What to do about one item that cannot go out as written."""
    substance = clinical.normalise(item.get("active_substance", ""))
    from_interview = item.get("source") == "interview"

    # ── Supplements: stop, do not swap ────────────────────────────────────────
    resolved_name, _ = substances.resolve(db, item.get("active_substance", ""))
    advice = SUPPLEMENT_ADVICE.get(resolved_name or "") or SUPPLEMENT_ADVICE.get(substance)
    if advice:
        return {
            "kind": "stop",
            "item": item["trade_name"],
            "headline": f"{item['trade_name']} prestaňte užívať",
            "detail": advice,
            "substitute": None,
        }

    # ── Self-medication: a real swap the counter can make right now ───────────
    if from_interview:
        for option in OTC_LADDER.get(substance, []):
            candidate = option["substance"]
            clean, note = _is_clean(db, candidate, regimen, item["trade_name"], patient)
            if not clean:
                continue
            product = _product_for(db, candidate, topical=option.get("topical_only", False))
            if not product:
                continue
            return {
                "kind": "substitute",
                "item": item["trade_name"],
                "headline": f"Namiesto {item['trade_name']} vám vydáme {product['trade_name']}",
                "detail": option["why"],
                "caveat": " ".join(x for x in (option.get("caveat", ""), note) if x),
                "substitute": {
                    "trade_name": product["trade_name"],
                    "active_substance": product["active_substance"],
                    "form": product.get("form"),
                    "strength": product.get("strength"),
                    "topical": option.get("topical_only", False),
                },
            }

        return {
            "kind": "stop",
            "item": item["trade_name"],
            "headline": f"{item['trade_name']} prestaňte užívať",
            "detail": "Bezpečnú náhradu, ktorá by sa nekrížila s vašou liečbou, nemáme. "
                      "Poraďte sa o bolesti s lekárom.",
            "substitute": None,
        }

    # ── Prescribed: the pharmacy cannot change the molecule ───────────────────
    proposal = None
    atc = (item.get("atc_code") or "")[:4]
    if atc:
        rows = db.execute(
            """SELECT active_substance, COUNT(*) n FROM drugs
               WHERE atc_code LIKE ? AND LOWER(active_substance) != ?
                 AND active_substance NOT LIKE '%,%'
               GROUP BY LOWER(active_substance) ORDER BY n DESC LIMIT 12""",
            (f"{atc}%", (item.get("active_substance") or "").lower()),
        ).fetchall()
        avoid = _classes_of(item.get("active_substance", ""))
        for row in rows:
            clean, _ = _is_clean(
                db, row["active_substance"], regimen, item["trade_name"], patient, avoid_classes=avoid
            )
            if clean:
                proposal = row["active_substance"]
                break

    return {
        "kind": "prescriber",
        "item": item["trade_name"],
        "headline": f"{item['trade_name']} musíme najprv overiť u lekára",
        "detail": (
            "Nejde o bežnú interakciu — tú by sme vám vydali a len na ňu upozornili. "
            "Tu máme podozrenie na chybu v predpise, tak zavoláme lekárovi a vydáme "
            "podľa jeho pokynu."
        ),
        "proposal": proposal,
        "proposal_note": (
            f"Lekárovi navrhujeme zvážiť {proposal} — v rovnakej skupine a bez interakcie "
            "so zvyškom vašej liečby."
            if proposal
            else "V rovnakej skupine sme nenašli liek bez interakcie — rozhodnutie je na lekárovi."
        ),
        "substitute": None,
    }


def resolve_all(db, items: list[dict], patient) -> list[dict]:
    """Resolutions for items the counter will not simply hand over.

    Self-medication can be swapped on the spot. A prescribed item held for a phone
    call gets a proposal for the prescriber, never a substitution by the pharmacy.
    """
    return [
        resolve_item(db, it, items, patient)
        for it in items
        if it.get("status") in ("decline", "verify")
    ]
