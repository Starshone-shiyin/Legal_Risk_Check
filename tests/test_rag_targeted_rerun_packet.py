import tempfile
import unittest
from pathlib import Path

from tools.build_rag_targeted_rerun_packet import build_report, write_json


def row(
    case_id,
    next_action,
    *,
    passed=True,
    bucket="anchor_only_or_anchor_primary",
    score=35,
    labels=None,
):
    return {
        "id": case_id,
        "category": "test_domain",
        "passed": passed,
        "dependency_bucket": bucket,
        "independence_score": score,
        "next_action": next_action,
        "contribution_labels": labels or ["ANCHOR_PASS"],
        "retrieval_layers": {
            "dense": {"satisfied": False, "matched_count": 0},
            "sparse": {"satisfied": False, "matched_count": 0},
            "union": {"satisfied": False, "matched_count": 0},
            "anchor": {"satisfied": True, "matched_count": 3},
            "final": {"satisfied": True, "matched_count": 3},
        },
    }


class RagTargetedRerunPacketTest(unittest.TestCase):
    def build_with_rows(self, rows, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "baseline.json"
            output_path = root / "targeted.json"
            write_json(input_path, {"case_rows": rows})
            return build_report(input_path, output_eval_path=output_path, cases_path=Path("tests/rag_eval_cases.json"), **kwargs)

    def test_build_report_selects_bounded_groups_without_runtime_recommendation(self):
        report = self.build_with_rows(
            [
                row("base_a", "inspect_base_retrieval_query_lexical_coverage", score=20),
                row("base_b", "inspect_base_retrieval_query_lexical_coverage", score=30),
                row("rule_a", "inspect_output_rule_dependency", bucket="risk_supplement_primary", labels=["RISK_SUPPLEMENT_PASS"], score=70),
                row("failed_a", "failed_case_fact_or_expected_level_review", passed=False, score=5),
                row("control_a", "candidate_stable_baseline", bucket="pure_llm_or_low_rule_dependency", labels=["PURE_LLM_PASS"], score=100),
            ],
            max_base_triage=1,
            max_output_rule=1,
            max_control=1,
            repeat=2,
        )

        summary = report["summary"]
        self.assertEqual(summary["status"], "targeted_rerun_packet_ready")
        self.assertEqual(summary["selected_case_count"], 4)
        self.assertEqual(summary["runtime_patch_recommendation"], "not_recommended_by_this_packet")
        self.assertEqual(report["guardrails"]["runs_eval"], "disallowed")
        self.assertIn("--repeat 2", report["suggested_commands"]["combined_targeted_repeat"])
        self.assertIn("--case-id base_a", report["suggested_commands"]["combined_targeted_repeat"])
        self.assertNotIn("--case-id base_b", report["suggested_commands"]["combined_targeted_repeat"])

    def test_failed_case_is_kept_in_separate_group(self):
        report = self.build_with_rows(
            [
                row("base_a", "inspect_base_retrieval_query_lexical_coverage"),
                row("failed_a", "failed_case_fact_or_expected_level_review", passed=False, score=0),
            ]
        )

        groups = {group["group_id"]: group for group in report["groups"]}
        self.assertEqual(groups["failed_or_expected_level_review"]["case_ids"], ["failed_a"])
        self.assertEqual(groups["failed_or_expected_level_review"]["cases"][0]["passed"], False)

    def test_empty_input_reports_no_candidates(self):
        report = self.build_with_rows([])

        self.assertEqual(report["summary"]["status"], "no_targeted_rerun_candidates")
        self.assertEqual(report["summary"]["selected_case_count"], 0)
        self.assertEqual(report["suggested_commands"]["combined_targeted_repeat"], "")


if __name__ == "__main__":
    unittest.main()
