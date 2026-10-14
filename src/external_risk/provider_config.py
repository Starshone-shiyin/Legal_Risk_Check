from __future__ import annotations

import os
import json
from dataclasses import dataclass


TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


@dataclass(frozen=True)
class IntelligenceFeedConfig:
    feed_id: str
    url: str
    signal_type: str = "news"
    source_name: str = ""
    adapter: str = "rss_atom"
    risk_relevance: float = 1.0
    # Static market pages can retain old research links. A zero value keeps
    # the window disabled for custom feeds; core futures pages use seven days.
    max_age_hours: int = 0


CORE_INTELLIGENCE_FEEDS = (
    IntelligenceFeedConfig(
        feed_id="cailianshe-telegraph",
        url="https://www.cls.cn/api/cache?rn=50&lastTime={now}&name=telegraph",
        signal_type="news",
        source_name="财联社电报",
        adapter="cailianshe_telegraph",
    ),
    IntelligenceFeedConfig(
        feed_id="yicai-market-brief",
        url="https://www.yicai.com/",
        signal_type="news",
        source_name="第一财经全球市场大直播",
        adapter="yicai_homepage",
    ),
    IntelligenceFeedConfig(
        feed_id="sina-futures-market",
        url="https://finance.sina.com.cn/futuremarket/",
        signal_type="news",
        source_name="新浪期货",
        adapter="sina_futures_html",
        risk_relevance=0.75,
        max_age_hours=168,
    ),
    IntelligenceFeedConfig(
        feed_id="eastmoney-futures-market",
        url="https://futures.eastmoney.com/",
        signal_type="news",
        source_name="东方财富期货",
        adapter="eastmoney_futures_html",
        risk_relevance=0.75,
        max_age_hours=168,
    ),
    IntelligenceFeedConfig(
        feed_id="csrc-regulatory-actions",
        url="https://www.csrc.gov.cn/csrc/zwxx/index.shtml",
        signal_type="policy",
        source_name="中国证监会政务信息",
        adapter="official_policy_html",
        risk_relevance=0.35,
    ),
    IntelligenceFeedConfig(
        feed_id="mofcom-policy-release",
        url="https://www.mofcom.gov.cn/zcfb/",
        signal_type="policy",
        source_name="商务部政策发布",
        adapter="official_policy_html",
        risk_relevance=0.75,
    ),
    IntelligenceFeedConfig(
        feed_id="ndrc-notices",
        url="https://www.ndrc.gov.cn/xwdt/tzgg/",
        signal_type="policy",
        source_name="国家发展改革委通知公告",
        adapter="official_policy_html",
        risk_relevance=0.60,
    ),
)


@dataclass(frozen=True)
class ExternalRiskProviderConfig:
    live_enabled: bool = False
    http_enabled: bool = False
    akshare_enabled: bool = False
    http_timeout_seconds: float = 6.0
    akshare_market_function: str = "stock_zh_index_daily"
    akshare_commodity_function: str = "futures_zh_spot"
    default_lookback_days: int = 5
    intelligence_enabled: bool = True
    intelligence_feeds: tuple[IntelligenceFeedConfig, ...] = ()
    intelligence_poll_seconds: int = 300
    intelligence_scheduler_enabled: bool = False
    web_search_enabled: bool = False
    web_search_provider: str = "tavily"
    web_search_api_key: str = ""
    web_search_timeout_seconds: float = 8.0
    web_search_max_results: int = 5

    @property
    def akshare_live_enabled(self) -> bool:
        return self.live_enabled and self.akshare_enabled

    @property
    def http_live_enabled(self) -> bool:
        return self.live_enabled and self.http_enabled


def load_provider_config(env: dict[str, str] | None = None) -> ExternalRiskProviderConfig:
    values = os.environ if env is None else env
    live_enabled = _env_bool(values.get("EXTERNAL_RISK_LIVE_ENABLED"), default=True)
    configured_feeds = _env_intelligence_feeds(values.get("EXTERNAL_RISK_INTELLIGENCE_FEEDS"))
    intelligence_feeds = configured_feeds if configured_feeds is not None else CORE_INTELLIGENCE_FEEDS
    return ExternalRiskProviderConfig(
        live_enabled=live_enabled,
        http_enabled=_env_bool(values.get("EXTERNAL_RISK_HTTP_ENABLED"), default=live_enabled),
        akshare_enabled=_env_bool(values.get("EXTERNAL_RISK_AKSHARE_ENABLED")),
        http_timeout_seconds=_env_float(values.get("EXTERNAL_RISK_HTTP_TIMEOUT_SECONDS"), default=6.0),
        akshare_market_function=values.get("EXTERNAL_RISK_AKSHARE_MARKET_FUNCTION", "stock_zh_index_daily"),
        akshare_commodity_function=values.get("EXTERNAL_RISK_AKSHARE_COMMODITY_FUNCTION", "futures_zh_spot"),
        default_lookback_days=_env_int(values.get("EXTERNAL_RISK_DEFAULT_LOOKBACK_DAYS"), default=5),
        intelligence_enabled=_env_bool(values.get("EXTERNAL_RISK_INTELLIGENCE_ENABLED"), default=live_enabled),
        intelligence_feeds=intelligence_feeds,
        intelligence_poll_seconds=_env_int(values.get("EXTERNAL_RISK_INTELLIGENCE_POLL_SECONDS"), default=300),
        intelligence_scheduler_enabled=_env_bool(values.get("EXTERNAL_RISK_INTELLIGENCE_SCHEDULER_ENABLED")),
        web_search_enabled=_env_bool(values.get("EXTERNAL_RISK_WEB_SEARCH_ENABLED")),
        web_search_provider=values.get("EXTERNAL_RISK_WEB_SEARCH_PROVIDER", "tavily"),
        web_search_api_key=values.get("EXTERNAL_RISK_WEB_SEARCH_API_KEY", "").strip(),
        web_search_timeout_seconds=_env_float(values.get("EXTERNAL_RISK_WEB_SEARCH_TIMEOUT_SECONDS"), default=8.0),
        web_search_max_results=min(10, _env_int(values.get("EXTERNAL_RISK_WEB_SEARCH_MAX_RESULTS"), default=5)),
    )


def _env_bool(value: str | None, *, default: bool = False) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return default
    if normalized in FALSE_VALUES:
        return False
    return normalized in TRUE_VALUES


def _env_int(value: str | None, *, default: int) -> int:
    try:
        parsed = int(str(value or "").strip())
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _env_float(value: str | None, *, default: float) -> float:
    try:
        parsed = float(str(value or "").strip())
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _env_intelligence_feeds(value: str | None) -> tuple[IntelligenceFeedConfig, ...] | None:
    if value is None or not str(value).strip():
        return None
    try:
        raw_feeds = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return ()
    if not isinstance(raw_feeds, list):
        return ()
    feeds: list[IntelligenceFeedConfig] = []
    for index, item in enumerate(raw_feeds, start=1):
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url.startswith("https://"):
            continue
        signal_type = str(item.get("type") or "news").strip().lower()
        if signal_type not in {"news", "policy"}:
            continue
        feed_id = str(item.get("id") or f"intelligence-feed-{index}").strip()
        if not feed_id:
            continue
        adapter = str(item.get("adapter") or "rss_atom").strip().lower()
        if adapter not in {
            "rss_atom",
            "cailianshe_telegraph",
            "yicai_homepage",
            "official_policy_html",
            "sina_futures_html",
            "eastmoney_futures_html",
            "futures_exchange_notice_html",
        }:
            continue
        default_max_age = 168 if adapter in {"sina_futures_html", "eastmoney_futures_html"} else 0
        feeds.append(
            IntelligenceFeedConfig(
                feed_id=feed_id,
                url=url,
                signal_type=signal_type,
                source_name=str(item.get("name") or feed_id).strip(),
                adapter=adapter,
                risk_relevance=_bounded_float(item.get("risk_relevance"), default=1.0),
                max_age_hours=_nonnegative_int(item.get("max_age_hours"), default=default_max_age),
            )
        )
    return tuple(feeds)


def _bounded_float(value: object, *, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(1.0, max(0.1, parsed))


def _nonnegative_int(value: object, *, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return max(0, default)
