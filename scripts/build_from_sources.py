#!/usr/bin/env python3
"""
Build PharmCheck SK database from open-source data:
  1. Czech SÚKL drug catalog (dlp_lecivepripravky.csv) → drug names, ATC codes, forms
  2. Czech SÚKL active substances (dlp_lecivelatky.csv) → INN names
  3. Czech SÚKL composition (dlp_slozeni.csv) → links drugs to substances
  4. DDInter v1 CSVs → drug-drug interactions with severity

Maps via active substance (INN) names between SÚKL drugs and DDInter interactions.
"""

import csv
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "backend" / "data" / "pharmcheck.db"
DATA_DIR = Path(__file__).parent.parent / "data"
SUKL_DIR = DATA_DIR / "sukl_cz"
DDINTER_DIR = DATA_DIR / "ddinter_raw"


def read_csv_win1250(filepath, delimiter=";"):
    """Read a CSV file with Windows-1250 encoding."""
    rows = []
    with open(filepath, encoding="windows-1250", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)
    return rows


# Common salt forms to strip when matching to DDInter
SALT_SUFFIXES = [
    " hydrochloride", " sodium", " potassium", " calcium", " maleate",
    " fumarate", " succinate", " tartrate", " mesylate", " besylate",
    " acetate", " phosphate", " sulfate", " citrate", " bromide",
    " nitrate", " oxide", " dihydrate", " monohydrate", " trihydrate",
    " hemihydrate", " decanoate", " valerate", " propionate",
    " disodium", " dipotassium", " meglumine", " erbumine",
    " hemifumarate", " hemisulfate", " hydrobromide",
    " dihydrochloride", " trihydrochloride",
]


def normalize_substance(name):
    """Strip salt forms from substance name for DDInter matching."""
    n = name.lower().strip()
    for suffix in SALT_SUFFIXES:
        if n.endswith(suffix):
            n = n[: -len(suffix)]
            break
    return n


def build_substance_map():
    """Build substance code → (full_name, normalized_name) mapping from dlp_lecivelatky.csv."""
    rows = read_csv_win1250(SUKL_DIR / "dlp_lecivelatky.csv")
    substance_map = {}
    for r in rows:
        code = r.get("KOD_LATKY", "").strip()
        inn = r.get("NAZEV_EN", "").strip()  # English INN name
        if code and inn:
            substance_map[code] = {
                "full": inn.lower(),
                "normalized": normalize_substance(inn),
            }
    print(f"  Načítaných {len(substance_map)} účinných látok")
    return substance_map


def build_composition_map():
    """Build drug SUKL code → list of active substance codes from dlp_slozeni.csv.
    Only includes S='L' (léčivá = active substance), filtering out excipients (S='X')."""
    rows = read_csv_win1250(SUKL_DIR / "dlp_slozeni.csv")
    comp = defaultdict(set)
    for r in rows:
        sukl = r.get("KOD_SUKL", "").strip()
        latka = r.get("KOD_LATKY", "").strip()
        typ = r.get("S", "").strip()
        # L = léčivá (active substance), skip X (excipient), O, etc.
        if sukl and latka and typ == "L":
            comp[sukl].add(latka)
    print(f"  Načítaných {len(comp)} zložení liekov (iba účinné látky)")
    return comp


def load_drugs(substance_map, composition_map):
    """Load drugs from dlp_lecivepripravky.csv, filter to active registrations."""
    rows = read_csv_win1250(SUKL_DIR / "dlp_lecivepripravky.csv")

    drugs = []
    seen_names = set()

    for r in rows:
        reg = r.get("REG", "").strip()
        # Only include registered drugs (R = registered)
        if reg != "R":
            continue

        sukl_code = r.get("KOD_SUKL", "").strip()
        name = r.get("NAZEV", "").strip()
        strength = r.get("SILA", "").strip()
        form = r.get("FORMA", "").strip()
        atc = r.get("ATC_WHO", "").strip()

        if not name:
            continue

        # Build display name
        display_name = name
        if strength:
            display_name = f"{name} {strength}"

        # Deduplicate by display name (keep first occurrence)
        if display_name in seen_names:
            continue
        seen_names.add(display_name)

        # Get active substance from composition
        substance_codes = composition_map.get(sukl_code, set())
        substances = []
        for sc in substance_codes:
            info = substance_map.get(sc)
            if info:
                # Store normalized name for DDInter matching
                substances.append(info["normalized"])

        # Use first substance as primary, join if multiple
        active_substance = ", ".join(sorted(substances)) if substances else ""

        if not active_substance and not atc:
            continue  # Skip if we have no way to map interactions

        drugs.append({
            "trade_name": display_name,
            "active_substance": active_substance,
            "atc_code": atc or None,
            "strength": strength or None,
            "form": form or None,
            "sukl_code": sukl_code,
        })

    print(f"  Načítaných {len(drugs)} registrovaných liekov")
    return drugs


def load_ddinter_interactions():
    """Load all DDInter CSV files and build interaction records."""
    interactions = {}
    drug_name_set = set()

    for csv_file in sorted(DDINTER_DIR.glob("ddinter_downloads_code_*.csv")):
        with open(csv_file, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                drug_a = row.get("Drug_A", "").strip().lower()
                drug_b = row.get("Drug_B", "").strip().lower()
                level = row.get("Level", "").strip()

                if not drug_a or not drug_b or not level:
                    continue

                # Normalize severity to Slovak
                severity_map = {
                    "Major": "Závažná",
                    "Moderate": "Stredná",
                    "Minor": "Mierna",
                    "Unknown": "Stredná",  # Default unknown to Stredná
                }
                severity = severity_map.get(level, "Stredná")

                # Deduplicate (A,B) and (B,A)
                pair = tuple(sorted([drug_a, drug_b]))
                if pair not in interactions:
                    interactions[pair] = severity

                drug_name_set.add(drug_a)
                drug_name_set.add(drug_b)

    print(f"  Načítaných {len(interactions)} unikátnych interakcií z DDInter")
    print(f"  DDInter obsahuje {len(drug_name_set)} unikátnych názvov liekov")
    return interactions, drug_name_set


def build_mapping(drugs, ddinter_drug_names):
    """Map SÚKL drugs to DDInter drug names via active substance (INN)."""
    # DDInter uses INN / generic drug names (lowercased)
    # SÚKL has active_substance field with INN names

    substance_to_ddinter = {}
    for dname in ddinter_drug_names:
        substance_to_ddinter[dname] = dname

    mapped = 0
    for drug in drugs:
        substances = [s.strip() for s in drug["active_substance"].split(",")]
        drug["_ddinter_names"] = []
        for s in substances:
            if s in substance_to_ddinter:
                drug["_ddinter_names"].append(s)
                mapped += 1

    drugs_with_mapping = [d for d in drugs if d.get("_ddinter_names")]
    print(f"  Namapovaných {len(drugs_with_mapping)} liekov na DDInter ({mapped} väzieb)")
    return drugs


def seed_database(drugs, interactions):
    """Create and populate the database."""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.database import init_db
    init_db()

    conn = sqlite3.connect(str(DB_PATH))

    # Insert drugs
    drug_rows = []
    for d in drugs:
        drug_rows.append((
            d["trade_name"],
            d["active_substance"],
            d["atc_code"],
            d["strength"],
            d["form"],
            d["sukl_code"],
        ))

    conn.executemany(
        "INSERT INTO drugs (trade_name, active_substance, atc_code, strength, form, sukl_code) VALUES (?, ?, ?, ?, ?, ?)",
        drug_rows,
    )

    # Add drugs registered in Slovakia but not in Czech Republic
    sk_only_drugs = [
        ("Jumex 5 mg", "selegiline", "N04BD01", "5 mg", "tableta", "SKL-EXT-001"),
        ("Jumex 10 mg", "selegiline", "N04BD01", "10 mg", "tableta", "SKL-EXT-002"),
        ("Selegilín Mylan 5 mg", "selegiline", "N04BD01", "5 mg", "tableta", "SKL-EXT-003"),
        ("Niar 5 mg", "selegiline", "N04BD01", "5 mg", "tableta", "SKL-EXT-004"),
        ("Paralen 500", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-EXT-010"),
        ("Paralen Extra", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-EXT-011"),
        ("Paralen Grip", "paracetamol", "N02BE01", "500 mg", "tableta", "SKL-EXT-012"),
        ("Ibalgin 400", "ibuprofen", "M01AE01", "400 mg", "tableta", "SKL-EXT-013"),
        ("Nurofen 400", "ibuprofen", "M01AE01", "400 mg", "tableta", "SKL-EXT-014"),
        ("Warfarin Orion 5 mg", "warfarin", "B01AA03", "5 mg", "tableta", "SKL-EXT-015"),
        ("Warfarin Orion 3 mg", "warfarin", "B01AA03", "3 mg", "tableta", "SKL-EXT-016"),
        ("Helicid 20 mg", "omeprazole", "A02BC01", "20 mg", "kapsula", "SKL-EXT-017"),
        ("Simvacard 20 mg", "simvastatin", "C10AA01", "20 mg", "tableta", "SKL-EXT-018"),
        ("Zoloft 50 mg", "sertraline", "N06AB06", "50 mg", "tableta", "SKL-EXT-019"),
        ("Ciprinol 500 mg", "ciprofloxacin", "J01MA02", "500 mg", "tableta", "SKL-EXT-020"),
        ("Siofor 850 mg", "metformin", "A10BA02", "850 mg", "tableta", "SKL-EXT-021"),
        ("Tramal 50 mg", "tramadol", "N02AX02", "50 mg", "kapsula", "SKL-EXT-022"),
        ("Tritace 5 mg", "ramipril", "C09AA05", "5 mg", "tableta", "SKL-EXT-023"),
        ("Enap 10 mg", "enalapril", "C09AA02", "10 mg", "tableta", "SKL-EXT-024"),
        ("Concor 5 mg", "bisoprolol", "C07AB07", "5 mg", "tableta", "SKL-EXT-025"),
        ("Euthyrox 100", "levothyroxine", "H03AA01", "100 mcg", "tableta", "SKL-EXT-026"),
        ("Lexaurin 3 mg", "bromazepam", "N05BA08", "3 mg", "tableta", "SKL-EXT-027"),
        ("Stilnox 10 mg", "zolpidem", "N05CF02", "10 mg", "tableta", "SKL-EXT-028"),
        ("Cipralex 10 mg", "escitalopram", "N06AB10", "10 mg", "tableta", "SKL-EXT-029"),
        ("Plavix 75 mg", "clopidogrel", "B01AC04", "75 mg", "tableta", "SKL-EXT-030"),
        ("Xarelto 20 mg", "rivaroxaban", "B01AF01", "20 mg", "tableta", "SKL-EXT-031"),
        ("Eliquis 5 mg", "apixaban", "B01AF02", "5 mg", "tableta", "SKL-EXT-032"),
        ("Lithium Carbonicum 300 mg", "lithium", "N05AN01", "300 mg", "tableta", "SKL-EXT-033"),
        ("Cordarone 200 mg", "amiodarone", "C01BD01", "200 mg", "tableta", "SKL-EXT-034"),
        ("Digoxin 0,25 mg", "digoxin", "C01AA05", "0.25 mg", "tableta", "SKL-EXT-035"),
        ("Verospiron 25 mg", "spironolactone", "C03DA01", "25 mg", "tableta", "SKL-EXT-036"),
        ("Aspirin 100 mg", "acetylsalicylic acid", "B01AC06", "100 mg", "tableta", "SKL-EXT-037"),
        ("Godasal 100 mg", "acetylsalicylic acid", "B01AC06", "100 mg", "tableta", "SKL-EXT-038"),
        ("Voltaren 50 mg", "diclofenac", "M01AB05", "50 mg", "tableta", "SKL-EXT-039"),
        ("Nalgesin Forte", "naproxen", "M01AE02", "550 mg", "tableta", "SKL-EXT-040"),
        ("Fromilid 500 mg", "clarithromycin", "J01FA09", "500 mg", "tableta", "SKL-EXT-041"),
        ("Tegretol 200 mg", "carbamazepine", "N03AF01", "200 mg", "tableta", "SKL-EXT-042"),
        ("Prednison 5 mg", "prednisone", "H02AB07", "5 mg", "tableta", "SKL-EXT-043"),
        ("Milurit 300 mg", "allopurinol", "M04AA01", "300 mg", "tableta", "SKL-EXT-044"),
        ("Clexane 4000 IU", "enoxaparin", "B01AB05", "40 mg/0.4 ml", "injekcia", "SKL-EXT-045"),
        ("Aurorix 150 mg", "moclobemide", "N06AG02", "150 mg", "tableta", "SKL-EXT-046"),
        ("Azilect 1 mg", "rasagiline", "N04BD02", "1 mg", "tableta", "SKL-EXT-047"),
    ]
    conn.executemany(
        "INSERT INTO drugs (trade_name, active_substance, atc_code, strength, form, sukl_code) VALUES (?, ?, ?, ?, ?, ?)",
        sk_only_drugs,
    )
    print(f"  Pridaných {len(sk_only_drugs)} slovenských liekov")

    # Build substance → drug interactions lookup
    # For each drug pair, check if their active substances have a DDInter interaction
    substance_interactions = {}
    for (drug_a, drug_b), severity in interactions.items():
        substance_interactions[(drug_a, drug_b)] = severity
        substance_interactions[(drug_b, drug_a)] = severity

    # Insert interactions - we store at substance level
    # Get unique substance pairs from DDInter
    interaction_rows = []
    for (drug_a, drug_b), severity in interactions.items():
        interaction_rows.append((
            drug_a,   # substance name
            None,     # no ATC in DDInter CSV
            drug_b,
            None,
            severity,
            None,     # no mechanism in DDInter CSV download
            None,     # no management
            None,     # no alternatives
        ))

    conn.executemany(
        "INSERT INTO interactions (drug_a, drug_a_atc, drug_b, drug_b_atc, severity, mechanism, management, alternatives) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        interaction_rows,
    )

    conn.commit()

    # Stats
    drug_count = conn.execute("SELECT COUNT(*) FROM drugs").fetchone()[0]
    interaction_count = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    mapped_drugs = conn.execute(
        "SELECT COUNT(DISTINCT d.id) FROM drugs d "
        "JOIN interactions i ON LOWER(d.active_substance) = i.drug_a OR LOWER(d.active_substance) = i.drug_b"
    ).fetchone()[0]

    severity_counts = {}
    for row in conn.execute("SELECT severity, COUNT(*) FROM interactions GROUP BY severity").fetchall():
        severity_counts[row[0]] = row[1]

    print(f"\n=== Databáza vytvorená ===")
    print(f"  Liekov: {drug_count}")
    print(f"  Interakcií: {interaction_count}")
    print(f"  Liekov s aspoň 1 interakciou: {mapped_drugs}")
    for sev, count in sorted(severity_counts.items()):
        print(f"    {sev}: {count}")

    conn.close()


def main():
    print("1. Načítavanie účinných látok zo SÚKL...")
    substance_map = build_substance_map()

    print("2. Načítavanie zložení liekov zo SÚKL...")
    composition_map = build_composition_map()

    print("3. Načítavanie liekov zo SÚKL...")
    drugs = load_drugs(substance_map, composition_map)

    print("4. Načítavanie interakcií z DDInter...")
    interactions, ddinter_names = load_ddinter_interactions()

    print("5. Mapovanie liekov na DDInter...")
    drugs = build_mapping(drugs, ddinter_names)

    print("6. Vytváranie databázy...")
    seed_database(drugs, interactions)

    print("\nHotovo!")


if __name__ == "__main__":
    main()
