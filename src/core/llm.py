from __future__ import annotations

from typing import Any

import httpx
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from src.config import get_settings


LLM_PROVIDER_OPENAI_COMPATIBLE = "openai_compatible"
LLM_PROVIDER_ANTHROPIC = "anthropic_messages"
LLM_PROVIDER_GEMINI = "gemini_generate_content"
SUPPORTED_LLM_PROVIDERS = {
    LLM_PROVIDER_OPENAI_COMPATIBLE,
    LLM_PROVIDER_ANTHROPIC,
    LLM_PROVIDER_GEMINI,
}


class NativeProviderChatModel:
    """Small adapter for the two mainstream non-OpenAI chat protocols."""

    def __init__(self, provider: str, api_key: str, base_url: str, model: str, temperature: float = 0.1) -> None:
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    def invoke(self, input: str | list[BaseMessage], config: dict[str, Any] | None = None) -> AIMessage:
        timeout = float((config or {}).get("timeout") or 60)
        messages = _normalize_messages(input)
        if self.provider == LLM_PROVIDER_ANTHROPIC:
            content = self._invoke_anthropic(messages, timeout)
        elif self.provider == LLM_PROVIDER_GEMINI:
            content = self._invoke_gemini(messages, timeout)
        else:
            raise ValueError(f"Unsupported LLM provider protocol: {self.provider}")
        return AIMessage(content=content)

    def _invoke_anthropic(self, messages: list[dict[str, str]], timeout: float) -> str:
        system_parts = [item["content"] for item in messages if item["role"] == "system"]
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "messages": [
                {"role": "assistant" if item["role"] == "assistant" else "user", "content": item["content"]}
                for item in messages
                if item["role"] != "system"
            ],
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        response = httpx.post(
            _anthropic_messages_url(self.base_url),
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        return _anthropic_response_text(response)

    def _invoke_gemini(self, messages: list[dict[str, str]], timeout: float) -> str:
        system_parts = [item["content"] for item in messages if item["role"] == "system"]
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "model" if item["role"] == "assistant" else "user",
                    "parts": [{"text": item["content"]}],
                }
                for item in messages
                if item["role"] != "system"
            ],
            "generationConfig": {"temperature": self.temperature},
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        response = httpx.post(
            _gemini_generate_url(self.base_url, self.model),
            params={"key": self.api_key},
            headers={"content-type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        try:
            response.raise_for_status()
            body = response.json()
            parts = body["candidates"][0]["content"]["parts"]
            text = "".join(str(part.get("text") or "") for part in parts).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("Gemini model request failed") from exc
        if not text:
            raise RuntimeError("Gemini model returned an empty response")
        return text


def get_llm() -> ChatOpenAI | NativeProviderChatModel:
    settings = get_settings()
    provider = str(settings.llm_provider or LLM_PROVIDER_OPENAI_COMPATIBLE).strip().lower()
    if provider == LLM_PROVIDER_OPENAI_COMPATIBLE:
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=0.1,
        )
    if provider not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider protocol: {provider}")
    return NativeProviderChatModel(
        provider=provider,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )


def _normalize_messages(input: str | list[BaseMessage]) -> list[dict[str, str]]:
    if isinstance(input, str):
        return [{"role": "user", "content": input}]
    messages: list[dict[str, str]] = []
    for message in input:
        role = "assistant" if message.type == "ai" else ("system" if message.type == "system" else "user")
        content = _message_content_text(message.content)
        if content:
            messages.append({"role": role, "content": content})
    if not messages:
        raise ValueError("LLM prompt cannot be empty")
    return messages


def _message_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces = []
        for item in content:
            if isinstance(item, str):
                pieces.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                pieces.append(str(item.get("text") or ""))
        return "\n".join(piece for piece in pieces if piece)
    return str(content or "")


def _anthropic_messages_url(base_url: str) -> str:
    if base_url.endswith("/v1/messages"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/messages"
    return f"{base_url}/v1/messages"


def _gemini_generate_url(base_url: str, model: str) -> str:
    versioned_base = base_url if base_url.endswith("/v1beta") else f"{base_url}/v1beta"
    return f"{versioned_base}/models/{model}:generateContent"


def _anthropic_response_text(response: httpx.Response) -> str:
    try:
        response.raise_for_status()
        body = response.json()
        parts = body["content"]
        text = "".join(str(item.get("text") or "") for item in parts if isinstance(item, dict)).strip()
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Anthropic model request failed") from exc
    if not text:
        raise RuntimeError("Anthropic model returned an empty response")
    return text
