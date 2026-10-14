import unittest

from tools.audit_rule_debt import build_report, render_markdown


def sample_anchor_config() -> dict:
    return {
        "domains": {
            "数据合规": {
                "scene_anchors": [
                    {
                        "id": "children_data",
                        "triggers": ["儿童", "监护人同意"],
                        "context_any": ["普通用户协议"],
                        "anchors": [],
                        "risk_types": ["儿童信息保护不力"],
                        "actions": ["制定专门的儿童个人信息处理规则"],
                    },
                    {
                        "id": "trade_secret",
                        "scenario_id": "trade_secret_leak",
                        "triggers": ["客户名单", "商业秘密"],
                        "context_any": ["离职"],
                        "anchors": [],
                    },
                ]
            }
        }
    }


def sample_risk_config() -> dict:
    return {
        "rules": [
            {
                "question_any_groups": [["儿童"], ["普通用户协议", "监护人同意"]],
                "risk_types": ["儿童信息保护不力"],
                "actions": ["制定专门的儿童个人信息处理规则"],
            },
            {
                "scenario_id": "trade_secret_leak",
                "question_all": ["客户名单"],
                "question_any": ["离职", "商业秘密"],
                "risk_types": ["商业秘密侵权"],
            },
        ]
    }


def sample_stability_report() -> dict:
    return {
        "runs": [
            {
                "run": 1,
                "reports": [
                    {
                        "id": "risk_children_data_001",
                        "question": "某儿童游戏APP仅用普通用户协议征得监护人同意，是否合规？",
                        "contribution_labels": ["ANCHOR_PASS", "RISK_SUPPLEMENT_PASS"],
                    }
                ],
            }
        ]
    }


class RuleDebtAuditTest(unittest.TestCase):
    def test_build_report_finds_duplicate_and_cross_config_triggers(self):
        report = build_report(sample_anchor_config(), sample_risk_config(), sample_stability_report())

        duplicate_terms = {item["term"] for item in report["duplicate_triggers"]}
        overlap_terms = {item["term"] for item in report["cross_config_trigger_overlaps"]}

        self.assertIn("儿童", duplicate_terms)
        self.assertIn("监护人同意", overlap_terms)

    def test_build_report_finds_suspicious_same_scene_pairs(self):
        report = build_report(sample_anchor_config(), sample_risk_config(), sample_stability_report())

        pairs = report["suspicious_same_scene_pairs"]

        self.assertTrue(any(pair["anchor_id"] == "children_data" for pair in pairs))

    def test_build_report_tracks_missing_scenario_ids(self):
        report = build_report(sample_anchor_config(), sample_risk_config(), sample_stability_report())

        self.assertEqual(report["summary"]["anchor_rules_without_shared_scenario_id"], 1)
        self.assertEqual(report["summary"]["risk_rules_without_scenario_id"], 1)

    def test_build_report_maps_high_dependency_cases_to_rules(self):
        report = build_report(sample_anchor_config(), sample_risk_config(), sample_stability_report())
        mappings = report["high_dependency_case_mappings"]

        self.assertEqual(mappings[0]["id"], "risk_children_data_001")
        self.assertTrue(mappings[0]["matched_anchor_rules"])
        self.assertTrue(mappings[0]["matched_risk_rules"])

    def test_render_markdown_contains_audit_sections(self):
        report = build_report(sample_anchor_config(), sample_risk_config(), sample_stability_report())
        markdown = render_markdown(report)

        self.assertIn("重复 Trigger", markdown)
        self.assertIn("疑似同场景多处维护", markdown)
        self.assertIn("缺失 Scenario ID", markdown)
        self.assertIn("高规则依赖 Case 映射", markdown)


if __name__ == "__main__":
    unittest.main()
