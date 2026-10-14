from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Protocol

from src.internal_risk.contracts import INTERNAL_RISK_WORKFLOW_VERSION


DEFAULT_INTERNAL_RISK_FIXTURE_PATH = Path("data/internal_risk_workflow.json")


class InternalRiskDataError(RuntimeError):
    pass


class InternalRiskWorkflowRepository(Protocol):
    source_name: str

    def load_payload(self) -> dict[str, Any]:
        ...

    def save_payload(self, payload: dict[str, Any]) -> None:
        ...


class JsonInternalRiskWorkflowRepository:
    """File-backed workflow store until a tenant-scoped database is connected."""

    source_name = "fixture_sample"

    def __init__(self, fixture_path: Path = DEFAULT_INTERNAL_RISK_FIXTURE_PATH) -> None:
        self.fixture_path = fixture_path
        self._lock = threading.RLock()

    def load_payload(self) -> dict[str, Any]:
        with self._lock:
            try:
                payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise InternalRiskDataError(
                    f"internal risk workflow fixture unavailable: {self.fixture_path}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise InternalRiskDataError("internal risk workflow fixture is invalid JSON") from exc
            self._validate_payload(payload)
            return payload

    def save_payload(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._validate_payload(payload)
            self.fixture_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.fixture_path.with_suffix(".tmp")
            temporary_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.fixture_path)

    @staticmethod
    def _validate_payload(payload: Any) -> None:
        if not isinstance(payload, dict):
            raise InternalRiskDataError("internal risk workflow fixture must be an object")
        if payload.get("version") != INTERNAL_RISK_WORKFLOW_VERSION:
            raise InternalRiskDataError(
                "internal risk workflow fixture version mismatch: "
                f"expected {INTERNAL_RISK_WORKFLOW_VERSION}, got {payload.get('version')}"
            )
        has_legacy_workflow = isinstance(payload.get("workflow"), dict)
        workflows = payload.get("workflows")
        has_workflows = isinstance(workflows, dict) and all(
            isinstance(company_id, str) and isinstance(workflow, dict)
            for company_id, workflow in workflows.items()
        )
        if not has_legacy_workflow and not has_workflows:
            raise InternalRiskDataError("internal risk workflow fixture missing workflow")
        if workflows is not None and not has_workflows:
            raise InternalRiskDataError("internal risk workflows must be an object keyed by company id")
        baselines = payload.get("business_state_baselines")
        if baselines is not None and not isinstance(baselines, dict):
            raise InternalRiskDataError("business state baselines must be an object")
        audit_log = payload.get("business_state_audit")
        if audit_log is not None and not isinstance(audit_log, list):
            raise InternalRiskDataError("business state audit must be a list")
        templates = payload.get("workflow_templates")
        if templates is not None and (
            not isinstance(templates, dict)
            or not all(isinstance(company_id, str) and isinstance(items, dict) for company_id, items in templates.items())
        ):
            raise InternalRiskDataError("workflow templates must be an object keyed by company id")
        registrations = payload.get("legacy_baseline_registrations")
        if registrations is not None and not isinstance(registrations, dict):
            raise InternalRiskDataError("legacy baseline registrations must be an object")
        template_audit = payload.get("workflow_template_audit")
        if template_audit is not None and not isinstance(template_audit, list):
            raise InternalRiskDataError("workflow template audit must be a list")
