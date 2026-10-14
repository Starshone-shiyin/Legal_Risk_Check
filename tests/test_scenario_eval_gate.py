import unittest

from tools.check_scenario_eval_report import validate_scenario_eval_report


def valid_report() -> dict:
    return {
        "total_scenarios": 10,
        "total_unique_eval_cases": 15,
        "missing_case_ids": {},
        "scenarios_without_eval_case_ids": [],
        "scenarios_all_failed": [],
        "scenario_summaries": [
            {
                "scenario_id": f"scenario_{index}",
                "passed": 1,
                "total": 1,
                "missing_case_ids": [],
                "retrieval_failure_stage_summary": {"PASS": 1},
            }
            for index in range(5)
        ]
        + [
            {
                "scenario_id": f"scenario_extra_{index}",
                "passed": 1,
                "total": 1,
                "missing_case_ids": [],
                "retrieval_failure_stage_summary": {"PASS": 1},
            }
            for index in range(5)
        ],
    }


class ScenarioEvalGateTest(unittest.TestCase):
    def test_valid_report_passes(self):
        self.assertEqual(validate_scenario_eval_report(valid_report()), [])

    def test_missing_case_groups_fail(self):
        report = valid_report()
        report["missing_case_ids"] = {"scenario_a": ["missing_case"]}

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any("missing_case_groups" in error for error in errors))

    def test_scenarios_without_eval_case_ids_fail(self):
        report = valid_report()
        report["scenarios_without_eval_case_ids"] = ["scenario_a"]

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any("scenarios_without_eval_case_ids must be empty" in error for error in errors))

    def test_scenarios_all_failed_fail(self):
        report = valid_report()
        report["scenarios_all_failed"] = ["scenario_a"]

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any("scenarios_all_failed must be empty" in error for error in errors))

    def test_scenario_total_zero_fails(self):
        report = valid_report()
        report["scenario_summaries"][0]["total"] = 0

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any(".total must be > 0" in error for error in errors))

    def test_scenario_passed_zero_fails(self):
        report = valid_report()
        report["scenario_summaries"][0]["passed"] = 0

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any(".passed must be > 0" in error for error in errors))

    def test_min_scenarios_threshold_applies(self):
        report = valid_report()
        report["total_scenarios"] = 9
        report["scenario_summaries"] = report["scenario_summaries"][:9]

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any("total_scenarios must be >= 10" in error for error in errors))

    def test_min_cases_threshold_applies(self):
        report = valid_report()
        report["total_unique_eval_cases"] = 14

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any("total_unique_eval_cases must be >= 15" in error for error in errors))

    def test_missing_key_fields_fail_clearly(self):
        report = valid_report()
        del report["scenario_summaries"][0]["retrieval_failure_stage_summary"]
        del report["scenario_summaries"][1]["passed"]

        errors = validate_scenario_eval_report(report)

        self.assertTrue(any("retrieval_failure_stage_summary" in error for error in errors))
        self.assertTrue(any(".passed must be an integer" in error for error in errors))

    def test_partial_pass_allowed_by_default(self):
        report = valid_report()
        report["scenario_summaries"][0]["passed"] = 1
        report["scenario_summaries"][0]["total"] = 2

        self.assertEqual(validate_scenario_eval_report(report), [])

    def test_partial_pass_can_be_disabled(self):
        report = valid_report()
        report["scenario_summaries"][0]["passed"] = 1
        report["scenario_summaries"][0]["total"] = 2

        errors = validate_scenario_eval_report(report, allow_partial_pass=False)

        self.assertTrue(any("must equal total" in error for error in errors))

    def test_repository_report_passes(self):
        import json
        from pathlib import Path

        report = json.loads(Path("tests/scenario_eval_report.json").read_text(encoding="utf-8"))

        self.assertEqual(validate_scenario_eval_report(report), [])


if __name__ == "__main__":
    unittest.main()
