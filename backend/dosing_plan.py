"""Turning a prescription into instructions a patient can actually follow.

The registry says "1-0-1". The patient needs "ráno jedna tableta, večer jedna
tableta, najlepšie s jedlom". Everything here is derived from what the parser
already extracted, plus per-substance timing advice that changes whether the drug
works at all — levothyroxine with breakfast is a wasted dose, and a fluoroquinolone
with a calcium supplement barely absorbs.
"""
from __future__ import annotations

from . import clinical

SLOT_NAMES = ["ráno", "na obed", "večer", "na noc"]

# How to take it, in the patient's language.
#
# Advice here must never contradict the schedule on the prescription — that is the
# prescriber's call and the patient will notice the conflict immediately. So these
# speak about food, water, posture and what to keep apart from what, and about the
# clock only where the prescription is silent.
TIMING: dict[str, dict] = {
    "levothyroxine": {
        "when": "Nalačno, aspoň 30 minút pred jedlom.",
        "avoid": "Vápnik, horčík, železo a kávu užite až o 4 hodiny neskôr — inak sa liek nevstrebe.",
    },
    "omeprazole": {"when": "30 minút pred jedlom.", "avoid": ""},
    "pantoprazole": {"when": "30 minút pred jedlom.", "avoid": ""},
    "esomeprazole": {"when": "30 minút pred jedlom.", "avoid": ""},
    "metformin": {
        "when": "Počas jedla alebo tesne po ňom.",
        "avoid": "Zmierni to žalúdočné ťažkosti, ktoré liek na začiatku často spôsobuje.",
    },
    "ibuprofen": {"when": "Po jedle, nikdy nalačno.", "avoid": "Nekombinujte s ďalším liekom proti bolesti zo skupiny NSAID."},
    "diclofenac": {"when": "Po jedle, nikdy nalačno.", "avoid": "Nekombinujte s ibuprofenom ani aspirínom proti bolesti."},
    "naproxen": {"when": "Po jedle.", "avoid": ""},
    "acetylsalicylic acid": {"when": "Po jedle, zapiť plným pohárom vody.", "avoid": ""},
    "prednisone": {"when": "Po jedle, nikdy nalačno.", "avoid": "Nevysadzujte náhle, dávka sa znižuje postupne podľa lekára."},
    "warfarin": {
        "when": "Každý deň v rovnakom čase podľa rozpisu.",
        "avoid": "Jedzte približne rovnaké množstvo listovej zeleniny — dôležitá je stálosť, nie vynechávanie.",
    },
    "simvastatin": {"when": "Zapite vodou, držte sa času uvedeného v rozpise.", "avoid": "Vyhnite sa grepu a grepovej šťave."},
    "atorvastatin": {"when": "Vždy v rovnakom čase podľa rozpisu.", "avoid": "Vyhnite sa grepovej šťave."},
    "rosuvastatin": {"when": "Vždy v rovnakom čase podľa rozpisu.", "avoid": ""},
    "furosemide": {
        "when": "Poslednú dávku dňa užite najneskôr popoludní.",
        "avoid": "Neskorá dávka vás bude v noci budiť na toaletu.",
    },
    "ciprofloxacin": {
        "when": "S dostatkom vody.",
        "avoid": "Mliečne výrobky, vápnik, horčík a železo až 2 hodiny pred alebo po užití.",
    },
    "amoxicillin": {"when": "V pravidelných intervaloch, aj keď sa už cítite lepšie.", "avoid": "Dobrať celé balenie podľa lekára."},
    "clarithromycin": {"when": "S jedlom.", "avoid": ""},
    "alendronic acid": {
        "when": "Nalačno, zapiť veľkým pohárom čistej vody.",
        "avoid": "Pol hodiny po užití neležte a nič nejedzte.",
    },
    "methotrexate": {
        "when": "RAZ TÝŽDENNE, vždy v ten istý deň. Nikdy nie denne.",
        "avoid": "Kyselinu listovú užívajte v iný deň, než metotrexát.",
    },
    "tramadol": {"when": "Len keď bolesť skutočne je, nie preventívne.", "avoid": "Nekombinujte s alkoholom — zosilní útlm."},
    "zolpidem": {"when": "Až keď ležíte v posteli, nie skôr.", "avoid": "Počítajte s aspoň 7 hodinami spánku, inak budete ráno spomalení."},
    "sertraline": {"when": "S jedlom.", "avoid": "Účinok sa prejaví až po 2–4 týždňoch, nevysadzujte skôr."},
    "escitalopram": {"when": "Vždy v rovnakom čase podľa rozpisu.", "avoid": "Nevysadzujte náhle."},
    "ramipril": {"when": "Zapite pohárom vody.", "avoid": "Prvé dni môže spôsobiť závrat pri rýchlom postavení."},
    "perindopril": {"when": "Nalačno, pred jedlom.", "avoid": ""},
    "amlodipine": {"when": "Vždy v rovnakom čase podľa rozpisu.", "avoid": "Môže spôsobiť opuchy členkov — povedzte o tom lekárovi."},
    "bisoprolol": {"when": "Zapite vodou, s jedlom aj bez.", "avoid": "Nevysadzujte náhle."},
    "paracetamol": {"when": "Kedykoľvek, s jedlom aj bez.", "avoid": "Pozor na kombinované prípravky proti chrípke — často už paracetamol obsahujú."},
}


def _schedule_text(item: dict) -> str:
    """1-0-1 becomes a sentence."""
    if item.get("weekly"):
        return "Raz týždenne, vždy v ten istý deň."

    units = item.get("units_per_day")
    freq = item.get("frequency_per_day")
    if not units:
        return "Podľa pokynov lekára."

    # Reconstruct the slots from the raw line, which still carries the notation.
    raw = item.get("raw_line") or ""
    import re

    m = re.search(r"(\d+(?:[.,]\d+)?|\d/\d)\s*-\s*(\d+(?:[.,]\d+)?|\d/\d)\s*-\s*(\d+(?:[.,]\d+)?|\d/\d)"
                  r"(?:\s*-\s*(\d+(?:[.,]\d+)?|\d/\d))?", raw)
    if m:
        parts = [g for g in m.groups() if g is not None]
        pieces = []
        for slot, value in zip(SLOT_NAMES, parts):
            amount = _amount_text(value)
            if amount:
                pieces.append(f"{slot} {amount}")
        if pieces:
            return (", ".join(pieces)).capitalize() + "."

    if freq:
        return f"{int(units)}× denne, rozdelene počas dňa." if units >= 2 else "Raz denne."
    return "Podľa pokynov lekára."


def _amount_text(token: str) -> str:
    """'1' -> 'jedna tableta', '0' -> '', '1/2' -> 'pol tablety'."""
    token = token.strip()
    if token in ("0", "0.0", "0,0"):
        return ""
    if token == "1/2":
        return "pol tablety"
    if token == "1/4":
        return "štvrť tablety"
    try:
        value = float(token.replace(",", "."))
    except ValueError:
        return token
    if value == 0:
        return ""
    if value == 0.5:
        return "pol tablety"
    if value == 1:
        return "jedna tableta"
    if value == 2:
        return "dve tablety"
    if value == 3:
        return "tri tablety"
    return f"{value:g} tablety"


def build(items: list[dict]) -> list[dict]:
    """A patient-facing plan for everything actually going home."""
    plan = []
    for item in items:
        if item.get("source") == "interview" or item.get("status") == "verify":
            continue
        substance = clinical.normalise(item.get("active_substance", ""))
        advice = TIMING.get(substance, {})
        plan.append(
            {
                "trade_name": item["trade_name"],
                "substance": item.get("active_substance"),
                "schedule": _schedule_text(item),
                "daily_total": (
                    f"{item['daily_dose_mg']:g} mg denne" if item.get("daily_dose_mg") else ""
                ),
                "when": advice.get("when", ""),
                "avoid": advice.get("avoid", ""),
            }
        )
    return plan


def as_text(patient_name: str, plan: list[dict], advisories: list[dict]) -> str:
    """The same plan as plain text — for a QR code, an email body, or a printed slip."""
    lines = [f"Rozpis liekov — {patient_name or 'pacient'}", ""]
    for entry in plan:
        lines.append(f"{entry['trade_name']}")
        lines.append(f"  Kedy: {entry['schedule']}")
        if entry["when"]:
            lines.append(f"  {entry['when']}")
        if entry["avoid"]:
            lines.append(f"  Pozor: {entry['avoid']}")
        lines.append("")
    if advisories:
        lines.append("Na čo sa spýtať lekára:")
        for a in advisories:
            lines.append(f"  - {a}")
        lines.append("")
    lines.append("Vygenerované systémom AvatarAI Dispense. Nenahrádza pokyny lekára.")
    return "\n".join(lines)


# ── Taking it off the kiosk ───────────────────────────────────────────────────

SLOT_TIMES = {"ráno": "080000", "na obed": "120000", "večer": "200000", "na noc": "220000"}


def _ascii_slug(text: str) -> str:
    """iCalendar UIDs must stay ASCII."""
    import unicodedata

    stripped = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return "".join(c for c in stripped if c.isalnum()).lower()


def _slots(plan: list[dict]) -> dict[str, list[str]]:
    """Group the plan by time of day, so a reminder covers everything due at once."""
    buckets: dict[str, list[str]] = {}
    for entry in plan:
        schedule = (entry.get("schedule") or "").lower()
        for slot in SLOT_TIMES:
            if slot in schedule:
                amount = ""
                for part in schedule.split(","):
                    if slot in part:
                        amount = part.replace(slot, "").strip(" .")
                        break
                label = f"{entry['trade_name']}" + (f" — {amount}" if amount else "")
                buckets.setdefault(slot, []).append(label)
    return buckets


def as_icalendar(plan: list[dict], start_date: str, audit_id: str) -> str:
    """Daily reminders the phone actually keeps.

    One recurring event per time of day rather than one per medicine, so a patient on
    seven drugs gets two or three notifications a day instead of seven. Times float —
    no timezone — so 8:00 stays 8:00 wherever the patient is.
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AvatarAI Dispense//SK//",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for slot, medicines in _slots(plan).items():
        time_part = SLOT_TIMES[slot]
        description = "\\n".join(medicines)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{audit_id}-{_ascii_slug(slot)}@avatarai",
            f"DTSTAMP:{start_date}T{time_part}Z",
            f"DTSTART:{start_date}T{time_part}",
            "DURATION:PT15M",
            "RRULE:FREQ=DAILY",
            f"SUMMARY:Lieky — {slot}",
            f"DESCRIPTION:{description}",
            "BEGIN:VALARM",
            "TRIGGER:PT0M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:Lieky — {slot}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
