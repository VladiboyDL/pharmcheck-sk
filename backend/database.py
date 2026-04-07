import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "pharmcheck.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = get_db()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS drugs (
            id INTEGER PRIMARY KEY,
            trade_name TEXT NOT NULL,
            active_substance TEXT NOT NULL,
            atc_code TEXT,
            strength TEXT,
            form TEXT,
            sukl_code TEXT
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY,
            drug_a TEXT NOT NULL,
            drug_a_atc TEXT,
            drug_b TEXT NOT NULL,
            drug_b_atc TEXT,
            severity TEXT NOT NULL,
            mechanism TEXT,
            management TEXT,
            alternatives TEXT
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS drugs_fts USING fts5(
            trade_name, active_substance, content='drugs', content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS drugs_ai AFTER INSERT ON drugs BEGIN
            INSERT INTO drugs_fts(rowid, trade_name, active_substance)
            VALUES (new.id, new.trade_name, new.active_substance);
        END;

        CREATE TRIGGER IF NOT EXISTS drugs_ad AFTER DELETE ON drugs BEGIN
            INSERT INTO drugs_fts(drugs_fts, rowid, trade_name, active_substance)
            VALUES ('delete', old.id, old.trade_name, old.active_substance);
        END;

        CREATE TRIGGER IF NOT EXISTS drugs_au AFTER UPDATE ON drugs BEGIN
            INSERT INTO drugs_fts(drugs_fts, rowid, trade_name, active_substance)
            VALUES ('delete', old.id, old.trade_name, old.active_substance);
            INSERT INTO drugs_fts(rowid, trade_name, active_substance)
            VALUES (new.id, new.trade_name, new.active_substance);
        END;

        CREATE INDEX IF NOT EXISTS idx_interactions_drug_a ON interactions(LOWER(drug_a));
        CREATE INDEX IF NOT EXISTS idx_interactions_drug_b ON interactions(LOWER(drug_b));
        CREATE INDEX IF NOT EXISTS idx_interactions_atc_a ON interactions(drug_a_atc);
        CREATE INDEX IF NOT EXISTS idx_interactions_atc_b ON interactions(drug_b_atc);
        CREATE INDEX IF NOT EXISTS idx_drugs_atc ON drugs(atc_code);
        CREATE INDEX IF NOT EXISTS idx_drugs_substance ON drugs(LOWER(active_substance));
    """)
        conn.commit()
    finally:
        conn.close()
