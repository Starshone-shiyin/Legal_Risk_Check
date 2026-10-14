"""Controlled online search primitives for current legal and market facts.

This module deliberately searches result pages only. It does not treat arbitrary
web text as legal authority and it fails closed when the provider is disabled.
"""
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Protocol

from src.external_risk.provider_config import ExternalRiskProviderConfig, load_provider_config
from src.external_risk.schemas import (
    SearchDomain,
    SearchIntent,
    WebSearchPlan,
    WebSearchResult,
)


OFFICIAL_DOMAINS = (
    "gov.cn", "npc.gov.cn", "court.gov.cn", "mofcom.gov.cn", "samr.gov.cn",
    "cac.gov.cn", "moj.gov.cn", "mps.gov.cn", "mohrss.gov.cn", "mee.gov.cn",
    "chinatax.gov.cn", "customs.gov.cn", "pbc.gov.cn", "csrc.gov.cn",
)
PRIMARY_PUBLIC_DOMAINS = (
    "cninfo.com.cn", "sse.com.cn", "szse.cn", "hkex.com.hk",
)
TRUSTED_MEDIA_DOMAINS = (
    "reuters.com", "bloomberg.com", "cls.cn", "yicai.com", "caixin.com",
)

REALTIME_MARKERS = tuple(
    "\u6700\u65b0 \u5f53\u524d \u76ee\u524d \u8fd1\u671f \u6700\u8fd1 \u4eca\u5929 \u4eca\u65e5 \u622a\u81f3 \u5f53\u524d\u6709\u6548 \u751f\u6548 \u516c\u544a \u65b0\u89c4 \u653f\u7b56 \u52a8\u6001 \u65b0\u95fb \u5904\u7f5a \u76d1\u7ba1 \u80a1\u4ef7 \u5e02\u573a \u878d\u8d44 \u4e0a\u5e02 \u98ce\u9669\u4e8b\u4ef6 \u8fd1\u671f \u53d1\u751f".split()
)
EXPLICIT_LOOKUP_MARKERS = tuple(
    "\u68c0\u7d22 \u67e5\u8be2 \u67e5\u627e \u641c\u7d22 \u67e5\u4e00\u4e0b \u8bf7\u67e5 \u5e2e\u6211\u67e5 \u5b98\u7f51 \u539f\u6587 \u51fa\u5904 \u6765\u6e90 \u94fe\u63a5 \u88c1\u5224\u6587\u4e66 \u5224\u4f8b".split()
)
LEGAL_REFERENCE_MARKERS = tuple(
    "\u6cd5\u5f8b \u6cd5\u89c4 \u6cd5\u6761 \u53f8\u6cd5\u89e3\u91ca \u884c\u653f\u89c4\u7ae0 \u89c4\u8303\u6027\u6587\u4ef6 \u76d1\u7ba1 \u5904\u7f5a \u653f\u7b56 \u6c11\u6cd5\u5178 \u5211\u6cd5 \u516c\u53f8\u6cd5 \u52b3\u52a8\u6cd5 \u4e2a\u4eba\u4fe1\u606f\u4fdd\u62a4\u6cd5 \u6570\u636e\u5b89\u5168\u6cd5 \u53cd\u5784\u65ad\u6cd5 \u5408\u540c\u6cd5 \u5408\u89c4 \u8fdd\u6cd5 \u4fb5\u6743 \u8bc9\u8bbc \u4ef2\u88c1".split()
)

RECENT_RISK_OVERVIEW_TIME_MARKERS = ("最近", "近期", "当前", "目前")
RECENT_RISK_OVERVIEW_RISK_MARKERS = ("风险事项", "风险", "风险点", "需要注意", "需注意", "关注事项")


@dataclass(frozen=True)
class SearchProviderStatus:
    provider_id: str
    enabled: bool
    message: str
    runtime_access: str = "not_called"


class WebSearchProvider(Protocol):
    provider_id: str

    def search(self, query: str, *, max_results: int, allowed_domains: tuple[str, ...]) -> list[WebSearchResult]:
        ...

    def status(self) -> SearchProviderStatus:
        ...


class _DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._field: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            self._current = {"url": attributes.get("href") or "", "title": ""}
            self._field = "title"
        elif self._current is not None and "result__snippet" in classes:
            self._field = "snippet"

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current is not None and self._field == "title":
            self.results.append(self._current)
            self._current = None
            self._field = None

    def handle_data(self, data: str) -> None:
        if self._current is not None and self._field:
            self._current[self._field] = self._current.get(self._field, "") + data


class _BingResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._in_heading = False
        self._in_snippet = False
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "li" and "b_algo" in classes and self._current is None:
            self._current = {"url": "", "title": "", "snippet": ""}
            self._depth = 1
            return
        if self._current is None:
            return
        self._depth += 1
        if tag == "h2":
            self._in_heading = True
        elif tag == "a" and self._in_heading and not self._current["url"]:
            self._current["url"] = attributes.get("href") or ""
        elif "b_caption" in classes or tag == "p":
            self._in_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return
        if tag == "h2":
            self._in_heading = False
        if tag == "p":
            self._in_snippet = False
        self._depth -= 1
        if tag == "li" and self._depth <= 0:
            if self._current["url"] and self._current["title"]:
                self.results.append(self._current)
            self._current = None
            self._in_heading = False
            self._in_snippet = False
            self._depth = 0

    def handle_data(self, data: str) -> None:
        if self._current is None:
            return
        if self._in_heading:
            self._current["title"] += data
        elif self._in_snippet:
            self._current["snippet"] += data


class DuckDuckGoHtmlProvider:
    provider_id = "duckduckgo_html"

    def __init__(self, config: ExternalRiskProviderConfig, *, opener: Any | None = None) -> None:
        self.config = config
        self._opener = opener or urllib.request.urlopen
        self._runtime_access = "not_called"
        self._last_error = ""

    def status(self) -> SearchProviderStatus:
        return SearchProviderStatus(
            provider_id=self.provider_id,
            enabled=self.config.web_search_enabled,
            message=(self._last_error or ("ready" if self.config.web_search_enabled else "disabled by configuration")),
            runtime_access=self._runtime_access,
        )

    def search(self, query: str, *, max_results: int, allowed_domains: tuple[str, ...]) -> list[WebSearchResult]:
        if not self.config.web_search_enabled:
            return []
        params = urllib.parse.urlencode({"q": query, "kl": "cn-zh"})
        request = urllib.request.Request(
            f"https://html.duckduckgo.com/html/?{params}",
            headers={"User-Agent": "LegalRiskCheck/0.6 (+controlled-search)"},
        )
        self._runtime_access = "live_called"
        with self._opener(request, timeout=self.config.web_search_timeout_seconds) as response:
            raw = response.read(512_000).decode("utf-8", errors="replace")
            if getattr(response, "status", 200) == 202 or "challenge" in raw.lower():
                self._last_error = "provider returned a bot challenge"
                raise RuntimeError(self._last_error)
        parser = _DuckDuckGoParser()
        parser.feed(raw)
        fetched_at = _utc_now_iso()
        results: list[WebSearchResult] = []
        for item in parser.results:
            url = _normalize_result_url(item.get("url", ""))
            if not url or not _domain_allowed(url, allowed_domains):
                continue
            title = _clean_text(item.get("title", ""))
            snippet = _clean_text(item.get("snippet", ""))
            if not title or not url:
                continue
            results.append(
                WebSearchResult(
                    title=title[:240],
                    url=url,
                    snippet=snippet[:1200],
                    source_name=_registrable_domain(url),
                    source_tier=classify_source_tier(url),
                    trust_score=source_trust_score(url),
                    fetched_at=fetched_at,
                )
            )
            if len(results) >= max_results:
                break
        return results


class BingHtmlProvider:
    provider_id = "bing_html"

    def __init__(self, config: ExternalRiskProviderConfig, *, opener: Any | None = None) -> None:
        self.config = config
        self._opener = opener or urllib.request.urlopen
        self._runtime_access = "not_called"
        self._last_error = ""

    def status(self) -> SearchProviderStatus:
        return SearchProviderStatus(
            provider_id=self.provider_id,
            enabled=self.config.web_search_enabled,
            message=(self._last_error or ("ready" if self.config.web_search_enabled else "disabled by configuration")),
            runtime_access=self._runtime_access,
        )

    def search(self, query: str, *, max_results: int, allowed_domains: tuple[str, ...]) -> list[WebSearchResult]:
        if not self.config.web_search_enabled:
            return []
        params = urllib.parse.urlencode({"q": query, "setlang": "zh-hans"})
        request = urllib.request.Request(
            f"https://www.bing.com/search?{params}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )
        self._runtime_access = "live_called"
        try:
            with self._opener(request, timeout=self.config.web_search_timeout_seconds) as response:
                raw = response.read(512_000).decode("utf-8", errors="replace")
            parser = _BingResultParser()
            parser.feed(raw)
        except Exception as exc:
            self._last_error = f"provider request failed: {exc.__class__.__name__}"
            raise
        fetched_at = _utc_now_iso()
        results: list[WebSearchResult] = []
        for item in parser.results:
            url = _normalize_result_url(item.get("url", ""))
            if not url or not _domain_allowed(url, allowed_domains):
                continue
            title = _clean_text(item.get("title", ""))
            if not title:
                continue
            results.append(WebSearchResult(
                title=title[:240],
                url=url,
                snippet=_clean_text(item.get("snippet", ""))[:1200],
                source_name=_registrable_domain(url),
                source_tier=classify_source_tier(url),
                trust_score=source_trust_score(url),
                fetched_at=fetched_at,
            ))
            if len(results) >= max_results:
                break
        return results


class TavilySearchProvider:
    """API-backed provider intended for stable production-like demonstrations."""

    provider_id = "tavily_api"

    def __init__(self, config: ExternalRiskProviderConfig, *, opener: Any | None = None) -> None:
        self.config = config
        self._opener = opener or urllib.request.urlopen
        self._runtime_access = "not_called"
        self._last_error = ""

    def status(self) -> SearchProviderStatus:
        enabled = self.config.web_search_enabled and bool(self.config.web_search_api_key)
        message = self._last_error or ("ready" if enabled else "requires EXTERNAL_RISK_WEB_SEARCH_API_KEY")
        return SearchProviderStatus(
            provider_id=self.provider_id,
            enabled=enabled,
            message=message,
            runtime_access=self._runtime_access,
        )

    def search(self, query: str, *, max_results: int, allowed_domains: tuple[str, ...]) -> list[WebSearchResult]:
        if not self.config.web_search_enabled or not self.config.web_search_api_key:
            return []
        payload = {
            "api_key": self.config.web_search_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_domains": list(allowed_domains) or None,
            "include_answer": False,
            "include_raw_content": False,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.tavily.com/search",
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "LegalRiskCheck/0.6"},
            method="POST",
        )
        self._runtime_access = "live_called"
        try:
            with self._opener(request, timeout=self.config.web_search_timeout_seconds) as response:
                raw = response.read(512_000).decode("utf-8", errors="replace")
            data = json.loads(raw)
        except Exception as exc:
            self._last_error = f"provider request failed: {exc.__class__.__name__}"
            raise
        records = data.get("results") if isinstance(data, dict) else []
        fetched_at = _utc_now_iso()
        results: list[WebSearchResult] = []
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict):
                continue
            url = _normalize_result_url(str(record.get("url") or ""))
            if not url or not _domain_allowed(url, allowed_domains):
                continue
            title = _clean_text(str(record.get("title") or ""))
            if not title:
                continue
            results.append(WebSearchResult(
                title=title[:240],
                url=url,
                snippet=_clean_text(str(record.get("content") or ""))[:1200],
                source_name=_registrable_domain(url),
                source_tier=classify_source_tier(url),
                trust_score=source_trust_score(url),
                published_at=_optional_text(record.get("published_date")),
                fetched_at=fetched_at,
            ))
        return results[:max_results]


class OnlineSearchService:
    def __init__(
        self,
        config: ExternalRiskProviderConfig | None = None,
        *,
        provider: WebSearchProvider | None = None,
    ) -> None:
        self.config = config or load_provider_config()
        self.provider = provider or self._build_provider()

    def _build_provider(self) -> WebSearchProvider:
        provider = self.config.web_search_provider.strip().lower()
        if provider == "tavily":
            return TavilySearchProvider(self.config)
        if provider == "duckduckgo_html":
            return DuckDuckGoHtmlProvider(self.config)
        return BingHtmlProvider(self.config)

    def status(self) -> SearchProviderStatus:
        return self.provider.status()

    def plan(
        self,
        question: str,
        *,
        mode: str = "auto",
        domain: SearchDomain = "general",
        max_results: int | None = None,
    ) -> WebSearchPlan:
        intent, trigger = classify_search_intent(question, domain=domain)
        should_search = mode == "force" or (mode == "auto" and intent != "none")
        queries = build_search_queries(question, intent) if should_search else []
        policy_domain = _infer_search_domain(question, requested_domain=domain, intent=intent)
        allowed_domains = allowed_domains_for(policy_domain)
        return WebSearchPlan(
            mode=mode, intent=intent, trigger=trigger, queries=queries,
            allowed_domains=list(allowed_domains), max_results=max_results or self.config.web_search_max_results,
            should_search=should_search, requires_human_review=should_search,
        )

    def search(self, plan: WebSearchPlan) -> list[WebSearchResult]:
        if not plan.should_search or not self.config.web_search_enabled:
            return []
        results: list[WebSearchResult] = []
        for query in plan.queries[:3]:
            try:
                results.extend(self.provider.search(
                    query, max_results=plan.max_results, allowed_domains=tuple(plan.allowed_domains)
                ))
            except Exception:
                continue
        return dedupe_results(results)[: plan.max_results]


def classify_search_intent(question: str, *, domain: SearchDomain = "general") -> tuple[SearchIntent, str]:
    text = str(question or "").strip().lower()
    if not text:
        return "none", "empty_question"
    is_legal = domain in {"legal", "regulatory"} or any(term in text for term in LEGAL_REFERENCE_MARKERS)
    if any(marker in text for marker in EXPLICIT_LOOKUP_MARKERS):
        if is_legal:
            return "legal_reference", "explicit_source_lookup"
        return "general_realtime", "explicit_web_lookup"
    if not any(marker in text for marker in REALTIME_MARKERS):
        return "none", "no_realtime_marker"
    if is_recent_risk_overview_question(question):
        return "general_realtime", "recent_risk_overview"
    if is_legal:
        return "legal_update", "legal_or_regulatory_fact"
    if domain == "market" or any(term in text for term in ("\u80a1\u4ef7", "\u5e02\u573a", "\u80a1\u7968", "\u884c\u4e1a")):
        return "market_event", "market_fact"
    if domain == "company" or any(term in text for term in ("\u516c\u53f8", "\u4f01\u4e1a", "\u878d\u8d44", "\u4e0a\u5e02")):
        return "company_event", "company_fact"
    return "general_realtime", "explicit_realtime_marker"


def is_recent_risk_overview_question(question: str) -> bool:
    """Identify broad requests for time-sensitive risk observations.

    These requests ask for an external fact snapshot, rather than a legal
    determination.  Keeping the classifier narrow prevents ordinary legal
    risk questions from bypassing the evidence gate.
    """
    text = str(question or "").strip().lower()
    return bool(text) and any(marker in text for marker in RECENT_RISK_OVERVIEW_TIME_MARKERS) and any(
        marker in text for marker in RECENT_RISK_OVERVIEW_RISK_MARKERS
    )


def should_search_for_retrieval_gap(
    result: dict[str, Any],
    *,
    question: str,
    domain: SearchDomain = "general",
) -> bool:
    """Promote only an evidenced local retrieval gap to controlled web search."""
    if not str(question or "").strip():
        return False
    if is_recent_risk_overview_question(question):
        return True
    if domain in {"legal", "regulatory", "market", "company"}:
        scoped_question = True
    else:
        text = str(question).lower()
        scoped_question = any(term in text for term in LEGAL_REFERENCE_MARKERS)
    if not scoped_question:
        return False
    sufficiency = result.get("evidence_sufficiency")
    if isinstance(sufficiency, dict) and sufficiency.get("recommended_route") == "web_supplement":
        return True
    if list(result.get("missing_evidence") or []):
        return True
    try:
        confidence = float(result.get("retrieval_confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    return confidence < 0.65 and not bool(result.get("evidence_chain"))


def _infer_search_domain(
    question: str,
    *,
    requested_domain: SearchDomain,
    intent: SearchIntent,
) -> SearchDomain:
    if requested_domain != "general":
        return requested_domain
    text = str(question or "").lower()
    if intent in {"legal_update", "legal_reference"} or any(term in text for term in LEGAL_REFERENCE_MARKERS):
        return "legal"
    if intent == "market_event" or any(term in text for term in ("\u80a1\u4ef7", "\u5e02\u573a", "\u80a1\u7968", "\u884c\u4e1a")):
        return "market"
    if intent == "company_event" or any(term in text for term in ("\u516c\u53f8", "\u4f01\u4e1a", "\u878d\u8d44", "\u4e0a\u5e02")):
        return "company"
    return "general"


def build_search_queries(question: str, intent: SearchIntent) -> list[str]:
    suffix = {
        "legal_update": "官方 现行 有效 条文 公告",
        "market_event": "公告 新闻 数据",
        "company_event": "公告 新闻 监管",
        "general_realtime": "最新 信息",
        "none": "",
    }.get(intent, "")
    query = f"{str(question).strip()} {suffix}".strip()
    return [query[:240]] if query else []


def allowed_domains_for(domain: SearchDomain) -> tuple[str, ...]:
    if domain in {"legal", "regulatory"}:
        return OFFICIAL_DOMAINS
    if domain in {"market", "company"}:
        return PRIMARY_PUBLIC_DOMAINS + TRUSTED_MEDIA_DOMAINS
    return ()


def classify_source_tier(url: str) -> str:
    host = urllib.parse.urlparse(url).hostname or ""
    if _host_matches(host, OFFICIAL_DOMAINS):
        return "official"
    if _host_matches(host, PRIMARY_PUBLIC_DOMAINS):
        return "primary_public"
    if _host_matches(host, TRUSTED_MEDIA_DOMAINS):
        return "trusted_media"
    return "unverified_web"


def source_trust_score(url: str) -> float:
    return {"official": 1.0, "primary_public": 0.9, "trusted_media": 0.75, "unverified_web": 0.35}[classify_source_tier(url)]


def dedupe_results(results: list[WebSearchResult]) -> list[WebSearchResult]:
    seen: set[str] = set()
    output: list[WebSearchResult] = []
    for result in sorted(results, key=lambda item: (-item.trust_score, item.url)):
        if result.url in seen:
            continue
        seen.add(result.url)
        output.append(result)
    return output


def search_results_to_evidence(results: list[WebSearchResult]) -> list[dict[str, Any]]:
    """Convert search results into explicitly non-statutory evidence records."""
    evidence: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        source_tier = classify_source_tier(result.url)
        trust_score = source_trust_score(result.url)
        evidence.append({
            "source": result.url,
            "law_name": result.source_name,
            "document_type": "web_search_result",
            "type": "web_result",
            "block_type": "external_web_evidence",
            "law_level": "unknown",
            "authority_level": source_tier,
            "jurisdiction": "unknown",
            "issuing_authority": result.source_name,
            "legal_effect": "unknown",
            "standard_type": None,
            "case_type": None,
            "patent_type": None,
            "chapter": "",
            "section": "",
            "article": "",
            "article_no": "",
            "section_no": "",
            "section_title": result.title,
            "section_level": 0,
            "appendix": "",
            "chunk_index": index,
            "chunk_count": len(results),
            "paragraph_no": index,
            "item_no": "",
            "item_label": "",
            "citation": f"[网页来源：{result.title}]",
            "content": f"{result.title}\n{result.snippet}\nURL: {result.url}\n抓取时间: {result.fetched_at or 'unknown'}",
            "source_tier": source_tier,
            "trust_score": trust_score,
        })
    return evidence


def _normalize_result_url(value: str) -> str:
    url = html.unescape(str(value or "")).strip()
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    if "duckduckgo.com/l/" in url:
        target = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
        return _normalize_result_url(urllib.parse.unquote(target))
    return url


def _domain_allowed(url: str, allowed_domains: tuple[str, ...]) -> bool:
    if not allowed_domains:
        return True
    host = urllib.parse.urlparse(url).hostname or ""
    return _host_matches(host, allowed_domains)


def _host_matches(host: str, domains: tuple[str, ...]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == domain or host.endswith("." + domain) for domain in domains)


def _registrable_domain(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
