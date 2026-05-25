"""Vets / breeders / shelters / owners — role lookup."""

from typing import Optional

from .schema import get_conn

ROLE_VET = "vet"
ROLE_BREEDER = "breeder"
ROLE_SHELTER = "shelter"
ROLE_OWNER = "owner"


def lookup_actor(key: str) -> Optional[dict]:
    """Return {'role': ..., 'name': ..., 'key': ...} or None if key unknown."""
    conn = get_conn()
    try:
        for role, table, extra in [
            (ROLE_VET, "vets", "signed_by_izba"),
            (ROLE_BREEDER, "breeders", "registered"),
            (ROLE_SHELTER, "shelters", None),
            (ROLE_OWNER, "owners", None),
        ]:
            cols = "key, name"
            if extra:
                cols += f", {extra}"
            row = conn.execute(
                f"SELECT {cols} FROM {table} WHERE key = ?", (key,)
            ).fetchone()
            if row:
                actor = {"role": role, "key": row["key"], "name": row["name"]}
                if extra:
                    actor[extra] = bool(row[extra])
                return actor
        return None
    finally:
        conn.close()
