"""Durable primitives for project department metadata migrations.

The API may still dispatch the current worker in-process, but these helpers
define the production-safe task contract: stable task IDs, bounded leases,
cursor checkpoints, idempotent enqueue, cancellation, and retryable terminal
failures.  They intentionally do not delete or roll back project data.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any

from sqlalchemy import text


def enqueue_department_migration(
    orm,
    *,
    project_id: uuid.UUID,
    source_department_id: str,
    target_department_id: str,
    requested_by_user_id: uuid.UUID,
    idempotency_key: str | None = None,
    max_attempts: int = 3,
    total_count: int = 0,
) -> uuid.UUID:
    """Create or return a migration task without duplicate active work."""
    params = {
        "project_id": str(project_id),
        "source_department_id": source_department_id,
        "target_department_id": target_department_id,
        "requested_by_user_id": str(requested_by_user_id),
        "idempotency_key": idempotency_key,
        "max_attempts": max(1, int(max_attempts)),
        "total_count": max(0, int(total_count)),
    }
    row = orm.execute(
        text("""
            INSERT INTO public.project_department_migrations (
                task_id, project_id, source_department_id, target_department_id,
                requested_by_user_id, idempotency_key, status, current_step,
                progress, max_attempts, total_count, remaining_count
            ) VALUES (
                :task_id, :project_id, :source_department_id, :target_department_id,
                :requested_by_user_id, :idempotency_key, 'queued', 'queued', 0,
                :max_attempts, :total_count, :total_count
            )
            ON CONFLICT DO NOTHING
            RETURNING task_id
        """),
        {**params, "task_id": str(uuid.uuid4())},
    ).first()
    if row is None:
        row = orm.execute(
            text("""
                SELECT task_id FROM public.project_department_migrations
                 WHERE project_id = :project_id
                   AND requested_by_user_id = :requested_by_user_id
                   AND idempotency_key IS NOT DISTINCT FROM :idempotency_key
                 ORDER BY created_at DESC LIMIT 1
            """),
            params,
        ).first()
    if row is None:
        raise RuntimeError("failed to persist project department migration task")
    orm.commit()
    return uuid.UUID(str(row.task_id))


def claim_next_department_migration(
    orm,
    *,
    worker_id: str,
    lease_seconds: int | None = None,
    max_concurrency: int = 1,
):
    lease = max(30, int(lease_seconds or os.getenv("PROJECT_DEPARTMENT_MIGRATION_LEASE_SECONDS", "900")))
    concurrency = max(1, min(int(max_concurrency), 8))
    # Finalize cooperative controls for a worker that died before observing
    # them. Otherwise a requested pause/cancel can leave a row permanently
    # running because the normal claim predicate excludes requested controls.
    orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = CASE WHEN cancel_requested THEN 'cancelled' ELSE 'paused' END,
                   current_step = CASE WHEN cancel_requested THEN 'cancelled' ELSE 'paused' END,
                   next_attempt_at = 'infinity'::timestamptz,
                   lease_expires_at = NULL, claimed_by = NULL,
                   completed_at = CASE WHEN cancel_requested THEN COALESCE(completed_at, now()) ELSE NULL END,
                   updated_at = now()
             WHERE status = 'running'
               AND (lease_expires_at IS NULL OR lease_expires_at < now())
               AND (cancel_requested OR pause_requested)
        """),
    )
    # A worker that died after consuming the final attempt must not be run a
    # fourth time. Reap that lease before selecting retryable work.
    orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = 'failed', current_step = 'failed',
                   error_message = COALESCE(error_message, 'worker lease expired after max attempts'),
                   next_attempt_at = 'infinity'::timestamptz,
                   lease_expires_at = NULL, claimed_by = NULL,
                   completed_at = COALESCE(completed_at, now()), updated_at = now()
             WHERE status = 'running' AND lease_expires_at < now()
               AND attempt_count >= max_attempts
               AND cancel_requested = false AND pause_requested = false
        """),
    )
    row = orm.execute(
        text("""
            SELECT id, task_id
              FROM public.project_department_migrations
             WHERE (
                    (status IN ('queued', 'failed')
                     AND next_attempt_at <= now()
                     AND attempt_count < max_attempts)
                 OR (status = 'running' AND lease_expires_at < now()
                     AND attempt_count < max_attempts)
             )
               AND cancel_requested = false AND pause_requested = false
               AND (SELECT count(*) FROM public.project_department_migrations
                      WHERE status = 'running') < :max_concurrency
             ORDER BY created_at
             FOR UPDATE SKIP LOCKED LIMIT 1
        """),
        {"max_concurrency": concurrency},
    ).first()
    if row is None:
        orm.commit()
        return None
    claimed = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = 'running', claimed_by = :worker_id,
                   attempt_count = attempt_count + 1,
                   lease_expires_at = now() + (:lease_seconds * interval '1 second'),
                   started_at = COALESCE(started_at, now()), updated_at = now()
             WHERE id = :id AND cancel_requested = false AND pause_requested = false
             RETURNING task_id
        """),
        {"id": str(row.id), "worker_id": worker_id, "lease_seconds": lease},
    ).first()
    orm.commit()
    return uuid.UUID(str(claimed.task_id)) if claimed else None


def claim_department_migration(
    orm,
    *,
    migration_id: uuid.UUID,
    worker_id: str,
    lease_seconds: int | None = None,
) -> uuid.UUID | None:
    """Atomically claim one specific migration for an API-dispatched worker.

    A dispatch can race with another process (or a stale worker whose lease
    expired).  The row lock plus the eligibility predicate makes claiming
    idempotent and fences the previous worker by replacing ``claimed_by``.
    """
    lease = max(30, int(lease_seconds or os.getenv("PROJECT_DEPARTMENT_MIGRATION_LEASE_SECONDS", "900")))
    orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = CASE WHEN cancel_requested THEN 'cancelled' ELSE 'paused' END,
                   current_step = CASE WHEN cancel_requested THEN 'cancelled' ELSE 'paused' END,
                   next_attempt_at = 'infinity'::timestamptz,
                   lease_expires_at = NULL, claimed_by = NULL,
                   completed_at = CASE WHEN cancel_requested THEN COALESCE(completed_at, now()) ELSE NULL END,
                   updated_at = now()
             WHERE id = :migration_id AND status = 'running'
               AND (lease_expires_at IS NULL OR lease_expires_at < now())
               AND (cancel_requested OR pause_requested)
        """),
        {"migration_id": str(migration_id)},
    )
    orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = 'failed', current_step = 'failed',
                   error_message = COALESCE(error_message, 'worker lease expired after max attempts'),
                   next_attempt_at = 'infinity'::timestamptz,
                   lease_expires_at = NULL, claimed_by = NULL,
                   completed_at = COALESCE(completed_at, now()), updated_at = now()
             WHERE id = :migration_id AND status = 'running'
               AND lease_expires_at < now() AND attempt_count >= max_attempts
               AND cancel_requested = false AND pause_requested = false
        """),
        {"migration_id": str(migration_id)},
    )
    claimed = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = 'running', claimed_by = :worker_id,
                   attempt_count = attempt_count + 1,
                   lease_expires_at = now() + (:lease_seconds * interval '1 second'),
                   started_at = COALESCE(started_at, now()), completed_at = NULL,
                   error_message = NULL, updated_at = now()
             WHERE id = :migration_id
               AND cancel_requested = false AND pause_requested = false
               AND (
                    (status IN ('queued', 'failed')
                     AND COALESCE(next_attempt_at, now()) <= now()
                     AND attempt_count < max_attempts)
                 OR (status = 'running'
                     AND (lease_expires_at IS NULL OR lease_expires_at < now())
                     AND attempt_count < max_attempts)
               )
             RETURNING task_id
        """),
        {
            "migration_id": str(migration_id),
            "worker_id": worker_id,
            "lease_seconds": lease,
        },
    ).first()
    orm.commit()
    return uuid.UUID(str(claimed.task_id)) if claimed and getattr(claimed, "task_id", None) else None


def heartbeat_department_migration(orm, *, task_id: uuid.UUID, worker_id: str, lease_seconds: int = 900) -> bool:
    result = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET lease_expires_at = now() + (:lease_seconds * interval '1 second'), updated_at = now()
             WHERE task_id = :task_id AND claimed_by = :worker_id AND status = 'running'
               AND lease_expires_at > now()
        """),
        {"task_id": str(task_id), "worker_id": worker_id, "lease_seconds": max(30, int(lease_seconds))},
    )
    ok = bool(getattr(result, "rowcount", 0))
    if ok:
        orm.commit()
    else:
        # Never commit business mutations from a worker that lost its lease.
        orm.rollback()
    return ok


def pause_department_migration(
    orm,
    *,
    task_id: uuid.UUID,
    worker_id: str | None = None,
) -> bool:
    """Request a cooperative pause; a matching worker may finalize it safely."""
    if worker_id:
        result = orm.execute(
            text("""
                UPDATE public.project_department_migrations
                   SET pause_requested = true, status = 'paused',
                       next_attempt_at = 'infinity'::timestamptz,
                       lease_expires_at = NULL, claimed_by = NULL,
                       completed_at = NULL, updated_at = now()
                 WHERE task_id = :task_id AND claimed_by = :worker_id
                   AND status = 'running' AND lease_expires_at > now()
            """),
            {"task_id": str(task_id), "worker_id": worker_id},
        )
        orm.commit()
        return bool(getattr(result, "rowcount", 0))
    result = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET pause_requested = true,
                   status = CASE
                       WHEN status IN ('queued', 'failed') THEN 'paused'
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN 'paused'
                       ELSE status
                   END,
                   next_attempt_at = CASE
                       WHEN status IN ('queued', 'failed') THEN 'infinity'::timestamptz
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN 'infinity'::timestamptz
                       ELSE next_attempt_at
                   END,
                   lease_expires_at = CASE
                       WHEN status IN ('queued', 'failed') THEN NULL
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN NULL
                       ELSE lease_expires_at
                   END,
                   claimed_by = CASE
                       WHEN status IN ('queued', 'failed') THEN NULL
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN NULL
                       ELSE claimed_by
                   END,
                   completed_at = NULL, updated_at = now()
             WHERE task_id = :task_id AND status IN ('queued', 'running', 'failed')
        """),
        {"task_id": str(task_id)},
    )
    orm.commit()
    return bool(getattr(result, "rowcount", 0))


def resume_department_migration(orm, *, task_id: uuid.UUID) -> bool:
    """Make a paused task eligible again while preserving its cursor."""
    result = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = 'queued', pause_requested = false,
                   next_attempt_at = now(), completed_at = NULL,
                   error_message = NULL, updated_at = now()
             WHERE task_id = :task_id AND status = 'paused'
        """),
        {"task_id": str(task_id)},
    )
    orm.commit()
    return bool(getattr(result, "rowcount", 0))


def update_department_migration_progress(
    orm,
    *,
    task_id: uuid.UUID,
    worker_id: str,
    current_step: str,
    progress: int,
    cursor: dict[str, Any] | None = None,
) -> bool:
    result = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET current_step = :current_step, progress = :progress,
                   cursor = COALESCE(CAST(:cursor AS jsonb), cursor),
                   last_cursor = COALESCE(CAST(:cursor AS jsonb), last_cursor),
                   elapsed_seconds = CASE WHEN started_at IS NULL THEN elapsed_seconds
                                         ELSE EXTRACT(EPOCH FROM (now() - started_at))::int END,
                   updated_at = now()
             WHERE task_id = :task_id AND claimed_by = :worker_id AND status = 'running'
               AND lease_expires_at > now()
        """),
        {
            "task_id": str(task_id), "worker_id": worker_id,
            "current_step": current_step, "progress": max(0, min(int(progress), 100)),
            "cursor": json.dumps(cursor, ensure_ascii=False) if cursor is not None else None,
        },
    )
    ok = bool(getattr(result, "rowcount", 0))
    if ok:
        orm.commit()
    else:
        orm.rollback()
    return ok


def request_cancel_department_migration(orm, *, task_id: uuid.UUID) -> bool:
    result = orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET cancel_requested = true,
                   status = CASE
                       WHEN status IN ('queued', 'failed', 'paused') THEN 'cancelled'
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN 'cancelled'
                       ELSE status
                   END,
                   completed_at = CASE
                       WHEN status IN ('queued', 'failed', 'paused') THEN now()
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN now()
                       ELSE completed_at
                   END,
                   lease_expires_at = CASE
                       WHEN status IN ('queued', 'failed', 'paused') THEN NULL
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN NULL
                       ELSE lease_expires_at
                   END,
                   claimed_by = CASE
                       WHEN status IN ('queued', 'failed', 'paused') THEN NULL
                       WHEN status = 'running' AND (lease_expires_at IS NULL OR lease_expires_at < now()) THEN NULL
                       ELSE claimed_by
                   END,
                   updated_at = now()
             WHERE task_id = :task_id AND status IN ('queued', 'running', 'failed', 'paused')
        """),
        {"task_id": str(task_id)},
    )
    orm.commit()
    return bool(getattr(result, "rowcount", 0))


def finish_department_migration(
    orm,
    *,
    task_id: uuid.UUID,
    worker_id: str,
    success: bool,
    error_message: str | None = None,
) -> str:
    """Persist a fenced completion/failure and schedule bounded retries."""
    row = orm.execute(
        text("""
            SELECT attempt_count, max_attempts, cancel_requested, pause_requested
              FROM public.project_department_migrations
             WHERE task_id = :task_id AND claimed_by = :worker_id AND status = 'running'
               AND lease_expires_at > now()
             FOR UPDATE
        """),
        {"task_id": str(task_id), "worker_id": worker_id},
    ).first()
    if row is None:
        orm.rollback()
        return "stale"
    if bool(row.cancel_requested):
        status = "cancelled"
    elif bool(getattr(row, "pause_requested", False)):
        status = "paused"
    elif success:
        status = "completed"
    else:
        status = "failed"
    terminal = status in {"completed", "cancelled", "paused"} or int(row.attempt_count or 0) >= int(row.max_attempts or 3)
    orm.execute(
        text("""
            UPDATE public.project_department_migrations
               SET status = :status, current_step = :status,
                   progress = CASE WHEN :status = 'completed' THEN 100 ELSE progress END,
                   failed_count = CASE
                       WHEN :status = 'failed' AND total_count > succeeded_count
                       THEN GREATEST(failed_count, 1)
                       ELSE failed_count
                   END,
                   remaining_count = GREATEST(
                       total_count - succeeded_count - CASE
                           WHEN :status = 'failed' AND total_count > succeeded_count
                           THEN GREATEST(failed_count, 1)
                           ELSE failed_count
                       END,
                       0
                   ),
                   error_message = :error_message,
                   next_attempt_at = CASE WHEN :terminal THEN 'infinity'::timestamptz ELSE now() + interval '30 seconds' END,
                   lease_expires_at = NULL, claimed_by = NULL,
                   completed_at = CASE
                       WHEN :status = 'paused' THEN NULL
                       WHEN :terminal THEN now()
                       ELSE NULL
                   END,
                   elapsed_seconds = CASE WHEN started_at IS NULL THEN elapsed_seconds
                                         ELSE EXTRACT(EPOCH FROM (now() - started_at))::int END,
                   updated_at = now()
             WHERE task_id = :task_id
        """),
        {"task_id": str(task_id), "status": status, "error_message": error_message, "terminal": terminal},
    )
    orm.commit()
    # Keep the persisted status as ``failed`` while allowing the dispatcher
    # (or an external worker loop) to claim it again after ``next_attempt_at``.
    return "retry" if status == "failed" and not terminal else status
