from __future__ import annotations

import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


TASK_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


class DocumentStorageError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_filename(filename: str | None) -> str:
    candidate = Path(filename or "upload.pdf").name.strip()
    candidate = re.sub(r"[^A-Za-z0-9._()\-\u4e00-\u9fff]", "_", candidate)
    return candidate[:160] or "upload.pdf"


class DocumentTaskStorage:
    def __init__(self, root: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.root = (root or project_root / "data" / "document_ingest").resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_task(self, *, original_filename: str, purpose: str, content_type: str) -> dict:
        task_id = uuid4().hex
        directory = self._task_dir(task_id)
        directory.mkdir(parents=True, exist_ok=False)
        now = utc_now()
        task = {
            "task_id": task_id,
            "original_filename": safe_filename(original_filename),
            "purpose": purpose or "reference_material",
            "content_type": content_type or "application/octet-stream",
            "size_bytes": 0,
            "status": "uploaded",
            "created_at": now,
            "updated_at": now,
            "parser": "MineU",
            "parser_message": "等待 MineU 解析",
            "error_code": None,
            "error_message": None,
            "markdown_available": False,
            "ingestion_state": "not_ingested",
            "source_path": f"source{Path(original_filename).suffix.lower() or '.bin'}",
            "markdown_path": None,
        }
        self.write_task(task)
        return task

    def task_dir(self, task_id: str) -> Path:
        return self._task_dir(task_id)

    def source_path(self, task_id: str) -> Path:
        task = self.read_task(task_id)
        relative_path = str(task.get("source_path") or "")
        target = (self._task_dir(task_id) / relative_path).resolve()
        if self._task_dir(task_id) not in target.parents:
            raise DocumentStorageError("原始文件路径无效")
        return target

    def markdown_path(self, task: dict) -> Path:
        relative_path = task.get("markdown_path")
        if not relative_path:
            raise DocumentStorageError("解析结果尚不可用")
        target = (self._task_dir(task["task_id"]) / relative_path).resolve()
        if self._task_dir(task["task_id"]) not in target.parents:
            raise DocumentStorageError("解析结果路径无效")
        return target

    def write_task(self, task: dict) -> None:
        task = dict(task)
        task["updated_at"] = utc_now()
        target = self._task_dir(task["task_id"]) / "task.json"
        temporary = target.with_name(f"{target.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
            for attempt in range(3):
                try:
                    os.replace(temporary, target)
                    return
                except PermissionError as exc:
                    if attempt == 2:
                        raise DocumentStorageError("文件任务状态暂时无法写入，请稍后重试") from exc
                    time.sleep(0.05 * (attempt + 1))
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def read_task(self, task_id: str) -> dict:
        target = self._task_dir(task_id) / "task.json"
        if not target.exists():
            raise DocumentStorageError("未找到该文件任务")
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DocumentStorageError("文件任务元数据不可读取") from exc

    def list_tasks(self) -> list[dict]:
        tasks: list[dict] = []
        for item in self.root.iterdir():
            if not item.is_dir() or not TASK_ID_PATTERN.fullmatch(item.name):
                continue
            try:
                tasks.append(self.read_task(item.name))
            except DocumentStorageError:
                continue
        return sorted(tasks, key=lambda task: task.get("created_at", ""), reverse=True)

    def delete_task(self, task_id: str) -> None:
        directory = self._task_dir(task_id)
        if not directory.exists():
            raise DocumentStorageError("未找到该文件任务")
        shutil.rmtree(directory)

    def _task_dir(self, task_id: str) -> Path:
        if not TASK_ID_PATTERN.fullmatch(task_id):
            raise DocumentStorageError("文件任务标识无效")
        return self.root / task_id
