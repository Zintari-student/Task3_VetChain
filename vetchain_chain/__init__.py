"""Public API — mirror starego vetchain_db, ale na realnym łańcuchu bloków.

UI woła te same funkcje (lookup_actor, get_animal, add_visit...), pod spodem
buduje + podpisuje transakcję, wysyła do chain, mutuje state.
"""

from __future__ import annotations

import base64
import os
import secrets
from datetime import datetime
from typing import Optional

from vetchain_crypto import VetChainCrypto

from . import keys
from .chain import Chain
from .contracts import BackdateError, ContractError, TempKeyError, UnknownChipError
from .state import (
    ROLE_BREEDER,
    ROLE_OWNER,
    ROLE_SHELTER,
    ROLE_VET,
    State,
)
from .tx import Transaction, sign_tx


# ---------- session ----------

_chain: Optional[Chain] = None
_session_priv: Optional[bytes] = None
_session_addr: Optional[str] = None


def get_chain() -> Chain:
    if _chain is None:
        raise RuntimeError("Łańcuch nieinicjalizowany. Zawołaj init_chain() na starcie.")
    return _chain


def set_session_key(priv_pem: bytes) -> None:
    """Ustaw klucz prywatny do podpisywania kolejnych transakcji."""
    global _session_priv, _session_addr
    _session_priv = priv_pem
    _session_addr = keys.address_from_priv(priv_pem)


def clear_session() -> None:
    global _session_priv, _session_addr
    _session_priv = None
    _session_addr = None


def current_address() -> Optional[str]:
    return _session_addr


def _require_session() -> tuple[bytes, str]:
    if _session_priv is None or _session_addr is None:
        raise RuntimeError("Brak aktywnej sesji — set_session_key().")
    return _session_priv, _session_addr


# ---------- init + seed ----------

def init_chain() -> None:
    global _chain
    _chain = Chain()
    if not os.path.exists(_chain.path):
        from .seed import bootstrap_demo
        bootstrap_demo(_chain)
    else:
        _chain.replay()


# ---------- helpery czasu ----------

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today_iso() -> str:
    return datetime.now().date().isoformat()


# ---------- tx builders ----------

def _next_nonce(addr: str) -> int:
    chain = get_chain()
    n = chain.state.nonces.get(addr, 0)
    chain.state.nonces[addr] = n + 1
    return n


def _build_and_submit(tx_type: str, payload: dict) -> dict:
    priv, addr = _require_session()
    tx = Transaction(type=tx_type, payload=payload, signer=addr, nonce=_next_nonce(addr))
    sign_tx(tx, priv)
    block = get_chain().submit_one(tx)
    return {"block_index": block.index, "block_hash": block.hash}


# ---------- read-only API ----------

def lookup_actor(address_or_priv_hex: str) -> Optional[dict]:
    """Akceptuje adres '0x...' lub hex priv (64 znaki) — zwraca rekord aktora albo None."""
    chain = get_chain()
    s = address_or_priv_hex.strip()
    # Hex priv key (64 hex chars bez prefixu lub 66 z 0x)
    raw = s.removeprefix("0x")
    if len(raw) == 64 and all(c in "0123456789abcdefABCDEF" for c in raw):
        try:
            priv_pem = keys.priv_from_hex(s)
            addr = keys.address_from_priv(priv_pem)
        except Exception:
            addr = s if s.startswith("0x") else "0x" + s
    else:
        addr = s if s.startswith("0x") else "0x" + s

    actor = chain.state.actors.get(addr)
    if not actor:
        return None
    out = {"role": actor["role"], "address": addr, "key": addr, "name": actor["name"]}
    if actor["role"] == ROLE_VET:
        out["signed_by_izba"] = actor.get("signed_by_izba", False)
    if actor["role"] == ROLE_BREEDER:
        out["registered"] = actor.get("registered", False)
    return out


def get_animal(chip_id: Optional[str]) -> Optional[dict]:
    if not chip_id:
        return None
    chain = get_chain()
    a = chain.state.animals.get(chip_id)
    if not a:
        return None
    # Format zbliżony do starej sqlite3.Row (dostęp przez [klucz])
    return {
        "chip_id": a["chip_id"],
        "name": a["name"],
        "species": a["species"],
        "sex": a["sex"],
        "birth_date": a["birth_date"],
        "owner_key": a.get("owner"),
        "breeder_key": a.get("breeder"),
        "shelter_key": a.get("shelter"),
        "shared_key": base64.b64decode(a["shared_key_b64"]),
        "vaccines_ok": 1 if a.get("vaccines_ok") else 0,
        "neutered": 1 if a.get("neutered") else 0,
    }


def list_animals_by_breeder(breeder_key: str) -> list:
    chain = get_chain()
    out = []
    for chip_id, a in chain.state.animals.items():
        if a.get("breeder") == breeder_key:
            out.append({
                "chip_id": chip_id,
                "name": a["name"],
                "species": a["species"],
                "sex": a["sex"],
                "birth_date": a["birth_date"],
                "owner_key": a.get("owner"),
                "breeder_key": a.get("breeder"),
                "shelter_key": a.get("shelter"),
                "shared_key": base64.b64decode(a["shared_key_b64"]),
                "vaccines_ok": 1 if a.get("vaccines_ok") else 0,
                "neutered": 1 if a.get("neutered") else 0,
            })
    out.sort(key=lambda r: r["name"])
    pending = [
        {
            "id": p["id"],
            "name": p["name"],
            "species": p["species"],
            "sex": p["sex"],
            "birth_date": p["birth_date"],
            "owner_key": p["owner"],
            "breeder_key": p["breeder"],
            "shelter_key": p["shelter"],
            "created_at": p["created_at"],
        }
        for p in chain.state.pending_animals.values()
        if p.get("breeder") == breeder_key
    ]
    pending.sort(key=lambda r: r["name"])
    return out + pending


def list_animals_by_shelter(shelter_key: str) -> list:
    chain = get_chain()
    out = []
    for chip_id, a in chain.state.animals.items():
        if a.get("shelter") == shelter_key:
            out.append({
                "chip_id": chip_id,
                "name": a["name"],
                "species": a["species"],
                "sex": a["sex"],
                "birth_date": a["birth_date"],
                "vaccines_ok": 1 if a.get("vaccines_ok") else 0,
                "neutered": 1 if a.get("neutered") else 0,
            })
    out.sort(key=lambda r: r["name"])
    return out


def list_animals_by_owner(owner_key: str) -> list:
    chain = get_chain()
    out = []
    for chip_id, a in chain.state.animals.items():
        if a.get("owner") == owner_key:
            out.append({
                "chip_id": chip_id,
                "name": a["name"],
                "species": a["species"],
                "shared_key": base64.b64decode(a["shared_key_b64"]),
            })
    return out


def list_pending_animals() -> list:
    chain = get_chain()
    return [
        dict(p) for p in sorted(
            chain.state.pending_animals.values(),
            key=lambda x: x["created_at"], reverse=True
        )
    ]


def search_chip(query: str) -> list:
    chain = get_chain()
    return [
        {"chip_id": chip_id, "name": a["name"], "species": a["species"]}
        for chip_id, a in chain.state.animals.items()
        if query in chip_id
    ][:20]


def get_visits_for_animal(chip_id: str) -> list:
    chain = get_chain()
    out = []
    for v in chain.state.visits:
        if v["chip_id"] != chip_id:
            continue
        out.append({
            "id": v["id"],
            "visit_date": v["visit_date"],
            "visit_type": v["visit_type"],
            "med_data": v["med_b64"],
            "fin_data": v["fin_b64"],
            "doc_hash": v.get("doc_hash"),
            "vet_key": v["vet"],
        })
    out.sort(key=lambda r: r["visit_date"])
    return out


def pending_reveals(vet_key: str, max_age_hours: int = 8) -> list:
    chain = get_chain()
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    out = []
    for v in chain.state.visits:
        if v["vet"] == vet_key and not v.get("doc_hash") and v["block_ts"] > cutoff:
            out.append({
                "id": v["id"], "chip_id": v["chip_id"],
                "visit_type": v["visit_type"], "block_ts": v["block_ts"],
            })
    out.sort(key=lambda r: r["block_ts"], reverse=True)
    return out


def recent_closed_visits(vet_key: str, limit: int = 10) -> list:
    chain = get_chain()
    out = [
        {"visit_date": v["visit_date"], "chip_id": v["chip_id"], "visit_type": v["visit_type"]}
        for v in chain.state.visits
        if v["vet"] == vet_key and v.get("doc_hash")
    ]
    out.sort(key=lambda r: r["visit_date"], reverse=True)
    return out[:limit]


def has_medical_exception_covering(chip_id: str, date_iso: str) -> bool:
    chain = get_chain()
    for e in chain.state.medical_exceptions:
        if e["chip_id"] == chip_id and e["start_date"] <= date_iso <= e["end_date"]:
            return True
    return False


def get_pedigree_status(chip_id: str) -> list:
    chain = get_chain()
    return list(chain.state.pedigree.get(chip_id, [False, False, False]))


def has_cites_cert(chip_id: str) -> bool:
    return chip_id in get_chain().state.cites_certs


def last_visit_ts(chip_id: str) -> Optional[str]:
    chain = get_chain()
    ts = [v["block_ts"] for v in chain.state.visits if v["chip_id"] == chip_id]
    return max(ts) if ts else None


# ---------- write API (buduje + podpisuje + submituje) ----------

def add_pending_animal(name: str, species: str, sex: str, birth_date: str,
                       breeder_key: Optional[str] = None,
                       shelter_key: Optional[str] = None) -> int:
    chain = get_chain()
    prev_max = chain.state._pending_seq
    _build_and_submit("register_pending_animal", {
        "name": name, "species": species, "sex": sex, "birth_date": birth_date,
    })
    return chain.state._pending_seq if chain.state._pending_seq > prev_max else 0


def assign_chip_to_pending(pending_id: int, chip_id: str) -> None:
    shared = VetChainCrypto.generate_shared_key()
    _build_and_submit("assign_chip", {
        "pending_id": pending_id,
        "chip_id": chip_id,
        "shared_key_b64": base64.b64encode(shared).decode("utf-8"),
    })


def register_shelter_animal(name: str, species: str, sex: str, birth_year: str,
                             chip_id: str, shelter_key: str,
                             cites_token: Optional[str] = None) -> str:
    if not chip_id:
        chip_id = f"ISO-967000{secrets.randbelow(10**9):09d}"
    shared = VetChainCrypto.generate_shared_key()
    payload = {
        "name": name, "species": species, "sex": sex, "birth_date": birth_year,
        "chip_id": chip_id,
        "shared_key_b64": base64.b64encode(shared).decode("utf-8"),
    }
    if cites_token:
        payload["cites_token"] = cites_token
    _build_and_submit("register_shelter_animal", payload)
    return chip_id


def _encrypt_for_animal(chip_id: str, med: str, fin: str) -> dict:
    animal = get_chain().state.animals.get(chip_id)
    if not animal:
        raise UnknownChipError(f"Czip nieznany w sieci: {chip_id}")
    shared = base64.b64decode(animal["shared_key_b64"])
    return VetChainCrypto.encrypt_visit_data(shared, med, fin)


def add_visit(chip_id: str, vet_key: str, visit_date: str, visit_type: str,
              medical_text: str, financial_text: str,
              doc_hash: Optional[str] = None) -> int:
    enc = _encrypt_for_animal(chip_id, medical_text, financial_text)
    chain = get_chain()
    prev = chain.state._visit_seq
    _build_and_submit("add_visit", {
        "chip_id": chip_id, "visit_date": visit_date, "visit_type": visit_type,
        "med_b64": enc["med_data"], "fin_b64": enc["fin_data"],
        "doc_hash": doc_hash,
    })
    return chain.state._visit_seq if chain.state._visit_seq > prev else 0


def add_commit_only_visit(chip_id: str, vet_key: str, visit_date: str,
                           visit_type: str, medical_text: str,
                           financial_text: str) -> int:
    enc = _encrypt_for_animal(chip_id, medical_text, financial_text)
    chain = get_chain()
    prev = chain.state._visit_seq
    _build_and_submit("commit_only_visit", {
        "chip_id": chip_id, "visit_date": visit_date, "visit_type": visit_type,
        "med_b64": enc["med_data"], "fin_b64": enc["fin_data"],
    })
    return chain.state._visit_seq if chain.state._visit_seq > prev else 0


def reveal_visit_hash(visit_id: int, doc_hash: str) -> None:
    _build_and_submit("reveal_hash", {"visit_id": visit_id, "doc_hash": doc_hash})


def add_medical_exception(chip_id: str, vet_key: str, start_date: str,
                           end_date: str, reason: str) -> int:
    _build_and_submit("add_medical_exception", {
        "chip_id": chip_id, "start_date": start_date,
        "end_date": end_date, "reason": reason,
    })
    return len(get_chain().state.medical_exceptions)


def issue_sbt(chip_id: str, breeder_key: str) -> None:
    _build_and_submit("issue_sbt", {"chip_id": chip_id})


def create_temp_key(chip_id: str, owner_key: str, ttl_hours: int = 24) -> str:
    animal = get_chain().state.animals.get(chip_id)
    if not animal:
        raise UnknownChipError(chip_id)
    token = secrets.token_urlsafe(16)
    _build_and_submit("create_temp_key", {
        "chip_id": chip_id, "token": token,
        "key_b64": animal["shared_key_b64"],
        "ttl_hours": ttl_hours,
    })
    return token


def consume_temp_key(token: str) -> dict:
    # Sprawdź stan zanim wyślesz tx, żeby zwrócić sensowny błąd
    chain = get_chain()
    row = chain.state.temp_keys.get(token)
    if not row:
        raise TempKeyError("Token nieznany - klucz odrzucony przez sieć.")
    if row["used"]:
        raise TempKeyError("Token już wykorzystany - klucz jednorazowy.")
    if row["expires_at"] < now_iso():
        raise TempKeyError(f"Token wygasł ({row['expires_at']}).")
    chip = row["chip_id"]
    key_bytes = base64.b64decode(row["key_b64"])
    _build_and_submit("consume_temp_key", {"token": token})
    return {"chip_id": chip, "key_bytes": key_bytes}


# ---------- exports ----------

__all__ = [
    "ROLE_VET", "ROLE_BREEDER", "ROLE_SHELTER", "ROLE_OWNER",
    "BackdateError", "ContractError", "UnknownChipError", "TempKeyError",
    "init_chain", "set_session_key", "clear_session", "current_address",
    "now_iso", "today_iso",
    "lookup_actor", "get_animal",
    "list_animals_by_breeder", "list_animals_by_shelter", "list_animals_by_owner",
    "list_pending_animals", "search_chip",
    "get_visits_for_animal", "pending_reveals", "recent_closed_visits",
    "has_medical_exception_covering", "get_pedigree_status", "has_cites_cert",
    "add_pending_animal", "assign_chip_to_pending", "register_shelter_animal",
    "add_visit", "add_commit_only_visit", "reveal_visit_hash",
    "add_medical_exception", "issue_sbt",
    "create_temp_key", "consume_temp_key", "last_visit_ts",
    "get_chain",
]
