from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.external_risk.schemas import ExternalRiskSignal
from src.internal_risk.service import InternalRiskWorkflowService
from src.risk_intake.schemas import ExternalIntakeTriageUpdate, LifecycleStateTransitionRequest
from src.risk_intake.service import RiskIntakeService, RiskIntakeStateError


class RiskIntakeServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.intake_path = root / "risk_intake.json"
        self.workflow_path = root / "internal_risk_workflow.json"
        self.intake_path.write_text(Path("tests/fixtures/regression/risk_intake.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.workflow_path.write_text(Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"), encoding="utf-8")
        self.internal_service = InternalRiskWorkflowService(self.workflow_path)
        self.service = RiskIntakeService(self.intake_path, internal_service=self.internal_service)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def _matched_signal() -> ExternalRiskSignal:
        return ExternalRiskSignal(
            signal_id="signal-cloud-001",
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

    def test_exact_object_match_creates_one_idempotent_pending_case(self) -> None:
        created = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])
        updated = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])

        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].status, "pending_triage")
        self.assertEqual(created[0].matched_objects[0].object_id, "supplier-overseas-cloud")
        self.assertEqual(created[0].matched_objects[0].match_type, "supplier_id")
        self.assertEqual(created[0].target_lifecycle_stage, "model_training")
        self.assertEqual(created[0].intake_id, updated[0].intake_id)
        self.assertEqual(len(self.service.cases("demo-ai-enterprise")), 1)

    def test_unmatched_signal_does_not_enter_internal_intake(self) -> None:
        signal = self._matched_signal().model_copy(update={
            "signal_id": "signal-unmatched-001",
            "affected_supply_links": [],
            "entity": "未登记供应商",
        })
        result = self.service.sync_external_cases("demo-ai-enterprise", [signal])

        self.assertEqual(result, [])
        self.assertEqual(self.service.cases("demo-ai-enterprise"), [])

    def test_region_or_tag_only_signal_is_an_observation_not_a_case(self) -> None:
        signal = self._matched_signal().model_copy(update={
            "signal_id": "signal-region-only-001",
            "affected_supply_links": [],
            "entity": "unregistered external organisation",
            "metadata": {"region": "Singapore", "industry_tags": ["data_compliance"]},
        })

        result = self.service.sync_external_cases("demo-ai-enterprise", [signal])
        batch = self.service.sync_batches("demo-ai-enterprise")[0]

        self.assertEqual(result, [])
        self.assertEqual(self.service.cases("demo-ai-enterprise"), [])
        self.assertEqual(batch.observation_count, 1)
        self.assertEqual(batch.exact_match_count, 0)

    def test_stale_or_failed_source_never_creates_a_case(self) -> None:
        from src.risk_intake.schemas import ExternalSyncSourceHealth

        stale = ExternalSyncSourceHealth(source_name="policy-feed", status="stale", fresh=False)
        stale_batches = self.service.sync_polled_signals([self._matched_signal()], stale)
        failed_batches = self.service.record_poll_failure("policy feed unavailable")

        self.assertEqual(self.service.cases("demo-ai-enterprise"), [])
        self.assertEqual(stale_batches[0].skipped_unusable_source_count, 1)
        self.assertEqual(failed_batches[0].source_health.status, "failed")
        self.assertEqual(failed_batches[0].new_case_count, 0)

    def test_a_failed_feed_is_excluded_when_other_sources_remain_healthy(self) -> None:
        from src.risk_intake.schemas import ExternalSyncSourceHealth

        blocked = ExternalSyncSourceHealth(
            source_name="policy-feeds", status="healthy", fresh=True,
            blocked_source_ids=["policy-feed-a"],
        )
        signal = self._matched_signal().model_copy(update={"metadata": {"feed_id": "policy-feed-a"}})

        batches = self.service.sync_polled_signals([signal], blocked)

        self.assertEqual(self.service.cases("demo-ai-enterprise"), [])
        self.assertEqual(batches[0].skipped_unusable_source_count, 1)

    def test_rejected_case_is_not_reopened_but_material_change_creates_linked_case(self) -> None:
        first = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])[0]
        self.service.triage_case(
            first.intake_id,
            ExternalIntakeTriageUpdate(decision="reject", reviewer="reviewer", conclusion="not applicable"),
        )

        unchanged = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])
        changed_signal = self._matched_signal().model_copy(update={
            "title": "updated regulatory requirement",
            "evidence": "The regulator published a materially changed requirement.",
        })
        changed = self.service.sync_external_cases("demo-ai-enterprise", [changed_signal])

        self.assertEqual(unchanged, [])
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0].status, "pending_triage")
        self.assertEqual(changed[0].supersedes_intake_id, first.intake_id)
        self.assertEqual(len(self.service.cases("demo-ai-enterprise")), 2)

    def test_pending_case_with_changed_evidence_is_updated_in_place(self) -> None:
        first = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])[0]
        changed = self.service.sync_external_cases(
            "demo-ai-enterprise",
            [self._matched_signal().model_copy(update={"evidence": "Updated source evidence."})],
        )[0]

        self.assertEqual(changed.intake_id, first.intake_id)
        self.assertEqual(len(changed.signal_history), 1)
        self.assertEqual(len(self.service.cases("demo-ai-enterprise")), 1)

    def test_cross_border_topic_uses_the_matched_activity_control_stage(self) -> None:
        signal = self._matched_signal().model_copy(update={
            "signal_id": "signal-cross-border-001",
            "affected_domains": ["export_control"],
        })

        case = self.service.sync_external_cases("demo-ai-enterprise", [signal])[0]
        promoted = self.service.triage_case(
            case.intake_id,
            ExternalIntakeTriageUpdate(
                decision="promote",
                reviewer="风险治理负责人",
                conclusion="供应商命中后按研发活动的当前控制阶段转入核验。",
            ),
        )
        event = self.internal_service.risk_event(promoted.internal_event_id)

        self.assertEqual(case.risk_domain, "cross_border_supply_chain")
        self.assertEqual(case.target_lifecycle_stage, "model_training")
        self.assertEqual(event.lifecycle_stage, "model_training")

    def test_selected_project_must_belong_to_a_matched_object(self) -> None:
        case = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])[0]

        with self.assertRaises(RiskIntakeStateError):
            self.service.triage_case(
                case.intake_id,
                ExternalIntakeTriageUpdate(
                    decision="promote",
                    reviewer="风险治理负责人",
                    conclusion="不能绕过命中对象指定其他项目。",
                    project_id="project-not-matched",
                ),
            )

    def test_multi_project_case_requires_an_explicit_matched_project(self) -> None:
        payload = json.loads(self.intake_path.read_text(encoding="utf-8"))
        scope = payload["scopes"]["demo-ai-enterprise"]
        scope["objects"][1]["aliases"].append("shared cloud provider")
        scope["objects"].append({
            "object_id": "supplier-secondary-cloud",
            "object_type": "supplier",
            "name": "Secondary cloud provider",
            "aliases": ["shared cloud provider"],
            "supplier_id": "supplier-secondary-cloud",
            "project_id": "project-secondary",
            "lifecycle_state_ids": ["state-secondary-research"],
            "active": True,
        })
        scope["lifecycle_states"].append({
            "state_id": "state-secondary-research",
            "scope_id": "project-secondary",
            "scope_type": "project",
            "business_stage": "research",
            "control_stage": "data_access",
            "status": "active",
        })
        self.intake_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        signal = self._matched_signal().model_copy(update={
            "signal_id": "signal-multi-project-001",
            "affected_supply_links": [],
            "entity": "shared cloud provider",
        })
        case = self.service.sync_external_cases("demo-ai-enterprise", [signal])[0]

        with self.assertRaises(RiskIntakeStateError):
            self.service.triage_case(
                case.intake_id,
                ExternalIntakeTriageUpdate(
                    decision="promote",
                    reviewer="风险治理负责人",
                    conclusion="需要选择实际受影响项目。",
                ),
            )

        promoted = self.service.triage_case(
            case.intake_id,
            ExternalIntakeTriageUpdate(
                decision="promote",
                reviewer="风险治理负责人",
                conclusion="选择第二个项目进入事实核验。",
                project_id="project-secondary",
            ),
        )
        event = self.internal_service.risk_event(promoted.internal_event_id)
        self.assertEqual(event.project_id, "project-secondary")
        self.assertEqual(event.lifecycle_stage, "data_access")

    def test_promote_creates_only_a_draft_internal_event_with_traceability(self) -> None:
        case = self.service.sync_external_cases("demo-ai-enterprise", [self._matched_signal()])[0]
        before_risks = len(self.internal_service.workflow().risk_items)

        promoted = self.service.triage_case(
            case.intake_id,
            ExternalIntakeTriageUpdate(
                decision="promote",
                reviewer="风险治理负责人",
                conclusion="与已登记境外云服务商精确匹配，转入事实核验。",
            ),
        )
        event = self.internal_service.risk_event(promoted.internal_event_id)

        self.assertEqual(promoted.status, "promoted")
        self.assertEqual(event.status, "draft")
        self.assertEqual(event.origin, "external_signal")
        self.assertEqual(event.external_intake_id, case.intake_id)
        self.assertEqual(event.matched_object_ids, ["supplier-overseas-cloud"])
        self.assertEqual(event.signal_snapshot["signal_id"], "signal-cloud-001")
        self.assertEqual(len(self.internal_service.workflow().risk_items), before_risks)
        with self.assertRaises(RiskIntakeStateError):
            self.service.triage_case(
                case.intake_id,
                ExternalIntakeTriageUpdate(decision="promote", reviewer="风险治理负责人", conclusion="重复转入"),
            )

    def test_lifecycle_transition_retains_basis_owner_and_gate_decision(self) -> None:
        state, transition = self.service.transition_lifecycle_state(
            "demo-ai-enterprise",
            "state-project-research",
            LifecycleStateTransitionRequest(
                business_stage="product",
                control_stage="product_launch",
                status="active",
                changed_by="产品合规负责人",
                basis="完成验证并经产品准入闸门有条件批准。",
                gate_id="gate-product-launch-001",
            ),
        )
        scope = self.service.scope("demo-ai-enterprise")

        self.assertEqual(state.business_stage, "product")
        self.assertEqual(state.owner, "产品合规负责人")
        self.assertEqual(transition.previous_business_stage, "research")
        self.assertEqual(transition.gate_decision, "conditional_approval")
        self.assertEqual(scope.lifecycle_state_history[-1].transition_id, transition.transition_id)

    def test_lifecycle_transition_rejects_unrelated_gate_and_noop(self) -> None:
        with self.assertRaises(RiskIntakeStateError):
            self.service.transition_lifecycle_state(
                "demo-ai-enterprise",
                "state-project-research",
                LifecycleStateTransitionRequest(
                    business_stage="research",
                    control_stage="model_training",
                    status="active",
                    changed_by="风险治理负责人",
                    basis="未发生状态变更。",
                ),
            )
        with self.assertRaises(RiskIntakeStateError):
            self.service.transition_lifecycle_state(
                "demo-ai-enterprise",
                "state-project-research",
                LifecycleStateTransitionRequest(
                    business_stage="product",
                    control_stage="product_launch",
                    status="active",
                    changed_by="风险治理负责人",
                    basis="测试错误的闸门归属。",
                    gate_id="gate-commercialization-001",
                ),
            )


if __name__ == "__main__":
    unittest.main()
