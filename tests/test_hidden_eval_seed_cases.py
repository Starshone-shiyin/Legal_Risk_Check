import copy
import json
import unittest
from pathlib import Path

from tools.check_hidden_eval_seeds import REQUIRED_CASE_IDS, validate_hidden_eval_seeds


def valid_payload() -> dict:
    return {
        "legal_domains": [
            "personal_information_protection",
            "corporate_governance",
        ],
        "functional_types": [
            "definition",
            "operative_rule",
            "procedural",
        ],
        "issue_levels": [
            "primary",
            "secondary",
            "peripheral",
        ],
        "cases": [
            {
                "case_id": "seed_001_pipl_facial_attendance_complex",
                "scenario_label": "Facial recognition attendance",
                "expected_domains": [
                    "personal_information_protection",
                ],
                "primary_issues": [
                    "biometric_sensitive_info",
                ],
                "secondary_issues": [
                    "access_control",
                ],
                "peripheral_issues": [],
                "expected_statutes": [
                    {
                        "ref": "pipl::article_29",
                        "functional_type": "operative_rule",
                        "supports": [
                            "biometric_sensitive_info",
                        ],
                    }
                ],
                "contaminating_domains": [
                    "corporate_governance",
                ],
                "known_bad_evidence": [
                    {
                        "ref": "company_law::article_57",
                        "reason": "Unrelated corporate governance evidence.",
                    }
                ],
                "notes": "Fixture.",
            }
        ],
    }


class HiddenEvalSeedCasesTest(unittest.TestCase):
    fixture_required_case_ids = {"seed_001_pipl_facial_attendance_complex"}

    def test_valid_fixture_passes_without_required_set(self):
        self.assertEqual(
            validate_hidden_eval_seeds(valid_payload(), required_case_ids=self.fixture_required_case_ids),
            [],
        )

    def test_repository_seed_file_passes(self):
        payload = json.loads(Path("config/hidden_eval_seed_cases.json").read_text(encoding="utf-8"))

        self.assertEqual(validate_hidden_eval_seeds(payload), [])
        self.assertEqual({case["case_id"] for case in payload["cases"]}, REQUIRED_CASE_IDS)

    def test_duplicate_case_id_fails(self):
        payload = valid_payload()
        payload["cases"].append(copy.deepcopy(payload["cases"][0]))

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("duplicate case_id" in error for error in errors))

    def test_missing_primary_issues_fails(self):
        payload = valid_payload()
        payload["cases"][0]["primary_issues"] = []

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("primary_issues must not be empty" in error for error in errors))

    def test_missing_expected_statutes_fails(self):
        payload = valid_payload()
        payload["cases"][0]["expected_statutes"] = []

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("expected_statutes must not be empty" in error for error in errors))

    def test_expected_statute_must_include_operative_rule(self):
        payload = valid_payload()
        payload["cases"][0]["expected_statutes"][0]["functional_type"] = "definition"

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("at least one operative_rule" in error for error in errors))

    def test_unknown_domain_fails(self):
        payload = valid_payload()
        payload["cases"][0]["expected_domains"] = ["unknown_domain"]

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("unknown domain" in error for error in errors))

    def test_contaminating_domain_overlap_fails(self):
        payload = valid_payload()
        payload["cases"][0]["contaminating_domains"] = ["personal_information_protection"]

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("overlaps expected_domains" in error for error in errors))

    def test_unknown_supported_issue_fails(self):
        payload = valid_payload()
        payload["cases"][0]["expected_statutes"][0]["supports"] = ["missing_issue"]

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("unknown issue" in error for error in errors))

    def test_bad_ref_format_fails(self):
        payload = valid_payload()
        payload["cases"][0]["known_bad_evidence"][0]["ref"] = "company_law article 57"

        errors = validate_hidden_eval_seeds(payload, required_case_ids=self.fixture_required_case_ids)

        self.assertTrue(any("must match <source>::<article_or_section>" in error for error in errors))

    def test_required_case_ids_are_enforced(self):
        errors = validate_hidden_eval_seeds(valid_payload())

        self.assertTrue(any("missing required hidden seed case ids" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
