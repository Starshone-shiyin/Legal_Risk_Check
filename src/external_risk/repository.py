from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from src.external_risk.contracts import EXTERNAL_RISK_FIXTURE_VERSION


DEFAULT_EXTERNAL_RISK_FIXTURE_PATH = Path("tests/fixtures/external_risk_context_v0.1.0.json")


class ExternalRiskDataError(RuntimeError):
    pass


class ExternalRiskRepository(Protocol):
    source_name: str

    def load_payload(self) -> dict[str, Any]:
        ...


class FixtureExternalRiskRepository:
    source_name = "fixture_sample"

    def __init__(self, fixture_path: Path = DEFAULT_EXTERNAL_RISK_FIXTURE_PATH) -> None:
        self.fixture_path = fixture_path

    def load_payload(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ExternalRiskDataError(f"external risk fixture unavailable: {self.fixture_path}") from exc
        except json.JSONDecodeError as exc:
            raise ExternalRiskDataError(f"external risk fixture is invalid JSON: {self.fixture_path}") from exc
        if payload.get("version") != EXTERNAL_RISK_FIXTURE_VERSION:
            raise ExternalRiskDataError(
                f"external risk fixture version mismatch: expected {EXTERNAL_RISK_FIXTURE_VERSION}, got {payload.get('version')}"
            )
        return payload
