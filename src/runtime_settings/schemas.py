from __future__ import annotations

from pydantic import BaseModel, Field


class RuntimeFeedConfig(BaseModel):
    feed_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=8, max_length=1000)
    signal_type: str = "news"
    adapter: str = "rss_atom"
    risk_relevance: float = Field(default=1.0, ge=0.1, le=1.0)


class RuntimeSettingsSnapshot(BaseModel):
    llm_provider: str
    llm_base_url: str
    llm_model: str
    llm_api_key_configured: bool
    vision_llm_enabled: bool
    vision_llm_base_url: str
    vision_llm_model: str
    vision_llm_api_key_configured: bool
    siliconflow_base_url: str
    embedding_model: str
    siliconflow_api_key_configured: bool
    qdrant_host: str
    qdrant_port: int
    external_risk_live_enabled: bool
    external_risk_http_enabled: bool
    external_risk_akshare_enabled: bool
    external_risk_http_timeout_seconds: float
    external_risk_intelligence_enabled: bool
    external_risk_intelligence_poll_seconds: int
    external_risk_intelligence_scheduler_enabled: bool
    external_risk_web_search_enabled: bool
    external_risk_web_search_provider: str
    external_risk_web_search_api_key_configured: bool
    external_risk_web_search_timeout_seconds: float
    external_risk_web_search_max_results: int
    intelligence_feeds: list[RuntimeFeedConfig] = Field(default_factory=list)


class RuntimeSettingsResponse(BaseModel):
    status: str = "ok"
    data: RuntimeSettingsSnapshot


class RuntimeSettingsUpdate(BaseModel):
    llm_provider: str | None = Field(default=None, max_length=64)
    llm_base_url: str | None = Field(default=None, max_length=500)
    llm_model: str | None = Field(default=None, max_length=160)
    llm_api_key: str | None = Field(default=None, max_length=1000)
    vision_llm_enabled: bool | None = None
    vision_llm_base_url: str | None = Field(default=None, max_length=500)
    vision_llm_model: str | None = Field(default=None, max_length=160)
    vision_llm_api_key: str | None = Field(default=None, max_length=1000)
    siliconflow_base_url: str | None = Field(default=None, max_length=500)
    embedding_model: str | None = Field(default=None, max_length=200)
    siliconflow_api_key: str | None = Field(default=None, max_length=1000)
    qdrant_host: str | None = Field(default=None, max_length=240)
    qdrant_port: int | None = Field(default=None, ge=1, le=65535)
    external_risk_live_enabled: bool | None = None
    external_risk_http_enabled: bool | None = None
    external_risk_akshare_enabled: bool | None = None
    external_risk_http_timeout_seconds: float | None = Field(default=None, ge=1, le=60)
    external_risk_intelligence_enabled: bool | None = None
    external_risk_intelligence_poll_seconds: int | None = Field(default=None, ge=30, le=86400)
    external_risk_intelligence_scheduler_enabled: bool | None = None
    external_risk_web_search_enabled: bool | None = None
    external_risk_web_search_provider: str | None = Field(default=None, max_length=64)
    external_risk_web_search_api_key: str | None = Field(default=None, max_length=1000)
    external_risk_web_search_timeout_seconds: float | None = Field(default=None, ge=1, le=60)
    external_risk_web_search_max_results: int | None = Field(default=None, ge=1, le=10)
    intelligence_feeds: list[RuntimeFeedConfig] | None = None


class RuntimeSettingsUpdateResponse(BaseModel):
    status: str = "ok"
    data: RuntimeSettingsSnapshot
    restart_required: bool = False
