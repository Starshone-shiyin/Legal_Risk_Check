from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.internal_risk.schemas import RiskEventAssessmentRequest, RiskEventCreate
from src.internal_risk.service import InternalRiskWorkflowService, RiskWorkflowStateError


class _CompletedDocuments:
    def build_llm_materials(self, task_ids: list[str] | None) -> list[dict]:
        return [{
            "task_id": "b" * 32,
            "filename": "supplier-control.pdf",
            "content": "供应商出口管制分类、原产地声明和替代采购安排已经归档。",
            "truncated": False,
        }]


def _supported_report(_: str, **__: object) -> dict:
    return {
        "risk_level": "medium",
        "review_reasons": [],
        "source_analysis": {},
        "citation_integrity": {
            "passed": True,
            "coverage": {"requires_review": False},
        },
    }


class InternalRiskAssessmentJobTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_path = Path(self.temporary_directory.name) / "internal_risk_workflow.json"
        self.fixture_path.write_text(
            Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.service = InternalRiskWorkflowService(
            self.fixture_path,
            report_generator=_supported_report,
            document_service=_CompletedDocuments(),  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _event(self):
        return self.service.create_risk_event(RiskEventCreate(
            title="电子级材料供应商证据核验",
            description="进口电子级材料供应商的出口管制分类和原产地证明需要进行RAG证据评估。",
            lifecycle_stage="cross_border",
            risk_domain="cross_border_supply_chain",
            occurred_at="2026-08-20T09:00:00+08:00",
            reported_by="risk-operator",
            document_task_ids=["b" * 32],
        ))

    def test_async_job_persists_stages_and_result_snapshot(self) -> None:
        event = self._event()
        job = self.service.start_risk_event_assessment_job(
            event.event_id, RiskEventAssessmentRequest(), event.company_id,
        )

        self.assertEqual(job.status, "queued")
        self.assertEqual(job.stage, "accepted")
        with self.assertRaisesRegex(RiskWorkflowStateError, "active assessment job"):
            self.service.assess_risk_event(event.event_id, RiskEventAssessmentRequest(), event.company_id)

        completed = self.service.run_risk_event_assessment_job(job.assessment_job_id, event.company_id)
        loaded = self.service.assessment_job(job.assessment_job_id, event.company_id)
        assessed_event = self.service.risk_event(event.event_id, event.company_id)

        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.stage, "snapshot_persisted")
        self.assertEqual(loaded.assessment_snapshot_id, assessed_event.assessment_snapshot.snapshot_id)
        self.assertIsNotNone(loaded.result_sha256)
        self.assertEqual(
            [entry.stage for entry in loaded.audit_trail],
            ["accepted", "material_loading", "rag_assessment", "snapshot_persisted"],
        )
        self.assertEqual(assessed_event.status, "assessed")

    def test_failed_job_retains_auditable_failure_without_assessment_snapshot(self) -> None:
        event = self._event()
        job = self.service.start_risk_event_assessment_job(
            event.event_id, RiskEventAssessmentRequest(), event.company_id,
        )
        self.service.document_service = _FailingDocuments()  # type: ignore[assignment]

        failed = self.service.run_risk_event_assessment_job(job.assessment_job_id, event.company_id)

        self.assertEqual(failed.status, "failed")
        self.assertEqual(failed.stage, "failed")
        self.assertEqual(failed.failure_code, "DOCUMENT_NOT_READY")
        self.assertIsNone(self.service.risk_event(event.event_id, event.company_id).assessment_snapshot)
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["workflow"]["assessment_jobs"][0]["audit_trail"])


class _FailingDocuments:
    def build_llm_materials(self, task_ids: list[str] | None) -> list[dict]:
        from src.document_ingest.service import DocumentIngestError

        raise DocumentIngestError("DOCUMENT_NOT_READY", "Document material is still processing.", 409)


if __name__ == "__main__":
    unittest.main()
