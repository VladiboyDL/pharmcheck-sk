"""Demo patient registry — simulates a health-insurance card (eID/EHIC) lookup.

The demo is presented live with a real camera pointed at the presenter, so there is
exactly one patient: the presenter. Scanning a 36-year-old man's face and announcing
a 98 % match against a 78-year-old woman is the fastest way to lose a room.

The clinical variety lives in the SCENARIOS instead. Each one overlays a plausible
medical profile onto the same person — renal function, chronic conditions, weight —
so the engine gets its edge cases without the identity having to lie.

In production this layer would call the Slovak eZdravie / NCZI patient index and the
insurer's photo service. For the demo everything is local and deterministic.
"""
from __future__ import annotations

# The presenter. Demographics are demo values — edit here, nowhere else.
PRIMARY_CARD = "SK8909174023"

DEMO_PATIENTS: dict[str, dict] = {
    PRIMARY_CARD: {
        "card_id": PRIMARY_CARD,
        "name": "Vladimír Rovčanin",
        "birth_id_masked": "890917/****",
        "birth_date": "1989-09-17",
        "age": 36,
        "sex": "M",
        "weight_kg": 84,
        "height_cm": 181,
        "egfr": 96,
        "hepatic_impairment": False,
        "pregnant": False,
        "breastfeeding": False,
        "allergies": [],
        "insurer": "Všeobecná zdravotná poisťovňa",
        "insurer_code": "25",
        "chronic": [],
        "photo_seed": "vlad",
        "biometric_reference": True,
        "primary": True,
    },
}


def get_patient(card_id: str) -> dict | None:
    return DEMO_PATIENTS.get((card_id or "").strip().upper())


def primary_patient() -> dict:
    return DEMO_PATIENTS[PRIMARY_CARD]


def list_patients() -> list[dict]:
    return list(DEMO_PATIENTS.values())


def with_profile(patient: dict, profile: dict | None) -> dict:
    """Overlay a scenario's clinical profile onto the identity."""
    merged = dict(patient)
    if profile:
        merged.update(profile)
    return merged
