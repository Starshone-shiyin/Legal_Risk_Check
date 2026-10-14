"""Allowed user-material formats and their safe handling metadata."""
from __future__ import annotations

from pathlib import Path


PDF_EXTENSIONS = {".pdf"}
OFFICE_EXTENSIONS = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp"}
VISION_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv"}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | OFFICE_EXTENSIONS | IMAGE_EXTENSIONS | TEXT_EXTENSIONS

MIME_TYPES_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jp2": "image/jp2",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}
ACCEPTED_CONTENT_TYPES = set(MIME_TYPES_BY_EXTENSION.values()) | {"application/octet-stream"}
UPLOAD_ACCEPT_ATTRIBUTE = ",".join(sorted(SUPPORTED_EXTENSIONS))


def extension_for(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def canonical_content_type(filename: str | None) -> str:
    return MIME_TYPES_BY_EXTENSION.get(extension_for(filename), "application/octet-stream")


def is_image_filename(filename: str | None) -> bool:
    return extension_for(filename) in IMAGE_EXTENSIONS


def is_vision_supported_image_filename(filename: str | None) -> bool:
    """Return whether an image can be sent to DeepSeek's vision endpoint."""
    return extension_for(filename) in VISION_IMAGE_EXTENSIONS


def is_text_filename(filename: str | None) -> bool:
    return extension_for(filename) in TEXT_EXTENSIONS
