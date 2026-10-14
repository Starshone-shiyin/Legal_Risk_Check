from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


DEFAULT_SUPPLY_CHAIN_PATH = Path("data/supply_chain.json")


class SupplyChainRepository:
    """Small file-backed store until a tenant-scoped database is connected."""

    def __init__(self, path: Path = DEFAULT_SUPPLY_CHAIN_PATH) -> None:
        self.path = path
        self._lock = threading.RLock()

    def load(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.path.exists():
                return []
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            suppliers = payload.get("suppliers", []) if isinstance(payload, dict) else []
            if not isinstance(suppliers, list):
                raise ValueError("supply_chain.suppliers must be a list")
            return suppliers

    def save(self, suppliers: list[dict[str, Any]]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            target = self.path
            temporary = target.with_suffix(".tmp")
            temporary.write_text(
                json.dumps({"version": 1, "suppliers": suppliers}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(target)
