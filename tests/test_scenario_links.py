import unittest
import json
from pathlib import Path

from tools.check_scenario_links import (
    anchor_scenario_map,
    risk_scenario_map,
    validate_scenario_links,
)


def sample_anchor_config() -> dict:
    return {
        "domains": {
            "市场秩序": {
                "scene_anchors": [
                    {
                        "id": "unfair_competition_trade_secret",
                        "scenario_id": "trade_secret_customer_list_leak",
                        "triggers": ["客户名单"],
                    },
                    {
                        "id": "pipl_data_leak",
                        "scenario_id": "trade_secret_customer_list_leak",
                        "triggers": ["导出"],
                    }
                ]
            }
        }
    }


def sample_risk_config() -> dict:
    return {
        "rules": [
            {
                "scenario_id": "trade_secret_customer_list_leak",
                "question_all": ["客户名单"],
                "risk_types": ["商业秘密侵权"],
            },
            {
                "scenario_id": "trade_secret_customer_list_leak",
                "question_any": ["员工私自", "导出"],
                "risk_types": ["内部人员违规"],
            }
        ]
    }


class ScenarioLinksTest(unittest.TestCase):
    def test_scenario_maps_collect_links(self):
        self.assertEqual(
            anchor_scenario_map(sample_anchor_config()),
            {"trade_secret_customer_list_leak": ["unfair_competition_trade_secret", "pipl_data_leak"]},
        )
        self.assertEqual(
            risk_scenario_map(sample_risk_config()),
            {"trade_secret_customer_list_leak": ["risk_rule_0", "risk_rule_1"]},
        )

    def test_validate_scenario_links_accepts_shared_scenario(self):
        errors = validate_scenario_links(
            sample_anchor_config(),
            sample_risk_config(),
            required_scenario="trade_secret_customer_list_leak",
            required_anchor_rules=["unfair_competition_trade_secret", "pipl_data_leak"],
            required_risk_rules=["risk_rule_0", "risk_rule_1"],
        )

        self.assertEqual(errors, [])

    def test_validate_scenario_links_rejects_missing_required_rule(self):
        errors = validate_scenario_links(
            sample_anchor_config(),
            sample_risk_config(),
            required_scenario="trade_secret_customer_list_leak",
            required_risk_rules=["risk_rule_9"],
        )

        self.assertTrue(any("missing risk rule risk_rule_9" in error for error in errors))

    def test_validate_scenario_links_rejects_missing_risk_side(self):
        errors = validate_scenario_links(sample_anchor_config(), {"rules": []})

        self.assertTrue(any("missing risk supplement rules" in error for error in errors))

    def test_validate_scenario_links_rejects_invalid_name(self):
        anchor_config = sample_anchor_config()
        anchor_config["domains"]["市场秩序"]["scene_anchors"][0]["scenario_id"] = "TradeSecret"
        risk_config = sample_risk_config()
        risk_config["rules"][0]["scenario_id"] = "TradeSecret"

        errors = validate_scenario_links(anchor_config, risk_config)

        self.assertTrue(any("invalid scenario_id" in error for error in errors))

    def test_repository_trade_secret_scenario_is_linked(self):
        anchor_config = json.loads(Path("config/rag_anchor_rules.json").read_text(encoding="utf-8"))
        risk_config = json.loads(Path("config/risk_payload_supplement_rules.json").read_text(encoding="utf-8"))

        errors = validate_scenario_links(
            anchor_config,
            risk_config,
            required_scenario="trade_secret_customer_list_leak",
            required_anchor_rules=[
                "pipl_data_leak",
                "pipl_internal_leak",
                "unfair_competition_trade_secret",
            ],
            required_risk_rules=["risk_rule_0", "risk_rule_4"],
            allowed_missing_risk_scenarios=["pipl_facial_recognition_attendance"],
        )

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
