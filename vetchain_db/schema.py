"""Connection, schema, migrations, and shared time helpers."""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "vetchain.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today_iso() -> str:
    return datetime.now().date().isoformat()


def _create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS vets (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            license_no TEXT NOT NULL,
            signed_by_izba INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS breeders (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            federation TEXT NOT NULL,
            registered INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS shelters (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS owners (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS animals (
            chip_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            sex TEXT,
            birth_date TEXT,
            owner_key TEXT,
            breeder_key TEXT,
            shelter_key TEXT,
            shared_key BLOB NOT NULL,
            vaccines_ok INTEGER NOT NULL DEFAULT 0,
            neutered INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS pending_animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            sex TEXT,
            birth_date TEXT,
            owner_key TEXT,
            breeder_key TEXT,
            shelter_key TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chip_id TEXT NOT NULL,
            vet_key TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            visit_type TEXT NOT NULL,
            med_data BLOB,
            fin_data BLOB,
            doc_hash TEXT,
            block_ts TEXT NOT NULL,
            FOREIGN KEY (chip_id) REFERENCES animals(chip_id),
            FOREIGN KEY (vet_key) REFERENCES vets(key)
        );

        CREATE TABLE IF NOT EXISTS medical_exceptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chip_id TEXT NOT NULL,
            vet_key TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            block_ts TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS temp_keys (
            token TEXT PRIMARY KEY,
            chip_id TEXT NOT NULL,
            owner_key TEXT NOT NULL,
            key_b64 TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS cites_certs (
            chip_id TEXT PRIMARY KEY,
            ministry_sig TEXT NOT NULL,
            issued_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sbts (
            chip_id TEXT PRIMARY KEY,
            breeder_key TEXT NOT NULL,
            generated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pedigree (
            chip_id TEXT NOT NULL,
            generation INTEGER NOT NULL,
            verified INTEGER NOT NULL,
            PRIMARY KEY (chip_id, generation)
        );
        """
    )
    conn.commit()


def _flags_for_visit_type(visit_type: str) -> dict:
    """Map visit type → animal flag updates (vaccines_ok / neutered)."""
    t = visit_type.lower()
    updates = {}
    if "szczepien" in t or "wścieklizn" in t or "wscieklizn" in t:
        updates["vaccines_ok"] = 1
    if "kastracj" in t or "sterylizacj" in t:
        updates["neutered"] = 1
    return updates


def _apply_animal_flags(conn: sqlite3.Connection, chip_id: str, visit_type: str) -> None:
    updates = _flags_for_visit_type(visit_type)
    if not updates:
        return
    sets = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [chip_id]
    conn.execute(f"UPDATE animals SET {sets} WHERE chip_id = ?", params)


def _migrate_flags_from_visits(conn: sqlite3.Connection) -> None:
    """Idempotent: re-derive vaccines_ok/neutered for every animal from visit history."""
    rows = conn.execute(
        "SELECT DISTINCT chip_id, visit_type FROM visits WHERE visit_type IS NOT NULL"
    ).fetchall()
    for r in rows:
        _apply_animal_flags(conn, r["chip_id"], r["visit_type"])
    conn.commit()


def init_db() -> None:
    """Idempotent: create schema, seed first-run, run migrations."""
    from .seed import seed_first_run

    conn = get_conn()
    try:
        _create_schema(conn)
        seed_first_run(conn)
        _migrate_flags_from_visits(conn)
    finally:
        conn.close()
