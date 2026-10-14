from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from src.risk_intake.contracts import RISK_INTAKE_VERSION


DEFAULT_RISK_INTAKE_PATH = Path("data/risk_intake.json")


class RiskIntakeDataError(RuntimeError):
    pass


class JsonRiskIntakeRepository:
    """File-backed demonstration store; production requires tenant-scoped persistence."""

    source_name = "fixture_sample"

    def __init__(self, fixture_path: Path = DEFAULT_RISK_INTAKE_PATH) -> None:
        self.fixture_path = fixture_path
        self._lock = threading.RLock()

    def load_payload(self) -> dict[str, Any]:
        with self._lock:
            try:
                payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise RiskIntakeDataError(f"risk intake fixture unavailable: {self.fixture_path}") from exc
            except json.JSONDecodeError as exc:
                raise RiskIntakeDataError("risk intake fixture is invalid JSON") from exc
            self._validate_payload(payload)
            return payload

    def save_payload(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._validate_payload(payload)
            self.fixture_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.fixture_path.with_suffix(".tmp")
            temporary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary_path.replace(self.fixture_path)

    @staticmethod
    def _validate_payload(payload: Any) -> None:
        if not isinstance(payload, dict) or payload.get("version") != RISK_INTAKE_VERSION:
            raise RiskIntakeDataError("risk intake fixture version mismatch")
        if not isinstance(payload.get("scopes"), dict) or not isinstance(payload.get("cases"), list):
            raise RiskIntakeDataError("risk intake fixture must include scopes and cases")
        if "sync_batches" in payload and not isinstance(payload["sync_batches"], list):
            raise RiskIntakeDataError("risk intake sync batches must be a list")
