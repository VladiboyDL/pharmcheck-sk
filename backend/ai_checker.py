"""AI-powered drug interaction checker using Claude as a pharmacology knowledge base."""
from __future__ import annotations
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """Si farmakologický expert. Tvoja úloha je posúdiť liekové interakcie medzi dvoma účinnými látkami.

Odpovedaj VÝHRADNE vo formáte JSON. Žiadny iný text.

Ak existuje klinicky významná interakcia, odpovedz:
{
  "has_interaction": true,
  "severity": "Závažná" alebo "Stredná" alebo "Mierna",
  "mechanism": "Stručný popis mechanizmu interakcie po slovensky (1-2 vety)",
  "management": "Odporúčanie pre lekárnika/lekára po slovensky (1-2 vety)",
  "alternatives": "Bezpečnejšie alternatívy ak existujú, po slovensky (1 veta)"
}

Ak interakcia neexistuje alebo nie je klinicky významná:
{
  "has_interaction": false
}

Pravidlá závažnosti:
- Závažná: kontraindikácia, život ohrozujúca interakcia (napr. sérotonínový syndróm, závažné krvácanie, QT predĺženie)
- Stredná: potrebná úprava dávkovania alebo monitorovanie, klinicky významná
- Mierna: minimálny klinický význam, informačný charakter"""


def check_interaction_ai(substance_a: str, substance_b: str, db=None) -> Optional[dict]:
    """Check interaction between two substances using AI.

    Returns dict with interaction data or None if no API key or error.
    Caches results in ai_interaction_cache table.
    """
    if not ANTHROPIC_API_KEY:
        return None

    # Normalize for cache lookup (alphabetical order)
    sa, sb = sorted([substance_a.lower().strip(), substance_b.lower().strip()])

    # Check cache first
    if db:
        cached = db.execute(
            """SELECT has_interaction, severity, mechanism, management, alternatives
            FROM ai_interaction_cache
            WHERE substance_a = ? AND substance_b = ?""",
            (sa, sb),
        ).fetchone()
        if cached:
            if not cached["has_interaction"]:
                return {"has_interaction": False}
            return {
                "has_interaction": True,
                "severity": cached["severity"],
                "mechanism": cached["mechanism"],
                "management": cached["management"],
                "alternatives": cached["alternatives"],
                "source": "ai_cached",
            }

    # Call Claude
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Posúď interakciu medzi: {substance_a} a {substance_b}",
            }],
        )

        text = response.content[0].text.strip()
        # Parse JSON from response
        result = json.loads(text)

        # Cache the result
        if db:
            try:
                db.execute(
                    """INSERT OR REPLACE INTO ai_interaction_cache
                    (substance_a, substance_b, has_interaction, severity, mechanism, management, alternatives)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sa, sb,
                        1 if result.get("has_interaction") else 0,
                        result.get("severity"),
                        result.get("mechanism"),
                        result.get("management"),
                        result.get("alternatives"),
                    ),
                )
                db.commit()
            except Exception:
                pass  # Cache write failure is non-critical

        if result.get("has_interaction"):
            result["source"] = "ai"
            return result

        return {"has_interaction": False}

    except json.JSONDecodeError:
        logger.warning(f"AI returned invalid JSON for {substance_a} <-> {substance_b}")
        return None
    except Exception as e:
        logger.warning(f"AI check failed for {substance_a} <-> {substance_b}: {e}")
        return None


def check_interactions_batch(pairs: list[tuple[str, str]], db=None) -> dict:
    """Check multiple substance pairs. Returns dict keyed by (sa, sb) tuples."""
    results = {}
    for sa, sb in pairs:
        result = check_interaction_ai(sa, sb, db)
        if result:
            key = (sa.lower().strip(), sb.lower().strip())
            results[key] = result
    return results
