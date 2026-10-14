import unittest

from src.rag.answer_policy import apply_answer_mode_policy, normalize_answer_text


class AnswerPolicyTest(unittest.TestCase):
    def test_normalize_answer_text_demotes_items_under_difference_section(self):
        raw = "\n".join([
            "1、*共同点：**",
            "2、三者均为民事主体，平等参与民事活动。",
            "3、*不同点：**",
            "4、自然人基于出生取得民事主体资格。",
            "5、法人和非法人组织通常需要依法设立或登记。",
        ])

        normalized = normalize_answer_text(raw)

        self.assertIn("共同点：\n（1）三者均为民事主体", normalized)
        self.assertIn("不同点：\n（1）自然人基于出生取得", normalized)
        self.assertIn("（2）法人和非法人组织通常需要依法设立或登记。", normalized)
        self.assertNotIn("*", normalized)
        self.assertNotIn("4、自然人", normalized)

    def test_apply_answer_mode_policy_marks_contract_version(self):
        payload = {
            "answer": "自然人、法人和非法人组织都是民事主体。",
            "missing_evidence": [],
            "recommended_actions": [],
            "filters": {},
        }

        normalized = apply_answer_mode_policy(
            payload,
            question="民法上的自然人、法人、非法人组织有何异同？",
            mode="legal_qa",
            external_fact_needs={"requires_external_facts": False},
            evidence_chain=[],
        )

        self.assertEqual(normalized["filters"]["answer_contract_version"], "v2_markdown_html")
        self.assertIn("简要结论：", normalized["answer"])

    def test_normalize_answer_text_preserves_markdown_and_html(self):
        raw = "## 结论\n\n- **需要单独同意**\n- <strong>应保留审计日志</strong>"

        normalized = normalize_answer_text(raw)

        self.assertEqual(normalized, raw)


if __name__ == "__main__":
    unittest.main()
