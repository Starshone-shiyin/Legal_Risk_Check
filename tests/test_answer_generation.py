import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.rag.answer_generation import build_answer_plan, build_material_context, generate_answer_payload


class AnswerGenerationTest(unittest.TestCase):
    def test_risk_plan_includes_markdown_structure_and_available_citations(self):
        plan = build_answer_plan(
            "risk_analysis",
            [{"citation": "[《中华人民共和国个人信息保护法》第六条]"}],
            ["最高相似度偏低，检索依据可能不足"],
        )

        self.assertIn("## 风险结论", plan)
        self.assertIn("[《中华人民共和国个人信息保护法》第六条]", plan)
        self.assertIn("最高相似度偏低", plan)

    def test_action_plan_uses_executable_markdown_guidance(self):
        plan = build_answer_plan("action_plan", [], [])

        self.assertIn("## 优先动作", plan)
        self.assertIn("当前没有可用引文", plan)

    def test_visual_observations_are_prompt_only_not_legal_evidence(self):
        materials = [{
            "task_id": "a" * 32,
            "filename": "receipt.png",
            "content": "MineU 解析文本",
            "truncated": False,
            "visual_input": {"data_url": "data:image/png;base64,private-bytes"},
        }]
        self.assertNotIn("private-bytes", build_material_context(materials))

        class FakeLlm:
            messages = None

            def invoke(self, messages, config):
                self.messages = messages
                return SimpleNamespace(content=(
                    '{"answer":"材料可见金额为 100 元。 [《中华人民共和国民法典》第一条]",'
                    '"confidence_score":0.8,"risk_level":"low","risk_types":[],"recommended_actions":[]}'
                ))

        fake_llm = FakeLlm()
        evidence = [{"citation": "[《中华人民共和国民法典》第一条]", "content": "民事主体依法享有民事权利。"}]
        with patch("src.rag.answer_generation.get_llm", return_value=fake_llm), patch(
            "src.rag.answer_generation.summarize_visual_materials", return_value="可见金额：100 元。"
        ):
            payload = generate_answer_payload(
                question="审查图片材料",
                context="[《中华人民共和国民法典》第一条] 民事主体依法享有民事权利。",
                evidence_chain=evidence,
                retrieval_confidence=0.8,
                missing_evidence=[],
                filters={},
                user_materials=materials,
            )

        prompt_text = "\n".join(str(message.content) for message in fake_llm.messages)
        self.assertIn("视觉材料观察", prompt_text)
        self.assertIn("可见金额：100 元", prompt_text)
        self.assertNotIn("private-bytes", prompt_text)
        self.assertEqual(payload["evidence_chain"], evidence)
        self.assertEqual(payload["sources"][0]["citation"], evidence[0]["citation"])
        self.assertTrue(payload["material_sources"][0]["visual_analysis_used"])
        self.assertNotIn("visual_input", payload["material_sources"][0])


if __name__ == "__main__":
    unittest.main()
