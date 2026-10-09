"""Serialization and safety helpers for read-only material MCP tools."""
from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Any


TEXT_CODE_FORMATS = {
    "bat", "c", "conf", "cpp", "cs", "css", "csv", "go", "h", "hpp",
    "java", "js", "json", "jsx", "log", "ps1", "py", "rs", "scss", "sh",
    "sql", "ts", "tsx", "vue", "xml", "yaml", "yml",
}
CONTENT_FORMATS = {
    "txt", "md", "markdown", "docx", "pdf", "xlsx", "pptx", "html", "htm", "zip",
    "png", "jpg", "jpeg", *TEXT_CODE_FORMATS,
}
METADATA_ONLY_FORMATS = {
    "doc", "xls", "ppt", "rtf", "gif", "svg", "webp", "mp3", "wav", "aac",
    "flac", "m4a", "mp4", "avi", "mkv", "mov", "wmv", "rar", "7z",
    "tar", "gz", "db", "sqlite", "exe", "msi", "dll", "iso", "epub", "mobi", "azw",
}
SUPPORTED_FORMATS = CONTENT_FORMATS | METADATA_ONLY_FORMATS
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def _value(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def normalize_relative_path(value: str | None, *, fallback: str) -> str:
    cleaned = str(value or fallback).strip().replace("\\", "/")
    if (
        not cleaned
        or "\x00" in cleaned
        or cleaned.startswith("/")
        or cleaned.startswith("//")
        or _WINDOWS_DRIVE.match(cleaned)
    ):
        cleaned = PurePosixPath(str(fallback).replace("\\", "/")).name
    path = PurePosixPath(cleaned)
    if any(part in {"", ".", ".."} for part in path.parts):
        return PurePosixPath(str(fallback).replace("\\", "/")).name
    return path.as_posix()[:1024]


def parser_capability(fmt: str) -> str:
    if fmt in METADATA_ONLY_FORMATS:
        return "metadata_only"
    if fmt in {"png", "jpg", "jpeg"}:
        return "image_metadata_pending_ocr"
    if fmt in {"pdf", "docx", "pptx", "xlsx"}:
        return "structured_text_extract"
    if fmt == "zip":
        return "safe_archive_extract"
    if fmt in TEXT_CODE_FORMATS:
        return "text_or_code_extract"
    return "text_extract"


def format_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "format": fmt,
            "accepted": True,
            "searchability": "metadata_only" if fmt in METADATA_ONLY_FORMATS else "content",
            "metadata_only": fmt in METADATA_ONLY_FORMATS,
            "executable": False,
            "parser_capability": parser_capability(fmt),
        }
        for fmt in sorted(SUPPORTED_FORMATS)
    ]


def material_item(row: Any, *, include_excerpt: bool = False) -> dict[str, Any]:
    document_id = str(_value(row, "document_id"))
    filename = str(_value(row, "filename") or "unnamed")
    relative_path = normalize_relative_path(_value(row, "relative_path"), fallback=filename)
    fmt = str(_value(row, "format") or "").lower().lstrip(".")
    metadata_only = fmt in METADATA_ONLY_FORMATS
    version_number = int(_value(row, "version_number") or 1)
    asset_family_id = str(_value(row, "asset_family_id") or document_id)
    locator = {
        "document_id": document_id,
        "relative_path": relative_path,
    }
    for source, target in (
        ("chunk_id", "block_id"),
        ("chunk_index", "chunk_index"),
        ("source_page", "page"),
        ("source_line", "line"),
        ("heading_path", "heading_path"),
    ):
        value = _value(row, source)
        if value is not None:
            locator[target] = str(value) if source == "chunk_id" else value
    citation_locator = f", p.{locator['page']}" if locator.get("page") else ""
    result = {
        "document_id": document_id,
        "filename": filename,
        "display_name": str(_value(row, "display_name") or filename),
        "relative_path": relative_path,
        "format": fmt,
        "size_bytes": int(_value(row, "size_bytes") or 0),
        "searchability": "metadata_only" if metadata_only else "content",
        "metadata_only": metadata_only,
        "executable": False,
        "parser_capability": parser_capability(fmt),
        "content_hash": _value(row, "content_hash"),
        "asset_family_id": asset_family_id,
        "version_number": version_number,
        "is_current": bool(_value(row, "is_current", True)),
        "approval_status": str(_value(row, "approval_status") or "approved"),
        "chunk_count": int(_value(row, "chunk_count") or 0),
        "created_at": str(_value(row, "created_at")) if _value(row, "created_at") else None,
        "updated_at": str(_value(row, "updated_at")) if _value(row, "updated_at") else None,
        "locator": locator,
        "citation": f"[资料: {relative_path}, v{version_number}{citation_locator}]",
    }
    if include_excerpt:
        result["excerpt"] = str(_value(row, "excerpt") or "")[:2000]
        result["score"] = float(_value(row, "score") or 0.0)
    return result
