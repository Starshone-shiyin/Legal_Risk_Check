import unittest

from tools.check_scenario_registry import (
    anchor_scenario_links,
    coverage_audit,
    load_json,
    risk_scenario_links,
    validate_scenario_registry,
)


def sample_anchor_config() -> dict:
    return {
        "domains": {
            "数据合规": {
                "scene_anchors": [
                    {"id": "pipl_children", "scenario_id": "pipl_children_consent"},
                    {"id": "pipl_data_export"},
                ]
            }
        }
    }


def sample_risk_config() -> dict:
    return {
        "rules": [
            {"scenario_id": "pipl_children_consent", "risk_types": ["儿童信息保护不力"]},
            {"risk_types": ["数据出境合规风险"]},
        ]
    }


def sample_eval_config() -> dict:
    return {"cases": [{"id": "risk_children_data_001"}]}


def sample_registry() -> dict:
    return {
        "scenarios": [
            {
                "scenario_id": "pipl_children_consent",
                "domain": "数据合规",
                "description": "儿童个人信息监护人同意场景",
                "risk_level": "high",
                "core_articles": [{"source": "中华人民共和国个人信息保护法", "article_no": 31}],
                "risk_types": ["儿童信息保护不力"],
                "required_actions": ["取得监护人同意"],
                "legal_terms": ["儿童个人信息"],
                "linked_anchor_rule_ids": ["pipl_children"],
                "linked_risk_rule_ids": ["risk_rule_0"],
                "eval_case_ids": ["risk_children_data_001"],
            }
        ]
    }


class ScenarioRegistryTest(unittest.TestCase):
    def test_validate_accepts_linked_registry(self):
        errors, audit = validate_scenario_registry(
            sample_registry(),
            sample_anchor_config(),
            sample_risk_config(),
            sample_eval_config(),
        )

        self.assertEqual(errors, [])
        self.assertEqual(audit["scenarios_missing_anchor_link"], [])
        self.assertEqual(audit["scenarios_missing_risk_supplement_link"], [])
        self.assertEqual(audit["scenarios_missing_eval_case"], [])

    def test_validate_rejects_duplicate_scenario_id(self):
        registry = sample_registry()
        registry["scenarios"].append(dict(registry["scenarios"][0]))

        errors, _audit = validate_scenario_registry(
            registry,
            sample_anchor_config(),
            sample_risk_config(),
            sample_eval_config(),
        )

        self.assertTrue(any("duplicate scenario_id" in error for error in errors))

    def test_validate_rejects_unknown_links_and_empty_core_fields(self):
        registry = sample_registry()
        scenario = registry["scenarios"][0]
        scenario["domain"] = "不存在的法域"
        scenario["risk_level"] = "critical"
        scenario["core_articles"] = []
        scenario["linked_anchor_rule_ids"] = ["missing_anchor"]
        scenario["linked_risk_rule_ids"] = ["risk_rule_99"]
        scenario["eval_case_ids"] = ["missing_case"]

        errors, _audit = validate_scenario_registry(
            registry,
            sample_anchor_config(),
            sample_risk_config(),
            sample_eval_config(),
        )

        self.assertTrue(any("domain" in error for error in errors))
        self.assertTrue(any("risk_level" in error for error in errors))
        self.assertTrue(any("core_articles" in error for error in errors))
        self.assertTrue(any("missing_anchor" in error for error in errors))
        self.assertTrue(any("risk_rule_99" in error for error in errors))
        self.assertTrue(any("missing_case" in error for error in errors))

    def test_validate_requires_reverse_links_for_existing_scenario_ids(self):
        registry = sample_registry()
        registry["scenarios"][0]["linked_anchor_rule_ids"] = []

        errors, _audit = validate_scenario_registry(
            registry,
            sample_anchor_config(),
            sample_risk_config(),
            sample_eval_config(),
        )

        self.assertTrue(any("must be reverse-linked" in error for error in errors))

    def test_coverage_audit_reports_missing_links_and_unregistered_rule_scenario(self):
        audit = coverage_audit(
            [
                {
                    "scenario_id": "pipl_children_consent",
                    "linked_anchor_rule_ids": [],
                    "linked_risk_rule_ids": [],
                    "eval_case_ids": [],
                }
            ],
            {"unregistered_scenario": ["pipl_data_export"]},
            {},
        )

        self.assertEqual(audit["scenarios_missing_anchor_link"], ["pipl_children_consent"])
        self.assertEqual(audit["scenarios_missing_risk_supplement_link"], ["pipl_children_consent"])
        self.assertEqual(audit["scenarios_missing_eval_case"], ["pipl_children_consent"])
        self.assertEqual(audit["rule_scenario_ids_missing_registry"], ["unregistered_scenario"])

    def test_repository_registry_passes(self):
        registry = load_json("config/scenario_registry.json")
        anchor_config = load_json("config/rag_anchor_rules.json")
        risk_config = load_json("config/risk_payload_supplement_rules.json")
        eval_config = load_json("tests/rag_eval_cases.json")

        errors, audit = validate_scenario_registry(registry, anchor_config, risk_config, eval_config)

        self.assertEqual(errors, [])
        self.assertEqual(audit["scenarios_missing_anchor_link"], [])
        self.assertEqual(audit["scenarios_missing_risk_supplement_link"], ["pipl_facial_recognition_attendance"])
        self.assertEqual(audit["scenarios_missing_eval_case"], [])
        self.assertEqual(audit["rule_scenario_ids_missing_registry"], [])

    def test_repository_reverse_links_include_metadata_trial(self):
        registry = load_json("config/scenario_registry.json")
        anchor_config = load_json("config/rag_anchor_rules.json")
        risk_config = load_json("config/risk_payload_supplement_rules.json")
        scenario = {
            item["scenario_id"]: item
            for item in registry["scenarios"]
        }["trade_secret_customer_list_leak"]

        self.assertEqual(
            set(anchor_scenario_links(anchor_config)["trade_secret_customer_list_leak"]),
            set(scenario["linked_anchor_rule_ids"]),
        )
        self.assertEqual(
            set(risk_scenario_links(risk_config)["trade_secret_customer_list_leak"]),
            set(scenario["linked_risk_rule_ids"]),
        )


if __name__ == "__main__":
    unittest.main()
