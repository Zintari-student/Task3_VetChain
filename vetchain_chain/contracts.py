"""Smart contracts — handlery dla każdego typu transakcji.

Każdy handler dostaje (state, tx, block_ts):
  - Waliduje payload + uprawnienia signera w state
  - Mutuje state przy sukcesie
  - Raise ContractError przy odrzuceniu (tx nie trafi do bloku)
"""

from datetime import datetime, timedelta

from .state import (
    ROLE_BREEDER,
    ROLE_SHELTER,
    ROLE_VET,
    State,
)
from .tx import Transaction


class ContractError(ValueError):
    """Transakcja odrzucona przez kontrakt."""


class BackdateError(ContractError):
    pass


class UnknownChipError(ContractError):
    pass


class TempKeyError(ContractError):
    pass


# ---------- helpery ----------

def _require_actor(state: State, addr: str, role: str) -> dict:
    actor = state.actors.get(addr)
    if not actor:
        raise ContractError(f"Adres {addr} nie figuruje w rejestrze aktorów.")
    if actor["role"] != role:
        raise ContractError(f"Adres {addr} ma rolę '{actor['role']}', wymagana '{role}'.")
    return actor


def _require_vet_with_izba(state: State, addr: str) -> dict:
    a = _require_actor(state, addr, ROLE_VET)
    if not a.get("signed_by_izba"):
        raise ContractError("Weterynarz bez podpisu Krajowej Izby (KILW).")
    return a


def _require_animal(state: State, chip_id: str) -> dict:
    a = state.animals.get(chip_id)
    if not a:
        raise UnknownChipError(f"Czip nieznany w sieci: {chip_id}")
    return a


def _last_visit_date(state: State, chip_id: str) -> str | None:
    visits = [v for v in state.visits if v["chip_id"] == chip_id]
    if not visits:
        return None
    return max(v["visit_date"] for v in visits)


def _flags_for_visit_type(visit_type: str) -> dict:
    t = visit_type.lower()
    updates = {}
    if "szczepien" in t or "wścieklizn" in t or "wscieklizn" in t:
        updates["vaccines_ok"] = True
    if "kastracj" in t or "sterylizacj" in t:
        updates["neutered"] = True
    return updates


# ---------- handlery ----------

def h_register_actor(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {role, name, address, pub_pem_b64, license_no?, federation?, signed_by_izba?, registered?}

    Self-registracja (signer == payload.address) lub bootstrap w genesis.
    """
    p = tx.payload
    addr = p["address"]
    if addr != tx.signer:
        raise ContractError("Self-rejestracja: signer musi być równy address w payload.")
    if addr in state.actors:
        raise ContractError(f"Adres {addr} już zarejestrowany.")
    state.actors[addr] = {
        "role": p["role"],
        "name": p["name"],
        "pub_pem_b64": p["pub_pem_b64"],
        "license_no": p.get("license_no"),
        "federation": p.get("federation"),
        "signed_by_izba": bool(p.get("signed_by_izba", False)),
        "registered": bool(p.get("registered", False)),
    }


def h_register_pending_animal(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {name, species, sex, birth_date}"""
    actor = _require_actor(state, tx.signer, ROLE_BREEDER)
    if not actor.get("registered"):
        raise ContractError("Hodowla bez aktywnego statusu (ZKwP/PKR).")
    p = tx.payload
    pid = state.next_pending_id()
    state.pending_animals[pid] = {
        "id": pid,
        "name": p["name"],
        "species": p.get("species", "Pies"),
        "sex": p.get("sex"),
        "birth_date": p.get("birth_date"),
        "owner": None,
        "breeder": tx.signer,
        "shelter": None,
        "created_at": block_ts,
    }


def h_assign_chip(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {pending_id, chip_id, shared_key_b64}"""
    _require_vet_with_izba(state, tx.signer)
    p = tx.payload
    pid = int(p["pending_id"])
    chip_id = p["chip_id"]
    if pid not in state.pending_animals:
        raise ContractError(f"Brak oczekującego zwierzęcia id={pid}.")
    if chip_id in state.animals:
        raise ContractError(f"Czip {chip_id} już zajęty.")
    row = state.pending_animals.pop(pid)
    state.animals[chip_id] = {
        "chip_id": chip_id,
        "name": row["name"],
        "species": row["species"],
        "sex": row["sex"],
        "birth_date": row["birth_date"],
        "owner": row["owner"],
        "breeder": row["breeder"],
        "shelter": row["shelter"],
        "shared_key_b64": p["shared_key_b64"],
        "vaccines_ok": False,
        "neutered": False,
    }


def h_register_shelter_animal(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {name, species, sex, birth_date, chip_id, shared_key_b64, cites_token?}"""
    _require_actor(state, tx.signer, ROLE_SHELTER)
    p = tx.payload
    chip_id = p["chip_id"]
    if chip_id in state.animals:
        raise ContractError(f"Czip {chip_id} już zajęty.")
    species = p.get("species", "Pies")
    if species == "Egzotyczne" and not p.get("cites_token"):
        raise ContractError("Gatunek egzotyczny wymaga tokenu CITES.")
    state.animals[chip_id] = {
        "chip_id": chip_id,
        "name": p["name"],
        "species": species,
        "sex": p.get("sex"),
        "birth_date": p.get("birth_date"),
        "owner": None,
        "breeder": None,
        "shelter": tx.signer,
        "shared_key_b64": p["shared_key_b64"],
        "vaccines_ok": False,
        "neutered": False,
    }
    if p.get("cites_token"):
        state.cites_certs[chip_id] = {
            "ministry_sig": p["cites_token"],
            "issued_at": block_ts,
        }


def _do_visit(state: State, tx: Transaction, block_ts: str, with_reveal: bool) -> None:
    _require_vet_with_izba(state, tx.signer)
    p = tx.payload
    chip_id = p["chip_id"]
    _require_animal(state, chip_id)
    visit_date = p["visit_date"]
    last = _last_visit_date(state, chip_id)
    if last and visit_date < last:
        raise BackdateError(
            f"Wpis z datą {visit_date} jest wcześniejszy niż ostatni blok ({last})."
        )

    visit = {
        "id": state.next_visit_id(),
        "chip_id": chip_id,
        "vet": tx.signer,
        "visit_date": visit_date,
        "visit_type": p["visit_type"],
        "med_b64": p["med_b64"],
        "fin_b64": p["fin_b64"],
        "doc_hash": p.get("doc_hash") if with_reveal else None,
        "block_ts": block_ts,
    }
    state.visits.append(visit)

    flags = _flags_for_visit_type(p["visit_type"])
    if flags:
        state.animals[chip_id].update(flags)


def h_add_visit(state: State, tx: Transaction, block_ts: str) -> None:
    """Pełny commit+reveal. Payload: {chip_id, visit_date, visit_type, med_b64, fin_b64, doc_hash}"""
    _do_visit(state, tx, block_ts, with_reveal=True)


def h_commit_only_visit(state: State, tx: Transaction, block_ts: str) -> None:
    """Tylko commit (doc_hash później). Payload: {chip_id, visit_date, visit_type, med_b64, fin_b64}"""
    _do_visit(state, tx, block_ts, with_reveal=False)


def h_reveal_hash(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {visit_id, doc_hash}"""
    _require_vet_with_izba(state, tx.signer)
    p = tx.payload
    vid = int(p["visit_id"])
    for v in state.visits:
        if v["id"] == vid:
            if v["vet"] != tx.signer:
                raise ContractError("Tylko weterynarz który zrobił commit może uzupełnić hash.")
            v["doc_hash"] = p["doc_hash"]
            return
    raise ContractError(f"Wizyta id={vid} nie istnieje.")


def h_add_medical_exception(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {chip_id, start_date, end_date, reason}"""
    _require_vet_with_izba(state, tx.signer)
    p = tx.payload
    _require_animal(state, p["chip_id"])
    state.medical_exceptions.append({
        "chip_id": p["chip_id"],
        "vet": tx.signer,
        "start_date": p["start_date"],
        "end_date": p["end_date"],
        "reason": p["reason"],
        "block_ts": block_ts,
    })


def h_issue_sbt(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {chip_id}. Hodowca z registered=True i pełnym pedigree."""
    actor = _require_actor(state, tx.signer, ROLE_BREEDER)
    if not actor.get("registered"):
        raise ContractError("Hodowla bez aktywnego statusu.")
    p = tx.payload
    animal = _require_animal(state, p["chip_id"])
    if animal["breeder"] != tx.signer:
        raise ContractError("Tylko hodowca przypisany do zwierzęcia może emitować SBT.")
    pedi = state.pedigree.get(p["chip_id"], [False, False, False])
    if not all(pedi):
        raise ContractError("Niekompletne pokolenia w rodowodzie.")
    state.sbts[p["chip_id"]] = {
        "breeder": tx.signer,
        "generated_at": block_ts,
    }


def h_set_pedigree(state: State, tx: Transaction, block_ts: str) -> None:
    """Bootstrap-only: payload {chip_id, generations: [bool, bool, bool]}. Tylko breeder."""
    _require_actor(state, tx.signer, ROLE_BREEDER)
    p = tx.payload
    if p["chip_id"] not in state.animals and p["chip_id"] not in {
        a["chip_id"] for a in [] # noop
    }:
        # Pozwalamy na ustawienie pedigree dla istniejącego lub jeszcze nie-czipowanego (ze schroniska)
        pass
    state.pedigree[p["chip_id"]] = list(p["generations"])


def h_create_temp_key(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {chip_id, token, key_b64, ttl_hours}"""
    p = tx.payload
    chip_id = p["chip_id"]
    animal = _require_animal(state, chip_id)
    if tx.signer != animal.get("owner") and tx.signer != animal.get("shelter"):
        raise ContractError("Token może wystawić tylko właściciel albo schronisko zwierzęcia.")
    if p["token"] in state.temp_keys:
        raise ContractError("Token już istnieje.")
    expires = (datetime.fromisoformat(block_ts) + timedelta(hours=int(p["ttl_hours"]))).isoformat(timespec="seconds")
    state.temp_keys[p["token"]] = {
        "chip_id": chip_id,
        "owner": tx.signer,
        "key_b64": p["key_b64"],
        "expires_at": expires,
        "used": False,
    }


def h_transfer_owner(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {chip_id, new_owner}.

    Może podpisać dotychczasowy owner, breeder (jeśli brak ownera) lub shelter
    (przy adopcji ze schroniska).
    """
    p = tx.payload
    animal = _require_animal(state, p["chip_id"])
    new_owner = p["new_owner"]
    if new_owner not in state.actors:
        raise ContractError(f"Nowy właściciel {new_owner} nie figuruje w rejestrze.")
    allowed = {animal.get("owner"), animal.get("breeder"), animal.get("shelter")} - {None}
    if tx.signer not in allowed:
        raise ContractError("Tylko obecny owner/breeder/shelter może przenieść własność.")
    animal["owner"] = new_owner


def h_consume_temp_key(state: State, tx: Transaction, block_ts: str) -> None:
    """Payload: {token}. Każdy może zgłosić, ale walidujemy stan tokenu."""
    p = tx.payload
    row = state.temp_keys.get(p["token"])
    if not row:
        raise TempKeyError("Token nieznany - odrzucony przez sieć.")
    if row["used"]:
        raise TempKeyError("Token już wykorzystany - klucz jednorazowy.")
    if row["expires_at"] < block_ts:
        raise TempKeyError(f"Token wygasł ({row['expires_at']}).")
    row["used"] = True


# ---------- dispatcher ----------

HANDLERS = {
    "register_actor": h_register_actor,
    "register_pending_animal": h_register_pending_animal,
    "assign_chip": h_assign_chip,
    "register_shelter_animal": h_register_shelter_animal,
    "add_visit": h_add_visit,
    "commit_only_visit": h_commit_only_visit,
    "reveal_hash": h_reveal_hash,
    "add_medical_exception": h_add_medical_exception,
    "issue_sbt": h_issue_sbt,
    "set_pedigree": h_set_pedigree,
    "transfer_owner": h_transfer_owner,
    "create_temp_key": h_create_temp_key,
    "consume_temp_key": h_consume_temp_key,
}


def apply_tx(state: State, tx: Transaction, block_ts: str) -> None:
    handler = HANDLERS.get(tx.type)
    if not handler:
        raise ContractError(f"Nieznany typ transakcji: {tx.type}")
    handler(state, tx, block_ts)
