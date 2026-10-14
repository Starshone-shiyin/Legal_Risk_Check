import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from src.developer_debug import router as developer_debug_router_module
from src.developer_debug.service import DeveloperDebugService, _compile_scenario_context
from src.external_risk.schemas import (
    ExternalRiskProviderStatus,
    ExternalRiskQuotePoint,
    ExternalRiskQuoteSeries,
    ExternalRiskSignal,
)
from src.main import app


class DeveloperDebugApiTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.previous_service = developer_debug_router_module.service
        self.previous_enabled = os.environ.get("RISK_DEVELOPER_DEBUG_ENABLED")
        os.environ["RISK_DEVELOPER_DEBUG_ENABLED"] = "true"
        developer_debug_router_module.service = DeveloperDebugService(
            run_root=Path(self.temporary_directory.name) / "runs"
        )
        self.client = TestClient(app)

    def tearDown(self):
        developer_debug_router_module.service = self.previous_service
        if self.previous_enabled is None:
            os.environ.pop("RISK_DEVELOPER_DEBUG_ENABLED", None)
        else:
            os.environ["RISK_DEVELOPER_DEBUG_ENABLED"] = self.previous_enabled
        self.temporary_directory.cleanup()

    def test_semiconductor_scenario_is_isolated_repeatable_and_has_real_symbols(self):
        baseline = Path("data/supply_chain.json").read_bytes()
        created = self.client.post("/developer-debug/scenarios/china-semiconductor-ai-chain/runs")
        self.assertEqual(created.status_code, 201)
        run_id = created.json()["run_id"]

        suppliers = self.client.get(f"/developer-debug/runs/{run_id}/suppliers")
        self.assertEqual(suppliers.status_code, 200)
        items = suppliers.json()
        self.assertEqual(len(items), 8)
        self.assertEqual({item["security_code"] for item in items}, {
            "sh688019", "sh688126", "sz002371", "sh688012", "sh688981", "sh600584", "sh603986", "sz000977"
        })
        self.assertTrue(all("测试模拟" in item["notes"] for item in items))
        self.assertEqual(Path("data/supply_chain.json").read_bytes(), baseline)

        context_response = self.client.get(f"/developer-debug/runs/{run_id}/context")
        self.assertEqual(context_response.status_code, 200)
        context = context_response.json()
        lifecycle_stages = context["lifecycle_product"]["stages"]
        self.assertEqual(len(lifecycle_stages), 8)
        self.assertTrue(context["lifecycle_product"]["scenario_driven"])
        self.assertEqual(context["lifecycle"]["stages"], lifecycle_stages)
        self.assertTrue(all(stage["node_ids"] and stage["project_ids"] and stage["state_ids"] for stage in lifecycle_stages))
        self.assertTrue(all(item.get("lifecycle_stage_ids") for item in context["external_risk"]["signals"]))

        executed = self.client.post(f"/developer-debug/runs/{run_id}/execute")
        self.assertEqual(executed.status_code, 200)
        self.assertEqual(executed.json()["intake_status"], "promoted")
        self.assertEqual(executed.json()["event_status"], "confirmed")
        self.assertGreaterEqual(executed.json()["risk_count"], 1)

        reset = self.client.post(f"/developer-debug/runs/{run_id}/reset")
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(
            self.client.get(f"/developer-debug/runs/{run_id}/suppliers").json(),
            items,
        )

    def test_live_snapshot_uses_injected_sources_and_persists_selected_subject_and_canvas(self):
        selector_calls = []
        quote_symbols = []
        provider_paths = []

        def select_subject(candidates):
            selector_calls.append([candidate["node_id"] for candidate in candidates])
            return candidates[0] if len(selector_calls) == 1 else candidates[-1]

        class OfflineRssProvider:
            def __init__(self, run_path):
                self.cache_path = run_path / "intelligence_feed_cache.json"
                provider_paths.append(self.cache_path)

            def refresh(self):
                self.cache_path.write_text(json.dumps({"source": "offline-test-rss"}), encoding="utf-8")
                return [
                    ExternalRiskSignal(
                        signal_id="offline-rss-semiconductor-shipping",
                        signal_type="news",
                        title="Semiconductor shipping disruption raises supply-chain costs",
                        severity="high",
                        direction="negative",
                        as_of="2026-08-03T09:00:00+08:00",
                        entity="semiconductor supply chain",
                        metric="offline_test_industry",
                        value=1.0,
                        threshold=1.0,
                        affected_domains=["supply_chain"],
                        evidence="Observed public RSS content about semiconductor shipping and freight.",
                        source="https://example.test/rss/semiconductor-shipping",
                        confidence=0.8,
                    ),
                    ExternalRiskSignal(
                        signal_id="offline-rss-semiconductor-methanol",
                        signal_type="news",
                        title="Semiconductor methanol solvent supply disruption",
                        severity="high",
                        direction="negative",
                        as_of="2026-08-03T10:00:00+08:00",
                        entity="semiconductor electronic chemicals",
                        metric="offline_test_chemical",
                        value=1.0,
                        threshold=1.0,
                        affected_domains=["supply_chain", "contract"],
                        evidence="Observed public RSS content about semiconductor methanol solvent inputs.",
                        source="https://example.test/rss/semiconductor-methanol",
                        confidence=0.8,
                    ),
                    ExternalRiskSignal(
                        signal_id="offline-rss-stale-regulatory-action",
                        signal_type="policy",
                        title="Generic regulatory action",
                        severity="medium",
                        direction="negative",
                        as_of="2026-06-30T09:00:00+08:00",
                        entity="unrelated entity",
                        metric="offline_test_old",
                        value=1.0,
                        threshold=1.0,
                        affected_domains=["corporate_governance"],
                        evidence="A stale, unrelated regulatory action.",
                        source="https://example.test/rss/stale-regulatory-action",
                        confidence=0.8,
                    ),
                ]

            @staticmethod
            def status():
                return ExternalRiskProviderStatus(
                    provider_id="offline-test-rss",
                    provider_type="news_policy",
                    status="available",
                    mode="live",
                    message="offline injected provider",
                    runtime_access="offline_test",
                )

        def load_quote(symbol):
            quote_symbols.append(symbol)
            return ExternalRiskQuoteSeries(
                symbol=symbol,
                name=f"Offline quote {symbol}",
                provider="offline_test_quote",
                interval="intraday",
                source="eastmoney_provider",
                as_of="2026-08-03T09:31:00+08:00",
                points=[
                    ExternalRiskQuotePoint(time="09:30", close=100.0, baseline_price=99.0),
                    ExternalRiskQuotePoint(time="09:31", close=101.0, baseline_price=99.0),
                ],
                reference_price=99.0,
                change_rate=2 / 99,
                change_basis="previous_close",
                instrument_status="normal",
            )

        developer_debug_router_module.service = DeveloperDebugService(
            run_root=Path(self.temporary_directory.name) / "runs",
            subject_selector=select_subject,
            rss_provider_factory=OfflineRssProvider,
            quote_series_loader=load_quote,
            now_provider=lambda: datetime(2026, 8, 3, 12, tzinfo=timezone.utc),
        )
        global_cache = Path("data/external_risk/intelligence_feed_cache.json")
        global_workflow = Path("data/external_risk/workflow_graph.json")
        global_cache_before = global_cache.read_bytes() if global_cache.exists() else None
        global_workflow_before = global_workflow.read_bytes() if global_workflow.exists() else None

        first = self.client.post("/developer-debug/scenarios/china-semiconductor-ai-chain/runs")
        second = self.client.post("/developer-debug/scenarios/china-semiconductor-ai-chain/runs")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(len(selector_calls), 2)
        self.assertEqual(first.json()["test_subject"]["node_id"], "anji")
        self.assertEqual(second.json()["test_subject"]["node_id"], "inspur")

        run_id = first.json()["run_id"]
        snapshot_response = self.client.post(f"/developer-debug/runs/{run_id}/live-snapshot")
        self.assertEqual(snapshot_response.status_code, 200)
        snapshot = snapshot_response.json()
        self.assertEqual(snapshot["selection"], first.json()["test_subject"])
        self.assertEqual(snapshot["quote"]["symbol"], "bk_BK1326")
        self.assertEqual(quote_symbols, ["bk_BK1326", "if_EC0", "if_MA0"])
        self.assertEqual(snapshot["rss"]["matched_signal_ids"], [])
        self.assertEqual(snapshot["rss"]["industry_signal_ids"], ["offline-rss-semiconductor-shipping", "offline-rss-semiconductor-methanol"])
        self.assertNotEqual(snapshot["external_risk"]["company"]["name"], snapshot["selection"]["name"])
        self.assertIn("市场与产业链", snapshot["external_risk"]["company"]["name"])
        self.assertTrue(all(not signal["metadata"]["subject_match"] for signal in snapshot["rss"]["signals"]))
        self.assertTrue(all(signal["as_of"] != "2026-06-30T09:00:00+08:00" for signal in snapshot["rss"]["signals"]))
        commodity_signals = [signal for signal in snapshot["external_risk"]["signals"] if signal["signal_type"] == "commodity_futures"]
        self.assertEqual({signal["metadata"]["contracts"][0] for signal in commodity_signals}, {"if_EC0", "if_MA0"})
        self.assertTrue(all(signal["metadata"]["chain_linked"] for signal in commodity_signals))
        chemical_signal = next(signal for signal in commodity_signals if signal["metadata"]["contracts"] == ["if_MA0"])
        self.assertEqual(chemical_signal["metadata"]["latest_price"], 101.0)
        self.assertEqual(chemical_signal["metadata"]["linked_node_ids"], ["anji", "smic"])
        self.assertEqual(snapshot["external_risk"]["chain_alerts"][0]["path_node_ids"], [])

        executed = self.client.post(f"/developer-debug/runs/{run_id}/execute")
        self.assertEqual(executed.status_code, 200)
        self.assertEqual(executed.json()["test_subject"], snapshot["selection"])

        canvas = snapshot["market_canvas"]
        self.assertTrue(canvas["read_only"])
        self.assertEqual(len(canvas["nodes"]), 8)
        self.assertEqual(len(canvas["links"]), 7)
        self.assertEqual({node["id"] for node in canvas["nodes"]}, {
            "anji", "shanghai-silicon", "naura", "amec", "smic", "jcet", "gigadevice", "inspur",
        })
        self.assertEqual({(link["source"], link["target"]) for link in canvas["links"]}, {
            ("anji", "shanghai-silicon"), ("shanghai-silicon", "smic"),
            ("naura", "smic"), ("amec", "smic"), ("gigadevice", "smic"),
            ("smic", "jcet"), ("jcet", "inspur"),
        })

        run_path = Path(self.temporary_directory.name) / "runs" / run_id
        self.assertTrue((run_path / "live_snapshot.json").exists())
        self.assertEqual(json.loads((run_path / "live_snapshot.json").read_text(encoding="utf-8")), snapshot)
        self.assertTrue((run_path / "intelligence_feed_cache.json").exists())
        self.assertEqual(provider_paths, [run_path / "intelligence_feed_cache.json"])
        self.assertEqual(global_cache.read_bytes() if global_cache.exists() else None, global_cache_before)
        self.assertEqual(global_workflow.read_bytes() if global_workflow.exists() else None, global_workflow_before)

        persisted = self.client.post(f"/developer-debug/runs/{run_id}/live-snapshot")
        self.assertEqual(persisted.status_code, 200)
        self.assertEqual(persisted.json(), snapshot)
        self.assertEqual(quote_symbols, ["bk_BK1326", "if_EC0", "if_MA0"])

        reset = self.client.post(f"/developer-debug/runs/{run_id}/reset")
        self.assertEqual(reset.status_code, 200)
        self.assertEqual(reset.json()["test_subject"], snapshot["selection"])
        self.assertEqual(len(selector_calls), 2)

    def test_alternate_industry_can_supply_custom_lifecycle_directory(self):
        fixture = {
            "scenario": {
                "company": {"company_id": "debug-energy-enterprise", "name": "储能产业链调试主体"},
                "risk_profiles": [
                    {"node_id": "source", "severity": "high", "title": "材料供给风险"},
                    {"node_id": "assembly", "severity": "medium", "title": "装配交付风险"},
                ],
                "lifecycle_stages": [
                    {"id": "assembly-phase", "label": "储能系统装配", "order": 2, "node_ids": ["assembly"]},
                    {"id": "source-phase", "label": "电芯材料来源", "order": 1, "node_ids": ["source"]},
                ],
            },
            "nodes": [
                {"node_id": "source", "supplier_id": "energy-source", "stage": "正极材料", "lifecycle": {"business_stage": "custom-source", "control_stage": "custom-control"}},
                {"node_id": "assembly", "supplier_id": "energy-assembly", "stage": "储能装配", "lifecycle": {"business_stage": "custom-assembly", "control_stage": "custom-control"}},
            ],
            "edges": [{"from": "source", "to": "assembly", "is_simulated": True, "source_ids": ["source-ref"]}],
            "sources": [{"source_id": "source-ref", "publisher": "测试来源", "title": "公开测试来源", "url": "https://example.invalid/source", "published_at": "2026-08-02", "retrieved_at": "2026-08-02"}],
        }
        suppliers = [
            {"supplier_id": "energy-source", "name": "储能材料企业", "category": "正极材料", "province": "江苏", "country": "中国", "security_code": "sh600000"},
            {"supplier_id": "energy-assembly", "name": "储能装配企业", "category": "系统装配", "province": "浙江", "country": "中国", "security_code": "sz000001"},
        ]
        context = _compile_scenario_context(
            {"run_id": "alternate-energy-run", "title": "储能测试", "industry": "储能", "disclaimer": "仅用于测试"},
            fixture,
            suppliers,
        )
        stages = context["lifecycle_product"]["stages"]
        self.assertEqual([stage["stage_id"] for stage in stages], ["source-phase", "assembly-phase"])
        self.assertEqual([stage["label"] for stage in stages], ["电芯材料来源", "储能系统装配"])
        self.assertEqual(len(context["internal_risk"]["risk_items"]), 2)
        self.assertTrue(all(item["lifecycle_stage"] == "commercialization" for item in context["internal_risk"]["risk_items"]))

    def test_debug_runs_are_hidden_without_local_flag(self):
        os.environ["RISK_DEVELOPER_DEBUG_ENABLED"] = "false"
        self.assertEqual(self.client.get("/developer-debug/status").status_code, 404)
        response = self.client.post("/developer-debug/scenarios/china-semiconductor-ai-chain/runs")
        self.assertEqual(response.status_code, 404)

    def test_regular_risk_services_remain_available_when_debug_is_disabled(self):
        """The normal workspace must not depend on the isolated debug scenario API."""
        os.environ["RISK_DEVELOPER_DEBUG_ENABLED"] = "false"
        os.environ["RISK_DEMO_IDENTITY_ENABLED"] = "true"

        responses = [
            self.client.get("/product/dashboard/summary"),
            self.client.get("/product/legal/workspace"),
            self.client.get("/product/lifecycle/risk"),
            self.client.get("/product/risks"),
            self.client.get("/supply-chain/suppliers"),
            self.client.get("/internal-risk/workflow"),
            self.client.get("/internal-risk/management-assistance", params={"company_id": "demo-ai-enterprise"}),
            self.client.get("/risk-intake/scopes/demo-ai-enterprise"),
            self.client.get("/risk-intake/external-cases", params={"company_id": "demo-ai-enterprise"}),
            self.client.get("/external-risk/market-dashboard", params={"include_live": "false"}),
            self.client.get("/external-risk/workflow"),
            self.client.get("/documents/capabilities"),
            self.client.get("/skills/node-types"),
            self.client.get("/settings/runtime"),
        ]

        self.assertEqual([response.status_code for response in responses], [200] * len(responses))


if __name__ == "__main__":
    unittest.main()
