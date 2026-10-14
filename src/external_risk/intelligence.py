from __future__ import annotations

import hashlib
import html
import json
import re
import threading
import time
import urllib.request
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from src.external_risk.commodity_catalog import CATALOG_BY_SYMBOL, symbols_from_text
from src.external_risk.provider_config import ExternalRiskProviderConfig, IntelligenceFeedConfig, load_provider_config
from src.external_risk.schemas import (
    ExternalRiskIntelligenceStatus,
    ExternalRiskProviderStatus,
    ExternalRiskSignal,
    IntelligenceFeedHealth,
)


DEFAULT_INTELLIGENCE_CACHE_PATH = Path("data/external_risk/intelligence_feed_cache.json")


@dataclass(frozen=True)
class IntelligenceRule:
    rule_id: str
    keywords: tuple[str, ...]
    risk_domain: str
    severity: str
    entity: str
    supply_links: tuple[str, ...] = ()
    trigger_keywords: tuple[str, ...] = ()
    industry_tags: tuple[str, ...] = ()


INTELLIGENCE_RULES = (
    IntelligenceRule(
        "geopolitical_shipping_disruption",
        (
            "maritime embargo", "oil tanker", "shipping disruption", "shipping blockade",
            "red sea", "hormuz", "bab el-mandeb", "海上禁运", "油轮", "商船遇袭",
            "船舶遇袭", "航运中断", "航道封锁", "港口封锁", "红海", "霍尔木兹", "曼德海峡",
        ),
        "supply_chain",
        "high",
        "geopolitical_shipping_disruption",
        ("maritime_logistics", "oil_transport", "cross_border_delivery", "energy_supply"),
        (),
        ("maritime_logistics", "oil_transport", "energy"),
    ),
    IntelligenceRule(
        "export_control",
        (
            "export control", "export management", "export quota", "entity list", "sanction", "embargo",
            "出口管制", "出口管理", "出口配额", "禁止出口", "实体清单", "制裁",
        ),
        "export_control",
        "high",
        "export_control",
        ("overseas_sales", "technical_support"),
    ),
    IntelligenceRule(
        "semiconductor_supply",
        ("semiconductor", "chip", "wafer", "lithography", "半导体", "芯片", "晶圆", "光刻"),
        "supply_chain",
        "medium",
        "semiconductor_supply",
        ("semiconductor_materials", "semiconductor_equipment"),
        ("shortage", "supply disruption", "outage", "restriction", "sanction", "短缺", "断供", "停产", "供应紧张", "出口限制", "制裁", "火灾", "召回"),
    ),
    IntelligenceRule(
        "data_compliance",
        ("data security", "personal information", "cybersecurity", "数据安全", "个人信息", "网络安全"),
        "data_compliance",
        "high",
        "data_compliance",
        (),
        ("breach", "leak", "penalty", "investigation", "violation", "泄露", "罚款", "处罚", "立案", "违规", "整改"),
    ),
    IntelligenceRule(
        "trade_remedy",
        ("anti-dumping", "countervailing", "tariff", "反倾销", "反补贴", "关税", "贸易救济"),
        "contract",
        "medium",
        "trade_remedy",
        ("cross_border_delivery",),
    ),
    IntelligenceRule(
        "securities_disclosure",
        ("securities regulator", "investigation", "administrative penalty", "证监", "立案调查", "行政处罚", "信息披露"),
        "disclosure",
        "high",
        "securities_disclosure",
        (),
        ("investigation", "penalty", "violation", "立案", "处罚", "违规", "谴责", "问询"),
    ),
    IntelligenceRule(
        "energy_cost_policy",
        ("electricity price", "power tariff", "grid tariff", "energy consumption", "电价", "输配电价", "能耗", "限产", "碳排放"),
        "supply_chain",
        "medium",
        "energy_cost_policy",
        ("electricity", "energy_supply"),
        ("electricity price", "power tariff", "grid tariff", "电价", "输配电价", "限产"),
    ),
    IntelligenceRule(
        "product_quality_recall",
        ("product recall", "defect", "quality safety", "产品召回", "缺陷", "质量安全"),
        "contract",
        "medium",
        "product_quality",
        ("product_delivery", "after_sales"),
        ("recall", "defect", "召回", "缺陷"),
    ),
    IntelligenceRule(
        "commodity_futures_supply_shock",
        (
            "期货", "期权", "原油", "燃料油", "天然气", "铜", "铝", "锡", "镍",
            "铁矿石", "钢材", "玻璃", "纯碱", "大豆", "豆油", "豆粕", "玉米",
            "棉花", "白糖", "航运", "集运", "黄金",
        ),
        "supply_chain",
        "medium",
        "commodity_futures_supply_shock",
        (),
        (
            "地缘", "冲突", "禁运", "制裁", "关税", "出口限制", "出口禁令", "减产",
            "停产", "罢工", "供应紧张", "供应扰动", "库存告急", "交割风险", "极端天气",
            "干旱", "洪涝", "厄尔尼诺", "涨跌停", "保证金", "限仓", "限制开仓", "暂停交易",
            "异常交易", "强制减仓",
            "价格", "报价", "涨价", "降价", "上涨", "下跌", "涨超", "跌超", "涨近", "跌近",
            "涨幅", "跌幅", "走强", "走弱", "走高", "走低", "异动", "震荡", "现货", "供需", "库存",
            "进口", "出口", "产量", "需求", "成本", "运费", "运价", "基差", "储备",
            "主力合约", "日内", "收益",
        ),
    ),
)


# Financial news feeds often publish a useful supply-chain observation without
# calling it a "shock". Keep this rule deliberately narrow: an explicit
# supply-chain object and an observable market/supply trigger are both required.
SUPPLY_CHAIN_MARKET_OBSERVATION_RULE = IntelligenceRule(
    "supply_chain_market_observation",
    (
        "供应链", "产业链", "上游", "下游", "中游", "原材料", "原料", "材料",
        "半导体", "芯片", "晶圆", "光刻", "cpo", "光模块", "消费电子", "电子特气",
        "电子", "显示面板", "面板", "玻璃基板", "pcb", "印制电路", "封装", "测试",
        "通信", "光纤", "光缆", "基站", "服务器", "数据中心", "算力", "存储",
        "电网", "电力", "有色金属", "稀有金属", "钼", "钨", "锂", "钴",
        "航运", "海运", "油运", "港口", "物流", "运输", "原油", "天然气", "煤炭",
        "焦煤", "焦炭", "铁矿石", "钢材", "铜", "铝", "镍", "锡", "玻璃", "纯碱",
        "橡胶", "纸浆", "化工", "化纤", "纺织", "包装", "汽车", "新能源汽车", "零部件",
        "电池", "锂电", "储能", "光伏", "风电", "新能源", "医药", "医疗器械", "农产品",
        "粮食", "食品", "化肥", "制造业", "制造", "工业", "产线", "设备", "装备",
        "工业母机", "机床", "期货", "现货",
    ),
    "supply_chain",
    "low",
    "supply_chain_market_observation",
    ("supply_chain_market_observation",),
    (
        "价格", "报价", "涨价", "降价", "上涨", "下跌", "涨超", "跌超", "涨近", "跌近",
        "涨幅", "跌幅", "走强", "走弱", "走高", "走低", "异动", "震荡", "净流入", "净流出", "供需",
        "库存", "进口", "出口", "产量", "需求", "成本", "运费", "运价", "基差",
        "储备", "供应", "供货", "供应商", "短缺", "断供", "中断", "订单", "采购", "交付", "发货",
        "停航", "停运", "停产", "停工", "检修", "复产", "扩产", "投产", "产能", "排产", "开工",
        "招标", "中标", "封装", "测试", "召回", "事故", "火灾", "罢工", "主力合约", "日内", "收益", "交割",
    ),
)

TRANSPORT_DISRUPTION_RULE = IntelligenceRule(
    "transport_disruption",
    ("航线", "航运", "海运", "油运", "港口", "船舶", "铁路", "物流", "运输", "航道"),
    "supply_chain",
    "medium",
    "transport_disruption",
    ("maritime_logistics", "oil_transport", "cross_border_delivery"),
    ("停航", "停运", "受阻", "中断", "封锁", "拥堵", "台风", "大风", "暴雨", "洪涝", "地震", "罢工", "事故"),
    ("maritime_logistics", "oil_transport"),
)

COMMODITY_MARKET_TRIGGER_TERMS = (
    "价格", "报价", "涨价", "降价", "上涨", "下跌", "涨超", "跌超", "涨近", "跌近",
    "涨幅", "跌幅", "走强", "走弱", "走高", "走低", "异动", "震荡", "现货", "供需", "库存", "进口",
    "出口", "产量", "需求", "成本", "运费", "运价", "基差", "储备", "主力合约",
    "日内", "收益", "交割",
)

SUPPLY_CHAIN_MARKET_KEYWORDS = SUPPLY_CHAIN_MARKET_OBSERVATION_RULE.keywords
SUPPLY_CHAIN_MARKET_ANCHORS = (
    "半导体", "芯片", "晶圆", "光刻", "cpo", "光模块", "消费电子", "电子特气",
    "电子", "显示面板", "面板", "玻璃基板", "pcb", "印制电路", "封装", "测试",
    "通信", "光纤", "光缆", "基站", "服务器", "数据中心", "算力", "存储",
    "电网", "电力", "有色金属", "稀有金属", "钼", "钨", "锂", "钴",
    "航运", "海运", "油运", "港口", "物流", "运输", "原油", "天然气", "煤炭",
    "焦煤", "焦炭", "铁矿石", "钢材", "铜", "铝", "镍", "锡", "玻璃", "纯碱",
    "橡胶", "纸浆", "化工", "化纤", "纺织", "包装", "汽车", "新能源汽车", "零部件",
    "电池", "锂电", "储能", "光伏", "风电", "新能源", "医药", "医疗器械", "农产品",
    "粮食", "食品", "化肥", "制造业", "制造", "工业", "产线", "设备", "装备", "工业母机", "机床", "原材料",
)


SECURITY_INDUSTRY_CATALOG = (
    (("中国石油", "三桶油", "petrochina", "601857"), ("oil_transport", "energy"), "中国石油（SH.601857）"),
    (("中国石化", "三桶油", "sinopec", "600028"), ("oil_transport", "energy"), "中国石化（SH.600028）"),
    (("中国海油", "三桶油", "cnooc", "600938"), ("oil_transport", "energy"), "中国海油（SH.600938）"),
    (("中远海控", "cosco shipping", "601919"), ("maritime_logistics",), "中远海控（SH.601919）"),
    (("中远海能", "600026"), ("maritime_logistics", "oil_transport"), "中远海能（SH.600026）"),
    (("招商轮船", "601872"), ("maritime_logistics", "oil_transport"), "招商轮船（SH.601872）"),
    (("宁波远洋", "601022"), ("maritime_logistics",), "宁波远洋（SH.601022）"),
    (("中谷物流", "603565"), ("maritime_logistics",), "中谷物流（SH.603565）"),
)

SUPPLY_CHAIN_INDUSTRY_ALIASES = (
    (("半导体", "芯片", "晶圆", "光刻", "封装", "测试", "存储", "hbm", "dram", "nand"), ("semiconductor",)),
    (("cpo", "光模块", "通信", "光纤", "光缆", "基站", "交换机"), ("telecom",)),
    (("消费电子", "显示面板", "面板", "玻璃基板", "电子", "pcb", "印制电路"), ("consumer_electronics", "display_panel")),
    (("电网", "电力", "输配电", "变压器", "电气设备"), ("power_grid",)),
    (("服务器", "数据中心", "算力", "ai算力"), ("data_center",)),
    (("电池", "锂电", "锂", "钴", "储能", "光伏", "风电", "新能源汽车"), ("new_energy",)),
    (("原油", "天然气", "煤炭", "油运", "炼化", "燃料油"), ("energy", "oil_transport")),
    (("航运", "海运", "港口", "物流", "运输", "集运", "航线"), ("maritime_logistics",)),
    (("铜", "铝", "镍", "锡", "锌", "铅", "钼", "钨", "铁矿石", "钢材"), ("metals",)),
    (("化工", "化纤", "橡胶", "纸浆", "包装", "化肥"), ("chemical_materials",)),
    (("汽车", "零部件", "工业母机", "机床", "机械设备", "电力设备", "装备制造", "制造业"), ("industrial_equipment",)),
    (("农产品", "粮食", "食品", "棉花", "白糖", "大豆", "玉米"), ("agriculture_food",)),
    (("医药", "医疗器械"), ("healthcare",)),
)

INDUSTRY_WATCHLIST_INSTRUMENTS = {
    "oil_transport": ("中国石油（SH.601857）", "中国石化（SH.600028）", "中国海油（SH.600938）", "中远海能（SH.600026）", "招商轮船（SH.601872）"),
    "maritime_logistics": ("中远海控（SH.601919）", "中远海能（SH.600026）", "招商轮船（SH.601872）", "宁波远洋（SH.601022）"),
}

MAJOR_LISTED_EVENT_RULE = IntelligenceRule(
    "listed_company_major_event",
    (),
    "corporate_governance",
    "high",
    "listed_company_major_event",
)

MAJOR_LISTED_EVENT_TERMS = (
    "重大事项", "重大事故", "安全事故", "停产", "停工", "停航", "停运", "罢工",
    "重大合同", "违约", "立案调查", "行政处罚", "召回", "重大亏损", "业绩预亏",
    "major incident", "major accident", "shutdown", "suspension", "strike", "recall",
    "investigation", "contract default",
)

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
ESCALATION_TERMS = ("ban", "prohibit", "sanction", "penalty", "investigation", "禁止", "限制", "制裁", "处罚", "立案")

FUTURES_EXCHANGE_NOTICE_RULE = IntelligenceRule(
    "futures_exchange_notice",
    (),
    "market",
    "medium",
    "futures_exchange_notice",
)

FUTURES_EXCHANGE_NOTICE_TERMS = (
    "保证金", "涨跌停板", "限仓", "限制开仓", "风险控制", "风险管理", "异常交易",
    "强制减仓", "暂停交易", "交割", "交割仓库", "仓单", "结算参数", "手续费", "合约",
)


class NewsPolicyRssExternalRiskProvider:
    """Configurable RSS/Atom adapter with transparent, reviewable rule classification."""

    provider_id = "news_policy_rss_provider"
    provider_type = "news_policy"

    def __init__(
        self,
        config: ExternalRiskProviderConfig | None = None,
        *,
        fetcher: Callable[[str], str] | None = None,
        cache_path: Path = DEFAULT_INTELLIGENCE_CACHE_PATH,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.config = config or load_provider_config()
        self._fetcher = fetcher or self._default_fetcher
        self.cache_path = cache_path
        self._clock = clock
        self._last_runtime_access = "not_called"
        self._refresh_lock = threading.RLock()

    def status(self) -> ExternalRiskProviderStatus:
        if not self.config.live_enabled:
            message = "News and policy monitoring is disabled because EXTERNAL_RISK_LIVE_ENABLED is false."
            status, mode = "not_configured", "disabled"
        elif not self.config.intelligence_enabled:
            message = "Set EXTERNAL_RISK_INTELLIGENCE_ENABLED=true to enable configured RSS/Atom monitoring."
            status, mode = "not_configured", "disabled"
        elif not self.config.intelligence_feeds:
            message = "Add HTTPS feeds in EXTERNAL_RISK_INTELLIGENCE_FEEDS before monitoring can start."
            status, mode = "not_configured", "disabled"
        else:
            health = self.feed_health()
            succeeded = sum(item.status == "success" for item in health)
            empty = sum(item.status == "empty" for item in health)
            failed = sum(item.status == "failed" for item in health)
            if failed and not succeeded:
                message = f"All {failed} configured financial or policy sources failed on the latest poll; cached evidence is retained for review."
                status, mode = "unavailable", "live"
            elif succeeded:
                suffix = f" {empty} source(s) returned no parseable article records and are excluded from the healthy count." if empty else ""
                message = f"{succeeded}/{len(health)} configured financial and policy sources are healthy; matched events are sent to reviewable risk signals.{suffix}"
                status, mode = "available", "live"
            else:
                message = f"Monitoring {len(self.config.intelligence_feeds)} configured financial, policy, and RSS/Atom sources with review signals."
                status, mode = "available", "live"
        return ExternalRiskProviderStatus(
            provider_id=self.provider_id,
            provider_type="news_policy",
            status=status,  # type: ignore[arg-type]
            mode=mode,  # type: ignore[arg-type]
            message=message,
            runtime_access=self._runtime_access_from_cache(),
        )

    def intelligence_status(self) -> ExternalRiskIntelligenceStatus:
        cached = self._read_cache()
        signals = _signals_from_cache(cached)
        return ExternalRiskIntelligenceStatus(
            provider=self.status(),
            cache_fresh=self._cache_is_fresh(cached),
            cache_updated_at=_clock_iso(cached.get("fetched_at")),
            cached_signal_count=len(signals),
            poll_seconds=self.config.intelligence_poll_seconds,
            feeds=self.feed_health(cached),
        )

    def feed_health(self, cached: dict[str, Any] | None = None) -> list[IntelligenceFeedHealth]:
        payload = cached if cached is not None else self._read_cache()
        records = payload.get("feed_health") if payload.get("feed_fingerprint") == self._feed_fingerprint() else []
        by_id = {
            str(record.get("feed_id")): record
            for record in records
            if isinstance(record, dict) and record.get("feed_id")
        } if isinstance(records, list) else {}
        health: list[IntelligenceFeedHealth] = []
        for feed in self.config.intelligence_feeds:
            record = by_id.get(feed.feed_id, {})
            status = str(record.get("status") or "not_called")
            if status not in {"success", "empty", "failed", "not_called"}:
                status = "not_called"
            health.append(
                IntelligenceFeedHealth(
                    feed_id=feed.feed_id,
                    source_name=feed.source_name or feed.feed_id,
                    adapter=feed.adapter,
                    url=feed.url,
                    signal_type=feed.signal_type,  # type: ignore[arg-type]
                    risk_relevance=feed.risk_relevance,
                    status=status,  # type: ignore[arg-type]
                    last_checked_at=_optional_text(record.get("last_checked_at")),
                    last_success_at=_optional_text(record.get("last_success_at")),
                    item_count=_nonnegative_int(record.get("item_count")),
                    signal_count=_nonnegative_int(record.get("signal_count")),
                    error=_optional_text(record.get("error")),
                )
            )
        return health

    def live_signals(
        self,
        *,
        signal_type: str | None = None,
        symbol: str | None = None,
        commodity_group: str | None = None,
    ) -> list[ExternalRiskSignal]:
        del symbol, commodity_group
        if signal_type and signal_type not in {"news", "policy", "all"}:
            return []
        signals = self._signals(force_refresh=False)
        return [signal for signal in signals if not signal_type or signal_type == "all" or signal.signal_type == signal_type]

    def refresh(self) -> list[ExternalRiskSignal]:
        return self._signals(force_refresh=True)

    def _signals(self, *, force_refresh: bool) -> list[ExternalRiskSignal]:
        if not (self.config.live_enabled and self.config.intelligence_enabled and self.config.intelligence_feeds):
            self._last_runtime_access = "not_called"
            return []
        with self._refresh_lock:
            cached = self._read_cache()
            if not force_refresh and self._cache_is_fresh(cached):
                self._last_runtime_access = "cache_read"
                return _signals_from_cache(cached)

            cached_signals = _signals_from_cache(cached)
            signals: list[ExternalRiskSignal] = []
            feed_health: list[dict[str, Any]] = []
            previous_health = {item.feed_id: item for item in self.feed_health(cached)}
            for feed in self.config.intelligence_feeds:
                checked_at = _utc_now_iso()
                previous = previous_health.get(feed.feed_id)
                try:
                    raw = self._fetcher(_resolve_feed_url(feed.url, self._clock()))
                    parsed = signals_from_feed_payload(raw, feed, fetched_at=checked_at)
                    parsed = _filter_recent_static_feed_signals(parsed, feed, now=self._clock())
                    if feed.feed_id == "csrc-regulatory-actions":
                        parsed = enrich_csrc_action_signals(parsed, self._fetcher)
                    signals.extend(parsed)
                    item_count = _payload_item_count(raw, feed)
                    feed_health.append(
                        _feed_health_record(
                            feed,
                            status="success" if item_count else "empty",
                            checked_at=checked_at,
                            last_success_at=checked_at if item_count else (previous.last_success_at if previous else None),
                            item_count=item_count,
                            signal_count=len(parsed),
                            error="No parseable article records were returned by this adapter." if not item_count else None,
                        )
                    )
                except Exception as exc:
                    fallback = [
                        signal
                        for signal in cached_signals
                        if signal.metadata.get("feed_id") == feed.feed_id
                    ]
                    signals.extend(_mark_stale_signals(fallback, checked_at))
                    feed_health.append(
                        _feed_health_record(
                            feed,
                            status="failed",
                            checked_at=checked_at,
                            last_success_at=previous.last_success_at if previous else None,
                            item_count=previous.item_count if previous else 0,
                            signal_count=len(fallback),
                            error=_safe_error_message(exc),
                        )
                    )
            signals = _dedupe_signals(signals)
            self._write_cache(signals, feed_health)
            self._last_runtime_access = "live_called"
            return signals

    def _cache_is_fresh(self, payload: dict[str, Any]) -> bool:
        fetched_at = payload.get("fetched_at")
        return (
            isinstance(fetched_at, (int, float))
            and payload.get("feed_fingerprint") == self._feed_fingerprint()
            and self._clock() - float(fetched_at) < self.config.intelligence_poll_seconds
        )

    def _read_cache(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _write_cache(self, signals: list[ExternalRiskSignal], feed_health: list[dict[str, Any]]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": 2,
                "fetched_at": self._clock(),
                "feed_fingerprint": self._feed_fingerprint(),
                "signals": [signal.model_dump(mode="json") for signal in signals],
                "feed_health": feed_health,
            }
            temporary_path = self.cache_path.with_suffix(f"{self.cache_path.suffix}.tmp")
            temporary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary_path.replace(self.cache_path)
        except OSError:
            pass

    def _runtime_access_from_cache(self) -> str:
        if self._last_runtime_access != "not_called":
            return self._last_runtime_access
        cached = self._read_cache()
        if self._cache_is_fresh(cached):
            return "cache_read"
        return "not_called"

    def _feed_fingerprint(self) -> str:
        value = "|".join(
            f"{feed.feed_id}:{feed.signal_type}:{feed.adapter}:{feed.risk_relevance}:{feed.max_age_hours}:{feed.url}"
            for feed in self.config.intelligence_feeds
        )
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    def _default_fetcher(self, url: str) -> str:
        # Several exchange notice pages return a WAF shell to non-browser user agents.
        # This identifies the client normally while preserving the same bounded timeout.
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"})
        with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")


def signals_from_feed_xml(raw: str, feed: IntelligenceFeedConfig, *, fetched_at: str | None = None) -> list[ExternalRiskSignal]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    entries = [element for element in root.iter() if _xml_local_name(element.tag) in {"item", "entry"}]
    signals: list[ExternalRiskSignal] = []
    for entry in entries[:80]:
        title = _entry_text(entry, ("title",))
        summary = _entry_text(entry, ("description", "summary", "content"))
        content = _clean_text(f"{title} {summary}")
        if not title or not content:
            continue
        rules = _matching_rules(content)
        if not rules:
            continue
        published_at = _entry_text(entry, ("pubDate", "published", "updated", "date")) or fetched_at or _utc_now_iso()
        link = _entry_link(entry) or feed.url
        signals.append(_signal_from_entry(feed, title, content, link, published_at, rules))
    return _dedupe_signals(signals)


def signals_from_feed_payload(raw: str, feed: IntelligenceFeedConfig, *, fetched_at: str | None = None) -> list[ExternalRiskSignal]:
    if feed.adapter == "cailianshe_telegraph":
        return signals_from_cailianshe_telegraph(raw, feed, fetched_at=fetched_at)
    if feed.adapter == "yicai_homepage":
        return signals_from_yicai_homepage(raw, feed, fetched_at=fetched_at)
    if feed.adapter == "sina_futures_html":
        return signals_from_sina_futures_html(raw, feed, fetched_at=fetched_at)
    if feed.adapter == "eastmoney_futures_html":
        return signals_from_eastmoney_futures_html(raw, feed, fetched_at=fetched_at)
    if feed.adapter == "futures_exchange_notice_html":
        return signals_from_futures_exchange_notice_html(raw, feed, fetched_at=fetched_at)
    if feed.adapter == "official_policy_html":
        return signals_from_official_policy_html(raw, feed, fetched_at=fetched_at)
    return signals_from_feed_xml(raw, feed, fetched_at=fetched_at)


def signals_from_cailianshe_telegraph(
    raw: str,
    feed: IntelligenceFeedConfig,
    *,
    fetched_at: str | None = None,
) -> list[ExternalRiskSignal]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    records = payload.get("data", {}).get("roll_data", []) if isinstance(payload, dict) else []
    if not isinstance(records, list):
        return []
    signals: list[ExternalRiskSignal] = []
    for record in records[:80]:
        if not isinstance(record, dict):
            continue
        title = _clean_text(str(record.get("title") or record.get("brief") or ""))
        content = _clean_text(str(record.get("content") or record.get("brief") or title))
        if not title or not content:
            continue
        rules = _matching_rules(f"{title} {content}")
        if not rules:
            continue
        item_id = str(record.get("id") or "").strip()
        link = f"https://www.cls.cn/telegraph/{item_id}" if item_id else "https://www.cls.cn/telegraph"
        published_at = _timestamp_iso(record.get("ctime")) or fetched_at or _utc_now_iso()
        signals.append(_signal_from_entry(feed, title, content, link, published_at, rules))
    return _dedupe_signals(signals)


def signals_from_yicai_homepage(
    raw: str,
    feed: IntelligenceFeedConfig,
    *,
    fetched_at: str | None = None,
) -> list[ExternalRiskSignal]:
    match = re.search(r'id=["\']scrollFontDiv["\'][^>]*>\s*<ul[^>]*>(.*?)</ul>', raw, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    signals: list[ExternalRiskSignal] = []
    pattern = r"<li[^>]*>\s*<span[^>]*>([^<]+)</span>\s*<a[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>\s*</li>"
    for item in re.finditer(pattern, match.group(1), flags=re.IGNORECASE | re.DOTALL):
        time_label = _clean_text(item.group(1))
        content_html = item.group(3)
        title_match = re.search(r"<b[^>]*>(.*?)</b>", content_html, flags=re.IGNORECASE | re.DOTALL)
        title = _clean_text(title_match.group(1) if title_match else content_html)
        content = _clean_text(content_html)
        if not title or not content:
            continue
        rules = _matching_rules(f"{title} {content}")
        if not rules:
            continue
        link = urljoin("https://www.yicai.com/", item.group(2))
        published_at = _same_day_time_iso(time_label) or fetched_at or _utc_now_iso()
        signals.append(_signal_from_entry(feed, title, content, link, published_at, rules))
    return _dedupe_signals(signals)


def signals_from_sina_futures_html(
    raw: str,
    feed: IntelligenceFeedConfig,
    *,
    fetched_at: str | None = None,
) -> list[ExternalRiskSignal]:
    """Read first-party Sina Futures article links and retain material event signals only."""
    signals: list[ExternalRiskSignal] = []
    seen_links: set[str] = set()
    for title, href in _html_anchor_entries(raw, feed.url):
        if "/money/future/" not in href.lower() or href in seen_links:
            continue
        seen_links.add(href)
        rules = _matching_rules(title)
        if not rules or not _is_supply_chain_relevant(title, rules):
            continue
        signals.append(
            _signal_from_entry(
                feed,
                title,
                title,
                href,
                _published_at_from_text(f"{href} {title}") or fetched_at or _utc_now_iso(),
                rules,
            )
        )
    return _dedupe_signals(signals)


def signals_from_eastmoney_futures_html(
    raw: str,
    feed: IntelligenceFeedConfig,
    *,
    fetched_at: str | None = None,
) -> list[ExternalRiskSignal]:
    """Read material commodity and futures articles from Eastmoney's futures channel."""
    signals: list[ExternalRiskSignal] = []
    seen_links: set[str] = set()
    for title, href in _html_anchor_entries(raw, feed.url):
        if "/a/" not in href.lower() or "eastmoney.com" not in href.lower() or href in seen_links:
            continue
        seen_links.add(href)
        rules = _matching_rules(title)
        if not rules or not _is_supply_chain_relevant(title, rules):
            continue
        signals.append(
            _signal_from_entry(
                feed,
                title,
                title,
                href,
                _published_at_from_text(f"{href} {title}") or fetched_at or _utc_now_iso(),
                rules,
            )
        )
    return _dedupe_signals(signals)


def signals_from_futures_exchange_notice_html(
    raw: str,
    feed: IntelligenceFeedConfig,
    *,
    fetched_at: str | None = None,
) -> list[ExternalRiskSignal]:
    """Extract material trading, delivery, and risk-control notices from an exchange page."""
    signals: list[ExternalRiskSignal] = []
    seen_links: set[str] = set()
    for title, href in _html_anchor_entries(raw, feed.url):
        if href in seen_links or not _is_futures_exchange_notice(title, href):
            continue
        seen_links.add(href)
        rules = [FUTURES_EXCHANGE_NOTICE_RULE, *_matching_rules(title)]
        if not _is_supply_chain_relevant(title, rules):
            continue
        signals.append(
            _signal_from_entry(
                feed,
                title,
                title,
                href,
                _published_at_from_text(f"{href} {title}") or fetched_at or _utc_now_iso(),
                rules,
            )
        )
    return _dedupe_signals(signals)


def signals_from_official_policy_html(
    raw: str,
    feed: IntelligenceFeedConfig,
    *,
    fetched_at: str | None = None,
) -> list[ExternalRiskSignal]:
    """Read article links from official notice and enforcement list pages, excluding navigation links."""
    signals: list[ExternalRiskSignal] = []
    for item in re.findall(r"<li\b[^>]*>(.*?)</li>", raw, flags=re.IGNORECASE | re.DOTALL):
        article = _official_article_link(item)
        if article is None:
            continue
        title, href = article
        if len(title) < 8:
            continue
        rules = _matching_rules(title)
        if not rules:
            continue
        date_match = re.search(r"\b(20\d{2})[/-](\d{1,2})[/-](\d{1,2})\b", item)
        published_at = (
            f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}T00:00:00+08:00"
            if date_match
            else fetched_at or _utc_now_iso()
        )
        signals.append(_signal_from_entry(feed, title, title, urljoin(feed.url, href), published_at, rules))
    return _dedupe_signals(signals)


def enrich_csrc_action_signals(
    signals: list[ExternalRiskSignal],
    fetcher: Callable[[str], str],
) -> list[ExternalRiskSignal]:
    """Add the public decision number and subject when a CSRC list page uses a generic title."""
    enriched: list[ExternalRiskSignal] = []
    for signal in signals:
        if signal.metadata.get("feed_id") != "csrc-regulatory-actions" or "行政处罚决定书" not in signal.title:
            enriched.append(signal)
            continue
        try:
            raw = fetcher(signal.source)
            description = _html_meta_description(raw)
            details = _csrc_action_details(raw, description)
            is_general_regulatory_context = not details["instruments"]
            title = _csrc_action_title(
                description,
                violation=details["violation"],
                instruments=details["instruments"],
            ) or signal.title
            evidence = description or signal.evidence
            enriched.append(
                signal.model_copy(
                    update={
                        "title": title,
                        "evidence": evidence[:4000],
                        "severity": "low" if is_general_regulatory_context else signal.severity,
                        "confidence": min(signal.confidence, 0.12) if is_general_regulatory_context else signal.confidence,
                        "affected_domains": ["corporate_governance"] if is_general_regulatory_context else signal.affected_domains,
                        "metadata": {
                            **signal.metadata,
                            "csrc_subjects": details["subjects"],
                            "csrc_violation": details["violation"],
                            "csrc_instruments": details["instruments"],
                            "csrc_instrument_status": "disclosed" if details["instruments"] else "not_disclosed",
                            "risk_scope": "general_regulatory_environment" if is_general_regulatory_context else "identified_security_event",
                            "risk_relevance": min(float(signal.metadata.get("risk_relevance") or 1.0), 0.15)
                            if is_general_regulatory_context else signal.metadata.get("risk_relevance", 1.0),
                        },
                    }
                )
            )
        except Exception:
            enriched.append(signal)
    return enriched


def _signal_from_entry(
    feed: IntelligenceFeedConfig,
    title: str,
    content: str,
    link: str,
    published_at: str,
    rules: list[IntelligenceRule],
) -> ExternalRiskSignal:
    article_text = _clean_text(f"{title} {content}")
    highest = max(rules, key=lambda rule: SEVERITY_RANK[rule.severity])
    severity = highest.severity
    if any(term in article_text.lower() for term in ESCALATION_TERMS):
        severity = {"low": "medium", "medium": "high", "high": "critical", "critical": "critical"}[severity]
    domains = list(dict.fromkeys(rule.risk_domain for rule in rules))
    supply_links = list(dict.fromkeys(link for rule in rules for link in rule.supply_links))
    is_futures_message = (
        feed.adapter in {"sina_futures_html", "eastmoney_futures_html", "futures_exchange_notice_html"}
        or (
            any(rule.rule_id == "commodity_futures_supply_shock" for rule in rules)
            and not any(rule.rule_id == "geopolitical_shipping_disruption" for rule in rules)
        )
    )
    # Resolve catalog instruments for any article that names one explicitly,
    # including general financial feeds such as CLS and Yicai.
    commodity_symbols = symbols_from_text(article_text) if is_futures_message else []
    commodity_tags = [
        tag
        for symbol in commodity_symbols
        for tag in CATALOG_BY_SYMBOL[symbol].chain_tags
        if symbol in CATALOG_BY_SYMBOL
    ]
    industry_tags = list(dict.fromkeys([
        *(tag for rule in rules for tag in rule.industry_tags),
        *_mentioned_industry_tags(article_text),
        *commodity_tags,
    ]))
    affected_instruments = list(dict.fromkeys([
        *(_commodity_instrument_label(symbol) for symbol in commodity_symbols),
        *_industry_watchlist_instruments(industry_tags, _mentioned_industry_instruments(article_text)),
    ]))[:8]
    item_key = hashlib.sha256(f"{feed.feed_id}|{link}|{title}".encode("utf-8")).hexdigest()[:20]
    source_confidence = min(0.92, (0.80 if feed.signal_type == "policy" else 0.66) + 0.04 * min(len(rules), 3))
    confidence = source_confidence * feed.risk_relevance
    evidence = _evidence_without_title(content, title)
    return ExternalRiskSignal(
        signal_id=f"live-intelligence-{item_key}",
        signal_type=feed.signal_type,  # type: ignore[arg-type]
        title=title[:180],
        severity=severity,  # type: ignore[arg-type]
        direction="negative",
        as_of=published_at,
        entity=highest.entity,
        metric="policy_rule_match" if feed.signal_type == "policy" else "news_rule_match",
        value=float(len(rules)),
        threshold=1.0,
        affected_domains=domains,  # type: ignore[arg-type]
        affected_supply_links=supply_links,
        # Keep sufficient clean article text for review. The UI folds it by default,
        # so a longer evidence field does not turn the dashboard into a wall of text.
        evidence=evidence[:4000],
        source=link,
        confidence=round(confidence, 2),
        metadata={
            "provider_id": "news_policy_rss_provider",
            "feed_id": feed.feed_id,
            "feed_name": feed.source_name or feed.feed_id,
            "feed_url": feed.url,
            "source_confidence": round(source_confidence, 2),
            "risk_relevance": feed.risk_relevance,
            "matched_rules": [rule.rule_id for rule in rules],
            "commodity_symbols": commodity_symbols,
            "industry_tags": industry_tags,
            "affected_instruments": affected_instruments,
            "requires_human_review": True,
        },
    )


def _commodity_instrument_label(symbol: str) -> str:
    contract = CATALOG_BY_SYMBOL.get(symbol)
    if contract is None:
        return symbol
    prefix = "HF" if symbol.startswith("hf_") else "CNF" if symbol.startswith("if_") else contract.exchange
    return f"{contract.name}（{prefix}.{symbol.split('_', 1)[-1].upper()}）"


def _is_supply_chain_relevant(content: str, rules: list[IntelligenceRule]) -> bool:
    """Require futures-source records to have a reviewable supply-chain connection."""
    commodity_symbols = symbols_from_text(content)
    if commodity_symbols:
        non_financial_tags = {
            tag
            for symbol in commodity_symbols
            for tag in CATALOG_BY_SYMBOL[symbol].chain_tags
        }.difference({"financial", "rates", "risk_appetite", "safe_haven", "precious_metal"})
        if non_financial_tags:
            return True
        # A bond or equity-index contract is a macro-market observation, not a
        # commodity or physical supply-chain event for this news queue.
        if not any(term in content.lower() for term in ("物流", "运输", "港口", "航运", "海运", "原材料")):
            return False
    if any(rule.risk_domain == "supply_chain" for rule in rules):
        return True
    if any(_mentioned_industry_tags(content)):
        return True
    for symbol in symbols_from_text(content):
        contract = CATALOG_BY_SYMBOL.get(symbol)
        if contract and set(contract.chain_tags).difference({"financial", "rates", "risk_appetite", "safe_haven"}):
            return True
    normalized = content.lower()
    return any(term in normalized for term in ("交割", "交割仓库", "仓单", "库存", "物流", "运输", "港口"))


def _mentioned_industry_instruments(content: str) -> list[str]:
    normalized = content.lower()
    instruments: list[str] = []
    for keywords, _tags, label in SECURITY_INDUSTRY_CATALOG:
        if any(keyword in normalized for keyword in keywords):
            instruments.append(label)
    return list(dict.fromkeys(instruments))[:8]


def _mentioned_industry_tags(content: str) -> list[str]:
    normalized = content.lower()
    tags: list[str] = []
    for keywords, industry_tags, _label in SECURITY_INDUSTRY_CATALOG:
        if any(keyword in normalized for keyword in keywords):
            tags.extend(industry_tags)
    for keywords, industry_tags in SUPPLY_CHAIN_INDUSTRY_ALIASES:
        if any(keyword.lower() in normalized for keyword in keywords):
            tags.extend(industry_tags)
    return list(dict.fromkeys(tags))


def _industry_watchlist_instruments(industry_tags: list[str], mentioned: list[str]) -> list[str]:
    instruments = list(mentioned)
    for tag in industry_tags:
        instruments.extend(INDUSTRY_WATCHLIST_INSTRUMENTS.get(tag, ()))
    return list(dict.fromkeys(instruments))[:8]


def _signals_from_cache(payload: dict[str, Any]) -> list[ExternalRiskSignal]:
    records = payload.get("signals")
    if not isinstance(records, list):
        return []
    signals: list[ExternalRiskSignal] = []
    for record in records:
        try:
            if isinstance(record, dict):
                signals.append(ExternalRiskSignal(**record))
        except Exception:
            continue
    return signals


def _feed_health_record(
    feed: IntelligenceFeedConfig,
    *,
    status: str,
    checked_at: str,
    last_success_at: str | None,
    item_count: int,
    signal_count: int,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "feed_id": feed.feed_id,
        "source_name": feed.source_name or feed.feed_id,
        "adapter": feed.adapter,
        "url": feed.url,
        "signal_type": feed.signal_type,
        "risk_relevance": feed.risk_relevance,
        "status": status,
        "last_checked_at": checked_at,
        "last_success_at": last_success_at,
        "item_count": item_count,
        "signal_count": signal_count,
        "error": error,
    }


def _payload_item_count(raw: str, feed: IntelligenceFeedConfig) -> int:
    if feed.adapter == "cailianshe_telegraph":
        try:
            payload = json.loads(raw)
            records = payload.get("data", {}).get("roll_data", []) if isinstance(payload, dict) else []
            return len(records) if isinstance(records, list) else 0
        except json.JSONDecodeError:
            return 0
    if feed.adapter == "yicai_homepage":
        return len(re.findall(r"<li(?:\s|>)", raw, flags=re.IGNORECASE))
    if feed.adapter == "sina_futures_html":
        return sum("/money/future/" in href.lower() for _title, href in _html_anchor_entries(raw, feed.url))
    if feed.adapter == "eastmoney_futures_html":
        return sum("/a/" in href.lower() and "eastmoney.com" in href.lower() for _title, href in _html_anchor_entries(raw, feed.url))
    if feed.adapter == "futures_exchange_notice_html":
        return sum(_is_futures_exchange_notice(title, href) for title, href in _html_anchor_entries(raw, feed.url))
    if feed.adapter == "official_policy_html":
        return sum(
            _official_article_link(item) is not None
            for item in re.findall(r"<li\b[^>]*>(.*?)</li>", raw, flags=re.IGNORECASE | re.DOTALL)
        )
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return 0
    return sum(1 for element in root.iter() if _xml_local_name(element.tag) in {"item", "entry"})


def _mark_stale_signals(signals: list[ExternalRiskSignal], checked_at: str) -> list[ExternalRiskSignal]:
    return [
        signal.model_copy(
            update={
                "metadata": {
                    **signal.metadata,
                    "source_stale": True,
                    "source_last_failure_at": checked_at,
                    "requires_human_review": True,
                }
            }
        )
        for signal in signals
    ]


def _filter_recent_static_feed_signals(
    signals: list[ExternalRiskSignal],
    feed: IntelligenceFeedConfig,
    *,
    now: float,
) -> list[ExternalRiskSignal]:
    """Bound stale links from static futures pages without hiding live feeds."""
    if feed.adapter not in {"sina_futures_html", "eastmoney_futures_html"} or feed.max_age_hours <= 0:
        return signals
    cutoff = now - feed.max_age_hours * 60 * 60
    return [signal for signal in signals if _signal_epoch(signal.as_of) >= cutoff]


def _safe_error_message(exc: Exception) -> str:
    text = _clean_text(str(exc)) or exc.__class__.__name__
    return text[:220]


def _signal_epoch(value: str) -> float:
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        return 0.0


def _clock_iso(value: Any) -> str | None:
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat(timespec="seconds")


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _matching_rules(content: str) -> list[IntelligenceRule]:
    normalized = content.lower()
    rules = [
        rule
        for rule in INTELLIGENCE_RULES
        if any(keyword.lower() in normalized for keyword in rule.keywords)
        and (not rule.trigger_keywords or any(keyword.lower() in normalized for keyword in rule.trigger_keywords))
    ]
    matched_rule_ids = {rule.rule_id for rule in rules}
    if "commodity_futures_supply_shock" in matched_rule_ids and not _has_physical_commodity_basis(normalized):
        rules = [rule for rule in rules if rule.rule_id != "commodity_futures_supply_shock"]
        matched_rule_ids.remove("commodity_futures_supply_shock")
    # A catalog update should not require a second hard-coded keyword list in
    # the news classifier. Explicitly named commodity contracts are enough to
    # widen the commodity rule when paired with an observable market or supply
    # change, while unrelated price commentary remains excluded.
    if (
        symbols_from_text(normalized)
        and _has_physical_commodity_basis(normalized)
        and any(term.lower() in normalized for term in COMMODITY_MARKET_TRIGGER_TERMS)
        and "commodity_futures_supply_shock" not in matched_rule_ids
    ):
        rules.append(next(rule for rule in INTELLIGENCE_RULES if rule.rule_id == "commodity_futures_supply_shock"))
        matched_rule_ids.add("commodity_futures_supply_shock")
    if (
        any(keyword.lower() in normalized for keyword in TRANSPORT_DISRUPTION_RULE.keywords)
        and any(term.lower() in normalized for term in TRANSPORT_DISRUPTION_RULE.trigger_keywords)
        and "transport_disruption" not in matched_rule_ids
    ):
        rules.append(TRANSPORT_DISRUPTION_RULE)
        matched_rule_ids.add("transport_disruption")
    if (
        any(anchor.lower() in normalized for anchor in SUPPLY_CHAIN_MARKET_ANCHORS)
        and any(term.lower() in normalized for term in SUPPLY_CHAIN_MARKET_OBSERVATION_RULE.trigger_keywords)
        and not matched_rule_ids.intersection({"commodity_futures_supply_shock", "transport_disruption"})
    ):
        rules.append(SUPPLY_CHAIN_MARKET_OBSERVATION_RULE)
    if _mentioned_industry_instruments(normalized) and any(term.lower() in normalized for term in MAJOR_LISTED_EVENT_TERMS):
        rules.append(MAJOR_LISTED_EVENT_RULE)
    return rules


def _has_physical_commodity_basis(content: str) -> bool:
    symbols = symbols_from_text(content)
    if symbols:
        tags = {
            tag
            for symbol in symbols
            for tag in CATALOG_BY_SYMBOL[symbol].chain_tags
        }
        if tags.difference({"financial", "rates", "risk_appetite", "safe_haven", "precious_metal"}):
            return True
        return False
    # Do not turn an unnamed, generic futures-market bulletin into a supply
    # chain signal. Specific physical commodities are resolved by the catalog
    # above; this fallback covers article wording that uses a commodity name
    # not yet present in that catalog.
    return any(term in content for term in (
        "原油", "天然气", "燃料油", "煤炭", "焦煤", "焦炭", "铁矿石", "钢材", "铜",
        "铝", "镍", "锡", "锌", "铅", "锂", "钴", "钨", "钼", "玻璃", "纯碱",
        "大豆", "豆油", "豆粕", "玉米", "棉花", "白糖", "橡胶", "纸浆", "航运", "集运",
    ))


def _resolve_feed_url(url: str, now: float) -> str:
    return url.replace("{now}", str(int(now)))


def _timestamp_iso(value: Any) -> str | None:
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def _same_day_time_iso(value: str) -> str | None:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", value.strip())
    if not match:
        return None
    now = datetime.now(timezone(timedelta(hours=8)))
    return now.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=0, microsecond=0).isoformat()


def _entry_text(entry: ET.Element, names: tuple[str, ...]) -> str:
    for element in entry.iter():
        if _xml_local_name(element.tag) in names and element.text:
            return _clean_text(element.text)
    return ""


def _entry_link(entry: ET.Element) -> str:
    for element in entry.iter():
        if _xml_local_name(element.tag) != "link":
            continue
        href = str(element.attrib.get("href") or "").strip()
        if href:
            return href
        if element.text and element.text.strip():
            return element.text.strip()
    return ""


def _html_anchor_entries(raw: str, base_url: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for match in re.finditer(
        r"<a\b(?P<attributes>[^>]*)href=[\"'](?P<href>[^\"'#]+)[\"'][^>]*>(?P<title>.*?)</a>",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        attributes = match.group("attributes")
        title_match = re.search(r"\btitle=[\"'](.*?)[\"']", attributes, flags=re.IGNORECASE | re.DOTALL)
        title = _clean_text(title_match.group(1) if title_match else match.group("title"))
        href = urljoin(base_url, html.unescape(match.group("href")).strip())
        if title and href.startswith("https://"):
            entries.append((title, href))
    return entries


def _is_futures_exchange_notice(title: str, href: str) -> bool:
    if "/publicnotice/notice/" not in href.lower():
        return False
    normalized = title.lower()
    return any(term.lower() in normalized for term in FUTURES_EXCHANGE_NOTICE_TERMS)


def _published_at_from_text(value: str) -> str | None:
    match = re.search(r"(20\d{2})[-_/]?(\d{2})[-_/]?(\d{2})", value)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}T00:00:00+08:00"


def _official_article_link(item: str) -> tuple[str, str] | None:
    for match in re.finditer(
        r"<a\b(?P<attributes>[^>]*)href=[\"'](?P<href>[^\"'#]+)[\"'][^>]*>(?P<title>.*?)</a>",
        item,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        href = html.unescape(match.group("href")).strip()
        if not re.search(r"(?:/content\.shtml|/art/20\d{2}/|/t20\d{6}_\d+\.html)", href, flags=re.IGNORECASE):
            continue
        attributes = match.group("attributes")
        title_match = re.search(r"\btitle=[\"'](.*?)[\"']", attributes, flags=re.IGNORECASE | re.DOTALL)
        title = _clean_text(title_match.group(1) if title_match else match.group("title"))
        if title:
            return title, href
    return None


def _html_meta_description(raw: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", raw, flags=re.IGNORECASE | re.DOTALL):
        name_match = re.search(r"\bname=[\"']([^\"']+)[\"']", tag, flags=re.IGNORECASE)
        if not name_match or name_match.group(1).strip().lower() != "description":
            continue
        content_match = re.search(r"\bcontent=[\"'](.*?)[\"']", tag, flags=re.IGNORECASE | re.DOTALL)
        if content_match:
            return _clean_text(content_match.group(1))
    return ""


def _csrc_action_title(
    description: str,
    *,
    violation: str = "",
    instruments: list[str] | None = None,
) -> str:
    normalized = _clean_text(description)
    if not normalized or "当事人" not in normalized:
        return ""
    number_match = re.search(r"(〔[^〕]{1,18}〕\s*\d+号)", normalized)
    subject_match = re.search(r"当事人\s*[:：]\s*(.+?)(?=依据|根据|因[此为]|经查|$)", normalized)
    if not subject_match:
        return ""
    subject = re.sub(r"[，,]\s*[男女]", "", subject_match.group(1))
    subject = _clean_text(subject).rstrip("。；;")
    if not subject:
        return ""
    decision = number_match.group(1).replace(" ", "") if number_match else ""
    parts = [f"证监会行政处罚决定书{decision}"]
    if violation:
        parts.append(violation)
    if instruments:
        parts.append(f"涉及证券：{'、'.join(instruments[:3])}")
    parts.append(f"当事人：{subject[:72]}")
    return "｜".join(parts)


def _csrc_action_details(raw: str, description: str) -> dict[str, Any]:
    normalized = _clean_text(raw)
    subject_match = re.search(r"当事人\s*[:：]\s*(.+?)(?=依据|根据|因|经查|$)", _clean_text(description))
    subjects = _clean_text(subject_match.group(1)).rstrip("。；;") if subject_match else ""
    violation = next(
        (
            label
            for keyword, label in (
                ("操纵证券市场", "操纵证券市场"),
                ("内幕交易", "内幕交易"),
                ("信息披露违法", "信息披露违法"),
                ("欺诈发行", "欺诈发行"),
                ("违法减持", "违法减持"),
            )
            if keyword in normalized
        ),
        "",
    )
    return {
        "subjects": subjects,
        "violation": violation,
        "instruments": _csrc_disclosed_instruments(normalized),
    }


def _csrc_disclosed_instruments(text: str) -> list[str]:
    labels: list[str] = []
    for name, code in re.findall(r"([\u4e00-\u9fffA-Za-z]{2,16})\s*[（(]\s*(?:证券代码|股票代码)?\s*(\d{6})\s*[）)]", text):
        label = f"{name}（{_csrc_security_code(code)}）"
        if label not in labels:
            labels.append(label)
    for code in re.findall(r"(?:证券代码|股票代码)\s*[:：]\s*(\d{6})", text):
        label = _csrc_security_code(code)
        if label not in labels:
            labels.append(label)
    return labels[:6]


def _csrc_security_code(code: str) -> str:
    exchange = "SH" if str(code).startswith(("5", "6", "9")) else "BJ" if str(code).startswith(("4", "8")) else "SZ"
    return f"{exchange}.{code}"


def _xml_local_name(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(str(value)))
    return re.sub(r"\s+", " ", text).strip()


def _evidence_without_title(content: str, title: str) -> str:
    """Avoid rendering the card heading again as the first evidence sentence."""
    evidence = _clean_text(content)
    heading = _clean_text(title)
    if heading and evidence.startswith(heading):
        trimmed = evidence[len(heading):].lstrip(" |｜:：，,。；;")
        return trimmed
    return evidence


def _dedupe_signals(signals: list[ExternalRiskSignal]) -> list[ExternalRiskSignal]:
    deduped: dict[str, ExternalRiskSignal] = {}
    for signal in signals:
        key = signal.signal_id
        event_key = _event_dedup_key(signal)
        existing = deduped.get(event_key) or deduped.get(key)
        if existing is None or _intelligence_signal_priority(signal) > _intelligence_signal_priority(existing):
            deduped[event_key] = signal
    return list(deduped.values())


def _event_dedup_key(signal: ExternalRiskSignal) -> str:
    # The CSRC index intentionally repeats a generic decision title; detail-page enrichment
    # differentiates those notices by decision number and subject after list parsing.
    if signal.metadata.get("feed_id") == "csrc-regulatory-actions":
        return signal.signal_id
    correlated_key = _futures_event_dedup_key(signal)
    if correlated_key:
        return correlated_key
    # A policy article and a financial-media repost usually differ in their lead
    # sentence. Deduplicate on the canonical event title and calendar date instead
    # of the source-specific evidence; preserving both would double count one event.
    date_key = str(signal.as_of or "")[:10]
    title = _canonical_event_title(signal.title)
    return f"{signal.entity}|{date_key}|{title[:120]}"


def _futures_event_dedup_key(signal: ExternalRiskSignal) -> str:
    """Collapse multi-source coverage of one futures shock before risk scoring."""
    date_key = str(signal.as_of or "")[:10]
    content = f"{signal.title} {signal.evidence}".lower()
    if signal.entity == "geopolitical_shipping_disruption":
        route = next(
            (
                label
                for label, terms in {
                    "hormuz": ("霍尔木兹", "hormuz", "波斯湾"),
                    "red_sea": ("红海", "red sea", "曼德海峡", "bab el-mandeb"),
                }.items()
                if any(term in content for term in terms)
            ),
            "",
        )
        return f"{signal.entity}|{date_key}|{route}" if route else ""
    if signal.entity != "commodity_futures_supply_shock":
        return ""
    cause = next(
        (
            label
            for label, terms in {
                "geopolitical": ("地缘", "冲突", "制裁", "禁运"),
                "trade": ("关税", "出口限制", "出口禁令"),
                "supply": ("减产", "停产", "罢工", "供应紧张", "供应扰动", "库存告急"),
                "weather": ("极端天气", "干旱", "洪涝", "厄尔尼诺"),
                "market_rules": ("交割风险", "保证金", "限仓", "限制开仓", "暂停交易", "强制减仓"),
            }.items()
            if any(term in content for term in terms)
        ),
        "",
    )
    symbols = signal.metadata.get("commodity_symbols")
    contracts = ",".join(sorted(str(symbol) for symbol in symbols)) if isinstance(symbols, list) else ""
    return f"{signal.entity}|{date_key}|{cause}|{contracts}" if cause and contracts else ""


def _canonical_event_title(value: str) -> str:
    text = _clean_text(value).lower()
    text = re.sub(r"^(?:商务部|国家发展改革委|证监会|中国证监会|财联社|第一财经)[：:、\s-]*", "", text)
    text = re.sub(r"^(?:新闻发言人)?就", "", text)
    text = re.sub(r"(?:答记者问|回应记者提问|情况说明|最新消息|快讯)$", "", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", text)
    return text


def _intelligence_signal_priority(signal: ExternalRiskSignal) -> tuple[int, int, float, str]:
    # When an official policy release and media repost describe one event, retain
    # the primary source even when the repost carries a more urgent headline.
    official = int(str(signal.metadata.get("feed_id") or "") in {
        "csrc-regulatory-actions", "mofcom-policy-release", "ndrc-notices",
    })
    return (official, SEVERITY_RANK.get(signal.severity, 0), float(signal.confidence or 0.0), signal.as_of)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
