"""Access tokens (24h temp keys), SBTs, pedigree, CITES."""

import base64
import secrets
from datetime import datetime, timedelta

from .animals import UnknownChipError, get_animal
from .schema import get_conn, now_iso


class TempKeyError(ValueError):
    pass


def create_temp_key(chip_id: str, owner_key: str, ttl_hours: int = 24) -> str:
    """Returns a UUID token. The actual decryption key is stored in DB."""
    animal = get_animal(chip_id)
    if not animal:
        raise UnknownChipError(chip_id)
    token = secrets.token_urlsafe(16)
    key_b64 = base64.b64encode(animal["shared_key"]).decode("utf-8")
    expires = (datetime.now() + timedelta(hours=ttl_hours)).isoformat(timespec="seconds")
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO temp_keys(token, chip_id, owner_key, key_b64, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (token, chip_id, owner_key, key_b64, expires),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def consume_temp_key(token: str) -> dict:
    """Validate a token, mark it used, return {chip_id, key_bytes}."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT chip_id, key_b64, expires_at, used FROM temp_keys WHERE token = ?",
            (token,),
        ).fetchone()
        if not row:
            raise TempKeyError("Token nieznany - klucz odrzucony przez sieć.")
        if row["used"]:
            raise TempKeyError("Token już wykorzystany - klucz jednorazowy.")
        if row["expires_at"] < now_iso():
            raise TempKeyError(f"Token wygasł ({row['expires_at']}).")
        conn.execute("UPDATE temp_keys SET used = 1 WHERE token = ?", (token,))
        conn.commit()
        return {
            "chip_id": row["chip_id"],
            "key_bytes": base64.b64decode(row["key_b64"]),
        }
    finally:
        conn.close()


def get_pedigree_status(chip_id: str) -> list:
    """Return [verified_gen1, verified_gen2, verified_gen3] booleans."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT generation, verified FROM pedigree WHERE chip_id = ? ORDER BY generation",
            (chip_id,),
        ).fetchall()
        if not rows:
            return [False, False, False]
        status = [False, False, False]
        for r in rows:
            if 1 <= r["generation"] <= 3:
                status[r["generation"] - 1] = bool(r["verified"])
        return status
    finally:
        conn.close()


def issue_sbt(chip_id: str, breeder_key: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO sbts(chip_id, breeder_key, generated_at)
               VALUES (?, ?, ?)""",
            (chip_id, breeder_key, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def has_cites_cert(chip_id: str) -> bool:
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT 1 FROM cites_certs WHERE chip_id = ?", (chip_id,)
        ).fetchone() is not None
    finally:
        conn.close()
