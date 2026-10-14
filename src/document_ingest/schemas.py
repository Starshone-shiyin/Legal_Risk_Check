from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from src.document_ingest.formats import MIME_TYPES_BY_EXTENSION


DocumentTaskStatus = Literal["uploaded", "processing", "completed", "failed"]


class DocumentTask(BaseModel):
    task_id: str
    original_filename: str
    purpose: str = "reference_material"
    content_type: str = "application/octet-stream"
    size_bytes: int = Field(ge=0)
    status: DocumentTaskStatus
    created_at: str
    updated_at: str
    parser: str = "MineU"
    parser_message: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    markdown_available: bool = False
    ingestion_state: Literal["not_ingested"] = "not_ingested"


class DocumentTaskResponse(BaseModel):
    status: Literal["accepted", "ok"] = "ok"
    data: DocumentTask


class DocumentTaskListResponse(BaseModel):
    status: Literal["ok"] = "ok"
    items: list[DocumentTask] = Field(default_factory=list)


class DocumentResultResponse(BaseModel):
    status: Literal["ok"] = "ok"
    task_id: str
    markdown: str


class DocumentParserStatusResponse(BaseModel):
    status: Literal["ok"] = "ok"
    parser: str = "MineU"
    available: bool
    command: str | None = None
    message: str
    accepted_types: list[str] = Field(default_factory=lambda: sorted(MIME_TYPES_BY_EXTENSION.values()))
    max_file_size_bytes: int = Field(ge=1)
