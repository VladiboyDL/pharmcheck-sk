from __future__ import annotations
from itertools import combinations
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from .. import security
from ..database import get_db
from ..ai_checker import check_interaction_ai, explain_interaction_ai, ANTHROPIC_API_KEY
from ..models import (
    InteractionCheckRequest,
    InteractionCheckResponse,
    Interaction,
    InteractionDrug,
    SafePair,
    InteractionSummary,
)

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


def _find_interaction_db(db, substance_a: str, substance_b: str) -> dict | None:
    """Find interaction in DDInter database.
    Handles multi-substance drugs (comma-separated) by checking each pair."""
    subs_a = [s.strip().lower() for s in substance_a.split(",")]
    subs_b = [s.strip().lower() for s in substance_b.split(",")]

    best = None
    severity_rank = {"Závažná": 0, "Stredná": 1, "Mierna": 2}

    for sa in subs_a:
        for sb in subs_b:
            if sa == sb:
                continue
            row = db.execute(
                """
                SELECT severity, mechanism, management, alternatives
                FROM interactions
                WHERE (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                   OR (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                LIMIT 1
                """,
                (sa, sb, sb, sa),
            ).fetchone()

            if row:
                r = dict(row)
                r["source"] = "db"
                if best is None or severity_rank.get(r["severity"], 9) < severity_rank.get(best["severity"], 9):
                    best = r

    return best


def _find_interaction_ai(db, substance_a: str, substance_b: str) -> dict | None:
    """Find interaction using AI. Checks each substance pair for multi-substance drugs."""
    subs_a = [s.strip().lower() for s in substance_a.split(",")]
    subs_b = [s.strip().lower() for s in substance_b.split(",")]

    best = None
    severity_rank = {"Závažná": 0, "Stredná": 1, "Mierna": 2}

    for sa in subs_a:
        for sb in subs_b:
            if sa == sb:
                continue
            result = check_interaction_ai(sa, sb, db)
            if result and result.get("has_interaction"):
                if best is None or severity_rank.get(result.get("severity"), 9) < severity_rank.get(best.get("severity"), 9):
                    best = result

    return best


@router.post("/check", response_model=InteractionCheckResponse)
def check_interactions(req: InteractionCheckRequest, request: Request):
    security.rate_limit(request, "check", limit=60)
    if len(req.drug_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 drugs to check interactions")
    if len(req.drug_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 drugs per check")

    ai_enabled = bool(ANTHROPIC_API_KEY)
    db = get_db()
    try:
        # Fetch all drugs
        placeholders = ",".join("?" * len(req.drug_ids))
        drugs = db.execute(
            f"SELECT id, trade_name, active_substance, atc_code FROM drugs WHERE id IN ({placeholders})",
            req.drug_ids,
        ).fetchall()

        if len(drugs) < 2:
            raise HTTPException(status_code=404, detail="Not enough valid drugs found")

        drug_map = {d["id"]: dict(d) for d in drugs}
        found_interactions: list[Interaction] = []
        safe_pairs: list[SafePair] = []
        severity_counts = {"Závažná": 0, "Stredná": 0, "Mierna": 0}

        # Check all pairwise combinations
        for id_a, id_b in combinations(req.drug_ids, 2):
            if id_a not in drug_map or id_b not in drug_map:
                continue

            da = drug_map[id_a]
            db_drug = drug_map[id_b]

            # Step 1: Check DDInter database
            interaction = _find_interaction_db(db, da["active_substance"], db_drug["active_substance"])

            # Step 2: If not found in DB and AI is enabled, check with AI
            if not interaction and ai_enabled:
                ai_result = _find_interaction_ai(db, da["active_substance"], db_drug["active_substance"])
                if ai_result and ai_result.get("has_interaction"):
                    interaction = ai_result

            if interaction:
                sev = interaction["severity"]
                if sev in severity_counts:
                    severity_counts[sev] += 1

                found_interactions.append(
                    Interaction(
                        drug_a=InteractionDrug(
                            id=da["id"],
                            trade_name=da["trade_name"],
                            active_substance=da["active_substance"],
                        ),
                        drug_b=InteractionDrug(
                            id=db_drug["id"],
                            trade_name=db_drug["trade_name"],
                            active_substance=db_drug["active_substance"],
                        ),
                        severity=sev,
                        mechanism=interaction.get("mechanism"),
                        management=interaction.get("management"),
                        alternatives=interaction.get("alternatives"),
                        source=interaction.get("source", "db"),
                    )
                )
            else:
                safe_pairs.append(
                    SafePair(drug_a=da["trade_name"], drug_b=db_drug["trade_name"])
                )

        # Sort: Závažná first, then Stredná, then Mierna
        severity_order = {"Závažná": 0, "Stredná": 1, "Mierna": 2}
        found_interactions.sort(key=lambda x: severity_order.get(x.severity, 3))

        total_pairs = len(found_interactions) + len(safe_pairs)

        return InteractionCheckResponse(
            interactions_found=len(found_interactions),
            interactions=found_interactions,
            safe_pairs=safe_pairs,
            summary=InteractionSummary(
                total_pairs_checked=total_pairs,
                major=severity_counts["Závažná"],
                moderate=severity_counts["Stredná"],
                minor=severity_counts["Mierna"],
                none=len(safe_pairs),
            ),
            ai_enabled=ai_enabled,
        )
    finally:
        db.close()


# ── Lazy explanation ──────────────────────────────────────────────────────────


class ExplainRequest(BaseModel):
    substance_a: str
    substance_b: str
    severity: str


@router.post("/explain")
def explain(req: ExplainRequest, request: Request):
    """Clinical text for one pair, fetched when the pharmacist opens it.

    Kept out of the dispense pass on purpose: generating text costs seconds, and the
    dispense decision must stay fast and reproducible. Serves the stored text when it
    exists, generates and persists it otherwise.
    """
    security.rate_limit(request, "explain", limit=30)
    db = get_db()
    try:
        sa = req.substance_a.split(",")[0].strip().lower()
        sb = req.substance_b.split(",")[0].strip().lower()

        row = db.execute(
            """SELECT mechanism, management, alternatives FROM interactions
               WHERE (LOWER(drug_a)=? AND LOWER(drug_b)=?) OR (LOWER(drug_a)=? AND LOWER(drug_b)=?)
               LIMIT 1""",
            (sa, sb, sb, sa),
        ).fetchone()

        if row and row["mechanism"]:
            return {**dict(row), "source": "db"}

        if not ANTHROPIC_API_KEY:
            raise HTTPException(status_code=503, detail="Vysvetlenie nie je k dispozícii")

        result = explain_interaction_ai(sa, sb, req.severity, db)
        if not result:
            raise HTTPException(status_code=503, detail="Vysvetlenie sa nepodarilo vygenerovať")

        return {**result, "source": "ai"}
    finally:
        db.close()
