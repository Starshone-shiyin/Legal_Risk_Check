from __future__ import annotations

import base64
import os
import zipfile
from pathlib import Path

from src.document_ingest.formats import (
    ACCEPTED_CONTENT_TYPES,
    IMAGE_EXTENSIONS,
    OFFICE_EXTENSIONS,
    PDF_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    canonical_content_type,
    extension_for,
    is_image_filename,
    is_text_filename,
    is_vision_supported_image_filename,
)
from src.document_ingest.mineu_adapter import MineUAdapter, MineUError, MineUParseResult
from src.document_ingest.storage import DocumentStorageError, DocumentTaskStorage


MAX_UPLOAD_SIZE_BYTES = int(os.getenv("DOCUMENT_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024)))
MAX_LIGHTWEIGHT_PAGES = 20
PDF_SIGNATURE = b"%PDF-"
MAX_LLM_MATERIALS = 3
MAX_LLM_MATERIAL_CHARS = 12_000
MAX_LLM_MATERIAL_TOTAL_CHARS = 24_000
MAX_VISION_IMAGE_BYTES = 5 * 1024 * 1024


class DocumentIngestError(Exception):
    def __init__(self, code: str, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


class DocumentIngestService:
    def __init__(self, storage: DocumentTaskStorage | None = None, parser: MineUAdapter | None = None) -> None:
        self.storage = storage or DocumentTaskStorage()
        self.parser = parser or MineUAdapter()

    @property
    def max_upload_size_bytes(self) -> int:
        return MAX_UPLOAD_SIZE_BYTES

    def create_task(self, *, filename: str | None, content_type: str | None, purpose: str | None) -> dict:
        suffix = extension_for(filename)
        if not filename or suffix not in SUPPORTED_EXTENSIONS:
            raise DocumentIngestError(
                "UNSUPPORTED_FILE_TYPE",
                "支持 PDF、Word、PPT、Excel、图片、TXT、Markdown 和 CSV 文件。",
            )
        if content_type and content_type not in ACCEPTED_CONTENT_TYPES:
            raise DocumentIngestError("UNSUPPORTED_CONTENT_TYPE", "文件 MIME 类型不在允许范围内。")
        return self.storage.create_task(
            original_filename=filename,
            content_type=canonical_content_type(filename),
            purpose=(purpose or "reference_material").strip()[:80],
        )

    def save_upload_chunk(self, task_id: str, chunk: bytes, total_size: int) -> None:
        if total_size > self.max_upload_size_bytes:
            limit_mb = max(1, self.max_upload_size_bytes // (1024 * 1024))
            raise DocumentIngestError("FILE_TOO_LARGE", f"文件超过 {limit_mb} MB 上传上限。", http_status=413)
        with self.storage.source_path(task_id).open("ab") as handle:
            handle.write(chunk)

    def finalize_upload(self, task_id: str, total_size: int) -> dict:
        if total_size <= 0:
            raise DocumentIngestError("EMPTY_FILE", "不能上传空文件。")
        source_path = self.storage.source_path(task_id)
        task = self.storage.read_task(task_id)
        suffix = extension_for(task.get("original_filename"))
        self._validate_source_file(source_path, suffix)
        if getattr(self.parser, "mode", "local") == "lightweight" and suffix in PDF_EXTENSIONS:
            self._validate_lightweight_page_limit(source_path)
        task["size_bytes"] = total_size
        task["parser_message"] = "已接收，等待解析"
        self.storage.write_task(task)
        return self.public_task(task)

    def process_task(self, task_id: str) -> None:
        try:
            task = self.storage.read_task(task_id)
        except DocumentStorageError:
            return
        task.update({
            "status": "processing",
            "parser_message": "MineU 正在解析文件",
            "error_code": None,
            "error_message": None,
        })
        self.storage.write_task(task)
        try:
            task_dir = self.storage.task_dir(task_id)
            parsed_dir = task_dir / "mineu_output"
            source_path = self.storage.source_path(task_id)
            if is_text_filename(task.get("original_filename")):
                result = MineUParseResult(
                    markdown=source_path.read_text(encoding="utf-8"),
                    command="local UTF-8 text extraction",
                )
            else:
                result = self.parser.parse(source_path, parsed_dir)
            normalized_path = task_dir / "result" / "parsed.md"
            normalized_path.parent.mkdir(parents=True, exist_ok=True)
            normalized_path.write_text(result.markdown, encoding="utf-8")
            used_local_fallback = "local PDF text fallback" in result.command
            task.update({
                "status": "completed",
                "parser_message": (
                    "MineU 结果暂不可用，已使用本地 PDF 文本提取；请人工核对表格和版面。"
                    if used_local_fallback
                    else (
                        "本地 UTF-8 文本提取完成，等待人工确认后再用于分析。"
                        if is_text_filename(task.get("original_filename"))
                        else "MineU 解析完成，等待人工确认后再用于分析。"
                    )
                ),
                "markdown_available": True,
                "markdown_path": "result/parsed.md",
                "parser_command": result.command,
            })
        except MineUError as exc:
            task.update({
                "status": "failed",
                "parser_message": "MineU 解析未完成",
                "error_code": exc.code,
                "error_message": exc.message,
            })
        except Exception:
            task.update({
                "status": "failed",
                "parser_message": "解析服务发生未预期错误",
                "error_code": "DOCUMENT_PROCESSING_ERROR",
                "error_message": "解析未完成，请查看服务日志后重试。",
            })
        finally:
            try:
                self.storage.write_task(task)
            except DocumentStorageError:
                # The user may remove an attachment while its background parse is still unwinding.
                return

    def get_task(self, task_id: str) -> dict:
        try:
            return self.public_task(self.storage.read_task(task_id))
        except DocumentStorageError as exc:
            raise DocumentIngestError("DOCUMENT_NOT_FOUND", str(exc), http_status=404) from exc

    def list_tasks(self) -> list[dict]:
        return [self.public_task(task) for task in self.storage.list_tasks()]

    def result_markdown(self, task_id: str) -> str:
        task = self._read_completed_task(task_id)
        try:
            return self.storage.markdown_path(task).read_text(encoding="utf-8")
        except (DocumentStorageError, OSError) as exc:
            raise DocumentIngestError("DOCUMENT_RESULT_UNAVAILABLE", "解析结果暂不可用。", http_status=409) from exc

    def result_path(self, task_id: str) -> Path:
        return self.storage.markdown_path(self._read_completed_task(task_id))

    def source_file_path(self, task_id: str) -> Path:
        try:
            task = self.storage.read_task(task_id)
            path = self.storage.source_path(task_id)
        except DocumentStorageError as exc:
            raise DocumentIngestError("DOCUMENT_NOT_FOUND", str(exc), http_status=404) from exc
        if not path.is_file():
            raise DocumentIngestError("DOCUMENT_SOURCE_UNAVAILABLE", "原始文件暂不可用。", http_status=409)
        # Reading task metadata first ensures the task id is validated by storage.
        if not task.get("original_filename"):
            raise DocumentIngestError("DOCUMENT_SOURCE_UNAVAILABLE", "原始文件元数据不完整。", http_status=409)
        return path

    def delete_task(self, task_id: str) -> None:
        try:
            self.storage.delete_task(task_id)
        except DocumentStorageError as exc:
            raise DocumentIngestError("DOCUMENT_NOT_FOUND", str(exc), http_status=404) from exc

    def retry_task(self, task_id: str) -> dict:
        try:
            task = self.storage.read_task(task_id)
        except DocumentStorageError as exc:
            raise DocumentIngestError("DOCUMENT_NOT_FOUND", str(exc), http_status=404) from exc
        if task.get("status") not in {"failed", "completed"}:
            raise DocumentIngestError("DOCUMENT_BUSY", "该文件正在解析，请稍后查看状态。", http_status=409)
        task.update({
            "status": "uploaded",
            "parser_message": "等待重新解析",
            "error_code": None,
            "error_message": None,
            "markdown_available": False,
            "markdown_path": None,
        })
        self.storage.write_task(task)
        return self.public_task(task)

    def parser_status(self) -> dict:
        return {**self.parser.status(), "max_file_size_bytes": self.max_upload_size_bytes}

    def build_llm_materials(self, task_ids: list[str] | None) -> list[dict]:
        """Load a bounded, explicit set of reviewed parser outputs for one LLM call."""
        selected_ids = list(dict.fromkeys(task_ids or []))
        if len(selected_ids) > MAX_LLM_MATERIALS:
            raise DocumentIngestError(
                "TOO_MANY_DOCUMENTS",
                f"一次分析最多选择 {MAX_LLM_MATERIALS} 份材料。",
            )

        materials: list[dict] = []
        remaining = MAX_LLM_MATERIAL_TOTAL_CHARS
        for task_id in selected_ids:
            task = self._read_completed_task(task_id)
            markdown = self.result_markdown(task_id).strip()
            excerpt = markdown[: min(MAX_LLM_MATERIAL_CHARS, remaining)]
            if not excerpt:
                continue
            materials.append({
                "task_id": task_id,
                "filename": task["original_filename"],
                "content": excerpt,
                "truncated": len(markdown) > len(excerpt),
                **self._visual_material_input(task, task_id),
            })
            remaining -= len(excerpt)
            if remaining <= 0:
                break
        return materials

    @staticmethod
    def public_task(task: dict) -> dict:
        return {key: value for key, value in task.items() if key not in {"source_path", "markdown_path", "parser_command"}}

    def _read_completed_task(self, task_id: str) -> dict:
        try:
            task = self.storage.read_task(task_id)
        except DocumentStorageError as exc:
            raise DocumentIngestError("DOCUMENT_NOT_FOUND", str(exc), http_status=404) from exc
        if task.get("status") != "completed" or not task.get("markdown_available"):
            raise DocumentIngestError("DOCUMENT_NOT_READY", "文件尚未解析完成。", http_status=409)
        return task

    def _visual_material_input(self, task: dict, task_id: str) -> dict:
        """Expose a bounded data URL only to the in-memory visual analysis path."""
        filename = str(task.get("original_filename") or "")
        if not is_image_filename(filename):
            return {}
        if not is_vision_supported_image_filename(filename):
            return {"visual_input_omitted": "该图片格式可由 MineU 解析，但不受视觉模型接口支持，已仅保留解析文本。"}
        source_path = self.storage.source_path(task_id)
        try:
            size = source_path.stat().st_size
            if size > MAX_VISION_IMAGE_BYTES:
                return {"visual_input_omitted": "图片超过视觉模型输入上限，已仅保留 MineU 解析文本。"}
            payload = base64.b64encode(source_path.read_bytes()).decode("ascii")
        except OSError:
            return {"visual_input_omitted": "图片原件暂不可用，已仅保留 MineU 解析文本。"}
        return {
            "visual_input": {
                "data_url": f"data:{task['content_type']};base64,{payload}",
                "media_type": task["content_type"],
            }
        }

    @staticmethod
    def _validate_source_file(source_path: Path, suffix: str) -> None:
        with source_path.open("rb") as handle:
            signature = handle.read(16)
        if suffix in PDF_EXTENSIONS and not signature.startswith(PDF_SIGNATURE):
            raise DocumentIngestError("INVALID_PDF", "文件不是有效的 PDF。")
        if suffix in IMAGE_EXTENSIONS:
            try:
                from PIL import Image

                with Image.open(source_path) as image:
                    image.verify()
            except Exception as exc:
                raise DocumentIngestError("INVALID_IMAGE", "图片无法读取或已损坏。") from exc
        if suffix in {".docx", ".pptx", ".xlsx"} and not zipfile.is_zipfile(source_path):
            raise DocumentIngestError("INVALID_OFFICE_FILE", "Office 文件格式无效，请重新导出后上传。")
        if suffix in {".doc", ".ppt", ".xls"} and not signature.startswith(b"\xd0\xcf\x11\xe0"):
            raise DocumentIngestError("INVALID_OFFICE_FILE", "旧版 Office 文件格式无效，请重新导出后上传。")
        if is_text_filename(source_path.name):
            try:
                source_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                raise DocumentIngestError("INVALID_TEXT_FILE", "文本文件需要 UTF-8 编码。") from exc

    @staticmethod
    def _validate_lightweight_page_limit(source_path: Path) -> None:
        try:
            import pypdfium2 as pdfium

            page_count = len(pdfium.PdfDocument(str(source_path)))
        except Exception as exc:
            raise DocumentIngestError("PDF_PAGE_COUNT_UNAVAILABLE", "无法读取 PDF 页数，请更换有效合同文件。") from exc
        if page_count > MAX_LIGHTWEIGHT_PAGES:
            raise DocumentIngestError(
                "TOO_MANY_PAGES",
                f"MineU 轻量 API 最多支持 {MAX_LIGHTWEIGHT_PAGES} 页，请拆分合同后上传。",
            )
