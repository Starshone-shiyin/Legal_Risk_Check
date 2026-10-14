import unittest

from src.risk.analyzer import build_risk_analysis


class RiskAnalyzerTest(unittest.TestCase):
    def test_structured_high_taxonomy_risk_type_upgrades_medium_rag_level(self):
        result = build_risk_analysis(
            "\u5177\u6709\u5e02\u573a\u652f\u914d\u5730\u4f4d\u7684\u5e73\u53f0\u8981\u6c42\u5546\u5bb6\u4e8c\u9009\u4e00",
            {
                "answer": "\u8be5\u884c\u4e3a\u5c5e\u4e8e\u6ee5\u7528\u5e02\u573a\u652f\u914d\u5730\u4f4d\u3002",
                "risk_level": "medium",
                "risk_types": ["\u6ee5\u7528\u5e02\u573a\u652f\u914d\u5730\u4f4d\u98ce\u9669"],
                "recommended_actions": ["\u505c\u6b62\u6392\u4ed6\u6027\u8981\u6c42"],
                "evidence_chain": [],
            },
        )

        self.assertEqual(result["risk_level"], "high")
        self.assertEqual(result["risk_categories"][0]["id"], "abuse_of_dominance")


if __name__ == "__main__":
    unittest.main()
