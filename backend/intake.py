"""Pre-dispense interview — the questions the prescriber never asked.

The prescription is the known part of a patient's exposure. What actually causes
harm at the counter is what is *not* on it: OTC analgesics bought the same morning,
herbal supplements nobody considers medicine, and a second prescriber's script.
This module turns short tap-answers into substances the clinical engine can check
alongside the prescription.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IntakeOption:
    id: str
    label: str
    # Active substances this answer contributes to the checked regimen.
    substances: list[str] = field(default_factory=list)
    icon: str = ""
    # Free-standing risk note, used when the answer has no substance to check.
    note: str = ""
    severity: str = ""          # "critical" | "warning" | "info"
    exclusive: bool = False     # "nič z uvedeného" clears the other options


@dataclass
class IntakeQuestion:
    id: str
    prompt: str
    hint: str
    multi: bool
    options: list[IntakeOption]
    # Questions sharing a group are shown on one screen. Five screens of one question
    # each is a form; two screens of related questions is a conversation.
    group: str = "other"
    short: str = ""          # kiosk phrasing — plainer and shorter than the console's


NONE = IntakeOption(id="none", label="Nič z uvedeného", exclusive=True)

QUESTIONS: list[IntakeQuestion] = [
    IntakeQuestion(
        id="otc_pain",
        prompt="Užívate niečo na bolesť, čo vám lekár nepredpísal?",
        short="Beriete niečo na bolesť?",
        hint="Aj to, čo ste si kúpili v lekárni alebo máte doma v zásobe.",
        group="self_medication",
        multi=True,
        options=[
            IntakeOption("ibuprofen", "Ibalgin, Nurofen, Ibumax", ["ibuprofen"], icon="pill"),
            IntakeOption("paracetamol", "Paralen, Panadol, Coldrex", ["paracetamol"], icon="pill"),
            IntakeOption("aspirin", "Acylpyrín, Aspirín", ["acetylsalicylic acid"], icon="pill"),
            IntakeOption("diclofenac", "Voltaren, Olfen — aj masť", ["diclofenac"], icon="tube"),
            IntakeOption("naproxen", "Aleve, Nalgesin", ["naproxen"], icon="pill"),
            NONE,
        ],
    ),
    IntakeQuestion(
        id="supplements",
        prompt="Beriete výživové doplnky alebo bylinky?",
        short="A doplnky alebo bylinky?",
        hint="Aj čaje a kvapky. Väčšina pacientov ich za lieky nepovažuje.",
        group="self_medication",
        multi=True,
        options=[
            IntakeOption("st_johns_wort", "Ľubovník bodkovaný", ["st john's wort"], icon="leaf"),
            IntakeOption("ginkgo", "Ginkgo biloba", ["ginkgo biloba"], icon="leaf"),
            IntakeOption("fish_oil", "Rybí olej, omega-3", ["omega-3 fatty acids"], icon="drop"),
            IntakeOption(
                "vitamin_k", "Vitamín K, zelené smoothie", [], icon="leaf",
                note="Vitamín K priamo znižuje účinok warfarínu. Dôležitá je stabilita príjmu, nie jeho vynechanie.",
                severity="warning",
            ),
            IntakeOption(
                "calcium_iron", "Vápnik, horčík alebo železo", [], icon="mineral",
                note="Dvojmocné katióny viažu tetracyklíny, fluorochinolóny a levotyroxín. Dodržať odstup aspoň 2 hodiny.",
                severity="info",
            ),
            NONE,
        ],
    ),
    IntakeQuestion(
        id="other_prescriber",
        prompt="Predpísal vám niečo iný lekár za posledné 3 mesiace?",
        short="Boli ste u iného lekára?",
        hint="Špecialista nevidí, čo napísal obvodný lekár, a naopak.",
        group="context",
        multi=False,
        options=[
            IntakeOption(
                "yes", "Áno", [],
                note="Pacient má recepty od viacerých predpisujúcich. Doplniť zoznam a skontrolovať duplicity — "
                     "žiadny z lekárov nevidí kompletnú medikáciu.",
                severity="warning",
            ),
            IntakeOption("no", "Nie", []),
        ],
    ),
    IntakeQuestion(
        id="alcohol",
        prompt="Pijete alkohol pravidelne?",
        short="Pijete alkohol pravidelne?",
        hint="Ovplyvňuje pečeňový metabolizmus aj riziko krvácania.",
        group="context",
        multi=False,
        options=[
            IntakeOption(
                "daily", "Denne alebo takmer denne", [],
                note="Pravidelný alkohol zvyšuje hepatotoxicitu paracetamolu, riziko GIT krvácania pri NSAID "
                     "a rozkolísava INR pri warfaríne.",
                severity="warning",
            ),
            IntakeOption("occasional", "Príležitostne", []),
            IntakeOption("no", "Nepijem", []),
        ],
    ),
    IntakeQuestion(
        id="adherence",
        prompt="Užívate všetky predpísané lieky tak, ako máte?",
        short="Beriete lieky podľa predpisu?",
        hint="Bez výčitiek — vysadené lieky menia interakčný profil.",
        group="context",
        multi=False,
        options=[
            IntakeOption(
                "no", "Niečo som vysadil alebo beriem inak", [],
                note="Pacient neužíva medikáciu podľa predpisu. Zistiť ktorý liek a prečo — "
                     "dávkovanie sa validovalo voči predpisu, nie voči skutočnosti.",
                severity="warning",
            ),
            IntakeOption("yes", "Áno, podľa predpisu", []),
        ],
    ),
]


def questions_for(patient: dict | None) -> list[dict]:
    """Serialise the interview, tailored to what we already know about the patient."""
    out = []
    for q in QUESTIONS:
        # Adherence only matters for someone already on chronic therapy.
        if q.id == "adherence" and not (patient or {}).get("chronic"):
            continue
        out.append(
            {
                "id": q.id,
                "prompt": q.prompt,
                "short": q.short or q.prompt,
                "hint": q.hint,
                "multi": q.multi,
                "group": q.group,
                "options": [
                    {"id": o.id, "label": o.label, "exclusive": o.exclusive, "icon": o.icon}
                    for o in q.options
                ],
            }
        )
    return out


def _option(question_id: str, option_id: str) -> IntakeOption | None:
    for q in QUESTIONS:
        if q.id != question_id:
            continue
        for o in q.options:
            if o.id == option_id:
                return o
    return None


def resolve_answers(answers: dict[str, list[str]]) -> tuple[list[dict], list[dict]]:
    """Turn interview answers into (extra substances to check, standalone notes).

    Extra substances are fed through the same interaction and dosing engine as the
    prescription, marked so the UI can show where they came from.
    """
    substances: list[dict] = []
    notes: list[dict] = []
    seen: set[str] = set()

    for question_id, chosen in (answers or {}).items():
        for option_id in chosen or []:
            opt = _option(question_id, option_id)
            if not opt or opt.id == "none":
                continue

            for sub in opt.substances:
                if sub in seen:
                    continue
                seen.add(sub)
                substances.append(
                    {
                        "active_substance": sub,
                        "trade_name": opt.label.split(",")[0].strip(),
                        "source": "interview",
                        "question": question_id,
                    }
                )

            if opt.note:
                notes.append(
                    {
                        "code": f"INTAKE_{question_id.upper()}",
                        "severity": opt.severity or "info",
                        "title": f"Z rozhovoru — {opt.label}",
                        "detail": opt.note,
                        "drugs": [],
                        "action": "Zaznamenať do karty pacienta a zohľadniť pri výdaji.",
                    }
                )

    return substances, notes
