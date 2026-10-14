import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.external_risk.contracts import (
    EXTERNAL_RISK_API_VERSION,
    EXTERNAL_RISK_ENDPOINTS,
    EXTERNAL_RISK_FIXTURE_VERSION,
)
from src.external_risk.commodity_catalog import CATALOG_BY_SYMBOL, catalog_display_name
from src.external_risk.provider_config import CORE_INTELLIGENCE_FEEDS, ExternalRiskProviderConfig, IntelligenceFeedConfig, load_provider_config
from src.external_risk.repository import FixtureExternalRiskRepository
from src.supply_chain.repository import SupplyChainRepository
from src.external_risk.providers import (
    AkShareExternalRiskProvider,
    NormalizedMarketObservation,
    TencentHttpExternalRiskProvider,
    commodity_observation_to_signal,
    market_observation_to_signal,
    aggregate_eastmoney_sector_ticks,
    parse_eastmoney_klines,
    parse_eastmoney_details,
    parse_eastmoney_quote_observation,
    parse_sina_cn_futures_daily,
    parse_sina_cn_futures_minute,
    parse_eastmoney_trends,
    parse_yahoo_chart,
    parse_tencent_global_quote_snapshot,
    parse_tencent_quote_series,
    parse_tencent_quote_name,
    parse_tencent_quote_observations,
    _yahoo_symbol,
)
from src.external_risk.intelligence import (
    NewsPolicyRssExternalRiskProvider,
    _dedupe_signals,
    enrich_csrc_action_signals,
    signals_from_eastmoney_futures_html,
    signals_from_cailianshe_telegraph,
    signals_from_feed_xml,
    signals_from_futures_exchange_notice_html,
    signals_from_official_policy_html,
    signals_from_sina_futures_html,
    signals_from_yicai_homepage,
)
from src.external_risk.service import (
    ExternalRiskDataError,
    ExternalRiskService,
    _quote_display_metadata,
    _chain_alerts,
    _live_signal_legal_query_tasks,
    _broad_supply_chain_observations,
    _relevant_live_signals,
    _risk_coefficient,
)
from src.external_risk.schemas import (
    ExternalRiskSignal,
    ExternalRiskQuotePoint,
    ExternalRiskWorkflowGraph,
    ExternalRiskWorkflowLink,
    ExternalRiskWorkflowNode,
)
from src.main import app


FIXTURE_PATH = Path("tests/fixtures/external_risk_context_v0.1.0.json")


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class ExternalRiskApiTest(unittest.TestCase):
    def test_a_share_quote_metadata_uses_listing_reference_without_capping_change(self):
        metadata = _quote_display_metadata(
            symbol="sh688825",
            name="N长鑫",
            interval="intraday",
            points=[
                ExternalRiskQuotePoint(time="09:30", close=49.50, baseline_price=8.66),
                ExternalRiskQuotePoint(time="15:30", close=49.00, baseline_price=8.66),
            ],
        )

        self.assertEqual(metadata["instrument_status"], "new_listing")
        self.assertEqual(metadata["change_basis"], "listing_reference")
        self.assertEqual(metadata["price_limit_label"], "new_listing_initial_period")
        self.assertIsNone(metadata["price_limit_rate"])
        self.assertEqual(metadata["reference_price"], 8.66)
        self.assertAlmostEqual(metadata["change_rate"], 4.6581986143)

    def test_a_share_quote_metadata_applies_board_and_st_limit_rules(self):
        cases = [
            ("sh600519", "普通股", "normal", 0.10, "main_normal_10pct"),
            ("sh600519", "*ST普通股", "st", 0.10, "main_st_10pct"),
            ("sh688001", "科创公司", "normal", 0.20, "star_normal_20pct"),
            ("sz300001", "创业公司", "normal", 0.20, "chinext_normal_20pct"),
            ("bj430001", "北交公司", "normal", 0.30, "bse_normal_30pct"),
        ]
        points = [ExternalRiskQuotePoint(time="15:30", close=110.0, baseline_price=100.0)]

        for symbol, name, status, limit_rate, limit_label in cases:
            with self.subTest(symbol=symbol):
                metadata = _quote_display_metadata(symbol=symbol, name=name, interval="intraday", points=points)
                self.assertEqual(metadata["instrument_status"], status)
                self.assertEqual(metadata["price_limit_rate"], limit_rate)
                self.assertEqual(metadata["price_limit_label"], limit_label)

    def test_a_share_quote_metadata_updates_after_status_marker_is_removed(self):
        points = [ExternalRiskQuotePoint(time="15:30", close=110.0, baseline_price=100.0)]
        before = _quote_display_metadata(
            symbol="sh600519",
            name="*ST示例",
            interval="intraday",
            points=points,
        )
        after = _quote_display_metadata(
            symbol="sh600519",
            name="示例股份",
            interval="intraday",
            points=points,
        )

        self.assertEqual(before["instrument_status"], "st")
        self.assertEqual(before["price_limit_rate"], 0.10)
        self.assertEqual(after["instrument_status"], "normal")
        self.assertEqual(after["price_limit_rate"], 0.10)
        self.assertEqual(after["price_limit_label"], "main_normal_10pct")

    def test_c_listing_marker_uses_previous_close_then_restores_board_rule(self):
        points = [ExternalRiskQuotePoint(time="15:30", close=120.0, baseline_price=100.0)]
        during_listing = _quote_display_metadata(
            symbol="sz300001",
            name="C示例",
            interval="intraday",
            points=points,
        )
        after_listing = _quote_display_metadata(
            symbol="sz300001",
            name="示例股份",
            interval="intraday",
            points=points,
        )

        self.assertEqual(during_listing["instrument_status"], "new_listing")
        self.assertEqual(during_listing["change_basis"], "previous_close")
        self.assertIsNone(during_listing["price_limit_rate"])
        self.assertEqual(after_listing["instrument_status"], "normal")
        self.assertEqual(after_listing["price_limit_rate"], 0.20)
        self.assertEqual(after_listing["price_limit_label"], "chinext_normal_20pct")

    def test_openapi_exposes_external_risk_paths(self):
        paths = app.openapi().get("paths", {})

        for endpoint in EXTERNAL_RISK_ENDPOINTS:
            self.assertIn(endpoint["path"], paths)
            self.assertIn(endpoint["method"].lower(), paths[endpoint["path"]])

    def test_context_endpoint_returns_fixture_backed_contract(self):
        client = TestClient(app)
        response = client.get("/external-risk/context")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        fixture_context = load_fixture()["context"]
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["meta"]["contract_version"], EXTERNAL_RISK_API_VERSION)
        self.assertEqual(payload["meta"]["fixture_version"], EXTERNAL_RISK_FIXTURE_VERSION)
        self.assertEqual(payload["meta"]["data_source"], "fixture_sample")
        self.assertEqual(payload["data"]["company"], fixture_context["company"])
        self.assertTrue(payload["data"]["signals"])
        self.assertTrue(payload["data"]["findings"])
        self.assertTrue(any(item["signal_type"] == "commodity_futures" for item in payload["data"]["signals"]))

    def test_signal_filters_are_applied(self):
        client = TestClient(app)

        commodity = client.get("/external-risk/signals", params={"signal_type": "commodity_futures"}).json()["items"]
        self.assertTrue(commodity)
        self.assertTrue(all(item["signal_type"] == "commodity_futures" for item in commodity))

        high = client.get("/external-risk/signals", params={"severity": "high"}).json()["items"]
        self.assertTrue(high)
        self.assertTrue(all(item["severity"] == "high" for item in high))

    def test_finding_filters_are_applied(self):
        client = TestClient(app)

        export_control = client.get(
            "/external-risk/findings",
            params={"risk_domain": "export_control"},
        ).json()["items"]
        self.assertEqual(len(export_control), 1)
        self.assertEqual(export_control[0]["risk_domain"], "export_control")

    def test_legal_query_plan_maps_external_facts_to_rag_tasks(self):
        client = TestClient(app)
        response = client.get("/external-risk/legal-query-plan")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"]["scope"], "external_fact_to_legal_rag_query_plan")
        tasks = payload["data"]["tasks"]
        self.assertTrue(tasks)
        first_task = tasks[0]
        self.assertIn("query", first_task)
        self.assertIn("fact_background", first_task)
        self.assertTrue(first_task["triggering_signal_ids"])
        self.assertTrue(first_task["evidence_refs"])
        self.assertTrue(payload["data"]["guardrails"])

    def test_legal_query_plan_filters_by_domain(self):
        client = TestClient(app)
        response = client.get("/external-risk/legal-query-plan", params={"risk_domain": "export_control"})

        self.assertEqual(response.status_code, 200)
        tasks = response.json()["data"]["tasks"]
        self.assertTrue(tasks)
        self.assertTrue(all(task["risk_domain"] == "export_control" for task in tasks))

    def test_live_signal_generates_traceable_legal_query_task(self):
        signal = ExternalRiskSignal(
            signal_id="live-policy-1",
            signal_type="policy",
            title="\u51fa\u53e3\u7ba1\u5236\u63aa\u65bd\u66f4\u65b0",
            severity="high",
            direction="negative",
            as_of="2026-07-22T10:00:00+08:00",
            entity="export_control",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["export_control"],
            evidence="\u76f8\u5173\u51fa\u53e3\u9650\u5236\u5c06\u5f71\u54cd\u6280\u672f\u652f\u6301\u3002",
            source="https://example.gov/notices/1",
            confidence=0.9,
            metadata={"feed_id": "official-policy", "feed_name": "\u5b98\u65b9\u653f\u7b56", "risk_relevance": 0.9},
        )

        tasks = _live_signal_legal_query_tasks([signal])

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].metadata["origin"], "live_external_signal")
        self.assertEqual(tasks[0].evidence_refs, ["live-policy-1"])
        self.assertIn("https://example.gov/notices/1", tasks[0].fact_background)

    def test_market_signal_includes_human_readable_instrument_name_and_code(self):
        observation = NormalizedMarketObservation(
            provider_id="unit_provider",
            entity="sz000725",
            title="raw title",
            metric="intraday_return",
            value=-0.02,
            threshold=0.015,
            source="unit.fixture",
            as_of="2026-07-22T10:00:00+08:00",
            lookback_days=1,
            affected_domains=("market",),
            metadata={"quote_name": "\u4eac\u4e1c\u65b9A"},
        )

        signal = market_observation_to_signal(observation)

        self.assertEqual(signal.metadata["instrument_code"], "SZ.000725")
        self.assertEqual(signal.metadata["instrument_label"], "\u4eac\u4e1c\u65b9A\uff08SZ.000725\uff09")
        self.assertIn("\u4eac\u4e1c\u65b9A\uff08SZ.000725\uff09", signal.title)

    def test_commodity_market_signal_uses_disambiguated_name_and_venue(self):
        observation = NormalizedMarketObservation(
            provider_id="unit_provider",
            entity="hf_NG",
            title="raw title",
            metric="intraday_return",
            value=0.021,
            threshold=0.02,
            source="unit.fixture",
            as_of="2026-09-03T10:00:00+08:00",
            lookback_days=1,
            affected_domains=("supply_chain",),
            metadata={"quote_name": "天然气"},
        )

        signal = commodity_observation_to_signal(
            observation,
            commodity_group="natural_gas",
            affected_supply_links=("energy",),
        )

        self.assertEqual(catalog_display_name("hf_NG"), "天然气（NYMEX）")
        self.assertEqual(signal.metadata["instrument_name"], "天然气（NYMEX）")
        self.assertEqual(signal.metadata["instrument_label"], "天然气（NYMEX） · HF.NG")
        self.assertIn("天然气（NYMEX）", signal.title)

    def test_chain_alert_propagates_upstream_commodity_shock_to_downstream_nodes(self):
        signal = ExternalRiskSignal(
            signal_id="copper-shock",
            signal_type="commodity_futures",
            title="\u4f26\u94dc\u5927\u5e45\u6ce2\u52a8",
            severity="high",
            direction="negative",
            as_of="2026-07-24T10:00:00+08:00",
            entity="hf_CAD",
            metric="intraday_return",
            value=0.04,
            threshold=0.02,
            affected_domains=["supply_chain", "contract"],
            affected_supply_links=["copper"],
            evidence="\u94dc\u4ef7\u4e0a\u6da8\u589e\u52a0 PCB \u4e0e\u7535\u7f51\u8bbe\u5907\u6210\u672c\u538b\u529b\u3002",
            source="https://example.test/copper",
            confidence=0.8,
            metadata={"commodity_group": "copper", "risk_relevance": 0.9},
        )
        graph = ExternalRiskWorkflowGraph(
            nodes=[
                ExternalRiskWorkflowNode(id="copper", symbol="hf_CAD"),
                ExternalRiskWorkflowNode(id="pcb", symbol="bk_BK0877"),
                ExternalRiskWorkflowNode(id="consumer", symbol="bk_BK1037"),
            ],
            links=[
                ExternalRiskWorkflowLink(source="copper", target="pcb", confirmed_by="qa", confirmed_at="2026-08-20T00:00:00Z"),
                ExternalRiskWorkflowLink(source="pcb", target="consumer", confirmed_by="qa", confirmed_at="2026-08-20T00:00:00Z"),
            ],
        )

        alerts = _chain_alerts([signal], graph)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].affected_node_ids, ["copper", "pcb", "consumer"])
        self.assertEqual(alerts[0].path_node_ids, ["pcb", "consumer"])
        self.assertIn(alerts[0].path_node_ids[-1], alerts[0].affected_node_ids)
        self.assertGreater(alerts[0].transmission_score, 0)

    def test_risk_score_does_not_increase_when_legal_query_count_changes(self):
        signal = ExternalRiskSignal(
            signal_id="measured-market-signal",
            signal_type="market",
            title="\u5e02\u573a\u6ce2\u52a8",
            severity="high",
            direction="negative",
            as_of="2026-07-24T10:00:00+08:00",
            entity="sz399006",
            metric="intraday_return",
            value=-0.03,
            threshold=0.015,
            affected_domains=["market"],
            evidence="\u8d85\u8fc7\u9608\u503c\u7684\u5e02\u573a\u6ce2\u52a8\u3002",
            source="https://example.test/market",
            confidence=0.8,
            metadata={"risk_relevance": 0.9},
        )

        low_task_count = _risk_coefficient([signal], legal_task_count=1)
        high_task_count = _risk_coefficient([signal], legal_task_count=99)

        self.assertEqual(low_task_count, high_task_count)

    def test_generic_export_policy_does_not_create_unrelated_chain_alert(self):
        signal = ExternalRiskSignal(
            signal_id="generic-export-policy",
            signal_type="policy",
            title="\u5bf9\u6c2e\u6c14\u5b9e\u65bd\u4e34\u65f6\u51fa\u53e3\u7ba1\u7406",
            severity="high",
            direction="negative",
            as_of="2026-07-24T10:00:00+08:00",
            entity="export_control",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["export_control"],
            affected_supply_links=["overseas_sales", "technical_support"],
            evidence="\u4e34\u65f6\u51fa\u53e3\u7ba1\u7406\u3002",
            source="https://example.test/export",
            confidence=0.8,
            metadata={"risk_relevance": 0.8},
        )
        graph = ExternalRiskWorkflowGraph(
            nodes=[ExternalRiskWorkflowNode(id="consumer", symbol="bk_BK1037")],
        )

        self.assertEqual(_chain_alerts([signal], graph), [])

    def test_live_query_queue_dedupes_repeated_csrc_actions(self):
        common = dict(
            signal_type="policy",
            title="\u4e2d\u56fd\u8bc1\u76d1\u4f1a\u884c\u653f\u5904\u7f5a\u51b3\u5b9a\u4e66",
            severity="high",
            direction="negative",
            as_of="2026-07-22T10:00:00+08:00",
            entity="securities_disclosure",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["disclosure"],
            evidence="\u884c\u653f\u5904\u7f5a\u51b3\u5b9a\u4e66",
            confidence=0.85,
            metadata={"feed_id": "csrc-regulatory-actions", "feed_name": "\u4e2d\u56fd\u8bc1\u76d1\u4f1a"},
        )
        first = ExternalRiskSignal(signal_id="csrc-1", source="https://example.gov/csrc/1", **common)
        second = ExternalRiskSignal(signal_id="csrc-2", source="https://example.gov/csrc/2", **common)

        tasks = _live_signal_legal_query_tasks([first, second])

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].risk_domain, "disclosure")

    def test_provider_status_endpoint_is_fixture_safe(self):
        client = TestClient(app)
        with patch.dict(
            "os.environ",
            {"EXTERNAL_RISK_LIVE_ENABLED": "false", "EXTERNAL_RISK_HTTP_ENABLED": "false"},
        ):
            response = client.get("/external-risk/provider-status")

        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertTrue(items)
        self.assertTrue(all(item["runtime_access"] in {"not_called", "fixture_only", "cache_read"} for item in items))
        self.assertTrue(any(item["provider_type"] == "commodity_futures" for item in items))

    def test_market_dashboard_endpoint_returns_frontend_ready_data(self):
        client = TestClient(app)
        with patch.dict(
            "os.environ",
            {"EXTERNAL_RISK_LIVE_ENABLED": "false", "EXTERNAL_RISK_HTTP_ENABLED": "false"},
        ):
            response = client.get("/external-risk/market-dashboard")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        data = payload["data"]
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["meta"]["data_source"], "unavailable_live_provider")
        self.assertIn("headline", data["summary"])
        self.assertEqual(data["summary"]["signal_count"], 0)
        self.assertEqual(data["summary"]["legal_task_count"], 0)
        self.assertIn("risk_coefficient", data["summary"])
        self.assertGreaterEqual(data["summary"]["risk_coefficient"], 0)
        self.assertLessEqual(data["summary"]["risk_coefficient"], 100)
        self.assertIn(data["summary"]["risk_coefficient_level"], {"low", "medium", "high", "critical"})
        self.assertIn("0.22S", data["summary"]["risk_coefficient_formula"])
        self.assertIn("chain_transmission", data["summary"]["risk_coefficient_components"])
        self.assertIn("materiality", data["summary"]["risk_coefficient_components"])
        self.assertGreaterEqual(data["summary"]["risk_coefficient_quality"], 0)
        self.assertLessEqual(data["summary"]["risk_coefficient_quality"], 1)
        self.assertEqual(data["signals"], [])
        self.assertEqual(data["findings"], [])
        self.assertEqual(data["legal_query_tasks"], [])
        self.assertTrue(data["provider_statuses"])
        self.assertIn("intelligence_status", data)
        self.assertIn("feeds", data["intelligence_status"])

    def test_broad_supply_chain_observations_are_context_only(self):
        signal = ExternalRiskSignal(
            signal_id="industry-observation",
            signal_type="news",
            title="服务器设备扩产，供应链交付节奏变化",
            severity="low",
            direction="mixed",
            as_of="2026-09-03T10:00:00+08:00",
            entity="supply_chain_market_observation",
            metric="news_rule_match",
            evidence="服务器设备扩产，供应商交付节奏变化。",
            source="https://example.test/industry",
            affected_domains=["supply_chain"],
            metadata={"industry_tags": ["data_center"]},
        )

        observations = _broad_supply_chain_observations([signal])

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].metadata["observation_scope"], "broad_supply_chain")
        self.assertEqual(observations[0].metadata["risk_inclusion"], "context_only")

    def test_observation_normalizers_build_contract_signals(self):
        observation = NormalizedMarketObservation(
            provider_id="unit_provider",
            entity="copper_main_contract",
            title="Copper main contract moved up",
            metric="5d_return",
            value=0.064,
            threshold=0.05,
            source="unit.fixture",
            as_of="2026-06-24T15:00:00+08:00",
            lookback_days=5,
            affected_domains=("supply_chain", "contract"),
        )

        commodity = commodity_observation_to_signal(
            observation,
            commodity_group="copper",
            affected_supply_links=("motors", "cables"),
        )
        self.assertEqual(commodity.signal_type, "commodity_futures")
        self.assertEqual(commodity.severity, "high")
        self.assertIn("motors", commodity.affected_supply_links)
        self.assertEqual(commodity.metadata["observation_periods"], 5)
        self.assertEqual(commodity.metadata["contract"], "COPPER_MAIN_CONTRACT")

        market = market_observation_to_signal(
            NormalizedMarketObservation(
                **{**observation.__dict__, "entity": "semiconductor_index", "value": -0.08}
            )
        )
        self.assertEqual(market.signal_type, "market")
        self.assertEqual(market.direction, "negative")

    def test_external_risk_endpoints_do_not_call_legal_runtime_chains(self):
        client = TestClient(app)
        with (
            patch.dict(
                "os.environ",
                {"EXTERNAL_RISK_LIVE_ENABLED": "false", "EXTERNAL_RISK_HTTP_ENABLED": "false"},
            ),
            patch("src.main.rag_query") as rag_query,
            patch("src.main.analyze_risk") as analyze_risk,
            patch("src.main.generate_risk_report") as generate_risk_report,
            patch("src.main.generate_risk_report_export") as generate_risk_report_export,
        ):
            for endpoint in EXTERNAL_RISK_ENDPOINTS:
                if endpoint["method"] != "GET":
                    continue
                response = client.get(endpoint["path"])
                self.assertEqual(response.status_code, 200)

        rag_query.assert_not_called()
        analyze_risk.assert_not_called()
        generate_risk_report.assert_not_called()
        generate_risk_report_export.assert_not_called()

    def test_live_signals_endpoint_is_disabled_by_default(self):
        client = TestClient(app)
        with patch.dict(
            "os.environ",
            {"EXTERNAL_RISK_LIVE_ENABLED": "false", "EXTERNAL_RISK_HTTP_ENABLED": "false"},
        ):
            response = client.get("/external-risk/live-signals", params={"signal_type": "commodity_futures"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["items"], [])
        self.assertEqual(payload["meta"]["data_source"], "disabled_live_provider")
        self.assertEqual(payload["meta"]["runtime_data_access"]["rag"], "not_called")
        self.assertEqual(payload["meta"]["runtime_data_access"]["market_data"], "not_called")

    def test_intelligence_feed_rules_create_reviewable_policy_signal(self):
        feed = IntelligenceFeedConfig(
            feed_id="official-policy",
            url="https://example.gov/policy.xml",
            signal_type="policy",
            source_name="Official policy",
        )
        xml = """
        <rss><channel><item>
          <title>半导体出口管制限制措施更新</title>
          <link>https://example.gov/notices/1</link>
          <pubDate>2026-07-22T09:00:00+08:00</pubDate>
          <description>相关实体清单和出口管制措施将限制部分技术支持。</description>
        </item></channel></rss>
        """

        signals = signals_from_feed_xml(xml, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, "policy")
        self.assertEqual(signals[0].severity, "critical")
        self.assertIn("export_control", signals[0].affected_domains)
        self.assertTrue(signals[0].metadata["requires_human_review"])
        self.assertIn("export_control", signals[0].metadata["matched_rules"])

    def test_cailianshe_adapter_requires_risk_trigger_not_only_industry_word(self):
        feed = IntelligenceFeedConfig(
            "cailianshe", "https://www.cls.cn/api/cache?lastTime={now}", "news", "财联社", "cailianshe_telegraph"
        )
        raw = json.dumps(
            {
                "errno": 0,
                "data": {
                    "roll_data": [
                        {
                            "id": 1,
                            "ctime": 1784701714,
                            "title": "芯片企业宣布扩大合作",
                            "content": "半导体企业宣布新的芯片合作项目。",
                        },
                        {
                            "id": 2,
                            "ctime": 1784701715,
                            "title": "美国 ITC 对电池材料启动 337 调查",
                            "content": "美国国际贸易委员会对相关产品启动 337 调查，涉及关税和贸易救济。",
                        },
                    ]
                },
            }
        )

        signals = signals_from_cailianshe_telegraph(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "trade_remedy")
        self.assertIn("cls.cn/telegraph/2", signals[0].source)

    def test_financial_feeds_keep_current_commodity_price_observations(self):
        feed = IntelligenceFeedConfig(
            "cailianshe",
            "https://www.cls.cn/api/cache?lastTime={now}",
            "news",
            "财联社",
            "cailianshe_telegraph",
        )
        raw = json.dumps(
            {
                "data": {
                    "roll_data": [
                        {
                            "id": 11,
                            "ctime": 1788406272,
                            "title": "国内期货主力合约多数上涨 钯涨超4%",
                            "content": "沪银、铂、SC原油、纯碱上涨，集运欧线下跌。",
                        },
                        {
                            "id": 12,
                            "ctime": 1788405027,
                            "title": "焦煤期货主力合约日内跌4%",
                            "content": "焦煤期货主力合约日内跌4%，现报1640元/吨。",
                        },
                    ]
                }
            }
        )

        signals = signals_from_cailianshe_telegraph(raw, feed)

        self.assertEqual(len(signals), 2)
        self.assertTrue(all(signal.entity == "commodity_futures_supply_shock" for signal in signals))
        self.assertTrue(any("hf_XPD" in signal.metadata["commodity_symbols"] for signal in signals))
        self.assertTrue(any("if_JM0" in signal.metadata["commodity_symbols"] for signal in signals))

    def test_supply_chain_market_observation_is_wider_but_not_generic(self):
        feed = IntelligenceFeedConfig("yicai", "https://www.yicai.com/", "news", "第一财经", "yicai_homepage")
        raw = """
        <div id="scrollFontDiv"><ul>
        <li><span>11:30</span><a href="/brief/101.html"><b>半导体板块走强</b> 芯片和光模块产业链出现资金异动。</a></li>
        <li><span>11:29</span><a href="/brief/102.html"><b>芯片企业宣布扩大合作</b> 半导体企业签署合作协议。</a></li>
        </ul></div>
        """

        signals = signals_from_yicai_homepage(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "supply_chain_market_observation")
        self.assertEqual(signals[0].severity, "low")

    def test_pure_macro_futures_observation_is_not_supply_chain_news(self):
        feed = IntelligenceFeedConfig("yicai", "https://www.yicai.com/", "news", "第一财经", "yicai_homepage")
        raw = """
        <div id="scrollFontDiv"><ul>
        <li><span>11:30</span><a href="/brief/103.html"><b>国债期货午盘全线上涨</b> 利率债市场走势偏强。</a></li>
        </ul></div>
        """

        self.assertEqual(signals_from_yicai_homepage(raw, feed), [])

    def test_transport_weather_disruption_is_supply_chain_signal(self):
        feed = IntelligenceFeedConfig("cls", "https://www.cls.cn/api/cache", "news", "财联社", "cailianshe_telegraph")
        raw = json.dumps(
            {
                "data": {
                    "roll_data": [
                        {
                            "id": 13,
                            "ctime": 1788405582,
                            "title": "受台风影响福建沿海24条航线停航",
                            "content": "沿海多条航线停运，船舶避开台风影响区域。",
                        }
                    ]
                }
            }
        )

        signals = signals_from_cailianshe_telegraph(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "transport_disruption")
        self.assertIn("maritime_logistics", signals[0].affected_supply_links)

    def test_maritime_disruption_is_classified_as_supply_chain_not_export_control(self):
        feed = IntelligenceFeedConfig(
            "cailianshe", "https://www.cls.cn/api/cache?lastTime={now}", "news", "财联社", "cailianshe_telegraph"
        )
        raw = json.dumps(
            {
                "errno": 0,
                "data": {
                    "roll_data": [
                        {
                            "id": 3,
                            "ctime": 1784701716,
                            "title": "红海局势升级，油轮和商船通行受阻",
                            "content": "有关方面对经过相关航道的船只实施海上禁运，油轮及航运成本面临中断风险。",
                        }
                    ]
                },
            }
        )

        signals = signals_from_cailianshe_telegraph(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "geopolitical_shipping_disruption")
        self.assertIn("supply_chain", signals[0].affected_domains)
        self.assertNotIn("export_control", signals[0].affected_domains)
        self.assertEqual(signals[0].metadata["industry_tags"], ["maritime_logistics", "oil_transport", "energy"])
        self.assertIn("中国石油（SH.601857）", signals[0].metadata["affected_instruments"])
        self.assertIn("中远海控（SH.601919）", signals[0].metadata["affected_instruments"])

    def test_industry_alert_reaches_canvas_when_related_securities_are_not_nodes(self):
        signal = ExternalRiskSignal(
            signal_id="oil-shipping-event",
            signal_type="news",
            title="红海航道受阻推高油运与海运风险",
            severity="high",
            direction="negative",
            as_of="2026-07-24T10:00:00+08:00",
            entity="geopolitical_shipping_disruption",
            metric="news_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["supply_chain"],
            affected_supply_links=["maritime_logistics", "oil_transport"],
            evidence="油轮和商船通行受阻，影响油运与海运价格。",
            source="https://example.test/shipping",
            confidence=0.8,
            metadata={
                "risk_relevance": 0.9,
                "industry_tags": ["maritime_logistics", "oil_transport", "energy"],
                "affected_instruments": ["中国石油（SH.601857）", "中远海控（SH.601919）"],
            },
        )
        graph = ExternalRiskWorkflowGraph(
            nodes=[
                ExternalRiskWorkflowNode(id="freight", symbol="if_EC0"),
                ExternalRiskWorkflowNode(id="oil", symbol="hf_CL"),
                ExternalRiskWorkflowNode(id="downstream", symbol="bk_BK1037"),
            ],
            links=[ExternalRiskWorkflowLink(source="freight", target="downstream", confirmed_by="qa", confirmed_at="2026-08-20T00:00:00Z")],
        )

        alerts = _chain_alerts([signal], graph)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].association_type, "mixed")
        self.assertIn("freight", alerts[0].affected_node_ids)
        self.assertIn("oil", alerts[0].affected_node_ids)
        self.assertIn("downstream", alerts[0].affected_node_ids)
        self.assertIn("中国石油（SH.601857）", alerts[0].external_instruments)

    def test_major_event_for_an_off_canvas_oil_company_gets_industry_tags(self):
        feed = IntelligenceFeedConfig(
            "cailianshe", "https://www.cls.cn/api/cache?lastTime={now}", "news", "财联社", "cailianshe_telegraph"
        )
        raw = json.dumps(
            {
                "errno": 0,
                "data": {
                    "roll_data": [
                        {
                            "id": 4,
                            "ctime": 1784701717,
                            "title": "中国石油一处设施发生安全事故并停产检修",
                            "content": "中国石油相关设施发生重大事故，正在停产检修。",
                        }
                    ]
                },
            }
        )

        signals = signals_from_cailianshe_telegraph(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "listed_company_major_event")
        self.assertIn("oil_transport", signals[0].metadata["industry_tags"])
        self.assertIn("energy", signals[0].metadata["industry_tags"])
        self.assertIn("中国石油（SH.601857）", signals[0].metadata["affected_instruments"])

    def test_yicai_adapter_parses_market_brief(self):
        feed = IntelligenceFeedConfig("yicai", "https://www.yicai.com/", "news", "第一财经", "yicai_homepage")
        raw = """
        <div class="scrolfont" id="scrollFontDiv"><ul>
        <li><span>14:30</span><a href="/brief/100.html"><b>欧盟启动反倾销调查 |</b> 涉及进口产品和关税。</a></li>
        </ul></div>
        """

        signals = signals_from_yicai_homepage(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "trade_remedy")
        self.assertEqual(signals[0].source, "https://www.yicai.com/brief/100.html")
        self.assertFalse(signals[0].evidence.startswith(signals[0].title))

    def test_sina_futures_adapter_links_material_news_to_contracts(self):
        feed = IntelligenceFeedConfig(
            "sina-futures-market",
            "https://finance.sina.com.cn/futuremarket/",
            "news",
            "新浪期货",
            "sina_futures_html",
        )
        raw = """
        <a href="https://finance.sina.com.cn/money/future/fmnews/2026-08-17/doc-oil.shtml">
        原油供应扰动升级，燃料油期货面临交割风险</a>
        <a href="https://finance.sina.com.cn/money/future/fmnews/2026-08-17/doc-routine.shtml">
        午盘商品期货涨跌互现</a>
        <a href="https://finance.sina.com.cn/money/future/fmnews/2026-08-17/doc-macro.shtml">
        海外扩大关税措施引发市场讨论</a>
        """

        signals = signals_from_sina_futures_html(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "commodity_futures_supply_shock")
        self.assertIn("hf_CL", signals[0].metadata["commodity_symbols"])
        self.assertIn("if_FU0", signals[0].metadata["commodity_symbols"])
        self.assertIn("原油（HF.CL）", signals[0].metadata["affected_instruments"])

    def test_exchange_notice_adapter_keeps_material_risk_control_notice(self):
        feed = IntelligenceFeedConfig(
            "ine-exchange-notices",
            "https://www.ine.cn/publicnotice/notice/",
            "policy",
            "上海国际能源交易中心公告",
            "futures_exchange_notice_html",
        )
        raw = """
        <a href="/publicnotice/notice/202608/t20260817_1234.html">
        关于原油期货部分客户采取限制开仓监管措施的公告</a>
        <a href="/publicnotice/notice/202608/t20260817_5678.html">
        关于交易系统测试的通知</a>
        """

        signals = signals_from_futures_exchange_notice_html(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].entity, "futures_exchange_notice")
        self.assertEqual(signals[0].as_of, "2026-08-17T00:00:00+08:00")
        self.assertEqual(signals[0].source, "https://www.ine.cn/publicnotice/notice/202608/t20260817_1234.html")

    def test_eastmoney_futures_adapter_keeps_material_commodity_event(self):
        feed = IntelligenceFeedConfig(
            "eastmoney-futures-market",
            "https://futures.eastmoney.com/",
            "news",
            "东方财富期货",
            "eastmoney_futures_html",
        )
        raw = """
        <a href="https://finance.eastmoney.com/a/202608173842910290.html">
        伊朗禁止美军进入霍尔木兹海峡 原油系全线飘红</a>
        <a href="https://finance.eastmoney.com/a/202608173842961335.html">午盘播报</a>
        """

        signals = signals_from_eastmoney_futures_html(raw, feed)

        self.assertEqual(len(signals), 1)
        self.assertIn("hf_CL", signals[0].metadata["commodity_symbols"])
        self.assertIn("geopolitical_shipping_disruption", signals[0].metadata["matched_rules"])

    def test_cross_source_hormuz_futures_reports_are_deduplicated(self):
        base = ExternalRiskSignal(
            signal_id="sina-hormuz",
            signal_type="news",
            title="霍尔木兹海峡通行量大幅放缓",
            severity="high",
            direction="negative",
            as_of="2026-08-17T10:00:00+08:00",
            entity="geopolitical_shipping_disruption",
            metric="news_rule_match",
            affected_domains=["supply_chain"],
            evidence="油轮和商船通行受阻。",
            source="https://example.test/sina",
            confidence=0.7,
            metadata={"feed_id": "sina-futures-market"},
        )
        repost = base.model_copy(update={
            "signal_id": "eastmoney-hormuz",
            "title": "霍尔木兹局势突变，航运风险上升",
            "source": "https://example.test/eastmoney",
            "metadata": {"feed_id": "eastmoney-futures-market"},
        })

        self.assertEqual(len(_dedupe_signals([base, repost])), 1)

    def test_official_policy_adapter_excludes_navigation_and_keeps_article_evidence(self):
        feed = IntelligenceFeedConfig(
            "csrc", "https://www.csrc.gov.cn/csrc/zwxx/index.shtml", "policy", "中国证监会", "official_policy_html"
        )
        raw = """
        <ul>
          <li><a href="/csrc/c101971/zfxxgk_zdgk.shtml">行政处罚</a></li>
          <li><a href="/csrc/c101971/c7643184/content.shtml" title="中国证监会行政处罚决定书">中国证监会行政处罚决定书</a><span>2026-07-22</span></li>
          <li><a href="./202607/t20260710_1406433.html" title="关于电网输配电价的通知">关于电网输配电价的通知</a><span>2026/07/10</span></li>
        </ul>
        """

        signals = signals_from_official_policy_html(raw, feed)

        self.assertEqual(len(signals), 2)
        self.assertEqual({signal.entity for signal in signals}, {"securities_disclosure", "energy_cost_policy"})
        self.assertTrue(all(signal.signal_type == "policy" for signal in signals))
        self.assertTrue(all("content.shtml" in signal.source or "t20260710" in signal.source for signal in signals))

    def test_csrc_action_enrichment_uses_detail_page_subject_and_decision_number(self):
        generic = ExternalRiskSignal(
            signal_id="csrc-generic",
            signal_type="policy",
            title="\u4e2d\u56fd\u8bc1\u76d1\u4f1a\u884c\u653f\u5904\u7f5a\u51b3\u5b9a\u4e66",
            severity="high",
            direction="negative",
            as_of="2026-07-22T00:00:00+08:00",
            entity="securities_disclosure",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["disclosure"],
            evidence="\u884c\u653f\u5904\u7f5a\u51b3\u5b9a\u4e66",
            source="https://example.gov/csrc/1",
            confidence=0.85,
            metadata={"feed_id": "csrc-regulatory-actions"},
        )
        html = (
            '<meta name="description" content="\u30142026\u301525\u53f7\u5f53\u4e8b\u4eba:\u8d75\u6768,\u7537\u3002'
            "\u4f9d\u636e\u300a\u8bc1\u5238\u6cd5\u300b\u76f8\u5173\u89c4\u5b9a\u3002\">"
        )

        enriched = enrich_csrc_action_signals([generic], lambda _url: html)

        self.assertIn("\u30142026\u301525\u53f7", enriched[0].title)
        self.assertIn("\u8d75\u6768", enriched[0].title)

    def test_csrc_action_marks_instrument_as_not_disclosed_when_absent_from_article(self):
        generic = ExternalRiskSignal(
            signal_id="csrc-no-instrument",
            signal_type="policy",
            title="\u4e2d\u56fd\u8bc1\u76d1\u4f1a\u884c\u653f\u5904\u7f5a\u51b3\u5b9a\u4e66",
            severity="high",
            direction="negative",
            as_of="2026-07-22T00:00:00+08:00",
            entity="securities_disclosure",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["disclosure"],
            evidence="\u884c\u653f\u5904\u7f5a\u51b3\u5b9a\u4e66",
            source="https://example.gov/csrc/1",
            confidence=0.85,
            metadata={"feed_id": "csrc-regulatory-actions"},
        )
        html = (
            '<meta name="description" content="\u30142026\u301525\u53f7\u5f53\u4e8b\u4eba:\u8d75\u6768,\u7537\u3002">'
            "<p>\u5f53\u4e8b\u4eba\u6784\u6210\u64cd\u7eb5\u8bc1\u5238\u5e02\u573a\u884c\u4e3a\u3002</p>"
        )

        enriched = enrich_csrc_action_signals([generic], lambda _url: html)

        self.assertEqual(enriched[0].metadata["csrc_instrument_status"], "not_disclosed")
        self.assertEqual(enriched[0].metadata["csrc_instruments"], [])
        self.assertEqual(enriched[0].metadata["csrc_violation"], "\u64cd\u7eb5\u8bc1\u5238\u5e02\u573a")
        self.assertEqual(enriched[0].metadata["risk_scope"], "general_regulatory_environment")
        self.assertEqual(enriched[0].severity, "low")
        self.assertEqual(_live_signal_legal_query_tasks(enriched), [])

    def test_core_financial_source_registry_is_enabled_by_default(self):
        config = load_provider_config({})

        self.assertEqual(
            {feed.feed_id for feed in CORE_INTELLIGENCE_FEEDS},
            {
                "cailianshe-telegraph",
                "yicai-market-brief",
                "sina-futures-market",
                "eastmoney-futures-market",
                "csrc-regulatory-actions",
                "mofcom-policy-release",
                "ndrc-notices",
            },
        )
        self.assertTrue(config.intelligence_enabled)
        self.assertEqual(config.intelligence_feeds, CORE_INTELLIGENCE_FEEDS)

    def test_intelligence_provider_uses_cache_inside_poll_window(self):
        feed = IntelligenceFeedConfig("policy", "https://example.gov/feed.xml", "policy", "Policy")
        config = ExternalRiskProviderConfig(
            live_enabled=True,
            intelligence_enabled=True,
            intelligence_feeds=(feed,),
            intelligence_poll_seconds=300,
        )
        xml = """
        <rss><channel><item><title>数据安全行政处罚</title>
        <link>https://example.gov/notices/2</link><description>数据安全和个人信息监管处罚。</description>
        </item></channel></rss>
        """
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            provider = NewsPolicyRssExternalRiskProvider(
                config,
                fetcher=lambda url: calls.append(url) or xml,
                cache_path=Path(directory) / "intelligence.json",
                clock=lambda: 1_000.0,
            )
            self.assertTrue(provider.refresh())
            cached = provider.live_signals(signal_type="policy")

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(cached), 1)
        self.assertEqual(provider.status().runtime_access, "cache_read")

    def test_intelligence_provider_marks_a_successful_but_empty_feed_as_not_healthy(self):
        feed = IntelligenceFeedConfig(
            "empty-source",
            "https://example.gov/empty.html",
            "policy",
            "Empty source",
            adapter="official_policy_html",
        )
        config = ExternalRiskProviderConfig(
            live_enabled=True,
            intelligence_enabled=True,
            intelligence_feeds=(feed,),
        )
        with tempfile.TemporaryDirectory() as directory:
            provider = NewsPolicyRssExternalRiskProvider(
                config,
                fetcher=lambda _url: "<html><body><main>Rendered by client script</main></body></html>",
                cache_path=Path(directory) / "intelligence.json",
            )
            self.assertEqual(provider.refresh(), [])
            health = provider.intelligence_status().feeds[0]

        self.assertEqual(health.status, "empty")
        self.assertEqual(health.item_count, 0)
        self.assertIn("no parseable", (health.error or "").lower())
        self.assertNotIn("healthy", provider.status().message.lower())

    def test_static_futures_feed_applies_configured_recent_window(self):
        feed = IntelligenceFeedConfig(
            "sina-futures-market",
            "https://finance.sina.com.cn/futuremarket/",
            "news",
            "新浪期货",
            adapter="sina_futures_html",
            max_age_hours=168,
        )
        config = ExternalRiskProviderConfig(
            live_enabled=True,
            intelligence_enabled=True,
            intelligence_feeds=(feed,),
        )
        raw = """
        <a href="https://finance.sina.com.cn/money/future/fmnews/2026-08-19/doc-new.shtml">
            铜价上涨，供应链成本压力
        </a>
        <a href="https://finance.sina.com.cn/money/future/fmnews/2026-08-01/doc-old.shtml">
            铜价下跌，供应链库存观察
        </a>
        """
        now = datetime(2026, 8, 20, tzinfo=timezone.utc).timestamp()
        with tempfile.TemporaryDirectory() as directory:
            provider = NewsPolicyRssExternalRiskProvider(
                config,
                fetcher=lambda _url: raw,
                cache_path=Path(directory) / "intelligence.json",
                clock=lambda: now,
            )
            signals = provider.refresh()

        self.assertEqual(len(signals), 1)
        self.assertIn("doc-new", signals[0].source)

    def test_intelligence_provider_keeps_last_signal_when_one_source_fails(self):
        feeds = (
            IntelligenceFeedConfig("source-a", "https://example.gov/a.xml", "policy", "Source A"),
            IntelligenceFeedConfig("source-b", "https://example.gov/b.xml", "news", "Source B"),
        )
        config = ExternalRiskProviderConfig(
            live_enabled=True,
            intelligence_enabled=True,
            intelligence_feeds=feeds,
            intelligence_poll_seconds=300,
        )
        source_a = """
        <rss><channel><item><title>出口管制限制措施</title>
        <link>https://example.gov/a/1</link><description>实体清单限制技术支持。</description>
        </item></channel></rss>
        """
        source_b = """
        <rss><channel><item><title>数据安全行政处罚</title>
        <link>https://example.gov/b/1</link><description>个人信息违规被处罚。</description>
        </item></channel></rss>
        """
        source_b_available = [True]

        def fetcher(url: str) -> str:
            if url.endswith("a.xml"):
                return source_a
            if source_b_available[0]:
                return source_b
            raise OSError("source-b timeout")

        with tempfile.TemporaryDirectory() as directory:
            provider = NewsPolicyRssExternalRiskProvider(
                config,
                fetcher=fetcher,
                cache_path=Path(directory) / "intelligence.json",
            )
            self.assertEqual(len(provider.refresh()), 2)
            source_b_available[0] = False
            retained = provider.refresh()
            status = provider.intelligence_status()

        retained_b = [signal for signal in retained if signal.metadata["feed_id"] == "source-b"]
        self.assertEqual(len(retained_b), 1)
        self.assertTrue(retained_b[0].metadata["source_stale"])
        health_by_id = {item.feed_id: item for item in status.feeds}
        self.assertEqual(health_by_id["source-a"].status, "success")
        self.assertEqual(health_by_id["source-b"].status, "failed")
        self.assertIn("timeout", health_by_id["source-b"].error or "")

    def test_intelligence_status_endpoint_reports_configured_sources(self):
        client = TestClient(app)

        response = client.get("/external-risk/intelligence/status")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual({item["feed_id"] for item in data["feeds"]}, {feed.feed_id for feed in CORE_INTELLIGENCE_FEEDS})
        self.assertIn(data["provider"]["status"], {"available", "unavailable", "not_configured"})

    def test_risk_coefficient_is_not_reduced_by_an_added_negative_news_signal(self):
        critical = ExternalRiskSignal(
            signal_id="critical-export-control",
            signal_type="policy",
            title="出口管制",
            severity="critical",
            direction="negative",
            as_of="2026-07-22T10:00:00+08:00",
            entity="export_control",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["export_control"],
            evidence="限制措施",
            source="https://example.gov/1",
            confidence=0.9,
        )
        medium_news = ExternalRiskSignal(
            signal_id="medium-trade-remedy",
            signal_type="news",
            title="贸易救济调查",
            severity="medium",
            direction="negative",
            as_of="2026-07-22T10:01:00+08:00",
            entity="trade_remedy",
            metric="news_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["contract"],
            evidence="调查启动",
            source="https://example.com/1",
            confidence=0.7,
        )

        base_score = _risk_coefficient([critical], legal_task_count=2)
        combined_score = _risk_coefficient([critical, medium_news], legal_task_count=2)

        self.assertGreaterEqual(combined_score, base_score)

    def test_risk_coefficient_caps_repeated_headlines_from_one_source_and_entity(self):
        signal = ExternalRiskSignal(
            signal_id="csrc-1",
            signal_type="policy",
            title="中国证监会行政处罚决定书",
            severity="critical",
            direction="negative",
            as_of="2026-07-22T10:00:00+08:00",
            entity="securities_disclosure",
            metric="policy_rule_match",
            value=1.0,
            threshold=1.0,
            affected_domains=["disclosure"],
            evidence="行政处罚决定书",
            source="https://www.csrc.gov.cn/csrc/c101971/c1/content.shtml",
            confidence=0.29,
            metadata={"feed_id": "csrc-regulatory-actions"},
        )
        repeated = signal.model_copy(
            update={
                "signal_id": "csrc-2",
                "as_of": "2026-07-22T11:00:00+08:00",
                "source": "https://www.csrc.gov.cn/csrc/c101971/c2/content.shtml",
            }
        )

        one_score = _risk_coefficient([signal], legal_task_count=1)
        repeated_score = _risk_coefficient([signal, repeated], legal_task_count=1)

        self.assertEqual(repeated_score, one_score)

    def test_intelligence_refresh_endpoint_fails_closed_without_configuration(self):
        client = TestClient(app)
        with patch.dict(
            "os.environ",
            {"EXTERNAL_RISK_LIVE_ENABLED": "false", "EXTERNAL_RISK_INTELLIGENCE_ENABLED": "false"},
        ):
            response = client.post("/external-risk/intelligence/refresh")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(response.json()["meta"]["data_source"], "disabled_live_provider")

    def test_default_intelligence_provider_reloads_when_runtime_configuration_changes(self):
        service = ExternalRiskService()
        with patch.dict("os.environ", {"EXTERNAL_RISK_LIVE_ENABLED": "false"}):
            disabled_provider = service._intelligence_provider()
            self.assertFalse(disabled_provider.config.live_enabled)

        with patch.dict("os.environ", {"EXTERNAL_RISK_LIVE_ENABLED": "true"}):
            enabled_provider = service._intelligence_provider()
            self.assertTrue(enabled_provider.config.live_enabled)

        self.assertIsNot(disabled_provider, enabled_provider)

    def test_akshare_provider_does_not_import_when_disabled(self):
        def fail_loader(_name: str):
            raise AssertionError("akshare should not be imported when live mode is disabled")

        provider = AkShareExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=False, akshare_enabled=False),
            module_loader=fail_loader,
        )

        self.assertEqual(provider.live_signals(signal_type="market"), [])
        self.assertEqual(provider.status().runtime_access, "not_called")

    def test_akshare_provider_normalizes_mock_market_data(self):
        class FakeAkShare:
            @staticmethod
            def stock_zh_index_daily(symbol=None):
                return [
                    {"close": 100},
                    {"close": 94},
                    {"close": 91},
                ]

        provider = AkShareExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=True, akshare_enabled=True, default_lookback_days=5),
            module_loader=lambda _name: FakeAkShare,
        )

        signals = provider.live_signals(signal_type="market", symbol="semiconductor_index")

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, "market")
        self.assertEqual(signals[0].direction, "negative")
        self.assertEqual(signals[0].metadata["provider_id"], "akshare_live_provider")
        self.assertEqual(provider.status().runtime_access, "live_called")

    def test_akshare_provider_normalizes_mock_commodity_data(self):
        class FakeAkShare:
            @staticmethod
            def futures_zh_spot(symbol=None):
                return [{"pct_chg": 6.4}]

        provider = AkShareExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=True, akshare_enabled=True),
            module_loader=lambda _name: FakeAkShare,
        )

        signals = provider.live_signals(
            signal_type="commodity_futures",
            symbol="CU0",
            commodity_group="copper",
        )

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_type, "commodity_futures")
        self.assertEqual(signals[0].severity, "high")
        self.assertIn("copper", signals[0].affected_supply_links)

    def test_tencent_http_provider_does_not_fetch_when_disabled(self):
        def fail_fetcher(_symbols):
            raise AssertionError("http provider should not fetch when live mode is disabled")

        provider = TencentHttpExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=False, http_enabled=True),
            fetcher=fail_fetcher,
        )

        self.assertEqual(provider.live_signals(), [])
        self.assertEqual(provider.status().runtime_access, "not_called")

    def test_tencent_quote_parser_builds_market_and_commodity_observations(self):
        raw = (
            'v_sh000001="1~上证指数~000001~4110.81~4106.25~4090.10~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~~20260624161419~4.56~0.11";\n'
            'v_hf_CAD="13372.32,0.01,13373.50,13375.50,13482.00,13353.00,16:43:58,13371.00,13376.00,0,1,2,2026-06-24,伦铜";'
        )

        observations = parse_tencent_quote_observations(raw)

        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].metadata["signal_type"], "market")
        self.assertEqual(observations[1].metadata["signal_type"], "commodity_futures")
        self.assertEqual(observations[1].metadata["commodity_group"], "copper")

    def test_tencent_http_provider_normalizes_mock_live_data(self):
        raw = (
            'v_sz399001="51~深证成指~399001~16051.32~15854.00~15800.00~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~0~~20260624161419~197.32~1.24";\n'
            'v_hf_AHD="3181.37,-1.58,3182.00,3183.00,3264.00,3175.00,16:44:00,3232.50,3259.50,0,5,4,2026-06-24,伦铝";'
        )
        provider = TencentHttpExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=True, http_enabled=True),
            fetcher=lambda _symbols: raw,
        )

        signals = provider.live_signals()

        self.assertGreaterEqual(len(signals), 2)
        self.assertTrue(any(signal.signal_type == "market" for signal in signals))
        self.assertTrue(any(signal.signal_type == "commodity_futures" for signal in signals))
        self.assertTrue(any(signal.entity == "sz399001" for signal in signals))
        self.assertTrue(any(signal.entity == "hf_AHD" for signal in signals))
        self.assertEqual(provider.status().runtime_access, "live_called")

    def test_tencent_quote_series_parser_builds_kline_points(self):
        raw = json.dumps(
            {
                "data": {
                    "sh000001": {
                        "qfqday": [
                            ["2026-06-23", "4090.10", "4106.25", "4110.00", "4075.00", "10000"],
                            ["2026-06-24", "4106.25", "4110.81", "4117.28", "4075.49", "12000"],
                        ]
                    }
                }
            }
        )

        points = parse_tencent_quote_series(raw, symbol="sh000001", interval="daily")

        self.assertEqual(len(points), 2)
        self.assertEqual(points[0].time, "2026-06-23")
        self.assertEqual(points[1].close, 4110.81)

    def test_tencent_intraday_uses_quote_previous_close_as_baseline(self):
        raw = json.dumps(
            {
                "data": {
                    "sh600707": {
                        "data": {
                            "data": [
                                "0930 15.05 51570 77612850.00",
                                "1500 16.89 2117757 3422618616.15",
                            ]
                        },
                        "qt": {
                            "sh600707": [
                                "1",
                                "stock",
                                "600707",
                                "16.89",
                                "15.35",
                                "15.05",
                            ]
                        },
                    }
                }
            }
        )

        points = parse_tencent_quote_series(raw, symbol="sh600707", interval="intraday")

        self.assertEqual(points[0].baseline_price, 15.35)
        self.assertEqual(points[-1].baseline_price, 15.35)
        self.assertAlmostEqual((points[-1].close - points[-1].baseline_price) / points[-1].baseline_price, 0.1003257)

    def test_global_quote_snapshot_is_used_when_us_history_sources_are_unavailable(self):
        raw = json.dumps(
            {
                "data": {
                    "usTSLA": {
                        "qt": {
                            "usTSLA": [
                                "delay", "特斯拉", "TSLA.OQ", "345.13", "351.12", "346.20", "30766360",
                                "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "2026-08-20 16:00:01", "-5.99", "-1.71", "347.50", "338.96",
                            ]
                        }
                    }
                }
            }
        )
        provider = TencentHttpExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=True, http_enabled=True),
        )
        provider._fetch_eastmoney_us_quote_series = lambda **_kwargs: []  # type: ignore[method-assign]
        provider._fetch_yahoo_quote_series = lambda **_kwargs: []  # type: ignore[method-assign]
        provider._fetch_quote_series = lambda **_kwargs: raw  # type: ignore[method-assign]

        points, source = provider.quote_series(symbol="us_TSLA", interval="intraday")

        self.assertEqual(source, "live_provider")
        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].close, 345.13)
        self.assertEqual(points[0].baseline_price, 351.12)
        self.assertEqual(points[0].time, "2026-08-20 16:00:01")

    def test_global_quote_snapshot_rejects_invalid_or_empty_price(self):
        points = parse_tencent_global_quote_snapshot(
            json.dumps({"data": {"usTSLA": {"qt": {"usTSLA": ["delay", "Tesla", "TSLA.OQ", ""]}}}}),
            quote_symbol="usTSLA",
        )

        self.assertEqual(points, [])

    def test_tencent_quote_name_parser_reads_display_name(self):
        raw = 'v_sh600519="1~贵州茅台~600519~1194.45";v_pv_none_match="1";'

        self.assertEqual(parse_tencent_quote_name(raw, symbol="sh600519"), "贵州茅台")

    def test_tencent_commodity_name_parser_does_not_return_percentage_as_name(self):
        raw = 'v_hf_GC="4002.61,-0.15,4004.50,4005.00,4010.00,3998.00,13:30:00,4008.60,4009.00,0,1,2,2026-06-25,纽约黄金";'

        self.assertIsNone(parse_tencent_quote_name(raw, symbol="hf_GC"))

    def test_eastmoney_numeric_name_falls_back_to_canonical_market_label(self):
        raw = json.dumps(
            {
                "data": {
                    "f14": "-2.1",
                    "f58": "-2.1",
                    "f2": 7741.65,
                    "f3": -210,
                    "f18": 7907.33,
                    "f124": 1788400000,
                }
            }
        )

        observation = parse_eastmoney_quote_observation(
            raw,
            symbol="bond_000012",
            provider_id="eastmoney_test",
        )

        self.assertIsNotNone(observation)
        self.assertEqual(observation.metadata["quote_name"], "国债指数")

    def test_market_signal_title_keeps_name_code_and_period_separate(self):
        signal = market_observation_to_signal(
            NormalizedMarketObservation(
                provider_id="test",
                entity="if_CU0",
                title="unused",
                metric="intraday_return",
                value=0.012,
                threshold=0.03,
                source="test",
                as_of="2026-09-03T09:30:00+08:00",
                lookback_days=1,
                affected_domains=("market",),
            )
        )

        self.assertEqual(signal.metadata["instrument_label"], "沪铜主连（上期所） · SHFE.CU0")
        self.assertEqual(signal.title, "沪铜主连（上期所） · SHFE.CU0 · 日内涨跌")

    def test_commodity_catalog_includes_domestic_cost_and_macro_futures(self):
        self.assertEqual(CATALOG_BY_SYMBOL["if_CU0"].name, "沪铜主连")
        self.assertEqual(CATALOG_BY_SYMBOL["if_EC0"].exchange, "INE")
        self.assertEqual(CATALOG_BY_SYMBOL["if_SI0"].name, "工业硅主连")
        self.assertEqual(catalog_display_name("if_SI0"), "工业硅主连（广期所）")
        self.assertEqual(CATALOG_BY_SYMBOL["if_T0"].name, "十年期国债主连")
        self.assertEqual(CATALOG_BY_SYMBOL["if_IF0"].exchange, "CFFEX")

    def test_eastmoney_details_parser_builds_sector_intraday_points(self):
        raw = json.dumps(
            {
                "data": {
                    "prePrice": 5338.09,
                    "details": [
                        "14:52:18,5454.38,89,0,2",
                        "14:52:21,5454.84,168,0,2",
                    ],
                }
            }
        )

        points = parse_eastmoney_details(raw)

        self.assertEqual(len(points), 2)
        self.assertEqual(points[0].baseline_price, 5338.09)
        self.assertEqual(points[-1].time, "14:52:21")
        self.assertEqual(points[-1].close, 5454.84)

    def test_sector_ticks_are_aggregated_to_full_day_minute_bars(self):
        raw = json.dumps(
            {
                "data": {
                    "prePrice": 100,
                    "details": [
                        "09:29:59,99.8,5,0,1",
                        "09:30:03,100.2,10,0,1",
                        "09:30:48,101.1,20,0,1",
                        "11:30:00,102.0,6,0,1",
                        "12:10:00,102.2,7,0,1",
                        "13:00:12,101.8,8,0,1",
                        "15:00:00,103.0,9,0,1",
                    ],
                }
            }
        )

        points = aggregate_eastmoney_sector_ticks(parse_eastmoney_details(raw))

        self.assertEqual([point.time for point in points], ["09:30", "11:30", "13:00", "15:00"])
        self.assertEqual(points[0].open, 100.2)
        self.assertEqual(points[0].high, 101.1)
        self.assertEqual(points[0].close, 101.1)
        self.assertEqual(points[0].volume, 30)
        self.assertEqual(points[-1].baseline_price, 100)

    def test_official_policy_repost_is_deduplicated_by_event(self):
        official = ExternalRiskSignal(
            signal_id="official-policy",
            signal_type="policy",
            title="商务部新闻发言人就将14家欧盟实体列入出口管制管控名单答记者问",
            severity="high",
            direction="negative",
            as_of="2026-07-24T09:00:00+08:00",
            entity="export_control",
            metric="policy_rule_match",
            value=1,
            threshold=1,
            affected_domains=["export_control"],
            evidence="商务部发布出口管制管控名单原文。",
            source="https://www.mofcom.gov.cn/article",
            confidence=0.70,
            metadata={"feed_id": "mofcom-policy-release"},
        )
        repost = official.model_copy(
            update={
                "signal_id": "media-repost",
                "signal_type": "news",
                "title": "商务部：将14家欧盟实体列入出口管制管控名单",
                "evidence": "第一财经转述商务部发布的出口管制管控名单。",
                "source": "https://www.yicai.com/article",
                "confidence": 0.90,
                "metadata": {"feed_id": "yicai-market-brief"},
            }
        )

        deduped = _dedupe_signals([repost, official])

        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].signal_id, "official-policy")

    def test_yahoo_chart_parser_builds_kr_stock_points(self):
        raw = json.dumps(
            {
                "chart": {
                    "result": [
                        {
                            "meta": {"previousClose": 82000},
                            "timestamp": [1782743400, 1782743700],
                            "indicators": {
                                "quote": [
                                    {
                                        "open": [82100, 82200],
                                        "high": [82300, 82400],
                                        "low": [82000, 82100],
                                        "close": [82200, 82350],
                                        "volume": [1000, 1200],
                                    }
                                ]
                            },
                        }
                    ],
                    "error": None,
                }
            }
        )

        points = parse_yahoo_chart(raw, interval="intraday")

        self.assertEqual(len(points), 2)
        self.assertEqual(points[0].baseline_price, 82000)
        self.assertEqual(points[0].timestamp, 1782743400)
        self.assertEqual(points[-1].close, 82350)

    def test_yahoo_symbol_maps_generic_kr_stock_code(self):
        self.assertEqual(_yahoo_symbol("kr_005930"), "005930.KS")
        self.assertEqual(_yahoo_symbol("kr_000660"), "000660.KS")
        self.assertEqual(_yahoo_symbol("kr_035420"), "035420.KS")
        self.assertEqual(_yahoo_symbol("hk_700"), "0700.HK")
        self.assertEqual(_yahoo_symbol("hk_00700"), "0700.HK")

    def test_eastmoney_trends_parser_preserves_preclose_baseline(self):
        raw = json.dumps(
            {
                "data": {
                    "preClose": 100.0,
                    "trends": [
                        "2026-06-26 09:30,99.0,99.5,100.0,98.8,1200,0,99.5",
                        "2026-06-26 09:31,99.5,101.0,101.2,99.5,1600,0,100.2",
                    ],
                }
            }
        )

        points = parse_eastmoney_trends(raw)

        self.assertEqual(len(points), 2)
        self.assertEqual(points[0].time, "09:30")
        self.assertEqual(points[0].baseline_price, 100.0)
        self.assertAlmostEqual(points[1].pct_change or 0, (101.0 - 99.5) / 99.5)

    def test_eastmoney_kline_parser_builds_sector_points(self):
        raw = json.dumps(
            {
                "data": {
                    "klines": [
                        "2026-06-25,100.0,101.0,102.0,99.0,10000,0,0,0,0,0",
                        "2026-06-26,101.0,99.0,102.5,98.5,12000,0,0,0,0,0",
                    ]
                }
            }
        )

        points = parse_eastmoney_klines(raw)

        self.assertEqual(len(points), 2)
        self.assertEqual(points[1].time, "2026-06-26")
        self.assertEqual(points[1].close, 99.0)
        self.assertAlmostEqual(points[1].pct_change or 0, (99.0 - 101.0) / 101.0)

    def test_eastmoney_quote_observation_builds_market_signal_input(self):
        raw = json.dumps(
            {
                "data": {
                    "f43": 63231.04,
                    "f57": "BK1326",
                    "f58": "semiconductor equipment",
                    "f60": 61647.67,
                    "f86": 1782459587,
                    "f169": 1583.37,
                    "f170": 2.57,
                }
            }
        )

        observation = parse_eastmoney_quote_observation(
            raw,
            symbol="bk_BK1326",
            provider_id="unit_provider",
        )

        self.assertIsNotNone(observation)
        self.assertEqual(observation.entity, "bk_BK1326")
        self.assertEqual(observation.source, "eastmoney.push2")
        self.assertAlmostEqual(observation.value, 0.0257)

    def test_sector_quote_series_reports_unavailable_when_history_is_not_available(self):
        provider = TencentHttpExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=True, http_enabled=True),
            fetcher=lambda _symbols: "",
        )
        provider._fetch_eastmoney_quote_series = lambda **_kwargs: []  # type: ignore[method-assign]
        intraday_points, intraday_source = provider.quote_series(symbol="bk_BK1326", interval="intraday")
        daily_points, daily_source = provider.quote_series(symbol="bk_BK1326", interval="daily")

        self.assertEqual(intraday_points, [])
        self.assertEqual(intraday_source, "provider_unavailable")
        self.assertEqual(daily_points, [])
        self.assertEqual(daily_source, "provider_unavailable")

    def test_sina_cn_futures_parsers_build_points(self):
        minute_raw = 'var _EC0=([["09:00","3715.000","3731.981","1589","21604","3697.500","2026-06-26"],["09:01","3713.000","3730.099","154","21592"]]);'
        daily_raw = 'var _EC0=([{"d":"2026-06-25","o":"3600.000","h":"3720.000","l":"3580.000","c":"3700.000","v":"1000"},{"d":"2026-06-26","o":"3700.000","h":"3740.000","l":"3680.000","c":"3715.000","v":"1200"}]);'

        minute_points = parse_sina_cn_futures_minute(minute_raw)
        daily_points = parse_sina_cn_futures_daily(daily_raw)

        self.assertEqual(len(minute_points), 2)
        self.assertEqual(minute_points[0].baseline_price, 3715.0)
        self.assertEqual(len(daily_points), 2)
        self.assertEqual(daily_points[1].close, 3715.0)

    def test_global_futures_series_returns_chart_ready_points(self):
        provider = TencentHttpExternalRiskProvider(
            ExternalRiskProviderConfig(live_enabled=True, http_enabled=True),
            fetcher=lambda _symbols: 'v_hf_GC="4002.61,-0.15,4004.50,4005.00,4010.00,3998.00,13:30:00,4008.60,4009.00,0,1,2,2026-06-25,纽约黄金";',
        )

        points, source = provider.quote_series(symbol="hf_GC", interval="daily")

        self.assertEqual(source, "sina_global_futures")
        self.assertGreaterEqual(len(points), 30)
        self.assertRegex(points[0].time, r"^\d{4}-\d{2}-\d{2}$")
        self.assertGreater(points[-1].close, 0)

    def test_quote_series_endpoint_returns_empty_when_live_provider_is_disabled(self):
        client = TestClient(app)
        with patch.dict(
            "os.environ",
            {"EXTERNAL_RISK_LIVE_ENABLED": "false", "EXTERNAL_RISK_HTTP_ENABLED": "false"},
        ):
            response = client.get("/external-risk/quote-series", params={"symbol": "sh000001", "interval": "daily"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["data"]["symbol"], "sh000001")
        self.assertEqual(payload["data"]["interval"], "daily")
        self.assertEqual(payload["meta"]["data_source"], "unavailable_live_provider")
        self.assertEqual(payload["data"]["source"], "provider_unavailable")
        self.assertEqual(payload["data"]["points"], [])

    def test_workflow_endpoint_persists_graph_to_project_file(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow_graph.json"
            payload = {
                "version": "0.1.0",
                "nodes": [{"id": "node-corning", "symbol": "us_GLW", "x": 12, "y": 34}],
                "links": [],
            }

            with patch("src.external_risk.service._workflow_graph_path", return_value=path):
                put_response = client.put("/external-risk/workflow", json=payload)
                get_response = client.get("/external-risk/workflow")

            self.assertEqual(put_response.status_code, 200)
            self.assertEqual(get_response.status_code, 200)
            self.assertTrue(path.exists())
            saved = get_response.json()["data"]
            self.assertEqual(saved["nodes"][0]["symbol"], "us_GLW")
            self.assertEqual(saved["storage_path"], str(path))

    def test_workflow_save_rejects_stale_revision_without_overwriting_saved_graph(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow_graph.json"
            first = {
                "version": "0.1.0", "revision": 0,
                "nodes": [{"id": "copper", "symbol": "hf_CAD"}], "links": [],
            }
            stale = {
                "version": "0.1.0", "revision": 0,
                "nodes": [{"id": "soy", "symbol": "hf_S"}], "links": [],
            }
            with patch("src.external_risk.service._workflow_graph_path", return_value=path):
                first_response = client.put("/external-risk/workflow", json=first)
                stale_response = client.put("/external-risk/workflow", json=stale)
                saved_response = client.get("/external-risk/workflow")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.json()["data"]["revision"], 1)
        self.assertEqual(stale_response.status_code, 409)
        self.assertEqual(stale_response.json()["error"]["code"], "EXTERNAL_RISK_WORKFLOW_CONFLICT")
        self.assertEqual(saved_response.json()["data"]["nodes"][0]["symbol"], "hf_CAD")

    def test_complex_semiconductor_workflow_is_evidence_bounded(self):
        graph = ExternalRiskService().workflow_graph()

        self.assertEqual({node.symbol for node in graph.nodes}, {
            "if_SI0", "hf_NG", "if_CU0", "sh688146", "sh688268",
            "sh603688", "sh688019", "sh688012", "sh688981", "us_NVDA",
        })
        self.assertEqual(len(graph.links), 9)
        self.assertTrue(all(link.relation_id for link in graph.links))
        self.assertTrue(all(link.correlation_layers for link in graph.links))
        links = {link.relation_id: link for link in graph.links}
        commercial = links["rel-public-cssc-gas-smic-2025"]
        self.assertEqual((commercial.source, commercial.target), ("supplier-cssc-gas", "enterprise-smic"))
        self.assertEqual(commercial.relationship_scope, "commercial_relationship")
        self.assertEqual(commercial.evidence_grade, "document_referenced")
        proxies = [link for link in graph.links if link.relation_id != commercial.relation_id]
        self.assertTrue(all(link.evidence_grade == "scenario_proxy" for link in proxies))
        self.assertTrue(all(link.confirmed_by and link.confirmed_at and link.evidence_refs for link in graph.links))
        self.assertTrue(all(link.boundary_note for link in graph.links))
        projections = {item.projection: item.relation_ids for item in graph.relationship_projections}
        self.assertEqual(len(projections["product_supply_chain"]), 9)
        self.assertTrue(projections["supplier_master"])
        self.assertEqual(len(projections["commodity_futures"]), 3)
        self.assertEqual(graph.supply_chain_sync.synchronized_supplier_ids, [
            "supplier-hq-gas", "supplier-hq-gas-secondary", "supplier-hq-quartz", "supplier-hq-slurry",
        ])
        self.assertEqual([item.node_id for item in graph.supply_chain_sync.unbound_supplier_nodes], ["supplier-amec-unbound"])

    def test_market_dashboard_exposes_runtime_and_relationship_boundaries(self):
        data = ExternalRiskService().market_dashboard(include_live=False)

        self.assertEqual(data.data_quality.supply_chain_data_access, "scenario_record")
        self.assertEqual(data.data_quality.relationship_evidence_counts["document_referenced"], 1)
        self.assertEqual(data.data_quality.relationship_evidence_counts["scenario_proxy"], 8)
        self.assertIn("比赛演练", data.data_quality.relationship_boundary)

    def test_unconfirmed_relationship_does_not_create_formal_chain_transmission(self):
        signal = ExternalRiskSignal(
            signal_id="copper-risk", signal_type="commodity_futures", title="Copper up", severity="high",
            direction="negative", as_of="2026-08-20T10:00:00Z", entity="hf_CAD", metric="intraday_return",
            value=0.04, threshold=0.02, affected_domains=["supply_chain"], evidence="cost", source="qa", confidence=0.9,
        )
        graph = ExternalRiskWorkflowGraph(
            nodes=[ExternalRiskWorkflowNode(id="copper", symbol="hf_CAD"), ExternalRiskWorkflowNode(id="supplier", symbol="SUP", node_kind="supplier")],
            links=[ExternalRiskWorkflowLink(source="copper", target="supplier")],
        )

        self.assertEqual(_chain_alerts([signal], graph), [])
        graph.links[0].confirmed_by = "risk-owner"
        graph.links[0].confirmed_at = "2026-08-20T10:01:00Z"
        self.assertEqual(_chain_alerts([signal], graph)[0].affected_node_ids, ["copper", "supplier"])

    def test_workflow_conflict_returns_diff_and_controlled_merge_preserves_server_additions(self):
        client = TestClient(app)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow_graph.json"
            first = {"version": "0.1.0", "revision": 0, "nodes": [{"id": "server", "symbol": "hf_CAD"}], "links": []}
            stale = {"version": "0.1.0", "revision": 0, "nodes": [{"id": "draft", "symbol": "hf_XPD"}], "links": []}
            with patch("src.external_risk.service._workflow_graph_path", return_value=path):
                self.assertEqual(client.put("/external-risk/workflow", json=first).status_code, 200)
                conflict = client.put("/external-risk/workflow", json=stale)
                merged = client.post("/external-risk/workflow/merge", json={
                    "base_revision": 0, "draft": stale, "confirmed_by": "qa-owner", "confirmation_note": "retain local palladium node",
                })

        self.assertEqual(conflict.status_code, 409)
        self.assertTrue(conflict.json()["merge_required"])
        self.assertIn("server", conflict.json()["diff"]["nodes"]["server_only"])
        relations = conflict.json()["diff"]["relations"]
        self.assertIn("draft_added_unconfirmed_relation_ids", relations)
        self.assertIn("preexisting_unconfirmed_relation_ids", relations)
        self.assertIn("changed_unconfirmed_relation_ids", relations)
        self.assertEqual(merged.status_code, 200)
        node_ids = {item["id"] for item in merged.json()["data"]["nodes"]}
        self.assertEqual(node_ids, {"server", "draft"})
        self.assertEqual(merged.json()["data"]["merge_audit"][-1]["confirmed_by"], "qa-owner")

    def test_single_domain_market_match_does_not_auto_create_legal_task_without_confirmation(self):
        signal = ExternalRiskSignal(
            signal_id="single-domain", signal_type="commodity_futures", title="Copper up", severity="high",
            direction="negative", as_of="2026-08-20T10:00:00Z", entity="hf_CAD", metric="intraday_return",
            value=0.04, threshold=0.02, affected_domains=["supply_chain"], evidence="cost", source="market", confidence=0.9,
        )

        self.assertEqual(_live_signal_legal_query_tasks([signal]), [])
        signal.metadata["legal_task_confirmed"] = True
        self.assertEqual(len(_live_signal_legal_query_tasks([signal])), 1)

    def test_workflow_save_derives_explicit_supplier_binding_from_canvas_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow_graph.json"
            graph = ExternalRiskWorkflowGraph(
                nodes=[
                    ExternalRiskWorkflowNode(id="market", symbol="hf_CAD"),
                    ExternalRiskWorkflowNode(
                        id="supplier", symbol="SIM-CU", node_kind="supplier", supplier_id="supplier-copper",
                    ),
                ],
                bound_supplier_ids=["untrusted-client-value"],
            )
            with patch("src.external_risk.service._workflow_graph_path", return_value=path):
                saved = ExternalRiskService().save_workflow_graph(graph)

        self.assertEqual(saved.bound_supplier_ids, ["supplier-copper"])
        self.assertEqual(saved.revision, 1)

    def test_workflow_save_reports_supply_map_sync_and_unbound_supplier_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = root / "workflow_graph.json"
            supplier_path = root / "supply_chain.json"
            supplier_path.write_text(json.dumps({"version": 1, "suppliers": [{"supplier_id": "supplier-gas"}]}), encoding="utf-8")
            graph = ExternalRiskWorkflowGraph(
                nodes=[
                    ExternalRiskWorkflowNode(id="gas", symbol="sh688146", node_kind="supplier", supplier_id="supplier-gas"),
                    ExternalRiskWorkflowNode(id="cmp", symbol="sh688019", name="CMP 材料候选", node_kind="supplier"),
                    ExternalRiskWorkflowNode(id="smic", symbol="sh688981", node_kind="enterprise"),
                ],
            )
            service = ExternalRiskService(supply_chain_repository=SupplyChainRepository(supplier_path))
            with patch("src.external_risk.service._workflow_graph_path", return_value=graph_path):
                saved = service.save_workflow_graph(graph)

        self.assertEqual(saved.supply_chain_sync.status, "action_required")
        self.assertEqual(saved.supply_chain_sync.synchronized_supplier_ids, ["supplier-gas"])
        self.assertEqual(saved.supply_chain_sync.missing_supplier_ids, [])
        self.assertEqual([item.node_id for item in saved.supply_chain_sync.unbound_supplier_nodes], ["cmp"])
        self.assertIn("前往供应链地图", saved.supply_chain_sync.message)

    def test_live_signal_filter_keeps_company_material_and_graph_matched_evidence_only(self):
        company = ExternalRiskService().context().company
        graph = ExternalRiskWorkflowGraph(
            revision=4,
            nodes=[ExternalRiskWorkflowNode(id="copper", symbol="hf_CAD")],
        )
        copper = ExternalRiskSignal(
            signal_id="live-copper", signal_type="commodity_futures", title="Copper rises",
            severity="high", direction="negative", as_of="2026-08-20T10:00:00+08:00",
            entity="hf_CAD", metric="intraday_return", value=0.04, threshold=0.02,
            affected_domains=["supply_chain"], evidence="copper cost increased", source="provider",
            metadata={"commodity_group": "copper"},
        )
        unrelated = copper.model_copy(update={
            "signal_id": "live-soy", "title": "Soybean rises", "entity": "hf_S",
            "evidence": "soybean cost increased", "metadata": {"commodity_group": "soybean"},
        })

        selected = _relevant_live_signals([copper, unrelated], company, graph)

        self.assertEqual([signal.signal_id for signal in selected], ["live-copper"])
        self.assertIn("graph_instrument", selected[0].metadata["relevance"]["matched_on"])
        self.assertEqual(selected[0].metadata["relevance"]["workflow_revision"], 4)

    def test_service_fails_closed_on_fixture_version_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            payload = load_fixture()
            payload["version"] = "0.0.9"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            service = ExternalRiskService(FixtureExternalRiskRepository(path))

            with self.assertRaises(ExternalRiskDataError):
                service.context()


if __name__ == "__main__":
    unittest.main()
