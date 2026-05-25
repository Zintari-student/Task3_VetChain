"""Animals + pending_animals: create, list, search, chip assignment."""

import secrets
import sqlite3
from typing import Optional

from vetchain_crypto import VetChainCrypto

from .schema import get_conn, now_iso


class UnknownChipError(ValueError):
    pass


def get_animal(chip_id: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM animals WHERE chip_id = ?", (chip_id,)
        ).fetchone()
    finally:
        conn.close()


def list_animals_by_breeder(breeder_key: str) -> list:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM animals WHERE breeder_key = ? ORDER BY name", (breeder_key,)
        ).fetchall()
        pending = conn.execute(
            "SELECT * FROM pending_animals WHERE breeder_key = ? ORDER BY name", (breeder_key,)
        ).fetchall()
        return list(rows) + list(pending)
    finally:
        conn.close()


def list_animals_by_shelter(shelter_key: str) -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM animals WHERE shelter_key = ? ORDER BY name", (shelter_key,)
        ).fetchall()
    finally:
        conn.close()


def list_animals_by_owner(owner_key: str) -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM animals WHERE owner_key = ? ORDER BY name", (owner_key,)
        ).fetchall()
    finally:
        conn.close()


def add_pending_animal(name: str, species: str, sex: str, birth_date: str,
                       breeder_key: Optional[str] = None,
                       shelter_key: Optional[str] = None) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO pending_animals(name, species, sex, birth_date,
               breeder_key, shelter_key, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, species, sex, birth_date, breeder_key, shelter_key, now_iso()),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def register_shelter_animal(name: str, species: str, sex: str, birth_year: str,
                            chip_id: str, shelter_key: str,
                            cites_token: Optional[str] = None) -> str:
    """Register an animal taken in by a shelter. Assigns a chip if missing."""
    if not chip_id:
        chip_id = f"ISO-967000{secrets.randbelow(10**9):09d}"
    shared = VetChainCrypto.generate_shared_key()
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO animals(chip_id, name, species, sex, birth_date,
               shelter_key, shared_key) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chip_id, name, species, sex, birth_year, shelter_key, shared),
        )
        if cites_token:
            conn.execute(
                """INSERT INTO cites_certs(chip_id, ministry_sig, issued_at)
                   VALUES (?, ?, ?)""",
                (chip_id, cites_token, now_iso()),
            )
        conn.commit()
        return chip_id
    finally:
        conn.close()


def search_chip(query: str) -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT chip_id, name, species FROM animals WHERE chip_id LIKE ? LIMIT 20",
            (f"%{query}%",),
        ).fetchall()
    finally:
        conn.close()


def assign_chip_to_pending(pending_id: int, chip_id: str) -> None:
    """Move a row from pending_animals → animals with the given chip."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM pending_animals WHERE id = ?", (pending_id,)
        ).fetchone()
        if not row:
            raise UnknownChipError(f"Brak oczekującego zwierzęcia id={pending_id}")
        shared = VetChainCrypto.generate_shared_key()
        conn.execute(
            """INSERT INTO animals(chip_id, name, species, sex, birth_date,
               owner_key, breeder_key, shelter_key, shared_key)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (chip_id, row["name"], row["species"], row["sex"], row["birth_date"],
             row["owner_key"], row["breeder_key"], row["shelter_key"], shared),
        )
        conn.execute("DELETE FROM pending_animals WHERE id = ?", (pending_id,))
        conn.commit()
    finally:
        conn.close()


def list_pending_animals() -> list:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM pending_animals ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
