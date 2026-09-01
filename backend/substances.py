"""Substance name normalisation between the ŠÚKL registry and the interaction data.

The registry names the salt a product actually contains ("amlodipine besilate",
"atorvastatin calcium"); the interaction data names the base substance. Matching the
two by exact string silently drops the interaction — 71 of the 220 most-dispensed
registry substances never matched before this layer existed.

`resolve` also reports when a substance is simply absent from the interaction data,
so the caller can say "not verified" instead of implying "safe".
"""
from __future__ import annotations

import functools
import re

# Salt, ester and hydrate tokens that qualify a base substance. Stripped repeatedly
# from the end, since registry names stack them ("pantoprazole sodium sesquihydrate").
SALT_TOKENS = {
    "hydrochloride", "dihydrochloride", "hydrobromide", "hydroiodide",
    "sodium", "disodium", "potassium", "dipotassium", "calcium", "magnesium",
    "besilate", "besylate", "mesilate", "mesylate", "tosilate", "tosylate",
    "esilate", "esylate", "edisilate", "camsilate", "napadisilate",
    "maleate", "fumarate", "hemifumarate", "succinate", "tartrate", "bitartrate",
    "citrate", "dihydrogen", "hydrogen", "acetate", "phosphate", "diphosphate",
    "sulfate", "sulphate", "hemisulfate", "bisulfate", "nitrate", "oxalate",
    "malate", "lactate", "gluconate", "glucuronate", "stearate", "palmitate",
    "valerate", "propionate", "dipropionate", "butyrate", "furoate", "benzoate",
    "xinafoate", "embonate", "pamoate", "olamine", "trometamol", "meglumine",
    "arginine", "lysine", "erbumine", "aspartate", "orotate", "pivoxil",
    "monohydrate", "dihydrate", "trihydrate", "tetrahydrate", "pentahydrate",
    "hemihydrate", "sesquihydrate", "anhydrous", "micronised", "micronized",
    "monosodium", "hemicalcium", "trihydroxide",
}

# Prodrug esters the interaction data indexes under the parent substance.
PRODRUG_TOKENS = {"etexilate", "axetil", "proxetil", "medoxomil", "cilexetil", "fosil"}

# INN / USAN divergences and other genuine naming differences.
SYNONYMS = {
    "paracetamol": "acetaminophen",
    "ciclosporin": "cyclosporine",
    "cyclosporin": "cyclosporine",
    "st john's wort": "st. john's wort",
    "st johns wort": "st. john's wort",
    "hypericum perforatum": "st. john's wort",
    "ľubovník bodkovaný": "st. john's wort",
    "ginkgo": "ginkgo biloba",
    "fish oil": "omega-3 fatty acids",
    "omega-3": "omega-3 fatty acids",
    "salbutamol": "albuterol",
    "glibenclamide": "glyburide",
    "furosemide": "furosemide",
    "bendroflumethiazide": "bendroflumethiazide",
    "rifampicin": "rifampin",
    "trimethoprim sulfamethoxazole": "sulfamethoxazole",
    "co-trimoxazole": "sulfamethoxazole",
    "adrenaline": "epinephrine",
    "noradrenaline": "norepinephrine",
    "lidocaine": "lidocaine",
    "pethidine": "meperidine",
    "amoxicilline": "amoxicillin",
    "acetylsalicylic acid": "acetylsalicylic acid",
    "sodium valproate": "valproic acid",
    "valproate": "valproic acid",
    "valproate semisodium": "valproic acid",
    "levothyroxine sodium": "levothyroxine",
    "beclometasone": "beclomethasone",
    "dexamfetamine": "dextroamphetamine",
    "oestradiol": "estradiol",
    "colecalciferol": "cholecalciferol",
    "phenobarbital sodium": "phenobarbital",
    "metamizole": "dipyrone",
    "metamizole sodium": "dipyrone",
}

_WORD = re.compile(r"[a-z0-9'’\-\. ]+")


def _strip_salts(name: str) -> str:
    """Remove trailing salt/hydrate/prodrug qualifiers, innermost first."""
    tokens = name.split()
    changed = True
    while changed and len(tokens) > 1:
        changed = False
        if tokens[-1] in SALT_TOKENS or tokens[-1] in PRODRUG_TOKENS:
            tokens.pop()
            changed = True
    # Some registry entries lead with the salt: "sodium valproate".
    while len(tokens) > 1 and tokens[0] in SALT_TOKENS:
        tokens.pop(0)
    return " ".join(tokens)


def candidates(substance: str) -> list[str]:
    """Every form worth trying against the interaction data, best first."""
    raw = (substance or "").strip().lower()
    raw = raw.replace("’", "'")
    if not raw:
        return []

    forms: list[str] = []

    def add(value: str) -> None:
        value = value.strip(" .,")
        if value and value not in forms:
            forms.append(value)

    add(raw)
    add(SYNONYMS.get(raw, ""))

    stripped = _strip_salts(raw)
    add(stripped)
    add(SYNONYMS.get(stripped, ""))

    # "warfarin sodium clathrate" -> "warfarin"
    head = raw.split()[0]
    if len(head) > 4:
        add(head)
        add(SYNONYMS.get(head, ""))

    return forms


def split_components(substance: str) -> list[str]:
    """Combination products list their substances comma-separated."""
    return [p.strip() for p in (substance or "").split(",") if p.strip()]


@functools.lru_cache(maxsize=1)
def _known(db_path: str) -> frozenset[str]:
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT LOWER(drug_a) FROM interactions "
            "UNION SELECT DISTINCT LOWER(drug_b) FROM interactions"
        ).fetchall()
    finally:
        conn.close()
    return frozenset(r[0] for r in rows if r[0])


def known_substances(db) -> frozenset[str]:
    """Substances the interaction data actually covers, cached per database file."""
    try:
        path = next(r[2] for r in db.execute("PRAGMA database_list") if r[1] == "main")
    except Exception:
        path = ""
    return _known(path) if path else frozenset()


def resolve(db, substance: str) -> tuple[str | None, str]:
    """Map a registry substance onto its interaction-data name.

    Returns (resolved_name, status) where status is:
      "exact"      matched without changes
      "normalised" matched after stripping a salt or applying a synonym
      "unknown"    absent from the interaction data — absence of a hit proves nothing
    """
    known = known_substances(db)
    forms = candidates(substance)
    if not forms:
        return None, "unknown"
    for index, form in enumerate(forms):
        if form in known:
            return form, "exact" if index == 0 else "normalised"
    return None, "unknown"
