"""Bounded multimodal observation for user-uploaded image materials."""
from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import get_settings


VISION_SYSTEM_PROMPT = """你是法律材料审查中的视觉信息提取助手。
只描述图片中可见、可读的事实：主体名称、日期、金额、印章/签名、表格字段、条款标题、风险提示或无法辨认之处。
不得给出法律结论、不得编造图片中不可见的内容。输出简洁中文要点。"""
MAX_VISION_IMAGES = 3


def get_vision_llm() -> ChatOpenAI | None:
    settings = get_settings()
    if not settings.vision_llm_enabled:
        return None
    return ChatOpenAI(
        model=settings.vision_llm_model,
        api_key=settings.vision_llm_api_key or settings.llm_api_key,
        base_url=settings.vision_llm_base_url or settings.llm_base_url,
        temperature=0.0,
    )


def summarize_visual_materials(question: str, materials: list[dict[str, Any]]) -> str:
    """Return non-authoritative image observations, or an empty value on failure."""
    images = [item for item in materials if isinstance(item.get("visual_input"), dict)][:MAX_VISION_IMAGES]
    if not images:
        return ""
    try:
        model = get_vision_llm()
        if model is None:
            return ""
        content: list[dict[str, Any]] = [{
            "type": "text",
            "text": f"用户问题：{question}\n请提取以下 {len(images)} 张用户上传图片中与问题有关的可见事实。",
        }]
        for item in images:
            visual_input = item["visual_input"]
            content.append({"type": "text", "text": f"图片文件：{item.get('filename') or '未命名'}"})
            content.append({"type": "image_url", "image_url": {"url": visual_input["data_url"]}})
        response = model.invoke([SystemMessage(content=VISION_SYSTEM_PROMPT), HumanMessage(content=content)], config={"timeout": 45})
    except Exception:
        return ""
    text = response.content
    if isinstance(text, list):
        text = "\n".join(str(part.get("text") or "") for part in text if isinstance(part, dict))
    return str(text or "").strip()[:8_000]
