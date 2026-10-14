import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_near_tie_patch_validation import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_REPEAT_REPORT_PATH,
    DEFAULT_SUMMARY_PATH,
    GUARDRAILS,
    VERSION,
    build_report,
    collect_case_runs,
    main,
    render_markdown,
    write_json,
)


def repeat_payload(*, stable: bool = True, all_pass: bool = True):
    selected_a = [
        {"source": "Law A", "article_no": 24, "exact_key": "a24"},
        {"source": "Law A", "article_no": 48, "exact_key": "a48"},
        {"source": "Law B", "article_no": 20, "exact_key": "b20"},
    ]
    selected_b = [
        {"source": "Law A", "article_no": 24, "exact_key": "a24"},
        {"source": "Law A", "article_no": 48, "exact_key": "a48"},
        {"source": "Law C", "article_no": 56, "exact_key": "c56"},
    ]
    runs = []
    for index in range(1, 4):
        selected = selected_a if stable or index < 3 else selected_b
        runs.append(
            {
                "run": index,
                "total": 1,
                "passed": 1 if all_pass else 0,
                "reports": [
                    {
                        "id": "case_alpha",
                        "passed": all_pass,
                        "retrieval_failure_stage": "PASS" if all_pass else "FINAL",
                        "debug_info": {
                            "final_evidence_selection_trace": {
                                "selected": selected,
                            }
                        },
                    }
                ],
            }
        )
    return {
        "repeat": len(runs),
        "stability_summary": {"all_runs_full_pass": all_pass},
        "runs": runs,
    }


class PostRebuildNearTiePatchValidationTest(unittest.TestCase):
    def test_default_paths_and_guardrails(self):
        self.assertEqual(VERSION, "0.4.15.6")
        self.assertEqual(
            DEFAULT_REPEAT_REPORT_PATH,
            Path("tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json"),
        )
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            Path("tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json"),
        )
        self.assertEqual(
            DEFAULT_SUMMARY_PATH,
            Path("docs/post_rebuild_near_tie_patch_validation_v0.4.15.6.md"),
        )
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["rerank_score_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_collect_case_runs_uses_final_selection_trace(self):
        runs = collect_case_runs(repeat_payload())

        self.assertEqual(len(runs), 3)
        self.assertEqual(runs[0]["selected_evidence"][0], "Law A|article:24")
        self.assertEqual(runs[0]["selected_evidence"][2], "Law B|article:20")

    def test_stable_repeat_passes_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "repeat.json"
            write_json(path, repeat_payload())

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["unique_selected_evidence_chains"], 1)
        self.assertTrue(
            next(item for item in report["checks"] if item["name"] == "selected_evidence_identity_stable")[
                "passed"
            ]
        )

    def test_missing_repeat_report_blocks_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.json"

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("repeat_report_missing_or_unavailable", report["summary"]["blockers"])
        self.assertFalse(report["checks"][0]["passed"])

    def test_unstable_repeat_blocks_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "repeat.json"
            write_json(path, repeat_payload(stable=False))

            report = build_report(path)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("selected_evidence_identity_stable", report["summary"]["blockers"])

    def test_markdown_documents_patch_boundary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "repeat.json"
            write_json(path, repeat_payload())

            markdown = render_markdown(build_report(path))

        self.assertIn("Near-Tie Patch Validation", markdown)
        self.assertIn("same-bucket deterministic ordering", markdown)
        self.assertIn("add anchors", markdown)
        self.assertIn("change prompt", markdown)

    def test_main_writes_report_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "repeat.json"
            output = Path(tmpdir) / "report.json"
            summary = Path(tmpdir) / "summary.md"
            write_json(input_path, repeat_payload())

            import sys

            old_argv = sys.argv
            try:
                sys.argv = [
                    "build_post_rebuild_near_tie_patch_validation.py",
                    "--repeat-report",
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
