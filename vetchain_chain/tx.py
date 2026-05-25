"""Transakcje — payload + adres sygnatariusza + podpis ECDSA."""

import json
from dataclasses import dataclass, asdict

from . import keys


@dataclass
class Transaction:
    type: str
    payload: dict
    signer: str  # adres (derive_address z pub_pem)
    nonce: int = 0
    signature: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            type=d["type"],
            payload=d["payload"],
            signer=d["signer"],
            nonce=d.get("nonce", 0),
            signature=d.get("signature", ""),
        )

    def canonical_bytes(self) -> bytes:
        """Bytes do podpisania — JSON bez pola signature, sorted keys."""
        body = {
            "type": self.type,
            "payload": self.payload,
            "signer": self.signer,
            "nonce": self.nonce,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_tx(tx: Transaction, priv_pem: bytes) -> Transaction:
    """Dopisuje podpis ECDSA do transakcji (mutuje i zwraca)."""
    tx.signature = keys.sign(priv_pem, tx.canonical_bytes())
    return tx


def verify_tx(tx: Transaction, pub_pem: bytes) -> bool:
    if not tx.signature:
        return False
    return keys.verify(pub_pem, tx.canonical_bytes(), tx.signature)
