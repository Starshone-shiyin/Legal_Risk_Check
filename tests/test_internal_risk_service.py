from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.internal_risk.repository import InternalRiskDataError
from src.internal_risk.schemas import (
    BusinessStateInitializeRequest,
    BusinessStateResetRequest,
    GateDecisionUpdate,
    LegacyBaselineConfirmationRequest,
    LegacyBaselineProposalRequest,
    ManualReviewDecisionUpdate,
    RiskEventAssessmentRequest,
    RiskEventConfirmationUpdate,
    RiskEventCreate,
    RiskClosureUpdate,
    SuggestionAdoptionRequest,
    TaskEvidenceUpdate,
    TaskStatusUpdate,
    WorkflowTemplateCreateRequest,
    WorkflowTemplateImportRequest,
    WorkflowTemplateVersionCreateRequest,
)
from src.internal_risk.service import (
    InternalRiskWorkflowService,
    RiskWorkflowNotFoundError,
    RiskWorkflowStateError,
)


class InternalRiskWorkflowServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_path = Path(self.temporary_directory.name) / "internal_risk_workflow.json"
        source_path = Path("tests/fixtures/regression/internal_risk_workflow.json")
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        cloud_task = next(task for task in payload["workflow"]["remediation_tasks"] if task["task_id"] == "task-cloud-assessment-001")
        cloud_task["status"] = "not_started"
        cloud_task["evidence_refs"] = []
        self.fixture_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.service = InternalRiskWorkflowService(self.fixture_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_workflow_exposes_risks_gates_tasks_and_manual_reviews(self) -> None:
        workflow = self.service.workflow()

        self.assertEqual(workflow.company_id, "demo-ai-enterprise")
        self.assertEqual(len(workflow.risk_items), 3)
        self.assertEqual(len(workflow.gates), 3)
        self.assertEqual(len(workflow.remediation_tasks), 4)
        self.assertGreaterEqual(len(workflow.manual_reviews), 3)

    def test_filters_follow_the_internal_risk_workflow_relationships(self) -> None:
        risks = self.service.risk_items(risk_domain="data_model_governance", risk_level="high")
        gates = self.service.gates(lifecycle_stage="model_training")
        tasks = self.service.remediation_tasks(risk_id=risks[0].risk_id, status="not_started")
        reviews = self.service.manual_reviews(target_id=gates[0].gate_id, status="changes_requested")

        self.assertEqual([risk.risk_id for risk in risks], ["risk-training-data-cross-border-001"])
        self.assertEqual([gate.gate_id for gate in gates], ["gate-model-training-001"])
        self.assertEqual([task.task_id for task in tasks], ["task-cloud-assessment-001"])
        self.assertEqual([review.review_id for review in reviews], ["review-training-gate-001"])

    def test_task_status_update_is_persisted_with_an_audit_event(self) -> None:
        self.service.update_task_status(
            "task-cloud-assessment-001",
            TaskStatusUpdate(
                status="in_progress",
                changed_by="security-compliance-lead",
                note="Assessment work started.",
            ),
        )
        updated = self.service.update_task_status(
            "task-cloud-assessment-001",
            TaskStatusUpdate(
                status="pending_review",
                changed_by="security-compliance-lead",
                note="Assessment submitted for legal review.",
                evidence_refs=["cloud-assessment-v1"],
            ),
        )
        reloaded = InternalRiskWorkflowService(self.fixture_path).remediation_task("task-cloud-assessment-001")

        self.assertEqual(updated.status, "pending_review")
        self.assertEqual(reloaded.evidence_refs, ["cloud-assessment-v1"])
        self.assertEqual(reloaded.status_history[-1].changed_by, "security-compliance-lead")
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "0.1.0")

    def test_not_found_and_version_drift_fail_explicitly(self) -> None:
        with self.assertRaises(RiskWorkflowNotFoundError):
            self.service.remediation_task("missing-task")

        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        payload["version"] = "0.0.0"
        self.fixture_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(InternalRiskDataError):
            self.service.workflow()

    def test_semiconductor_company_initialization_is_isolated_and_reset_is_auditable(self) -> None:
        company_id = "demo-semiconductor-materials"
        initialized = self.service.initialize_business_state(
            company_id,
            BusinessStateInitializeRequest(
                company_name="华芯高纯材料（模拟）有限公司",
                industry="半导体设备上游材料",
                lifecycle_stages=[
                    "establishment", "research_and_development",
                    "market_expansion", "strategic_adjustment",
                ],
                reason="创建端到端比赛演练租户",
            ),
            actor_id="semiconductor-risk-owner",
        )

        semiconductor = self.service.workflow(company_id)
        self.assertEqual(initialized.action, "initialized")
        self.assertEqual(semiconductor.company_profile.company_name, "华芯高纯材料（模拟）有限公司")
        self.assertEqual(semiconductor.company_profile.lifecycle_stages[1], "research_and_development")
        self.assertEqual(self.service.workflow("demo-ai-enterprise").company_id, "demo-ai-enterprise")

        event = self.service.create_risk_event(
            RiskEventCreate(
                project_id="project-high-purity-copper",
                title="高纯铜原料价格异常波动",
                description="关键原料期货价格持续上升，拟评估对设备零部件材料成本和交付承诺的影响。",
                lifecycle_stage="market_expansion",
                risk_domain="cross_border_supply_chain",
                occurred_at="2026-08-20T10:00:00+08:00",
                reported_by="semiconductor-risk-owner",
            ),
            company_id,
        )
        self.assertEqual(event.company_id, company_id)
        self.assertEqual(len(self.service.workflow(company_id).risk_events), 1)

        reset = self.service.reset_business_state(
            company_id,
            BusinessStateResetRequest(reason="完成演练后恢复企业业务默认状态"),
            actor_id="semiconductor-risk-owner",
        )
        self.assertEqual(reset.action, "reset")
        self.assertNotEqual(reset.previous_state_sha256, reset.resulting_state_sha256)
        self.assertEqual(self.service.workflow(company_id).risk_events, [])
        self.assertEqual([item.action for item in self.service.business_state_audit(company_id)], ["initialized", "reset"])

    def test_user_owned_workflow_template_is_versioned_and_can_initialize_any_industry(self) -> None:
        company_id = "template-test-enterprise"
        template = self.service.create_workflow_template(
            WorkflowTemplateCreateRequest(
                template_id="commercial-rollout", name="商业项目准入",
                description="由企业自行维护的项目准入工作流。",
                gates=[{
                    "key": "supplier-review", "title": "供应商准入", "lifecycle_stage": "project_initiation",
                    "owner_role": "risk_reviewer", "checks": ["合同主体核验", "关键资质核验"],
                }],
            ), company_id, "risk-owner-a",
        )
        version_two = self.service.create_workflow_template_version(
            "commercial-rollout",
            WorkflowTemplateVersionCreateRequest(
                name="商业项目准入", description="增加合同审批的第二版。", change_note="新增合同审批条件。",
                gates=[{
                    "key": "supplier-review", "title": "供应商准入", "lifecycle_stage": "project_initiation",
                    "owner_role": "risk_reviewer", "checks": ["合同主体核验", "关键资质核验", "合同审批"],
                }],
            ), company_id, "risk-owner-b",
        )
        initialized = self.service.initialize_business_state(
            company_id,
            BusinessStateInitializeRequest(
                company_name="通用设备服务（演练）有限公司", industry="工业服务",
                lifecycle_stages=["project_initiation"], workflow_template_id=template.template_id,
                workflow_template_version=template.version,
            ), actor_id="risk-owner-a",
        )
        workflow = self.service.workflow(company_id)

        self.assertEqual(initialized.action, "initialized")
        self.assertEqual(version_two.version, 2)
        self.assertNotEqual(template.content_sha256, version_two.content_sha256)
        self.assertEqual(self.service.workflow_template("commercial-rollout", company_id, 1).gates[0].checks[-1], "关键资质核验")
        self.assertEqual(workflow.workflow_template.version, 1)
        self.assertEqual(workflow.gates[0].checks[0].title, "合同主体核验")
        self.assertEqual(workflow.gates[0].owner, "risk_reviewer")
        audit = self.service.workflow_template_audit("commercial-rollout", company_id)
        self.assertEqual([(item.action, item.version) for item in audit], [("created", 1), ("version_created", 2)])

    def test_json_template_import_is_tenant_scoped_and_validated(self) -> None:
        imported = self.service.import_workflow_template(
            WorkflowTemplateImportRequest(
                template_id="imported-safety", name="Imported safety workflow",
                source_version=7, gates=[{
                    "key": "launch", "title": "Launch readiness", "lifecycle_stage": "product_launch",
                    "owner_role": "risk_decision_maker", "checks": ["Safety sign-off"],
                }],
            ), "importing-company", "import-owner",
        )
        self.assertTrue(imported.imported)
        self.assertEqual(imported.version, 1)
        self.assertEqual(self.service.workflow_templates("importing-company")[0].template_id, "imported-safety")
        with self.assertRaises(RiskWorkflowNotFoundError):
            self.service.workflow_template("imported-safety", "another-company")

    def test_legacy_tenant_baseline_requires_second_person_and_stable_hash(self) -> None:
        proposal = self.service.propose_legacy_baseline(
            "demo-ai-enterprise", LegacyBaselineProposalRequest(reason="登记既有演练租户基线"), "decision-maker-a",
        )
        with self.assertRaisesRegex(RiskWorkflowStateError, "different authorized"):
            self.service.confirm_legacy_baseline(
                "demo-ai-enterprise", LegacyBaselineConfirmationRequest(reason="本人不能确认"), "decision-maker-a",
            )
        confirmed = self.service.confirm_legacy_baseline(
            "demo-ai-enterprise", LegacyBaselineConfirmationRequest(reason="复核快照与当前状态一致"), "decision-maker-b",
        )
        reset = self.service.reset_business_state(
            "demo-ai-enterprise", BusinessStateResetRequest(reason="验证可恢复既有基线"), "decision-maker-b",
        )

        self.assertEqual(proposal.status, "pending_confirmation")
        self.assertEqual(confirmed.status, "registered")
        self.assertEqual(confirmed.proposed_state_sha256, confirmed.resulting_state_sha256)
        self.assertEqual(reset.resulting_state_sha256, confirmed.resulting_state_sha256)

    def test_gate_and_closure_blockers_are_structured(self) -> None:
        blockers = self.service.gate_blockers("gate-model-training-001")
        closure_blockers = self.service.risk_closure_blockers("risk-training-data-cross-border-001")

        self.assertEqual(blockers[0].code, "GATE_CHECK_MISSING")
        self.assertEqual(blockers[0].target_type, "gate_check")
        self.assertTrue(all(blocker.remediation for blocker in closure_blockers))

    def test_task_status_must_follow_the_review_workflow(self) -> None:
        with self.assertRaises(RiskWorkflowStateError):
            self.service.update_task_status(
                "task-cloud-assessment-001",
                TaskStatusUpdate(status="verified", changed_by="security-compliance-lead"),
            )

    def test_evidence_attachment_is_deduplicated_and_audited(self) -> None:
        updated = self.service.add_task_evidence(
            "task-cloud-assessment-001",
            TaskEvidenceUpdate(
                evidence_refs=["document-evidence-001", "document-evidence-001"],
                changed_by="security-compliance-lead",
                note="Cloud assessment evidence uploaded.",
            ),
        )
        reloaded = InternalRiskWorkflowService(self.fixture_path).remediation_task("task-cloud-assessment-001")

        self.assertIn("document-evidence-001", updated.evidence_refs)
        self.assertEqual(reloaded.evidence_refs.count("document-evidence-001"), 1)
        self.assertEqual(reloaded.status_history[-1].changed_by, "security-compliance-lead")
        self.assertEqual(reloaded.status_history[-1].note, "Cloud assessment evidence uploaded.")

    def test_task_cannot_be_submitted_for_review_without_evidence(self) -> None:
        self.service.update_task_status(
            "task-cloud-assessment-001",
            TaskStatusUpdate(status="in_progress", changed_by="security-compliance-lead"),
        )

        with self.assertRaisesRegex(RiskWorkflowStateError, "needs at least one evidence"):
            self.service.update_task_status(
                "task-cloud-assessment-001",
                TaskStatusUpdate(status="pending_review", changed_by="security-compliance-lead"),
            )

    def test_event_assessment_snapshot_requires_human_confirmation_before_creating_a_risk(self) -> None:
        original_risk_count = len(self.service.workflow().risk_items)
        event = self.service.create_risk_event(
            RiskEventCreate(
                title="新增境外模型服务",
                description="项目计划将客户交互数据发送至境外模型服务，用于生成产品答复。",
                lifecycle_stage="cross_border",
                risk_domain="data_model_governance",
                occurred_at="2026-07-28T12:00:00+08:00",
                reported_by="风险治理专员",
                source_refs=["architecture-v3", "architecture-v3"],
            )
        )
        report = {
            "risk_level": "high",
            "executive_summary": "需核验数据出境路径与境外接收方安排。",
            "review_reasons": ["需要人工确认事实与适用路径。"],
            "evidence_chain": [{"law_name": "个人信息保护法", "article": "第三十八条"}],
            "source_analysis": {"missing_evidence": ["境外接收方评估记录"]},
        }
        with patch("src.internal_risk.service.generate_risk_report", return_value=report) as generate_report:
            assessed = self.service.assess_risk_event(event.event_id, RiskEventAssessmentRequest())

        self.assertEqual(assessed.status, "assessed")
        self.assertEqual(len(self.service.workflow().risk_items), original_risk_count)
        self.assertEqual(assessed.assessment_snapshot.report["risk_level"], "high")
        generate_report.assert_called_once()

        confirmed = self.service.confirm_risk_event(
            event.event_id,
            RiskEventConfirmationUpdate(
                decision="confirmed",
                reviewer="法务负责人",
                conclusion="纳入跨境数据风险台账并安排专项核验。",
            ),
        )
        workflow = self.service.workflow()
        created_risk = next(item for item in workflow.risk_items if item.risk_id == confirmed.confirmed_risk_id)

        self.assertEqual(confirmed.status, "confirmed")
        self.assertEqual(created_risk.risk_level, "high")
        self.assertEqual(created_risk.evidence_refs, ["architecture-v3"])
        self.assertEqual(created_risk.task_ids, [])

        with self.assertRaisesRegex(RiskWorkflowStateError, "draft risk event"):
            self.service.assess_risk_event(event.event_id, RiskEventAssessmentRequest())
        with self.assertRaisesRegex(RiskWorkflowStateError, "must be assessed"):
            self.service.confirm_risk_event(
                event.event_id,
                RiskEventConfirmationUpdate(decision="rejected", reviewer="法务负责人", conclusion="重复决定"),
            )

    def test_gate_approval_and_risk_closure_are_human_commands_with_blockers(self) -> None:
        with self.assertRaisesRegex(RiskWorkflowStateError, "核验项未完成"):
            self.service.record_gate_decision(
                "gate-model-training-001",
                GateDecisionUpdate(decision="approved", reviewer="法务负责人", conclusion="尝试放行"),
            )

        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        workflow = payload["workflow"]
        gate = next(item for item in workflow["gates"] if item["gate_id"] == "gate-model-training-001")
        for check in gate["checks"]:
            check["status"] = "passed"
        linked_tasks = [task for task in workflow["remediation_tasks"] if task["risk_id"] == "risk-training-data-cross-border-001"]
        for task in linked_tasks:
            task["status"] = "verified"
        linked_review_ids = {task["review_id"] for task in linked_tasks}
        for review in workflow["manual_reviews"]:
            if review["review_id"] in linked_review_ids:
                review["status"] = "approved"
        self.fixture_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        approved = self.service.record_gate_decision(
            "gate-model-training-001",
            GateDecisionUpdate(decision="approved", reviewer="法务负责人", conclusion="核验项与整改均已完成。"),
        )
        closed = self.service.close_risk(
            "risk-training-data-cross-border-001",
            RiskClosureUpdate(reviewer="法务负责人", conclusion="闸门正式通过，关闭本事项。"),
        )

        self.assertEqual(approved.decision, "approved")
        self.assertEqual(approved.decision_history[-1].reviewer, "法务负责人")
        self.assertEqual(closed.status, "closed")
        self.assertEqual(closed.status_history[-1].note, "闸门正式通过，关闭本事项。")

    def test_human_review_decision_is_audited_and_controls_task_closure(self) -> None:
        review = self.service.record_manual_review_decision(
            "review-task-sbom-001",
            ManualReviewDecisionUpdate(
                status="approved",
                reviewer="Product compliance lead",
                conclusion="SBOM and license review evidence are complete.",
            ),
        )
        task = self.service.remediation_task("task-sbom-review-001")

        self.assertEqual(review.status, "approved")
        self.assertEqual(review.decision_history[-1].reviewer, "Product compliance lead")
        self.assertEqual(task.status, "verified")
        self.assertEqual(task.status_history[-1].changed_by, "Product compliance lead")

    def test_management_assistance_only_creates_idempotent_suggestions_and_reminders(self) -> None:
        task_status_before = self.service.remediation_task("task-cloud-assessment-001").status
        risk_count_before = len(self.service.workflow().risk_items)

        suggestions, reminders = self.service.refresh_management_assistance("demo-ai-enterprise")
        repeated_suggestions, repeated_reminders = self.service.refresh_management_assistance("demo-ai-enterprise")

        self.assertGreaterEqual(len(suggestions), 1)
        self.assertGreaterEqual(len(reminders), 1)
        self.assertEqual(len(suggestions), len(repeated_suggestions))
        self.assertEqual(len(reminders), len(repeated_reminders))
        self.assertEqual(self.service.remediation_task("task-cloud-assessment-001").status, task_status_before)
        self.assertEqual(len(self.service.workflow().risk_items), risk_count_before)

    def test_adopting_a_suggestion_is_the_only_path_that_creates_a_task(self) -> None:
        suggestions, _ = self.service.refresh_management_assistance()
        task_count_before = len(self.service.workflow().remediation_tasks)

        adopted = self.service.adopt_remediation_suggestion(
            suggestions[0].suggestion_id,
            SuggestionAdoptionRequest(owner="data-owner", adopted_by="risk-owner"),
        )

        self.assertEqual(adopted.status, "adopted")
        self.assertEqual(len(self.service.workflow().remediation_tasks), task_count_before + 1)
        with self.assertRaises(RiskWorkflowStateError):
            self.service.adopt_remediation_suggestion(
                adopted.suggestion_id,
                SuggestionAdoptionRequest(owner="data-owner", adopted_by="risk-owner"),
            )

    def test_high_risk_task_owner_cannot_complete_its_own_review(self) -> None:
        self.service.update_task_status(
            "task-cloud-assessment-001",
            TaskStatusUpdate(status="in_progress", changed_by="security-compliance-lead"),
        )
        self.service.update_task_status(
            "task-cloud-assessment-001",
            TaskStatusUpdate(
                status="pending_review", changed_by="security-compliance-lead", evidence_refs=["assessment-v1"],
            ),
        )
        review_id = self.service.remediation_task("task-cloud-assessment-001").review_id
        with self.assertRaisesRegex(RiskWorkflowStateError, "reviewer other than the task owner"):
            self.service.record_manual_review_decision(
                review_id,
                ManualReviewDecisionUpdate(status="approved", reviewer="Security compliance lead", conclusion="self review"),
            )

    def test_high_risk_event_reporter_cannot_confirm_their_own_event(self) -> None:
        event = self.service.create_risk_event(RiskEventCreate(
            title="High-risk data arrangement", description="Customer data will be processed through an overseas service.",
            lifecycle_stage="cross_border", risk_domain="data_model_governance",
            occurred_at="2026-07-31T09:00:00+08:00", reported_by="risk-operator",
        ))
        with patch("src.internal_risk.service.generate_risk_report", return_value={"risk_level": "high", "review_reasons": [], "source_analysis": {}}):
            self.service.assess_risk_event(event.event_id, RiskEventAssessmentRequest())
        with self.assertRaisesRegex(RiskWorkflowStateError, "confirmer other than the reporter"):
            self.service.confirm_risk_event(
                event.event_id,
                RiskEventConfirmationUpdate(decision="confirmed", reviewer="risk-operator", conclusion="self confirmation"),
            )


if __name__ == "__main__":
    unittest.main()
