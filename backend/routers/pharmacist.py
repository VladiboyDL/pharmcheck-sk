"""AI Pharmacist conversational endpoint."""
from __future__ import annotations

import json
import logging
import os
import re
from itertools import combinations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..ai_checker import check_interaction_ai, ANTHROPIC_API_KEY
from ..database import get_db
from ..models import (
    PharmacistChatRequest,
    PharmacistChatResponse,
    PharmacistDrug,
    PharmacistInteraction,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pharmacist", tags=["pharmacist"])

PHARMACIST_SYSTEM = """Si AI lekárnik v slovenskej lekárni. Tvoje meno je PharmBot.

Tvoja úloha:
1. Privítať zákazníka a opýtať sa na jeho lieky
2. Keď zákazník uvedie lieky, identifikuješ ich a skontrolujeteš interakcie
3. Vysvetlíš výsledky zrozumiteľným jazykom pre laika/pacienta
4. Poskytuješ odporúčania

Pravidlá:
- Hovor po slovensky, priateľsky ale profesionálne
- Používaj jednoduché vysvetlenia, vyhýbaj sa odborným termínom pokiaľ možno
- Vždy zdôrazni, že tvoje rady nenahrádzajú konzultáciu s lekárom alebo lekárnikom
- Ak nájdeš závažnú interakciu, buď priamy ale pokojný — nevyvolávaj paniku
- Pýtaj sa na alergie a ďalšie lieky
- Odpovedaj stručne (2-5 viet), nie dlhé eseje
- Nepoužívaj markdown formátovanie (hviezdičky, pomlčky na odrážky). Píš čistý text.
- Ak zákazník chce len poradiť alebo sa opýtať na niečo, odpovedz normálne ako lekárnik

Keď ti dám KONTEXT s výsledkami kontroly interakcií, použi tieto informácie vo svojej odpovedi.
Neopakuj ich doslovne — spracuj ich ľudsky a zrozumiteľne pre pacienta."""

# Words to skip during drug name extraction
SKIP_WORDS = frozenset({
    "beriem", "berem", "uzivam", "užívam", "mam", "mám", "som", "prosim", "prosím",
    "dobry", "dobrý", "den", "deň", "ahoj", "zdravim", "zdravím", "dakujem", "ďakujem",
    "chcem", "chcel", "chcela", "vediet", "vedieť", "poradit", "poradiť", "liek", "lieky",
    "tieto", "tiež", "este", "ešte", "asi", "kde", "ako", "pre", "pri", "nad", "pod",
    "alebo", "ale", "ked", "keď", "tak", "potom", "preto", "lebo", "pretože", "nie",
    "ano", "hej", "dobre", "dnes", "denne", "ráno", "večer", "raz", "dva", "tri",
    "stále", "nové", "novy", "nová", "starý", "starší", "bolest", "bolesť", "hlava",
    "brucho", "doktor", "lekár", "lekáreň", "predpísal", "predpisal", "recept", "recepty",
    "nech", "budem", "bude", "boli", "sú", "toto", "tato", "tieto", "aky", "aký",
    "kontrolu", "kontrola", "skontrolovat", "skontrolovať", "interakcie", "interakciu",
    "vdaka", "vďaka", "dobré", "zlé", "možné", "dať", "daj", "skúsiť", "skús",
    "pán", "pani", "slečna", "môže", "môžem", "môžete", "mohli", "mohol", "mohla",
    "bol", "bola", "bolo", "byť", "nejaký", "nejaké", "nejakú", "teda", "vlastne",
    "inak", "okrem", "okej", "dobre", "super", "fajn", "ďalšie", "ďalší", "este",
    "lekárnik", "lekárnikovi", "lekárke", "liekov", "tablety", "tabliet", "tabletky",
    "kapsuly", "kvapky", "mastí", "krém", "sirup", "injekcie", "prášok", "prášky",
    "predpis", "predpísané", "predpísaný", "doporučil", "odporučil",
    "ráno", "obed", "večer", "noc", "spať", "jedlo", "jedlom", "pred", "potom",
    "denne", "týždenne", "mesačne", "pravidelne", "občas", "niekedy",
    "skontroluj", "skontrolujte", "over", "overte", "zisti", "zistite",
    "vitajte", "zdravím", "nazdar", "servus", "čaute", "čau",
})


def _find_drugs_in_message(db, message: str) -> list[dict]:
    """Find drugs mentioned in user message by searching each word against DB."""
    words = re.findall(r"\b[\w]{3,}\b", message)

    found = []
    seen_ids = set()

    for word in words:
        if word.lower() in SKIP_WORDS:
            continue
        if len(word) < 4:
            continue

        # Try FTS first with quoted exact match
        result = None
        try:
            result = db.execute(
                """SELECT drugs.id, drugs.trade_name, drugs.active_substance, drugs.atc_code
                FROM drugs_fts JOIN drugs ON drugs.id = drugs_fts.rowid
                WHERE drugs_fts MATCH ?
                LIMIT 1""",
                (f'"{word}"',),
            ).fetchone()
        except Exception:
            pass

        if not result:
            # LIKE fallback — match beginning of trade name or substance
            result = db.execute(
                """SELECT id, trade_name, active_substance, atc_code FROM drugs
                WHERE LOWER(trade_name) LIKE ? OR LOWER(active_substance) LIKE ?
                ORDER BY LENGTH(trade_name)
                LIMIT 1""",
                (f"{word.lower()}%", f"{word.lower()}%"),
            ).fetchone()

        if result and result["id"] not in seen_ids:
            found.append(dict(result))
            seen_ids.add(result["id"])

    return found


def _check_pair_db(db, substance_a: str, substance_b: str) -> dict | None:
    """Check interaction between two substances in DDInter DB."""
    subs_a = [s.strip().lower() for s in substance_a.split(",")]
    subs_b = [s.strip().lower() for s in substance_b.split(",")]

    best = None
    severity_rank = {"Závažná": 0, "Stredná": 1, "Mierna": 2}

    for sa in subs_a:
        for sb in subs_b:
            if sa == sb:
                continue
            row = db.execute(
                """SELECT severity, mechanism, management, alternatives
                FROM interactions
                WHERE (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                   OR (LOWER(drug_a) = ? AND LOWER(drug_b) = ?)
                LIMIT 1""",
                (sa, sb, sb, sa),
            ).fetchone()
            if row:
                r = dict(row)
                if best is None or severity_rank.get(r["severity"], 9) < severity_rank.get(
                    best["severity"], 9
                ):
                    best = r
    return best


@router.post("/chat", response_model=PharmacistChatResponse)
def chat(req: PharmacistChatRequest):
    """Chat with AI pharmacist."""
    use_ai = bool(ANTHROPIC_API_KEY)

    db = get_db()
    try:
        # ── 1. Find drugs in the message ──
        identified_drugs = _find_drugs_in_message(db, req.message)

        # Merge with previously known drugs from context
        all_drugs = list(identified_drugs)
        for prev in req.context_drugs or []:
            if not any(d["id"] == prev.id for d in all_drugs):
                all_drugs.append(
                    {"id": prev.id, "trade_name": prev.trade_name, "active_substance": prev.active_substance}
                )

        # ── 2. Check interactions if 2+ drugs ──
        interactions_found: list[dict] = []
        if len(all_drugs) >= 2:
            for da, db_drug in combinations(all_drugs, 2):
                interaction = _check_pair_db(db, da["active_substance"], db_drug["active_substance"])

                if not interaction and use_ai:
                    ai_result = check_interaction_ai(
                        da["active_substance"], db_drug["active_substance"], db
                    )
                    if ai_result and ai_result.get("has_interaction"):
                        interaction = ai_result

                if interaction:
                    interactions_found.append(
                        {
                            "drug_a": da["trade_name"],
                            "drug_b": db_drug["trade_name"],
                            "severity": interaction.get("severity") or "Neznáma",
                            "mechanism": interaction.get("mechanism") or "",
                            "management": interaction.get("management") or "",
                        }
                    )

        # ── 3. Build context for Claude ──
        context_parts = []
        if identified_drugs:
            context_parts.append(
                "IDENTIFIKOVANÉ LIEKY V DATABÁZE:\n"
                + "\n".join(f"- {d['trade_name']} ({d['active_substance']})" for d in identified_drugs)
            )

        if interactions_found:
            context_parts.append(
                "VÝSLEDKY KONTROLY INTERAKCIÍ:\n"
                + "\n".join(
                    f"- {i['drug_a']} + {i['drug_b']}: závažnosť={i['severity']}. "
                    f"Mechanizmus: {i['mechanism']}. Odporúčanie: {i['management']}"
                    for i in interactions_found
                )
            )
        elif len(all_drugs) >= 2:
            names = ", ".join(d["trade_name"] for d in all_drugs)
            context_parts.append(f"VÝSLEDKY: Medzi liekmi ({names}) neboli nájdené žiadne klinicky významné interakcie.")

        # ── 4. Generate response ──
        if use_ai:
            # Build messages for Claude
            messages = []
            for msg in req.history or []:
                messages.append({"role": msg.role, "content": msg.content})

            user_content = req.message
            if context_parts:
                user_content = (
                    "[KONTEXT — použi tieto dáta vo svojej odpovedi]\n"
                    + "\n".join(context_parts)
                    + f"\n\n[SPRÁVA ZÁKAZNÍKA]\n{req.message}"
                )

            messages.append({"role": "user", "content": user_content})

            import anthropic

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=PHARMACIST_SYSTEM,
                messages=messages,
            )

            reply = response.content[0].text.strip()
        else:
            # Fallback template when no API key
            if interactions_found:
                lines = [f"Našiel som {len(interactions_found)} interakcii medzi vašimi liekmi:"]
                for i in interactions_found:
                    lines.append(f"{i['drug_a']} + {i['drug_b']}: {i['severity']}. {i['mechanism']}")
                reply = " ".join(lines)
            elif identified_drugs:
                names = ", ".join(d["trade_name"] for d in identified_drugs)
                reply = f"Identifikoval som tieto lieky: {names}. Medzi nimi som nenašiel žiadne interakcie v databáze."
            else:
                reply = "Prepáčte, nepodarilo sa mi identifikovať lieky vo vašej správe. Skúste napísať presné názvy liekov."

        return PharmacistChatResponse(
            message=reply,
            identified_drugs=[
                PharmacistDrug(id=d["id"], trade_name=d["trade_name"], active_substance=d["active_substance"])
                for d in identified_drugs
            ],
            interactions=[
                PharmacistInteraction(
                    drug_a=i["drug_a"],
                    drug_b=i["drug_b"],
                    severity=i["severity"],
                    mechanism=i["mechanism"],
                    management=i["management"],
                )
                for i in interactions_found
            ],
        )

    except Exception as e:
        logger.error(f"Pharmacist chat error: {e}")
        return PharmacistChatResponse(
            message="Prepáčte, nastala chyba. Skúste to prosím znova.",
            identified_drugs=[],
            interactions=[],
        )
    finally:
        db.close()
