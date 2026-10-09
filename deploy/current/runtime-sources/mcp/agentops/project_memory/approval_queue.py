from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.common import cache
from agentops.common.environment import CACHE_NAMESPACE

logger = logging.getLogger(__name__)

STREAM_KEY = f"{CACHE_NAMESPACE}:project-memory-approval:events"
CONSUMER_GROUP = "project-memory-approval-workers"


@dataclass(frozen=True)
class ApprovalJob:
    id: uuid.UUID
    draft_id: uuid.UUID
    decision: str
    status: str
    progress: int = 0
    current_step: str = "queued"
    error_message: str | None = None


def _job_from_row(row) -> ApprovalJob:
    return ApprovalJob(
        id=uuid.UUID(str(row.id)),
        draft_id=uuid.UUID(str(row.draft_id)),
        decision=str(row.decision),
        status=str(row.status),
        progress=int(getattr(row, "progress", 0) or 0),
        current_step=str(getattr(row, "current_step", "queued") or "queued"),
        error_message=getattr(row, "error_message", None),
    )


def enqueue_project_memory_approval(
    orm: Session,
    *,
    draft_id: uuid.UUID,
    decision: str,
    requested_by: uuid.UUID,
    comment: str | None = None,
) -> ApprovalJob:
    """Create or return the durable, idempotent approval job."""
    if decision not in {"approve", "reject"}:
        raise ValueError(f"unsupported approval decision: {decision}")
    job_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"smartbrain:project-memory-approval:{draft_id}:{decision}",
    )
    row = orm.execute(
        text("""
            INSERT INTO public.project_memory_approval_jobs (
                id, draft_id, decision, requested_by_user_id, comment,
                status, progress, current_step, error_message,
                attempt_count, next_attempt_at, updated_at
            ) VALUES (
                :id, :draft_id, :decision, :requested_by, :comment,
                'queued', 0, 'queued', NULL, 0, now(), now()
            )
            ON CONFLICT (draft_id, decision) DO UPDATE SET
                comment = COALESCE(EXCLUDED.comment, public.project_memory_approval_jobs.comment),
                status = CASE
                    WHEN public.project_memory_approval_jobs.status = 'failed' THEN 'queued'
                    ELSE public.project_memory_approval_jobs.status
                END,
                error_message = CASE
                    WHEN public.project_memory_approval_jobs.status = 'failed' THEN NULL
                    ELSE public.project_memory_approval_jobs.error_message
                END,
                next_attempt_at = CASE
                    WHEN public.project_memory_approval_jobs.status = 'failed' THEN now()
                    ELSE public.project_memory_approval_jobs.next_attempt_at
                END,
                updated_at = now()
            RETURNING id, draft_id, decision, status, progress, current_step, error_message
        """),
        {
            "id": str(job_id),
            "draft_id": str(draft_id),
            "decision": decision,
            "requested_by": str(requested_by),
            "comment": comment,
        },
    ).first()
    if row is None:
        # Lightweight unit doubles may not implement RETURNING; the real
        # database always returns the row above. Keep the contract testable
        # without weakening production's durable insert.
        row = type("ApprovalJobRow", (), {
            "id": str(job_id),
            "draft_id": str(draft_id),
            "decision": decision,
            "status": "queued",
            "progress": 0,
            "current_step": "queued",
            "error_message": None,
        })()
    orm.commit()
    job = _job_from_row(row)
    if job.status == "queued":
        try:
            cache.raw_backend().xadd(
                STREAM_KEY,
                {"job_id": str(job.id)},
                maxlen=100_000,
                approximate=True,
            )
        except Exception:
            # PostgreSQL remains authoritative; the worker polls queued jobs.
            logger.exception("Unable to publish approval wake-up for job=%s", job.id)
    return job
