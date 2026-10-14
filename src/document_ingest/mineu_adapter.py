from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import httpx


class MineUError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class MineUParseResult:
    markdown: str
    command: str


class MineUAdapter:
    """MineU lightweight API adapter with an optional local CLI fallback."""

    def __init__(
        self,
        command: str | None = None,
        timeout_seconds: int | None = None,
        mode: str | None = None,
        api_base_url: str | None = None,
    ) -> None:
        self.mode = (mode or os.getenv("MINEU_MODE", "lightweight")).strip().lower()
        self._configured_command = (command if command is not None else os.getenv("MINEU_COMMAND", "")).strip()
        self.api_base_url = (api_base_url or os.getenv("MINEU_API_BASE_URL", "https://mineru.net")).rstrip("/")
        self.timeout_seconds = timeout_seconds or int(os.getenv("MINEU_TIMEOUT_SECONDS", "300"))
        self.poll_seconds = max(1.0, float(os.getenv("MINEU_API_POLL_SECONDS", "2")))
        self.result_download_attempts = max(1, int(os.getenv("MINEU_RESULT_DOWNLOAD_ATTEMPTS", "5")))
        self.result_download_retry_seconds = max(
            0.2,
            float(os.getenv("MINEU_RESULT_DOWNLOAD_RETRY_SECONDS", "2")),
        )

    def status(self) -> dict:
        if self.mode == "lightweight":
            return {
                "available": True,
                "command": self.api_base_url,
                "message": "MineU 轻量云端 API 已就绪，无需 Token。合同将发送至云端解析（最大 10 MB、20 页）。",
            }
        if self.mode != "local":
            return {
                "available": False,
                "command": None,
                "message": "MINEU_MODE 仅支持 lightweight 或 local。",
            }
        command = self._resolve_local_command()
        if command is None:
            return {
                "available": False,
                "command": None,
                "message": "未检测到本地 MineU。安装 mineru 后重启服务，或设置 MINEU_COMMAND。",
            }
        return {
            "available": True,
            "command": " ".join(command),
            "message": "本机 MineU CLI 可用。上传的合同将在本机解析。",
        }

    def parse(self, source_path: Path, output_dir: Path) -> MineUParseResult:
        if self.mode == "lightweight":
            return self._parse_lightweight(source_path)
        if self.mode == "local":
            return self._parse_local(source_path, output_dir)
        raise MineUError("MINEU_MODE_INVALID", self.status()["message"])

    def _parse_lightweight(self, source_path: Path) -> MineUParseResult:
        try:
            markdown = self._parse_lightweight_cloud(source_path)
        except MineUError as exc:
            if exc.code != "MINEU_RESULT_DOWNLOAD_FAILED":
                raise
            markdown = self._extract_local_pdf_text(source_path)
            if not markdown:
                raise
            return MineUParseResult(
                markdown=markdown,
                command=f"MineU Lightweight API {self.api_base_url}; local PDF text fallback",
            )

        if not markdown:
            raise MineUError("MINEU_EMPTY_OUTPUT", "MineU 未提取到可用文本，请检查扫描件质量或 OCR 配置。")
        return MineUParseResult(markdown=markdown, command=f"MineU Lightweight API {self.api_base_url}")

    def _parse_lightweight_cloud(self, source_path: Path) -> str:
        filename = source_path.name
        deadline = time.monotonic() + max(30, self.timeout_seconds)
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0), follow_redirects=True) as client:
                upload_payload = self._api_request(
                    client,
                    "POST",
                    "/api/v1/agent/parse/file",
                    json={
                        "file_name": filename,
                        "language": "ch",
                        "enable_table": True,
                        "is_ocr": False,
                        "enable_formula": True,
                    },
                )
                upload_data = self._response_data(upload_payload)
                task_id = str(upload_data.get("task_id") or "").strip()
                upload_url = self._first_url(upload_data.get("file_url") or upload_data.get("upload_url"))
                if not task_id or not upload_url:
                    raise MineUError("MINEU_API_PROTOCOL_ERROR", "MineU 轻量 API 未返回可用的上传任务。")

                with source_path.open("rb") as source_file:
                    # MineU issues an OSS pre-signed URL whose signature has an empty Content-Type.
                    upload_response = client.put(upload_url, content=source_file)
                if upload_response.is_error:
                    raise MineUError("MINEU_UPLOAD_FAILED", "文件上传至 MineU 轻量云端失败，请稍后重试。")

                markdown_url = self._wait_for_markdown_url(client, task_id, deadline)
                markdown = self._download_markdown(client, markdown_url)
        except httpx.HTTPError as exc:
            raise MineUError("MINEU_API_REQUEST_FAILED", "MineU 轻量云端 API 请求失败，请检查网络后重试。") from exc
        return markdown

    @staticmethod
    def _extract_local_pdf_text(source_path: Path) -> str:
        """Return selectable PDF text when MineU's result CDN is unavailable.

        This is deliberately a narrow fallback: it preserves reviewability for
        text-based PDFs but does not pretend to reproduce MineU's OCR or table
        reconstruction for scanned documents.
        """
        try:
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(str(source_path))
            pages = []
            for page in pdf:
                text = page.get_textpage().get_text_range().strip()
                if text:
                    pages.append(text)
            return "\n\n".join(pages).strip()
        except Exception:
            return ""

    def _download_markdown(self, client: httpx.Client, markdown_url: str) -> str:
        """Fetch MineU Markdown after a short CDN-readiness grace period.

        MineU can expose the task's Markdown URL shortly before the result CDN
        serves the object. The former single fallback turned that temporary
        404/5xx window into a permanent task failure. Each attempt first uses
        the configured client, then retries without proxy environment settings
        for installations whose proxy cannot reach the result CDN.
        """
        for attempt in range(self.result_download_attempts):
            markdown = self._fetch_markdown(client, markdown_url)
            if markdown:
                return markdown

            # Some local proxies terminate TLS connections to MineU's result CDN.
            # Keep the task API on its configured network path, but fetch the
            # public result URL directly as a fallback on every bounded retry.
            try:
                with httpx.Client(
                    timeout=httpx.Timeout(60.0),
                    follow_redirects=True,
                    trust_env=False,
                ) as direct_client:
                    markdown = self._fetch_markdown(direct_client, markdown_url)
                    if markdown:
                        return markdown
            except httpx.HTTPError:
                pass

            if attempt < self.result_download_attempts - 1:
                time.sleep(self.result_download_retry_seconds)

        raise MineUError(
            "MINEU_RESULT_DOWNLOAD_FAILED",
            "无法下载 MineU 的解析结果，请检查网络或稍后重试。",
        )

    @staticmethod
    def _fetch_markdown(client: httpx.Client, markdown_url: str) -> str:
        try:
            response = client.get(markdown_url)
            if not response.is_error:
                return response.text.strip()
        except httpx.HTTPError:
            pass
        return ""

    def _wait_for_markdown_url(self, client: httpx.Client, task_id: str, deadline: float) -> str:
        result_path = f"/api/v1/agent/parse/{task_id}"
        completed_states = {"done", "success", "succeeded", "completed", "finished"}
        while time.monotonic() < deadline:
            payload = self._api_request(client, "GET", result_path)
            item = self._result_item(self._response_data(payload))
            state = str(item.get("state") or item.get("status") or "").lower()
            markdown_url = self._first_url(
                item.get("full_md_url") or item.get("md_url") or item.get("markdown_url")
            )
            if state in {"failed", "error", "cancelled", "canceled"}:
                detail = str(item.get("err_msg") or item.get("error") or "")[:300]
                suffix = f"：{detail}" if detail else ""
                raise MineUError("MINEU_PARSE_FAILED", f"MineU 未能完成文件解析{suffix}")
            # MineU may publish a result URL before its CDN object is ready.
            # Wait for an explicit completion state when one is supplied, while
            # retaining compatibility with API responses that expose only a URL.
            if markdown_url and (not state or state in completed_states):
                return markdown_url
            time.sleep(self.poll_seconds)
        raise MineUError("MINEU_TIMEOUT", "MineU 轻量云端解析超时，请稍后重试。")

    def _api_request(self, client: httpx.Client, method: str, path: str, **kwargs) -> dict:
        response = client.request(method, f"{self.api_base_url}{path}", **kwargs)
        if response.is_error:
            raise MineUError("MINEU_API_REQUEST_FAILED", "MineU 轻量云端 API 请求失败，请检查网络或稍后重试。")
        try:
            payload = response.json()
        except ValueError as exc:
            raise MineUError("MINEU_API_PROTOCOL_ERROR", "MineU 轻量云端返回了无法识别的响应。") from exc
        if not isinstance(payload, dict) or payload.get("code") not in {None, 0, "0"}:
            detail = str((payload or {}).get("msg") or "")[:300] if isinstance(payload, dict) else ""
            suffix = f"：{detail}" if detail else ""
            raise MineUError("MINEU_API_REQUEST_FAILED", f"MineU 轻量云端拒绝了请求{suffix}")
        return payload

    @staticmethod
    def _response_data(payload: dict) -> dict:
        data = payload.get("data") if isinstance(payload, dict) else None
        return data if isinstance(data, dict) else {"items": data} if isinstance(data, list) else {}

    @staticmethod
    def _first_url(value: object) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, str):
                return first.strip()
            if isinstance(first, dict):
                return str(first.get("url") or first.get("file_url") or "").strip()
        return ""

    @staticmethod
    def _result_item(data: dict) -> dict:
        for key in ("extract_result", "results", "files", "items"):
            value = data.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value[0]
        return data

    def _parse_local(self, source_path: Path, output_dir: Path) -> MineUParseResult:
        command = self._resolve_local_command()
        if command is None:
            raise MineUError("MINEU_UNAVAILABLE", self.status()["message"])

        output_dir.mkdir(parents=True, exist_ok=True)
        invocation = [*command, "-p", str(source_path), "-o", str(output_dir)]
        try:
            completed = subprocess.run(
                invocation,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(30, self.timeout_seconds),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise MineUError("MINEU_TIMEOUT", "MineU 解析超时，请缩小文件或检查本机解析服务。") from exc
        except OSError as exc:
            raise MineUError("MINEU_START_FAILED", "MineU 无法启动，请检查 MINEU_COMMAND 配置。") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip().replace("\n", " ")[:400]
            suffix = f"：{detail}" if detail else ""
            raise MineUError("MINEU_PARSE_FAILED", f"MineU 未能完成解析{suffix}")

        markdown_files = sorted(output_dir.rglob("*.md"), key=lambda item: item.stat().st_size, reverse=True)
        if not markdown_files:
            raise MineUError("MINEU_OUTPUT_MISSING", "MineU 未生成 Markdown 结果，请检查该 PDF 是否可解析。")
        markdown = markdown_files[0].read_text(encoding="utf-8", errors="replace").strip()
        if not markdown:
            raise MineUError("MINEU_EMPTY_OUTPUT", "MineU 未提取到可用文本，请检查扫描件质量或 OCR 配置。")
        return MineUParseResult(markdown=markdown, command=" ".join(invocation))

    def _resolve_local_command(self) -> list[str] | None:
        if self._configured_command:
            parts = shlex.split(self._configured_command, posix=os.name != "nt")
            return parts if parts and self._command_exists(parts[0]) else None
        for candidate in ("mineru", "magic-pdf"):
            if shutil.which(candidate):
                return [candidate]
        return None

    @staticmethod
    def _command_exists(command: str) -> bool:
        return bool(shutil.which(command) or Path(command).exists())
