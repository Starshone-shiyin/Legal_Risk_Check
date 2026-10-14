import unittest

from tools.check_rag_stability_report import validate_report
from tools.summarize_rag_stability import render_markdown, rule_heavy_cases


def sample_report() -> dict:
    return {
        "experiment_note": "two experiment objects",
        "experiment_comparison": [
            {
                "experiment_id": "v0.4.5.13-pre-patch-repeat",
                "relationship_to_current_runs": "historical baseline only",
                "code_state": "before patch",
                "pass_counts": [58, 59, 60],
                "total_counts": [60, 60, 60],
                "conclusion": "baseline was unstable",
            },
            {
                "experiment_id": "v0.4.5.14-post-patch-repeat",
                "relationship_to_current_runs": "complete run represented by top-level runs",
                "code_state": "after patch",
                "pass_counts": [60, 60, 60],
                "total_counts": [60, 60, 60],
                "dense_fallback_pass_counts": [0, 0, 0],
                "conclusion": "patch verified",
            },
        ],
        "repeat": 3,
        "stability_summary": {
            "all_runs_full_pass": True,
            "pass_counts": [60, 60, 60],
            "total_counts": [60, 60, 60],
            "unstable_cases": [],
            "label_variation_cases": [
                {"id": "case_b", "contribution_labels": [["ANCHOR_PASS"], ["PURE_LLM_PASS"], ["ANCHOR_PASS"]]}
            ],
        },
        "runs": [
            {
                "run": 1,
                "total": 60,
                "passed": 60,
                "failed": 0,
                "contribution_summary": {
                    "label_counts": {
                        "ANCHOR_PASS": 1,
                        "RISK_SUPPLEMENT_PASS": 1,
                    },
                    "dense_fallback_passed": 0,
                },
                "reports": [
                    {
                        "id": "case_a",
                        "category": "market",
                        "question": "question | with pipe",
                        "contribution_labels": ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"],
                    }
                ],
            },
            {
                "run": 2,
                "total": 60,
                "passed": 60,
                "failed": 0,
                "contribution_summary": {"label_counts": {}, "dense_fallback_passed": 0},
                "reports": [],
            },
            {
                "run": 3,
                "total": 60,
                "passed": 60,
                "failed": 0,
                "contribution_summary": {"label_counts": {}, "dense_fallback_passed": 0},
                "reports": [],
            },
        ],
    }


class RagStabilityToolsTest(unittest.TestCase):
    def test_render_markdown_keeps_two_experiment_boundary(self):
        markdown = render_markdown(sample_report())

        self.assertIn("v0.4.5.13-pre-patch-repeat", markdown)
        self.assertIn("v0.4.5.14-post-patch-repeat", markdown)
        self.assertIn("规则依赖较高 Case", markdown)
        self.assertIn("case_a", markdown)
        self.assertIn("question \\| with pipe", markdown)

    def test_rule_heavy_cases_requires_anchor_and_risk_labels(self):
        cases = rule_heavy_cases(sample_report()["runs"])

        self.assertEqual([case["id"] for case in cases], ["case_a"])

    def test_gate_accepts_clean_report(self):
        self.assertEqual(validate_report(sample_report()), [])

    def test_gate_rejects_unstable_cases(self):
        report = sample_report()
        report["stability_summary"]["unstable_cases"] = [{"id": "case_x"}]

        errors = validate_report(report)

        self.assertTrue(any("unstable_cases" in error for error in errors))

    def test_gate_rejects_dense_fallback(self):
        report = sample_report()
        report["runs"][0]["contribution_summary"]["dense_fallback_passed"] = 1

        errors = validate_report(report)

        self.assertTrue(any("DENSE_FALLBACK_PASS" in error for error in errors))

    def test_gate_rejects_missing_experiment_boundary(self):
        report = sample_report()
        report["experiment_comparison"] = report["experiment_comparison"][1:]

        errors = validate_report(report)

        self.assertTrue(any("v0.4.5.13-pre-patch-repeat" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
