"""Deterministic document-family and version decisions for approved materials."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePath
import re
import unicodedata
import uuid
from typing import Any, Iterable, Mapping

_VERSION_SUFFIX = re.compile(r"(?:[\s._-]*(?:v|ver|version|版本)[\s._-]*\d+(?:[._-]\d+)*)$", re.IGNORECASE)
_DRAFT_SUFFIX = re.compile(r"(?:[\s._-]*(?:final|final版|最新版|终版|定稿|修订版|草稿))$", re.IGNORECASE)

@dataclass(frozen=True)
class VersionDecision:
    asset_family_id: uuid.UUID
    version_number: int
    normalized_filename: str
    is_current: bool
    supersedes_document_id: uuid.UUID | None
    version_conflict: bool = False
    conflict_reason: str | None = None
    is_duplicate: bool = False
    duplicate_document_id: uuid.UUID | None = None

def _value(row: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)

def _uuid(value: Any) -> uuid.UUID | None:
    if value in {None, ""}:
        return None
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))

def _time(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

def normalize_document_family_key(filename: str) -> str:
    safe_name = PurePath(str(filename or "document").replace("\\", "/")).name
    normalized = unicodedata.normalize("NFKC", safe_name).strip()
    stem, dot, suffix = normalized.rpartition(".")
    if not dot or not stem:
        stem, suffix = normalized, ""
    stem = re.sub(r"\s+", " ", stem).strip()
    stem = _DRAFT_SUFFIX.sub("", _VERSION_SUFFIX.sub("", stem)).rstrip(" ._-") or "document"
    result = stem.casefold()
    return (result + ("." + suffix.casefold() if suffix else ""))[:255]

def decide_document_version(*, filename: str, content_hash: str, existing: Iterable[Mapping[str, Any] | Any], asset_family_id: uuid.UUID | str | None = None, effective_at: datetime | str | None = None, source_modified_at: datetime | str | None = None) -> VersionDecision:
    rows = list(existing)
    normalized = normalize_document_family_key(filename)
    explicit_family = _uuid(asset_family_id)
    for row in rows:
        if content_hash and str(_value(row, "content_hash") or "") == content_hash:
            document_id = _uuid(_value(row, "document_id"))
            family_id = _uuid(_value(row, "asset_family_id")) or document_id or uuid.uuid4()
            return VersionDecision(asset_family_id=family_id, version_number=max(1, int(_value(row, "version_number") or 1)), normalized_filename=str(_value(row, "normalized_filename") or normalized), is_current=bool(_value(row, "is_current", True)), supersedes_document_id=None, is_duplicate=True, duplicate_document_id=document_id)
    family_rows = []
    for row in rows:
        row_family = _uuid(_value(row, "asset_family_id"))
        row_key = str(_value(row, "normalized_filename") or normalize_document_family_key(str(_value(row, "filename") or "document")))
        if (explicit_family and row_family == explicit_family) or (explicit_family is None and row_key == normalized):
            family_rows.append(row)
    if not family_rows:
        return VersionDecision(asset_family_id=explicit_family or uuid.uuid4(), version_number=1, normalized_filename=normalized, is_current=True, supersedes_document_id=None)
    family_id = explicit_family or next((_uuid(_value(row, "asset_family_id")) for row in family_rows if _uuid(_value(row, "asset_family_id"))), None) or _uuid(_value(family_rows[0], "document_id")) or uuid.uuid4()
    max_version = max(max(1, int(_value(row, "version_number") or 1)) for row in family_rows)
    current = max((row for row in family_rows if bool(_value(row, "is_current", False))), key=lambda row: int(_value(row, "version_number") or 1), default=max(family_rows, key=lambda row: int(_value(row, "version_number") or 1)))
    candidate_effective = _time(effective_at)
    current_effective = _time(_value(current, "effective_at"))
    if candidate_effective is not None and current_effective is not None:
        if candidate_effective == current_effective:
            return VersionDecision(asset_family_id=family_id, version_number=max_version + 1, normalized_filename=normalized, is_current=False, supersedes_document_id=None, version_conflict=True, conflict_reason="equal_effective_at")
        if candidate_effective < current_effective:
            return VersionDecision(asset_family_id=family_id, version_number=max_version + 1, normalized_filename=normalized, is_current=False, supersedes_document_id=None, conflict_reason="historical_effective_at")
    _time(source_modified_at)
    return VersionDecision(asset_family_id=family_id, version_number=max_version + 1, normalized_filename=normalized, is_current=True, supersedes_document_id=_uuid(_value(current, "document_id")))
