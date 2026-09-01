"""Clinical validation engine — dosing, renal/hepatic adjustment, duplicate therapy,
geriatric risk. Rules are derived from SmPC/EMA labelling and widely used geriatric
criteria. Decision support only — never a substitute for a pharmacist's judgement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

Severity = Literal["critical", "warning", "info"]

# ── Patient model ──────────────────────────────────────────────────────────────


@dataclass
class Patient:
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    egfr: Optional[float] = None           # ml/min/1.73m2
    hepatic_impairment: bool = False
    pregnant: bool = False
    breastfeeding: bool = False
    allergies: list[str] = field(default_factory=list)

    @property
    def is_elderly(self) -> bool:
        return self.age is not None and self.age >= 65

    @property
    def is_child(self) -> bool:
        return self.age is not None and self.age < 18


@dataclass
class Finding:
    code: str
    severity: Severity
    title: str
    detail: str
    drugs: list[str] = field(default_factory=list)
    action: str = ""


# ── Dosing rule table ──────────────────────────────────────────────────────────
# max_daily_mg   : licensed maximum daily dose for an adult
# renal          : list of (egfr_below, action, note) evaluated low → high
# min_age        : minimum licensed age in years
# max_daily_elderly_mg : reduced ceiling for patients >= 65 (or as noted)
# pregnancy      : "contraindicated" | "caution"
# hepatic        : note when hepatic impairment is flagged
# beers          : geriatric caution (potentially inappropriate medication)
# frequency      : "weekly" for drugs that must NOT be taken daily

RULES: dict[str, dict] = {
    # ── Analgesics / NSAIDs ────────────────────────────────────────────────────
    "paracetamol": {
        "max_daily_mg": 4000,
        "max_daily_elderly_mg": 3000,
        "hepatic": "Pri hepatálnej insuficiencii znížiť maximálnu dennú dávku na 2 g a vyhnúť sa dlhodobému podávaniu.",
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min predĺžiť interval podávania na minimálne 8 hodín.")],
        "note": "Pozor na kumulatívnu dávku z kombinovaných prípravkov (Coldrex, Paralen Plus, Ataralgin).",
    },
    "ibuprofen": {
        "max_daily_mg": 3200,
        "max_daily_elderly_mg": 1200,
        "renal": [
            (30, "contraindicated", "NSAID sú pri eGFR < 30 ml/min kontraindikované — riziko akútneho zlyhania obličiek."),
            (60, "caution", "Pri eGFR 30–59 ml/min podávať čo najkratšie, monitorovať renálne funkcie a kálium."),
        ],
        "pregnancy": "contraindicated",
        "pregnancy_note": "Od 20. týždňa riziko oligohydramniónu, od 30. týždňa predčasný uzáver ductus arteriosus.",
        "beers": "NSAID u seniorov zvyšujú riziko GIT krvácania a zhoršenia renálnych funkcií.",
        "min_age": 0,
    },
    "diclofenac": {
        "max_daily_mg": 150,
        "max_daily_elderly_mg": 100,
        "renal": [
            (30, "contraindicated", "Kontraindikované pri eGFR < 30 ml/min."),
            (60, "caution", "Pri eGFR 30–59 ml/min len krátkodobo, s monitoringom."),
        ],
        "pregnancy": "contraindicated",
        "beers": "Najvyššie kardiovaskulárne riziko spomedzi bežných NSAID — u seniorov preferovať alternatívu.",
    },
    "naproxen": {
        "max_daily_mg": 1000,
        "max_daily_elderly_mg": 660,
        "renal": [(30, "contraindicated", "Kontraindikované pri eGFR < 30 ml/min.")],
        "pregnancy": "contraindicated",
        "beers": "NSAID u seniorov — riziko GIT krvácania.",
    },
    "acetylsalicylic acid": {
        "max_daily_mg": 4000,
        "min_age": 16,
        "min_age_note": "Do 16 rokov riziko Reyeovho syndrómu — nepodávať pri horúčkovitých vírusových ochoreniach.",
        "pregnancy": "caution",
        "note": "V antiagregačnej indikácii je cieľová dávka 75–100 mg denne, nie analgetická.",
    },
    "metamizole": {
        "max_daily_mg": 4000,
        "note": "Riziko agranulocytózy — nepodávať dlhodobo bez kontroly krvného obrazu.",
        "renal": [(30, "caution", "Pri eGFR < 30 ml/min znížiť dávku, vyhnúť sa dlhodobému podávaniu.")],
    },
    "tramadol": {
        "max_daily_mg": 400,
        "max_daily_elderly_mg": 300,
        "elderly_age": 75,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min maximálne 200 mg denne, interval predĺžiť na 12 hodín.")],
        "hepatic": "Pri hepatálnej insuficiencii maximálne 100 mg každých 12 hodín.",
        "min_age": 12,
        "beers": "Zvyšuje riziko pádov, hyponatriémie a delíria u seniorov.",
        "note": "Znižuje záchvatový prah — pozor pri epilepsii a v kombinácii so serotonergnými liekmi.",
    },
    "codeine": {
        "max_daily_mg": 240,
        "min_age": 12,
        "min_age_note": "Do 12 rokov kontraindikované (riziko respiračnej depresie u ultrarýchlych metabolizátorov CYP2D6).",
        "breastfeeding": "Počas dojčenia kontraindikované.",
    },
    # ── Anticoagulants / antiplatelets ─────────────────────────────────────────
    "warfarin": {
        "monitoring": "Dávkovanie sa riadi INR (cieľ zvyčajne 2,0–3,0). Fixná maximálna dávka neexistuje.",
        "pregnancy": "contraindicated",
        "pregnancy_note": "Teratogénne v 1. trimestri, riziko krvácania plodu — nahradiť LMWH.",
        "note": "Každý nový liek si vyžaduje kontrolu INR do 3–5 dní.",
    },
    "apixaban": {
        "max_daily_mg": 10,
        "renal": [
            (15, "contraindicated", "Pri eGFR < 15 ml/min sa neodporúča."),
            (30, "reduce", "Pri eGFR 15–29 ml/min podávať 2,5 mg dvakrát denne."),
        ],
        "dose_reduction_criteria": {
            "text": "Znížiť na 2,5 mg 2× denne pri splnení aspoň 2 kritérií: vek ≥ 80 rokov, hmotnosť ≤ 60 kg, kreatinín ≥ 133 µmol/l.",
            "age_min": 80,
            "weight_max": 60,
            "reduced_daily_mg": 5,
        },
        "pregnancy": "contraindicated",
    },
    "rivaroxaban": {
        "max_daily_mg": 20,
        "renal": [
            (15, "contraindicated", "Pri eGFR < 15 ml/min sa neodporúča."),
            (50, "reduce", "Pri eGFR 15–49 ml/min podávať 15 mg denne namiesto 20 mg."),
        ],
        "pregnancy": "contraindicated",
        "note": "V indikácii fibrilácie predsiení užívať s jedlom — inak klesá biologická dostupnosť.",
    },
    "dabigatran": {
        "max_daily_mg": 300,
        "renal": [
            (30, "contraindicated", "Pri eGFR < 30 ml/min kontraindikované."),
            (50, "reduce", "Pri eGFR 30–49 ml/min zvážiť 110 mg dvakrát denne."),
        ],
        "max_daily_elderly_mg": 220,
        "elderly_age": 80,
        "pregnancy": "contraindicated",
    },
    "clopidogrel": {
        "max_daily_mg": 75,
        "note": "Účinnosť znižujú silné inhibítory CYP2C19 (omeprazol, esomeprazol) — preferovať pantoprazol.",
    },
    # ── Diabetes ───────────────────────────────────────────────────────────────
    "metformin": {
        "max_daily_mg": 3000,
        "renal": [
            (30, "contraindicated", "Pri eGFR < 30 ml/min kontraindikované — riziko laktátovej acidózy."),
            (45, "reduce", "Pri eGFR 30–44 ml/min maximálne 1000 mg denne a liečbu nezačínať."),
            (60, "caution", "Pri eGFR 45–59 ml/min monitorovať renálne funkcie každých 3–6 mesiacov."),
        ],
        "note": "Pred podaním jódovej kontrastnej látky prerušiť a obnoviť najskôr o 48 hodín.",
    },
    "gliclazide": {
        "max_daily_mg": 120,
        "renal": [(30, "caution", "Pri ťažkej renálnej insuficiencii riziko protrahovanej hypoglykémie.")],
        "beers": "Sulfonylurey s dlhým účinkom u seniorov zvyšujú riziko ťažkej hypoglykémie.",
    },
    "empagliflozin": {
        "max_daily_mg": 25,
        "renal": [(20, "contraindicated", "Pri eGFR < 20 ml/min sa nezačína liečba.")],
        "note": "Riziko genitálnych mykotických infekcií a euglykemickej ketoacidózy.",
    },
    "sitagliptin": {
        "max_daily_mg": 100,
        "renal": [
            (30, "reduce", "Pri eGFR < 30 ml/min podávať 25 mg denne."),
            (45, "reduce", "Pri eGFR 30–44 ml/min podávať 50 mg denne."),
        ],
    },
    # ── Cardiovascular ─────────────────────────────────────────────────────────
    "bisoprolol": {"max_daily_mg": 20, "renal": [(20, "reduce", "Pri eGFR < 20 ml/min maximálne 10 mg denne.")]},
    "metoprolol": {"max_daily_mg": 200},
    "amlodipine": {"max_daily_mg": 10, "hepatic": "Pri hepatálnej insuficiencii začínať dávkou 2,5 mg denne."},
    "ramipril": {
        "max_daily_mg": 10,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min maximálne 5 mg denne, monitorovať kálium a kreatinín.")],
        "pregnancy": "contraindicated",
        "pregnancy_note": "ACE inhibítory sú v 2. a 3. trimestri fetotoxické — okamžite vysadiť.",
    },
    "perindopril": {
        "max_daily_mg": 10,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min maximálne 2,5 mg denne.")],
        "pregnancy": "contraindicated",
    },
    "enalapril": {
        "max_daily_mg": 40,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min začínať dávkou 2,5 mg denne.")],
        "pregnancy": "contraindicated",
    },
    "losartan": {"max_daily_mg": 100, "pregnancy": "contraindicated"},
    "valsartan": {"max_daily_mg": 320, "pregnancy": "contraindicated"},
    "furosemide": {
        "max_daily_mg": 600,
        "note": "Monitorovať kálium, nátrium a renálne funkcie, najmä v kombinácii s ACEI/ARB a NSAID.",
    },
    "hydrochlorothiazide": {
        "max_daily_mg": 50,
        "renal": [(30, "contraindicated", "Pri eGFR < 30 ml/min je tiazid neúčinný — nahradiť kľučkovým diuretikom.")],
        "beers": "U seniorov zvyšuje riziko hyponatriémie — kontrola nátria po 2–4 týždňoch.",
    },
    "spironolactone": {
        "max_daily_mg": 100,
        "renal": [(30, "contraindicated", "Pri eGFR < 30 ml/min kontraindikované — riziko ťažkej hyperkaliémie.")],
        "note": "V kombinácii s ACEI/ARB kontrolovať kálium do 1 týždňa.",
    },
    "digoxin": {
        "max_daily_mg": 0.25,
        "max_daily_elderly_mg": 0.125,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min výrazne znížiť dávku a monitorovať hladinu digoxínu.")],
        "beers": "U seniorov neprekračovať 0,125 mg denne — úzke terapeutické okno.",
    },
    "amiodarone": {
        "max_daily_mg": 200,
        "note": "Silný inhibítor CYP a P-gp — po nasadení znížiť dávku warfarínu aj digoxínu. Kontrola TSH a pečeňových testov každých 6 mesiacov.",
        "beers": "U seniorov až druhá voľba pre fibriláciu predsiení — vysoká toxicita.",
    },
    "atorvastatin": {
        "max_daily_mg": 80,
        "hepatic": "Pri aktívnom ochorení pečene kontraindikované.",
        "pregnancy": "contraindicated",
    },
    "rosuvastatin": {
        "max_daily_mg": 40,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min maximálne 10 mg denne.")],
        "pregnancy": "contraindicated",
    },
    "simvastatin": {
        "max_daily_mg": 40,
        "pregnancy": "contraindicated",
        "note": "Dávka 80 mg sa už neodporúča — riziko myopatie. S amlodipínom neprekračovať 20 mg denne.",
    },
    # ── GI ─────────────────────────────────────────────────────────────────────
    "omeprazole": {
        "max_daily_mg": 40,
        "note": "Inhibítor CYP2C19 — znižuje účinnosť klopidogrelu. Dlhodobé podávanie: riziko hypomagneziémie a osteoporózy.",
    },
    "pantoprazole": {"max_daily_mg": 80, "note": "Spomedzi PPI má najmenší interakčný potenciál — voľba pri klopidogreli."},
    "esomeprazole": {"max_daily_mg": 40, "note": "Inhibítor CYP2C19 — rovnaké obmedzenie s klopidogrelom ako omeprazol."},
    # ── CNS ────────────────────────────────────────────────────────────────────
    "sertraline": {
        "max_daily_mg": 200,
        "hepatic": "Pri hepatálnej insuficiencii znížiť dávku alebo predĺžiť interval.",
        "beers": "SSRI u seniorov zvyšujú riziko hyponatriémie a pádov — kontrola nátria po 2–4 týždňoch.",
    },
    "escitalopram": {
        "max_daily_mg": 20,
        "max_daily_elderly_mg": 10,
        "note": "Závislé od dávky predlžuje QT interval.",
        "beers": "Riziko hyponatriémie u seniorov.",
    },
    "citalopram": {
        "max_daily_mg": 40,
        "max_daily_elderly_mg": 20,
        "note": "Nad 40 mg denne signifikantné predĺženie QT — u seniorov strop 20 mg.",
    },
    "venlafaxine": {
        "max_daily_mg": 375,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min znížiť dávku o 50 %.")],
        "note": "Nad 150 mg denne stúpa tlak krvi — monitorovať.",
    },
    "trazodone": {"max_daily_mg": 600, "max_daily_elderly_mg": 300, "beers": "Sedácia a riziko pádov u seniorov."},
    "alprazolam": {
        "max_daily_mg": 4,
        "max_daily_elderly_mg": 2,
        "beers": "Benzodiazepíny u seniorov: riziko pádov, fraktúr a kognitívneho zhoršenia — vyhnúť sa.",
    },
    "diazepam": {
        "max_daily_mg": 40,
        "max_daily_elderly_mg": 10,
        "beers": "Dlhý polčas — u seniorov výrazná kumulácia a riziko pádov.",
    },
    "bromazepam": {"max_daily_mg": 12, "max_daily_elderly_mg": 3, "beers": "Benzodiazepín — u seniorov sa neodporúča."},
    "zolpidem": {
        "max_daily_mg": 10,
        "max_daily_elderly_mg": 5,
        "beers": "Z-hypnotiká u seniorov: riziko pádov a nočnej zmätenosti — maximálne 5 mg.",
        "note": "U žien sa odporúča 5 mg pre pomalšiu elimináciu.",
    },
    "quetiapine": {
        "max_daily_mg": 800,
        "max_daily_elderly_mg": 200,
        "beers": "Antipsychotiká u pacientov s demenciou zvyšujú mortalitu — čierne varovanie.",
    },
    "levetiracetam": {
        "max_daily_mg": 3000,
        "renal": [
            (30, "reduce", "Pri eGFR < 30 ml/min maximálne 1000 mg denne."),
            (50, "reduce", "Pri eGFR 30–49 ml/min maximálne 1500 mg denne."),
        ],
    },
    # ── Anti-infectives ────────────────────────────────────────────────────────
    "ciprofloxacin": {
        "max_daily_mg": 1500,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min maximálne 500 mg denne.")],
        "min_age": 18,
        "min_age_note": "U detí a dospievajúcich len pri prísne vymedzených indikáciách — riziko poškodenia chrupaviek.",
        "note": "Riziko ruptúry šľachy, najmä v kombinácii s kortikoidmi a u pacientov nad 60 rokov. Chelatuje s Ca/Mg/Fe — odstup 2 hodiny.",
    },
    "amoxicillin": {"max_daily_mg": 6000, "renal": [(30, "reduce", "Pri eGFR < 30 ml/min predĺžiť interval podávania.")]},
    "clarithromycin": {
        "max_daily_mg": 1000,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min znížiť dávku o 50 %.")],
        "note": "Silný inhibítor CYP3A4 — kontraindikovaný so simvastatínom, zvyšuje hladiny mnohých liekov.",
    },
    "azithromycin": {"max_daily_mg": 500, "note": "Predlžuje QT interval — pozor v kombinácii s inými QT liekmi."},
    # ── Other high-risk ────────────────────────────────────────────────────────
    "methotrexate": {
        "frequency": "weekly",
        "max_weekly_mg": 25,
        "frequency_note": "V reumatologickej indikácii sa podáva RAZ TÝŽDENNE. Denné podanie je život ohrozujúce — myelosupresia, mukozitída.",
        "renal": [(30, "contraindicated", "Pri eGFR < 30 ml/min kontraindikované.")],
        "pregnancy": "contraindicated",
        "note": "Súbežne podávať kyselinu listovú. NSAID a trimetoprim zvyšujú toxicitu.",
    },
    "allopurinol": {
        "max_daily_mg": 900,
        "renal": [
            (30, "reduce", "Pri eGFR < 30 ml/min začínať 50–100 mg denne."),
            (60, "reduce", "Pri eGFR 30–59 ml/min maximálne 200 mg denne."),
        ],
        "note": "Nezačínať počas akútneho záchvatu dny.",
    },
    "colchicine": {
        "max_daily_mg": 2,
        "renal": [(30, "reduce", "Pri eGFR < 30 ml/min výrazne znížiť dávku — úzke terapeutické okno.")],
        "note": "So silnými inhibítormi CYP3A4/P-gp (klaritromycín) riziko fatálnej toxicity.",
    },
    "levothyroxine": {
        "max_daily_mg": 0.3,
        "note": "U seniorov a pri ischemickej chorobe srdca začínať 12,5–25 µg denne. Užívať nalačno, odstup od Ca/Fe 4 hodiny.",
    },
    "prednisone": {
        "max_daily_mg": 100,
        "note": "Pri liečbe nad 3 týždne vysadzovať postupne. S NSAID výrazne stúpa riziko GIT krvácania.",
    },
}

# Substance aliases seen in the SK/CZ registry
ALIASES = {
    "acetylsalicylic acid": "acetylsalicylic acid",
    "kyselina acetylsalicylová": "acetylsalicylic acid",
    "acidum acetylsalicylicum": "acetylsalicylic acid",
    "paracetamolum": "paracetamol",
    "ibuprofenum": "ibuprofen",
    "metforminum": "metformin",
    "metformin hydrochloride": "metformin",
    "tramadol hydrochloride": "tramadol",
    "ciprofloxacin hydrochloride": "ciprofloxacin",
    "sertraline hydrochloride": "sertraline",
    "diclofenac sodium": "diclofenac",
    "diclofenac potassium": "diclofenac",
    "amlodipine besilate": "amlodipine",
    "metoprolol succinate": "metoprolol",
    "metoprolol tartrate": "metoprolol",
    "omeprazolum": "omeprazole",
    "esomeprazole magnesium": "esomeprazole",
    "pantoprazole sodium": "pantoprazole",
    "warfarin sodium": "warfarin",
    "warfarin sodium clathrate": "warfarin",
    "acidum acetylsalicylicum": "acetylsalicylic acid",
    "ibuprofen lysine": "ibuprofen",
    "tramadol hydrochloride, paracetamol": "tramadol",
    "digoxinum": "digoxin",
    "amiodarone hydrochloride": "amiodarone",
    "venlafaxine hydrochloride": "venlafaxine",
    "methotrexate disodium": "methotrexate",
    "acetylsalicylate": "acetylsalicylic acid",
}


def normalise(substance: str) -> str:
    """Map a registry substance string onto a rule key."""
    s = (substance or "").strip().lower()
    if s in RULES:
        return s
    if s in ALIASES:
        return ALIASES[s]
    # strip common salt suffixes
    for suffix in (
        " hydrochloride", " sodium", " potassium", " besilate", " besylate",
        " succinate", " tartrate", " maleate", " mesylate", " sulfate",
        " sulphate", " fumarate", " calcium", " magnesium", " dihydrate",
        " monohydrate", " disodium",
    ):
        if s.endswith(suffix):
            base = s[: -len(suffix)].strip()
            if base in RULES:
                return base
            if base in ALIASES:
                return ALIASES[base]
    return s


def get_rule(substance: str) -> Optional[dict]:
    return RULES.get(normalise(substance))


# ── Duplicate-therapy classes ──────────────────────────────────────────────────
# Two members of the same class on one prescription is a therapeutic duplication.

THERAPEUTIC_CLASSES: dict[str, dict] = {
    "NSAID": {
        "label": "nesteroidné antiflogistiká",
        "atc_prefixes": ["M01A"],
        "substances": ["ibuprofen", "diclofenac", "naproxen", "ketoprofen", "meloxicam", "nimesulide", "aceclofenac"],
        "risk": "Súbežné podanie dvoch NSAID nezvyšuje analgetický účinok, ale násobí riziko GIT krvácania a poškodenia obličiek.",
        "severity": "critical",
    },
    "SSRI": {
        "label": "SSRI antidepresíva",
        "atc_prefixes": ["N06AB"],
        "substances": ["sertraline", "escitalopram", "citalopram", "fluoxetine", "paroxetine", "fluvoxamine"],
        "risk": "Dve SSRI súčasne — riziko sérotonínového syndrómu bez terapeutického prínosu.",
        "severity": "critical",
    },
    "PPI": {
        "label": "inhibítory protónovej pumpy",
        "atc_prefixes": ["A02BC"],
        "substances": ["omeprazole", "pantoprazole", "esomeprazole", "lansoprazole", "rabeprazole"],
        "risk": "Duplicitná gastroprotekcia — zbytočná záťaž a náklady, bez pridaného účinku.",
        "severity": "warning",
    },
    "BZD": {
        "label": "benzodiazepíny a Z-hypnotiká",
        "atc_prefixes": ["N05BA", "N05CD", "N05CF"],
        "substances": ["alprazolam", "diazepam", "bromazepam", "oxazepam", "clonazepam", "zolpidem", "zopiclone", "midazolam"],
        "risk": "Kumulatívna sedácia — riziko útlmu dýchania, pádov a fraktúr.",
        "severity": "critical",
    },
    "ACEI_ARB": {
        "label": "ACE inhibítory a sartany",
        "atc_prefixes": ["C09A", "C09C"],
        "substances": ["ramipril", "perindopril", "enalapril", "lisinopril", "losartan", "valsartan", "telmisartan", "candesartan"],
        "risk": "Duálna blokáda RAAS sa neodporúča — riziko hyperkaliémie, hypotenzie a akútneho renálneho zlyhania.",
        "severity": "critical",
    },
    "STATIN": {
        "label": "statíny",
        "atc_prefixes": ["C10AA"],
        "substances": ["atorvastatin", "rosuvastatin", "simvastatin", "fluvastatin", "pravastatin"],
        "risk": "Dva statíny súčasne — zvýšené riziko myopatie a rabdomyolýzy.",
        "severity": "critical",
    },
    "OPIOID": {
        "label": "opioidné analgetiká",
        "atc_prefixes": ["N02A"],
        "substances": ["tramadol", "codeine", "morphine", "oxycodone", "fentanyl", "hydromorphone", "tapentadol"],
        "risk": "Kombinácia opioidov zvyšuje riziko útlmu dýchania — vyžaduje explicitnú indikáciu lekára.",
        "severity": "warning",
    },
    "PARACETAMOL": {
        "label": "paracetamol",
        "atc_prefixes": [],
        "substances": ["paracetamol"],
        "risk": "Paracetamol vo viacerých prípravkoch — riziko prekročenia hepatotoxickej dennej dávky 4 g.",
        "severity": "critical",
    },
    "ANTICOAG": {
        "label": "antikoagulanciá",
        "atc_prefixes": ["B01AA", "B01AE", "B01AF"],
        "substances": ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban"],
        "risk": "Dve antikoagulanciá súčasne — vysoké riziko závažného krvácania.",
        "severity": "critical",
    },
}

# Drugs contributing to fall risk in the elderly
FALL_RISK = {
    "alprazolam", "diazepam", "bromazepam", "oxazepam", "clonazepam", "zolpidem",
    "zopiclone", "trazodone", "quetiapine", "tramadol", "codeine", "amitriptyline",
    "mirtazapine", "sertraline", "escitalopram", "citalopram", "venlafaxine",
    "furosemide", "doxazosin", "tamsulosin",
}

# Drugs that additively increase bleeding risk
BLEEDING_RISK = {
    "warfarin", "apixaban", "rivaroxaban", "dabigatran", "clopidogrel",
    "acetylsalicylic acid", "ibuprofen", "diclofenac", "naproxen", "ketoprofen",
    "sertraline", "escitalopram", "citalopram", "fluoxetine", "paroxetine", "venlafaxine",
}

# Serotonergic agents — additive risk of serotonin syndrome
SEROTONERGIC = {
    "sertraline", "escitalopram", "citalopram", "fluoxetine", "paroxetine", "fluvoxamine",
    "venlafaxine", "duloxetine", "mirtazapine", "trazodone", "amitriptyline", "clomipramine",
    "tramadol", "fentanyl", "pethidine", "dextromethorphan", "ondansetron", "lithium",
    "sumatriptan", "rizatriptan", "eletriptan", "linezolid", "buspirone", "st john's wort",
}

# Irreversible/reversible MAO inhibitors — absolute contraindication with any serotonergic
MAO_INHIBITORS = {"selegiline", "rasagiline", "moclobemide", "tranylcypromine", "phenelzine", "linezolid"}

# Drugs with meaningful QT-prolonging potential
QT_RISK = {
    "amiodarone", "citalopram", "escitalopram", "clarithromycin", "azithromycin",
    "ciprofloxacin", "quetiapine", "haloperidol", "domperidone", "sotalol",
}


def _renal_check(rule: dict, egfr: float) -> Optional[tuple[str, str]]:
    """Return the strictest matching renal rule as (action, note)."""
    thresholds = rule.get("renal") or []
    match = None
    for below, action, note in sorted(thresholds, key=lambda t: t[0]):
        if egfr < below:
            match = (action, note)
            break
    return match


def validate_item(item: dict, patient: Patient) -> list[Finding]:
    """Validate a single prescription item against the dosing rules.

    item: {"trade_name", "active_substance", "daily_dose_mg" (optional),
           "strength_mg" (optional), "frequency_per_day" (optional)}
    """
    findings: list[Finding] = []
    substance = normalise(item.get("active_substance", ""))
    rule = RULES.get(substance)
    name = item.get("trade_name") or substance
    if not rule:
        return findings

    daily = item.get("daily_dose_mg")

    # ── Frequency rules (methotrexate) ─────────────────────────────────────────
    if rule.get("frequency") == "weekly" and (item.get("frequency_per_day") or 0) >= 1:
        findings.append(
            Finding(
                code="FREQUENCY",
                severity="critical",
                title=f"{name} — denné podávanie namiesto týždenného",
                detail=rule["frequency_note"],
                drugs=[name],
                action="Nevydať bez telefonického overenia u predpisujúceho lekára.",
            )
        )

    # ── Renal ──────────────────────────────────────────────────────────────────
    if patient.egfr is not None:
        hit = _renal_check(rule, patient.egfr)
        if hit:
            action, note = hit
            sev: Severity = "critical" if action == "contraindicated" else "warning"
            title = {
                "contraindicated": f"{name} — kontraindikované pri eGFR {patient.egfr:.0f} ml/min",
                "reduce": f"{name} — nutná úprava dávky pri eGFR {patient.egfr:.0f} ml/min",
                "caution": f"{name} — opatrnosť pri eGFR {patient.egfr:.0f} ml/min",
            }[action]
            findings.append(
                Finding(
                    code=f"RENAL_{action.upper()}",
                    severity=sev,
                    title=title,
                    detail=note,
                    drugs=[name],
                    action="Konzultovať s predpisujúcim lekárom pred výdajom."
                    if sev == "critical"
                    else "Overiť dávku a upozorniť pacienta na monitoring.",
                )
            )

    # ── Maximum daily dose ─────────────────────────────────────────────────────
    if daily:
        ceiling = rule.get("max_daily_mg")
        elderly_ceiling = rule.get("max_daily_elderly_mg")
        elderly_from = rule.get("elderly_age", 65)
        applied, label = ceiling, "maximálna denná dávka"
        if (
            elderly_ceiling
            and patient.age is not None
            and patient.age >= elderly_from
            and (ceiling is None or elderly_ceiling < ceiling)
        ):
            applied, label = elderly_ceiling, f"maximálna denná dávka pre pacienta nad {elderly_from} rokov"

        if applied and daily > applied:
            findings.append(
                Finding(
                    code="MAX_DOSE",
                    severity="critical",
                    title=f"{name} — prekročená {label}",
                    detail=(
                        f"Predpísaná denná dávka {_fmt(daily)} mg prekračuje odporúčaný limit "
                        f"{_fmt(applied)} mg ({daily / applied:.1f}× limit)."
                    ),
                    drugs=[name],
                    action="Nevydať v predpísanej dávke — overiť u lekára.",
                )
            )
        elif applied and daily > applied * 0.8:
            findings.append(
                Finding(
                    code="NEAR_MAX_DOSE",
                    severity="info",
                    title=f"{name} — dávka blízko horného limitu",
                    detail=f"Predpísaná denná dávka {_fmt(daily)} mg pri limite {_fmt(applied)} mg.",
                    drugs=[name],
                    action="Bez zásahu, len upozorniť pacienta na dodržanie dávkovania.",
                )
            )

    # ── Weekly ceiling ─────────────────────────────────────────────────────────
    if rule.get("max_weekly_mg") and item.get("weekly_dose_mg"):
        if item["weekly_dose_mg"] > rule["max_weekly_mg"]:
            findings.append(
                Finding(
                    code="MAX_WEEKLY_DOSE",
                    severity="critical",
                    title=f"{name} — prekročená týždenná dávka",
                    detail=f"{_fmt(item['weekly_dose_mg'])} mg/týždeň pri limite {_fmt(rule['max_weekly_mg'])} mg.",
                    drugs=[name],
                    action="Nevydať — overiť u lekára.",
                )
            )

    # ── Age ────────────────────────────────────────────────────────────────────
    if rule.get("min_age") and patient.age is not None and patient.age < rule["min_age"]:
        findings.append(
            Finding(
                code="AGE",
                severity="critical",
                title=f"{name} — vek pod licencovanou hranicou ({rule['min_age']} rokov)",
                detail=rule.get("min_age_note", f"Prípravok nie je registrovaný pre pacientov pod {rule['min_age']} rokov."),
                drugs=[name],
                action="Nevydať bez konzultácie s lekárom.",
            )
        )

    # ── Pregnancy ──────────────────────────────────────────────────────────────
    if patient.pregnant and rule.get("pregnancy"):
        contra = rule["pregnancy"] == "contraindicated"
        findings.append(
            Finding(
                code="PREGNANCY",
                severity="critical" if contra else "warning",
                title=f"{name} — {'kontraindikované' if contra else 'opatrnosť'} v gravidite",
                detail=rule.get("pregnancy_note", "Prípravok sa v gravidite neodporúča."),
                drugs=[name],
                action="Nevydať a odoslať pacientku k lekárovi." if contra else "Overiť indikáciu u lekára.",
            )
        )

    if patient.breastfeeding and rule.get("breastfeeding"):
        findings.append(
            Finding(
                code="BREASTFEEDING",
                severity="warning",
                title=f"{name} — dojčenie",
                detail=rule["breastfeeding"],
                drugs=[name],
                action="Overiť u lekára.",
            )
        )

    # ── Hepatic ────────────────────────────────────────────────────────────────
    if patient.hepatic_impairment and rule.get("hepatic"):
        findings.append(
            Finding(
                code="HEPATIC",
                severity="warning",
                title=f"{name} — hepatálna insuficiencia",
                detail=rule["hepatic"],
                drugs=[name],
                action="Overiť dávku u lekára.",
            )
        )

    # ── Geriatric (Beers-type) ─────────────────────────────────────────────────
    if patient.is_elderly and rule.get("beers"):
        findings.append(
            Finding(
                code="GERIATRIC",
                severity="warning",
                title=f"{name} — potenciálne nevhodné u seniora",
                detail=rule["beers"],
                drugs=[name],
                action="Upozorniť pacienta, pri opakovanom výdaji navrhnúť lekárovi revíziu medikácie.",
            )
        )

    # ── Apixaban dose-reduction criteria ───────────────────────────────────────
    crit = rule.get("dose_reduction_criteria")
    if crit and daily:
        met = 0
        reasons = []
        if patient.age is not None and patient.age >= crit["age_min"]:
            met += 1
            reasons.append(f"vek {patient.age} rokov")
        if patient.weight_kg is not None and patient.weight_kg <= crit["weight_max"]:
            met += 1
            reasons.append(f"hmotnosť {_fmt(patient.weight_kg)} kg")
        if patient.egfr is not None and patient.egfr < 50:
            met += 1
            reasons.append(f"eGFR {patient.egfr:.0f} ml/min")
        if met >= 2 and daily > crit["reduced_daily_mg"]:
            findings.append(
                Finding(
                    code="DOSE_REDUCTION",
                    severity="critical",
                    title=f"{name} — pacient spĺňa kritériá pre zníženú dávku",
                    detail=f"{crit['text']} Splnené: {', '.join(reasons)}.",
                    drugs=[name],
                    action="Overiť u lekára — predpísaná je plná dávka.",
                )
            )

    return findings


def _fmt(v: float) -> str:
    return f"{v:g}"


def _class_of(substance: str, atc: str | None) -> list[str]:
    s = normalise(substance)
    hits = []
    for key, cls in THERAPEUTIC_CLASSES.items():
        if s in cls["substances"]:
            hits.append(key)
            continue
        if atc and any(atc.upper().startswith(p) for p in cls["atc_prefixes"]):
            hits.append(key)
    return hits


def validate_regimen(items: list[dict], patient: Patient) -> list[Finding]:
    """Cross-item checks: duplicate therapy and additive risk."""
    findings: list[Finding] = []

    # ── Therapeutic duplication ────────────────────────────────────────────────
    by_class: dict[str, list[dict]] = {}
    for it in items:
        for cls in _class_of(it.get("active_substance", ""), it.get("atc_code")):
            by_class.setdefault(cls, []).append(it)

    for cls, members in by_class.items():
        distinct = {normalise(m.get("active_substance", "")): m for m in members}
        spec = THERAPEUTIC_CLASSES[cls]
        # Paracetamol duplication counts distinct products, not distinct substances
        trigger = len(members) >= 2 if cls == "PARACETAMOL" else len(distinct) >= 2
        if trigger:
            names = [m.get("trade_name") or m.get("active_substance") for m in members]
            findings.append(
                Finding(
                    code="DUPLICATE",
                    severity=spec["severity"],
                    title=f"Duplicitná terapia — {spec['label']}",
                    detail=f"{' + '.join(names)}. {spec['risk']}",
                    drugs=names,
                    action="Overiť u lekára, či ide o zámer — inak vydať len jeden prípravok.",
                )
            )

    subs = {normalise(i.get("active_substance", "")): (i.get("trade_name") or i.get("active_substance")) for i in items}

    # ── Additive bleeding risk ─────────────────────────────────────────────────
    bleeders = [n for s, n in subs.items() if s in BLEEDING_RISK]
    if len(bleeders) >= 3:
        findings.append(
            Finding(
                code="BLEEDING_BURDEN",
                severity="critical",
                title=f"Kumulatívne riziko krvácania — {len(bleeders)} liekov",
                detail=f"{', '.join(bleeders)}. Tri a viac liekov ovplyvňujúcich hemostázu výrazne zvyšujú riziko závažného krvácania.",
                drugs=bleeders,
                action="Konzultovať s lekárom revíziu medikácie a zvážiť gastroprotekciu.",
            )
        )

    # ── Fall risk in the elderly ───────────────────────────────────────────────
    if patient.is_elderly:
        fallers = [n for s, n in subs.items() if s in FALL_RISK]
        if len(fallers) >= 3:
            findings.append(
                Finding(
                    code="FALL_RISK",
                    severity="warning",
                    title=f"Riziko pádov — {len(fallers)} liekov s tlmivým účinkom",
                    detail=f"{', '.join(fallers)}. U pacienta nad 65 rokov je kombinácia troch a viac takýchto liekov nezávislým prediktorom pádu a fraktúry.",
                    drugs=fallers,
                    action="Navrhnúť lekárovi deprescribing, upozorniť pacienta na riziko.",
                )
            )

    # ── Serotonergic burden ────────────────────────────────────────────────────
    serotonergic = [n for s_, n in subs.items() if s_ in SEROTONERGIC]
    maoi = [n for s_, n in subs.items() if s_ in MAO_INHIBITORS]

    if maoi and len(serotonergic) >= 1:
        findings.append(
            Finding(
                code="SEROTONIN_MAOI",
                severity="critical",
                title="Kontraindikácia — MAO inhibítor so serotonergným liekom",
                detail=f"{', '.join(sorted(set(maoi + serotonergic)))}. Kombinácia je absolútne kontraindikovaná — riziko fatálneho sérotonínového syndrómu.",
                drugs=sorted(set(maoi + serotonergic)),
                action="Nevydať. Okamžite kontaktovať predpisujúceho lekára.",
            )
        )
    elif len(serotonergic) >= 3:
        findings.append(
            Finding(
                code="SEROTONIN_BURDEN",
                severity="critical",
                title=f"Vysoké riziko sérotonínového syndrómu — {len(serotonergic)} serotonergných liekov",
                detail=f"{', '.join(serotonergic)}. Tri a viac serotonergných liekov súčasne predstavuje vysoké riziko sérotonínového syndrómu.",
                drugs=serotonergic,
                action="Nevydať bez konzultácie — navrhnúť lekárovi zámenu jedného z liekov.",
            )
        )
    elif len(serotonergic) >= 2:
        findings.append(
            Finding(
                code="SEROTONIN_BURDEN",
                severity="warning",
                title=f"Riziko sérotonínového syndrómu — {len(serotonergic)} serotonergné lieky",
                detail=(
                    f"{', '.join(serotonergic)}. Kombinácia zvyšuje hladinu serotonínu. "
                    "Varovné príznaky: nepokoj, tras, potenie, zrýchlený pulz, zmätenosť, horúčka."
                ),
                drugs=serotonergic,
                action="Poučiť pacienta o varovných príznakoch a odporučiť kontrolu u lekára pri ich výskyte.",
            )
        )

    # ── QT prolongation ────────────────────────────────────────────────────────
    qt = [n for s, n in subs.items() if s in QT_RISK]
    if len(qt) >= 2:
        findings.append(
            Finding(
                code="QT",
                severity="warning",
                title=f"Kumulatívne predĺženie QT intervalu — {len(qt)} liekov",
                detail=f"{', '.join(qt)}. Kombinácia zvyšuje riziko torsade de pointes, najmä pri hypokaliémii.",
                drugs=qt,
                action="Odporučiť EKG a kontrolu kália.",
            )
        )

    # ── Polypharmacy ───────────────────────────────────────────────────────────
    if len(items) >= 5:
        findings.append(
            Finding(
                code="POLYPHARMACY",
                severity="info",
                title=f"Polyfarmácia — {len(items)} liekov súčasne",
                detail="Pri piatich a viac liekoch stúpa riziko liekovej chyby približne o 30 % a exponenciálne rastie počet možných interakcií.",
                drugs=[],
                action="Kandidát na štruktúrovanú revíziu medikácie.",
            )
        )

    return findings


def allergy_check(items: list[dict], patient: Patient) -> list[Finding]:
    """Naive substring match of the patient's declared allergies against the regimen."""
    findings = []
    for allergen in patient.allergies:
        a = allergen.strip().lower()
        if not a:
            continue
        for it in items:
            sub = (it.get("active_substance") or "").lower()
            trade = (it.get("trade_name") or "").lower()
            if a in sub or a in trade:
                findings.append(
                    Finding(
                        code="ALLERGY",
                        severity="critical",
                        title=f"Zaznamenaná alergia — {it.get('trade_name')}",
                        detail=f"Pacient má v profile uvedenú alergiu na „{allergen}“, ktorá zodpovedá účinnej látke {it.get('active_substance')}.",
                        drugs=[it.get("trade_name")],
                        action="Nevydať. Kontaktovať predpisujúceho lekára.",
                    )
                )
    return findings
