import unittest

from src.risk.report import (
    build_report_citation_integrity,
    build_risk_report,
    export_risk_report,
    render_risk_report_markdown,
)


class RiskReportTest(unittest.TestCase):
    def test_build_high_risk_report(self):
        analysis = {
            "scenario": "某APP未告知即收集精准定位用于广告推荐",
            "summary": "该行为涉及敏感个人信息处理风险。 [《个人信息保护法》第二十八条] [《个人信息保护法》第二十九条]",
            "risk_level": "high",
            "risk_types": ["敏感个人信息处理风险", "告知同意不合规"],
            "risk_categories": [
                {
                    "id": "sensitive_personal_info",
                    "name": "敏感个人信息处理风险",
                    "default_level": "high",
                    "matched_keywords": ["精准定位", "敏感个人信息"],
                }
            ],
            "legal_basis": [
                {
                    "citation": "[《个人信息保护法》第二十八条]",
                    "source": "中华人民共和国个人信息保护法",
                    "article_no": 28,
                },
                {
                    "citation": "[《个人信息保护法》第二十九条]",
                    "source": "中华人民共和国个人信息保护法",
                    "article_no": 29,
                },
            ],
            "recommended_actions": ["补充告知并取得单独同意", "停止非必要收集"],
            "confidence": {"answer": 0.92, "retrieval": 0.98, "overall": 0.92},
            "needs_human_review": False,
            "missing_evidence": [],
            "risk_type_evidence": [
                {"text": "敏感个人信息处理风险", "citations": ["[《个人信息保护法》第二十八条]"]}
            ],
            "recommended_action_evidence": [
                {"text": "补充告知并取得单独同意", "citations": ["[《个人信息保护法》第二十九条]"]}
            ],
            "evidence_chain": [
                {"citation": "[《个人信息保护法》第二十八条]"},
                {"citation": "[《个人信息保护法》第二十九条]"},
            ],
        }

        report = build_risk_report(analysis)

        self.assertEqual(report["risk_level"], "high")
        self.assertIn("企业合规风险分析报告", report["title"])
        self.assertTrue(report["risk_findings"])
        self.assertEqual(report["risk_findings"][0]["legal_basis"][0]["article_no"], 28)
        self.assertEqual(report["action_plan"][0]["priority"], "P0")
        self.assertFalse(report["human_review_required"])

    def test_low_risk_report_has_single_clear_finding(self):
        analysis = {
            "scenario": "APP已告知并取得单独同意",
            "summary": "整体合规，建议保持现有措施。",
            "risk_level": "low",
            "risk_types": [],
            "risk_categories": [],
            "legal_basis": [{"citation": "[《个人信息保护法》第十三条]", "article_no": 13}],
            "recommended_actions": ["保持现有合规措施"],
            "confidence": {"answer": 0.95, "retrieval": 0.98, "overall": 0.95},
            "needs_human_review": False,
            "missing_evidence": [],
            "evidence_chain": [],
        }

        report = build_risk_report(analysis)

        self.assertEqual(report["risk_level"], "low")
        self.assertEqual(report["risk_findings"][0]["risk_type"], "未识别出明确重大风险")
        self.assertEqual(report["action_plan"][0]["priority"], "P2")

    def test_review_reasons_include_low_confidence(self):
        analysis = {
            "scenario": "证据不足的高风险场景",
            "summary": "需要复核。",
            "risk_level": "high",
            "risk_types": ["数据出境合规风险"],
            "risk_categories": [],
            "legal_basis": [],
            "recommended_actions": [],
            "confidence": {"answer": 0.6, "retrieval": 0.65, "overall": 0.6},
            "needs_human_review": True,
            "missing_evidence": ["有效证据数量少于预期"],
            "evidence_chain": [],
        }

        report = build_risk_report(analysis)

        self.assertTrue(report["human_review_required"])
        self.assertIn("有效证据数量少于预期", report["review_reasons"])
        self.assertIn("整体置信度低于 0.7", report["review_reasons"])

    def test_render_markdown_includes_report_sections(self):
        analysis = {
            "scenario": "APP未告知收集定位信息",
            "summary": "存在告知同意风险。",
            "risk_level": "high",
            "risk_types": ["告知同意不合规"],
            "risk_categories": [],
            "legal_basis": [{"citation": "[《个人信息保护法》第十七条]", "article_no": 17}],
            "recommended_actions": ["补充告知并取得同意"],
            "confidence": {"answer": 0.9, "retrieval": 0.95, "overall": 0.9},
            "needs_human_review": False,
            "missing_evidence": [],
            "evidence_chain": [{"citation": "[《个人信息保护法》第十七条]", "similarity_score": 0.95}],
        }
        report = build_risk_report(analysis)

        markdown = render_risk_report_markdown(report)

        self.assertIn("# 企业合规风险分析报告", markdown)
        self.assertIn("## 四、风险发现", markdown)
        self.assertIn("## 五、整改行动计划", markdown)
        self.assertIn("[《个人信息保护法》第十七条]", markdown)

    def test_export_json_can_trim_internal_fields(self):
        analysis = {
            "scenario": "APP已告知并取得同意",
            "summary": "整体合规。",
            "risk_level": "low",
            "risk_types": [],
            "risk_categories": [],
            "legal_basis": [],
            "recommended_actions": ["保持现有合规措施"],
            "confidence": {"answer": 0.9, "retrieval": 0.95, "overall": 0.9},
            "needs_human_review": False,
            "missing_evidence": [],
            "evidence_chain": [{"citation": "[《个人信息保护法》第十三条]"}],
        }
        report = build_risk_report(analysis)

        exported = export_risk_report(
            report,
            export_format="json",
            include_evidence_chain=False,
            include_source_analysis=False,
        )

        self.assertNotIn("evidence_chain", exported)
        self.assertNotIn("source_analysis", exported)
        self.assertEqual(exported["risk_level"], "low")

    def test_report_citation_integrity_flags_unsupported_finding_citation(self):
        report = {
            "executive_summary": "摘要无引用。",
            "risk_findings": [
                {
                    "analysis": "该行为违反[《个人信息保护法》第九十九条]。",
                    "recommended_actions": [],
                }
            ],
            "action_plan": [],
            "legal_basis": [{"citation": "[《个人信息保护法》第十七条]"}],
            "evidence_chain": [{"citation": "[《个人信息保护法》第十七条]"}],
        }

        integrity = build_report_citation_integrity(report)

        self.assertFalse(integrity["passed"])
        self.assertEqual(integrity["unsupported"], ["[《个人信息保护法》第九十九条]"])


if __name__ == "__main__":
    unittest.main()
