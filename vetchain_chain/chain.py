"""Append-only chain — bloki w pliku JSONL, replay na start."""

import base64
import copy
import json
import os
from typing import Optional

from .block import Block, GENESIS_PREV_HASH, make_block
from .contracts import ContractError, apply_tx
from .state import State
from .tx import Transaction, verify_tx


CHAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "vetchain_chain.jsonl")


class ChainValidationError(Exception):
    pass


class Chain:
    def __init__(self, path: str = CHAIN_PATH):
        self.path = path
        self.blocks: list[Block] = []
        self.state = State()

    # ---------- persistence ----------

    def _append_block_to_file(self, block: Block) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(block.to_dict(), sort_keys=True, separators=(",", ":")))
            f.write("\n")

    def _load_blocks(self) -> list[Block]:
        if not os.path.exists(self.path):
            return []
        blocks = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                blocks.append(Block.from_dict(json.loads(line)))
        return blocks

    # ---------- replay ----------

    def replay(self) -> None:
        """Wczytuje wszystkie bloki, weryfikuje hash chain + sygnatury + handlery."""
        blocks = self._load_blocks()
        state = State()
        prev: Optional[Block] = None
        for b in blocks:
            if not b.is_valid_chain_link(prev):
                raise ChainValidationError(
                    f"Niespójny hash chain przy bloku {b.index}."
                )
            for tx_dict in b.txs:
                tx = Transaction.from_dict(tx_dict)
                self._verify_and_apply(state, tx, b.timestamp)
            prev = b
        self.blocks = blocks
        self.state = state

    def _verify_and_apply(self, state: State, tx: Transaction, block_ts: str) -> None:
        # Genesis tx mogą nie mieć podpisu (system); znaczone signer=='0xGENESIS'
        if tx.signer != "0xGENESIS":
            actor = state.actors.get(tx.signer)
            # Wyjątek: register_actor jest self-rejestracją, więc payload niesie pub_pem
            if tx.type == "register_actor":
                pub_pem = base64.b64decode(tx.payload["pub_pem_b64"])
            elif actor:
                pub_pem = base64.b64decode(actor["pub_pem_b64"])
            else:
                raise ContractError(
                    f"Signer {tx.signer} nieznany w rejestrze i tx nie jest register_actor."
                )
            if not verify_tx(tx, pub_pem):
                raise ContractError(f"Nieprawidłowy podpis transakcji {tx.type}.")
        apply_tx(state, tx, block_ts)

    # ---------- submission ----------

    def submit(self, txs: list[Transaction]) -> Block:
        """Waliduje + appenduje nowy blok. Atomicznie: wszystko albo nic.

        Walidacja na kopii state — jeśli któryś handler zawiedzie, stan się nie zmienia.
        """
        if not txs:
            raise ValueError("Pusty zestaw transakcji.")

        prev_hash = self.blocks[-1].hash if self.blocks else GENESIS_PREV_HASH
        index = self.blocks[-1].index + 1 if self.blocks else 0
        block = make_block(index, prev_hash, txs)

        # Dry-run na kopii state
        state_copy = copy.deepcopy(self.state)
        for tx in txs:
            self._verify_and_apply(state_copy, tx, block.timestamp)

        # Sukces — persist + apply na żywym state
        self._append_block_to_file(block)
        for tx in txs:
            self._verify_and_apply(self.state, tx, block.timestamp)
        self.blocks.append(block)
        return block

    def submit_one(self, tx: Transaction) -> Block:
        return self.submit([tx])
