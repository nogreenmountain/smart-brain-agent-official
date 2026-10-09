"""Versioned parser capability manifest for asynchronous material ingestion.

The manifest is deliberately declarative.  It lets the API, workers and MCP
surface the same promise for each format without coupling callers to a parser
implementation.  Every capability is asynchronous and declares a safe
fallback; unsupported/deferred formats remain metadata-only and are never
executed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ParserCapability:
    extension: str
    parser: str
    fallback: str
    asynchronous: bool = True
    executable: bool = False
    metadata_only: bool = False


def _capability(
    extension: str,
    parser: str,
    fallback: str,
    *,
    metadata_only: bool = False,
) -> ParserCapability:
    return ParserCapability(
        extension=extension,
        parser=parser,
        fallback=fallback,
        metadata_only=metadata_only,
    )


DEFAULT_CAPABILITIES: tuple[ParserCapability, ...] = (
    _capability(".pdf", "structured-text", "metadata-only"),
    _capability(".docx", "structured-text", "metadata-only"),
    _capability(".pptx", "structured-text", "metadata-only"),
    _capability(".xlsx", "structured-table", "metadata-only"),
    _capability(".png", "ocr", "metadata-only"),
    _capability(".jpg", "ocr", "metadata-only"),
    _capability(".jpeg", "ocr", "metadata-only"),
    _capability(".py", "code-text", "metadata-only"),
    _capability(".ts", "code-text", "metadata-only"),
    _capability(".js", "code-text", "metadata-only"),
    _capability(".yaml", "text", "metadata-only"),
    _capability(".yml", "text", "metadata-only"),
    _capability(".md", "text", "metadata-only"),
    _capability(".txt", "text", "metadata-only"),
    _capability(".zip", "safe-archive", "metadata-only"),
    _capability(".exe", "blocked", "metadata-only", metadata_only=True),
    _capability(".dll", "blocked", "metadata-only", metadata_only=True),
    _capability(".msi", "blocked", "metadata-only", metadata_only=True),
    _capability(".iso", "blocked", "metadata-only", metadata_only=True),
)


def validate_capabilities(capabilities: Iterable[ParserCapability]) -> list[str]:
    """Return contract violations without mutating or executing anything."""
    errors: list[str] = []
    seen: set[str] = set()
    for item in capabilities:
        extension = str(item.extension or "").lower()
        if not extension.startswith(".") or len(extension) == 1:
            errors.append(f"invalid extension: {item.extension}")
        if extension in seen:
            errors.append(f"duplicate extension: {extension}")
        seen.add(extension)
        if not item.parser.strip():
            errors.append(f"parser is required: {extension}")
        if not item.asynchronous:
            errors.append(f"capability must be asynchronous: {extension}")
        if not item.fallback.strip():
            errors.append(f"safe fallback is required: {extension}")
        if item.executable:
            errors.append(f"executable capability is forbidden: {extension}")
        if item.metadata_only and item.fallback != "metadata-only":
            errors.append(f"metadata-only capability must fall back to metadata-only: {extension}")
    return errors


__all__ = ["DEFAULT_CAPABILITIES", "ParserCapability", "validate_capabilities"]
