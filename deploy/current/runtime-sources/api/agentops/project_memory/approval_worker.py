from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import timedelta
from types import SimpleNamespace

from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.common.orm import get_orm_session
from agentops.project_memory.approval_queue import CONSUMER_GROUP, STREAM_KEY
from agentops.common import cache

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = max(int(os.getenv("PROJECT_MEMORY_APPROVAL_MAX_ATTEMPTS", "5")), 1)
LEASE_SECONDS = max(int(os.getenv("PROJECT_MEMORY_APPROVAL_LEASE_SECONDS", "1800")), 60)


def _update_approval_progress(orm: Session, job_id: uuid.UUID, *, progress: int, step: str) -> None:
    """Persist worker-visible progress independently of the draft transaction."""
    bounded = max(0, min(100, int(progress)))
    orm.execute(
        text("""
            UPDATE public.project_memory_approval_jobs
            SET progress = :progress, current_step = :step, updated_at = now()
            WHERE id = :job_id AND status = 'running'
        """),
        {"job_id": str(job_id), "progress": bounded, "step": step},
    )
    orm.execute(
        text("""
            UPDATE public.project_memory_drafts AS draft
            SET approval_progress = :progress, approval_step = :step, updated_at = now()
            FROM public.project_memory_approval_jobs AS job
            WHERE job.id = :job_id
              AND draft.id = job.draft_id
        """),
        {"job_id": str(job_id), "progress": bounded, "step": step},
    )
    orm.commit()


def process_approval_job(orm: Session, job_id: uuid.UUID):
    """Execute one claimed approval job using the existing transactional path."""
    # The delegated path marks the draft status = 'approved' before this job
    # is finalized as status = 'completed'.
    row = orm.execute(
        text("""
            SELECT id, draft_id, decision, requested_by_user_id, comment, status,
                   attempt_count, claim_token
            FROM public.project_memory_approval_jobs
            WHERE id = :job_id
        """),
        {"job_id": str(job_id)},
    ).first()
    if row is None:
        return None
    try:
        if str(row.decision) != "approve":
            raise ValueError("approval worker only executes approve jobs")
        _update_approval_progress(orm, job_id, progress=5, step="validating")
        from agentops.api.routes.v4.project_memory import (
            ReviewDraftRequest,
            _approve_project_memory_draft_sync,
        )

        request = SimpleNamespace(
            state=SimpleNamespace(
                session=SimpleNamespace(user_id=uuid.UUID(str(row.requested_by_user_id))),
                process_approval_now=True,
            )
        )
        _approve_project_memory_draft_sync(
            request=request,
            draft_id=uuid.UUID(str(row.draft_id)),
            body=ReviewDraftRequest(decision="approve", comment=row.comment),
            orm=orm,
        )
        _update_approval_progress(orm, job_id, progress=95, step="finalizing")
        orm.execute(
            text("""
                UPDATE public.project_memory_approval_jobs
                SET status = 'completed', progress = 100, current_step = 'completed',
                    error_message = NULL, completed_at = now(), updated_at = now(),
                    claim_token = NULL
                WHERE id = :job_id AND status = 'running'
            """),
            {"job_id": str(job_id)},
        )
        orm.commit()
        return "completed"
    except Exception as error:
        orm.rollback()
        attempt = int(getattr(row, "attempt_count", 0) or 0)
        terminal = attempt >= MAX_ATTEMPTS
        orm.execute(
            text("""
                UPDATE public.project_memory_approval_jobs
                SET status = :status,
                    current_step = 'failed',
                    error_message = :error_message,
                    next_attempt_at = CASE
                        WHEN :terminal THEN 'infinity'::timestamptz
                        ELSE now() + :retry_delay
                    END,
                    updated_at = now(), claim_token = NULL
                WHERE id = :job_id AND status = 'running'
            """),
            {
                "job_id": str(job_id),
                "status": "failed",
                "error_message": str(error)[:4000],
                "retry_delay": timedelta(seconds=min(600, 2 ** min(max(attempt, 1), 9))),
                "terminal": terminal,
            },
        )
        orm.commit()
        logger.exception("Project memory approval job failed: %s", job_id)
        return "failed" if terminal else "retry"


def process_next_job(orm: Session):
    """Claim one queued/retryable job with row-level locking."""
    claim_token = uuid.uuid4()
    row = orm.execute(
        text("""
            SELECT id, draft_id, decision, requested_by_user_id, comment,
                   status, attempt_count, claim_token
            FROM public.project_memory_approval_jobs
            WHERE (
                status IN ('queued', 'failed') AND next_attempt_at <= now()
            ) OR (
                status = 'running'
                AND updated_at < now() - (:lease_seconds * interval '1 second')
            )
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED
         LIMIT 1
        """),
        {"lease_seconds": LEASE_SECONDS},
    ).first()
    if row is None:
        orm.commit()
        return None
    claimed = orm.execute(
        text("""
            UPDATE public.project_memory_approval_jobs
            SET status = 'running', current_step = 'starting', progress = GREATEST(progress, 1),
                attempt_count = attempt_count + 1, claim_token = :claim_token,
                started_at = COALESCE(started_at, now()), updated_at = now()
            WHERE id = :job_id
              AND (
                status IN ('queued', 'failed')
                OR (status = 'running' AND updated_at < now() - (:lease_seconds * interval '1 second'))
              )
            RETURNING id
        """),
        {"job_id": str(row.id), "claim_token": str(claim_token), "lease_seconds": LEASE_SECONDS},
    ).first()
    if claimed is None:
        orm.commit()
        return None
    orm.commit()
    return process_approval_job(orm, uuid.UUID(str(row.id)))


def main() -> None:
    # The durable PostgreSQL table is authoritative. Redis is only a wake-up
    # optimization, so a lost stream message cannot lose an approval.
    redis = cache.raw_backend()
    try:
        redis.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except Exception as error:
        if "BUSYGROUP" not in str(error):
            logger.warning("Unable to initialize approval stream group: %s", error)
    while True:
        generator = get_orm_session()
        orm = next(generator)
        try:
            result = process_next_job(orm)
        finally:
            try:
                next(generator)
            except StopIteration:
                pass
        if result is None:
            time.sleep(1)


if __name__ == "__main__":
    main()
