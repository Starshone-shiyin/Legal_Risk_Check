from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.document_ingest.mineu_adapter import MineUParseResult
from src.document_ingest.service import DocumentIngestService
from src.document_ingest.storage import DocumentTaskStorage
from src.external_risk.schemas import (
    ExternalRiskSignal,
    ExternalRiskWorkflowGraph,
    ExternalRiskWorkflowLink,
    ExternalRiskWorkflowNode,
)
from src.external_risk.service import _chain_alerts
from src.internal_risk.schemas import (
    GateCheckUpdate,
    LegacyBaselineCancelRequest,
    LegacyBaselineProposalRequest,
    RiskEventAssessmentRequest,
    RiskEventCreate,
)
from src.internal_risk.service import InternalRiskWorkflowService
from src.main import app
from src.risk.analyzer import build_risk_analysis


class _FourthRoundParser:
    mode = "local"

    def parse(self, _source_path: Path, _output_dir: Path) -> MineUParseResult:
        return MineUParseResult(
            markdown="# 电子级石英砂采购与原产地核验记录\n\n"
            "供应商原产地证明、出口管制分类和替代采购安排均已归档。",
            command="fourth-round-local-parser",
        )


def _supported_report(_: str, **__: object) -> dict:
    return {
        "risk_level": "medium",
        "review_reasons": [],
        "source_analysis": {},
        "citation_integrity": {"passed": True, "coverage": {"requires_review": False}},
    }


class FourthRoundEndToEndTest(unittest.TestCase):
    def test_external_confirmed_path_and_stale_canvas_diff_are_auditable(self) -> None:
        signal = ExternalRiskSignal(
            signal_id="copper-upstream-cost", signal_type="commodity_futures", title="铜价大幅上涨",
            severity="high", direction="negative", as_of="2026-08-20T10:00:00Z",
            entity="hf_CAD", metric="intraday_return", value=0.04, threshold=0.02,
            affected_domains=["supply_chain"], evidence="铜价上涨影响高纯材料加工成本。",
            source="fourth-round-fixture", confidence=0.95,
        )
        graph = ExternalRiskWorkflowGraph(
            nodes=[
                ExternalRiskWorkflowNode(id="copper", symbol="hf_CAD"),
                ExternalRiskWorkflowNode(id="quartz", symbol="SIM-QUARTZ", node_kind="supplier"),
            ],
            links=[ExternalRiskWorkflowLink(
                source="copper", target="quartz", relation="cost_pass_through",
                confirmed_by="supply-chain-owner", confirmed_at="2026-08-20T09:50:00Z",
            )],
        )
        alerts = _chain_alerts([signal], graph)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].path_node_ids, ["copper", "quartz"])
        self.assertEqual(alerts[0].path_node_ids[-1], "quartz")

        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = Path(temp_dir) / "workflow_graph.json"
            client = TestClient(app)
            saved = {
                "version": "0.1.0", "revision": 0,
                "nodes": [{"id": "server-copper", "symbol": "hf_CAD"}], "links": [],
            }
            stale = {
                "version": "0.1.0", "revision": 0,
                "nodes": [{"id": "draft-quartz", "symbol": "SIM-QUARTZ", "node_kind": "supplier"}],
                "links": [{"source": "draft-quartz", "target": "draft-customer"}],
            }
            with patch("src.external_risk.service._workflow_graph_path", return_value=graph_path):
                self.assertEqual(client.put("/external-risk/workflow", json=saved).status_code, 200)
                conflict = client.put("/external-risk/workflow", json=stale)

        self.assertEqual(conflict.status_code, 409)
        relations = conflict.json()["diff"]["relations"]
        self.assertTrue(relations["draft_added_unconfirmed_relation_ids"])
        self.assertEqual(relations["preexisting_unconfirmed_relation_ids"], [])
        self.assertEqual(relations["changed_unconfirmed_relation_ids"], [])

    def test_internal_baseline_gate_evidence_and_retry_close_the_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_path = Path(temp_dir) / "internal_risk_workflow.json"
            fixture_path.write_text(Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"), encoding="utf-8")
            documents = DocumentIngestService(
                storage=DocumentTaskStorage(root=Path(temp_dir) / "documents"), parser=_FourthRoundParser(),
            )
            uploaded = documents.create_task(
                filename="电子级石英砂采购与原产地核验记录.pdf",
                content_type="application/pdf", purpose="cross_border_supply_chain",
            )
            documents.save_upload_chunk(uploaded["task_id"], b"%PDF- fourth-round material", 27)
            documents.finalize_upload(uploaded["task_id"], 27)
            service = InternalRiskWorkflowService(
                fixture_path, report_generator=_supported_report, document_service=documents,
            )
            proposal = service.propose_legacy_baseline(
                "demo-ai-enterprise", LegacyBaselineProposalRequest(reason="第四轮测试：初始登记"), "owner-a",
            )
            cancelled = service.cancel_legacy_baseline(
                "demo-ai-enterprise", LegacyBaselineCancelRequest(reason="第四轮测试：发现经营状态需更新"), "owner-a",
            )
            renewed = service.propose_legacy_baseline(
                "demo-ai-enterprise", LegacyBaselineProposalRequest(reason="第四轮测试：重新登记"), "owner-a",
            )
            self.assertEqual((proposal.status, cancelled.status, renewed.status), ("pending_confirmation", "cancelled", "pending_confirmation"))
            self.assertEqual(
                [record.action for record in service.business_state_audit("demo-ai-enterprise")][-3:],
                ["baseline_proposed", "baseline_cancelled", "baseline_proposed"],
            )

            with self.assertRaises(ValidationError):
                GateCheckUpdate(status="passed", evidence_refs=[], note="无证据尝试通过")
            first_gate = service.update_gate_check(
                "gate-model-training-001", "data-source",
                GateCheckUpdate(status="missing", evidence_refs=[], note="等待供应商原产地证明"),
                "risk-operator",
            )
            updated_gate = service.update_gate_check(
                "gate-model-training-001", "data-source",
                GateCheckUpdate(
                    status="passed", evidence_refs=["document:fourth-round-quartz-origin-v1"],
                    note="已完成原产地与出口管制文件核验",
                ),
                "risk-reviewer",
            )
            self.assertEqual(first_gate.gate_id, updated_gate.gate_id)
            checked = next(item for item in updated_gate.checks if item.check_id == "data-source")
            self.assertEqual(checked.status, "passed")
            self.assertEqual(len(checked.evidence_history), 2)
            self.assertEqual(checked.evidence_history[-1]["changed_by"], "risk-reviewer")

            event = service.create_risk_event(RiskEventCreate(
                title="电子级石英砂跨境采购材料评估",
                description="高纯石英砂的原产地证明正在解析，暂不可作为 RAG 的可审阅材料。",
                lifecycle_stage="cross_border", risk_domain="cross_border_supply_chain",
                occurred_at="2026-08-20T10:00:00+08:00", reported_by="risk-operator",
                document_task_ids=[uploaded["task_id"]],
            ))
            job = service.start_risk_event_assessment_job(event.event_id, RiskEventAssessmentRequest(), event.company_id)
            failed = service.run_risk_event_assessment_job(job.assessment_job_id, event.company_id)
            self.assertEqual((failed.status, failed.failure_code), ("failed", "DOCUMENT_NOT_READY"))
            documents.process_task(uploaded["task_id"])
            self.assertEqual(documents.get_task(uploaded["task_id"])["status"], "completed")
            retried = service.retry_risk_event_assessment_job(job.assessment_job_id, event.company_id)
            completed = service.run_risk_event_assessment_job(job.assessment_job_id, event.company_id)
            self.assertEqual((retried.status, retried.retry_count), ("queued", 1))
            self.assertEqual(completed.status, "completed")
            self.assertTrue(any(item.stage == "failed" for item in completed.audit_trail))
            self.assertTrue(any("Retry 1/2" in item.detail for item in completed.audit_trail))

    def test_rag_domain_mismatch_fails_closed_before_human_confirmation(self) -> None:
        result = build_risk_analysis(
            "进口电子级石英砂的出口管制分类和原产地核验缺失。",
            {
                "answer": "该事项存在高风险。[《个人信息保护法》第十七条]",
                "risk_level": "high", "risk_types": ["数据处理风险"],
                "recommended_actions": ["完善告知"],
                "evidence_chain": [{
                    "citation": "[《个人信息保护法》第十七条]", "source": "个人信息保护法",
                    "law_name": "个人信息保护法", "document_type": "法律法规", "law_level": "法律",
                    "article_no": 17, "content": "处理个人信息应当遵循公开透明原则。",
                }],
            },
            expected_risk_domain="cross_border_supply_chain",
        )
        self.assertEqual(result["decision_state"], "pending_evidence")
        self.assertIsNone(result["risk_level"])
        self.assertEqual(result["evidence_guardrail"]["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
