"""First-run seed data for the demo."""

import secrets
import sqlite3

from vetchain_crypto import VetChainCrypto

from .schema import now_iso


def seed_first_run(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM vets")
    if cur.fetchone()[0] > 0:
        return

    cur.executemany(
        "INSERT INTO vets(key, name, license_no, signed_by_izba) VALUES (?, ?, ?, 1)",
        [
            ("0xWET_9921_KILW", "dr Anna Kowalska", "KILW-9921"),
            ("0xWET_1105_KILW", "dr Piotr Nowak", "KILW-1105"),
        ],
    )
    cur.executemany(
        "INSERT INTO breeders(key, name, federation, registered) VALUES (?, ?, ?, 1)",
        [("0xHOD_8821_ZKWP", "Hodowla Z Górskiej Doliny", "ZKwP")],
    )
    cur.executemany(
        "INSERT INTO shelters(key, name) VALUES (?, ?)",
        [("0xSCHR_1102_GOV", "Fundacja Schronisko Centrum")],
    )
    cur.executemany(
        "INSERT INTO owners(key, name) VALUES (?, ?)",
        [
            ("0xOWN_9912_USER", "Jan Kowalski"),
            ("0xBUY_5532_VIEW", "Maria Nowak"),
        ],
    )

    def _key():
        return VetChainCrypto.generate_shared_key()

    animals = [
        ("ISO-967000001234567", "Reksio (Z Górskiej Doliny)", "Pies", "Samiec", "2024-03-12",
         "0xOWN_9912_USER", "0xHOD_8821_ZKWP", None, _key(), 1, 0),
        ("ISO-967000008888888", "Ares", "Pies", "Samiec", "2025-05-10",
         None, "0xHOD_8821_ZKWP", None, _key(), 1, 0),
        ("ISO-96700000888888", "Bary", "Pies", "Samiec", "2020-01-01",
         None, None, "0xSCHR_1102_GOV", _key(), 1, 1),
        ("ISO-96700000444444", "Sonia", "Pies", "Samica", "2023-01-01",
         None, None, "0xSCHR_1102_GOV", _key(), 0, 0),
    ]
    cur.executemany(
        """INSERT INTO animals(chip_id, name, species, sex, birth_date,
           owner_key, breeder_key, shelter_key, shared_key, vaccines_ok, neutered)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        animals,
    )

    cur.execute(
        """INSERT INTO pending_animals(name, species, sex, birth_date,
           owner_key, breeder_key, shelter_key, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("Luna (Z Górskiej Doliny)", "Pies", "Samica", "2026-02-15",
         None, "0xHOD_8821_ZKWP", None, now_iso()),
    )

    for chip, ok_gens in [
        ("ISO-967000001234567", [1, 1, 1]),
        ("ISO-967000008888888", [1, 1, 0]),
    ]:
        for gen_idx, verified in enumerate(ok_gens, start=1):
            cur.execute(
                "INSERT INTO pedigree(chip_id, generation, verified) VALUES (?, ?, ?)",
                (chip, gen_idx, verified),
            )

    reksio = "ISO-967000001234567"
    cur.execute("SELECT shared_key FROM animals WHERE chip_id = ?", (reksio,))
    shared = cur.fetchone()["shared_key"]

    seed_visits = [
        ("2026-03-15", "0xWET_9921_KILW", "Badanie RTG stawów",
         "15.03.2026 | Wykonano badanie RTG stawów.\nDowód kryptograficzny: ZGODNY.",
         "Koszt: 450 PLN"),
        ("2026-04-10", "0xWET_9921_KILW", "Konsultacja (Zapalenie jelit)",
         "10.04.2026 | Odroczenie szczepień (Wskazania medyczne).\nPowód: Leczenie gastryczne.",
         "Koszt: 150 PLN"),
        ("2026-05-24", "0xWET_9921_KILW", "Obowiązkowe szczepienie (Wścieklizna)",
         "24.05.2026 | Szczepienie wścieklizna aktywne.\nAutoryzacja weterynarza: Pomyślna.",
         "Koszt: 120 PLN"),
    ]
    for visit_date, vet_key, vtype, med, fin in seed_visits:
        enc = VetChainCrypto.encrypt_visit_data(shared, med, fin)
        cur.execute(
            """INSERT INTO visits(chip_id, vet_key, visit_date, visit_type,
               med_data, fin_data, doc_hash, block_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (reksio, vet_key, visit_date, vtype,
             enc["med_data"], enc["fin_data"],
             secrets.token_hex(16), visit_date + "T10:00:00"),
        )

    cur.execute(
        """INSERT INTO medical_exceptions(chip_id, vet_key, start_date, end_date, reason, block_ts)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (reksio, "0xWET_9921_KILW", "2026-04-10", "2026-05-10",
         "Zapalenie jelit - odroczenie szczepień", "2026-04-10T10:00:00"),
    )

    conn.commit()
