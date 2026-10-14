from __future__ import annotations

import json
import hashlib
import hmac
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.internal_risk.service import InternalRiskWorkflowService
from src.main import app


class InternalRiskApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_demo_identity = os.environ.get("RISK_DEMO_IDENTITY_ENABLED")
        os.environ["RISK_DEMO_IDENTITY_ENABLED"] = "true"
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_path = Path(self.temporary_directory.name) / "internal_risk_workflow.json"
        payload = json.loads(Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"))
        cloud_task = next(task for task in payload["workflow"]["remediation_tasks"] if task["task_id"] == "task-cloud-assessment-001")
        cloud_task["status"] = "not_started"
        cloud_task["evidence_refs"] = []
        self.fixture_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        from src.internal_risk import router as internal_risk_router

        self.router_module = internal_risk_router
        self.original_service = internal_risk_router.service
        internal_risk_router.service = InternalRiskWorkflowService(self.fixture_path)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.router_module.service = self.original_service
        if self.previous_demo_identity is None:
            os.environ.pop("RISK_DEMO_IDENTITY_ENABLED", None)
        else:
            os.environ["RISK_DEMO_IDENTITY_ENABLED"] = self.previous_demo_identity
        self.temporary_directory.cleanup()

    def test_dashboard_exposes_full_internal_control_loop(self) -> None:
        response = self.client.get("/internal-risk/dashboard", params={"company_id": "demo-ai-enterprise"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(len(payload["data"]["risk_items"]), 3)
        self.assertEqual(len(payload["data"]["gates"]), 3)
        self.assertEqual(len(payload["data"]["remediation_tasks"]), 4)
        self.assertEqual(payload["meta"]["runtime_data_access"]["rag"], "not_called")

    def test_openapi_exposes_internal_risk_workflow_surface(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]

        self.assertIn("/internal-risk/workflow", paths)
        self.assertIn("/internal-risk/events", paths)
        self.assertIn("/internal-risk/events/{event_id}/assessment", paths)
        self.assertIn("/internal-risk/events/{event_id}/assessment-jobs", paths)
        self.assertIn("post", paths["/internal-risk/events/{event_id}/assessment-jobs"])
        self.assertIn("/internal-risk/assessment-jobs/{assessment_job_id}", paths)
        self.assertIn("/internal-risk/events/{event_id}/confirmation", paths)
        self.assertIn("/internal-risk/gates/{gate_id}/decision", paths)
        self.assertIn("/internal-risk/risks/{risk_id}/closure", paths)
        self.assertIn("/internal-risk/tasks/{task_id}", paths)
        self.assertIn("patch", paths["/internal-risk/tasks/{task_id}"])
        self.assertIn("/internal-risk/tasks/{task_id}/evidence", paths)
        self.assertIn("post", paths["/internal-risk/tasks/{task_id}/evidence"])
        self.assertIn("/internal-risk/reviews/{review_id}", paths)
        self.assertIn("/internal-risk/business-state/initialize", paths)
        self.assertIn("/internal-risk/business-state/reset", paths)
        self.assertIn("/internal-risk/workflow-templates", paths)
        self.assertIn("/internal-risk/workflow-templates/import", paths)
        self.assertIn("/internal-risk/workflow-templates/{template_id}/versions", paths)
        self.assertIn("/internal-risk/workflow-templates/{template_id}/audit", paths)
        self.assertIn("/internal-risk/gates/{gate_id}/blockers", paths)
        self.assertIn("/internal-risk/risks/{risk_id}/closure-blockers", paths)

    def test_signed_enterprise_can_initialize_and_audit_a_semiconductor_business_state(self) -> None:
        previous_secret = os.environ.get("RISK_GATEWAY_IDENTITY_SECRET")
        secret = "test-enterprise-access-secret"
        os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = secret
        identity = "semiconductor-owner|demo-semiconductor-materials|risk_viewer,risk_operator,risk_reviewer,risk_decision_maker"
        signature = hmac.new(secret.encode("utf-8"), identity.encode("utf-8"), hashlib.sha256).hexdigest()
        headers = {"X-Risk-Identity": identity, "X-Risk-Identity-Signature": signature}
        try:
            initialized = self.client.post(
                "/internal-risk/business-state/initialize",
                headers=headers,
                json={
                    "company_name": "华芯高纯材料（模拟）有限公司",
                    "industry": "半导体设备上游材料",
                    "business_model": "to_b",
                    "reason": "为比赛端到端测试创建隔离企业状态",
                },
            )
            self.assertEqual(initialized.status_code, 201)
            self.assertEqual(initialized.json()["data"]["action"], "initialized")

            workflow = self.client.get("/internal-risk/workflow", headers=headers)
            self.assertEqual(workflow.status_code, 200)
            self.assertEqual(workflow.json()["data"]["company_profile"]["industry"], "半导体设备上游材料")

            reset = self.client.post(
                "/internal-risk/business-state/reset",
                headers=headers,
                json={"reason": "完成测试后恢复默认业务状态"},
            )
            self.assertEqual(reset.status_code, 200)
            audit = self.client.get("/internal-risk/business-state/audit", headers=headers)
            self.assertEqual([item["action"] for item in audit.json()["items"]], ["initialized", "reset"])
        finally:
            if previous_secret is None:
                os.environ.pop("RISK_GATEWAY_IDENTITY_SECRET", None)
            else:
                os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = previous_secret

    def test_filtered_workflow_endpoints_and_task_update_are_auditable(self) -> None:
        risks = self.client.get("/internal-risk/risks", params={"risk_domain": "technology_ip"})
        gates = self.client.get("/internal-risk/gates", params={"decision": "rectification_required"})
        update = self.client.patch(
            "/internal-risk/tasks/task-cloud-assessment-001",
            json={
                "status": "in_progress",
                "changed_by": "security-compliance-lead",
                "note": "Assessment work started.",
            },
        )

        self.assertEqual([item["risk_id"] for item in risks.json()["items"]], ["risk-open-source-and-trade-secret-001"])
        self.assertEqual([item["gate_id"] for item in gates.json()["items"]], ["gate-model-training-001"])
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["data"]["status_history"][-1]["changed_by"], "demo-risk-operator")

    def test_task_evidence_endpoint_appends_an_auditable_reference(self) -> None:
        response = self.client.post(
            "/internal-risk/tasks/task-cloud-assessment-001/evidence",
            json={
                "evidence_refs": ["document-evidence-001"],
                "changed_by": "security-compliance-lead",
                "note": "Cloud assessment evidence uploaded.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("document-evidence-001", response.json()["data"]["evidence_refs"])
        self.assertEqual(response.json()["data"]["status_history"][-1]["changed_by"], "demo-risk-operator")

    def test_event_api_requires_human_confirmation_before_risk_is_created(self) -> None:
        created = self.client.post(
            "/internal-risk/events",
            json={
                "title": "新增境外模型服务",
                "description": "项目计划将客户交互数据发送至境外模型服务，用于生成产品答复。",
                "lifecycle_stage": "cross_border",
                "risk_domain": "data_model_governance",
                "occurred_at": "2026-07-28T12:00:00+08:00",
                "reported_by": "风险治理专员",
                "source_refs": ["architecture-v3"],
            },
        )
        event_id = created.json()["data"]["event_id"]
        report = {"risk_level": "high", "executive_summary": "需人工确认。", "review_reasons": [], "evidence_chain": []}
        with patch("src.internal_risk.service.generate_risk_report", return_value=report):
            assessed = self.client.post(f"/internal-risk/events/{event_id}/assessment", json={"input_filters": {}})

        risks_before = self.client.get("/internal-risk/risks").json()["items"]
        previous_secret = os.environ.get("RISK_GATEWAY_IDENTITY_SECRET")
        os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = "separation-test-secret"
        reviewer_identity = "risk-reviewer-01|demo-ai-enterprise|risk_reviewer"
        reviewer_signature = hmac.new(b"separation-test-secret", reviewer_identity.encode("utf-8"), hashlib.sha256).hexdigest()
        confirmed = self.client.patch(
            f"/internal-risk/events/{event_id}/confirmation",
            headers={"X-Risk-Identity": reviewer_identity, "X-Risk-Identity-Signature": reviewer_signature},
            json={"decision": "confirmed", "reviewer": "法务负责人", "conclusion": "纳入风险台账。"},
        )
        if previous_secret is None:
            os.environ.pop("RISK_GATEWAY_IDENTITY_SECRET", None)
        else:
            os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = previous_secret
        events = self.client.get("/internal-risk/events")
        risks_after = self.client.get("/internal-risk/risks").json()["items"]

        self.assertEqual(created.status_code, 201)
        self.assertEqual(assessed.status_code, 200)
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.json()["data"]["status"], "confirmed")
        self.assertEqual(events.json()["items"][0]["assessment_snapshot"]["report"]["risk_level"], "high")
        self.assertEqual(len(risks_after), len(risks_before) + 1)

    def test_assessment_job_api_returns_a_queryable_audit_receipt(self) -> None:
        def supported_report(*_args, **_kwargs):
            return {
                "risk_level": "medium",
                "review_reasons": [],
                "source_analysis": {},
                "citation_integrity": {"passed": True, "coverage": {"requires_review": False}},
            }

        original_service = self.router_module.service
        self.router_module.service = InternalRiskWorkflowService(
            self.fixture_path, report_generator=supported_report,
        )
        try:
            created = self.client.post(
                "/internal-risk/events",
                json={
                    "title": "材料供应商原产地核验", "description": "电子级材料进口供应商的原产地和出口管制分类需要进行证据评估。",
                    "lifecycle_stage": "cross_border", "risk_domain": "cross_border_supply_chain",
                    "occurred_at": "2026-08-20T09:00:00+08:00", "reported_by": "风险治理专员",
                },
            )
            queued = self.client.post(
                f"/internal-risk/events/{created.json()['data']['event_id']}/assessment-jobs",
                json={"input_filters": {}},
            )
            job_id = queued.json()["data"]["assessment_job_id"]
            queried = self.client.get(f"/internal-risk/assessment-jobs/{job_id}")
        finally:
            self.router_module.service = original_service

        self.assertEqual(created.status_code, 201)
        self.assertEqual(queued.status_code, 202)
        self.assertEqual(queued.json()["status"], "accepted")
        self.assertEqual(queried.status_code, 200)
        self.assertEqual(queried.json()["data"]["status"], "completed")
        self.assertEqual(
            [item["stage"] for item in queried.json()["data"]["audit_trail"]],
            ["accepted", "material_loading", "rag_assessment", "snapshot_persisted"],
        )

    def test_gate_approval_rejects_incomplete_controls(self) -> None:
        response = self.client.patch(
            "/internal-risk/gates/gate-model-training-001/decision",
            json={"decision": "approved", "reviewer": "法务负责人", "conclusion": "尝试放行。"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_RISK_INVALID_STATE")
        self.assertEqual(response.json()["error"]["blockers"][0]["code"], "GATE_CHECK_MISSING")
        blockers = self.client.get("/internal-risk/gates/gate-model-training-001/blockers")
        self.assertEqual(blockers.status_code, 200)
        self.assertEqual(blockers.json()["items"][0]["target_type"], "gate_check")

    def test_template_import_versioning_and_legacy_baseline_confirmation_are_role_scoped(self) -> None:
        previous_secret = os.environ.get("RISK_GATEWAY_IDENTITY_SECRET")
        secret = "template-api-secret"
        os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = secret

        def headers(identity: str) -> dict[str, str]:
            return {
                "X-Risk-Identity": identity,
                "X-Risk-Identity-Signature": hmac.new(secret.encode("utf-8"), identity.encode("utf-8"), hashlib.sha256).hexdigest(),
            }

        company = "template-api-company"
        maker_a = headers(f"template-maker-a|{company}|risk_decision_maker,risk_viewer")
        maker_b = headers(f"template-maker-b|{company}|risk_decision_maker,risk_viewer")
        try:
            imported = self.client.post("/internal-risk/workflow-templates/import", headers=maker_a, json={
                "template_id": "generic-rollout", "name": "Generic rollout", "source_version": 3,
                "gates": [{"key": "go-live", "title": "Go live", "lifecycle_stage": "product_launch",
                           "owner_role": "risk_reviewer", "checks": ["Evidence complete"]}],
            })
            version_two = self.client.post("/internal-risk/workflow-templates/generic-rollout/versions", headers=maker_a, json={
                "name": "Generic rollout", "change_note": "Add accountable review.",
                "gates": [{"key": "go-live", "title": "Go live", "lifecycle_stage": "product_launch",
                           "owner_role": "risk_decision_maker", "checks": ["Evidence complete", "Accountable review"]}],
            })
            initialized = self.client.post("/internal-risk/business-state/initialize", headers=maker_a, json={
                "company_name": "通用制造演练企业", "industry": "制造业", "business_model": "to_b",
                "lifecycle_stages": ["product_launch"], "workflow_template_id": "generic-rollout", "workflow_template_version": 1,
            })
            template_list = self.client.get("/internal-risk/workflow-templates", headers=maker_a)
            template_audit = self.client.get("/internal-risk/workflow-templates/generic-rollout/audit", headers=maker_a)
            workflow = self.client.get("/internal-risk/workflow", headers=maker_a)
            proposal = self.client.post("/internal-risk/business-state/baseline/proposal", headers=maker_a, json={"reason": "已有企业已初始化，不应允许登记"})

            self.assertEqual(imported.status_code, 201)
            self.assertTrue(imported.json()["data"]["imported"])
            self.assertEqual(version_two.json()["data"]["version"], 2)
            self.assertEqual(initialized.status_code, 201)
            self.assertEqual(workflow.json()["data"]["workflow_template"]["version"], 1)
            self.assertEqual(template_list.json()["items"][0]["version"], 2)
            self.assertEqual([item["action"] for item in template_audit.json()["items"]], ["imported", "version_created"])
            self.assertEqual(proposal.status_code, 409)

            legacy_a = headers("legacy-maker-a|demo-ai-enterprise|risk_decision_maker")
            legacy_b = headers("legacy-maker-b|demo-ai-enterprise|risk_decision_maker")
            proposed = self.client.post("/internal-risk/business-state/baseline/proposal", headers=legacy_a, json={"reason": "登记遗留租户基线"})
            same_actor = self.client.post("/internal-risk/business-state/baseline/confirmation", headers=legacy_a, json={"reason": "不允许自确认"})
            confirmed = self.client.post("/internal-risk/business-state/baseline/confirmation", headers=legacy_b, json={"reason": "完成第二人复核"})

            self.assertEqual(proposed.status_code, 201)
            self.assertEqual(same_actor.status_code, 409)
            self.assertEqual(confirmed.status_code, 200)
            self.assertEqual(confirmed.json()["data"]["proposed_state_sha256"], confirmed.json()["data"]["resulting_state_sha256"])
        finally:
            if previous_secret is None:
                os.environ.pop("RISK_GATEWAY_IDENTITY_SECRET", None)
            else:
                os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = previous_secret

    def test_invalid_transition_and_unknown_task_return_stable_errors(self) -> None:
        invalid = self.client.patch(
            "/internal-risk/tasks/task-cloud-assessment-001",
            json={"status": "verified", "changed_by": "security-compliance-lead"},
        )
        unknown = self.client.patch(
            "/internal-risk/tasks/missing-task",
            json={"status": "in_progress", "changed_by": "security-compliance-lead"},
        )

        self.assertEqual(invalid.status_code, 409)
        self.assertEqual(invalid.json()["error"]["code"], "INTERNAL_RISK_INVALID_STATE")
        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(unknown.json()["error"]["code"], "INTERNAL_RISK_NOT_FOUND")

    def test_enterprise_scope_and_gateway_roles_are_enforced(self) -> None:
        cross_enterprise = self.client.get("/internal-risk/workflow", params={"company_id": "another-company"})
        original_secret = os.environ.get("RISK_GATEWAY_IDENTITY_SECRET")
        os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = "test-gateway-secret"
        identity = "viewer-01|demo-ai-enterprise|risk_viewer"
        signature = hmac.new(b"test-gateway-secret", identity.encode("utf-8"), hashlib.sha256).hexdigest()
        role_denied = self.client.patch(
            "/internal-risk/tasks/task-cloud-assessment-001",
            headers={"X-Risk-Identity": identity, "X-Risk-Identity-Signature": signature},
            json={"status": "in_progress", "changed_by": "forged-name"},
        )
        forged_identity = self.client.get(
            "/internal-risk/workflow",
            headers={"X-Risk-Identity": "viewer-01|demo-ai-enterprise|risk_viewer"},
        )
        os.environ["RISK_DEMO_IDENTITY_ENABLED"] = "false"
        unsigned_request = self.client.get("/internal-risk/workflow")
        os.environ["RISK_DEMO_IDENTITY_ENABLED"] = "true"
        if original_secret is None:
            os.environ.pop("RISK_GATEWAY_IDENTITY_SECRET", None)
        else:
            os.environ["RISK_GATEWAY_IDENTITY_SECRET"] = original_secret

        self.assertEqual(cross_enterprise.status_code, 403)
        self.assertEqual(role_denied.status_code, 403)
        self.assertEqual(forged_identity.status_code, 401)
        self.assertEqual(unsigned_request.status_code, 401)

    def test_manual_review_requires_pending_review_task_and_leaves_an_audit_trail(self) -> None:
        response = self.client.patch(
            "/internal-risk/reviews/review-task-sbom-001",
            json={
                "status": "changes_requested",
                "reviewer": "product-compliance-lead",
                "conclusion": "Please attach the dependency provenance evidence.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "changes_requested")
        task = self.client.get("/internal-risk/tasks", params={"risk_id": "risk-open-source-and-trade-secret-001"})
        self.assertEqual(task.json()["items"][0]["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
