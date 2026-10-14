from __future__ import annotations

import json
import re


def normalize_string_list(value) -> list[str]:
    """Normalize LLM list-like output into a clean string list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()] if str(value).strip() else []


def extract_first_json_object(text: str) -> str | None:
    """Extract the first balanced JSON object from a possibly wrapped LLM reply."""
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


def parse_llm_json(content: str) -> dict:
    """Parse the RAG LLM JSON payload, preserving raw answer text on failure."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    payload = None
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        json_object = extract_first_json_object(cleaned)
        if json_object:
            try:
                payload = json.loads(json_object)
            except json.JSONDecodeError:
                payload = None

    if isinstance(payload, dict):
        answer = payload.get("answer", "").strip()
        confidence_score = payload.get("confidence_score")
        risk_level = payload.get("risk_level")
        risk_types = normalize_string_list(payload.get("risk_types"))
        recommended_actions = normalize_string_list(payload.get("recommended_actions"))
    else:
        answer = content.strip()
        match = re.search(r'"?confidence_score"?\s*[:：]\s*([01](?:\.\d+)?)', content)
        confidence_score = float(match.group(1)) if match else None
        risk_level = None
        risk_types = []
        recommended_actions = []

    if confidence_score is not None:
        try:
            confidence_score = max(0.0, min(1.0, float(confidence_score)))
        except (TypeError, ValueError):
            confidence_score = None

    if risk_level is not None:
        risk_level = str(risk_level).strip().lower()
        if risk_level not in {"low", "medium", "high"}:
            risk_level = None

    return {
        "answer": answer,
        "confidence_score": confidence_score,
        "risk_level": risk_level,
        "risk_types": risk_types,
        "recommended_actions": recommended_actions,
    }
