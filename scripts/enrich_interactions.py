#!/usr/bin/env python3
"""Backfill Slovak mechanism / management / alternatives onto interaction records.

DDInter gives us a severity for 160k pairs but no clinical text. A bare "Závažná" is
useless at the counter, so this pre-generates the explanation for the pairs that can
realistically appear on a Slovak prescription — ranked by how many products in the
ŠÚKL registry actually contain each substance.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 scripts/enrich_interactions.py                 # default plan, ~2 650 pairs
    python3 scripts/enrich_interactions.py --limit 200     # short test run
    python3 scripts/enrich_interactions.py --dry-run       # just show the plan

Safe to interrupt and re-run: already-enriched rows are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import sqlite3
import sys
import threading
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "backend" / "data" / "pharmcheck.db"
MODEL = "claude-haiku-4-5-20251001"

SYSTEM = """Si klinický farmakológ. Pre dvojicu účinných látok napíš stručné, prakticky
použiteľné vysvetlenie liekovej interakcie pre lekárnika za výdajným pultom.

Odpovedaj VÝHRADNE vo formáte JSON, bez akéhokoľvek iného textu:
{
  "mechanism": "Mechanizmus interakcie po slovensky, 1-2 vety. Konkrétne (CYP izoenzýmy, P-gp, farmakodynamika), nie všeobecné frázy.",
  "management": "Čo má lekárnik urobiť. 1-2 vety. Konkrétne: monitorovať čo, upraviť dávku ako, kedy kontaktovať lekára.",
  "alternatives": "Bezpečnejšia alternatíva ak existuje, 1 veta. Ak neexistuje, napíš čo monitorovať namiesto zámeny."
}

Závažnosť interakcie ti je zadaná — rešpektuj ju a prispôsob jej tón odporúčania.
Píš po slovensky, odborne ale zrozumiteľne. Bez markdown formátovania."""


def demo_plan(conn: sqlite3.Connection):
    """Exactly the pairs the six demo scenarios surface — a ~1 minute, ~$0.10 run.

    Guarantees the scripted demo never shows a bare severity, even when there is no
    time for the full backfill.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from backend.prescription import resolve
    from backend.routers.dispense import DEMO_PRESCRIPTIONS

    conn.row_factory = sqlite3.Row
    wanted: set[int] = set()

    for scenario in DEMO_PRESCRIPTIONS.values():
        items, _ = resolve(conn, scenario["text"])
        for a in items:
            for b in items:
                if a["id"] >= b["id"]:
                    continue
                for sa in (x.strip().lower() for x in a["active_substance"].split(",")):
                    for sb in (x.strip().lower() for x in b["active_substance"].split(",")):
                        if sa == sb:
                            continue
                        row = conn.execute(
                            """SELECT id FROM interactions
                               WHERE ((LOWER(drug_a)=? AND LOWER(drug_b)=?)
                                   OR (LOWER(drug_a)=? AND LOWER(drug_b)=?))
                                 AND (mechanism IS NULL OR mechanism='')""",
                            (sa, sb, sb, sa),
                        ).fetchone()
                        if row:
                            wanted.add(row["id"])

    if not wanted:
        return []
    placeholders = ",".join("?" * len(wanted))
    return conn.execute(
        f"SELECT id, drug_a, drug_b, severity FROM interactions WHERE id IN ({placeholders})",
        list(wanted),
    ).fetchall()


def build_plan(conn: sqlite3.Connection, major_top: int, moderate_top: int, limit: int | None):
    conn.execute(
        """CREATE TEMP TABLE sk_subs AS
           SELECT LOWER(TRIM(active_substance)) AS s, COUNT(*) n FROM drugs
           WHERE active_substance NOT LIKE '%,%' GROUP BY 1"""
    )

    def pairs(severity: str, top: int):
        # Ordered by how many registry products contain each substance, so a partial
        # run still covers the drugs a pharmacy actually dispenses.
        return conn.execute(
            f"""WITH t AS (SELECT s, n FROM sk_subs ORDER BY n DESC LIMIT {top})
                SELECT i.id, i.drug_a, i.drug_b, i.severity
                FROM interactions i
                JOIN t ta ON ta.s = LOWER(i.drug_a)
                JOIN t tb ON tb.s = LOWER(i.drug_b)
                WHERE i.severity = ?
                  AND (i.mechanism IS NULL OR i.mechanism = '')
                ORDER BY (ta.n + tb.n) DESC""",
            (severity,),
        ).fetchall()

    plan = pairs("Závažná", major_top) + pairs("Stredná", moderate_top)
    return plan[:limit] if limit else plan


def worker(q: queue.Queue, results: queue.Queue, api_key: str, stop: threading.Event):
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    while not stop.is_set():
        try:
            row = q.get_nowait()
        except queue.Empty:
            return
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=500,
                system=SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Účinné látky: {row['drug_a']} + {row['drug_b']}\n"
                            f"Závažnosť interakcie: {row['severity']}"
                        ),
                    }
                ],
            )
            text = resp.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            results.put(
                (
                    row["id"],
                    data.get("mechanism", "").strip(),
                    data.get("management", "").strip(),
                    data.get("alternatives", "").strip(),
                )
            )
        except Exception as e:  # keep going — a single bad pair must not kill the run
            results.put(("ERROR", row["id"], f"{row['drug_a']}+{row['drug_b']}", str(e)[:120]))
        finally:
            q.task_done()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--major-top", type=int, default=400, help="rank cutoff for Závažná pairs")
    ap.add_argument("--moderate-top", type=int, default=150, help="rank cutoff for Stredná pairs")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--demo", action="store_true",
                    help="only the pairs the six demo scenarios surface (~1 min)")
    args = ap.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ANTHROPIC_API_KEY nie je nastavený.", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    if args.demo:
        plan = demo_plan(conn)
        print("Režim: iba páry zo šiestich demo scenárov")
    else:
        plan = build_plan(conn, args.major_top, args.moderate_top, args.limit)
    majors = sum(1 for r in plan if r["severity"] == "Závažná")
    print(f"Na spracovanie: {len(plan)} párov  ({majors} závažných, {len(plan) - majors} stredných)")
    print(f"Odhad: ~{len(plan) * 0.45 / 1000:.1f}k requestov · približne ${len(plan) * 0.0013:.2f}")

    if not plan:
        print("Všetky cieľové páry už majú vysvetlenie — netreba nič robiť.")
        return 0

    if args.dry_run:
        for r in plan[:15]:
            print(f"  {r['severity']:9s} {r['drug_a']} + {r['drug_b']}")
        return 0

    q: queue.Queue = queue.Queue()
    for r in plan:
        q.put(r)
    results: queue.Queue = queue.Queue()
    stop = threading.Event()

    threads = [
        threading.Thread(target=worker, args=(q, results, api_key, stop), daemon=True)
        for _ in range(args.workers)
    ]
    for t in threads:
        t.start()

    done = errors = 0
    started = time.time()
    total = len(plan)
    try:
        while done + errors < total:
            item = results.get()
            if item[0] == "ERROR":
                errors += 1
                print(f"\n  ! {item[2]}: {item[3]}")
            else:
                iid, mech, mgmt, alts = item
                conn.execute(
                    "UPDATE interactions SET mechanism=?, management=?, alternatives=? WHERE id=?",
                    (mech, mgmt, alts, iid),
                )
                done += 1
                if done % 25 == 0:
                    conn.commit()
            elapsed = time.time() - started
            rate = (done + errors) / elapsed if elapsed else 0
            remaining = (total - done - errors) / rate if rate else 0
            print(
                f"\r  {done + errors}/{total} · {done} ok · {errors} chýb · "
                f"{rate:.1f}/s · zostáva ~{remaining / 60:.1f} min",
                end="",
                flush=True,
            )
    except KeyboardInterrupt:
        stop.set()
        print("\nPrerušené — priebeh je uložený, skript môžete spustiť znova.")
    finally:
        conn.commit()

    print(f"\n\nHotovo: {done} obohatených, {errors} chýb, {(time.time() - started) / 60:.1f} min")
    covered = conn.execute(
        "SELECT COUNT(*) FROM interactions WHERE mechanism IS NOT NULL AND mechanism != ''"
    ).fetchone()[0]
    print(f"Interakcií s vysvetlením v databáze: {covered:,}".replace(",", " "))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
