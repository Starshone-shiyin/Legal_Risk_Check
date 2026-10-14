import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.core.vision import summarize_visual_materials


class VisionMaterialTest(unittest.TestCase):
    def test_sends_bounded_image_data_to_openai_compatible_vision_model(self):
        class FakeModel:
            messages = None

            def invoke(self, messages, config):
                self.messages = messages
                self.config = config
                return SimpleNamespace(content="- 可见日期：2026年8月21日")

        model = FakeModel()
        materials = [{
            "filename": "notice.png",
            "visual_input": {"data_url": "data:image/png;base64,abc"},
        }]
        with patch("src.core.vision.get_vision_llm", return_value=model):
            result = summarize_visual_materials("图片写了什么？", materials)

        self.assertIn("可见日期", result)
        content = model.messages[1].content
        self.assertIn({"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}}, content)
        self.assertEqual(model.config["timeout"], 45)

    def test_vision_failure_does_not_interrupt_main_answer_path(self):
        with patch("src.core.vision.get_vision_llm", side_effect=RuntimeError("unavailable")):
            result = summarize_visual_materials("审查", [{"visual_input": {"data_url": "data:image/png;base64,abc"}}])
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
