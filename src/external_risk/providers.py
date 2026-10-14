from __future__ import annotations

import importlib
import importlib.util
import json
import re
import urllib.request
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from src.external_risk.provider_config import ExternalRiskProviderConfig, load_provider_config
from src.external_risk.commodity_catalog import CATALOG_BY_SYMBOL, COMMODITY_FUTURES, catalog_display_name
from src.external_risk.intelligence import NewsPolicyRssExternalRiskProvider
from src.external_risk.schemas import ExternalRiskProviderStatus, ExternalRiskQuotePoint, ExternalRiskSignal


class ExternalSignalProvider(Protocol):
    provider_id: str
    provider_type: str

    def status(self) -> ExternalRiskProviderStatus:
        ...

    def live_signals(
        self,
        *,
        signal_type: str | None = None,
        symbol: str | None = None,
        commodity_group: str | None = None,
    ) -> list[ExternalRiskSignal]:
        ...


@dataclass(frozen=True)
class NormalizedMarketObservation:
    provider_id: str
    entity: str
    title: str
    metric: str
    value: float
    threshold: float
    source: str
    as_of: str
    lookback_days: int
    affected_domains: tuple[str, ...]
    metadata: dict[str, Any] | None = None


class AkShareExternalRiskProvider:
    provider_id = "akshare_live_provider"
    provider_type = "market"

    def __init__(
        self,
        config: ExternalRiskProviderConfig | None = None,
        *,
        module_loader: Any | None = None,
    ) -> None:
        self.config = config or load_provider_config()
        self._module_loader = module_loader or importlib.import_module
        self._last_runtime_access = "not_called"

    def status(self) -> ExternalRiskProviderStatus:
        status = akshare_status(self.config)
        return status.model_copy(update={"runtime_access": self._last_runtime_access})

    def live_signals(
        self,
        *,
        signal_type: str | None = None,
        symbol: str | None = None,
        commodity_group: str | None = None,
    ) -> list[ExternalRiskSignal]:
        resolved_type = signal_type or "market"
        if not self.config.akshare_live_enabled:
            self._last_runtime_access = "not_called"
            return []
        if self._module_loader is importlib.import_module and importlib.util.find_spec("akshare") is None:
            self._last_runtime_access = "not_called"
            return []
        try:
            self._last_runtime_access = "live_called"
            akshare_module = self._module_loader("akshare")
            observation = self._fetch_observation(
                akshare_module,
                signal_type=resolved_type,
                symbol=symbol,
                commodity_group=commodity_group,
            )
        except Exception:
            return []
        if observation is None:
            return []
        if resolved_type == "commodity_futures":
            group = commodity_group or symbol or "commodity"
            return [
                commodity_observation_to_signal(
                    observation,
                    commodity_group=group,
                    affected_supply_links=(group,),
                )
            ]
        return [market_observation_to_signal(observation)]

    def _fetch_observation(
        self,
        akshare_module: Any,
        *,
        signal_type: str,
        symbol: str | None,
        commodity_group: str | None,
    ) -> NormalizedMarketObservation | None:
        function_name = (
            self.config.akshare_commodity_function
            if signal_type == "commodity_futures"
            else self.config.akshare_market_function
        )
        fetcher = getattr(akshare_module, function_name)
        raw = _call_akshare_fetcher(fetcher, symbol=symbol)
        records = _records_from_result(raw)
        move = _signed_move_from_records(records)
        if move is None:
            return None
        entity = symbol or commodity_group or function_name
        threshold = 0.05 if signal_type == "commodity_futures" else 0.07
        domains = ("supply_chain", "contract") if signal_type == "commodity_futures" else ("market", "disclosure")
        return NormalizedMarketObservation(
            provider_id=self.provider_id,
            entity=entity,
            title=f"{entity} live {self.config.default_lookback_days}d move",
            metric=f"{self.config.default_lookback_days}d_return",
            value=move,
            threshold=threshold,
            source=f"akshare.{function_name}",
            as_of=utc_now_iso(),
            lookback_days=self.config.default_lookback_days,
            affected_domains=domains,
        )


class TencentHttpExternalRiskProvider:
    provider_id = "tencent_http_provider"
    provider_type = "market"

    market_symbols = ("sh000001", "sz399001", "sz399006")
    sector_symbols = (
        "bk_BK1326",
        "bk_BK0457",
        "bk_BK1215",
        "bk_BK1590",
        "bk_BK1203",
        "bk_BK1037",
        "bk_BK1128",
        "bk_BK0877",
        "bk_BK1178",
        "bk_BK1164",
        "bk_BK1162",
        "bond_000012",
    )
    us_symbols = (
        "us_NDX",
        "us_SPX",
        "us_AAPL",
        "us_NVDA",
        "us_TSLA",
        "us_MSFT",
        "us_BABA",
        "us_GLW",
        "us_MU",
        "us_WDC",
        "us_SNDK",
    )
    commodity_symbols = tuple(item.symbol for item in COMMODITY_FUTURES)

    def __init__(
        self,
        config: ExternalRiskProviderConfig | None = None,
        *,
        fetcher: Any | None = None,
    ) -> None:
        self.config = config or load_provider_config()
        self._fetcher = fetcher or self._default_fetcher
        self._last_runtime_access = "not_called"

    def status(self) -> ExternalRiskProviderStatus:
        if not self.config.live_enabled:
            status = "not_configured"
            mode = "disabled"
            message = "HTTP market provider is ready. EXTERNAL_RISK_LIVE_ENABLED is not enabled."
        elif not self.config.http_enabled:
            status = "not_configured"
            mode = "disabled"
            message = "HTTP market provider is ready. EXTERNAL_RISK_HTTP_ENABLED is not enabled."
        else:
            status = "available"
            mode = "live"
            message = "HTTP market provider can read Tencent quote endpoints."
        return ExternalRiskProviderStatus(
            provider_id=self.provider_id,
            provider_type="market",
            status=status,  # type: ignore[arg-type]
            mode=mode,  # type: ignore[arg-type]
            message=message,
            runtime_access=self._last_runtime_access,
        )

    def live_signals(
        self,
        *,
        signal_type: str | None = None,
        symbol: str | None = None,
        commodity_group: str | None = None,
    ) -> list[ExternalRiskSignal]:
        if not self.config.http_live_enabled:
            self._last_runtime_access = "not_called"
            return []
        resolved_type = signal_type or "all"
        symbols = _resolve_tencent_symbols(
            resolved_type=resolved_type,
            symbol=symbol,
            commodity_group=commodity_group,
            market_symbols=self.market_symbols,
            sector_symbols=self.sector_symbols,
            commodity_symbols=self.commodity_symbols,
        )
        if not symbols:
            return []
        self._last_runtime_access = "live_called"
        tencent_symbols = tuple(item for item in symbols if not item.startswith(("bk_", "bond_")))
        sector_symbols = tuple(item for item in symbols if item.startswith(("bk_", "bond_")))
        observations: list[NormalizedMarketObservation] = []
        if tencent_symbols:
            try:
                raw = self._fetcher(tencent_symbols)
                observations.extend(parse_tencent_quote_observations(raw, provider_id=self.provider_id))
            except Exception:
                if not sector_symbols:
                    return []
        if sector_symbols:
            try:
                observations.extend(self._fetch_eastmoney_observations(sector_symbols))
            except Exception:
                pass
        signals: list[ExternalRiskSignal] = []
        for observation in observations:
            if observation.metadata.get("signal_type") == "commodity_futures":
                group = str(observation.metadata.get("commodity_group") or observation.entity)
                signals.append(
                    commodity_observation_to_signal(
                        observation,
                        commodity_group=group,
                        affected_supply_links=(group,),
                    )
                )
            else:
                signals.append(market_observation_to_signal(observation))
        return signals

    def _default_fetcher(self, symbols: tuple[str, ...]) -> str:
        query = ",".join(symbols)
        url = f"https://qt.gtimg.cn/q={query}"
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
            return response.read().decode("gbk", errors="replace")

    def quote_name(self, symbol: str) -> str | None:
        candidates = [symbol]
        if symbol.startswith("us_"):
            candidates.insert(0, f"us{symbol.removeprefix('us_')}")
        try:
            raw = self._fetcher(tuple(candidates))
        except Exception:
            return None
        return parse_tencent_quote_name(raw, symbol=symbol)

    def _fetch_eastmoney_observations(self, symbols: tuple[str, ...]) -> list[NormalizedMarketObservation]:
        observations: list[NormalizedMarketObservation] = []
        for symbol in symbols:
            observation: NormalizedMarketObservation | None = None
            try:
                observation = self._eastmoney_snapshot_observation(symbol)
            except Exception:
                try:
                    observation = self._eastmoney_observation_from_intraday(symbol)
                except Exception:
                    observation = None
            if observation is not None:
                observations.append(observation)
        return observations

    def _eastmoney_snapshot_observation(self, symbol: str) -> NormalizedMarketObservation | None:
        secid = _eastmoney_secid(symbol)
        if not secid:
            return None
        raw = self._fetch_eastmoney_snapshot_raw(secid)
        return parse_eastmoney_quote_observation(raw, symbol=symbol, provider_id=self.provider_id)

    def _fetch_eastmoney_snapshot_raw(self, secid: str) -> str:
        query = (
            "ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2"
            f"&secids={secid}&fields=f12,f14,f2,f3,f4,f15,f16,f17,f18,f20,f21,f13,f124"
        )
        last_error: Exception | None = None
        for host in ("https://push2.eastmoney.com", "https://push2delay.eastmoney.com"):
            try:
                return _read_eastmoney_url(f"{host}/api/qt/ulist.np/get?{query}", timeout=self.config.http_timeout_seconds)
            except Exception as exc:
                last_error = exc
        fallback_query = (
            "ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2"
            f"&secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f59,f60,f86,f169,f170"
        )
        for host in ("https://push2delay.eastmoney.com", "https://push2.eastmoney.com"):
            try:
                return _read_eastmoney_url(f"{host}/api/qt/stock/get?{fallback_query}", timeout=self.config.http_timeout_seconds)
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error
        return ""

    def _eastmoney_observation_from_intraday(self, symbol: str) -> NormalizedMarketObservation | None:
        points = self._fetch_eastmoney_quote_series(symbol=symbol, interval="intraday")
        if not points:
            return None
        last = points[-1]
        baseline = next((point.baseline_price for point in points if point.baseline_price not in {None, 0}), None)
        if baseline in {None, 0}:
            baseline = points[0].close
        pct = (last.close - float(baseline)) / float(baseline)
        is_bond = symbol.startswith("bond_")
        return NormalizedMarketObservation(
            provider_id=self.provider_id,
            entity=symbol,
            title=f"{_eastmoney_display_name(symbol)} intraday move",
            metric="intraday_return",
            value=pct,
            threshold=0.002 if is_bond else 0.03,
            source="eastmoney.push2his",
            as_of=last.time,
            lookback_days=1,
            affected_domains=("market", "disclosure") if not is_bond else ("market", "contract"),
            metadata={
                "signal_type": "market",
                "quote_name": _eastmoney_display_name(symbol),
                "current": last.close,
                "previous": baseline,
            },
        )

    def quote_series(
        self,
        *,
        symbol: str = "sh000001",
        interval: str = "intraday",
    ) -> tuple[list[ExternalRiskQuotePoint], str]:
        if not self.config.http_live_enabled:
            return [], "provider_unavailable"
        try:
            self._last_runtime_access = "live_called"
            if symbol.startswith("hf_"):
                points = self._fetch_sina_commodity_series(symbol=symbol, interval=interval)
                if points:
                    return points, "sina_global_futures"
            if symbol.startswith("if_"):
                points = self._fetch_sina_cn_futures_series(symbol=symbol, interval=interval)
                if points:
                    return points, "sina_cn_futures"
            if symbol.startswith(("hk_", "kr_")):
                try:
                    points = self._fetch_yahoo_quote_series(symbol=symbol, interval=interval)
                    if points:
                        return points, "yahoo_chart"
                except Exception:
                    pass
                points = self._fetch_tencent_global_quote_series(symbol=symbol)
                if points:
                    return points, "live_provider"
            if symbol.startswith("us_"):
                try:
                    points = self._fetch_eastmoney_us_quote_series(symbol=symbol, interval=interval)
                    if points:
                        return points, "eastmoney_provider"
                except Exception:
                    pass
                try:
                    points = self._fetch_yahoo_quote_series(symbol=symbol, interval=interval)
                    if points:
                        return points, "yahoo_chart"
                except Exception:
                    pass
                points = self._fetch_tencent_global_quote_series(symbol=symbol)
                if points:
                    return points, "live_provider"
            if symbol.startswith(("bk_", "bond_")):
                points = self._fetch_eastmoney_quote_series(symbol=symbol, interval=interval)
                if points:
                    return points, "eastmoney_provider"
                return [], "provider_unavailable"
            raw = self._fetch_quote_series(symbol=symbol, interval=interval)
            points = parse_tencent_quote_series(raw, symbol=symbol, interval=interval)
            if points:
                return points, "live_provider"
        except Exception:
            if symbol.startswith(("hk_", "kr_")):
                try:
                    points = self._fetch_yahoo_quote_series(symbol=symbol, interval=interval)
                    if points:
                        return points, "yahoo_chart"
                except Exception:
                    pass
                points = self._fetch_tencent_global_quote_series(symbol=symbol)
                if points:
                    return points, "live_provider"
                return [], "provider_unavailable"
            if symbol.startswith("us_"):
                try:
                    points = self._fetch_yahoo_quote_series(symbol=symbol, interval=interval)
                    if points:
                        return points, "yahoo_chart"
                except Exception:
                    pass
                try:
                    points = self._fetch_tencent_global_quote_series(symbol=symbol)
                    if points:
                        return points, "live_provider"
                except Exception:
                    pass
                return [], "provider_unavailable"
            if symbol.startswith(("bk_", "bond_")):
                return [], "provider_unavailable"
            return [], "provider_unavailable"
        return [], "provider_unavailable"

    def _fetch_quote_series(self, *, symbol: str, interval: str) -> str:
        if interval == "intraday":
            url = (
                "https://web.ifzq.gtimg.cn/appstock/app/minute/query"
                f"?code={symbol}"
            )
        else:
            param = {"daily": "day", "weekly": "week", "monthly": "month"}.get(interval, "day")
            url = (
                "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
                f"?param={symbol},{param},,,120,qfq"
            )
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")

    def _fetch_tencent_global_quote_series(self, *, symbol: str) -> list[ExternalRiskQuotePoint]:
        """Return a real global-market snapshot when history APIs are blocked.

        Tencent's global endpoint exposes a delayed/latest quote even during a
        closed overseas session. It is intentionally one point, so callers can
        display the verified latest price without treating it as full history.
        """
        quote_symbol = _tencent_global_symbol(symbol)
        if not quote_symbol:
            return []
        raw = self._fetch_quote_series(symbol=quote_symbol, interval="intraday")
        return parse_tencent_global_quote_snapshot(raw, quote_symbol=quote_symbol)

    def _fetch_sina_commodity_series(self, *, symbol: str, interval: str) -> list[ExternalRiskQuotePoint]:
        sina_symbol = _sina_global_futures_symbol(symbol)
        if not sina_symbol:
            return []
        if interval == "intraday":
            url = (
                "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_"
                f"{sina_symbol}=/GlobalFuturesService.getGlobalFuturesMinLine?symbol={sina_symbol}"
            )
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            return parse_sina_global_futures_minute(raw)
        url = (
            "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_"
            f"{sina_symbol}=/GlobalFuturesService.getGlobalFuturesDailyKLine?symbol={sina_symbol}"
        )
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
        daily = parse_sina_global_futures_daily(raw)
        if interval == "daily":
            return daily[-180:]
        return aggregate_quote_points(daily, bucket_size=5 if interval == "weekly" else 21)[-160:]

    def _fetch_sina_cn_futures_series(self, *, symbol: str, interval: str) -> list[ExternalRiskQuotePoint]:
        sina_symbol = _sina_cn_futures_symbol(symbol)
        if not sina_symbol:
            return []
        if interval == "intraday":
            url = (
                "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_"
                f"{sina_symbol}=/InnerFuturesNewService.getMinLine?symbol={sina_symbol}"
            )
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            return parse_sina_cn_futures_minute(raw)
        url = (
            "https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_"
            f"{sina_symbol}=/InnerFuturesNewService.getDailyKLine?symbol={sina_symbol}"
        )
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
        daily = parse_sina_cn_futures_daily(raw)
        if interval == "daily":
            return daily[-180:]
        return aggregate_quote_points(daily, bucket_size=5 if interval == "weekly" else 21)[-160:]

    def _fetch_eastmoney_us_quote_series(self, *, symbol: str, interval: str) -> list[ExternalRiskQuotePoint]:
        secid = _eastmoney_us_secid(symbol)
        if not secid:
            return []
        if interval == "intraday":
            url = (
                "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
                f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7,f8"
                "&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&iscca=0&ndays=1"
            )
            raw = _read_eastmoney_url(url, timeout=self.config.http_timeout_seconds)
            return parse_eastmoney_trends(raw)
        klt = {"daily": "101", "weekly": "102", "monthly": "103"}.get(interval, "101")
        url = (
            "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
            f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt=1&beg=20200101&end=20500101&lmt=240"
        )
        raw = _read_eastmoney_url(url, timeout=self.config.http_timeout_seconds)
        return parse_eastmoney_klines(raw)

    def _fetch_yahoo_quote_series(self, *, symbol: str, interval: str) -> list[ExternalRiskQuotePoint]:
        yahoo_symbol = _yahoo_symbol(symbol)
        if not yahoo_symbol:
            return []
        if interval == "intraday":
            query_interval = "5m"
            range_values = ("1d", "5d")
        else:
            query_interval = {"daily": "1d", "weekly": "1wk", "monthly": "1mo"}.get(interval, "1d")
            range_values = ({"daily": "6mo", "weekly": "2y", "monthly": "5y"}.get(interval, "6mo"),)
        encoded = urllib.parse.quote(yahoo_symbol, safe="")
        last_points: list[ExternalRiskQuotePoint] = []
        for range_value in range_values:
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
                f"?range={range_value}&interval={query_interval}&includePrePost=false&events=history"
            )
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json,text/plain,*/*",
                },
            )
            with urllib.request.urlopen(request, timeout=self.config.http_timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            points = parse_yahoo_chart(raw, interval=interval)
            if interval != "intraday" or len(points) >= 12:
                return points
            last_points = points
        return last_points

    def _fetch_eastmoney_quote_series(self, *, symbol: str, interval: str) -> list[ExternalRiskQuotePoint]:
        secid = _eastmoney_secid(symbol)
        if not secid:
            return []
        if interval == "intraday":
            # Board trend requests are frequently rejected or delayed, while the
            # delayed detail feed provides the complete trading day as ticks.
            if symbol.startswith("bk_"):
                return self._fetch_eastmoney_sector_details_series(secid=secid)
            url = (
                "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
                f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7,f8"
                "&fields2=f51,f52,f53,f54,f55,f56,f57,f58&iscr=0&iscca=0&ndays=1"
            )
            try:
                raw = _read_eastmoney_url(url, timeout=self.config.http_timeout_seconds)
                points = parse_eastmoney_trends(raw)
                if points:
                    return points
            except Exception:
                pass
            return []
        klt = {"daily": "101", "weekly": "102", "monthly": "103"}.get(interval, "101")
        url = (
            "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
            f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt={klt}&fqt=1&beg=20200101&end=20500101&lmt=240"
        )
        raw = _read_eastmoney_url(url, timeout=self.config.http_timeout_seconds)
        return parse_eastmoney_klines(raw)

    def _fetch_eastmoney_sector_details_series(self, *, secid: str) -> list[ExternalRiskQuotePoint]:
        # The trend endpoint intermittently rejects board secids.  The delayed details
        # endpoint retains the full trading day as ticks; request enough rows to cover
        # the morning and afternoon sessions, then aggregate to minute bars.
        query = f"secid={secid}&fields1=f1,f2,f3,f4,f5&fields2=f51,f52,f53,f54,f55&pos=-8000"
        last_error: Exception | None = None
        for host in ("https://push2delay.eastmoney.com", "https://push2.eastmoney.com"):
            try:
                raw = _read_eastmoney_url(f"{host}/api/qt/stock/details/get?{query}", timeout=self.config.http_timeout_seconds)
                points = aggregate_eastmoney_sector_ticks(parse_eastmoney_details(raw))
                if _has_board_intraday_coverage(points):
                    return points
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error
        return []


class CompositeExternalSignalProvider:
    provider_id = "composite_external_signal_provider"
    provider_type = "market"

    def __init__(self, providers: list[ExternalSignalProvider]) -> None:
        self.providers = providers

    def status(self) -> ExternalRiskProviderStatus:
        statuses = [provider.status() for provider in self.providers]
        live_called = any(status.runtime_access == "live_called" for status in statuses)
        available = any(status.status == "available" for status in statuses)
        return ExternalRiskProviderStatus(
            provider_id=self.provider_id,
            provider_type="market",
            status="available" if available else "not_configured",
            mode="live" if available else "disabled",
            message="Composite provider runs enabled live providers and fails closed.",
            runtime_access="live_called" if live_called else "not_called",
        )

    def live_signals(
        self,
        *,
        signal_type: str | None = None,
        symbol: str | None = None,
        commodity_group: str | None = None,
    ) -> list[ExternalRiskSignal]:
        signals: list[ExternalRiskSignal] = []
        for provider in self.providers:
            try:
                signals.extend(
                    provider.live_signals(
                        signal_type=signal_type,
                        symbol=symbol,
                        commodity_group=commodity_group,
                    )
                )
            except Exception:
                continue
        return _dedupe_live_signals(signals)


def provider_statuses(
    config: ExternalRiskProviderConfig | None = None,
    *,
    intelligence_provider: NewsPolicyRssExternalRiskProvider | None = None,
) -> list[ExternalRiskProviderStatus]:
    config = config or load_provider_config()
    return [
        TencentHttpExternalRiskProvider(config).status(),
        akshare_status(
            config,
            provider_id="akshare_market_provider",
            provider_type="market",
            message="AkShare market provider slot is ready.",
        ),
        akshare_status(
            config,
            provider_id="akshare_commodity_futures_provider",
            provider_type="commodity_futures",
            message="AkShare commodity futures provider slot is ready.",
        ),
        (intelligence_provider or NewsPolicyRssExternalRiskProvider(config)).status(),
        ExternalRiskProviderStatus(
            provider_id="fixture_supply_chain_provider",
            provider_type="supply_chain",
            status="fixture_only",
            mode="fixture",
            message="Supply-chain data currently comes from fixture.",
            runtime_access="fixture_only",
        ),
        ExternalRiskProviderStatus(
            provider_id="fixture_company_profile_provider",
            provider_type="company_profile",
            status="fixture_only",
            mode="fixture",
            message="Tech-company profile currently comes from fixture.",
            runtime_access="fixture_only",
        ),
    ]


def akshare_status(
    config: ExternalRiskProviderConfig | None = None,
    *,
    provider_id: str = "akshare_live_provider",
    provider_type: str = "market",
    message: str = "AkShare provider slot is ready.",
) -> ExternalRiskProviderStatus:
    config = config or load_provider_config()
    if not config.live_enabled:
        return ExternalRiskProviderStatus(
            provider_id=provider_id,
            provider_type=provider_type,  # type: ignore[arg-type]
            status="not_configured",
            mode="disabled",
            message=f"{message} EXTERNAL_RISK_LIVE_ENABLED is not enabled.",
            required_package="akshare",
            runtime_access="not_called",
        )
    if not config.akshare_enabled:
        return ExternalRiskProviderStatus(
            provider_id=provider_id,
            provider_type=provider_type,  # type: ignore[arg-type]
            status="not_configured",
            mode="disabled",
            message=f"{message} EXTERNAL_RISK_AKSHARE_ENABLED is not enabled.",
            required_package="akshare",
            runtime_access="not_called",
        )
    available = importlib.util.find_spec("akshare") is not None
    return ExternalRiskProviderStatus(
        provider_id=provider_id,
        provider_type=provider_type,  # type: ignore[arg-type]
        status="available" if available else "unavailable",
        mode="live" if available else "disabled",
        message=message if available else f"{message} Optional package akshare is not installed.",
        required_package="akshare",
        runtime_access="not_called",
    )


def commodity_observation_to_signal(
    observation: NormalizedMarketObservation,
    *,
    commodity_group: str,
    affected_supply_links: tuple[str, ...],
) -> ExternalRiskSignal:
    severity = _severity_from_signed_move(observation.value, observation.threshold)
    metadata = _instrument_metadata(observation)
    label = str(metadata["instrument_label"])
    return ExternalRiskSignal(
        signal_id=f"live-{observation.provider_id}-{commodity_group}-{observation.metric}",
        signal_type="commodity_futures",
        title=f"{label} · \u65e5\u5185\u6da8\u8dcc",
        severity=severity,
        direction="negative" if observation.value >= observation.threshold else "neutral",
        as_of=observation.as_of,
        entity=observation.entity,
        metric=observation.metric,
        value=observation.value,
        threshold=observation.threshold,
        affected_domains=list(observation.affected_domains),
        affected_supply_links=list(affected_supply_links),
        evidence=(
            f"{label}\u5728 {observation.lookback_days} \u4e2a\u89c2\u5bdf\u5468\u671f\u5185\u53d8\u52a8 {observation.value:.2%}\uff1b"
            f"\u98ce\u9669\u9608\u503c\u4e3a {observation.threshold:.2%}\u3002"
        ),
        source=observation.source,
        confidence=0.65,
        metadata={
            **metadata,
            "commodity_group": commodity_group,
            "provider_id": observation.provider_id,
            "observation_periods": observation.lookback_days,
            "latest_price": metadata.get("latest_price", metadata.get("current")),
            "previous_close": metadata.get("previous_close", metadata.get("previous")),
            "contract": metadata.get("contract", metadata.get("instrument_code")),
        },
    )


def market_observation_to_signal(observation: NormalizedMarketObservation) -> ExternalRiskSignal:
    severity = _severity_from_signed_move(observation.value, observation.threshold)
    direction = "negative" if observation.value <= -abs(observation.threshold) else "neutral"
    metadata = _instrument_metadata(observation)
    label = str(metadata["instrument_label"])
    period = "\u65e5\u5185" if observation.metric == "intraday_return" else f"{observation.lookback_days}\u65e5"
    return ExternalRiskSignal(
        signal_id=f"live-{observation.provider_id}-{observation.entity}-{observation.metric}",
        signal_type="market",
        title=f"{label} · {period}\u6da8\u8dcc",
        severity=severity,
        direction=direction,
        as_of=observation.as_of,
        entity=observation.entity,
        metric=observation.metric,
        value=observation.value,
        threshold=observation.threshold,
        affected_domains=list(observation.affected_domains),
        affected_supply_links=[],
        evidence=(
            f"{label}\u5728 {observation.lookback_days} \u4e2a\u89c2\u5bdf\u5468\u671f\u5185\u53d8\u52a8 {observation.value:.2%}\uff1b"
            f"\u98ce\u9669\u9608\u503c\u4e3a {observation.threshold:.2%}\u3002"
        ),
        source=observation.source,
        confidence=0.65,
        metadata={**metadata, "provider_id": observation.provider_id},
    )


def _instrument_metadata(observation: NormalizedMarketObservation) -> dict[str, Any]:
    metadata = dict(observation.metadata or {})
    code = _standard_instrument_code(observation.entity)
    catalog_name = catalog_display_name(observation.entity)
    name = next(
        (
            str(candidate).strip()
            for candidate in (
                catalog_name,
                metadata.get("quote_name"),
                _instrument_display_name(observation.entity),
                observation.entity,
            )
            if _usable_instrument_name(candidate)
        ),
        observation.entity,
    )
    # Commodity symbols can be deceptively short (for example SI0 or NG).
    # Keep the venue in the name and use a separate standardized code rather
    # than allowing the provider's terse symbol to become the card title.
    label = f"{name} \u00b7 {code}" if catalog_name and code else f"{name}\uff08{code}\uff09" if code else name
    return {**metadata, "instrument_name": name, "instrument_code": code, "instrument_label": label}


def _standard_instrument_code(symbol: str) -> str:
    normalized = str(symbol or "").strip()
    mainland = re.fullmatch(r"(sh|sz|bj)(\d{6})", normalized, flags=re.IGNORECASE)
    if mainland:
        return f"{mainland.group(1).upper()}.{mainland.group(2)}"
    hong_kong = re.fullmatch(r"hk_(\d{1,5})", normalized, flags=re.IGNORECASE)
    if hong_kong:
        return f"HKEX.{hong_kong.group(1).zfill(5)}"
    korean = re.fullmatch(r"kr_(\d{6})", normalized, flags=re.IGNORECASE)
    if korean:
        return f"KRX.{korean.group(1)}"
    if normalized.lower().startswith("us_"):
        return f"US.{normalized.removeprefix('us_').upper()}"
    if normalized.lower().startswith("bk_"):
        return f"EM.{normalized.removeprefix('bk_').upper()}"
    if normalized.lower().startswith("bond_"):
        return f"CNI.{normalized.removeprefix('bond_')}"
    if normalized.lower().startswith("hf_"):
        return f"HF.{normalized.removeprefix('hf_').upper()}"
    if normalized in CATALOG_BY_SYMBOL:
        contract = CATALOG_BY_SYMBOL[normalized]
        return f"{contract.exchange}.{normalized.removeprefix('if_').upper()}"
    if normalized.lower().startswith("if_"):
        return f"CNF.{normalized.removeprefix('if_').upper()}"
    return normalized.upper()


def _instrument_display_name(symbol: str) -> str:
    catalog_name = catalog_display_name(symbol)
    if catalog_name:
        return catalog_name
    return {
        "sh000001": "\u4e0a\u8bc1\u6307\u6570", "sz399001": "\u6df1\u8bc1\u6210\u6307", "sz399006": "\u521b\u4e1a\u677f\u6307",
        "us_AAPL": "\u82f9\u679c", "us_NVDA": "\u82f1\u4f1f\u8fbe", "us_TSLA": "\u7279\u65af\u62c9", "us_MSFT": "\u5fae\u8f6f", "us_BABA": "\u963f\u91cc\u5df4\u5df4",
        "kr_005930": "\u4e09\u661f\u7535\u5b50", "kr_000660": "SK\u6d77\u529b\u58eb", "sz000725": "\u4eac\u4e1c\u65b9A", "sz000100": "TCL\u79d1\u6280",
        "sh600552": "\u51ef\u76db\u79d1\u6280", "sh600707": "\u5f69\u8679\u80a1\u4efd", "sh688981": "\u4e2d\u82af\u56fd\u9645", "sh688012": "\u4e2d\u5fae\u516c\u53f8",
        "sh688072": "\u62d3\u8346\u79d1\u6280", "sz300308": "\u4e2d\u9645\u65ed\u521b",
    }.get(symbol, _eastmoney_display_name(symbol))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_tencent_quote_observations(
    raw: str,
    *,
    provider_id: str = "tencent_http_provider",
) -> list[NormalizedMarketObservation]:
    observations: list[NormalizedMarketObservation] = []
    for match in re.finditer(r'v_([^=]+)="([^"]*)"', raw or ""):
        symbol = match.group(1)
        fields = match.group(2).split("~") if "~" in match.group(2) else match.group(2).split(",")
        observation = _tencent_index_observation(symbol, fields, provider_id=provider_id)
        if observation is None:
            observation = _tencent_commodity_observation(symbol, fields, provider_id=provider_id)
        if observation is not None:
            observations.append(observation)
    return observations


def parse_tencent_quote_name(raw: str, *, symbol: str) -> str | None:
    normalized = symbol.replace("us_", "us")
    for match in re.finditer(r'v_([^=]+)="([^"]*)"', raw or ""):
        quote_symbol = match.group(1)
        if quote_symbol == "pv_none_match":
            continue
        if quote_symbol.lower() not in {symbol.lower(), normalized.lower()}:
            continue
        payload = match.group(2)
        # Commodity rows are comma-delimited and their second field is the
        # percentage move, not a security name. Let the canonical catalog name
        # win instead of exposing a value such as "-0.15" as the card title.
        if quote_symbol.lower().startswith(("hf_", "if_")) and "~" not in payload:
            return None
        fields = payload.split("~") if "~" in payload else payload.split(",")
        if len(fields) > 1 and _usable_instrument_name(fields[1]):
            return fields[1].strip()
    return None


def _usable_instrument_name(value: object) -> bool:
    """Reject provider fields that are actually prices or percentage moves."""
    text = str(value or "").strip()
    if not text:
        return False
    return re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)%?", text) is None


def parse_tencent_quote_series(raw: str, *, symbol: str, interval: str) -> list[ExternalRiskQuotePoint]:
    payload = json.loads(raw)
    data = payload.get("data", {}).get(symbol, {})
    if interval == "intraday":
        rows = data.get("data", {}).get("data") or data.get("data", {}).get("points") or []
        quote_fields = data.get("qt", {}).get(symbol) or []
        previous_close = _safe_float(quote_fields[4] if len(quote_fields) > 4 else None)
        return _parse_tencent_minute_rows(rows, baseline=previous_close)
    key = {"daily": "qfqday", "weekly": "qfqweek", "monthly": "qfqmonth"}.get(interval)
    rows = (data.get(key) or data.get(key.replace("qfq", ""))) if key else []
    return _parse_tencent_kline_rows(rows or [])


def parse_tencent_global_quote_snapshot(raw: str, *, quote_symbol: str) -> list[ExternalRiskQuotePoint]:
    """Parse Tencent's global latest-quote response into a single chart point."""
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    data = payload.get("data", {}).get(quote_symbol, {})
    quote_fields = data.get("qt", {}).get(quote_symbol) or []
    if not isinstance(quote_fields, list):
        return []
    current = _safe_float(quote_fields[3] if len(quote_fields) > 3 else None)
    previous_close = _safe_float(quote_fields[4] if len(quote_fields) > 4 else None)
    if current is None or current <= 0:
        return []
    return [
        ExternalRiskQuotePoint(
            time=str(quote_fields[30] if len(quote_fields) > 30 and quote_fields[30] else utc_now_iso()),
            open=_safe_float(quote_fields[5] if len(quote_fields) > 5 else None),
            high=_safe_float(quote_fields[33] if len(quote_fields) > 33 else None),
            low=_safe_float(quote_fields[34] if len(quote_fields) > 34 else None),
            close=current,
            volume=_safe_float(quote_fields[6] if len(quote_fields) > 6 else None),
            pct_change=(current - previous_close) / previous_close if previous_close not in {None, 0} else None,
            baseline_price=previous_close,
        )
    ]


def parse_eastmoney_details(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = json.loads(raw)
    data = payload.get("data") or {}
    rows = data.get("details") or []
    baseline = _safe_float(data.get("prePrice"))
    points: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    for row in rows:
        parts = str(row).split(",")
        if len(parts) < 2:
            continue
        close = _safe_float(parts[1])
        if close is None:
            continue
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=str(parts[0]),
                close=close,
                volume=_safe_float(parts[2]) if len(parts) > 2 else None,
                pct_change=pct,
                baseline_price=baseline,
            )
        )
        previous_close = close
    return points


def aggregate_eastmoney_sector_ticks(points: list[ExternalRiskQuotePoint]) -> list[ExternalRiskQuotePoint]:
    """Convert Eastmoney board ticks to chart-ready A-share minute bars."""
    minute_bars: dict[str, ExternalRiskQuotePoint] = {}
    for point in points:
        label = str(point.time or "")
        match = re.fullmatch(r"(\d{2}):(\d{2})(?::\d{2})?", label)
        if not match:
            continue
        minute = int(match.group(1)) * 60 + int(match.group(2))
        if not (9 * 60 + 30 <= minute <= 11 * 60 + 30 or 13 * 60 <= minute <= 15 * 60):
            continue
        minute_label = f"{match.group(1)}:{match.group(2)}"
        existing = minute_bars.get(minute_label)
        if existing is None:
            minute_bars[minute_label] = ExternalRiskQuotePoint(
                time=minute_label,
                open=point.close,
                high=point.close,
                low=point.close,
                close=point.close,
                volume=point.volume,
                baseline_price=point.baseline_price,
            )
            continue
        existing.close = point.close
        existing.high = max(value for value in (existing.high, point.close) if value is not None)
        existing.low = min(value for value in (existing.low, point.close) if value is not None)
        existing.volume = (existing.volume or 0) + (point.volume or 0)
        if existing.baseline_price is None:
            existing.baseline_price = point.baseline_price

    result = sorted(minute_bars.values(), key=lambda item: item.time)
    previous_close: float | None = None
    for point in result:
        point.pct_change = None if previous_close in {None, 0} else (point.close - previous_close) / previous_close
        previous_close = point.close
    return result


def _has_board_intraday_coverage(points: list[ExternalRiskQuotePoint]) -> bool:
    """Never render a last-100-tick tail as a full-day board chart."""
    if len(points) < 12:
        return False
    start = str(points[0].time or "")
    return start <= "09:35"


def parse_sina_global_futures_minute(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = _json_from_jsonp(raw)
    rows = payload.get("minLine_1d", []) if isinstance(payload, dict) else []
    points: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    baseline = _safe_float(rows[0][1] if rows and isinstance(rows[0], list) and len(rows[0]) > 1 else None)
    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue
        time_label = str(row[4] if len(row) > 4 and ":" in str(row[4]) else row[0])
        close = _safe_float(row[1])
        if close is None:
            continue
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=time_label,
                close=close,
                volume=_safe_float(row[2]) if len(row) > 2 else None,
                pct_change=pct,
                baseline_price=baseline,
            )
        )
        previous_close = close
    return points


def parse_sina_global_futures_daily(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = _json_from_jsonp(raw)
    rows = payload if isinstance(payload, list) else []
    points: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        close = _safe_float(row.get("close"))
        if close is None:
            continue
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=str(row.get("date") or ""),
                open=_safe_float(row.get("open")),
                high=_safe_float(row.get("high")),
                low=_safe_float(row.get("low")),
                close=close,
                volume=_safe_float(row.get("volume")),
                pct_change=pct,
            )
        )
        previous_close = close
    return points


def parse_sina_cn_futures_minute(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = _json_from_jsonp(raw)
    rows = payload if isinstance(payload, list) else []
    points: list[ExternalRiskQuotePoint] = []
    baseline: float | None = None
    previous_close: float | None = None
    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue
        close = _safe_float(row[1])
        if close is None:
            continue
        if baseline is None:
            baseline = close
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=str(row[0]),
                close=close,
                volume=_safe_float(row[3]) if len(row) > 3 else None,
                pct_change=pct,
                baseline_price=baseline,
            )
        )
        previous_close = close
    return points


def parse_sina_cn_futures_daily(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = _json_from_jsonp(raw)
    rows = payload if isinstance(payload, list) else []
    points: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        close = _safe_float(row.get("c"))
        if close is None:
            continue
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=str(row.get("d") or ""),
                open=_safe_float(row.get("o")),
                high=_safe_float(row.get("h")),
                low=_safe_float(row.get("l")),
                close=close,
                volume=_safe_float(row.get("v")),
                pct_change=pct,
            )
        )
        previous_close = close
    return points


def parse_eastmoney_trends(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = json.loads(raw)
    rows = payload.get("data", {}).get("trends") or []
    previous_close = _safe_float(payload.get("data", {}).get("preClose"))
    baseline = previous_close
    points: list[ExternalRiskQuotePoint] = []
    last_close = previous_close
    for row in rows:
        parts = str(row).split(",")
        if len(parts) < 6:
            continue
        close = _safe_float(parts[2])
        if close is None:
            continue
        pct = None if last_close in {None, 0} else (close - last_close) / last_close
        points.append(
            ExternalRiskQuotePoint(
                time=str(parts[0]).split()[-1],
                open=_safe_float(parts[1]),
                close=close,
                high=_safe_float(parts[3]),
                low=_safe_float(parts[4]),
                volume=_safe_float(parts[5]),
                pct_change=pct,
                baseline_price=baseline,
            )
        )
        last_close = close
    return points


def parse_eastmoney_klines(raw: str) -> list[ExternalRiskQuotePoint]:
    payload = json.loads(raw)
    rows = payload.get("data", {}).get("klines") or []
    points: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    for row in rows:
        parts = str(row).split(",")
        if len(parts) < 6:
            continue
        close = _safe_float(parts[2])
        if close is None:
            continue
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=str(parts[0]),
                open=_safe_float(parts[1]),
                close=close,
                high=_safe_float(parts[3]),
                low=_safe_float(parts[4]),
                volume=_safe_float(parts[5]),
                pct_change=pct,
            )
        )
        previous_close = close
    return points


def parse_yahoo_chart(raw: str, *, interval: str) -> list[ExternalRiskQuotePoint]:
    payload = json.loads(raw)
    result = next(iter(payload.get("chart", {}).get("result") or []), {})
    timestamps = result.get("timestamp") or []
    quote = next(iter(result.get("indicators", {}).get("quote") or []), {})
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    previous_close = _safe_float(result.get("meta", {}).get("previousClose"))
    points: list[ExternalRiskQuotePoint] = []
    last_close: float | None = None
    dates = {
        datetime.fromtimestamp(int(stamp), timezone.utc).astimezone().strftime("%Y-%m-%d")
        for stamp in timestamps
        if _safe_float(stamp) is not None
    }
    include_date = interval == "intraday" and len(dates) > 1
    for index, stamp in enumerate(timestamps):
        close = _safe_float(closes[index] if index < len(closes) else None)
        if close is None:
            continue
        if interval == "intraday":
            label_format = "%m-%d %H:%M" if include_date else "%H:%M"
            local_time = datetime.fromtimestamp(int(stamp), timezone.utc).astimezone()
            label = local_time.strftime(label_format)
            baseline = previous_close
        else:
            label = datetime.fromtimestamp(int(stamp), timezone.utc).astimezone().strftime("%Y-%m-%d")
            baseline = None
        pct = None if last_close in {None, 0} else (close - last_close) / last_close
        points.append(
            ExternalRiskQuotePoint(
                time=label,
                timestamp=int(stamp),
                open=_safe_float(opens[index] if index < len(opens) else None),
                high=_safe_float(highs[index] if index < len(highs) else None),
                low=_safe_float(lows[index] if index < len(lows) else None),
                close=close,
                volume=_safe_float(volumes[index] if index < len(volumes) else None),
                pct_change=pct,
                baseline_price=baseline,
            )
        )
        last_close = close
    return points[-240:]


def parse_eastmoney_quote_observation(
    raw: str,
    *,
    symbol: str,
    provider_id: str,
) -> NormalizedMarketObservation | None:
    payload = json.loads(raw)
    data = payload.get("data") or {}
    if isinstance(data.get("diff"), list):
        data = next(iter(data.get("diff") or []), {})
    name = next(
        (
            str(candidate).strip()
            for candidate in (data.get("f58"), data.get("f14"), _instrument_display_name(symbol), symbol)
            if _usable_instrument_name(candidate)
        ),
        symbol,
    )
    pct = _safe_float(data.get("f170") if "f170" in data else data.get("f3"))
    current = _safe_float(data.get("f43") if "f43" in data else data.get("f2"))
    previous = _safe_float(data.get("f60") if "f60" in data else data.get("f18"))
    price_scale = _safe_float(data.get("f59"))
    if price_scale and price_scale > 0 and current is not None and abs(current) > 10000:
        divisor = 10**int(price_scale)
        current = current / divisor
        if previous is not None:
            previous = previous / divisor
    if pct is None and current is not None and previous not in {None, 0}:
        pct = (current - previous) / previous * 100
    if pct is None:
        return None
    as_of = _eastmoney_datetime(data.get("f86") if "f86" in data else data.get("f124")) or utc_now_iso()
    is_bond = symbol.startswith("bond_")
    threshold = 0.002 if is_bond else 0.03
    return NormalizedMarketObservation(
        provider_id=provider_id,
        entity=symbol,
        title=f"{name} intraday move",
        metric="intraday_return",
        value=pct / 100,
        threshold=threshold,
        source="eastmoney.push2",
        as_of=as_of,
        lookback_days=1,
        affected_domains=("market", "disclosure") if not is_bond else ("market", "contract"),
        metadata={
            "signal_type": "market",
            "quote_name": name,
            "current": current,
            "previous": previous,
        },
    )


def aggregate_quote_points(points: list[ExternalRiskQuotePoint], *, bucket_size: int) -> list[ExternalRiskQuotePoint]:
    aggregated: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    for start in range(0, len(points), bucket_size):
        bucket = points[start : start + bucket_size]
        if not bucket:
            continue
        open_price = next((point.open for point in bucket if point.open is not None), bucket[0].close)
        high = max(float(point.high if point.high is not None else point.close) for point in bucket)
        low = min(float(point.low if point.low is not None else point.close) for point in bucket)
        close = bucket[-1].close
        volume_values = [point.volume for point in bucket if point.volume is not None]
        volume = sum(volume_values) if volume_values else None
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        aggregated.append(
            ExternalRiskQuotePoint(
                time=bucket[-1].time,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                pct_change=pct,
            )
        )
        previous_close = close
    return aggregated


def _json_from_jsonp(raw: str) -> Any:
    text = str(raw or "").strip()
    start = text.find("(")
    end = text.rfind(")")
    if start < 0 or end <= start:
        return {}
    return json.loads(text[start + 1 : end])


def _parse_tencent_minute_rows(rows: list[Any], *, baseline: float | None = None) -> list[ExternalRiskQuotePoint]:
    points: list[ExternalRiskQuotePoint] = []
    previous_close: float | None = None
    resolved_baseline = baseline
    for row in rows:
        if isinstance(row, str):
            parts = row.split()
        elif isinstance(row, list):
            parts = [str(item) for item in row]
        else:
            continue
        if len(parts) < 2:
            continue
        close = _safe_float(parts[1])
        if close is None:
            continue
        if resolved_baseline is None:
            resolved_baseline = close
        pct = None if previous_close in {None, 0} else (close - previous_close) / previous_close
        points.append(
            ExternalRiskQuotePoint(
                time=_format_tencent_minute_label(parts[0]),
                close=close,
                volume=_safe_float(parts[2]) if len(parts) > 2 else None,
                pct_change=pct,
                baseline_price=resolved_baseline,
            )
        )
        previous_close = close
    return points


def _format_tencent_minute_label(value: str) -> str:
    label = str(value).strip()
    if len(label) == 4 and label.isdigit():
        return f"{label[:2]}:{label[2:]}"
    return label


def _parse_tencent_kline_rows(rows: list[Any]) -> list[ExternalRiskQuotePoint]:
    points: list[ExternalRiskQuotePoint] = []
    for row in rows:
        parts = row if isinstance(row, list) else str(row).split()
        if len(parts) < 5:
            continue
        open_price = _safe_float(parts[1])
        close = _safe_float(parts[2])
        high = _safe_float(parts[3])
        low = _safe_float(parts[4])
        if close is None:
            continue
        pct = None if open_price in {None, 0} else (close - open_price) / open_price
        points.append(
            ExternalRiskQuotePoint(
                time=str(parts[0]),
                open=open_price,
                close=close,
                high=high,
                low=low,
                volume=_safe_float(parts[5]) if len(parts) > 5 else None,
                pct_change=pct,
            )
        )
    return points


def _sina_global_futures_symbol(symbol: str) -> str | None:
    return {
        "hf_CAD": "CAD",
        "hf_AHD": "AHD",
        "hf_SI": "SI",
        "hf_GC": "GC",
        "hf_CL": "CL",
        "hf_NG": "NG",
        "hf_ZSD": "ZSD",
        "hf_NID": "NID",
        "hf_PBD": "PBD",
        "hf_SND": "SND",
        "hf_XPD": "XPD",
        "hf_XPT": "XPT",
        "hf_C": "C",
        "hf_S": "S",
        "hf_W": "W",
    }.get(symbol)


def _sina_cn_futures_symbol(symbol: str) -> str | None:
    if not re.fullmatch(r"if_[A-Za-z]{1,3}0", symbol):
        return None
    return symbol.removeprefix("if_").upper()


def _eastmoney_us_secid(symbol: str) -> str | None:
    return {
        "us_NDX": "100.NDX",
        "us_SPX": "100.SPX",
        "us_AAPL": "105.AAPL",
        "us_NVDA": "105.NVDA",
        "us_TSLA": "105.TSLA",
        "us_MSFT": "105.MSFT",
        "us_BABA": "106.BABA",
        "us_GLW": "106.GLW",
        "us_MU": "105.MU",
        "us_WDC": "105.WDC",
        "us_SNDK": "105.SNDK",
    }.get(symbol)


def _yahoo_symbol(symbol: str) -> str | None:
    if symbol.startswith("us_"):
        return symbol.removeprefix("us_").replace(".", "-").upper()
    hk_match = re.fullmatch(r"hk_(\d{1,5})", symbol, flags=re.IGNORECASE)
    if hk_match:
        code = hk_match.group(1).lstrip("0") or "0"
        return f"{code.zfill(4)}.HK"
    kr_match = re.fullmatch(r"kr_(\d{6})", symbol, flags=re.IGNORECASE)
    if kr_match:
        return f"{kr_match.group(1)}.KS"
    return None


def _tencent_global_symbol(symbol: str) -> str | None:
    if symbol.startswith("us_"):
        return f"us{symbol.removeprefix('us_').upper()}"
    hong_kong = re.fullmatch(r"hk_(\d{1,5})", symbol, flags=re.IGNORECASE)
    if hong_kong:
        return f"hk{hong_kong.group(1).zfill(5)}"
    korean = re.fullmatch(r"kr_(\d{6})", symbol, flags=re.IGNORECASE)
    if korean:
        return f"kr{korean.group(1)}"
    return None


def _eastmoney_secid(symbol: str) -> str | None:
    aliases = {
        "bk_BK1215": "BK1590",
    }
    symbol = aliases.get(symbol, symbol)
    if symbol.startswith("bk_"):
        return f"90.{symbol.removeprefix('bk_')}"
    if symbol == "bond_000012":
        return "1.000012"
    return None


def _eastmoney_display_name(symbol: str) -> str:
    return {
        "bk_BK1326": "半导体设备",
        "bk_BK0457": "电网设备",
        "bk_BK1215": "通信",
        "bk_BK1590": "通信设备",
        "bk_BK1203": "非银金融",
        "bk_BK1037": "消费电子",
        "bk_BK1128": "CPO概念",
        "bk_BK0877": "PCB",
        "bk_BK1178": "AI眼镜",
        "bk_BK1164": "AIPC",
        "bk_BK1162": "AI手机",
        "bond_000012": "国债指数",
    }.get(symbol, symbol)


def _eastmoney_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "close",
        "Referer": "https://quote.eastmoney.com/",
    }


def _read_eastmoney_url(url: str, *, timeout: float) -> str:
    try:
        import requests  # type: ignore[import-not-found]

        for trust_env in (False, True):
            session = requests.Session()
            session.trust_env = trust_env
            response = session.get(url, headers=_eastmoney_headers(), timeout=timeout)
            response.raise_for_status()
            return response.text
    except Exception:
        pass
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers=_eastmoney_headers())
    with opener.open(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _tencent_index_observation(
    symbol: str,
    fields: list[str],
    *,
    provider_id: str,
) -> NormalizedMarketObservation | None:
    if not symbol.startswith(("sh", "sz")) or len(fields) < 33:
        return None
    name = fields[1] or symbol
    pct = _safe_float(fields[32])
    current = _safe_float(fields[3])
    previous = _safe_float(fields[4])
    if pct is None and current is not None and previous not in {None, 0}:
        pct = (current - previous) / previous * 100
    if pct is None:
        return None
    return NormalizedMarketObservation(
        provider_id=provider_id,
        entity=symbol,
        title=f"{name} intraday move",
        metric="intraday_return",
        value=pct / 100,
        threshold=0.015,
        source="tencent.qt.gtimg.cn",
        as_of=_tencent_datetime(fields[30]) or utc_now_iso(),
        lookback_days=1,
        affected_domains=("market", "disclosure"),
        metadata={"signal_type": "market", "quote_name": name},
    )


def _tencent_commodity_observation(
    symbol: str,
    fields: list[str],
    *,
    provider_id: str,
) -> NormalizedMarketObservation | None:
    if not symbol.startswith("hf_") or len(fields) < 14:
        return None
    name = catalog_display_name(symbol) or (fields[13] or symbol)
    pct = _safe_float(fields[1])
    current = _safe_float(fields[0])
    previous = _safe_float(fields[7])
    if pct is None and current is not None and previous not in {None, 0}:
        pct = (current - previous) / previous * 100
    if pct is None:
        return None
    commodity_group = {
        "hf_CAD": "copper",
        "hf_AHD": "aluminum",
        "hf_SI": "silver",
        "hf_GC": "gold",
        "hf_CL": "wti_crude",
        "hf_NG": "natural_gas",
        "hf_ZSD": "zinc",
        "hf_NID": "nickel",
        "hf_PBD": "lead",
        "hf_SND": "tin",
        "hf_XPD": "palladium",
        "hf_XPT": "platinum",
        "hf_C": "corn",
        "hf_S": "soybean",
        "hf_W": "wheat",
    }.get(symbol, symbol.replace("hf_", "").lower())
    return NormalizedMarketObservation(
        provider_id=provider_id,
        entity=symbol,
        title=f"{name} commodity quote move",
        metric="intraday_return",
        value=pct / 100,
        threshold=0.02,
        source="tencent.qt.gtimg.cn",
        as_of=f"{fields[12]}T{fields[6]}+08:00" if fields[12] and fields[6] else utc_now_iso(),
        lookback_days=1,
        affected_domains=("supply_chain", "contract"),
        metadata={
            "signal_type": "commodity_futures",
            "commodity_group": commodity_group,
            "quote_name": name,
            "current": current,
            "previous": previous,
            "high": _safe_float(fields[4]) if len(fields) > 4 else None,
            "low": _safe_float(fields[5]) if len(fields) > 5 else None,
        },
    )


def _severity_from_signed_move(value: float, threshold: float) -> str:
    abs_threshold = abs(threshold)
    abs_value = abs(value)
    if abs_threshold <= 0:
        return "medium"
    if abs_value >= abs_threshold * 2:
        return "critical"
    if abs_value >= abs_threshold * 1.25:
        return "high"
    if abs_value >= abs_threshold:
        return "medium"
    return "low"


def _resolve_tencent_symbols(
    *,
    resolved_type: str,
    symbol: str | None,
    commodity_group: str | None,
    market_symbols: tuple[str, ...],
    sector_symbols: tuple[str, ...],
    commodity_symbols: tuple[str, ...],
) -> tuple[str, ...]:
    if symbol:
        return (symbol,)
    if resolved_type == "market":
        return (*market_symbols, "bk_BK1326", "bk_BK1037", "bk_BK1128")
    if resolved_type == "commodity_futures":
        if commodity_group:
            mapped = {
                "copper": "hf_CAD",
                "aluminum": "hf_AHD",
                "silver": "hf_SI",
                "gold": "hf_GC",
                "crude": "hf_CL",
                "oil": "hf_CL",
                "natural_gas": "hf_NG",
                "zinc": "hf_ZSD",
                "nickel": "hf_NID",
                "lead": "hf_PBD",
                "tin": "hf_SND",
                "palladium": "hf_XPD",
                "platinum": "hf_XPT",
                "corn": "hf_C",
                "soybean": "hf_S",
                "wheat": "hf_W",
                "ethylene_glycol": "if_EG0",
                "polypropylene": "if_PP0",
                "polyethylene": "if_L0",
                "pvc": "if_V0",
                "methanol": "if_MA0",
                "pta": "if_TA0",
                "caustic_soda": "if_SH0",
                "glass": "if_FG0",
                "urea": "if_UR0",
                "styrene": "if_EB0",
                "paraxylene": "if_PX0",
                "polyester_fiber": "if_PF0",
                "lpg": "if_PG0",
            }.get(commodity_group)
            return (mapped,) if mapped else commodity_symbols
        return commodity_symbols
    return (*market_symbols, "hf_CAD", "hf_GC", "if_EC0", "if_SC0")


def _safe_float(value: Any) -> float | None:
    try:
        text = str(value).replace("%", "").strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _tencent_datetime(value: str) -> str | None:
    text = str(value or "").strip()
    if len(text) != 14 or not text.isdigit():
        return None
    return f"{text[0:4]}-{text[4:6]}-{text[6:8]}T{text[8:10]}:{text[10:12]}:{text[12:14]}+08:00"


def _eastmoney_datetime(value: Any) -> str | None:
    seconds = _safe_float(value)
    if seconds is None or seconds <= 0:
        return None
    return datetime.fromtimestamp(seconds, timezone.utc).astimezone().isoformat()


def _dedupe_live_signals(signals: list[ExternalRiskSignal]) -> list[ExternalRiskSignal]:
    seen: set[str] = set()
    deduped: list[ExternalRiskSignal] = []
    for signal in signals:
        key = f"{signal.source}:{signal.entity}:{signal.metric}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
    return deduped


def _call_akshare_fetcher(fetcher: Any, *, symbol: str | None) -> Any:
    if symbol:
        try:
            return fetcher(symbol=symbol)
        except TypeError:
            return fetcher(symbol)
    return fetcher()


def _records_from_result(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if hasattr(raw, "to_dict"):
        try:
            records = raw.to_dict("records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]
        except Exception:
            return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def _signed_move_from_records(records: list[dict[str, Any]]) -> float | None:
    if not records:
        return None
    direct = _first_numeric(records[-1], ("pct_chg", "change_pct", "change_percent", "涨跌幅", "涨幅", "涨跌"))
    if direct is not None:
        return direct / 100 if abs(direct) > 1 else direct
    first = _first_numeric(records[0], ("close", "收盘", "latest", "最新价", "price", "现价"))
    last = _first_numeric(records[-1], ("close", "收盘", "latest", "最新价", "price", "现价"))
    if first is None or last is None or first == 0:
        return None
    return (last - first) / first


def _first_numeric(row: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in row:
            continue
        try:
            return float(str(row[key]).replace("%", "").strip())
        except (TypeError, ValueError):
            continue
    return None
