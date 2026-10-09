from __future__ import annotations

import json
import logging
import os
import socket
import time
import uuid
from datetime import timedelta
from typing import Callable

from fastapi import Request
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError as RedisResponseError
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import text

from agentops.api.routes.v4.ai_chat import AIChatIngestRequest, device_ingest_ai_chat
from agentops.api.routes.v4.ai_usage import (
    CCSwitchUsageSyncRequest,
    device_ingest_cc_switch_usage,
)
from agentops.common import cache
from agentops.common.orm import get_orm_session
from agentops.ingest_queue import (
    DEAD_LETTER_STREAM_KEY,
    INGEST_CONSUMER_GROUP,
    STREAM_KEY,
    WORKER_HEARTBEAT_KEY,
    WORKER_HEARTBEAT_TTL_SECONDS,
)


logger = logging.getLogger(__name__)
GROUP = INGEST_CONSUMER_GROUP
CONSUMER = f"{socket.gethostname()}-{os.getpid()}"
MAX_ATTEMPTS = int(os.getenv("INGEST_QUEUE_MAX_ATTEMPTS", "5"))
LEASE_SECONDS = max(int(os.getenv("INGEST_QUEUE_LEASE_SECONDS", "900")), 30)
MESSAGE_IDLE_SECONDS = max(
    int(os.getenv("INGEST_QUEUE_MESSAGE_IDLE_SECONDS", "60")),
    5,
)
DEAD_LETTER_STREAM_MAXLEN = max(
    int(os.getenv("INGEST_QUEUE_DEAD_LETTER_MAXLEN", "10000")),
    100,
)
IDLE_STREAM_BLOCK_MILLISECONDS = max(
    int(os.getenv("INGEST_QUEUE_IDLE_BLOCK_MILLISECONDS", "5000")),
    1,
)
REDIS_SOCKET_TIMEOUT_SAFETY_SECONDS = 1.0
HEARTBEAT_INTERVAL_SECONDS = max(
    int(os.getenv("INGEST_QUEUE_HEARTBEAT_INTERVAL_SECONDS", "15")),
    5,
)


def _record_heartbeat(redis, *, now: float | None = None) -> bool:
    """Publish a short-lived liveness marker without stopping durable PG polling."""
    updated_at = time.time() if now is None else float(now)
    try:
        redis.set(
            WORKER_HEARTBEAT_KEY,
            json.dumps(
                {
                    "consumer": CONSUMER,
                    "updated_at": updated_at,
                },
                sort_keys=True,
            ),
            ex=WORKER_HEARTBEAT_TTL_SECONDS,
        )
        return True
    except Exception:
        logger.exception("Unable to publish ingest worker heartbeat")
        return False


def _record_heartbeat_if_due(
    redis,
    *,
    monotonic_now: float,
    next_heartbeat_at: float,
    wall_now: float | None = None,
) -> float:
    if monotonic_now < next_heartbeat_at:
        return next_heartbeat_at
    _record_heartbeat(redis, now=wall_now)
    return monotonic_now + HEARTBEAT_INTERVAL_SECONDS


def _idle_stream_block_milliseconds(redis) -> int:
    """Keep a blocking Stream read below the Redis client's socket timeout."""
    connection_pool = getattr(redis, "connection_pool", None)
    connection_kwargs = getattr(connection_pool, "connection_kwargs", {})
    socket_timeout = connection_kwargs.get("socket_timeout")
    if socket_timeout is None:
        return IDLE_STREAM_BLOCK_MILLISECONDS
    safe_timeout_milliseconds = max(
        int(
            (float(socket_timeout) - REDIS_SOCKET_TIMEOUT_SAFETY_SECONDS)
            * 1000
        ),
        1,
    )
    return min(IDLE_STREAM_BLOCK_MILLISECONDS, safe_timeout_milliseconds)


def _request(claims: dict, *, receipt_id: str) -> Request:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/internal/ingest-worker",
            "headers": [],
            "client": ("127.0.0.1", 0),
        }
    )
    request.state.ingest_worker_claims = claims
    request.state.process_ingest_now = True
    request.state.ingest_receipt_id = uuid.UUID(str(receipt_id))
    return request


def _process_receipt(receipt_id: str) -> str:
    session_generator = get_orm_session()
    orm = next(session_generator)
    attempt_count = 0
    claim_token = uuid.uuid4()
    try:
        row = orm.execute(
            text("""
                UPDATE public.ingest_queue_receipts
                SET status = 'processing',
                    attempt_count = attempt_count + 1,
                    next_attempt_at = now() + :lease_duration,
                    claim_token = :claim_token,
                    updated_at = now()
                WHERE id = :id
                  AND status IN ('accepted', 'processing')
                  AND next_attempt_at <= now()
                RETURNING id, stream, payload, claims, status, attempt_count
            """),
            {
                "id": receipt_id,
                "lease_duration": timedelta(seconds=LEASE_SECONDS),
                "claim_token": str(claim_token),
            },
        ).first()
        if row is None:
            orm.commit()
            return "complete"
        attempt_count = int(row.attempt_count)
        # Persist both the attempt counter and a recovery lease before invoking
        # business code. Those handlers may commit or roll back this session.
        orm.commit()
        payload = row.payload if isinstance(row.payload, dict) else json.loads(row.payload)
        claims = row.claims if isinstance(row.claims, dict) else json.loads(row.claims)
        if row.stream == "ai-chat":
            device_ingest_ai_chat(
                request=_request(claims, receipt_id=receipt_id),
                body=AIChatIngestRequest.model_validate(payload),
                orm=orm,
            )
        elif row.stream == "cc-switch-usage":
            device_ingest_cc_switch_usage(
                request=_request(claims, receipt_id=receipt_id),
                body=CCSwitchUsageSyncRequest.model_validate(payload),
                orm=orm,
            )
        else:
            raise ValueError(f"unsupported ingest stream: {row.stream}")
        result = orm.execute(
            text("""
                UPDATE public.ingest_queue_receipts
                SET status = 'synced', synced_at = now(), last_error = NULL,
                    payload = '{}'::jsonb, claims = '{}'::jsonb,
                    claim_token = NULL,
                    updated_at = now()
                WHERE id = :id
                  AND status = 'processing'
                  AND claim_token = :claim_token
                RETURNING id
            """),
            {"id": receipt_id, "claim_token": str(claim_token)},
        ).first()
        orm.commit()
        if result is None:
            logger.warning("Ingest receipt completion lost its claim: %s", receipt_id)
            return "stale"
        return "complete"
    except Exception as error:
        orm.rollback()
        if attempt_count <= 0:
            persisted_attempt = orm.execute(
                text("SELECT attempt_count FROM public.ingest_queue_receipts WHERE id = :id"),
                {"id": receipt_id},
            ).scalar_one_or_none()
            attempt_count = int(persisted_attempt or 0)
        dead = attempt_count >= MAX_ATTEMPTS
        updated = orm.execute(
            text("""
                UPDATE public.ingest_queue_receipts
                SET status = :status, last_error = :error,
                    next_attempt_at = now() + :retry_delay,
                    claim_token = NULL,
                    updated_at = now()
                WHERE id = :id
                  AND status = 'processing'
                  AND claim_token = :claim_token
                RETURNING id
            """),
            {
                "id": receipt_id,
                "status": "dead_letter" if dead else "accepted",
                "error": str(error)[:4000],
                "retry_delay": timedelta(seconds=min(300, 2 ** min(max(attempt_count, 1), 8))),
                "claim_token": str(claim_token),
            },
        ).first()
        orm.commit()
        if updated is None:
            logger.warning("Ingest receipt failure lost its claim: %s", receipt_id)
            return "stale"
        logger.exception("Ingest receipt failed: %s", receipt_id)
        return "dead_letter" if dead else "retry"
    finally:
        try:
            next(session_generator)
        except StopIteration:
            pass


def _pending_receipts() -> list[str]:
    session_generator = get_orm_session()
    orm = next(session_generator)
    try:
        rows = orm.execute(
            text("""
                SELECT id
                FROM public.ingest_queue_receipts
                WHERE status IN ('accepted', 'processing') AND next_attempt_at <= now()
                ORDER BY accepted_at
                LIMIT 20
            """)
        ).all()
        return [str(row.id) for row in rows]
    finally:
        try:
            next(session_generator)
        except StopIteration:
            pass


def _cleanup_receipts() -> None:
    session_generator = get_orm_session()
    orm = next(session_generator)
    try:
        orm.execute(
            text("""
                DELETE FROM public.ingest_queue_receipts
                WHERE status = 'synced' AND synced_at < now() - interval '7 days'
            """)
        )
        orm.commit()
    finally:
        try:
            next(session_generator)
        except StopIteration:
            pass


def _autoclaim_messages(redis) -> list[tuple[str, str]]:
    result = redis.xautoclaim(
        STREAM_KEY,
        GROUP,
        CONSUMER,
        min_idle_time=MESSAGE_IDLE_SECONDS * 1000,
        start_id="0-0",
        count=20,
    )
    entries = result[1] if len(result) > 1 else []
    return [
        (str(message_id), str(fields["receipt_id"]))
        for message_id, fields in entries
    ]


def _run_cycle(
    redis,
    idle_stream_block_milliseconds: int,
    *,
    heartbeat_callback: Callable[[], None] | None = None,
) -> bool:
    delivered: list[tuple[str, str]] = []
    try:
        delivered.extend(_autoclaim_messages(redis))
    except (RedisConnectionError, RedisTimeoutError):
        logger.exception(
            "Redis XAUTOCLAIM failed; continuing with fresh messages and durable receipt polling"
        )
    except RedisResponseError as error:
        if "NOGROUP" not in str(error):
            raise
        logger.warning(
            "Redis consumer group is missing during XAUTOCLAIM; recreating it"
        )
        _ensure_consumer_group(redis)

    try:
        messages = redis.xreadgroup(
            GROUP,
            CONSUMER,
            {STREAM_KEY: ">"},
            count=20,
            block=1 if delivered else idle_stream_block_milliseconds,
        )
        for _, entries in messages:
            for message_id, fields in entries:
                delivered.append((message_id, str(fields["receipt_id"])))
    except (RedisConnectionError, RedisTimeoutError):
        logger.exception(
            "Redis XREADGROUP failed; continuing with durable receipt polling"
        )
    except RedisResponseError as error:
        if "NOGROUP" not in str(error):
            raise
        logger.warning(
            "Redis consumer group is missing during XREADGROUP; recreating it"
        )
        _ensure_consumer_group(redis)

    delivered_receipt_ids = {receipt_id for _, receipt_id in delivered}
    delivered.extend(
        ("", receipt_id)
        for receipt_id in _pending_receipts()
        if receipt_id not in delivered_receipt_ids
    )
    for message_id, receipt_id in delivered:
        if heartbeat_callback is not None:
            heartbeat_callback()
        status = _process_receipt(receipt_id)
        if heartbeat_callback is not None:
            heartbeat_callback()
        if status == "dead_letter":
            try:
                redis.xadd(
                    DEAD_LETTER_STREAM_KEY,
                    {"receipt_id": receipt_id},
                    maxlen=DEAD_LETTER_STREAM_MAXLEN,
                    approximate=True,
                )
            except (RedisConnectionError, RedisTimeoutError):
                logger.exception(
                    "Unable to publish ingest dead letter for receipt=%s",
                    receipt_id,
                )
        if message_id and status in {"complete", "dead_letter", "retry", "stale"}:
            try:
                redis.xack(STREAM_KEY, GROUP, message_id)
            except (RedisConnectionError, RedisTimeoutError):
                # Leave the message in the PEL. A later XAUTOCLAIM pass will
                # observe the durable PostgreSQL outcome and retry only XACK.
                logger.exception(
                    "Redis XACK failed; leaving message pending for recovery: %s",
                    message_id,
                )
            except RedisResponseError as error:
                if "NOGROUP" not in str(error):
                    raise
                logger.warning(
                    "Redis consumer group disappeared before XACK; recreating it"
                )
                _ensure_consumer_group(redis)
    return bool(delivered)


def _ensure_consumer_group(redis) -> None:
    while True:
        try:
            redis.xgroup_create(STREAM_KEY, GROUP, id="0", mkstream=True)
            return
        except (RedisConnectionError, RedisTimeoutError):
            logger.exception(
                "Redis consumer-group creation timed out; retrying without exiting"
            )
            time.sleep(1)
        except RedisResponseError as error:
            if "BUSYGROUP" in str(error):
                return
            raise


def main() -> None:
    redis = cache.raw_backend()
    idle_stream_block_milliseconds = _idle_stream_block_milliseconds(redis)
    _ensure_consumer_group(redis)
    next_cleanup_at = 0.0
    next_heartbeat_at = 0.0
    while True:
        monotonic_now = time.monotonic()
        next_heartbeat_at = _record_heartbeat_if_due(
            redis,
            monotonic_now=monotonic_now,
            next_heartbeat_at=next_heartbeat_at,
        )
        if monotonic_now >= next_cleanup_at:
            _cleanup_receipts()
            next_cleanup_at = monotonic_now + 3600

        def refresh_heartbeat() -> None:
            nonlocal next_heartbeat_at
            next_heartbeat_at = _record_heartbeat_if_due(
                redis,
                monotonic_now=time.monotonic(),
                next_heartbeat_at=next_heartbeat_at,
            )

        if not _run_cycle(
            redis,
            idle_stream_block_milliseconds,
            heartbeat_callback=refresh_heartbeat,
        ):
            time.sleep(1)


if __name__ == "__main__":
    main()
