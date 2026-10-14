import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_near_tie_stability_policy_design import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_SUMMARY_PATH,
    DEFAULT_TRACE_ATTRIBUTION_PATH,
    GUARDRAILS,
    VERSION,
    build_report,
    main,
    render_markdown,
    validate_trace_attribution,
    write_json,
)


def attribution_payload(*, classification: str = "raw_rerank_order_boundary_drift_not_selector_replacement"):
    return {
        "schema_kind": "post_rebuild_selection_trace_attribution",
        "summary": {
            "classification": classification,
            "status": "needs_near_tie_stability_design",
            "runtime_fix_authorized": False,
            "all_selected_alternates_match_trace": True,
            "both_drift_candidates_present_in_full_order_all_runs": True,
            "selected_alternate_is_earlier_full_order_candidate": True,
            "selected_alternate_counts": {
                "中华人民共和国个人信息保护法|56": 2,
                "中华人民共和国网络安全法|20": 3,
            },
            "recommended_next_step": "design_near_tie_stability_policy_before_runtime_change",
        },
    }


class PostRebuildNearTieStabilityPolicyDesignTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(VERSION, "0.4.15.5")
        self.assertEqual(DEFAULT_TRACE_ATTRIBUTION_PATH, Path("tests/post_rebuild_selection_trace_attribution_v0.4.15.4_report.json"))
        self.assertEqual(DEFAULT_OUTPUT_PATH, Path("tests/post_rebuild_near_tie_stability_policy_design_v0.4.15.5_report.json"))
        self.assertEqual(DEFAULT_SUMMARY_PATH, Path("docs/post_rebuild_near_tie_stability_policy_design_v0.4.15.5.md"))
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertTrue(GUARDRAILS["design_only"])
        self.assertEqual(GUARDRAILS["runtime_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["rerank_score_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_validation_blocks_wrong_classification(self):
        validation = validate_trace_attribution(attribution_payload(classification="selector_replacement"))

        self.assertIn("classification_supports_near_tie_design", validation["blockers"])

    def test_real_trace_attribution_opens_near_tie_policy_review(self):
        report = build_report()

        self.assertEqual(report["version"], "0.4.15.5")
        self.assertEqual(report["summary"]["status"], "ready_for_near_tie_policy_review")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertFalse(report["summary"]["runtime_patch_authorized"])
        self.assertEqual(
            report["proposed_policy"]["name"],
            "deterministic_same_bucket_order_stabilization",
        )
        self.assertIn("legal_alignment_profile_score", report["proposed_policy"]["candidate_tie_break_keys_in_priority_order"])
        self.assertIn("Using case id specific branches.", report["proposed_policy"]["explicitly_disallowed"])

    def test_markdown_documents_design_only_boundary(self):
        markdown = render_markdown(build_report())

        self.assertIn("Near-Tie Stability Policy Design", markdown)
        self.assertIn("design-only", markdown)
        self.assertIn("不改变 Cross-Encoder 分数", markdown)
        self.assertIn("不写 case id 分支", markdown)

    def test_main_writes_report_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output = Path(tmpdir) / "report.json"
            summary = Path(tmpdir) / "summary.md"
            write_json(input_path, attribution_payload())

            import sys

            old_argv = sys.argv
            try:
                sys.argv = [
                    "build_post_rebuild_near_tie_stability_policy_design.py",
                    "--trace-attribution",
                    str(input_path),
                    "--output",
                    str(output),
                    "--summary",
                    str(summary),
                ]
                exit_code = main()
            finally:
                sys.argv = old_argv

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertTrue(summary.exists())


if __name__ == "__main__":
    unittest.main()
