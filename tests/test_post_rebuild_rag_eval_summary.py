import json
import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_rag_eval_summary import build_summary_report


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def check(name: str, passed: bool, message: str = "") -> dict:
    return {"name": name, "passed": passed, "message": message}


def case_report(case_id: str, passed: bool, checks: list[dict], layers: dict | None = None) -> dict:
    return {
        "id": case_id,
        "passed": passed,
        "retrieval_failure_stage": "PASS" if passed else "RERANK_MISS",
        "retrieval_diagnostics": {"layers": layers or {}},
        "checks": checks,
        "question": "sample question",
        "answer": "sample answer",
        "evidence": [],
    }


class PostRebuildRagEvalSummaryTest(unittest.TestCase):
    def test_passes_when_post_rebuild_matches_baseline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline = root / "baseline.json"
            post = root / "post.json"
            base_payload = {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "reports": [case_report("case_a", True, [check("expected_evidence", True)])],
            }
            write_json(baseline, base_payload)
            write_json(post, base_payload)

            report = build_summary_report(post_rebuild_rag_path=post, baseline_rag_path=baseline)

        self.assertEqual(report["version"], "0.4.14.31")
        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["rag_eval_summary"]["regression_count"], 0)
        self.assertEqual(report["failed_cases"], [])

    def test_classifies_final_evidence_selection_drop_without_case_id_logic(self):
        layers = {
            "sparse": {"satisfied": True, "matched_count": 1, "expected_count": 1, "required_count": 1},
            "rerank_input": {"satisfied": True, "matched_count": 1, "expected_count": 1, "required_count": 1},
            "final": {"satisfied": False, "matched_count": 0, "expected_count": 1, "required_count": 1},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline = root / "baseline.json"
            post = root / "post.json"
            write_json(
                baseline,
                {"total": 1, "passed": 1, "failed": 0, "reports": [case_report("generic_case", True, [check("expected_evidence", True)])]},
            )
            write_json(
                post,
                {
                    "total": 1,
                    "passed": 0,
                    "failed": 1,
                    "reports": [case_report("generic_case", False, [check("expected_evidence", False, "missing")], layers)],
                },
            )

            report = build_summary_report(post_rebuild_rag_path=post, baseline_rag_path=baseline)

        self.assertEqual(report["summary"]["status"], "needs_triage")
        self.assertIn("baseline_full_rag_regressions", report["summary"]["blockers"])
        self.assertEqual(report["failed_cases"][0]["classification"], "final_evidence_selection_drop")
        self.assertTrue(report["failed_cases"][0]["is_regression"])

    def test_classifies_answer_keyword_gap_when_final_evidence_is_present(self):
        layers = {
            "final": {"satisfied": True, "matched_count": 1, "expected_count": 1, "required_count": 1},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            baseline = root / "baseline.json"
            post = root / "post.json"
            write_json(
                baseline,
                {"total": 1, "passed": 1, "failed": 0, "reports": [case_report("case_b", True, [check("expected_answer_keywords", True)])]},
            )
            write_json(
                post,
                {
                    "total": 1,
                    "passed": 0,
                    "failed": 1,
                    "reports": [case_report("case_b", False, [check("expected_answer_keywords", False, "missing keyword")], layers)],
                },
            )

            report = build_summary_report(post_rebuild_rag_path=post, baseline_rag_path=baseline)

        self.assertEqual(report["failed_cases"][0]["classification"], "answer_keyword_coverage_gap")
        self.assertEqual(report["rag_eval_summary"]["failed_check_summary"], {"expected_answer_keywords": 1})


if __name__ == "__main__":
    unittest.main()
