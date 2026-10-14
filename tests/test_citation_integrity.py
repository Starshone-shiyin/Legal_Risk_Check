import unittest

from src.core.citations import (
    assess_citation_coverage,
    collect_supported_citations,
    extract_citations,
    verify_citation_integrity,
)


class CitationIntegrityTest(unittest.TestCase):
    def test_extract_citations_deduplicates_bracketed_legal_citations(self):
        text = "依据[《个人信息保护法》第十七条]，并结合[《个人信息保护法》第十七条]判断。"

        self.assertEqual(extract_citations(text), ["[《个人信息保护法》第十七条]"])

    def test_extract_citations_accepts_inline_and_parenthetical_article_references(self):
        citations = extract_citations(
            "《中华人民共和国个人信息保护法》第二十八条规定敏感个人信息。"
            "处理时还应符合（第二十九条）和（第三十条）的要求。"
        )

        self.assertEqual(
            citations,
            [
                "[《中华人民共和国个人信息保护法》第二十八条]",
                "[《中华人民共和国个人信息保护法》第二十九条]",
                "[《中华人民共和国个人信息保护法》第三十条]",
            ],
        )

    def test_collect_supported_citations_from_evidence_items(self):
        supported = collect_supported_citations([
            {"citation": "[《个人信息保护法》第十七条]"},
            {"citations": ["[《个人信息保护法》第二十九条]"]},
        ])

        self.assertIn("[《个人信息保护法》第十七条]", supported)
        self.assertIn("[《个人信息保护法》第二十九条]", supported)

    def test_verify_citation_integrity_flags_unsupported_citation(self):
        integrity = verify_citation_integrity(
            ["依据[《个人信息保护法》第十七条]和[《个人信息保护法》第九十九条]。"],
            [{"citation": "[《个人信息保护法》第十七条]"}],
        )

        self.assertFalse(integrity["passed"])
        self.assertEqual(integrity["unsupported"], ["[《个人信息保护法》第九十九条]"])

    def test_article_level_evidence_supports_paragraph_level_citation(self):
        integrity = verify_citation_integrity(
            ["依据[《中华人民共和国民法典》第一百一十条第一款、第二款]判断。"],
            [{"citation": "[《中华人民共和国民法典》第一百一十条]"}],
        )

        self.assertTrue(integrity["passed"])
        self.assertEqual(integrity["unsupported"], [])

    def test_composite_standard_citation_requires_each_referenced_section(self):
        text = "见[《信息安全技术 个人信息安全规范》3.1 个人信息 personal information、3.2 个人敏感信息 personal sensitive information]。"
        evidence = [
            {"citation": "[《信息安全技术 个人信息安全规范》3.1 个人信息 personal information]"},
            {"citation": "[《信息安全技术 个人信息安全规范》3.2 个人敏感信息 personal sensitive information]"},
        ]

        self.assertTrue(verify_citation_integrity([text], evidence)["passed"])
        self.assertFalse(verify_citation_integrity([text], evidence[:1])["passed"])

    def test_coverage_requires_review_when_answer_omits_available_citations(self):
        coverage = assess_citation_coverage(
            ["该处理行为需要遵循合法、正当、必要原则。"],
            [{"citation": "[《中华人民共和国个人信息保护法》第六条]"}],
        )

        self.assertTrue(coverage["evidence_has_citations"])
        self.assertFalse(coverage["has_any_citation"])
        self.assertTrue(coverage["requires_review"])

    def test_coverage_accepts_supported_article_level_citation(self):
        coverage = assess_citation_coverage(
            ["应遵循相关原则[《中华人民共和国个人信息保护法》第六条第一款]。"],
            [{"citation": "[《中华人民共和国个人信息保护法》第六条]"}],
        )

        self.assertEqual(coverage["supported_citations"], ["[《中华人民共和国个人信息保护法》第六条第一款]"])
        self.assertFalse(coverage["requires_review"])

    def test_coverage_allows_general_actions_to_inherit_a_nearby_legal_basis(self):
        coverage = assess_citation_coverage(
            [
                "- 企业处理个人信息应遵循合法、正当、必要和诚信原则[《中华人民共和国个人信息保护法》第六条]。\n"
                "- 企业还应立即建立完整的数据合规治理体系并覆盖所有业务流程。"
            ],
            [{"citation": "[《中华人民共和国个人信息保护法》第六条]"}],
        )

        self.assertEqual(coverage["substantive_unit_count"], 2)
        self.assertEqual(coverage["cited_substantive_unit_count"], 1)
        self.assertEqual(coverage["uncited_substantive_unit_count"], 1)
        self.assertEqual(coverage["uncited_core_legal_claim_unit_count"], 0)
        self.assertFalse(coverage["requires_review"])
        self.assertTrue(coverage["warnings"])

    def test_coverage_allows_safe_html_general_actions_to_inherit_a_legal_basis(self):
        coverage = assess_citation_coverage(
            [
                "<ul><li>企业处理个人信息应遵循合法、正当、必要和诚信原则"
                "[《中华人民共和国个人信息保护法》第六条]。</li>"
                "<li>企业应建立覆盖全部业务流程的数据治理制度。</li></ul>"
            ],
            [{"citation": "[《中华人民共和国个人信息保护法》第六条]"}],
        )

        self.assertEqual(coverage["substantive_unit_count"], 2)
        self.assertEqual(coverage["uncited_substantive_unit_count"], 1)
        self.assertFalse(coverage["requires_review"])

    def test_coverage_requires_review_for_uncited_core_legal_claim(self):
        coverage = assess_citation_coverage(
            [
                "- 企业处理个人信息应遵循合法、正当、必要和诚信原则[《中华人民共和国个人信息保护法》第六条]。\n"
                "- 未经同意向第三方提供个人信息构成违法，应承担相应责任。"
            ],
            [{"citation": "[《中华人民共和国个人信息保护法》第六条]"}],
        )

        self.assertEqual(coverage["core_legal_claim_unit_count"], 2)
        self.assertEqual(coverage["uncited_core_legal_claim_unit_count"], 1)
        self.assertTrue(coverage["requires_review"])

    def test_coverage_allows_conclusion_to_reference_a_later_cited_legal_basis_section(self):
        coverage = assess_citation_coverage(
            [
                "## 风险结论\n\n"
                "未经同意向第三方提供个人信息构成违法，应承担相应责任。\n\n"
                "## 判断依据\n\n"
                "[《中华人民共和国个人信息保护法》第二十三条]规定了向其他个人信息处理者提供个人信息的条件。"
            ],
            [{"citation": "[《中华人民共和国个人信息保护法》第二十三条]"}],
        )

        self.assertEqual(coverage["uncited_core_legal_claim_unit_count"], 1)
        self.assertTrue(coverage["has_structured_legal_basis"])
        self.assertFalse(coverage["requires_review"])

    def test_coverage_accepts_extended_legal_basis_heading(self):
        coverage = assess_citation_coverage(
            [
                "## 结论\n\n"
                "个人撤回同意后，处理者仍负有相应删除义务。\n\n"
                "## 法律依据与操作要求\n\n"
                "[《中华人民共和国个人信息保护法》第四十七条]规定了删除个人信息的法定情形。"
            ],
            [{"citation": "[《中华人民共和国个人信息保护法》第四十七条]"}],
        )

        self.assertTrue(coverage["has_structured_legal_basis"])
        self.assertFalse(coverage["requires_review"])

    def test_coverage_accepts_cited_conditions_section_as_structured_basis(self):
        coverage = assess_citation_coverage(
            [
                "## 结论\n\n"
                "标准合同有效期内发生法定变化时，应重新评估。\n\n"
                "## 需要重新评估的情形\n\n"
                "根据[《个人信息出境标准合同办法》第八条]，出现法定变化时应重新评估。"
            ],
            [{"citation": "[《个人信息出境标准合同办法》第八条]"}],
        )

        self.assertTrue(coverage["has_structured_legal_basis"])
        self.assertFalse(coverage["requires_review"])

    def test_coverage_allows_later_cited_summary_to_support_prior_list(self):
        coverage = assess_citation_coverage(
            [
                "标准合同有效期内出现以下可能影响个人信息权益的情形：\n"
                "1. 向境外提供个人信息的目的、范围或者种类发生变化；\n"
                "2. 境外接收方所在国家的个人信息保护法规发生变化。\n"
                "上述情形源于[《个人信息出境标准合同办法》第八条]。"
            ],
            [{"citation": "[《个人信息出境标准合同办法》第八条]"}],
        )

        self.assertEqual(coverage["cited_substantive_unit_count"], 3)

    def test_coverage_allows_cited_intro_to_support_its_contiguous_list(self):
        coverage = assess_citation_coverage(
            [
                "根据[《数据出境安全评估办法》第五条]，重点评估以下事项：\n\n"
                "1. 数据处理目的、范围和方式的合法性、正当性、必要性；\n"
                "2. 出境数据的规模、范围、种类和敏感程度；\n"
                "3. 境外接收方的数据安全保障能力。"
            ],
            [{"citation": "[《数据出境安全评估办法》第五条]"}],
        )

        self.assertEqual(coverage["substantive_unit_count"], 4)
        self.assertEqual(coverage["cited_substantive_unit_count"], 4)
        self.assertFalse(coverage["requires_review"])

    def test_coverage_allows_immediate_reference_summary_to_inherit_support(self):
        coverage = assess_citation_coverage(
            [
                "个人信息处理应遵循合法、正当、必要和诚信原则[《中华人民共和国个人信息保护法》第五条]。\n"
                "上述原则共同构成个人信息处理活动的基本准则。"
            ],
            [{"citation": "[《中华人民共和国个人信息保护法》第五条]"}],
        )

        self.assertEqual(coverage["cited_substantive_unit_count"], 2)
        self.assertFalse(coverage["requires_review"])

    def test_coverage_allows_cited_rule_to_support_following_statutory_conditions(self):
        coverage = assess_citation_coverage(
            [
                "根据[《个人信息出境标准合同办法》第八条]，出现下列情形之一：\n"
                "1. 向境外提供个人信息的目的、范围、种类发生变化；\n"
                "2. 境外接收方所在国家或者地区的政策和法规发生变化。"
            ],
            [{"citation": "[《个人信息出境标准合同办法》第八条]"}],
        )

        self.assertEqual(coverage["cited_substantive_unit_count"], 3)
        self.assertFalse(coverage["requires_review"])

    def test_coverage_allows_cited_rule_ending_with_colon_to_support_following_steps(self):
        coverage = assess_citation_coverage(
            [
                "一旦触发[《个人信息出境标准合同办法》第八条]所述情形，应当同时完成：\n"
                "1. 重新开展个人信息保护影响评估；\n"
                "2. 补充或者重新订立标准合同。"
            ],
            [{"citation": "[《个人信息出境标准合同办法》第八条]"}],
        )

        self.assertEqual(coverage["cited_substantive_unit_count"], 3)
        self.assertFalse(coverage["requires_review"])


if __name__ == "__main__":
    unittest.main()
