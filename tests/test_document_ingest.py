import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from fastapi.testclient import TestClient
from src.document_ingest.mineu_adapter import MineUAdapter, MineUError, MineUParseResult
from src.document_ingest.service import DocumentIngestError, DocumentIngestService
from src.document_ingest.storage import DocumentTaskStorage
from src.internal_risk.service import InternalRiskWorkflowService
from src.main import AskRequest, _run_ask_request, app


class StubMineU:
    mode = "local"

    def status(self):
        return {"available": True, "command": "stub-mineru", "message": "stub ready"}

    def parse(self, source_path, output_dir):
        assert source_path.name.startswith("source.")
        return MineUParseResult(markdown="# 合同\n\n付款期限为 30 日。", command="stub-mineru")


class FailingMineU(StubMineU):
    def parse(self, source_path, output_dir):
        raise MineUError("MINEU_PARSE_FAILED", "模拟解析失败")


def build_service(root: Path) -> DocumentIngestService:
    return DocumentIngestService(storage=DocumentTaskStorage(root=root), parser=StubMineU())


class DocumentIngestServiceTest(unittest.TestCase):
    def test_lightweight_mode_is_available_without_a_token(self):
        status = MineUAdapter(mode="lightweight").status()

        self.assertTrue(status["available"])
        self.assertIn("无需 Token", status["message"])

    def test_lightweight_upload_omits_content_type_for_presigned_url(self):
        class Response:
            def __init__(self, payload=None, text=""):
                self.is_error = False
                self._payload = payload
                self.text = text

            def json(self):
                return self._payload

        class Client:
            put_headers = "not-called"

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def request(self, method, url, **_):
                if method == "POST":
                    return Response({"code": 0, "data": {"task_id": "task-1", "file_url": "https://upload.test/file"}})
                return Response({"code": 0, "data": {"state": "done", "markdown_url": "https://result.test/full.md"}})

            def put(self, _url, *, content, headers=None):
                self.put_headers = headers
                self.uploaded = content.read()
                return Response()

            def get(self, _url):
                return Response(text="# 合同\n\n付款期限为 30 日。")

        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.pdf"
            source.write_bytes(b"%PDF- test")
            client = Client()
            with patch("src.document_ingest.mineu_adapter.httpx.Client", return_value=client):
                result = MineUAdapter(mode="lightweight").parse(source, Path(temp_dir) / "result")

        self.assertIsNone(client.put_headers)
        self.assertEqual(client.uploaded, b"%PDF- test")
        self.assertIn("付款期限", result.markdown)

    def test_lightweight_result_download_retries_when_cdn_is_not_ready(self):
        class Response:
            def __init__(self, text="", is_error=False):
                self.text = text
                self.is_error = is_error

        class PrimaryClient:
            def __init__(self):
                self.responses = [Response(is_error=True), Response("# 合同\n\n解析成功")]
                self.calls = 0

            def get(self, _url):
                response = self.responses[self.calls]
                self.calls += 1
                return response

        class DirectClient:
            calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def get(self, _url):
                self.calls += 1
                return Response(is_error=True)

        primary = PrimaryClient()
        direct = DirectClient()
        adapter = MineUAdapter(mode="lightweight")
        adapter.result_download_attempts = 2
        adapter.result_download_retry_seconds = 0.2

        with patch("src.document_ingest.mineu_adapter.httpx.Client", return_value=direct), patch(
            "src.document_ingest.mineu_adapter.time.sleep"
        ) as sleep:
            markdown = adapter._download_markdown(primary, "https://result.test/full.md")

        self.assertEqual(markdown, "# 合同\n\n解析成功")
        self.assertEqual(primary.calls, 2)
        self.assertEqual(direct.calls, 1)
        sleep.assert_called_once_with(0.2)

    def test_lightweight_waits_for_completed_state_before_downloading_result(self):
        adapter = MineUAdapter(mode="lightweight")
        running = {"code": 0, "data": {"state": "running", "markdown_url": "https://result.test/full.md"}}
        completed = {"code": 0, "data": {"state": "done", "markdown_url": "https://result.test/full.md"}}

        with patch.object(adapter, "_api_request", side_effect=[running, completed]) as request, patch(
            "src.document_ingest.mineu_adapter.time.monotonic", side_effect=[0, 0]
        ), patch("src.document_ingest.mineu_adapter.time.sleep") as sleep:
            result_url = adapter._wait_for_markdown_url(object(), "task-1", deadline=1)

        self.assertEqual(result_url, "https://result.test/full.md")
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(adapter.poll_seconds)

    def test_lightweight_uses_local_text_fallback_when_result_cdn_is_unavailable(self):
        adapter = MineUAdapter(mode="lightweight")
        source = Path("contract.pdf")

        with patch.object(
            adapter,
            "_parse_lightweight_cloud",
            side_effect=MineUError("MINEU_RESULT_DOWNLOAD_FAILED", "CDN unavailable"),
        ), patch.object(adapter, "_extract_local_pdf_text", return_value="# 合同\n\n本地提取文本"):
            result = adapter._parse_lightweight(source)

        self.assertIn("本地提取文本", result.markdown)
        self.assertIn("local PDF text fallback", result.command)

    def test_task_metadata_write_retries_windows_file_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = DocumentTaskStorage(root=Path(temp_dir))
            task = storage.create_task(
                original_filename="contract.pdf",
                content_type="application/pdf",
                purpose="contract_review",
            )
            with patch("src.document_ingest.storage.os.replace", side_effect=[PermissionError(), None]) as replace:
                storage.write_task(task)

            self.assertEqual(replace.call_count, 2)
            self.assertEqual(storage.read_task(task["task_id"])["task_id"], task["task_id"])

    def test_completed_contract_can_be_bounded_for_llm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(
                filename="供应合同.pdf",
                content_type="application/pdf",
                purpose="contract_review",
            )
            service.save_upload_chunk(task["task_id"], b"%PDF- test contract", 19)
            service.finalize_upload(task["task_id"], 19)
            service.process_task(task["task_id"])

            completed = service.get_task(task["task_id"])
            materials = service.build_llm_materials([task["task_id"]])

            self.assertEqual(completed["status"], "completed")
            self.assertTrue(completed["markdown_available"])
            self.assertEqual(materials[0]["filename"], "供应合同.pdf")
            self.assertIn("付款期限", materials[0]["content"])

    def test_rejects_unsupported_file_before_storage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            with self.assertRaises(DocumentIngestError) as context:
                service.create_task(filename="contract.exe", content_type="application/octet-stream", purpose="contract_review")
            self.assertEqual(context.exception.code, "UNSUPPORTED_FILE_TYPE")

    def test_docx_is_accepted_and_preserves_source_extension(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(
                filename="审查意见.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                purpose="reference_material",
            )
            source = service.storage.source_path(task["task_id"])
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
            size = source.stat().st_size
            service.finalize_upload(task["task_id"], size)
            service.process_task(task["task_id"])

            self.assertEqual(source.name, "source.docx")
            self.assertEqual(service.get_task(task["task_id"])["status"], "completed")

    def test_png_is_accepted_and_exposes_bounded_visual_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(filename="收据.png", content_type="image/png", purpose="reference_material")
            source = service.storage.source_path(task["task_id"])
            Image.new("RGB", (4, 4), "white").save(source, format="PNG")
            size = source.stat().st_size
            service.finalize_upload(task["task_id"], size)
            service.process_task(task["task_id"])
            materials = service.build_llm_materials([task["task_id"]])

            self.assertEqual(service.get_task(task["task_id"])["status"], "completed")
            self.assertTrue(materials[0]["visual_input"]["data_url"].startswith("data:image/png;base64,"))
            self.assertNotIn("visual_input", service.get_task(task["task_id"]))

    def test_invalid_png_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(filename="broken.png", content_type="image/png", purpose="reference_material")
            service.save_upload_chunk(task["task_id"], b"not an image", 12)
            with self.assertRaises(DocumentIngestError) as context:
                service.finalize_upload(task["task_id"], 12)
            self.assertEqual(context.exception.code, "INVALID_IMAGE")

    def test_bmp_keeps_mineu_text_but_is_not_sent_to_vision_model(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(filename="扫描件.bmp", content_type="image/bmp", purpose="reference_material")
            source = service.storage.source_path(task["task_id"])
            Image.new("RGB", (4, 4), "white").save(source, format="BMP")
            size = source.stat().st_size
            service.finalize_upload(task["task_id"], size)
            service.process_task(task["task_id"])
            material = service.build_llm_materials([task["task_id"]])[0]

            self.assertNotIn("visual_input", material)
            self.assertIn("不受视觉模型接口支持", material["visual_input_omitted"])

    def test_utf8_text_uses_local_extraction_without_mineu(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            parser = build_service(Path(temp_dir)).parser
            service = DocumentIngestService(storage=DocumentTaskStorage(root=Path(temp_dir)), parser=parser)
            task = service.create_task(filename="说明.txt", content_type="text/plain", purpose="reference_material")
            content = "第一条\n付款期限为三十日。".encode("utf-8")
            service.save_upload_chunk(task["task_id"], content, len(content))
            service.finalize_upload(task["task_id"], len(content))
            with patch.object(parser, "parse", side_effect=AssertionError("文本不应调用 MineU")):
                service.process_task(task["task_id"])

            self.assertEqual(service.result_markdown(task["task_id"]), content.decode("utf-8"))
            self.assertIn("本地 UTF-8", service.get_task(task["task_id"])["parser_message"])

    def test_requires_completed_document_for_llm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(filename="draft.pdf", content_type="application/pdf", purpose="contract_review")
            with self.assertRaises(DocumentIngestError) as context:
                service.build_llm_materials([task["task_id"]])
            self.assertEqual(context.exception.code, "DOCUMENT_NOT_READY")

    def test_material_selection_deduplicates_and_marks_truncated_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            task = service.create_task(filename="long.pdf", content_type="application/pdf", purpose="contract_review")
            service.save_upload_chunk(task["task_id"], b"%PDF- test contract", 19)
            service.finalize_upload(task["task_id"], 19)
            service.process_task(task["task_id"])

            with patch("src.document_ingest.service.MAX_LLM_MATERIAL_CHARS", 8), patch(
                "src.document_ingest.service.MAX_LLM_MATERIAL_TOTAL_CHARS", 8
            ):
                materials = service.build_llm_materials([task["task_id"], task["task_id"]])

            self.assertEqual(len(materials), 1)
            self.assertTrue(materials[0]["truncated"])
            self.assertEqual(len(materials[0]["content"]), 8)

    def test_material_selection_rejects_more_than_three_explicit_documents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_service(Path(temp_dir))
            with self.assertRaises(DocumentIngestError) as context:
                service.build_llm_materials([f"{index:032x}" for index in range(4)])

            self.assertEqual(context.exception.code, "TOO_MANY_DOCUMENTS")

    def test_parser_failure_is_visible_and_can_be_retried(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DocumentIngestService(storage=DocumentTaskStorage(root=Path(temp_dir)), parser=FailingMineU())
            task = service.create_task(filename="broken.pdf", content_type="application/pdf", purpose="contract_review")
            service.save_upload_chunk(task["task_id"], b"%PDF- test", 10)
            service.finalize_upload(task["task_id"], 10)
            service.process_task(task["task_id"])

            failed = service.get_task(task["task_id"])
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(failed["error_code"], "MINEU_PARSE_FAILED")
            self.assertEqual(service.retry_task(task["task_id"])["status"], "uploaded")


class DocumentIngestApiTest(unittest.TestCase):
    def test_invalid_pdf_upload_is_rejected_and_partial_task_is_cleaned_up(self):
        import src.document_ingest.router as document_router

        with tempfile.TemporaryDirectory() as temp_dir:
            original_service = document_router.service
            document_router.service = build_service(Path(temp_dir))
            try:
                with TestClient(app) as client:
                    response = client.post(
                        "/documents/upload",
                        files={"file": ("not-a-pdf.pdf", b"plain text", "application/pdf")},
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()["error"]["code"], "INVALID_PDF")
                    self.assertEqual(client.get("/documents").json()["items"], [])
            finally:
                document_router.service = original_service

    def test_upload_result_and_delete_contract(self):
        import src.document_ingest.router as document_router

        with tempfile.TemporaryDirectory() as temp_dir:
            original_service = document_router.service
            document_router.service = build_service(Path(temp_dir))
            try:
                with TestClient(app) as client:
                    response = client.post(
                        "/documents/upload",
                        data={"purpose": "contract_review"},
                        files={"file": ("supply.pdf", b"%PDF- sample", "application/pdf")},
                    )
                    self.assertEqual(response.status_code, 202)
                    task_id = response.json()["data"]["task_id"]
                    task = client.get(f"/documents/{task_id}").json()["data"]
                    self.assertEqual(task["status"], "completed")
                    self.assertIn("付款期限", client.get(f"/documents/{task_id}/result").json()["markdown"])
                    source = client.get(f"/documents/{task_id}/source")
                    self.assertEqual(source.status_code, 200)
                    self.assertEqual(source.content, b"%PDF- sample")
                    self.assertIn("supply.pdf", source.headers.get("content-disposition", ""))
                    with patch.dict("os.environ", {"RISK_LOCAL_FILE_OPEN_ENABLED": "true"}), patch("src.document_ingest.router.os.startfile", create=True) as open_with_default_app:
                        opened = client.post(f"/documents/{task_id}/open")
                    self.assertEqual(opened.status_code, 200)
                    self.assertEqual(opened.json()["status"], "opened")
                    open_with_default_app.assert_called_once()
                    retry_response = client.post(f"/documents/{task_id}/retry")
                    self.assertEqual(retry_response.status_code, 202)
                    self.assertEqual(retry_response.json()["data"]["status"], "uploaded")
                    self.assertEqual(client.delete(f"/documents/{task_id}").status_code, 200)
            finally:
                document_router.service = original_service

    def test_open_source_is_disabled_without_local_development_flag(self):
        import src.document_ingest.router as document_router

        with tempfile.TemporaryDirectory() as temp_dir:
            original_service = document_router.service
            document_router.service = build_service(Path(temp_dir))
            try:
                with patch.dict("os.environ", {}, clear=False):
                    os.environ.pop("RISK_LOCAL_FILE_OPEN_ENABLED", None)
                    with TestClient(app) as client:
                        response = client.post(
                            "/documents/upload",
                            files={"file": ("source.pdf", b"%PDF- sample", "application/pdf")},
                        )
                        task_id = response.json()["data"]["task_id"]
                        opened = client.post(f"/documents/{task_id}/open")
                self.assertEqual(opened.status_code, 403)
                self.assertEqual(opened.json()["error"]["code"], "DOCUMENT_OPEN_DISABLED")
            finally:
                document_router.service = original_service

    def test_referenced_remediation_evidence_cannot_be_deleted(self):
        import src.document_ingest.router as document_router

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixture_path = root / "internal_risk_workflow.json"
            fixture_path.write_text(
                Path("tests/fixtures/regression/internal_risk_workflow.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            original_document_service = document_router.service
            document_router.service = build_service(root / "documents")
            try:
                with patch.object(
                    document_router,
                    "InternalRiskWorkflowService",
                    return_value=InternalRiskWorkflowService(fixture_path),
                ):
                    with TestClient(app) as client:
                        response = client.post(
                            "/documents/upload",
                            data={"purpose": "remediation_evidence"},
                            files={"file": ("evidence.pdf", b"%PDF- sample", "application/pdf")},
                        )
                        task_id = response.json()["data"]["task_id"]
                        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
                        payload["workflow"]["remediation_tasks"][0]["evidence_refs"].append(task_id)
                        fixture_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

                        delete_response = client.delete(f"/documents/{task_id}")

                self.assertEqual(delete_response.status_code, 409)
                self.assertEqual(delete_response.json()["error"]["code"], "DOCUMENT_REFERENCED_BY_INTERNAL_RISK")
            finally:
                document_router.service = original_document_service

    def test_ask_passes_selected_contract_materials_to_rag(self):
        material = [{"task_id": "a" * 32, "filename": "supply.pdf", "content": "付款条款", "truncated": False}]
        rag_payload = {
            "answer": "合同需要复核。 [《中华人民共和国民法典》第一条]",
            "confidence_score": 0.7,
            "answer_confidence": 0.7,
            "retrieval_confidence": 0.7,
            "needs_human_review": True,
            "missing_evidence": [],
            "risk_level": "medium",
            "risk_types": [],
            "risk_type_evidence": [],
            "recommended_actions": [],
            "recommended_action_evidence": [],
            "citation_integrity": {},
            "evidence_chain": [{"citation": "[《中华人民共和国民法典》第一条]"}],
            "filters": {},
            "material_sources": [{"filename": "supply.pdf"}],
        }
        with patch("src.main.DocumentIngestService") as service_cls, patch("src.main.rag_query", return_value=rag_payload) as rag_query:
            service_cls.return_value.build_llm_materials.return_value = material
            _run_ask_request(AskRequest(question="审查合同", document_task_ids=["a" * 32]))
            self.assertEqual(rag_query.call_args.kwargs["user_materials"], material)


if __name__ == "__main__":
    unittest.main()
