"""Durable, side-effect-safe asynchronous material parsing primitives.

The parser intentionally treats uploaded bytes as data.  It never imports,
executes, or shells out to a payload.  A worker can persist the returned text
and metadata in ``project_material_intake_files`` and later rebuild the result
from the retained original object.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import uuid
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:  # production image exposes ``agentops``; source tests use agentops_local
    from agentops.project_memory.parsers import extract_text
    from agentops.project_memory.storage import read_bytes
except ModuleNotFoundError:  # pragma: no cover - source-tree fallback
    from agentops_local.project_memory.parsers import extract_text
    from agentops_local.project_memory.storage import read_bytes


class ParseJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


EXECUTION_BLOCKED_FORMATS = {"exe", "dll", "msi", "iso"}
PARSER_VERSION = "async-safe-v1"
METADATA_ONLY_FORMATS = {
    "exe", "dll", "msi", "iso", "doc", "xls", "ppt", "rtf", "gif", "svg",
    "webp", "mp3", "wav", "aac", "flac", "m4a", "mp4", "avi", "mkv", "mov",
    "wmv", "rar", "7z", "tar", "gz",
}
IMAGE_FORMATS = {"png", "jpg", "jpeg", "webp", "gif", "svg"}
TEXT_MEMBER_FORMATS = {
    "txt", "md", "markdown", "csv", "json", "yaml", "yml", "xml", "html", "htm",
    "py", "ts", "tsx", "js", "jsx", "css", "sql", "log", "conf", "ini", "sh", "bat",
}
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True)
class ParseResult:
    status: str
    text: str
    metadata: dict[str, Any]


def _format(filename: str) -> str:
    suffix = PurePosixPath(str(filename).replace("\\", "/")).suffix.lower().lstrip(".")
    return "html" if suffix == "htm" else suffix


def validate_archive_members(names: Iterable[str], *, max_members: int = 5000) -> None:
    members = list(names)
    if len(members) > max_members:
        raise ValueError(f"archive has too many members (>{max_members})")
    for name in members:
        cleaned = str(name).replace("\\", "/")
        path = PurePosixPath(cleaned)
        if (
            not cleaned
            or "\x00" in cleaned
            or cleaned.startswith("/")
            or cleaned.startswith("//")
            or _WINDOWS_DRIVE.match(cleaned)
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError(f"unsafe archive member: {name}")


def _metadata(fmt: str, size: int, digest: str) -> dict[str, Any]:
    blocked = fmt in EXECUTION_BLOCKED_FORMATS
    return {
        "parser_version": PARSER_VERSION,
        "format": fmt,
        "size_bytes": size,
        "content_hash": digest,
        "metadata_only": fmt in METADATA_ONLY_FORMATS,
        "executable": False,
        "execution_blocked": blocked,
    }


def _parse_archive(raw: bytes, digest: str) -> ParseResult:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            validate_archive_members((info.filename for info in infos))
            texts: list[str] = []
            blocked = 0
            extracted_bytes = 0
            for info in infos:
                fmt = _format(info.filename)
                if fmt in EXECUTION_BLOCKED_FORMATS:
                    blocked += 1
                    continue
                if fmt not in TEXT_MEMBER_FORMATS or info.is_dir():
                    continue
                # Never materialise an archive member on disk.  Bound each
                # member to avoid decompression bombs exhausting the worker.
                if info.file_size > 8 * 1024 * 1024 or extracted_bytes + info.file_size > 64 * 1024 * 1024:
                    continue
                payload = archive.read(info)
                extracted_bytes += len(payload)
                texts.append(payload.decode("utf-8", errors="replace"))
            return ParseResult(
                status=ParseJobStatus.COMPLETED.value,
                text="\n\n".join(item.strip() for item in texts if item.strip()),
                metadata={
                    "parser_version": PARSER_VERSION, "format": "zip", "size_bytes": len(raw), "content_hash": digest,
                    "metadata_only": False, "executable": False,
                    "execution_blocked": False, "archive_members": len(infos),
                    "executable_members_blocked": blocked,
                    "archive_text_bytes": extracted_bytes,
                },
            )
    except zipfile.BadZipFile:
        return ParseResult(
            status=ParseJobStatus.FAILED.value,
            text="",
            metadata={"format": "zip", "size_bytes": len(raw), "content_hash": digest,
                      "parser_version": PARSER_VERSION, "error": "invalid zip archive", "executable": False},
        )


def parse_payload(filename: str, raw: bytes) -> ParseResult:
    """Parse bytes without executing payloads or creating extracted files."""
    fmt = _format(filename)
    digest = hashlib.sha256(raw).hexdigest()
    base = _metadata(fmt, len(raw), digest)
    if fmt == "zip":
        return _parse_archive(raw, digest)
    if fmt in EXECUTION_BLOCKED_FORMATS or fmt in METADATA_ONLY_FORMATS:
        return ParseResult(ParseJobStatus.COMPLETED.value, "", base)
    if fmt in IMAGE_FORMATS:
        base.update({"ocr_status": "pending", "ocr_provider": None})
        return ParseResult(ParseJobStatus.COMPLETED.value, "", base)
    if not raw:
        return ParseResult(ParseJobStatus.FAILED.value, "", {**base, "error": "empty payload"})
    suffix = "." + ("html" if fmt == "html" else fmt or "bin")
    path = None
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(raw)
            path = handle.name
        extracted = extract_text(Path(path))
        return ParseResult(ParseJobStatus.COMPLETED.value, extracted.text, base)
    except Exception as error:
        return ParseResult(ParseJobStatus.FAILED.value, "", {**base, "error": str(error)[:500]})
    finally:
        if path:
            try:
                os.unlink(path)
            except OSError:
                pass


def enqueue_parse_job(
    orm,
    *,
    project_id: uuid.UUID,
    intake_file_id: uuid.UUID,
    created_by_user_id: uuid.UUID | None = None,
    timeout_seconds: int = 900,
    max_attempts: int = 3,
) -> uuid.UUID:
    """Create or return the idempotent queued job for one retained upload."""
    from sqlalchemy import text
    row = orm.execute(
        text("""
            INSERT INTO public.project_material_parse_jobs
                (project_id, intake_file_id, status, timeout_seconds, max_attempts,
                 created_by_user_id)
            VALUES (:project_id, :intake_file_id, 'queued', :timeout_seconds,
                    :max_attempts, :created_by_user_id)
            ON CONFLICT (intake_file_id) DO UPDATE SET updated_at = now()
            RETURNING id
        """),
        {"project_id": str(project_id), "intake_file_id": str(intake_file_id),
         "timeout_seconds": max(1, int(timeout_seconds)), "max_attempts": max(1, int(max_attempts)),
         "created_by_user_id": str(created_by_user_id) if created_by_user_id else None},
    ).first()
    if row is None:
        raise RuntimeError("failed to enqueue material parse job")
    return uuid.UUID(str(row.id))


def claim_next_parse_job(
    orm,
    *,
    worker_id: str,
    lease_seconds: int = 900,
    max_concurrency: int | None = None,
):
    """Claim one queued/retryable/expired job with PostgreSQL row locking."""
    from sqlalchemy import text

    concurrency = max_concurrency or int(os.getenv("PROJECT_MATERIAL_PARSE_MAX_CONCURRENCY", "2"))
    concurrency = max(1, min(concurrency, 32))
    # Reap leases that exhausted their attempts before selecting new work.
    # Without this guard a crashed worker could be claimed forever once its
    # attempt budget was exhausted.
    orm.execute(
        text("""
            UPDATE public.project_material_parse_jobs
               SET status = 'failed', error_message = COALESCE(error_message, 'parse worker lease expired after max attempts'),
                   next_attempt_at = 'infinity'::timestamptz,
                   lease_expires_at = NULL, claimed_by = NULL,
                   completed_at = COALESCE(completed_at, now()), updated_at = now()
             WHERE status = 'running' AND lease_expires_at < now()
               AND attempt_count >= max_attempts
        """),
    )
    row = orm.execute(
        text("""
            SELECT id
              FROM public.project_material_parse_jobs
             WHERE (
                    (status IN ('queued', 'failed') AND next_attempt_at <= now()
                     AND attempt_count < max_attempts)
                 OR (status = 'running' AND lease_expires_at < now()
                     AND attempt_count < max_attempts)
                 )
               AND (SELECT count(*) FROM public.project_material_parse_jobs
                      WHERE status = 'running') < :max_concurrency
             ORDER BY created_at
             FOR UPDATE SKIP LOCKED
             LIMIT 1
        """),
        {"max_concurrency": concurrency},
    ).first()
    if row is None:
        orm.commit()
        return None
    claimed = orm.execute(
        text("""
            UPDATE public.project_material_parse_jobs
               SET status = 'running', claimed_by = :worker_id,
                   attempt_count = attempt_count + 1,
                   lease_expires_at = now() + (:lease_seconds * interval '1 second'),
                   started_at = COALESCE(started_at, now()), completed_at = NULL,
                   error_message = NULL, updated_at = now()
             WHERE id = :job_id
             RETURNING id
        """),
        {"worker_id": worker_id, "job_id": str(row.id), "lease_seconds": max(1, int(lease_seconds))},
    ).first()
    orm.commit()
    return uuid.UUID(str(claimed.id)) if claimed else None


def reap_timed_out_parse_jobs(orm, *, limit: int = 100) -> int:
    """Move jobs exceeding their configured wall-clock timeout to retry/failed."""
    from sqlalchemy import text

    result = orm.execute(
        text("""
            WITH expired AS (
                SELECT id, attempt_count, max_attempts
                  FROM public.project_material_parse_jobs
                 WHERE status = 'running'
                   AND started_at IS NOT NULL
                   AND started_at + (timeout_seconds * interval '1 second') < now()
                 ORDER BY started_at
                 LIMIT :limit
                 FOR UPDATE SKIP LOCKED
            )
            UPDATE public.project_material_parse_jobs AS job
               SET status = 'failed',
                   error_message = 'parse job timed out',
                   next_attempt_at = CASE WHEN expired.attempt_count >= expired.max_attempts
                                          THEN 'infinity'::timestamptz
                                          ELSE now() + interval '30 seconds' END,
                   lease_expires_at = NULL, claimed_by = NULL, updated_at = now()
              FROM expired
             WHERE job.id = expired.id
            RETURNING job.id
        """),
        {"limit": max(1, min(int(limit), 1000))},
    )
    rows = result.all() if hasattr(result, "all") else []
    orm.commit()
    return len(rows)


def cancel_parse_job(orm, *, job_id: uuid.UUID, project_id: uuid.UUID | None = None) -> bool:
    from sqlalchemy import text
    params: dict[str, Any] = {"job_id": str(job_id)}
    scope = ""
    if project_id is not None:
        scope = " AND project_id = :project_id"
        params["project_id"] = str(project_id)
    result = orm.execute(
        text(f"""
            UPDATE public.project_material_parse_jobs
               SET status = 'cancelled', claimed_by = NULL, lease_expires_at = NULL,
                   updated_at = now()
             WHERE id = :job_id{scope}
               AND status IN ('queued', 'running', 'failed')
        """),
        params,
    )
    orm.commit()
    return bool(getattr(result, "rowcount", 0))


def retry_parse_job(orm, *, job_id: uuid.UUID, project_id: uuid.UUID | None = None) -> bool:
    """Explicitly requeue a failed job while it still has retry budget."""
    from sqlalchemy import text
    params: dict[str, Any] = {"job_id": str(job_id)}
    scope = ""
    if project_id is not None:
        scope = " AND project_id = :project_id"
        params["project_id"] = str(project_id)
    result = orm.execute(
        text(f"""
            UPDATE public.project_material_parse_jobs
               SET status = 'queued', error_message = NULL,
                   next_attempt_at = now(), completed_at = NULL,
                   claimed_by = NULL, lease_expires_at = NULL, updated_at = now()
             WHERE id = :job_id{scope} AND status = 'failed'
               AND attempt_count < max_attempts
        """),
        params,
    )
    orm.commit()
    return bool(getattr(result, "rowcount", 0))


def process_parse_job(
    orm,
    job_id: uuid.UUID,
    *,
    worker_id: str | None = None,
) -> str | None:
    """Process one claimed job; original bytes remain the source of truth."""
    from sqlalchemy import text
    row = orm.execute(
        text("""
            SELECT j.id, j.status, j.attempt_count, j.max_attempts,
                   j.claimed_by, j.lease_expires_at,
                   f.filename, f.storage_key, f.raw_content, f.id AS intake_file_id
              FROM public.project_material_parse_jobs j
              JOIN public.project_material_intake_files f ON f.id = j.intake_file_id
             WHERE j.id = :job_id
        """),
        {"job_id": str(job_id)},
    ).first()
    if row is None:
        return None
    if str(row.status) == ParseJobStatus.CANCELLED.value:
        return ParseJobStatus.CANCELLED.value
    owner = worker_id or getattr(row, "claimed_by", None)
    if (
        str(row.status) != ParseJobStatus.RUNNING.value
        or not owner
        or getattr(row, "lease_expires_at", None) is None
    ):
        return "stale"
    try:
        raw = read_bytes(str(row.storage_key)) if getattr(row, "storage_key", None) else bytes(row.raw_content or b"")
        result = parse_payload(str(row.filename), raw)
        if result.status == ParseJobStatus.FAILED.value:
            raise ValueError(str(result.metadata.get("error") or "parse failed"))
        result_update = orm.execute(
            text("""
                UPDATE public.project_material_intake_files
                   SET extracted_text = :extracted_text,
                       parser_metadata = CAST(:parser_metadata AS jsonb)
                 WHERE id = :intake_file_id
                   AND EXISTS (
                       SELECT 1 FROM public.project_material_parse_jobs
                        WHERE id = :job_id AND status = 'running'
                          AND claimed_by = :worker_id
                          AND lease_expires_at > now()
                   )
            """),
            {"extracted_text": result.text, "parser_metadata": json.dumps(result.metadata, ensure_ascii=False),
             "intake_file_id": str(row.intake_file_id), "job_id": str(job_id), "worker_id": owner},
        )
        if not bool(getattr(result_update, "rowcount", 0)):
            orm.rollback()
            return "stale"
        status_update = orm.execute(
            text("""
                UPDATE public.project_material_parse_jobs
                   SET status = 'completed', result_metadata = CAST(:result_metadata AS jsonb),
                       completed_at = now(), lease_expires_at = NULL, claimed_by = NULL, updated_at = now()
                 WHERE id = :job_id AND status = 'running'
                   AND claimed_by = :worker_id AND lease_expires_at > now()
            """),
            {"job_id": str(job_id), "worker_id": owner,
             "result_metadata": json.dumps(result.metadata, ensure_ascii=False)},
        )
        if not bool(getattr(status_update, "rowcount", 0)):
            orm.rollback()
            return "stale"
        orm.commit()
        return ParseJobStatus.COMPLETED.value
    except Exception as error:
        orm.rollback()
        attempts = int(getattr(row, "attempt_count", 1) or 1)
        terminal = attempts >= int(getattr(row, "max_attempts", 3) or 3)
        orm.execute(
            text("""
            UPDATE public.project_material_parse_jobs
               SET status = :status, error_message = :error_message,
                       next_attempt_at = CASE WHEN :terminal THEN 'infinity'::timestamptz
                                              ELSE now() + interval '30 seconds' END,
                       lease_expires_at = NULL, claimed_by = NULL, updated_at = now()
                 WHERE id = :job_id AND status = 'running'
                   AND claimed_by = :worker_id
            """),
            {"job_id": str(job_id), "worker_id": owner, "status": "failed",
             "error_message": str(error)[:4000], "terminal": terminal},
        )
        orm.commit()
        return ParseJobStatus.FAILED.value


def rebuild_parse_result(orm, *, intake_file_id: uuid.UUID) -> ParseResult:
    """Rebuild a derived parse result from the retained immutable original."""
    from sqlalchemy import text

    row = orm.execute(
        text("""
            SELECT filename, storage_key, raw_content
              FROM public.project_material_intake_files
             WHERE id = :intake_file_id
        """),
        {"intake_file_id": str(intake_file_id)},
    ).first()
    if row is None:
        raise ValueError("material intake file not found")
    raw = read_bytes(str(row.storage_key)) if getattr(row, "storage_key", None) else bytes(row.raw_content or b"")
    return parse_payload(str(row.filename), raw)
