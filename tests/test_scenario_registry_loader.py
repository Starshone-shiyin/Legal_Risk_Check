import unittest
from unittest.mock import patch

import src.rag.scenario_registry as scenario_registry_module
from src.rag.scenario_registry import (
    ScenarioRegistryError,
    clear_scenario_registry_cache,
    get_core_articles_for_scenario,
    get_required_actions_for_scenario,
    get_scenario_by_id,
    get_scenarios_by_anchor_rule,
    get_scenarios_by_risk_rule,
    list_scenarios,
    load_scenario_registry,
)


class ScenarioRegistryLoaderTest(unittest.TestCase):
    def tearDown(self):
        clear_scenario_registry_cache()

    def test_loads_current_ten_scenarios(self):
        registry = load_scenario_registry()

        self.assertEqual(registry["version"], "0.4.6.4")
        self.assertEqual(len(registry["scenarios"]), 10)

    def test_get_scenario_by_id_finds_trade_secret_scenario(self):
        scenario = get_scenario_by_id("trade_secret_customer_list_leak")

        self.assertIsNotNone(scenario)
        self.assertEqual(scenario["domain"], "市场秩序")
        self.assertIn("unfair_competition_trade_secret", scenario["linked_anchor_rule_ids"])

    def test_list_scenarios_filters_by_domain(self):
        scenarios = list_scenarios(domain="数据合规")
        ids = {scenario["scenario_id"] for scenario in scenarios}

        self.assertEqual(len(scenarios), 6)
        self.assertIn("pipl_children_consent", ids)
        self.assertIn("pipl_automated_decision_bias", ids)
        self.assertIn("pipl_cross_border_sensitive_medical", ids)
        self.assertIn("pipl_facial_recognition_attendance", ids)
        self.assertIn("pipl_data_export_security_assessment", ids)
        self.assertIn("pipl_third_party_sharing_without_consent", ids)

    def test_get_scenarios_by_anchor_rule(self):
        scenarios = get_scenarios_by_anchor_rule("pipl_children")

        self.assertEqual([scenario["scenario_id"] for scenario in scenarios], ["pipl_children_consent"])

    def test_get_scenarios_by_risk_rule(self):
        scenarios = get_scenarios_by_risk_rule("risk_rule_6")

        self.assertEqual([scenario["scenario_id"] for scenario in scenarios], ["pipl_automated_decision_bias"])

    def test_unknown_scenario_helpers_return_empty_results(self):
        self.assertIsNone(get_scenario_by_id("missing_scenario"))
        self.assertEqual(get_core_articles_for_scenario("missing_scenario"), [])
        self.assertEqual(get_required_actions_for_scenario("missing_scenario"), [])

    def test_article_and_action_helpers_return_expected_lists(self):
        articles = get_core_articles_for_scenario("vat_false_invoice_deduction")
        actions = get_required_actions_for_scenario("vat_false_invoice_deduction")

        self.assertTrue(any(article["article_no"] == 34 for article in articles))
        self.assertIn("停止违规抵扣", actions)

    def test_returned_objects_are_defensive_copies(self):
        scenario = get_scenario_by_id("trade_secret_customer_list_leak")
        scenario["linked_anchor_rule_ids"].append("polluted_anchor")

        fresh = get_scenario_by_id("trade_secret_customer_list_leak")

        self.assertNotIn("polluted_anchor", fresh["linked_anchor_rule_ids"])

    def test_loader_raises_clear_error_for_invalid_registry(self):
        registry = load_scenario_registry()
        registry["scenarios"][0]["domain"] = "不存在的法域"
        anchor_config = scenario_registry_module.load_json("config/rag_anchor_rules.json")
        risk_config = scenario_registry_module.load_json("config/risk_payload_supplement_rules.json")
        eval_config = scenario_registry_module.load_json("tests/rag_eval_cases.json")

        def fake_load_json(path):
            path_text = str(path)
            if path_text.endswith("scenario_registry.json"):
                return registry
            if path_text.endswith("rag_anchor_rules.json"):
                return anchor_config
            if path_text.endswith("risk_payload_supplement_rules.json"):
                return risk_config
            if path_text.endswith("rag_eval_cases.json"):
                return eval_config
            raise AssertionError(f"unexpected path: {path_text}")

        clear_scenario_registry_cache()
        with patch.object(scenario_registry_module, "load_json", side_effect=fake_load_json):
            with self.assertRaisesRegex(ScenarioRegistryError, "validation failed"):
                load_scenario_registry()


if __name__ == "__main__":
    unittest.main()
