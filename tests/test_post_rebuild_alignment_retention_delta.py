import json
import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_alignment_retention_delta import build_delta_report


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def check(name: str, passed: bool, message: str = "") -> dict:
    return {"name": name, "passed": passed, "message": message}


def evidence(source: str, article_no: int, citation: str | None = None, rank: int = 1) -> dict:
    return {
        "rank": rank,
        "source": source,
        "law_name": source,
        "article_no": article_no,
        "section_no": "",
        "citation": citation or f"[{source}第{article_no}条]",
        "rerank_score": 0.9,
    }


def case_report(case_id: str, passed: bool, evidence_items: list[dict], checks: list[dict] | None = None) -> dict:
    return {
        "id": case_id,
        "category": "sample",
        "question": "sample question",
        "passed": passed,
        "checks": checks or [check("expected_evidence", passed)],
        "evidence": evidence_items,
    }


def eval_case(case_id: str, expected: list[dict] | None = None) -> dict:
    return {"id": case_id, "expected_evidence": expected or []}


class PostRebuildAlignmentRetentionDeltaTest(unittest.TestCase):
    def build_with(self, before_cases: list[dict], after_cases: list[dict], eval_cases: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            before = root / "before.json"
            after = root / "after.json"
            cases = root / "cases.json"
            write_json(
                before,
                {
                    "total": len(before_cases),
                    "passed": sum(1 for item in before_cases if item["passed"]),
                    "failed": sum(1 for item in before_cases if not item["passed"]),
                    "reports": before_cases,
                },
            )
            write_json(
                after,
                {
                    "total": len(after_cases),
                    "passed": sum(1 for item in after_cases if item["passed"]),
                    "failed": sum(1 for item in after_cases if not item["passed"]),
                    "reports": after_cases,
                },
            )
            write_json(cases, {"cases": eval_cases})

            return build_delta_report(before_path=before, after_path=after, eval_cases_path=cases)

    def test_reports_same_case_ids_and_counts_delta_statuses(self):
        report = build_delta_report()

        self.assertEqual(report["comparison_summary"]["before_passed"], 58)
        self.assertEqual(report["comparison_summary"]["after_passed"], 60)
        self.assertEqual(report["comparison_summary"]["missing_from_after"], [])
        self.assertEqual(report["comparison_summary"]["new_in_after"], [])
        self.assertEqual(report["comparison_summary"]["pass_status_summary"]["improved"], 2)
        self.assertEqual(report["comparison_summary"]["pass_status_summary"].get("regressed", 0), 0)

    def test_detects_added_and_removed_final_evidence_by_canonical_key(self):
        before_case = case_report("generic", True, [evidence("Law A", 1), evidence("Law A", 2)])
        after_case = case_report("generic", True, [evidence("Law A", 1), evidence("Law A", 3)])

        report = self.build_with([before_case], [after_case], [eval_case("generic")])
        row = report["cases"][0]

        self.assertEqual(row["evidence_delta_kind"], "replacement")
        self.assertEqual(row["evidence_delta"]["added_evidence"][0]["evidence_key"], "Law A::3::")
        self.assertEqual(row["evidence_delta"]["removed_evidence"][0]["evidence_key"], "Law A::2::")

    def test_classifies_citation_only_delta_without_replacement(self):
        before_case = case_report("generic", True, [evidence("Law A", 35, "[Law A Article 35 Paragraph 1]")])
        after_case = case_report("generic", True, [evidence("Law A", 35, "[Law A Article 35]")])

        report = self.build_with([before_case], [after_case], [eval_case("generic")])
        row = report["cases"][0]

        self.assertEqual(row["evidence_delta_kind"], "citation_only")
        self.assertEqual(row["classification"], "harmless_citation_normalization")
        self.assertEqual(row["risk_flags"], [])

    def test_marks_trademark_non_use_as_explained_improvement(self):
        report = build_delta_report()
        row = next(item for item in report["cases"] if item["case_id"] == "risk_trademark_non_use_001")

        self.assertEqual(row["pass_status"]["delta"], "improved")
        self.assertEqual(row["classification"], "explained_improvement")
        self.assertTrue(row["evidence_delta"]["expected_evidence_delta"]["added_expected"])
        self.assertFalse(any(flag["severity"] == "block" for flag in row["risk_flags"]))

    def test_flags_unchanged_pass_replacement_as_warn(self):
        before_case = case_report("generic", True, [evidence("Law A", 1), evidence("Law A", 2)])
        after_case = case_report("generic", True, [evidence("Law A", 1), evidence("Law A", 3)])

        report = self.build_with([before_case], [after_case], [eval_case("generic")])
        row = report["cases"][0]

        self.assertEqual(row["classification"], "unchanged_pass_with_replacement_needs_review")
        self.assertTrue(any(flag["severity"] == "warn" for flag in row["risk_flags"]))

    def test_removed_expected_evidence_is_blocker(self):
        before_case = case_report("generic", True, [evidence("Law A", 1), evidence("Law A", 2)])
        after_case = case_report("generic", True, [evidence("Law A", 2), evidence("Law A", 3)])

        report = self.build_with(
            [before_case],
            [after_case],
            [eval_case("generic", [{"source": "Law A", "article_no": 1}])],
        )

        self.assertEqual(report["summary"]["status"], "needs_triage")
        self.assertIn("expected_evidence_removed", report["summary"]["blockers"])

    def test_regressed_with_evidence_change_is_blocker(self):
        before_case = case_report("generic", True, [evidence("Law A", 1)])
        after_case = case_report("generic", False, [evidence("Law A", 2)], [check("expected_evidence", False)])

        report = self.build_with([before_case], [after_case], [eval_case("generic")])

        self.assertEqual(report["summary"]["status"], "needs_triage")
        self.assertIn("post_fix_eval_regression_detected", report["summary"]["blockers"])
        self.assertEqual(report["cases"][0]["classification"], "regression_needs_triage")

    def test_saved_reports_only_contract(self):
        report = build_delta_report()

        self.assertTrue(report["inputs"]["saved_reports_only"])
        self.assertEqual(report["summary"]["runtime_changes"], "not_performed")
        self.assertEqual(report["summary"]["qdrant_access"], "not_called_by_delta_builder")
        self.assertEqual(report["summary"]["llm_access"], "not_called_by_delta_builder")


if __name__ == "__main__":
    unittest.main()
