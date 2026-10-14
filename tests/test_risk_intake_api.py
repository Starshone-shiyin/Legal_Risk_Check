from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from src.external_risk.schemas import ExternalRiskSignal
from src.internal_risk.service import InternalRiskWorkflowService
from src.main import app
from src.risk_intake.service import RiskIntakeService


class RiskIntakeApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_demo_identity = os.environ.get("RISK_DEMO_IDENTITY_ENABLED")
        os.environ["RISK_DEMO_IDENTITY_ENABLED"] = "true"
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        intake_path = root / "risk_intake.json"
        workflow_path = root / "internal_risk_workflow.json"
        intake_path.write_text(Path("tests/fixtures/regression/risk_intake.json").read_text(encoding="utf-8"), encoding="utf-8")
        workflow_path.write_text(Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.signal = ExternalRiskSignal(
            signal_id="signal-cloud-api-001",
            signal_type="policy",
            title="境外云服务商数据规则更新",
            severity="high",
            direction="negative",
            as_of="2026-07-31T09:00:00+08:00",
            entity="外部监管来源",
            metric="policy_update",
            affected_domains=["data_compliance"],
            affected_supply_links=["supplier-overseas-cloud"],
            evidence="监管要求发生更新，需核验现有数据处理安排。",
            source="https://example.test/regulation",
            confidence=0.92,
        )
        external_service = Mock()
        external_service.signals.return_value = [self.signal]
        self.service = RiskIntakeService(
            intake_path,
            external_service=external_service,
            internal_service=InternalRiskWorkflowService(workflow_path),
        )
        from src.risk_intake import router as risk_intake_router

        self.router_module = risk_intake_router
        self.original_service = risk_intake_router.service
        risk_intake_router.service = self.service
        from src.internal_risk import router as internal_risk_router

        self.internal_router_module = internal_risk_router
        self.original_internal_service = internal_risk_router.service
        internal_risk_router.service = self.service.internal_service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.router_module.service = self.original_service
        self.internal_router_module.service = self.original_internal_service
        if self.previous_demo_identity is None:
            os.environ.pop("RISK_DEMO_IDENTITY_ENABLED", None)
        else:
            os.environ["RISK_DEMO_IDENTITY_ENABLED"] = self.previous_demo_identity
        self.temporary_directory.cleanup()

    def test_sync_is_idempotent_and_unmatched_company_is_isolated(self) -> None:
        first = self.client.post("/risk-intake/external-cases/sync", params={"company_id": "demo-ai-enterprise"})
        second = self.client.post("/risk-intake/external-cases/sync", params={"company_id": "demo-ai-enterprise"})
        isolated = self.client.get("/risk-intake/external-cases", params={"company_id": "another-company"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["items"][0]["intake_id"], second.json()["items"][0]["intake_id"])
        self.assertEqual(isolated.status_code, 403)

    def test_sync_summary_exposes_source_health_and_batch_counts(self) -> None:
        self.client.post("/risk-intake/external-cases/sync", params={"company_id": "demo-ai-enterprise"})
        response = self.client.get(
            "/risk-intake/external-cases/sync-summary",
            params={"company_id": "demo-ai-enterprise"},
        )

        self.assertEqual(response.status_code, 200)
        batch = response.json()["items"][0]
        self.assertEqual(batch["signals_received"], 1)
        self.assertEqual(batch["new_case_count"], 1)
        self.assertEqual(batch["source_health"]["status"], "manual")

    def test_triage_promotion_creates_one_draft_event_and_cannot_repeat(self) -> None:
        case = self.client.post(
            "/risk-intake/external-cases/sync", params={"company_id": "demo-ai-enterprise"}
        ).json()["items"][0]
        promote = self.client.patch(
            f"/risk-intake/external-cases/{case['intake_id']}/triage",
            json={
                "decision": "promote",
                "reviewer": "风险治理负责人",
                "conclusion": "与登记供应商精确匹配，转入事实核验。",
            },
        )
        repeated = self.client.patch(
            f"/risk-intake/external-cases/{case['intake_id']}/triage",
            json={
                "decision": "promote",
                "reviewer": "风险治理负责人",
                "conclusion": "重复请求。",
            },
        )
        event_id = promote.json()["data"]["internal_event_id"]
        event = self.client.get("/internal-risk/events").json()["items"]

        self.assertEqual(promote.status_code, 200)
        self.assertEqual(promote.json()["data"]["status"], "promoted")
        self.assertEqual(repeated.status_code, 409)
        self.assertEqual(len([item for item in event if item["event_id"] == event_id]), 1)
        self.assertEqual(next(item for item in event if item["event_id"] == event_id)["status"], "draft")

    def test_lifecycle_transition_exposes_an_auditable_history_record(self) -> None:
        response = self.client.post(
            "/risk-intake/scopes/demo-ai-enterprise/lifecycle-states/state-project-research/transitions",
            json={
                "business_stage": "product",
                "control_stage": "product_launch",
                "status": "active",
                "changed_by": "产品合规负责人",
                "basis": "完成验证并经产品准入闸门有条件批准。",
                "gate_id": "gate-product-launch-001",
            },
        )
        scope = self.client.get("/risk-intake/scopes/demo-ai-enterprise")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transition"]["gate_decision"], "conditional_approval")
        self.assertEqual(scope.json()["data"]["lifecycle_state_history"][-1]["changed_by"], "demo-risk-operator")


if __name__ == "__main__":
    unittest.main()
