from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.internal_risk.schemas import (
    RiskEventAssessmentRequest,
    RiskEventConfirmationUpdate,
    RiskEventCreate,
)
from src.internal_risk.service import InternalRiskWorkflowService, RiskWorkflowStateError
from src.risk.analyzer import build_risk_analysis


class _CompletedDocumentService:
    def __init__(self) -> None:
        self.requested_ids: list[str] | None = None

    def build_llm_materials(self, task_ids: list[str] | None) -> list[dict]:
        self.requested_ids = task_ids
        return [{
            "task_id": "a" * 32,
            "filename": "supplier-review.pdf",
            "content": "供应商原产地、出口管制分类和替代采购安排尚待核验。",
            "truncated": False,
        }]


class InternalRagEvidenceGuardrailTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_path = Path(self.temporary_directory.name) / "internal_risk_workflow.json"
        self.fixture_path.write_text(
            Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_completed_documents_are_bounded_inputs_and_snapshot_provenance(self) -> None:
        documents = _CompletedDocumentService()
        received: dict = {}

        def report_generator(scenario: str, **kwargs: object) -> dict:
            received["scenario"] = scenario
            received.update(kwargs)
            return {
                "risk_level": "medium",
                "citation_integrity": {"passed": True},
                "review_reasons": [],
                "source_analysis": {},
            }

        service = InternalRiskWorkflowService(
            self.fixture_path,
            report_generator=report_generator,
            document_service=documents,  # type: ignore[arg-type]
        )
        event = service.create_risk_event(RiskEventCreate(
            title="原料进口合规核验缺口",
            description="电子级材料采购计划缺少原产地和出口管制核验记录。",
            lifecycle_stage="cross_border",
            risk_domain="cross_border_supply_chain",
            occurred_at="2026-08-20T09:00:00+08:00",
            reported_by="risk-operator",
            document_task_ids=["a" * 32],
        ))

        assessed = service.assess_risk_event(event.event_id, RiskEventAssessmentRequest())

        self.assertEqual(documents.requested_ids, ["a" * 32])
        self.assertEqual(received["expected_risk_domain"], "cross_border_supply_chain")
        self.assertEqual(received["user_materials"][0]["task_id"], "a" * 32)
        snapshot = assessed.assessment_snapshot
        assert snapshot is not None
        self.assertEqual(snapshot.material_sources[0]["filename"], "supplier-review.pdf")
        self.assertNotIn("content", snapshot.material_sources[0])
        self.assertEqual(snapshot.report["material_sources"][0]["task_id"], "a" * 32)
        self.assertEqual(snapshot.processing_metrics["material_count"], 1)
        self.assertIn("material_load_elapsed_ms", snapshot.processing_metrics["stages"])
        self.assertIn("rag_report_elapsed_ms", snapshot.processing_metrics["stages"])

    def test_pending_evidence_report_cannot_create_risk_item(self) -> None:
        service = InternalRiskWorkflowService(
            self.fixture_path,
            report_generator=lambda *_args, **_kwargs: {
                "risk_level": None,
                "decision_state": "pending_evidence",
                "citation_integrity": {"passed": False},
                "review_reasons": ["引用完整性校验失败"],
                "source_analysis": {},
            },
            document_service=_CompletedDocumentService(),  # type: ignore[arg-type]
        )
        event = service.create_risk_event(RiskEventCreate(
            title="供应链法源错配",
            description="跨境供应链事件只检索到无关个人信息条款。",
            lifecycle_stage="cross_border",
            risk_domain="cross_border_supply_chain",
            occurred_at="2026-08-20T09:00:00+08:00",
            reported_by="risk-operator",
        ))
        service.assess_risk_event(event.event_id, RiskEventAssessmentRequest())

        with self.assertRaisesRegex(RiskWorkflowStateError, "pending evidence"):
            service.confirm_risk_event(
                event.event_id,
                RiskEventConfirmationUpdate(
                    decision="confirmed", reviewer="risk-reviewer", conclusion="attempt confirmation",
                ),
            )

    def test_domain_mismatch_with_valid_citation_fails_closed(self) -> None:
        rag_result = {
            "answer": "该安排存在高风险。[《个人信息保护法》第十七条]",
            "risk_level": "high",
            "risk_types": ["数据处理风险"],
            "recommended_actions": ["完善告知"],
            "evidence_chain": [{
                "citation": "[《个人信息保护法》第十七条]",
                "source": "个人信息保护法",
                "law_name": "个人信息保护法",
                "document_type": "法律法规",
                "law_level": "法律",
                "article_no": 17,
                "content": "处理个人信息应当遵循公开透明原则。",
            }],
        }

        result = build_risk_analysis(
            "进口电子级材料的出口管制和原产地核验缺失。",
            rag_result,
            expected_risk_domain="cross_border_supply_chain",
        )

        self.assertIsNone(result["risk_level"])
        self.assertEqual(result["risk_types"], [])
        self.assertEqual(result["recommended_actions"], [])
        self.assertEqual(result["decision_state"], "pending_evidence")
        self.assertTrue(result["needs_human_review"])
        self.assertEqual(result["evidence_guardrail"]["status"], "blocked")

    def test_citation_failure_fails_closed_even_without_domain_guard(self) -> None:
        result = build_risk_analysis("测试场景", {
            "answer": "该安排违法。[《个人信息保护法》第九十九条]",
            "risk_level": "high",
            "risk_types": ["数据处理风险"],
            "recommended_actions": ["完善告知"],
            "evidence_chain": [{
                "citation": "[《个人信息保护法》第十七条]", "source": "个人信息保护法", "article_no": 17,
            }],
        })

        self.assertIsNone(result["risk_level"])
        self.assertEqual(result["decision_state"], "pending_evidence")

    def test_uncited_core_decision_fails_closed_on_citation_coverage(self) -> None:
        result = build_risk_analysis("测试场景", {
            "answer": "该事项存在高风险，企业应当立即停止相关安排并完成专项整改。",
            "risk_level": "high",
            "risk_types": ["数据处理风险"],
            "recommended_actions": ["立即停止相关安排"],
            "evidence_chain": [{
                "citation": "[《个人信息保护法》第十七条]", "source": "个人信息保护法", "article_no": 17,
            }],
        })

        self.assertIsNone(result["risk_level"])
        self.assertEqual(result["risk_types"], [])
        self.assertEqual(result["recommended_actions"], [])
        self.assertEqual(result["decision_state"], "pending_evidence")
        self.assertTrue(result["evidence_guardrail"]["citation_coverage"]["requires_review"])


if __name__ == "__main__":
    unittest.main()
