"""Visits + medical exceptions: insert, reveal, query."""

from datetime import datetime, timedelta
from typing import Optional

from vetchain_crypto import VetChainCrypto

from .animals import UnknownChipError, get_animal
from .schema import _apply_animal_flags, get_conn, now_iso


class BackdateError(ValueError):
    pass


def last_visit_ts(chip_id: str) -> Optional[str]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT MAX(block_ts) AS ts FROM visits WHERE chip_id = ?", (chip_id,)
        ).fetchone()
        return row["ts"] if row and row["ts"] else None
    finally:
        conn.close()


def _validate_visit_date(chip_id: str, visit_date: str) -> None:
    """Reject if before previous block."""
    last_ts = last_visit_ts(chip_id)
    if last_ts and visit_date < last_ts[:10]:
        raise BackdateError(
            f"Wpis z datą {visit_date} jest wcześniejszy niż ostatni blok ({last_ts[:10]})."
        )


def add_visit(chip_id: str, vet_key: str, visit_date: str, visit_type: str,
              medical_text: str, financial_text: str,
              doc_hash: Optional[str] = None) -> int:
    """Insert encrypted visit. Rejects backdates."""
    animal = get_animal(chip_id)
    if not animal:
        raise UnknownChipError(f"Czip nieznany w sieci: {chip_id}")

    _validate_visit_date(chip_id, visit_date)

    enc = VetChainCrypto.encrypt_visit_data(
        animal["shared_key"], medical_text, financial_text
    )
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO visits(chip_id, vet_key, visit_date, visit_type,
               med_data, fin_data, doc_hash, block_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (chip_id, vet_key, visit_date, visit_type,
             enc["med_data"], enc["fin_data"], doc_hash, now_iso()),
        )
        _apply_animal_flags(conn, chip_id, visit_type)
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def add_commit_only_visit(chip_id: str, vet_key: str, visit_date: str,
                          visit_type: str, medical_text: str,
                          financial_text: str) -> int:
    """Commit phase: encrypt med/fin immediately, doc_hash filled in Reveal."""
    animal = get_animal(chip_id)
    if not animal:
        raise UnknownChipError(f"Czip nieznany w sieci: {chip_id}")

    _validate_visit_date(chip_id, visit_date)

    enc = VetChainCrypto.encrypt_visit_data(
        animal["shared_key"], medical_text, financial_text
    )
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO visits(chip_id, vet_key, visit_date, visit_type,
               med_data, fin_data, block_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chip_id, vet_key, visit_date, visit_type,
             enc["med_data"], enc["fin_data"], now_iso()),
        )
        _apply_animal_flags(conn, chip_id, visit_type)
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def reveal_visit_hash(visit_id: int, doc_hash: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE visits SET doc_hash = ? WHERE id = ?", (doc_hash, visit_id)
        )
        conn.commit()
    finally:
        conn.close()


def pending_reveals(vet_key: str, max_age_hours: int = 8) -> list:
    """Visits without a doc_hash, younger than max_age_hours."""
    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    conn = get_conn()
    try:
        return conn.execute(
            """SELECT id, chip_id, visit_type, block_ts FROM visits
               WHERE vet_key = ? AND doc_hash IS NULL AND block_ts > ?
               ORDER BY block_ts DESC""",
            (vet_key, cutoff),
        ).fetchall()
    finally:
        conn.close()


def recent_closed_visits(vet_key: str, limit: int = 10) -> list:
    conn = get_conn()
    try:
        return conn.execute(
            """SELECT visit_date, chip_id, visit_type FROM visits
               WHERE vet_key = ? AND doc_hash IS NOT NULL
               ORDER BY block_ts DESC LIMIT ?""",
            (vet_key, limit),
        ).fetchall()
    finally:
        conn.close()


def get_visits_for_animal(chip_id: str) -> list:
    conn = get_conn()
    try:
        return conn.execute(
            """SELECT id, visit_date, visit_type, med_data, fin_data, doc_hash, vet_key
               FROM visits WHERE chip_id = ? AND med_data IS NOT NULL
               ORDER BY visit_date ASC""",
            (chip_id,),
        ).fetchall()
    finally:
        conn.close()


def add_medical_exception(chip_id: str, vet_key: str, start_date: str,
                          end_date: str, reason: str) -> int:
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO medical_exceptions(chip_id, vet_key, start_date,
               end_date, reason, block_ts) VALUES (?, ?, ?, ?, ?, ?)""",
            (chip_id, vet_key, start_date, end_date, reason, now_iso()),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def has_medical_exception_covering(chip_id: str, date_iso: str) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            """SELECT 1 FROM medical_exceptions
               WHERE chip_id = ? AND start_date <= ? AND end_date >= ?""",
            (chip_id, date_iso, date_iso),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
