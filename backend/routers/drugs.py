from fastapi import APIRouter, Query
from ..database import get_db
from ..models import Drug, DrugSearchResult

router = APIRouter(prefix="/api/drugs", tags=["drugs"])


@router.get("/search", response_model=DrugSearchResult)
def search_drugs(q: str = Query(..., min_length=1)):
    db = get_db()
    try:
        # FTS5 search with prefix matching
        fts_query = q.replace('"', '""') + "*"
        rows = db.execute(
            """
            SELECT d.id, d.trade_name, d.active_substance, d.atc_code, d.strength, d.form
            FROM drugs_fts fts
            JOIN drugs d ON d.id = fts.rowid
            WHERE drugs_fts MATCH ?
            ORDER BY rank
            LIMIT 10
            """,
            (fts_query,),
        ).fetchall()

        # Fallback to LIKE if FTS returns nothing
        if not rows:
            like_q = f"%{q}%"
            rows = db.execute(
                """
                SELECT id, trade_name, active_substance, atc_code, strength, form
                FROM drugs
                WHERE trade_name LIKE ? OR active_substance LIKE ?
                ORDER BY trade_name
                LIMIT 10
                """,
                (like_q, like_q),
            ).fetchall()

        return DrugSearchResult(results=[Drug(**dict(r)) for r in rows])
    finally:
        db.close()


@router.get("/{drug_id}", response_model=Drug)
def get_drug(drug_id: int):
    db = get_db()
    try:
        row = db.execute(
            "SELECT id, trade_name, active_substance, atc_code, strength, form FROM drugs WHERE id = ?",
            (drug_id,),
        ).fetchone()
        if not row:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Drug not found")
        return Drug(**dict(row))
    finally:
        db.close()
