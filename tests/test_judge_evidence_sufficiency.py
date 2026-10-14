"""Regression tests for the Evidence Sufficiency experiment report judge."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
JUDGE_PATH = ROOT / "tools" / "judge_evidence_sufficiency.py"
SPEC = importlib.util.spec_from_file_location("judge_evidence_sufficiency", JUDGE_PATH)
assert SPEC and SPEC.loader
JUDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JUDGE)


def _case(*, expected: int = 1, score: float = 0.95, status: str = "sufficient", route: str = "answer_with_evidence", local_law_count: int = 1) -> dict:
    return {
        "id": "case-1",
        "metrics": {
            "expected_evidence": expected,
            "matched_evidence": expected,
            "evidence_recall_at_k": 1.0,
            "mrr_at_k": 1.0,
            "ndcg_at_k": 1.0,
            "multi_source_coverage": 1.0,
        },
        "evidence_sufficiency": {
            "status": status,
            "score": score,
            "recommended_route": route,
            "local_legal_evidence_count": local_law_count,
        },
    }


def _formal_report() -> dict:
    first = _case(score=1.0)
    second = _case(score=0.8, status="review", route="human_review", local_law_count=0)
    return {
        "status": "completed",
        "benchmark_kind": "formal",
        "case_file": "tests/rag_eval_cases.json",
        "case_file_sha256": "a" * 64,
        "case_count": 2,
        "profiles": {
            "M4_full": {
                "cases": [first, second],
                "evidence_sufficiency_summary": {
                    "case_count": 2,
                    "mean_score": 0.9,
                    "sufficient_rate": 0.5,
                    "web_supplement_rate": 0.0,
                    "human_review_rate": 0.5,
                    "local_primary_law_coverage": 0.5,
                },
            }
        },
    }


class JudgeEvidenceSufficiencyTest(unittest.TestCase):
    def test_existing_smoke_report_is_accepted_but_metrics_are_diagnostic_only(self):
        report = json.loads((ROOT / "tests" / "rag_esg_smoke_report.json").read_text(encoding="utf-8"))

        result = JUDGE.judge(report)

        self.assertEqual(result["verdict"], "accepted")
        self.assertEqual(result["benchmark"]["kind"], "smoke")
        self.assertFalse(result["benchmark"]["formal_retrieval_metrics_eligible"])
        self.assertEqual(result["benchmark"]["smoke_metrics_policy"], "diagnostic_only")
        self.assertTrue(any("must not be reported as formal metrics" in item for item in result["notices"]))

    def test_formal_report_with_expected_evidence_and_consistent_esg_is_accepted(self):
        result = JUDGE.judge(_formal_report())

        self.assertEqual(result["verdict"], "accepted")
        self.assertEqual(result["benchmark"]["kind"], "formal")
        self.assertTrue(result["benchmark"]["formal_retrieval_metrics_eligible"])

    def test_formal_report_without_expected_evidence_is_rejected(self):
        report = _formal_report()
        report["profiles"]["M4_full"]["cases"][1]["metrics"]["expected_evidence"] = 0
        report["profiles"]["M4_full"]["cases"][1]["metrics"]["matched_evidence"] = 0

        result = JUDGE.judge(report)

        self.assertEqual(result["verdict"], "needs_revision")
        formal_gate = next(
            check for check in result["profiles"]["M4_full"]["checks"]
            if check["name"] == "formal_recall_has_expected_evidence"
        )
        self.assertFalse(formal_gate["passed"])
        self.assertIn("no expected_evidence", formal_gate["detail"])

    def test_esg_summary_mismatch_is_rejected(self):
        report = _formal_report()
        report["profiles"]["M4_full"]["evidence_sufficiency_summary"]["mean_score"] = 0.91

        result = JUDGE.judge(report)

        self.assertEqual(result["verdict"], "needs_revision")
        consistency_gate = next(
            check for check in result["profiles"]["M4_full"]["checks"]
            if check["name"] == "esg_summary_consistent"
        )
        self.assertFalse(consistency_gate["passed"])
        self.assertIn("mean_score", consistency_gate["detail"])

    def test_missing_esg_summary_field_is_rejected(self):
        report = _formal_report()
        del report["profiles"]["M4_full"]["evidence_sufficiency_summary"]["human_review_rate"]

        result = JUDGE.judge(report)

        self.assertEqual(result["verdict"], "needs_revision")
        completeness_gate = next(
            check for check in result["profiles"]["M4_full"]["checks"]
            if check["name"] == "esg_summary_complete"
        )
        self.assertFalse(completeness_gate["passed"])
        self.assertIn("human_review_rate", completeness_gate["detail"])

    def test_cli_writes_structured_judgment(self):
        report = _formal_report()
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            output_path = Path(directory) / "judgment.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(JUDGE_PATH), str(report_path), "--output", str(output_path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(written["verdict"], "accepted")


if __name__ == "__main__":
    unittest.main()
