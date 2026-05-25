"""VetChain DB package — re-exports all public API for backwards compatibility.

After this refactor `import vetchain_db as db` continues to work; the file-level
namespace has been split across schema/actors/animals/visits/access modules.
"""

from .access import (
    TempKeyError,
    consume_temp_key,
    create_temp_key,
    get_pedigree_status,
    has_cites_cert,
    issue_sbt,
)
from .actors import (
    ROLE_BREEDER,
    ROLE_OWNER,
    ROLE_SHELTER,
    ROLE_VET,
    lookup_actor,
)
from .animals import (
    UnknownChipError,
    add_pending_animal,
    assign_chip_to_pending,
    get_animal,
    list_animals_by_breeder,
    list_animals_by_owner,
    list_animals_by_shelter,
    list_pending_animals,
    register_shelter_animal,
    search_chip,
)
from .schema import get_conn, init_db, now_iso, today_iso
from .visits import (
    BackdateError,
    add_commit_only_visit,
    add_medical_exception,
    add_visit,
    get_visits_for_animal,
    has_medical_exception_covering,
    last_visit_ts,
    pending_reveals,
    recent_closed_visits,
    reveal_visit_hash,
)

__all__ = [
    # roles
    "ROLE_VET", "ROLE_BREEDER", "ROLE_SHELTER", "ROLE_OWNER",
    # schema
    "get_conn", "init_db", "now_iso", "today_iso",
    # actors
    "lookup_actor",
    # animals
    "UnknownChipError",
    "get_animal", "list_animals_by_breeder", "list_animals_by_shelter",
    "list_animals_by_owner", "add_pending_animal", "register_shelter_animal",
    "search_chip", "assign_chip_to_pending", "list_pending_animals",
    # visits
    "BackdateError",
    "add_visit", "add_commit_only_visit", "reveal_visit_hash",
    "pending_reveals", "recent_closed_visits", "get_visits_for_animal",
    "last_visit_ts", "add_medical_exception", "has_medical_exception_covering",
    # access
    "TempKeyError",
    "create_temp_key", "consume_temp_key", "get_pedigree_status",
    "issue_sbt", "has_cites_cert",
]
