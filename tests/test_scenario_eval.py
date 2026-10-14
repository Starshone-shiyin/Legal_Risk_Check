import unittest

from tools.run_scenario_eval import (
    case_map,
    missing_case_ids,
    render_markdown,
    scenario_eval_case_ids,
    stage_summary,
    summarize_scenarios,
)


def sample_scenarios() -> list[dict]:
    return [
        {
            "scenario_id": "trade_secret_customer_list_leak",
            "domain": "市场秩序",
            "risk_level": "high",
            "eval_case_ids": ["case_a", "case_b"],
        },
        {
            "scenario_id": "pipl_children_consent",
            "domain": "数据合规",
            "risk_level": "high",
            "eval_case_ids": [],
        },
        {
            "scenario_id": "missing_case_scenario",
            "domain": "数据合规",
            "risk_level": "medium",
            "eval_case_ids": ["missing_case"],
        },
    ]


def sample_report(case_id: str, passed: bool, stage: str, labels: list[str]) -> dict:
    return {
        "id": case_id,
        "passed": passed,
        "retrieval_diagnostics": {"failure_stage": stage},
        "contribution_labels": labels,
    }


class ScenarioEvalTest(unittest.TestCase):
    def test_scenario_eval_case_ids_are_unique_and_ordered(self):
        scenarios = sample_scenarios()
        scenarios.append(
            {
                "scenario_id": "duplicate_case_scenario",
                "eval_case_ids": ["case_b", "case_c"],
            }
        )

        self.assertEqual(scenario_eval_case_ids(scenarios), ["case_a", "case_b", "missing_case", "case_c"])

    def test_missing_case_ids_are_reported_by_scenario(self):
        cases_by_id = {"case_a": {"id": "case_a"}, "case_b": {"id": "case_b"}}

        self.assertEqual(
            missing_case_ids(sample_scenarios(), cases_by_id),
            {"missing_case_scenario": ["missing_case"]},
        )

    def test_case_map_reads_case_ids(self):
        mapped = case_map([{"id": "case_a"}, {"id": "case_b"}, {"question": "no id"}])

        self.assertEqual(set(mapped), {"case_a", "case_b"})

    def test_stage_summary_counts_retrieval_failure_stages(self):
        reports = [
            sample_report("case_a", True, "PASS", ["ANCHOR_PASS"]),
            sample_report("case_b", False, "RERANK_MISS", []),
        ]

        self.assertEqual(stage_summary(reports), {"PASS": 1, "RERANK_MISS": 1})

    def test_summarize_scenarios_counts_pass_total_and_labels(self):
        reports_by_case_id = {
            "case_a": sample_report("case_a", True, "PASS", ["ANCHOR_PASS"]),
            "case_b": sample_report("case_b", True, "PASS", ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"]),
        }

        summaries = summarize_scenarios(sample_scenarios(), reports_by_case_id)
        summary = summaries[0]

        self.assertEqual(summary["scenario_id"], "trade_secret_customer_list_leak")
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["retrieval_failure_stage_summary"], {"PASS": 2})
        self.assertEqual(summary["contribution_summary"]["label_counts"]["ANCHOR_PASS"], 2)
        self.assertEqual(summary["contribution_summary"]["label_counts"]["RISK_SUPPLEMENT_PASS"], 1)

    def test_summarize_scenarios_marks_all_failed(self):
        reports_by_case_id = {
            "case_a": sample_report("case_a", False, "RERANK_MISS", []),
            "case_b": sample_report("case_b", False, "RERANK_MISS", []),
        }

        summary = summarize_scenarios(sample_scenarios(), reports_by_case_id)[0]

        self.assertTrue(summary["all_failed"])
        self.assertEqual(summary["passed"], 0)
        self.assertEqual(summary["total"], 2)

    def test_summarize_scenarios_preserves_missing_case_ids(self):
        summaries = summarize_scenarios(
            sample_scenarios(),
            {},
            {"missing_case_scenario": ["missing_case"]},
        )

        self.assertEqual(summaries[2]["missing_case_ids"], ["missing_case"])

    def test_render_markdown_includes_scenario_rows(self):
        report = {
            "version": "0.4.6.2",
            "registry_version": "0.4.6.0",
            "total_scenarios": 1,
            "total_unique_eval_cases": 2,
            "missing_case_ids": {},
            "scenarios_without_eval_case_ids": [],
            "scenarios_all_failed": [],
            "scenario_summaries": [
                {
                    "scenario_id": "trade_secret_customer_list_leak",
                    "domain": "市场秩序",
                    "passed": 2,
                    "total": 2,
                    "retrieval_failure_stage_summary": {"PASS": 2},
                    "contribution_summary": {"label_counts": {"ANCHOR_PASS": 2}},
                }
            ],
        }

        markdown = render_markdown(report)

        self.assertIn("trade_secret_customer_list_leak", markdown)
        self.assertIn("ANCHOR_PASS:2", markdown)


if __name__ == "__main__":
    unittest.main()
