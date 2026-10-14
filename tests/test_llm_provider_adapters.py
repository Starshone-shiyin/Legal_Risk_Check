from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from langchain_core.messages import HumanMessage, SystemMessage

from src.core.llm import (
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_GEMINI,
    NativeProviderChatModel,
)


class NativeProviderChatModelTest(unittest.TestCase):
    @patch("src.core.llm.httpx.post")
    def test_anthropic_messages_adapter_keeps_system_and_chat_roles(self, post):
        response = Mock()
        response.json.return_value = {"content": [{"type": "text", "text": "分析结果"}]}
        post.return_value = response
        model = NativeProviderChatModel(
            LLM_PROVIDER_ANTHROPIC,
            api_key="anthropic-secret",
            base_url="https://api.anthropic.com",
            model="claude-test",
        )

        result = model.invoke([SystemMessage(content="系统规则"), HumanMessage(content="用户问题")], config={"timeout": 12})

        self.assertEqual(result.content, "分析结果")
        url, = post.call_args.args
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(post.call_args.kwargs["headers"]["x-api-key"], "anthropic-secret")
        self.assertEqual(post.call_args.kwargs["json"]["system"], "系统规则")
        self.assertEqual(post.call_args.kwargs["json"]["messages"], [{"role": "user", "content": "用户问题"}])
        self.assertEqual(post.call_args.kwargs["timeout"], 12)

    @patch("src.core.llm.httpx.post")
    def test_gemini_adapter_uses_generate_content_format(self, post):
        response = Mock()
        response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "Gemini 结果"}]}}]}
        post.return_value = response
        model = NativeProviderChatModel(
            LLM_PROVIDER_GEMINI,
            api_key="gemini-secret",
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-test",
        )

        result = model.invoke([SystemMessage(content="系统规则"), HumanMessage(content="用户问题")])

        self.assertEqual(result.content, "Gemini 结果")
        url, = post.call_args.args
        self.assertEqual(url, "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent")
        self.assertEqual(post.call_args.kwargs["params"], {"key": "gemini-secret"})
        self.assertEqual(post.call_args.kwargs["json"]["systemInstruction"]["parts"][0]["text"], "系统规则")
        self.assertEqual(post.call_args.kwargs["json"]["contents"], [{"role": "user", "parts": [{"text": "用户问题"}]}])


if __name__ == "__main__":
    unittest.main()
