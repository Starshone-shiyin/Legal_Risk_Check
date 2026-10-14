import unittest
from pathlib import Path

from tools.check_legal_functional_type_config import DEFAULT_REPORT_PATH, validate_functional_type_config


def minimal_valid_config():
    functional_types = [
        {"id": "definition", "label": "Definition", "description": "Definition clauses."},
        {"id": "principle", "label": "Principle", "description": "Principle clauses."},
        {"id": "operative_rule", "label": "Obligation", "description": "Obligation clauses."},
        {"id": "procedural", "label": "Procedure", "description": "Procedure clauses."},
        {"id": "liability", "label": "Liability", "description": "Liability clauses."},
        {"id": "rights_remedy", "label": "Rights", "description": "Rights and remedies."},
        {"id": "scope", "label": "Scope", "description": "Scope clauses."},
        {"id": "technical_standard", "label": "Standard", "description": "Technical standard."},
        {"id": "unrelated_or_contextual", "label": "Context", "description": "Context."},
        {"id": "unclassified", "label": "Unknown", "description": "Fallback."},
    ]
    return {
        "version": "test",
        "purpose": "test config",
        "functional_types": functional_types,
        "operative_support_types": [
            "operative_rule",
            "procedural",
            "liability",
            "rights_remedy",
            "technical_standard",
        ],
        "rules": [
            {
                "functional_type": "definition",
                "priority": 90,
                "confidence": "rule_high",
                "contains": ["本法所称"],
                "regex": [],
            },
            {
                "functional_type": "principle",
                "priority": 80,
                "confidence": "rule_low",
                "contains": ["原则"],
                "regex": [],
            },
            {
                "functional_type": "operative_rule",
                "priority": 70,
                "confidence": "rule_medium",
                "contains": ["应当"],
                "regex": [],
            },
            {
                "functional_type": "procedural",
                "priority": 60,
                "confidence": "rule_medium",
                "contains": ["申报"],
                "regex": [],
            },
            {
                "functional_type": "liability",
                "priority": 100,
                "confidence": "rule_high",
                "contains": ["罚款"],
                "regex": ["责令.{0,10}改正"],
            },
            {
                "functional_type": "rights_remedy",
                "priority": 50,
                "confidence": "rule_medium",
                "contains": ["有权"],
                "regex": [],
            },
            {
                "functional_type": "scope",
                "priority": 40,
                "confidence": "rule_medium",
                "contains": ["适用于"],
                "regex": [],
            },
        ],
    }


class LegalFunctionalTypeConfigTest(unittest.TestCase):
    def test_default_report_path_remains_legacy_tests_report(self):
        self.assertEqual(DEFAULT_REPORT_PATH, Path("tests/legal_functional_type_config_report.json"))

    def test_valid_config_has_no_errors(self):
        errors, warnings, summary = validate_functional_type_config(minimal_valid_config())

        self.assertEqual(errors, [])
        self.assertEqual(summary["functional_type_count"], 10)
        self.assertEqual(summary["regex_count"], 1)
        self.assertIn("definition", summary["rule_type_counts"])

    def test_unknown_rule_type_fails(self):
        config = minimal_valid_config()
        config["rules"][0]["functional_type"] = "not_declared"

        errors, _, _ = validate_functional_type_config(config)

        self.assertTrue(any("is not declared" in error for error in errors))

    def test_duplicate_functional_type_id_fails(self):
        config = minimal_valid_config()
        config["functional_types"].append(
            {"id": "definition", "label": "Duplicate", "description": "Duplicate."}
        )

        errors, _, _ = validate_functional_type_config(config)

        self.assertIn("duplicate functional type id: definition", errors)

    def test_invalid_regex_fails(self):
        config = minimal_valid_config()
        config["rules"][0]["regex"] = ["["]

        errors, _, _ = validate_functional_type_config(config)

        self.assertTrue(any("not a valid regex" in error for error in errors))

    def test_unknown_operative_support_type_fails(self):
        config = minimal_valid_config()
        config["operative_support_types"].append("unknown_support")

        errors, _, _ = validate_functional_type_config(config)

        self.assertIn("operative support type is not declared: unknown_support", errors)

    def test_repository_config_passes_gate(self):
        from tools.check_legal_functional_type_config import build_report

        report = build_report()

        self.assertTrue(report["passed"])
        self.assertEqual(report["errors"], [])
        self.assertGreaterEqual(report["summary"]["rule_count"], 1)


if __name__ == "__main__":
    unittest.main()
