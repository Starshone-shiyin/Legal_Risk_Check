import unittest

from tools.check_legal_functional_typing_fixtures import (
    build_report,
    evaluate_fixtures,
    validate_fixture_structure,
)


class LegalFunctionalTypingFixturesTest(unittest.TestCase):
    def test_repository_fixtures_pass(self):
        report = build_report()

        self.assertTrue(report["passed"])
        self.assertEqual(report["summary"]["failed_cases"], 0)
        self.assertGreaterEqual(report["summary"]["total_cases"], 8)
        self.assertIn("definition", report["summary"]["expected_type_counts"])
        self.assertIn("operative_rule", report["summary"]["expected_type_counts"])

    def test_structure_validation_rejects_unknown_expected_type(self):
        errors = validate_fixture_structure(
            {
                "version": "test",
                "purpose": "test",
                "cases": [
                    {
                        "id": "bad",
                        "expected_functional_type": "unknown_type",
                        "text": "本法所称测试，是指测试。",
                        "metadata": {},
                    }
                ],
            },
            {"definition"},
        )

        self.assertTrue(any("expected_functional_type is not declared" in error for error in errors))

    def test_structure_validation_rejects_duplicate_case_id(self):
        errors = validate_fixture_structure(
            {
                "version": "test",
                "purpose": "test",
                "cases": [
                    {
                        "id": "dup",
                        "expected_functional_type": "definition",
                        "text": "本法所称测试，是指测试。",
                        "metadata": {},
                    },
                    {
                        "id": "dup",
                        "expected_functional_type": "definition",
                        "text": "本法所称样本，是指样本。",
                        "metadata": {},
                    },
                ],
            },
            {"definition"},
        )

        self.assertTrue(any("duplicates fixture id" in error for error in errors))

    def test_evaluate_fixtures_reports_failure_details(self):
        fixtures = {
            "cases": [
                {
                    "id": "mismatch",
                    "expected_functional_type": "liability",
                    "text": "本法所称测试，是指测试。",
                    "metadata": {},
                }
            ]
        }
        config = {
            "functional_types": [
                {"id": "definition"},
                {"id": "liability"},
            ],
            "operative_support_types": ["liability"],
            "rules": [
                {
                    "functional_type": "definition",
                    "priority": 90,
                    "confidence": "rule_high",
                    "contains": ["本法所称"],
                    "regex": [],
                }
            ],
        }

        results, summary = evaluate_fixtures(fixtures, config)

        self.assertFalse(results[0]["passed"])
        self.assertEqual(results[0]["actual_functional_type"], "definition")
        self.assertEqual(summary["failed_cases"], 1)
        self.assertEqual(summary["failures_by_expected_type"], {"liability": ["mismatch"]})


if __name__ == "__main__":
    unittest.main()
