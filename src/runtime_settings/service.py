from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from src.config import get_settings
from src.external_risk.provider_config import load_provider_config
from src.runtime_settings.schemas import RuntimeFeedConfig, RuntimeSettingsSnapshot, RuntimeSettingsUpdate


_RUNTIME_ENV_PATH = os.environ.get("RISKFLOW_RUNTIME_ENV_PATH")
ENV_PATH = Path(_RUNTIME_ENV_PATH) if _RUNTIME_ENV_PATH else Path(__file__).resolve().parents[2] / ".env"
_ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=.*$")
_LOCAL_DISABLED_API_KEY = "desktop-local-disabled"
LLM_PROVIDERS = {"openai_compatible", "anthropic_messages", "gemini_generate_content"}


class RuntimeSettingsError(ValueError):
    pass


def read_runtime_settings() -> RuntimeSettingsSnapshot:
    values = _effective_environment()
    provider_config = load_provider_config(values)
    return RuntimeSettingsSnapshot(
        llm_provider=_normalized_llm_provider(values.get("LLM_PROVIDER")),
        llm_base_url=values.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        llm_model=values.get("LLM_MODEL", "deepseek-chat"),
        llm_api_key_configured=_api_key_configured(values.get("LLM_API_KEY")),
        vision_llm_enabled=_as_bool(values.get("VISION_LLM_ENABLED"), True),
        vision_llm_base_url=values.get("VISION_LLM_BASE_URL") or values.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        vision_llm_model=values.get("VISION_LLM_MODEL", "deepseek-v4-flash-vision-exp"),
        vision_llm_api_key_configured=_api_key_configured(
            values.get("VISION_LLM_API_KEY") or values.get("LLM_API_KEY")
        ),
        siliconflow_base_url=values.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
        embedding_model=values.get("EMBEDDING_MODEL", "BAAI/bge-m3"),
        siliconflow_api_key_configured=_api_key_configured(values.get("SILICONFLOW_API_KEY")),
        qdrant_host=values.get("QDRANT_HOST", "localhost"),
        qdrant_port=_as_int(values.get("QDRANT_PORT"), 6333),
        external_risk_live_enabled=provider_config.live_enabled,
        external_risk_http_enabled=provider_config.http_enabled,
        external_risk_akshare_enabled=provider_config.akshare_enabled,
        external_risk_http_timeout_seconds=provider_config.http_timeout_seconds,
        external_risk_intelligence_enabled=provider_config.intelligence_enabled,
        external_risk_intelligence_poll_seconds=provider_config.intelligence_poll_seconds,
        external_risk_intelligence_scheduler_enabled=provider_config.intelligence_scheduler_enabled,
        external_risk_web_search_enabled=provider_config.web_search_enabled,
        external_risk_web_search_provider=provider_config.web_search_provider,
        external_risk_web_search_api_key_configured=bool(provider_config.web_search_api_key),
        external_risk_web_search_timeout_seconds=provider_config.web_search_timeout_seconds,
        external_risk_web_search_max_results=provider_config.web_search_max_results,
        intelligence_feeds=[
            RuntimeFeedConfig(
                feed_id=feed.feed_id,
                name=feed.source_name or feed.feed_id,
                url=feed.url,
                signal_type=feed.signal_type,
                adapter=feed.adapter,
                risk_relevance=feed.risk_relevance,
            )
            for feed in provider_config.intelligence_feeds
        ],
    )


def update_runtime_settings(update: RuntimeSettingsUpdate) -> tuple[RuntimeSettingsSnapshot, bool]:
    payload = update.model_dump(exclude_none=True)
    env_updates: dict[str, str] = {}
    string_mapping = {
        "llm_provider": "LLM_PROVIDER",
        "llm_base_url": "LLM_BASE_URL",
        "llm_model": "LLM_MODEL",
        "llm_api_key": "LLM_API_KEY",
        "vision_llm_base_url": "VISION_LLM_BASE_URL",
        "vision_llm_model": "VISION_LLM_MODEL",
        "vision_llm_api_key": "VISION_LLM_API_KEY",
        "siliconflow_base_url": "SILICONFLOW_BASE_URL",
        "embedding_model": "EMBEDDING_MODEL",
        "siliconflow_api_key": "SILICONFLOW_API_KEY",
        "qdrant_host": "QDRANT_HOST",
        "qdrant_port": "QDRANT_PORT",
        "external_risk_http_timeout_seconds": "EXTERNAL_RISK_HTTP_TIMEOUT_SECONDS",
        "external_risk_intelligence_poll_seconds": "EXTERNAL_RISK_INTELLIGENCE_POLL_SECONDS",
        "external_risk_web_search_provider": "EXTERNAL_RISK_WEB_SEARCH_PROVIDER",
        "external_risk_web_search_api_key": "EXTERNAL_RISK_WEB_SEARCH_API_KEY",
        "external_risk_web_search_timeout_seconds": "EXTERNAL_RISK_WEB_SEARCH_TIMEOUT_SECONDS",
        "external_risk_web_search_max_results": "EXTERNAL_RISK_WEB_SEARCH_MAX_RESULTS",
    }
    bool_mapping = {
        "external_risk_live_enabled": "EXTERNAL_RISK_LIVE_ENABLED",
        "external_risk_http_enabled": "EXTERNAL_RISK_HTTP_ENABLED",
        "external_risk_akshare_enabled": "EXTERNAL_RISK_AKSHARE_ENABLED",
        "external_risk_intelligence_enabled": "EXTERNAL_RISK_INTELLIGENCE_ENABLED",
        "external_risk_intelligence_scheduler_enabled": "EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED",
        "external_risk_web_search_enabled": "EXTERNAL_RISK_WEB_SEARCH_ENABLED",
        "vision_llm_enabled": "VISION_LLM_ENABLED",
    }
    for field, key in string_mapping.items():
        if field in payload:
            value = str(payload[field]).strip()
            if not value and field not in {"llm_api_key", "vision_llm_api_key", "siliconflow_api_key"}:
                raise RuntimeSettingsError(f"{field} cannot be empty")
            if value:
                env_updates[key] = value
    if "llm_provider" in payload and payload["llm_provider"] not in LLM_PROVIDERS:
        raise RuntimeSettingsError("Unsupported LLM provider protocol")
    if "llm_base_url" in payload:
        _validate_llm_base_url(payload["llm_base_url"])
    if "vision_llm_base_url" in payload:
        _validate_llm_base_url(payload["vision_llm_base_url"])
    for field, key in bool_mapping.items():
        if field in payload:
            env_updates[key] = "true" if payload[field] else "false"
    provider = str(payload.get("external_risk_web_search_provider") or "").strip().lower()
    if provider and provider not in {"tavily", "bing_html", "duckduckgo_html"}:
        raise RuntimeSettingsError("Unsupported web search provider")
    if "intelligence_feeds" in payload:
        feeds = payload["intelligence_feeds"]
        _validate_feeds(feeds)
        env_updates["EXTERNAL_RISK_INTELLIGENCE_FEEDS"] = json.dumps(
            [
                {
                    "id": feed["feed_id"],
                    "name": feed["name"],
                    "url": feed["url"],
                    "type": feed["signal_type"],
                    "adapter": feed["adapter"],
                    "risk_relevance": feed["risk_relevance"],
                }
                for feed in feeds
            ],
            ensure_ascii=False,
        )
    _write_environment(env_updates)
    get_settings.cache_clear()
    restart_required = "EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED" in env_updates
    return read_runtime_settings(), restart_required


def _effective_environment() -> dict[str, str]:
    file_values = {key: value for key, value in dotenv_values(ENV_PATH).items() if value is not None}
    return {**file_values, **os.environ}


def _api_key_configured(value: object) -> bool:
    return bool(str(value or "").strip()) and str(value).strip() != _LOCAL_DISABLED_API_KEY


def _write_environment(updates: dict[str, str]) -> None:
    if not updates:
        return
    existing = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    lines = existing.splitlines()
    pending = dict(updates)
    rendered: list[str] = []
    for line in lines:
        match = _ENV_LINE.match(line)
        if not match or match.group(1) not in pending:
            rendered.append(line)
            continue
        key = match.group(1)
        rendered.append(f"{key}={json.dumps(pending.pop(key), ensure_ascii=False)}")
    rendered.extend(f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in pending.items())
    ENV_PATH.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")
    for key, value in updates.items():
        os.environ[key] = value


def _validate_feeds(feeds: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    for feed in feeds:
        feed_id = str(feed.get("feed_id") or "").strip()
        if feed_id in ids:
            raise RuntimeSettingsError("RSS source identifiers must be unique")
        ids.add(feed_id)
        if not str(feed.get("url") or "").strip().startswith("https://"):
            raise RuntimeSettingsError("RSS source URLs must use HTTPS")
        if feed.get("signal_type") not in {"news", "policy"}:
            raise RuntimeSettingsError("Unsupported RSS signal type")
        if feed.get("adapter") not in {
            "rss_atom",
            "cailianshe_telegraph",
            "yicai_homepage",
            "official_policy_html",
            "sina_futures_html",
            "eastmoney_futures_html",
            "futures_exchange_notice_html",
        }:
            raise RuntimeSettingsError("Unsupported RSS adapter")


def _as_int(value: object, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalized_llm_provider(value: object) -> str:
    provider = str(value or "").strip().lower()
    return provider if provider in LLM_PROVIDERS else "openai_compatible"


def _validate_llm_base_url(value: object) -> None:
    url = str(value or "").strip()
    if not re.match(r"^https?://[^\s/]+", url):
        raise RuntimeSettingsError("LLM service URL must be an HTTP(S) address")
