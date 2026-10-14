from __future__ import annotations

import unittest

from src.main import _normalize_ask_result


class AskEvidenceGateTest(unittest.TestCase):
    def test_domain_mismatch_removes_decision_fields(self) -> None:
        normalized = _normalize_ask_result(
            {
                "answer": "该事项存在高风险。[《个人信息保护法》第十七条]",
                "risk_level": "high",
                "risk_types": ["数据处理风险"],
                "recommended_actions": ["完善告知"],
                "evidence_chain": [{
                    "citation": "[《个人信息保护法》第十七条]",
                    "source": "个人信息保护法",
                    "law_name": "个人信息保护法",
                    "content": "处理个人信息应遵循公开透明原则。",
                }],
                "filters": {},
            },
            "进口电子级材料的出口管制与原产地核验缺失。",
            expected_risk_domain="cross_border_supply_chain",
        )

        self.assertIsNone(normalized["risk_level"])
        self.assertEqual(normalized["risk_types"], [])
        self.assertEqual(normalized["recommended_actions"], [])
        self.assertEqual(normalized["evidence_chain"], [])
        self.assertEqual(len(normalized["rejected_evidence"]), 1)
        self.assertIn("暂不输出风险等级", normalized["answer"])

    def test_citation_coverage_gap_removes_decision_fields(self) -> None:
        normalized = _normalize_ask_result(
            {
                "answer": "该事项存在高风险，企业应当立即停止相关安排并完成专项整改。",
                "risk_level": "high",
                "risk_types": ["数据处理风险"],
                "recommended_actions": ["立即停止相关安排"],
                "evidence_chain": [{
                    "citation": "[《个人信息保护法》第十七条]",
                    "source": "个人信息保护法",
                    "law_name": "个人信息保护法",
                }],
                "filters": {},
            },
            "供应商数据处理安排评估。",
        )

        self.assertIsNone(normalized["risk_level"])
        self.assertEqual(normalized["risk_types"], [])
        self.assertEqual(normalized["recommended_actions"], [])
        self.assertTrue(normalized["citation_integrity"]["coverage"]["requires_review"])


if __name__ == "__main__":
    unittest.main()
