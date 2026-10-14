import json
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from tools.export_openapi_schema import build_openapi_schema
from tools.export_api_contract_bundle import build_api_contract_bundle
from tools.export_api_field_catalog import build_api_field_catalog

from src.main import (
    AskRequest,
    AskResponse,
    RiskAnalyzeRequest,
    RiskAnalyzeResponse,
    RiskReportExportRequest,
    RiskReportResponse,
    _error_response,
    app,
)
from src.core.vectorstore import COLLECTION_NAME


EXAMPLE_PAYLOAD_PATH = Path("tests/fixtures/api_contract_example_payloads_v0.4.16.4.json")


def load_example_payloads() -> dict:
    payload = json.loads(EXAMPLE_PAYLOAD_PATH.read_text(encoding="utf-8"))
    return payload["examples"]


def assert_common_filter_kwargs(testcase: unittest.TestCase, kwargs: dict, request_payload: dict) -> None:
    for field in [
        "collection_name",
        "k",
        "doc_type",
        "block_type",
        "document_type",
        "law_name",
        "source",
        "law_level",
        "authority_level",
        "jurisdiction",
        "issuing_authority",
        "legal_effect",
        "standard_type",
        "case_type",
        "patent_type",
        "category",
        "version",
        "score_threshold",
        "debug",
    ]:
        testcase.assertEqual(kwargs[field], request_payload.get(field))


class ApiContractTest(unittest.TestCase):
    def test_openapi_exposes_stable_core_paths(self):
        schema = app.openapi()
        paths = schema.get("paths", {})

        self.assertIn("/health", paths)
        self.assertIn("get", paths["/health"])
        for path in ["/ask", "/risk/analyze", "/risk/report", "/risk/report/export"]:
            self.assertIn(path, paths)
            self.assertIn("post", paths[path])

    def test_request_defaults_are_frontend_safe(self):
        ask = AskRequest(question="测试问题")
        self.assertEqual(ask.k, 5)
        self.assertEqual(ask.collection_name, COLLECTION_NAME)
        self.assertEqual(ask.doc_type, "article")
        self.assertIsNone(ask.category)
        self.assertFalse(ask.debug)

        risk = RiskAnalyzeRequest(scenario="测试场景")
        self.assertEqual(risk.k, 5)
        self.assertEqual(risk.collection_name, COLLECTION_NAME)
        self.assertEqual(risk.doc_type, "article")
        self.assertFalse(risk.debug)

        export = RiskReportExportRequest(scenario="测试场景")
        self.assertEqual(export.export_format, "markdown")
        self.assertTrue(export.include_evidence_chain)
        self.assertFalse(export.include_source_analysis)

    def test_response_models_keep_frontend_required_fields(self):
        ask_schema = AskResponse.model_json_schema()
        self.assertEqual(
            set(ask_schema.get("required", [])),
            {"answer", "confidence_score", "evidence_chain", "filters"},
        )
        for field in [
            "answer_confidence",
            "retrieval_confidence",
            "risk_level",
            "risk_types",
            "recommended_actions",
            "citation_integrity",
            "debug_info",
        ]:
            self.assertIn(field, ask_schema["properties"])

        analyze_schema = RiskAnalyzeResponse.model_json_schema()
        self.assertEqual(
            set(analyze_schema.get("required", [])),
            {"scenario", "summary", "risk_level", "confidence"},
        )
        for field in [
            "risk_types",
            "risk_categories",
            "legal_basis",
            "recommended_actions",
            "evidence_chain",
            "filters",
            "debug_info",
        ]:
            self.assertIn(field, analyze_schema["properties"])

        report_schema = RiskReportResponse.model_json_schema()
        self.assertEqual(
            set(report_schema.get("required", [])),
            {"title", "scenario", "executive_summary", "risk_level"},
        )
        for field in [
            "risk_findings",
            "action_plan",
            "legal_basis",
            "confidence",
            "human_review_required",
            "review_reasons",
            "evidence_chain",
            "source_analysis",
        ]:
            self.assertIn(field, report_schema["properties"])

    def test_error_response_shape_is_stable(self):
        response = _error_response(504, "LLM_TIMEOUT", "模型响应超时")

        self.assertEqual(response.status_code, 504)
        payload = json.loads(response.body.decode("utf-8"))
        self.assertEqual(payload, {"error": {"code": "LLM_TIMEOUT", "message": "模型响应超时"}})

    def test_ask_timeout_error_returns_unified_504_envelope(self):
        client = TestClient(app)
        with patch("src.main.rag_query", side_effect=TimeoutError):
            response = client.post("/ask", json={"question": "测试问题"})

        self.assertEqual(response.status_code, 504)
        self.assertEqual(
            response.json(),
            {"error": {"code": "LLM_TIMEOUT", "message": "AI 模型响应超时，请简化问题后重试。"}},
        )

    def test_report_export_markdown_content_type_is_stable(self):
        client = TestClient(app)
        with patch("src.main.generate_risk_report_export", return_value="# 风险报告\n") as mocked:
            response = client.post(
                "/risk/report/export",
                json={"scenario": "测试场景", "export_format": "markdown"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/markdown", response.headers["content-type"])
        self.assertEqual(response.text, "# 风险报告\n")
        mocked.assert_called_once()

    def test_report_export_json_content_type_is_stable(self):
        client = TestClient(app)
        payload = {"title": "风险报告", "risk_level": "medium"}
        with patch("src.main.generate_risk_report_export", return_value=payload) as mocked:
            response = client.post(
                "/risk/report/export",
                json={"scenario": "测试场景", "export_format": "json"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("application/json", response.headers["content-type"])
        self.assertEqual(response.json(), payload)
        mocked.assert_called_once()

    def test_report_export_rejects_unknown_format_before_runtime_call(self):
        client = TestClient(app)
        with patch("src.main.generate_risk_report_export") as mocked:
            response = client.post(
                "/risk/report/export",
                json={"scenario": "测试场景", "export_format": "pdf"},
            )

        self.assertEqual(response.status_code, 422)
        mocked.assert_not_called()

    def test_ask_endpoint_uses_rag_query_and_returns_contract_payload(self):
        client = TestClient(app)
        examples = load_example_payloads()
        response_payload = examples["ask_response"]

        with patch("src.main.rag_query", return_value=response_payload) as mocked:
            response = client.post("/ask", json=examples["ask_request"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], response_payload["answer"])
        self.assertEqual(response.json()["evidence_chain"], response_payload["evidence_chain"])
        mocked.assert_called_once()
        _, kwargs = mocked.call_args
        self.assertEqual(mocked.call_args.args, (examples["ask_request"]["question"],))
        assert_common_filter_kwargs(self, kwargs, examples["ask_request"])

    def test_ask_endpoint_falls_back_to_local_knowledge_when_rag_fails(self):
        client = TestClient(app)

        with patch("src.main.rag_query", side_effect=RuntimeError("qdrant unavailable")):
            response = client.post("/ask", json={"question": "企业把客户数据传输给境外云服务商，需要关注哪些法律风险？"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("个人信息出境", payload["answer"])
        self.assertTrue(payload["needs_human_review"])
        self.assertEqual(payload["filters"]["fallback"], "local_knowledge")
        self.assertEqual(payload["debug_info"]["fallback"], "local_knowledge")
        self.assertTrue(payload["evidence_chain"])

    def test_ask_endpoint_does_not_use_data_fallback_for_uncovered_domains(self):
        client = TestClient(app)

        with patch("src.main.rag_query", side_effect=RuntimeError("qdrant unavailable")):
            response = client.post("/ask", json={"question": "什么是股权并购？"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("个人信息出境", payload["answer"])
        self.assertEqual(payload["filters"]["fallback"], "local_knowledge_unavailable_for_domain")
        self.assertEqual(payload["evidence_chain"], [])
        self.assertTrue(payload["needs_human_review"])

    def test_ask_endpoint_clears_irrelevant_evidence_when_direct_basis_is_missing(self):
        client = TestClient(app)
        response_payload = {
            "answer": "检索到的材料中不包含关于员工违反竞业协议的处理规定，因此无法基于现有依据回答。",
            "confidence_score": 0.5,
            "evidence_chain": [{"law_name": "中华人民共和国公司法", "article": "第一百六十三条"}],
            "filters": {},
            "missing_evidence": ["最高相似度偏低，检索依据可能不足"],
            "risk_types": ["劳动争议"],
        }

        with patch("src.main.rag_query", return_value=response_payload):
            response = client.post("/ask", json={"question": "员工违反竞业协议怎么办？"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["evidence_chain"], [])
        self.assertEqual(payload["rejected_evidence"], response_payload["evidence_chain"])
        self.assertEqual(payload["risk_types"], [])
        self.assertTrue(payload["needs_human_review"])
        self.assertEqual(payload["filters"]["answer_status"], "insufficient_direct_evidence")
        self.assertIn("竞业限制", payload["missing_evidence"][0])

    def test_ask_endpoint_preserves_evidence_when_answer_is_substantive_but_review_needed(self):
        client = TestClient(app)
        response_payload = {
            "answer": "根据检索到的个人信息保护法依据，企业应建立处理活动记录并开展合规审计，建议先梳理数据清单。",
            "confidence_score": 0.58,
            "evidence_chain": [{"law_name": "中华人民共和国个人信息保护法", "article": "第五十四条"}],
            "filters": {},
            "missing_evidence": ["最高相似度偏低，检索依据可能不足"],
            "risk_types": ["个人信息合规风险"],
            "recommended_actions": ["梳理数据清单"],
        }

        with patch("src.main.rag_query", return_value=response_payload):
            response = client.post("/ask", json={"question": "公司处理用户数据是否存在合规风险？"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["evidence_chain"], response_payload["evidence_chain"])
        self.assertIn(response_payload["risk_types"][0], payload["risk_types"])
        self.assertEqual(payload["filters"]["answer_status"], "answered_with_review_note")
        self.assertTrue(payload["needs_human_review"])

    def test_open_data_compliance_guidance_gets_practical_plan_without_losing_evidence(self):
        client = TestClient(app)
        response_payload = {
            "answer": "根据您提供的依据材料，其中未包含针对初创公司低成本开展数据合规工作的具体指引。",
            "confidence_score": 0.52,
            "answer_confidence": 0.52,
            "evidence_chain": [
                {"law_name": "中华人民共和国个人信息保护法", "article": "第五十四条"},
                {"law_name": "中华人民共和国数据安全法", "article": "第五条"},
            ],
            "filters": {},
            "missing_evidence": ["最高相似度偏低，检索依据可能不足"],
            "risk_types": [],
            "recommended_actions": [],
        }

        with patch("src.main.rag_query", return_value=response_payload):
            response = client.post("/ask", json={"question": "作为初创公司，没有专门法务，应该如何低成本地开展数据合规工作？"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("低成本路径", payload["answer"])
        self.assertIn("建立数据清单和处理目的台账。", payload["recommended_actions"])
        self.assertIn("数据合规体系不足", payload["risk_types"])
        self.assertEqual(len(payload["evidence_chain"]), 2)
        self.assertEqual(payload["filters"]["answer_status"], "guidance_with_limited_direct_basis")
        self.assertTrue(payload["needs_human_review"])

    def test_open_data_compliance_question_preserves_substantive_rag_answer(self):
        client = TestClient(app)
        response_payload = {
            "answer": "企业应先核对处理目的是否发生变化，并在向第三方提供信息前完成相应告知和同意核验。",
            "confidence_score": 0.78,
            "evidence_chain": [{"law_name": "中华人民共和国个人信息保护法", "article": "第二十三条"}],
            "filters": {},
            "missing_evidence": [],
            "risk_types": ["个人信息对外提供风险"],
            "recommended_actions": ["核对对外提供场景的告知与同意记录"],
        }

        with patch("src.main.rag_query", return_value=response_payload):
            response = client.post("/ask", json={"question": "公司应该如何开展用户数据合规管理？"})

        payload = response.json()
        self.assertEqual(payload["answer"], response_payload["answer"])
        self.assertNotEqual(payload["filters"].get("answer_status"), "guidance_with_limited_direct_basis")

    def test_risk_analyze_endpoint_uses_analyzer_and_returns_contract_payload(self):
        client = TestClient(app)
        examples = load_example_payloads()
        response_payload = examples["risk_analyze_response"]

        with patch("src.main.analyze_risk", return_value=response_payload) as mocked:
            response = client.post("/risk/analyze", json=examples["risk_analyze_request"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scenario"], response_payload["scenario"])
        self.assertEqual(response.json()["risk_level"], response_payload["risk_level"])
        mocked.assert_called_once()
        _, kwargs = mocked.call_args
        self.assertEqual(mocked.call_args.args, (examples["risk_analyze_request"]["scenario"],))
        assert_common_filter_kwargs(self, kwargs, examples["risk_analyze_request"])

    def test_risk_analyze_endpoint_passes_materials_and_expected_domain(self):
        client = TestClient(app)
        examples = load_example_payloads()
        response_payload = examples["risk_analyze_response"]
        material = [{"task_id": "a" * 32, "filename": "case.pdf", "content": "事实材料"}]
        request = {
            **examples["risk_analyze_request"],
            "document_task_ids": ["a" * 32],
            "expected_risk_domain": "cross_border_supply_chain",
        }

        with patch("src.main.DocumentIngestService") as service_cls, patch("src.main.analyze_risk", return_value=response_payload) as mocked:
            service_cls.return_value.build_llm_materials.return_value = material
            response = client.post("/risk/analyze", json=request)

        self.assertEqual(response.status_code, 200)
        kwargs = mocked.call_args.kwargs
        self.assertEqual(kwargs["user_materials"], material)
        self.assertEqual(kwargs["expected_risk_domain"], "cross_border_supply_chain")

    def test_stream_fallback_uses_the_unified_response_contract(self):
        client = TestClient(app)

        with patch("src.main.rag_query", side_effect=RuntimeError("qdrant unavailable")):
            response = client.post("/ask/stream", json={"question": "什么是股权并购？"})

        self.assertEqual(response.status_code, 200)
        events = [line[6:] for line in response.text.splitlines() if line.startswith("data: ")]
        final = next(json.loads(event)["result"] for event in events if "\"result\"" in event)
        self.assertEqual(final["retrieval_status"]["mode"], "local_fallback")
        self.assertIn("ask_route", final["filters"])

    def test_risk_report_endpoint_uses_report_generator_and_returns_contract_payload(self):
        client = TestClient(app)
        examples = load_example_payloads()
        response_payload = examples["risk_report_response"]

        with patch("src.main.generate_risk_report", return_value=response_payload) as mocked:
            response = client.post("/risk/report", json=examples["risk_report_request"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], response_payload["title"])
        self.assertEqual(response.json()["risk_findings"], response_payload["risk_findings"])
        mocked.assert_called_once()
        _, kwargs = mocked.call_args
        self.assertEqual(mocked.call_args.args, (examples["risk_report_request"]["scenario"],))
        assert_common_filter_kwargs(self, kwargs, examples["risk_report_request"])

    def test_openapi_schema_snapshot_payload_has_guardrails(self):
        payload = build_openapi_schema()

        self.assertEqual(payload["version"], app.version)
        self.assertEqual(payload["guardrails"]["rag_query"], "not_called")
        self.assertEqual(payload["guardrails"]["qdrant_access"], "not_called")
        paths = payload["openapi"]["paths"]
        for path in ["/health", "/ask", "/risk/analyze", "/risk/report", "/risk/report/export"]:
            self.assertIn(path, paths)

    def test_api_example_payload_fixture_matches_contract_models(self):
        payload = json.loads(EXAMPLE_PAYLOAD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(payload["version"], "0.4.16.4")
        self.assertEqual(payload["guardrails"]["rag_query"], "not_called")
        self.assertEqual(payload["guardrails"]["qdrant_access"], "not_called")
        self.assertEqual(payload["guardrails"]["llm_access"], "not_called")
        self.assertEqual(payload["guardrails"]["report_generation"], "not_called")
        self.assertEqual(payload["guardrails"]["frontend_integration"], "not_started")

        examples = payload["examples"]
        AskRequest(**examples["ask_request"])
        AskResponse(**examples["ask_response"])
        RiskAnalyzeRequest(**examples["risk_analyze_request"])
        RiskAnalyzeResponse(**examples["risk_analyze_response"])
        RiskAnalyzeRequest(**examples["risk_report_request"])
        RiskReportResponse(**examples["risk_report_response"])
        RiskReportResponse(**examples["risk_report_export_json"])

        markdown = examples["risk_report_export_markdown"]
        self.assertIsInstance(markdown, str)
        self.assertTrue(markdown.startswith("# "))
        self.assertIn("## 摘要", markdown)

        for key in ["risk_findings", "action_plan", "legal_basis", "evidence_chain"]:
            self.assertTrue(examples["risk_report_response"][key])
            self.assertTrue(examples["risk_report_export_json"][key])

    def test_api_contract_bundle_combines_openapi_and_examples_without_runtime_calls(self):
        payload = build_api_contract_bundle()

        self.assertEqual(payload["version"], app.version)
        self.assertEqual(payload["guardrails"]["service_started"], False)
        self.assertEqual(payload["guardrails"]["rag_query"], "not_called")
        self.assertEqual(payload["guardrails"]["qdrant_access"], "not_called")
        self.assertEqual(payload["guardrails"]["llm_access"], "not_called")
        self.assertEqual(payload["guardrails"]["report_generation"], "not_called")
        self.assertEqual(payload["guardrails"]["frontend_integration"], "not_started")
        self.assertEqual(payload["summary"]["missing_core_paths"], [])
        self.assertEqual(
            payload["summary"]["error_example_keys"],
            ["internal_error_500", "llm_timeout_504", "validation_error_422"],
        )
        for path in ["/health", "/ask", "/risk/analyze", "/risk/report", "/risk/report/export"]:
            self.assertIn(path, payload["openapi"]["paths"])
        for key in [
            "ask_request",
            "ask_response",
            "risk_analyze_request",
            "risk_analyze_response",
            "risk_report_request",
            "risk_report_response",
            "risk_report_export_markdown",
            "risk_report_export_json",
        ]:
            self.assertIn(key, payload["examples"])
        self.assertEqual(
            payload["error_examples"]["llm_timeout_504"]["body"],
            {"error": {"code": "LLM_TIMEOUT", "message": "AI 模型响应超时，请简化问题后重试。"}},
        )
        self.assertEqual(
            payload["error_examples"]["internal_error_500"]["body"],
            {"error": {"code": "INTERNAL_ERROR", "message": "内部服务错误，请稍后重试。"}},
        )
        self.assertEqual(payload["error_examples"]["validation_error_422"]["status_code"], 422)

    def test_api_field_catalog_exports_request_and_response_model_fields(self):
        payload = build_api_field_catalog()

        self.assertEqual(payload["version"], app.version)
        self.assertEqual(payload["guardrails"]["service_started"], False)
        self.assertEqual(payload["guardrails"]["rag_query"], "not_called")
        self.assertEqual(payload["guardrails"]["qdrant_access"], "not_called")
        self.assertEqual(payload["guardrails"]["llm_access"], "not_called")
        self.assertEqual(payload["guardrails"]["report_generation"], "not_called")
        self.assertEqual(payload["guardrails"]["frontend_integration"], "not_started")

        request_models = payload["models"]["requests"]
        response_models = payload["models"]["responses"]
        self.assertEqual(request_models["AskRequest"]["required_fields"], ["question"])
        self.assertEqual(request_models["RiskAnalyzeRequest"]["required_fields"], ["scenario"])
        self.assertEqual(request_models["RiskReportExportRequest"]["required_fields"], ["scenario"])
        self.assertIn("export_format", {field["name"] for field in request_models["RiskReportExportRequest"]["fields"]})
        self.assertIn("answer", response_models["AskResponse"]["required_fields"])
        self.assertIn("summary", response_models["RiskAnalyzeResponse"]["required_fields"])
        self.assertIn("title", response_models["RiskReportResponse"]["required_fields"])

        ask_defaults = {
            field["name"]: field["default"]
            for field in request_models["AskRequest"]["fields"]
        }
        self.assertEqual(ask_defaults["k"], 5)
        self.assertEqual(ask_defaults["collection_name"], COLLECTION_NAME)
        self.assertEqual(ask_defaults["doc_type"], "article")

if __name__ == "__main__":
    unittest.main()
