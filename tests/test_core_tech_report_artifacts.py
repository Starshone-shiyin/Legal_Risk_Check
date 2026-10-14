"""Offline integrity checks for the core-technology report artifacts.

These checks deliberately validate saved documents and JSON structures only. They
must remain runnable without a live RAG service, Qdrant, model provider, or
network connection.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"


def _read_text(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def _read_json(relative_path: str) -> dict:
    return json.loads(_read_text(relative_path))


class CoreTechReportArtifactTest(unittest.TestCase):
    def test_evidence_sufficiency_document_explains_score_and_routes(self):
        content = _read_text("docs/evidence_sufficiency_gate.md")

        self.assertIn("Evidence Sufficiency Gate", content)
        self.assertIn("ESG =", content)
        self.assertIn("Routing Policy", content)
        for route in ("answer_with_evidence", "web_supplement", "human_review"):
            self.assertIn(route, content)

    def test_evidence_sufficiency_diagram_covers_the_three_outcomes(self):
        content = _read_text("docs/diagrams/evidence_sufficiency_gate.mmd")

        self.assertIn("flowchart", content)
        self.assertIn("ESG score", content)
        for outcome in ("Answer with evidence", "Controlled web supplement", "Human review"):
            self.assertIn(outcome, content)

    def test_esg_smoke_cases_are_nonempty_and_identifiable(self):
        payload = _read_json("tests/rag_esg_smoke_cases.json")
        cases = payload.get("cases")

        self.assertIsInstance(cases, list)
        self.assertGreater(len(cases), 0)
        for case in cases:
            self.assertIsInstance(case.get("id"), str)
            self.assertTrue(case["id"].strip())
            self.assertIsInstance(case.get("question"), str)
            self.assertTrue(case["question"].strip())
            self.assertIsInstance(case.get("expected_evidence"), list)

    def test_esg_smoke_report_matches_case_fixture_and_has_gate_metrics(self):
        cases = _read_json("tests/rag_esg_smoke_cases.json")["cases"]
        report = _read_json("tests/rag_esg_smoke_report.json")

        self.assertEqual(report.get("schema_version"), "rag-ablation-v1")
        self.assertEqual(report.get("status"), "completed")
        self.assertEqual(report.get("case_count"), len(cases))
        self._assert_esg_profile(report, "M4_full", expected_case_count=len(cases))

    def test_core_ablation_report_has_four_profiles_and_valid_summaries(self):
        report = _read_json("tests/rag_ablation_report.json")

        self.assertEqual(report.get("schema_version"), "rag-ablation-v1")
        self.assertEqual(report.get("status"), "completed")
        self.assertGreater(report.get("case_count", 0), 0)
        self.assertTrue(report.get("case_file_sha256"))
        self.assertTrue({"M1_dense", "M2_hybrid", "M3_concept", "M4_full"}.issubset(report.get("profiles", {})))

        for profile_name in ("M1_dense", "M2_hybrid", "M3_concept", "M4_full"):
            profile = report["profiles"][profile_name]
            self.assertIsInstance(profile.get("cases"), list)
            self.assertEqual(len(profile["cases"]), report["case_count"])
            self._assert_metric_summary(profile.get("summary", {}))

        # The four-profile ablation artifact predates ESG; ESG is reported in
        # its dedicated M4 artifact and checked separately below.
        esg_report = _read_json("tests/rag_esg_m4_report.json")
        self.assertEqual(esg_report.get("case_count"), report["case_count"])
        self._assert_esg_profile(esg_report, "M4_full", expected_case_count=report["case_count"])

    def test_ablation_judge_artifact_is_consistent_with_core_report(self):
        report = _read_json("tests/rag_ablation_report.json")
        judge = _read_json("tests/rag_ablation_judge_report.json")

        self.assertEqual(judge.get("schema_version"), "rag-ablation-judge-v1")
        self.assertIn(judge.get("verdict"), {"accepted", "passed", "warning", "failed"})
        self.assertEqual(judge.get("case_count"), report.get("case_count"))
        self.assertEqual(judge.get("case_file_sha256"), report.get("case_file_sha256"))
        checks = judge.get("checks")
        self.assertIsInstance(checks, dict)
        self.assertGreater(len(checks), 0)
        self.assertTrue(all(isinstance(value, bool) for value in checks.values()))

    @staticmethod
    def _assert_metric_summary(summary: dict) -> None:
        for key in ("evidence_recall_at_k", "mrr_at_k", "ndcg_at_k", "multi_source_coverage"):
            value = summary.get(key)
            assert isinstance(value, (int, float)), f"{key} must be numeric"
            assert 0.0 <= value <= 1.0, f"{key} must be within [0, 1]"

        for key in ("retrieval_time_p50_ms", "retrieval_time_p95_ms"):
            value = summary.get(key)
            assert isinstance(value, (int, float)), f"{key} must be numeric"
            assert value >= 0.0, f"{key} must not be negative"

    def _assert_esg_profile(self, report: dict, profile_name: str, *, expected_case_count: int) -> None:
        profile = report.get("profiles", {}).get(profile_name)
        self.assertIsInstance(profile, dict)
        esg_summary = profile.get("evidence_sufficiency_summary", {})
        self.assertEqual(esg_summary.get("case_count"), expected_case_count)

        for key in ("mean_score", "sufficient_rate", "web_supplement_rate", "human_review_rate", "local_primary_law_coverage"):
            value = esg_summary.get(key)
            self.assertIsInstance(value, (int, float), key)
            self.assertGreaterEqual(value, 0.0, key)
            self.assertLessEqual(value, 1.0, key)

        cases = profile.get("cases", [])
        self.assertEqual(len(cases), expected_case_count)
        for case in cases:
            evidence_sufficiency = case.get("evidence_sufficiency", {})
            self.assertIn(evidence_sufficiency.get("recommended_route"), {
                "answer_with_evidence",
                "web_supplement",
                "human_review",
            })
            self.assertIsInstance(evidence_sufficiency.get("gaps"), list)


if __name__ == "__main__":
    unittest.main()
