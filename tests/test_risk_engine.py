import unittest

from src.risk.analyzer import build_legal_basis, build_risk_analysis, calculate_overall_confidence
from src.risk.taxonomy import classify_risk_categories, infer_taxonomy_risk_level


class RiskEngineTest(unittest.TestCase):
    def test_taxonomy_detects_multiple_categories(self):
        categories = classify_risk_categories(
            "某AI医疗公司使用患者病历训练模型，并同步至境外服务器。",
            ["敏感个人信息处理风险", "数据出境不合规"],
        )
        category_ids = {item["id"] for item in categories}

        self.assertIn("sensitive_personal_info", category_ids)
        self.assertIn("data_export", category_ids)
        self.assertEqual(infer_taxonomy_risk_level(categories), "high")

    def test_build_risk_analysis_uses_rag_result_contract(self):
        rag_result = {
            "answer": "该行为涉及敏感个人信息和数据出境风险。 [《个人信息保护法》第二十八条]",
            "confidence_score": 0.9,
            "answer_confidence": 0.9,
            "retrieval_confidence": 0.86,
            "needs_human_review": False,
            "missing_evidence": [],
            "risk_level": "high",
            "risk_types": ["敏感个人信息处理风险"],
            "recommended_actions": ["取得单独同意", "开展数据出境安全评估"],
            "risk_type_evidence": [{"text": "敏感个人信息处理风险", "citations": ["[《个人信息保护法》第二十八条]"]}],
            "recommended_action_evidence": [{"text": "取得单独同意", "citations": ["[《个人信息保护法》第二十九条]"]}],
            "filters": {"category": "数据合规"},
            "evidence_chain": [
                {
                    "citation": "[《个人信息保护法》第二十八条]",
                    "source": "中华人民共和国个人信息保护法",
                    "law_name": "中华人民共和国个人信息保护法",
                    "document_type": "法律法规",
                    "law_level": "法律",
                    "article_no": 28,
                    "section_no": "",
                    "rerank_score": 2.0,
                }
            ],
        }

        result = build_risk_analysis("使用患者病历训练模型并传输至境外", rag_result)

        self.assertEqual(result["risk_level"], "high")
        self.assertIn("敏感个人信息处理风险", result["risk_types"])
        self.assertIn("数据出境合规风险", result["risk_types"])
        self.assertEqual(result["confidence"]["overall"], 0.86)
        self.assertEqual(result["legal_basis"][0]["article_no"], 28)

    def test_low_risk_result_is_not_escalated_by_keywords(self):
        rag_result = {
            "answer": "已明确告知并取得单独同意，整体合规。",
            "confidence_score": 0.9,
            "answer_confidence": 0.9,
            "retrieval_confidence": 0.86,
            "needs_human_review": False,
            "missing_evidence": [],
            "risk_level": "low",
            "risk_types": [],
            "recommended_actions": ["保持现有合规措施"],
            "filters": {},
            "evidence_chain": [],
        }

        result = build_risk_analysis("APP明确告知用户收集定位信息并取得单独同意", rag_result)

        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["risk_categories"], [])

    def test_build_legal_basis_deduplicates_citations(self):
        basis = build_legal_basis([
            {"citation": "[A]", "source": "法A", "article_no": 1},
            {"citation": "[A]", "source": "法A", "article_no": 1},
            {"citation": "[B]", "source": "法B", "article_no": 2},
        ])

        self.assertEqual([item["citation"] for item in basis], ["[A]", "[B]"])

    def test_overall_confidence_uses_lower_bound(self):
        self.assertEqual(calculate_overall_confidence(0.9, 0.7), 0.7)
        self.assertEqual(calculate_overall_confidence(None, 0.7), 0.7)
        self.assertEqual(calculate_overall_confidence(0.8, None), 0.8)

    def test_unsupported_answer_citation_requests_review(self):
        rag_result = {
            "answer": "依据[《个人信息保护法》第九十九条]，该行为存在风险。",
            "confidence_score": 0.9,
            "answer_confidence": 0.9,
            "retrieval_confidence": 0.9,
            "needs_human_review": False,
            "missing_evidence": [],
            "risk_level": "high",
            "risk_types": ["告知同意不合规"],
            "recommended_actions": ["补充告知"],
            "filters": {},
            "evidence_chain": [
                {"citation": "[《个人信息保护法》第十七条]", "source": "个人信息保护法", "article_no": 17}
            ],
        }

        result = build_risk_analysis("测试场景", rag_result)

        self.assertFalse(result["citation_integrity"]["passed"])
        self.assertTrue(result["needs_human_review"])
        self.assertIn("[《个人信息保护法》第九十九条]", result["citation_integrity"]["unsupported"])


if __name__ == "__main__":
    unittest.main()
