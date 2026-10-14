import unittest
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.external_risk.provider_config import ExternalRiskProviderConfig
from src.external_risk.schemas import WebSearchPlan, WebSearchResult
from src.external_risk.web_search import (
    DuckDuckGoHtmlProvider,
    BingHtmlProvider,
    OnlineSearchService,
    TavilySearchProvider,
    classify_search_intent,
    classify_source_tier,
    is_recent_risk_overview_question,
    source_trust_score,
    should_search_for_retrieval_gap,
)
from src.rag.evidence import build_context
from src.main import app


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit: int) -> bytes:
        return self.content


class WebSearchTest(unittest.TestCase):
    def test_ask_defaults_to_auto_but_can_be_explicitly_disabled(self):
        from src.main import AskRequest

        self.assertEqual(AskRequest(question="latest policy").online_search_mode, "auto")
        self.assertEqual(AskRequest(question="legal concept", online_search_mode="off").online_search_mode, "off")

    def test_web_evidence_builds_a_context_without_vector_similarity(self):
        context = build_context([
            {
                "type": "web_result",
                "citation": "[web source]",
                "content": "current fact",
                "trust_score": 1.0,
            }
        ])
        self.assertIn("trust=1.00", context)
        self.assertIn("current fact", context)

    def test_auto_mode_searches_explicit_lookups_but_not_supported_local_concepts(self):
        intent, trigger = classify_search_intent("什么是附随义务")
        self.assertEqual(intent, "none")
        self.assertEqual(trigger, "no_realtime_marker")
        intent, _ = classify_search_intent("什么是附随义务", domain="legal")
        self.assertEqual(intent, "none")

        intent, trigger = classify_search_intent("请检索附随义务的法条依据")
        self.assertEqual(intent, "legal_reference")
        self.assertEqual(trigger, "explicit_source_lookup")

        intent, _ = classify_search_intent("最新的数据出境监管政策")
        self.assertEqual(intent, "legal_update")

    def test_recent_risk_overview_uses_controlled_realtime_search(self):
        question = "最近有没有需要注意的风险事项"
        self.assertTrue(is_recent_risk_overview_question(question))
        intent, trigger = classify_search_intent(question)
        self.assertEqual(intent, "general_realtime")
        self.assertEqual(trigger, "recent_risk_overview")

    def test_retrieval_gap_promotes_legal_question_to_controlled_search(self):
        self.assertTrue(should_search_for_retrieval_gap(
            {"retrieval_confidence": 0.42, "missing_evidence": ["当前知识库未覆盖相关司法解释"]},
            question="某项司法解释对竞业限制如何规定？",
        ))
        self.assertFalse(should_search_for_retrieval_gap(
            {"retrieval_confidence": 0.91, "evidence_chain": [{"source": "民法典"}]},
            question="什么是附随义务？",
        ))

    def test_plan_maps_legal_intent_to_official_domain_policy(self):
        service = OnlineSearchService(ExternalRiskProviderConfig(web_search_enabled=True))
        plan = service.plan("最新的数据出境监管政策")
        self.assertTrue(plan.should_search)
        self.assertIn("gov.cn", plan.allowed_domains)
        self.assertNotIn("reuters.com", plan.allowed_domains)

    def test_provider_filters_untrusted_results_for_official_search(self):
        raw = """
        <a class="result__a" href="https://www.gov.cn/zhengce/article">Official policy</a>
        <a class="result__snippet">Official snippet</a>
        <a class="result__a" href="https://example.com/copy">Untrusted copy</a>
        <a class="result__snippet">Untrusted snippet</a>
        """
        provider = DuckDuckGoHtmlProvider(
            ExternalRiskProviderConfig(web_search_enabled=True),
            opener=lambda *_args, **_kwargs: _FakeResponse(raw),
        )
        results = provider.search("policy", max_results=5, allowed_domains=("gov.cn",))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_tier, "official")
        self.assertEqual(provider.status().runtime_access, "live_called")

    def test_bing_provider_parses_results_and_enforces_domain_policy(self):
        raw = """
        <li class="b_algo"><h2><a href="https://www.gov.cn/zhengce/article">Official policy</a></h2>
        <div class="b_caption"><p>Official snippet</p></div></li>
        <li class="b_algo"><h2><a href="https://example.com/copy">Untrusted copy</a></h2>
        <div class="b_caption"><p>Untrusted snippet</p></div></li>
        """
        provider = BingHtmlProvider(
            ExternalRiskProviderConfig(web_search_enabled=True),
            opener=lambda *_args, **_kwargs: _FakeResponse(raw),
        )
        results = provider.search("policy", max_results=5, allowed_domains=("gov.cn",))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Official policy")
        self.assertEqual(results[0].snippet, "Official snippet")
        self.assertEqual(results[0].source_tier, "official")

    def test_source_tier_and_trust_score_are_explicit(self):
        self.assertEqual(classify_source_tier("https://www.gov.cn/a"), "official")
        self.assertEqual(classify_source_tier("https://example.com/a"), "unverified_web")
        self.assertEqual(source_trust_score("https://www.gov.cn/a"), 1.0)

    def test_tavily_provider_normalizes_api_results_and_enforces_domain_policy(self):
        raw = json.dumps({
            "results": [
                {
                    "title": "Official policy",
                    "url": "https://www.gov.cn/zhengce/article",
                    "content": "policy text",
                    "published_date": "2026-08-09",
                },
                {
                    "title": "Untrusted copy",
                    "url": "https://example.com/copy",
                    "content": "copy",
                },
            ]
        })
        provider = TavilySearchProvider(
            ExternalRiskProviderConfig(web_search_enabled=True, web_search_api_key="test-key"),
            opener=lambda *_args, **_kwargs: _FakeResponse(raw),
        )
        results = provider.search("policy", max_results=5, allowed_domains=("gov.cn",))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source_tier, "official")
        self.assertEqual(results[0].published_at, "2026-08-09")
        self.assertEqual(provider.status().runtime_access, "live_called")

    def test_disabled_service_fails_closed_without_provider_call(self):
        class FailProvider:
            provider_id = "fake"

            def status(self):
                from src.external_risk.web_search import SearchProviderStatus
                return SearchProviderStatus(provider_id="fake", enabled=False, message="disabled")

            def search(self, **_kwargs):
                raise AssertionError("disabled search must not call provider")

        service = OnlineSearchService(ExternalRiskProviderConfig(web_search_enabled=False), provider=FailProvider())
        plan = service.plan("最新监管政策")
        self.assertTrue(plan.should_search)
        self.assertEqual(service.search(plan), [])

    def test_api_returns_plan_and_disabled_provider_metadata(self):
        client = TestClient(app)
        with patch.dict("os.environ", {"EXTERNAL_RISK_WEB_SEARCH_ENABLED": "false"}):
            response = client.post(
                "/external-risk/web-search",
                json={"question": "最新的数据出境监管政策", "mode": "auto", "domain": "legal"},
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plan"]["intent"], "legal_update")
        self.assertTrue(payload["plan"]["should_search"])
        self.assertFalse(payload["provider_enabled"])
        self.assertEqual(payload["items"], [])
        self.assertIsNotNone(payload["error"])

    def test_ask_passes_online_results_as_separate_evidence_when_enabled(self):
        from src.main import AskRequest, _run_ask_request

        result = {
            "answer": "已有本地法条证据支持该问题。",
            "confidence_score": 0.7,
            "answer_confidence": 0.7,
            "retrieval_confidence": 0.7,
            "needs_human_review": True,
            "missing_evidence": [],
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": {},
            "evidence_chain": [],
            "filters": {},
            "debug_info": {},
        }

        class FakeSearch:
            def plan(self, *_args, **_kwargs):
                return WebSearchPlan(
                    mode="force", intent="general_realtime", trigger="test",
                    queries=["test"], should_search=True,
                )

            def search(self, _plan):
                return [WebSearchResult(title="Current event", url="https://www.gov.cn/event", snippet="evidence")]

        with patch("src.main.rag_query", return_value=result) as query_mock:
            with patch("src.main.OnlineSearchService", return_value=FakeSearch()):
                _run_ask_request(AskRequest(question="latest event", online_search_mode="force"))

        external = query_mock.call_args.kwargs["external_evidence"]
        self.assertEqual(len(external), 1)
        self.assertEqual(external[0]["type"], "web_result")
        self.assertEqual(external[0]["authority_level"], "official")

    def test_auto_mode_retries_with_web_evidence_after_local_source_gap(self):
        from src.main import AskRequest, _run_ask_request

        initial = {
            "answer": "local answer",
            "confidence_score": 0.45,
            "answer_confidence": 0.45,
            "retrieval_confidence": 0.45,
            "needs_human_review": True,
            "missing_evidence": ["missing primary source"],
            "risk_level": None,
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": {},
            "evidence_chain": [],
            "filters": {},
            "debug_info": {},
        }
        enriched = {**initial, "answer": "enriched answer", "missing_evidence": [], "retrieval_confidence": 0.8}

        class FakeSearch:
            def plan(self, *_args, **kwargs):
                should_search = kwargs["mode"] == "force"
                return WebSearchPlan(
                    mode=kwargs["mode"], intent="legal_reference", trigger="test",
                    queries=["test"] if should_search else [], should_search=should_search,
                    allowed_domains=["gov.cn"],
                )

            def search(self, _plan):
                return [WebSearchResult(title="Official source", url="https://www.gov.cn/law", snippet="evidence")]

        with patch("src.main.rag_query", side_effect=[initial, enriched]) as query_mock:
            with patch("src.main.OnlineSearchService", return_value=FakeSearch()):
                _run_ask_request(AskRequest(question="某项法律如何规定？", online_search_mode="auto"))

        self.assertEqual(query_mock.call_count, 2)
        external = query_mock.call_args.kwargs["external_evidence"]
        self.assertEqual(len(external), 1)
        self.assertEqual(external[0]["authority_level"], "official")

    def test_recent_risk_overview_returns_observations_without_legal_gate(self):
        from src.main import AskRequest, _run_ask_request

        class FakeSearch:
            def plan(self, *_args, **kwargs):
                return WebSearchPlan(
                    mode=kwargs["mode"], intent="general_realtime", trigger="recent_risk_overview",
                    queries=["test"], should_search=True,
                )

            def search(self, _plan):
                return [WebSearchResult(
                    title="监管机构发布最新公告",
                    url="https://www.gov.cn/example",
                    snippet="需要进一步核验是否与目标企业相关。",
                    source_name="国务院",
                    fetched_at="2026-08-22T00:00:00+00:00",
                )]

        with patch("src.main.rag_query") as query_mock:
            with patch("src.main.OnlineSearchService", return_value=FakeSearch()):
                payload = _run_ask_request(AskRequest(question="最近有没有需要注意的风险事项"))

        query_mock.assert_not_called()
        self.assertEqual(payload["filters"]["answer_status"], "recent_risk_observation")
        self.assertIn("待核验信号", payload["answer"])
        self.assertEqual(len(payload["evidence_chain"]), 1)
        self.assertIsNone(payload["risk_level"])

    def test_recent_risk_overview_explains_unavailable_signals(self):
        from src.main import AskRequest, _run_ask_request

        payload = _run_ask_request(AskRequest(
            question="最近有没有需要注意的风险事项",
            online_search_mode="off",
        ))

        self.assertEqual(payload["filters"]["answer_status"], "recent_risk_signals_unavailable")
        self.assertIn("联网检索已关闭", payload["answer"])
        self.assertNotIn("知识库缺少", payload["answer"])


if __name__ == "__main__":
    unittest.main()
