"""eRecept parsing — turns free-text prescription lines into structured, dosed items.

Handles the notation Slovak prescriptions actually use:
    WARFARIN ORION 5 mg tbl        1-0-0
    NUROFEN 400 mg                 1-1-1
    METHOTREXAT EBEWE 10 mg        1-0-0
    Siofor 850 mg, 2x denne
    Euthyrox 50 ug, 1/2-0-0
"""
from __future__ import annotations

import re
import unicodedata

# 1-0-0 / 1-1-1 / 1-0-1-0 / 0,5-0-1 / 1/2-0-0
SCHEDULE_RE = re.compile(
    r"(?<![\w.,])(\d+(?:[.,]\d+)?|\d/\d)\s*-\s*(\d+(?:[.,]\d+)?|\d/\d)\s*-\s*(\d+(?:[.,]\d+)?|\d/\d)"
    r"(?:\s*-\s*(\d+(?:[.,]\d+)?|\d/\d))?(?![\w.,])"
)
# 2x denne / 3 x denne / 1x týždenne
TIMES_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(denne|za\s*de[nň]|t[ýy]ždenne|za\s*t[ýy]žde[nň])", re.I)
# 5 mg / 850mg / 50 ug / 0,5 g / 1000 IU
STRENGTH_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(mg|g|µg|ug|mcg|ml|iu|m\.j\.)\b", re.I
)

UNIT_TO_MG = {"mg": 1.0, "g": 1000.0, "µg": 0.001, "ug": 0.001, "mcg": 0.001}

NOISE = re.compile(
    r"\b(tbl|tablet[ay]?|tabliet|cps|kapsul[ay]|cps\.|por|p\.o\.|susp|sir|sirup|"
    r"gtt|kvapky|ung|krém|krem|mast|inj|amp|sol|film|obalen[eé]|potahovan[eé]|"
    r"ret|sr|xr|forte|neo|plus|denne|po\s*jedle|nala[čc]no|r[áa]no|ve[čc]er|"
    r"\d+\s*ks|balenie)\b\.?",
    re.I,
)


def _num(token: str | None) -> float:
    if not token:
        return 0.0
    token = token.strip()
    if "/" in token:
        a, b = token.split("/", 1)
        try:
            return float(a) / float(b)
        except (ValueError, ZeroDivisionError):
            return 0.0
    try:
        return float(token.replace(",", "."))
    except ValueError:
        return 0.0


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def parse_line(line: str) -> dict | None:
    """Parse one prescription line into {query, strength_mg, units_per_day, weekly, raw}."""
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None

    working = raw

    # ── Dosing schedule ────────────────────────────────────────────────────────
    units_per_day = None
    weekly = False
    frequency_per_day = None

    m = SCHEDULE_RE.search(working)
    if m:
        parts = [_num(g) for g in m.groups() if g is not None]
        units_per_day = sum(parts)
        frequency_per_day = sum(1 for p in parts if p > 0)
        working = working[: m.start()] + " " + working[m.end() :]
    else:
        t = TIMES_RE.search(working)
        if t:
            n = _num(t.group(1))
            period = _strip_accents(t.group(2).lower())
            if "tyzden" in period:
                weekly = True
                units_per_day = n / 7.0
                frequency_per_day = 0
            else:
                units_per_day = n
                frequency_per_day = int(n) if n >= 1 else 1
            working = working[: t.start()] + " " + working[t.end() :]

    # ── Strength ───────────────────────────────────────────────────────────────
    strength_mg = None
    s = STRENGTH_RE.search(working)
    if s:
        value, unit = _num(s.group(1)), s.group(2).lower()
        if unit in UNIT_TO_MG:
            strength_mg = value * UNIT_TO_MG[unit]
        working = working[: s.start()] + " " + working[s.end() :]

    # ── Remaining text is the product name ─────────────────────────────────────
    name = NOISE.sub(" ", working)
    name = re.sub(r"[,;:–—\-•|/()]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .,")

    if not name:
        return None

    return {
        "raw": raw,
        "query": name,
        "strength_mg": strength_mg,
        "units_per_day": units_per_day,
        "frequency_per_day": frequency_per_day,
        "weekly": weekly,
    }


def parse_prescription(text: str) -> list[dict]:
    out = []
    for line in (text or "").splitlines():
        parsed = parse_line(line)
        if parsed:
            out.append(parsed)
    return out


def _registry_strength_mg(row: dict) -> float | None:
    """Parse the registry `strength` column into milligrams, if possible."""
    for field in (row.get("strength"), row.get("trade_name")):
        if not field:
            continue
        m = STRENGTH_RE.search(str(field))
        if m and m.group(2).lower() in UNIT_TO_MG:
            return _num(m.group(1)) * UNIT_TO_MG[m.group(2).lower()]
    return None


def _candidates(db, tokens: list[str]) -> list[dict]:
    """Collect candidate registry rows, widest useful net first."""
    seen: dict[int, dict] = {}

    def add(rows):
        for r in rows:
            d = dict(r)
            seen.setdefault(d["id"], d)

    cols = ("SELECT drugs.id, drugs.trade_name, drugs.active_substance, drugs.atc_code, "
            "drugs.strength, drugs.form FROM drugs_fts JOIN drugs ON drugs.id = drugs_fts.rowid")

    # All tokens present
    if len(tokens) > 1:
        try:
            add(db.execute(f"{cols} WHERE drugs_fts MATCH ? LIMIT 40",
                           (" AND ".join(f'"{t}"' for t in tokens),)).fetchall())
        except Exception:
            pass

    # Leading token (the brand name in practice)
    try:
        add(db.execute(f"{cols} WHERE drugs_fts MATCH ? LIMIT 40", (f'"{tokens[0]}"',)).fetchall())
    except Exception:
        pass

    if not seen:
        add(db.execute(
            """SELECT id, trade_name, active_substance, atc_code, strength, form FROM drugs
               WHERE LOWER(trade_name) LIKE ? OR LOWER(active_substance) LIKE ?
               ORDER BY LENGTH(trade_name) LIMIT 40""",
            (f"{tokens[0].lower()}%", f"{tokens[0].lower()}%"),
        ).fetchall())

    return list(seen.values())


def match_drug(db, query: str, strength_mg: float | None = None) -> dict | None:
    """Resolve a parsed product name to a registry row.

    When the prescription states a strength, a row with the same strength always wins —
    a 5 mg script must not resolve to the 3 mg pack.
    """
    q = query.strip()
    if not q:
        return None

    tokens = [t for t in re.findall(r"[\w]{3,}", q) if not t.isdigit()]
    if not tokens:
        return None

    candidates = _candidates(db, tokens)
    if not candidates:
        return None

    lead = tokens[0].lower()
    all_tokens = [t.lower() for t in tokens]

    def score(row: dict) -> tuple:
        name = (row.get("trade_name") or "").lower()
        missing = sum(1 for t in all_tokens if t not in name)
        rs = _registry_strength_mg(row)
        strength_match = 0
        if strength_mg is not None and rs is not None:
            if abs(rs - strength_mg) < 1e-6:
                strength_match = 0        # exact — best
            else:
                strength_match = 2        # wrong strength — worst
        else:
            strength_match = 1            # unknown — neutral
        return (
            strength_match,
            missing,                              # brand qualifier must survive
            0 if name.startswith(lead) else 1,
            len(name),
        )

    return sorted(candidates, key=score)[0]


def resolve(db, text: str) -> tuple[list[dict], list[str]]:
    """Parse and resolve a prescription. Returns (items, unresolved_lines)."""
    items: list[dict] = []
    unresolved: list[str] = []

    for parsed in parse_prescription(text):
        drug = match_drug(db, parsed["query"], parsed["strength_mg"])
        if not drug:
            unresolved.append(parsed["raw"])
            continue

        # Prefer the strength written on the prescription; fall back to the registry.
        strength = parsed["strength_mg"]
        if strength is None and drug.get("strength"):
            s = STRENGTH_RE.search(str(drug["strength"]))
            if s and s.group(2).lower() in UNIT_TO_MG:
                strength = _num(s.group(1)) * UNIT_TO_MG[s.group(2).lower()]

        units = parsed["units_per_day"]
        daily_dose_mg = round(strength * units, 4) if (strength and units) else None
        weekly_dose_mg = round(daily_dose_mg * 7, 4) if (daily_dose_mg and parsed["weekly"]) else None

        items.append(
            {
                "id": drug["id"],
                "trade_name": drug["trade_name"],
                "active_substance": drug["active_substance"],
                "atc_code": drug.get("atc_code"),
                "form": drug.get("form"),
                "registry_strength": drug.get("strength"),
                "raw_line": parsed["raw"],
                "strength_mg": strength,
                "units_per_day": units,
                "frequency_per_day": parsed["frequency_per_day"],
                "weekly": parsed["weekly"],
                "daily_dose_mg": daily_dose_mg,
                "weekly_dose_mg": weekly_dose_mg,
            }
        )

    return items, unresolved
