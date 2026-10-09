"""Stable read-only contracts for MCP access to approved project materials."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any


@dataclass(frozen=True)
class MaterialTool:
    name: str
    required: tuple[str, ...]
    description: str
    read_only: bool = True
    result_type: str = "application/json"


MATERIAL_TOOLS = (
    MaterialTool("list_material_format_capabilities", ("project_id",), "List accepted formats and current parser/search capabilities."),
    MaterialTool("list_knowledge_assets", ("project_id",), "List approved knowledge assets."),
    MaterialTool("search_project_materials", ("project_id", "query"), "Search project materials with ACL/version filters."),
    MaterialTool("get_document", ("project_id", "document_id"), "Read a document or explicit version."),
    MaterialTool("get_document_part", ("project_id", "document_id", "block_id"), "Read one traceable document block."),
    MaterialTool("get_document_structure", ("project_id", "document_id"), "Read a safe heading/block outline."),
    MaterialTool("validate_citations", ("project_id", "citations"), "Validate citation locators against approved material."),
    MaterialTool("get_latest_document", ("project_id", "logical_key"), "Resolve the latest effective document."),
    MaterialTool("compare_document_versions", ("project_id", "asset_family_id", "from_version", "to_version"), "Compare two versions."),
    MaterialTool("compare_versions", ("project_id", "asset_family_id", "from_version", "to_version"), "Compare two versions (task alias)."),
    MaterialTool("get_recent_knowledge_updates", ("project_id", "since"), "List recent approved updates."),
    MaterialTool("build_evidence_pack", ("project_id", "query"), "Build a cited evidence pack."),
    MaterialTool("draft_project_plan", ("project_id", "goal"), "Draft a non-publishable plan outline."),
    MaterialTool("list_knowledge_gaps", ("project_id", "query"), "List explicit evidence gaps."),
    MaterialTool("get_approval_job_status", ("project_id",), "Read a durable project-material approval job without changing it."),
)


TEXT_CODE_FORMATS = {
    "bat", "c", "conf", "cpp", "cs", "css", "csv", "go", "h", "hpp",
    "java", "js", "json", "jsx", "log", "ps1", "py", "rs", "scss", "sh",
    "sql", "ts", "tsx", "vue", "xml", "yaml", "yml",
}
STRUCTURED_CONTENT_FORMATS = {
    "txt", "md", "markdown", "docx", "pdf", "xlsx", "pptx", "html", "htm", "zip",
    "png", "jpg", "jpeg", *TEXT_CODE_FORMATS,
}
METADATA_ONLY_FORMATS = {
    "doc", "xls", "ppt", "rtf", "gif", "svg", "webp", "mp3", "wav", "aac",
    "flac", "m4a", "mp4", "avi", "mkv", "mov", "wmv", "rar", "7z",
    "tar", "gz", "db", "sqlite", "exe", "msi", "dll", "iso", "epub", "mobi", "azw",
}
SUPPORTED_FORMATS = STRUCTURED_CONTENT_FORMATS | METADATA_ONLY_FORMATS
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def parser_capability(fmt: str) -> str:
    value = fmt.lower().lstrip(".")
    if value in METADATA_ONLY_FORMATS:
        return "metadata_only"
    if value in {"png", "jpg", "jpeg"}:
        return "image_metadata_pending_ocr"
    if value in {"pdf", "docx", "pptx", "xlsx"}:
        return "structured_text_extract"
    if value in TEXT_CODE_FORMATS:
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


def normalize_relative_path(value: str) -> str:
    cleaned = str(value or "").strip().replace("\\", "/")
    if not cleaned or "\x00" in cleaned:
        raise ValueError("relative_path is required")
    if cleaned.startswith("/") or cleaned.startswith("//") or _WINDOWS_DRIVE.match(cleaned):
        raise ValueError("relative_path must not be absolute")
    path = PurePosixPath(cleaned)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("relative_path contains an unsafe segment")
    normalized = path.as_posix()
    if len(normalized) > 1024:
        raise ValueError("relative_path is too long")
    return normalized


def validate_material_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "filename", "relative_path", "format", "searchability", "metadata_only",
        "executable", "content_hash", "asset_family_id", "version_number",
        "is_current", "approval_status", "locator",
    }
    for field in sorted(required - result.keys()):
        errors.append(f"missing field {field}")
    fmt = str(result.get("format") or "").lower().lstrip(".")
    if fmt not in SUPPORTED_FORMATS:
        errors.append(f"unsupported format {fmt}")
    if result.get("executable") is not False:
        errors.append("executable must always be false")
    expected_metadata_only = fmt in METADATA_ONLY_FORMATS
    if result.get("metadata_only") is not expected_metadata_only:
        errors.append("metadata_only does not match the format capability")
    expected_searchability = "metadata_only" if expected_metadata_only else "content"
    if result.get("searchability") != expected_searchability:
        errors.append("searchability does not match the format capability")
    try:
        normalize_relative_path(str(result.get("relative_path") or ""))
    except ValueError as error:
        errors.append(str(error))
    if result.get("approval_status") != "approved":
        errors.append("material result must be approved")
    if int(result.get("version_number") or 0) < 1:
        errors.append("version_number must be positive")
    locator = result.get("locator")
    if not isinstance(locator, dict) or not locator.get("document_id"):
        errors.append("locator.document_id is required")
    return errors


def validate_material_tools(tools: tuple[MaterialTool, ...] | list[MaterialTool]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for tool in tools:
        if tool.name in seen:
            errors.append(f"duplicate tool {tool.name}")
        seen.add(tool.name)
        if "project_id" not in tool.required:
            errors.append(f"project_id is required: {tool.name}")
        if not tool.read_only:
            errors.append(f"material tool must be read-only: {tool.name}")
        if not tool.description.strip():
            errors.append(f"description is required: {tool.name}")
    return errors
