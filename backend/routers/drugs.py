from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from ..database import get_db
from ..models import (
    Drug,
    DrugDetail,
    DrugSearchResult,
    AlternativeSuggestion,
    ResolverResponse,
    ATCGroup,
    ATCBrowseResponse,
    DatabaseStats,
)

router = APIRouter(prefix="/api/drugs", tags=["drugs"])

ATC_GROUPS = {
    "A": "Tráviaci trakt a metabolizmus",
    "B": "Krv a krvotvorné orgány",
    "C": "Kardiovaskulárny systém",
    "D": "Dermatologiká",
    "G": "Urogenitálny systém a pohlavné hormóny",
    "H": "Systémové hormóny okrem pohlavných",
    "J": "Antiinfektíva na systémové použitie",
    "L": "Antineoplastiká a imunomodulátory",
    "M": "Muskuloskeletálny systém",
    "N": "Nervový systém",
    "P": "Antiparazitiká",
    "R": "Respiračný systém",
    "S": "Zmyslové orgány",
    "V": "Rôzne",
}


@router.get("/search", response_model=DrugSearchResult)
def search_drugs(q: str = Query(..., min_length=1), limit: int = Query(15, le=50)):
    db = get_db()
    try:
        fts_query = q.replace('"', '""') + "*"
        rows = db.execute(
            """
            SELECT d.id, d.trade_name, d.active_substance, d.atc_code, d.strength, d.form
            FROM drugs_fts fts
            JOIN drugs d ON d.id = fts.rowid
            WHERE drugs_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, limit),
        ).fetchall()

        if not rows:
            like_q = f"%{q}%"
            rows = db.execute(
                """
                SELECT id, trade_name, active_substance, atc_code, strength, form
                FROM drugs
                WHERE trade_name LIKE ? OR active_substance LIKE ?
                ORDER BY trade_name
                LIMIT ?
                """,
                (like_q, like_q, limit),
            ).fetchall()

        return DrugSearchResult(results=[Drug(**dict(r)) for r in rows])
    finally:
        db.close()


@router.get("/stats", response_model=DatabaseStats)
def get_stats():
    db = get_db()
    try:
        total_drugs = db.execute("SELECT COUNT(*) FROM drugs").fetchone()[0]
        total_interactions = db.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]

        drugs_with_interactions = db.execute("""
            SELECT COUNT(DISTINCT substance) FROM (
                SELECT LOWER(drug_a) as substance FROM interactions
                UNION
                SELECT LOWER(drug_b) as substance FROM interactions
            )
        """).fetchone()[0]

        severity_rows = db.execute(
            "SELECT severity, COUNT(*) as cnt FROM interactions GROUP BY severity"
        ).fetchall()
        severity_breakdown = {r["severity"]: r["cnt"] for r in severity_rows}

        atc_rows = db.execute("""
            SELECT SUBSTR(atc_code, 1, 1) as code, COUNT(*) as cnt
            FROM drugs
            WHERE atc_code IS NOT NULL AND atc_code != ''
            GROUP BY SUBSTR(atc_code, 1, 1)
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()

        top_atc = [
            ATCGroup(
                code=r["code"],
                name=ATC_GROUPS.get(r["code"], "Neznáma"),
                drug_count=r["cnt"],
            )
            for r in atc_rows
        ]

        return DatabaseStats(
            total_drugs=total_drugs,
            total_interactions=total_interactions,
            drugs_with_interactions=drugs_with_interactions,
            severity_breakdown=severity_breakdown,
            top_atc_groups=top_atc,
        )
    finally:
        db.close()


@router.get("/atc", response_model=ATCBrowseResponse)
def browse_atc(code: Optional[str] = Query(None)):
    db = get_db()
    try:
        if not code:
            groups = []
            for c, name in sorted(ATC_GROUPS.items()):
                cnt = db.execute(
                    "SELECT COUNT(*) FROM drugs WHERE atc_code LIKE ?",
                    (f"{c}%",),
                ).fetchone()[0]
                if cnt > 0:
                    groups.append(ATCGroup(code=c, name=name, drug_count=cnt))
            return ATCBrowseResponse(groups=groups, drugs=[])

        drugs = db.execute(
            """
            SELECT id, trade_name, active_substance, atc_code, strength, form
            FROM drugs
            WHERE atc_code LIKE ?
            ORDER BY trade_name
            LIMIT 100
            """,
            (f"{code}%",),
        ).fetchall()

        sub_groups = []
        if len(code) == 1:
            sub_rows = db.execute("""
                SELECT SUBSTR(atc_code, 1, 3) as code, COUNT(*) as cnt
                FROM drugs
                WHERE atc_code LIKE ?
                GROUP BY SUBSTR(atc_code, 1, 3)
                ORDER BY code
            """, (f"{code}%",)).fetchall()
            sub_groups = [
                ATCGroup(code=r["code"], name=r["code"], drug_count=r["cnt"])
                for r in sub_rows
            ]

        return ATCBrowseResponse(
            groups=sub_groups,
            drugs=[Drug(**dict(r)) for r in drugs],
        )
    finally:
        db.close()


@router.get("/{drug_id}", response_model=DrugDetail)
def get_drug(drug_id: int):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, trade_name, active_substance, atc_code, strength, form, sukl_code FROM drugs WHERE id = ?",
            (drug_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Drug not found")

        drug = dict(row)
        substance = drug["active_substance"].lower()

        # Count interactions for this substance
        interaction_count = db.execute("""
            SELECT COUNT(*) FROM interactions
            WHERE LOWER(drug_a) = ? OR LOWER(drug_b) = ?
        """, (substance, substance)).fetchone()[0]

        # Find related drugs (same ATC prefix)
        related = []
        if drug["atc_code"] and len(drug["atc_code"]) >= 5:
            atc_prefix = drug["atc_code"][:5]
            related_rows = db.execute("""
                SELECT id, trade_name, active_substance, atc_code, strength, form
                FROM drugs
                WHERE atc_code LIKE ? AND id != ?
                ORDER BY trade_name
                LIMIT 10
            """, (f"{atc_prefix}%", drug_id)).fetchall()
            related = [Drug(**dict(r)) for r in related_rows]

        atc_group = None
        if drug["atc_code"]:
            atc_group = ATC_GROUPS.get(drug["atc_code"][0])

        return DrugDetail(
            **{k: v for k, v in drug.items()},
            atc_group=atc_group,
            interaction_count=interaction_count,
            related_drugs=related,
        )
    finally:
        db.close()


@router.get("/{drug_id}/alternatives", response_model=ResolverResponse)
def get_alternatives(drug_id: int, context_ids: str = Query("", description="Comma-separated drug IDs for context")):
    """Find alternative drugs that would cause fewer interactions with the patient's other medications."""
    db = get_db()
    try:
        target_row = db.execute(
            "SELECT id, trade_name, active_substance, atc_code, strength, form FROM drugs WHERE id = ?",
            (drug_id,),
        ).fetchone()
        if not target_row:
            raise HTTPException(status_code=404, detail="Drug not found")

        target = dict(target_row)
        target_substance = target["active_substance"].lower()

        # Parse context drug IDs
        context_drug_ids = []
        if context_ids:
            context_drug_ids = [int(x.strip()) for x in context_ids.split(",") if x.strip().isdigit()]
        context_drug_ids = [cid for cid in context_drug_ids if cid != drug_id]

        # Get context drugs
        context_drugs = []
        if context_drug_ids:
            placeholders = ",".join("?" * len(context_drug_ids))
            context_drugs = db.execute(
                f"SELECT id, trade_name, active_substance FROM drugs WHERE id IN ({placeholders})",
                context_drug_ids,
            ).fetchall()
            context_drugs = [dict(r) for r in context_drugs]

        # Count original interactions
        original_count = 0
        for cd in context_drugs:
            if _has_interaction(db, target_substance, cd["active_substance"].lower()):
                original_count += 1

        # Find alternative drugs in the same ATC group
        alternatives = []
        if target["atc_code"] and len(target["atc_code"]) >= 4:
            atc_prefix = target["atc_code"][:4]
            alt_rows = db.execute("""
                SELECT id, trade_name, active_substance, atc_code, strength, form
                FROM drugs
                WHERE atc_code LIKE ? AND id != ? AND LOWER(active_substance) != ?
                GROUP BY LOWER(active_substance)
                ORDER BY trade_name
                LIMIT 20
            """, (f"{atc_prefix}%", drug_id, target_substance)).fetchall()

            for alt_row in alt_rows:
                alt = dict(alt_row)
                alt_substance = alt["active_substance"].lower()

                # Count interactions of this alternative with context drugs
                alt_interaction_count = 0
                for cd in context_drugs:
                    if _has_interaction(db, alt_substance, cd["active_substance"].lower()):
                        alt_interaction_count += 1

                interactions_avoided = original_count - alt_interaction_count
                if interactions_avoided > 0:
                    alternatives.append(
                        AlternativeSuggestion(
                            original_drug=Drug(**target),
                            alternative=Drug(**alt),
                            reason=f"Menej interakcií: {alt_interaction_count} vs {original_count} s ostatnými liekmi pacienta",
                            interactions_avoided=interactions_avoided,
                        )
                    )

            alternatives.sort(key=lambda x: x.interactions_avoided, reverse=True)

        return ResolverResponse(
            suggestions=alternatives[:5],
            original_interaction_count=original_count,
        )
    finally:
        db.close()


def _has_interaction(db, substance_a: str, substance_b: str) -> bool:
    """Check if two substances have any interaction."""
    subs_a = [s.strip().lower() for s in substance_a.split(",")]
    subs_b = [s.strip().lower() for s in substance_b.split(",")]

    for sa in subs_a:
        for sb in subs_b:
            if sa == sb:
                continue
            row = db.execute(
                """
                SELECT 1 FROM interactions
                WHERE (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                   OR (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                LIMIT 1
                """,
                (sa, sb, sb, sa),
            ).fetchone()
            if row:
                return True
    return False
