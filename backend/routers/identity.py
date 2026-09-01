"""Patient identity verification — insurance card read + biometric match.

The Slovak preukaz poistenca carries no chip and no NFC: it is a printed plastic card.
So the read is optical — the card goes under a camera and OCR lifts the name, birth
number and insurer code off the front. Anything that talks about tapping a chip is
describing a card Slovakia does not issue.

DEMO IMPLEMENTATION. The OCR and the face match are simulated locally and labelled as
such in every response (`simulated: true`). In production the OCR runs on-device and
the record is confirmed against the eZdravie/NCZI patient index.
"""
from __future__ import annotations

import hashlib
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..patients import get_patient, list_patients, primary_patient

router = APIRouter(prefix="/api/identity", tags=["identity"])

# A face match below this score cannot authorise a dispense on its own.
MATCH_THRESHOLD = 92.0


class CardReadRequest(BaseModel):
    card_id: str


class BiometricRequest(BaseModel):
    card_id: str
    # Optional: the frontend can send a frame hash so repeated scans of the same
    # face stay deterministic across a demo run.
    frame_signature: Optional[str] = None
    force_mismatch: bool = False


@router.get("/cards")
def demo_cards():
    """The card available to tap. One patient: whoever is presenting."""
    return {
        "simulated": True,
        "primary_card": primary_patient()["card_id"],
        "cards": [
            {
                "card_id": p["card_id"],
                "name": p["name"],
                "age": p["age"],
                "insurer": p["insurer"],
                "summary": ", ".join(p["chronic"]) or "Bez chronickej liečby",
            }
            for p in list_patients()
        ],
    }


@router.post("/card")
def read_card(req: CardReadRequest):
    """Simulate optically reading the printed front of the insurance card."""
    patient = get_patient(req.card_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Karta poistenca nebola rozpoznaná")

    return {
        "simulated": True,
        "read_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "channel": "Optické snímanie (OCR)",
        "fields_read": ["Meno a priezvisko", "Rodné číslo", "Číslo preukazu", "Kód poisťovne"],
        "card_valid": True,
        "insurance_active": True,
        "patient": {
            "card_id": patient["card_id"],
            "name": patient["name"],
            "birth_id_masked": patient["birth_id_masked"],
            "age": patient["age"],
            "sex": patient["sex"],
            "weight_kg": patient["weight_kg"],
            "height_cm": patient["height_cm"],
            "egfr": patient["egfr"],
            "allergies": patient["allergies"],
            "pregnant": patient.get("pregnant", False),
            "pregnancy_week": patient.get("pregnancy_week"),
            "hepatic_impairment": patient.get("hepatic_impairment", False),
            "insurer": patient["insurer"],
            "insurer_code": patient["insurer_code"],
            "chronic": patient["chronic"],
            "guardian": patient.get("guardian"),
            "biometric_reference": patient.get("biometric_reference", True),
            "biometric_note": patient.get("biometric_note"),
        },
    }


@router.post("/biometric")
def verify_biometric(req: BiometricRequest):
    """Simulate a 1:1 face match against the insurer's reference photo."""
    patient = get_patient(req.card_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Karta poistenca nebola rozpoznaná")

    if not patient.get("biometric_reference", True):
        return {
            "simulated": True,
            "verified": False,
            "requires_override": True,
            "match_score": None,
            "liveness": None,
            "reason": patient.get(
                "biometric_note", "Pre tohto pacienta nie je k dispozícii biometrická referencia."
            ),
            "escalation": "Vyžaduje sa prítomnosť zákonného zástupcu a potvrdenie obsluhy.",
        }

    if req.force_mismatch:
        return {
            "simulated": True,
            "verified": False,
            "requires_override": True,
            "match_score": 41.7,
            "liveness": {"passed": True, "score": 97.2},
            "reason": "Tvár sa nezhoduje s referenčnou fotografiou poistenca.",
            "escalation": "Výdaj zablokovaný. Vyžaduje sa doklad totožnosti a potvrdenie obsluhy.",
        }

    # Deterministic pseudo-score in the 94.0–99.4 band, stable per card + frame.
    seed = f"{patient['card_id']}:{req.frame_signature or 'default'}"
    digest = hashlib.sha256(seed.encode()).digest()
    match_score = round(94.0 + (digest[0] / 255) * 5.4, 1)
    liveness_score = round(95.0 + (digest[1] / 255) * 4.8, 1)

    return {
        "simulated": True,
        "verified": match_score >= MATCH_THRESHOLD,
        "requires_override": False,
        "match_score": match_score,
        "threshold": MATCH_THRESHOLD,
        "liveness": {"passed": True, "score": liveness_score, "method": "pasívna detekcia (blink + hĺbka)"},
        "matched_name": patient["name"],
        "reference": "Fotografia poistenca — " + patient["insurer"],
        "reason": (
            f"Zhoda {match_score} % s referenčnou fotografiou poistenca, prah {MATCH_THRESHOLD} %. "
            "Snímka sa neukladá."
        ),
    }
