"""Bootstrap demo: generuje 5 keypair w .demo_keys/ i wypełnia łańcuch genesis."""

import base64
import hashlib
import os

from vetchain_crypto import VetChainCrypto

from . import keys
from .chain import Chain
from .tx import Transaction, sign_tx


DEMO_KEYS_DIR = os.path.join(os.path.dirname(__file__), "..", ".demo_keys")


# Deterministyczne sekrety dla 5 ról — żeby demo wallety zawsze miały te same adresy.
# Realnie te bytes byłyby losowane, ale dla repeatability używamy fixed.
DEMO_ROLES = [
    ("vet_anna", "vet", "dr Anna Kowalska", {"license_no": "KILW-9921", "signed_by_izba": True}),
    ("vet_piotr", "vet", "dr Piotr Nowak", {"license_no": "KILW-1105", "signed_by_izba": True}),
    ("breeder_gorska", "breeder", "Hodowla Z Górskiej Doliny", {"federation": "ZKwP", "registered": True}),
    ("shelter_centrum", "shelter", "Fundacja Schronisko Centrum", {}),
    ("owner_jan", "owner", "Jan Kowalski", {}),
    ("buyer_maria", "owner", "Maria Nowak", {}),
]


def _derive_priv(label: str) -> bytes:
    """Deterministycznie wyprowadzony klucz prywatny (demo)."""
    seed = hashlib.sha256(f"vetchain-demo-2026:{label}".encode()).digest()
    return keys.priv_from_hex(seed.hex())


def _ensure_demo_dir():
    os.makedirs(DEMO_KEYS_DIR, exist_ok=True)


def _save_priv(label: str, priv_pem: bytes) -> None:
    _ensure_demo_dir()
    path = os.path.join(DEMO_KEYS_DIR, f"{label}.priv")
    if os.path.exists(path):
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(keys.priv_to_hex(priv_pem))


def _signed(priv: bytes, addr: str, ttype: str, payload: dict, nonce: int) -> Transaction:
    tx = Transaction(type=ttype, payload=payload, signer=addr, nonce=nonce)
    sign_tx(tx, priv)
    return tx


def bootstrap_demo(chain: Chain) -> None:
    """Tworzy łańcuch od zera z genesis i seed transakcjami."""
    wallets: dict[str, dict] = {}
    for label, role, name, extras in DEMO_ROLES:
        priv = _derive_priv(label)
        pub = keys.pub_pem_from_priv(priv)
        addr = keys.derive_address(pub)
        _save_priv(label, priv)
        wallets[label] = {
            "priv": priv, "pub": pub, "addr": addr,
            "role": role, "name": name, "extras": extras,
        }

    # Sequence of signed txs. Each block = jedna tx (proste, jasne dla demo).
    nonces: dict[str, int] = {}

    def n(addr):
        v = nonces.get(addr, 0)
        nonces[addr] = v + 1
        return v

    # 1) register_actor dla każdej z 6 portfeli
    for label, w in wallets.items():
        payload = {
            "address": w["addr"],
            "role": w["role"],
            "name": w["name"],
            "pub_pem_b64": base64.b64encode(w["pub"]).decode("utf-8"),
            **w["extras"],
        }
        tx = _signed(w["priv"], w["addr"], "register_actor", payload, n(w["addr"]))
        chain.submit_one(tx)

    breeder = wallets["breeder_gorska"]
    vet_anna = wallets["vet_anna"]
    shelter = wallets["shelter_centrum"]
    owner_jan = wallets["owner_jan"]

    # 2) Pending Luna (jeszcze bez czipu) — hodowca
    chain.submit_one(_signed(
        breeder["priv"], breeder["addr"], "register_pending_animal",
        {"name": "Luna (Z Górskiej Doliny)", "species": "Pies",
         "sex": "Samica", "birth_date": "2026-02-15"},
        n(breeder["addr"]),
    ))

    # 3) Schronisko: Bary i Sonia
    def _shared_b64():
        return base64.b64encode(VetChainCrypto.generate_shared_key()).decode("utf-8")

    chain.submit_one(_signed(
        shelter["priv"], shelter["addr"], "register_shelter_animal",
        {"name": "Bary", "species": "Pies", "sex": "Samiec", "birth_date": "2020",
         "chip_id": "ISO-96700000888888", "shared_key_b64": _shared_b64()},
        n(shelter["addr"]),
    ))

    chain.submit_one(_signed(
        shelter["priv"], shelter["addr"], "register_shelter_animal",
        {"name": "Sonia", "species": "Pies", "sex": "Samica", "birth_date": "2023",
         "chip_id": "ISO-96700000444444", "shared_key_b64": _shared_b64()},
        n(shelter["addr"]),
    ))

    # 4) Pierwotne czipowanie + przeniesienie własności poza prostym modelem -
    #    Bary / Sonia zostają w schronisku. Dla Reksia i Aresa: schronisko-vs-breeder
    #    nie ma; tworzymy bezpośrednio jako "shelter animals" - nie pasuje.
    #
    # Alternatywa: pre-bake'ujemy ich jako "pending" hodowcy i czipujemy.
    # Ares: pending → assign_chip → pozostaje u hodowcy.
    # Reksio: pending → assign_chip → transfer_owner do owner_jan (brak takiego tx → dodaj)
    #
    # Dla bare-minimum: zostawmy Reksia i Aresa jako pending tylko u hodowcy
    # (zostaną oczipowani podczas demo). Jeśli chcemy zobaczyć ich od razu z
    # historią wizyt — czipujemy w seedzie.

    # Pending Reksio i Ares
    chain.submit_one(_signed(
        breeder["priv"], breeder["addr"], "register_pending_animal",
        {"name": "Reksio (Z Górskiej Doliny)", "species": "Pies",
         "sex": "Samiec", "birth_date": "2024-03-12"},
        n(breeder["addr"]),
    ))
    pid_reksio = chain.state._pending_seq

    chain.submit_one(_signed(
        breeder["priv"], breeder["addr"], "register_pending_animal",
        {"name": "Ares", "species": "Pies",
         "sex": "Samiec", "birth_date": "2025-05-10"},
        n(breeder["addr"]),
    ))
    pid_ares = chain.state._pending_seq

    # Pedigree (set_pedigree)
    reksio_chip = "ISO-967000001234567"
    ares_chip = "ISO-967000008888888"

    # Vet oczipuje Reksia i Aresa
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "assign_chip",
        {"pending_id": pid_reksio, "chip_id": reksio_chip,
         "shared_key_b64": _shared_b64()},
        n(vet_anna["addr"]),
    ))
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "assign_chip",
        {"pending_id": pid_ares, "chip_id": ares_chip,
         "shared_key_b64": _shared_b64()},
        n(vet_anna["addr"]),
    ))

    # Reksio dostaje właściciela poprzez transfer_owner (z hodowcy do owner_jan)
    chain.submit_one(_signed(
        breeder["priv"], breeder["addr"], "transfer_owner",
        {"chip_id": reksio_chip, "new_owner": owner_jan["addr"]},
        n(breeder["addr"]),
    ))

    # Pedigree
    chain.submit_one(_signed(
        breeder["priv"], breeder["addr"], "set_pedigree",
        {"chip_id": reksio_chip, "generations": [True, True, True]},
        n(breeder["addr"]),
    ))
    chain.submit_one(_signed(
        breeder["priv"], breeder["addr"], "set_pedigree",
        {"chip_id": ares_chip, "generations": [True, True, False]},
        n(breeder["addr"]),
    ))

    # Bary i Sonia: szczepienia/kastracja dla Bary
    bary_chip = "ISO-96700000888888"
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "add_visit",
        {"chip_id": bary_chip, "visit_date": "2026-05-15",
         "visit_type": "Obowiązkowe szczepienie (Wścieklizna)",
         **_encrypt_pair(chain, bary_chip,
             "15.05.2026 | Szczepienie wścieklizna",
             "Koszt: 120 PLN"),
         "doc_hash": "seedhash_bary_vax"},
        n(vet_anna["addr"]),
    ))
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "add_visit",
        {"chip_id": bary_chip, "visit_date": "2026-05-20",
         "visit_type": "Kastracja / Sterylizacja",
         **_encrypt_pair(chain, bary_chip,
             "20.05.2026 | Kastracja - rutynowo",
             "Koszt: 600 PLN"),
         "doc_hash": "seedhash_bary_kast"},
        n(vet_anna["addr"]),
    ))

    # Reksio: 3 wizyty + wyjątek medyczny
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "add_visit",
        {"chip_id": reksio_chip, "visit_date": "2026-03-15",
         "visit_type": "Badanie ogólne / Kontrola",
         **_encrypt_pair(chain, reksio_chip,
             "15.03.2026 | Wykonano badanie RTG stawów.\nDowód kryptograficzny: ZGODNY.",
             "Koszt: 450 PLN"),
         "doc_hash": "seedhash_reksio_rtg"},
        n(vet_anna["addr"]),
    ))
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "add_medical_exception",
        {"chip_id": reksio_chip, "start_date": "2026-04-10", "end_date": "2026-05-10",
         "reason": "Zapalenie jelit - odroczenie szczepień"},
        n(vet_anna["addr"]),
    ))
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "add_visit",
        {"chip_id": reksio_chip, "visit_date": "2026-04-10",
         "visit_type": "Badanie ogólne / Kontrola",
         **_encrypt_pair(chain, reksio_chip,
             "10.04.2026 | Odroczenie szczepień (Wskazania medyczne).\nPowód: Leczenie gastryczne.",
             "Koszt: 150 PLN"),
         "doc_hash": "seedhash_reksio_jelita"},
        n(vet_anna["addr"]),
    ))
    chain.submit_one(_signed(
        vet_anna["priv"], vet_anna["addr"], "add_visit",
        {"chip_id": reksio_chip, "visit_date": "2026-05-24",
         "visit_type": "Obowiązkowe szczepienie (Wścieklizna)",
         **_encrypt_pair(chain, reksio_chip,
             "24.05.2026 | Szczepienie wścieklizna aktywne.\nAutoryzacja weterynarza: Pomyślna.",
             "Koszt: 120 PLN"),
         "doc_hash": "seedhash_reksio_vax"},
        n(vet_anna["addr"]),
    ))


def _encrypt_pair(chain: Chain, chip_id: str, med: str, fin: str) -> dict:
    animal = chain.state.animals[chip_id]
    shared = base64.b64decode(animal["shared_key_b64"])
    enc = VetChainCrypto.encrypt_visit_data(shared, med, fin)
    return {"med_b64": enc["med_data"], "fin_b64": enc["fin_data"]}


def load_demo_keys() -> dict[str, str]:
    """Zwraca dict {label: hex_priv} z .demo_keys/."""
    if not os.path.isdir(DEMO_KEYS_DIR):
        return {}
    out = {}
    for f in os.listdir(DEMO_KEYS_DIR):
        if f.endswith(".priv"):
            label = f.removesuffix(".priv")
            with open(os.path.join(DEMO_KEYS_DIR, f), "r", encoding="utf-8") as fh:
                out[label] = fh.read().strip()
    return out
