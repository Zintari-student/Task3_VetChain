"""Blok = lista transakcji + hash chain."""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime

from .tx import Transaction


GENESIS_PREV_HASH = "0" * 64


@dataclass
class Block:
    index: int
    prev_hash: str
    timestamp: str
    txs: list  # list[Transaction.to_dict()]
    hash: str = ""

    def compute_hash(self) -> str:
        body = {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "txs": self.txs,
        }
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def seal(self) -> "Block":
        self.hash = self.compute_hash()
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Block":
        return cls(
            index=d["index"],
            prev_hash=d["prev_hash"],
            timestamp=d["timestamp"],
            txs=d["txs"],
            hash=d.get("hash", ""),
        )

    def is_valid_chain_link(self, prev: "Block | None") -> bool:
        """Sprawdza hash bloku + spójność z poprzednim."""
        if self.compute_hash() != self.hash:
            return False
        if prev is None:
            return self.index == 0 and self.prev_hash == GENESIS_PREV_HASH
        return self.index == prev.index + 1 and self.prev_hash == prev.hash


def make_block(index: int, prev_hash: str, txs: list[Transaction]) -> Block:
    block = Block(
        index=index,
        prev_hash=prev_hash,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        txs=[t.to_dict() for t in txs],
    )
    return block.seal()
