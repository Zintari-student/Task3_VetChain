"""World state — derywowany przez replay całego łańcucha."""

import base64
from dataclasses import dataclass, field


ROLE_VET = "vet"
ROLE_BREEDER = "breeder"
ROLE_SHELTER = "shelter"
ROLE_OWNER = "owner"


@dataclass
class State:
    # actor addr -> {role, name, license_no, signed_by_izba, federation, registered, pub_pem(b64)}
    actors: dict = field(default_factory=dict)
    # chip_id -> {name, species, sex, birth_date, owner, breeder, shelter, shared_key_b64,
    #             vaccines_ok, neutered, has_sbt, has_cites}
    animals: dict = field(default_factory=dict)
    # id -> {name, species, sex, birth_date, owner, breeder, shelter, created_at}
    pending_animals: dict = field(default_factory=dict)
    _pending_seq: int = 0
    # list of visit dicts: {id, chip_id, vet, visit_date, visit_type, med_b64, fin_b64,
    #                        doc_hash, block_ts}
    visits: list = field(default_factory=list)
    _visit_seq: int = 0
    # list of {chip_id, vet, start_date, end_date, reason, block_ts}
    medical_exceptions: list = field(default_factory=list)
    # token -> {chip_id, owner, key_b64, expires_at, used}
    temp_keys: dict = field(default_factory=dict)
    # chip_id -> {ministry_sig, issued_at}
    cites_certs: dict = field(default_factory=dict)
    # chip_id -> {breeder, generated_at}
    sbts: dict = field(default_factory=dict)
    # chip_id -> [gen1, gen2, gen3] booleans
    pedigree: dict = field(default_factory=dict)
    # adres -> next nonce (replay protection — opcjonalne)
    nonces: dict = field(default_factory=dict)

    def next_visit_id(self) -> int:
        self._visit_seq += 1
        return self._visit_seq

    def next_pending_id(self) -> int:
        self._pending_seq += 1
        return self._pending_seq


def shared_key_bytes(animal_record: dict) -> bytes:
    return base64.b64decode(animal_record["shared_key_b64"])
