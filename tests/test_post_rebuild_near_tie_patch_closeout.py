import tempfile
import unittest
from pathlib import Path

from tools.build_post_rebuild_near_tie_patch_closeout import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_PATCH_VALIDATION_PATH,
    DEFAULT_PROJECT_HEALTH_PATH,
    DEFAULT_SUMMARY_PATH,
    DEFAULT_TARGETED_REPEAT_PATH,
    EXPECTED_RUNTIME_PATCH_SCOPE,
    GUARDRAILS,
    VERSION,
    build_report,
    main,
    render_markdown,
    write_json,
)


def targeted_repeat_payload(*, all_pass: bool = True):
    return {
        "repeat": 5,
        "stability_summary": {
            "runs": 5,
            "all_runs_full_pass": all_pass,
            "pass_counts": [1, 1, 1, 1, 1] if all_pass else [1, 1, 0, 1, 1],
            "total_counts": [1, 1, 1, 1, 1],
            "unstable_cases": [],
        },
        "runs": [
            {
                "run": index,
                "reports": [{"id": "case_alpha", "passed": all_pass}],
            }
            for index in range(1, 6)
        ],
    }


def validation_payload(*, status: str = "passed", unique_chains: int = 1):
    return {
        "summary": {
            "status": status,
            "blockers": [] if status == "passed" else ["blocked_reason"],
            "runtime_patch_authorized": True,
            "runtime_patch_scope": EXPECTED_RUNTIME_PATCH_SCOPE,
            "repeat_runs": 5,
            "case_run_count": 5,
            "case_ids": ["case_alpha"],
            "unique_selected_evidence_chains": unique_chains,
        },
        "selected_evidence_identity_counts": {
            "Law A|article:24 -> Law A|article:48 -> Law A|article:56": 5
        },
    }


def health_payload(*, status: str = "passed", failed_checks: int = 0):
    return {
        "version": "0.4.15.6",
        "summary": {
            "status": status,
            "total_checks": 486,
            "failed_checks": failed_checks,
            "failed": [],
        },
    }


class PostRebuildNearTiePatchCloseoutTest(unittest.TestCase):
    def write_inputs(self, tmpdir: str, **overrides):
        targeted = Path(tmpdir) / "targeted.json"
        validation = Path(tmpdir) / "validation.json"
        health = Path(tmpdir) / "health.json"
        if not overrides.get("skip_targeted"):
            write_json(targeted, overrides.get("targeted_payload", targeted_repeat_payload()))
        if not overrides.get("skip_validation"):
            write_json(validation, overrides.get("validation_payload", validation_payload()))
        if not overrides.get("skip_health"):
            write_json(health, overrides.get("health_payload", health_payload()))
        return targeted, validation, health

    def test_default_paths_and_guardrails(self):
        self.assertEqual(VERSION, "0.4.15.7")
        self.assertEqual(
            DEFAULT_TARGETED_REPEAT_PATH,
            Path("tests/targeted_repeat_algorithm_bias_near_tie_patch_v0.4.15.6_report.json"),
        )
        self.assertEqual(
            DEFAULT_PATCH_VALIDATION_PATH,
            Path("tests/post_rebuild_near_tie_patch_validation_v0.4.15.6_report.json"),
        )
        self.assertEqual(DEFAULT_PROJECT_HEALTH_PATH, Path("tests/project_health_check_report.json"))
        self.assertEqual(
            DEFAULT_OUTPUT_PATH,
            Path("tests/post_rebuild_near_tie_patch_closeout_v0.4.15.7_report.json"),
        )
        self.assertEqual(
            DEFAULT_SUMMARY_PATH,
            Path("docs/post_rebuild_near_tie_patch_closeout_v0.4.15.7.md"),
        )
        self.assertTrue(GUARDRAILS["saved_reports_only"])
        self.assertEqual(GUARDRAILS["runtime_patch"], "disallowed")
        self.assertEqual(GUARDRAILS["anchor_mutation"], "disallowed")
        self.assertEqual(GUARDRAILS["eval_case_mutation"], "disallowed")

    def test_clean_saved_reports_close_the_patch_loop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targeted, validation, health = self.write_inputs(tmpdir)

            report = build_report(targeted, validation, health)

        self.assertEqual(report["summary"]["status"], "closed_for_next_real_rag_quality_task")
        self.assertEqual(report["summary"]["blockers"], [])
        self.assertTrue(report["summary"]["runtime_patch_closed"])
        self.assertEqual(
            report["summary"]["next_action"],
            "move_to_post_patch_regression_or_broader_rag_quality_work",
        )

    def test_missing_validation_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targeted, validation, health = self.write_inputs(tmpdir, skip_validation=True)

            report = build_report(targeted, validation, health)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("patch_validation_available", report["summary"]["blockers"])

    def test_unstable_final_evidence_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targeted, validation, health = self.write_inputs(
                tmpdir,
                validation_payload=validation_payload(unique_chains=2),
            )

            report = build_report(targeted, validation, health)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("final_evidence_identity_stable", report["summary"]["blockers"])

    def test_project_health_failure_blocks_closeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targeted, validation, health = self.write_inputs(
                tmpdir,
                health_payload=health_payload(status="failed", failed_checks=1),
            )

            report = build_report(targeted, validation, health)

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertIn("project_health_passed", report["summary"]["blockers"])

    def test_markdown_states_closeout_boundary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targeted, validation, health = self.write_inputs(tmpdir)

            markdown = render_markdown(build_report(targeted, validation, health))

        self.assertIn("Near-Tie Patch Closeout", markdown)
        self.assertIn("same-bucket deterministic ordering", markdown)
        self.assertIn("does not run eval", markdown)
        self.assertIn("No hidden seed, anchor, prompt", markdown)

    def test_main_writes_report_and_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targeted, validation, health = self.write_inputs(tmpdir)
            output = Path(tmpdir) / "report.json"
            summary = Path(tmpdir) / "summary.md"

            import sys

            old_argv = sys.argv
            try:
                sys.argv = [
                    "build_post_rebuild_near_tie_patch_closeout.py",
                    "--targeted-repeat",
                    str(targeted),
                    "--patch-validation",
                    str(validation),
                    "--project-health",
                    str(health),
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
