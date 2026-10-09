import json
import os
import time
import urllib.request

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from agentops.common.middleware import (
    CacheControlMiddleware,
    ExceptionMiddleware,
    DefaultContentTypeMiddleware,
)
from agentops.api.routes import v1, v2, v3, v4
from agentops.common import cache
from agentops.common.orm import get_engine
from agentops.ingest_queue import (
    INGEST_CONSUMER_GROUP,
    PENDING_ENTRY_MAX_AGE_SECONDS,
    STREAM_KEY,
    WORKER_HEARTBEAT_KEY,
    WORKER_HEARTBEAT_MAX_AGE_SECONDS,
)


app = fastapi.FastAPI(
    docs_url=None,
    openapi_url=None,
    title="AgentOps API",
    description="AgentOps API for managing sessions, agents, and events",
)

# Middleware order matters. FastAPI wraps them so the *last added* is the
# outermost. We want ExceptionMiddleware on the OUTSIDE so that any
# HTTPException / 500 response it generates still passes through
# CORSMiddleware on the way out (otherwise CORS headers are missing and
# the browser fails the preflight/login response).
app.add_middleware(ExceptionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CacheControlMiddleware)
app.add_middleware(DefaultContentTypeMiddleware)

app.include_router(v1.router)
app.include_router(v2.router)
app.include_router(v3.router)
app.include_router(v4.router)


@app.get("/health")
async def health_check():
    return {"message": "Server Up"}


@app.get("/health/ready")
def readiness_check():
    checks = {"redis": False, "postgres": False, "auth": False}
    errors = {}
    try:
        checks["redis"] = cache.ping()
    except Exception as error:
        errors["redis"] = str(error)[:200]
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["postgres"] = True
    except Exception as error:
        errors["postgres"] = str(error)[:200]
    try:
        auth_url = os.environ["SUPABASE_URL"].rstrip("/") + "/auth/v1/health"
        with urllib.request.urlopen(auth_url, timeout=3) as response:
            checks["auth"] = 200 <= response.status < 300
    except Exception as error:
        errors["auth"] = str(error)[:200]
    if not all(checks.values()):
        raise fastapi.HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks, "errors": errors},
        )
    return {"status": "ready", "checks": checks}


@app.get("/health/queue")
def queue_health_check():
    try:
        with get_engine().connect() as connection:
            row = connection.execute(
                text("""
                    SELECT count(*) FILTER (
                               WHERE status = 'processing'
                                 AND next_attempt_at <= now()
                           ) AS expired_leases,
                           count(*) FILTER (
                               WHERE status = 'accepted'
                                 AND next_attempt_at <= now()
                                 AND accepted_at < now() - interval '15 minutes'
                           ) AS overdue_accepted,
                           count(*) FILTER (WHERE status = 'dead_letter') AS dead_letters,
                           count(*) FILTER (WHERE status = 'accepted') AS accepted,
                           count(*) FILTER (WHERE status = 'processing') AS processing
                    FROM public.ingest_queue_receipts
                """)
            ).first()
    except Exception as error:
        raise fastapi.HTTPException(
            status_code=503,
            detail={"status": "unavailable", "error": str(error)[:200]},
        ) from error

    snapshot = {
        "expired_leases": int(row.expired_leases or 0),
        "overdue_accepted": int(row.overdue_accepted or 0),
        "dead_letters": int(row.dead_letters or 0),
        "accepted": int(row.accepted or 0),
        "processing": int(row.processing or 0),
    }
    try:
        redis_snapshot = _queue_redis_snapshot(cache.raw_backend())
    except Exception as error:
        raise fastapi.HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                **snapshot,
                "error": f"queue Redis health unavailable: {str(error)[:160]}",
            },
        ) from error
    snapshot.update(redis_snapshot)
    if (
        snapshot["expired_leases"]
        or snapshot["overdue_accepted"]
        or not snapshot["healthy"]
    ):
        raise fastapi.HTTPException(
            status_code=503,
            detail={"status": "degraded", **snapshot},
        )
    return {"status": "healthy", **snapshot}


def _stream_id_timestamp_seconds(stream_id) -> float | None:
    if stream_id is None:
        return None
    raw = stream_id.decode("utf-8") if isinstance(stream_id, bytes) else str(stream_id)
    try:
        return int(raw.split("-", 1)[0]) / 1000.0
    except (TypeError, ValueError, OverflowError):
        return None


def _pending_idle_seconds(item) -> float | None:
    try:
        return max(0.0, float(item.get("time_since_delivered")) / 1000.0)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _queue_redis_snapshot(redis, *, now: float | None = None) -> dict:
    observed_at = time.time() if now is None else float(now)
    heartbeat_raw = redis.get(WORKER_HEARTBEAT_KEY)
    if isinstance(heartbeat_raw, bytes):
        heartbeat_raw = heartbeat_raw.decode("utf-8")
    heartbeat_updated_at = None
    if heartbeat_raw:
        try:
            heartbeat_updated_at = float(json.loads(heartbeat_raw)["updated_at"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            heartbeat_updated_at = None
    heartbeat_age_seconds = (
        max(0.0, observed_at - heartbeat_updated_at)
        if heartbeat_updated_at is not None
        else None
    )
    worker_heartbeat_fresh = (
        heartbeat_age_seconds is not None
        and heartbeat_age_seconds <= WORKER_HEARTBEAT_MAX_AGE_SECONDS
    )

    pending = redis.xpending(STREAM_KEY, INGEST_CONSUMER_GROUP)
    pending_entries = int(pending.get("pending", 0) or 0)
    oldest_pending_age_seconds = None
    pending_entries_fresh = pending_entries == 0
    if pending_entries:
        pending_range = getattr(redis, "xpending_range", None)
        details = []
        stale_details = []
        if pending_range is not None:
            details = pending_range(
                STREAM_KEY,
                INGEST_CONSUMER_GROUP,
                min="-",
                max="+",
                count=100,
            )
            stale_details = pending_range(
                STREAM_KEY,
                INGEST_CONSUMER_GROUP,
                min="-",
                max="+",
                count=1,
                idle=PENDING_ENTRY_MAX_AGE_SECONDS * 1000,
            )
        idle_ages = [
            age
            for age in (_pending_idle_seconds(item) for item in details)
            if age is not None
        ]
        if idle_ages:
            oldest_pending_age_seconds = max(idle_ages)
            pending_entries_fresh = not bool(stale_details)
            if stale_details:
                stale_age = _pending_idle_seconds(stale_details[0])
                if stale_age is not None:
                    oldest_pending_age_seconds = max(
                        oldest_pending_age_seconds,
                        stale_age,
                    )
        else:
            # Compatibility fallback for Redis clients without XPENDING RANGE.
            # Stream creation time is conservative; modern Redis clients use
            # delivery idle time above so reclaimed messages are not false alarms.
            oldest_timestamp = _stream_id_timestamp_seconds(pending.get("min"))
            oldest_pending_age_seconds = (
                max(0.0, observed_at - oldest_timestamp)
                if oldest_timestamp is not None
                else None
            )
            pending_entries_fresh = (
                oldest_pending_age_seconds is not None
                and oldest_pending_age_seconds <= PENDING_ENTRY_MAX_AGE_SECONDS
            )
    return {
        "heartbeat_age_seconds": heartbeat_age_seconds,
        "worker_heartbeat_fresh": worker_heartbeat_fresh,
        "pending_entries": pending_entries,
        "oldest_pending_age_seconds": oldest_pending_age_seconds,
        "pending_entries_fresh": pending_entries_fresh,
        "healthy": worker_heartbeat_fresh and pending_entries_fresh,
    }
