from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from src.document_ingest.schemas import (
    DocumentParserStatusResponse,
    DocumentResultResponse,
    DocumentTaskListResponse,
    DocumentTaskResponse,
)
from src.document_ingest.service import DocumentIngestError, DocumentIngestService
from src.internal_risk.service import InternalRiskWorkflowService


router = APIRouter(prefix="/documents", tags=["documents"])
service = DocumentIngestService()
CHUNK_SIZE_BYTES = 1024 * 1024


def _error_response(exc: DocumentIngestError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@router.get("/capabilities", response_model=DocumentParserStatusResponse)
async def document_capabilities():
    return DocumentParserStatusResponse(**service.parser_status())


@router.get("", response_model=DocumentTaskListResponse)
async def list_documents():
    return DocumentTaskListResponse(items=service.list_tasks())


@router.post("/upload", response_model=DocumentTaskResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    purpose: str = Form(default="reference_material"),
):
    task_id: str | None = None
    try:
        task = service.create_task(filename=file.filename, content_type=file.content_type, purpose=purpose)
        task_id = task["task_id"]
        total_size = 0
        while chunk := await file.read(CHUNK_SIZE_BYTES):
            total_size += len(chunk)
            service.save_upload_chunk(task_id, chunk, total_size)
        saved = service.finalize_upload(task_id, total_size)
        background_tasks.add_task(service.process_task, task_id)
        return DocumentTaskResponse(status="accepted", data=saved)
    except DocumentIngestError as exc:
        if task_id:
            try:
                service.delete_task(task_id)
            except DocumentIngestError:
                pass
        return _error_response(exc)
    finally:
        await file.close()


@router.get("/{task_id}", response_model=DocumentTaskResponse)
async def get_document(task_id: str):
    try:
        return DocumentTaskResponse(status="ok", data=service.get_task(task_id))
    except DocumentIngestError as exc:
        return _error_response(exc)


@router.post("/{task_id}/retry", response_model=DocumentTaskResponse, status_code=202)
async def retry_document(task_id: str, background_tasks: BackgroundTasks):
    try:
        task = service.retry_task(task_id)
        background_tasks.add_task(service.process_task, task_id)
        return DocumentTaskResponse(status="accepted", data=task)
    except DocumentIngestError as exc:
        return _error_response(exc)


@router.get("/{task_id}/result", response_model=DocumentResultResponse)
async def get_document_result(task_id: str):
    try:
        return DocumentResultResponse(task_id=task_id, markdown=service.result_markdown(task_id))
    except DocumentIngestError as exc:
        return _error_response(exc)


@router.get("/{task_id}/content")
async def download_document_result(task_id: str):
    try:
        return FileResponse(
            service.result_path(task_id),
            media_type="text/markdown; charset=utf-8",
            filename=f"{task_id}.md",
        )
    except DocumentIngestError as exc:
        return _error_response(exc)


@router.get("/{task_id}/source")
async def download_document_source(task_id: str):
    try:
        task = service.get_task(task_id)
        return FileResponse(
            service.source_file_path(task_id),
            media_type=task["content_type"],
            filename=task["original_filename"],
        )
    except DocumentIngestError as exc:
        return _error_response(exc)


@router.post("/{task_id}/open")
async def open_document_source_with_default_app(task_id: str):
    """Open the original local file through the operating system's default app."""
    try:
        if os.getenv("RISK_LOCAL_FILE_OPEN_ENABLED", "false").lower() != "true":
            raise DocumentIngestError(
                "DOCUMENT_OPEN_DISABLED",
                "远程或生产部署已关闭本机默认应用打开功能，请下载原始文件后在本机打开。",
                http_status=403,
            )
        source_path = service.source_file_path(task_id)
        startfile = getattr(os, "startfile", None)
        if startfile is None:
            raise DocumentIngestError(
                "DOCUMENT_OPEN_UNSUPPORTED",
                "当前运行环境不支持使用默认应用打开本地文件。",
                http_status=501,
            )
        startfile(str(source_path))
        return {"status": "opened", "task_id": task_id}
    except DocumentIngestError as exc:
        return _error_response(exc)
    except OSError as exc:
        return _error_response(DocumentIngestError(
            "DOCUMENT_OPEN_FAILED",
            "无法调用默认应用打开原始文件。",
            http_status=500,
        ))


@router.delete("/{task_id}")
async def delete_document(task_id: str):
    try:
        if InternalRiskWorkflowService().references_document(task_id):
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "DOCUMENT_REFERENCED_BY_INTERNAL_RISK",
                        "message": "该文件已作为整改证据关联，不能直接删除。",
                    }
                },
            )
        service.delete_task(task_id)
        return {"status": "deleted", "task_id": task_id}
    except DocumentIngestError as exc:
        return _error_response(exc)
