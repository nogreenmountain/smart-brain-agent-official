from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.common import cache
from agentops.common.environment import CACHE_NAMESPACE


logger = logging.getLogger(__name__)
STREAM_KEY = f"{CACHE_NAMESPACE}:ingest:events"
DEAD_LETTER_STREAM_KEY = f"{CACHE_NAMESPACE}:ingest:dead-letter"
INGEST_CONSUMER_GROUP = os.getenv("INGEST_QUEUE_CONSUMER_GROUP", "ingest-workers")
WORKER_HEARTBEAT_KEY = f"{CACHE_NAMESPACE}:ingest:worker-heartbeat"
WORKER_HEARTBEAT_TTL_SECONDS = max(
    int(os.getenv("INGEST_QUEUE_HEARTBEAT_TTL_SECONDS", "180")),
    60,
)
WORKER_HEARTBEAT_MAX_AGE_SECONDS = max(
    int(os.getenv("INGEST_QUEUE_HEARTBEAT_MAX_AGE_SECONDS", "120")),
    30,
)
PENDING_ENTRY_MAX_AGE_SECONDS = max(
    int(os.getenv("INGEST_QUEUE_PENDING_MAX_AGE_SECONDS", "300")),
    60,
)
HEARTBEAT_BUCKET_SECONDS = max(
    int(os.getenv("INGEST_QUEUE_HEARTBEAT_BUCKET_SECONDS", "600")),
    60,
)


@dataclass(frozen=True)
class IngestReceipt:
    id: uuid.UUID
    status: str
    synced_at: datetime | None


def enabled() -> bool:
    return os.getenv("INGEST_QUEUE_ENABLED", "false").lower() in {"1", "true", "yes"}


def _sanitize_text(value: str) -> str:
    return "".join(
        "\ufffd"
        if character == "\x00" or 0xD800 <= ord(character) <= 0xDFFF
        else character
        for character in value
    )


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, dict):
        return {
            _sanitize_text(str(key)): _sanitize_json(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_json(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(
        _sanitize_json(value),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _heartbeat_bucket(value: Any) -> int | str:
    try:
        attempted_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if attempted_at.tzinfo is None:
            attempted_at = attempted_at.replace(tzinfo=timezone.utc)
        return int(attempted_at.timestamp()) // HEARTBEAT_BUCKET_SECONDS
    except (TypeError, ValueError, OverflowError):
        # Preserve the unparseable value so malformed transports cannot all
        # collapse onto one immortal receipt fingerprint.
        return str(value)


def _fingerprint_payload(stream: str, payload: dict[str, Any]) -> Any:
    stable = dict(payload)
    attempted_at = stable.pop("attempted_at", None)
    trigger = str(stable.get("trigger") or "automatic")
    request_id = stable.get("request_id")
    if trigger == "manual" and request_id:
        return {
            "trigger": "manual",
            "request_id": str(request_id),
            "device_id": str(stable.get("device_id") or ""),
        }
    stable.pop("request_id", None)
    if trigger != "manual":
        stable.pop("trigger", None)
    if stream == "cc-switch-usage" and trigger == "automatic":
        stable["heartbeat_bucket"] = _heartbeat_bucket(attempted_at)
    return stable


def _payload_fingerprint(
    stream: str,
    payload: dict[str, Any],
    claims: dict[str, Any],
) -> str:
    identity = {
        key: str(claims.get(key) or "")
        for key in ("sub", "project_id", "employee_id")
    }
    material = {
        "stream": stream,
        "identity": identity,
        "payload": _fingerprint_payload(stream, payload),
    }
    return hashlib.sha256(_canonical(material).encode("utf-8")).hexdigest()


def enqueue(
    orm: Session,
    *,
    stream: str,
    payload: dict[str, Any],
    claims: dict[str, Any],
    processing_contract: str | None = None,
) -> IngestReceipt:
    payload_json = _canonical(payload)
    fingerprint = _payload_fingerprint(stream, payload, claims)
    if processing_contract is not None:
        from agentops import cc_queue_contracts
        if processing_contract != cc_queue_contracts.PROTOCOL or not cc_queue_contracts.enabled():
            raise RuntimeError('CC queued intake disabled or unsupported')
        try:
            row = orm.execute(text('''INSERT INTO public.ingest_queue_receipts
                (id,stream,payload_fingerprint,payload,claims,status)
                VALUES (:id,:stream,:fingerprint,CAST(:payload AS jsonb),CAST(:claims AS jsonb),'accepted')
                ON CONFLICT (stream,payload_fingerprint) DO NOTHING
                RETURNING id,status,synced_at'''), {'id':str(uuid.uuid4()), 'stream':stream,
                    'fingerprint':fingerprint, 'payload':payload_json, 'claims':_canonical(claims)}).first()
            if row is not None:
                cc_queue_contracts.register(orm,row.id)
            else:
                row = orm.execute(text('''SELECT id,status,synced_at FROM public.ingest_queue_receipts
                    WHERE stream=:stream AND payload_fingerprint=:fingerprint'''),
                    {'stream':stream,'fingerprint':fingerprint}).one()
                cc_queue_contracts.verify_replay(orm,row.id,payload_json=payload_json,claims=claims)
            orm.commit()
        except Exception:
            orm.rollback()
            raise
        receipt = IngestReceipt(id=uuid.UUID(str(row.id)),status=str(row.status),synced_at=row.synced_at)
        if receipt.status != 'synced':
            try:
                cache.raw_backend().xadd(STREAM_KEY,{'receipt_id':str(receipt.id)},maxlen=100_000,approximate=True)
            except Exception:
                logger.error('CC queued wake-up unavailable; durable receipt=%s',receipt.id)
        return receipt
    existing = orm.execute(
        text("""
            SELECT id, status, synced_at
            FROM public.ingest_queue_receipts
            WHERE stream = :stream AND payload_fingerprint = :payload_fingerprint
              AND status <> 'dead_letter'
        """),
        {"stream": stream, "payload_fingerprint": fingerprint},
    ).first()
    if existing is not None:
        receipt = IngestReceipt(
            id=uuid.UUID(str(existing.id)),
            status=str(existing.status),
            synced_at=existing.synced_at,
        )
        if receipt.status != "synced":
            try:
                cache.raw_backend().xadd(
                    STREAM_KEY,
                    {"receipt_id": str(receipt.id)},
                    maxlen=100_000,
                    approximate=True,
                )
            except Exception:
                logger.exception(
                    "Unable to republish ingest wake-up for receipt=%s", receipt.id
                )
        return receipt

    receipt_id = uuid.uuid4()
    row = orm.execute(
        text("""
            INSERT INTO public.ingest_queue_receipts (
                id, stream, payload_fingerprint, payload, claims, status
            ) VALUES (
                :id, :stream, :payload_fingerprint,
                CAST(:payload AS jsonb), CAST(:claims AS jsonb), 'accepted'
            )
            ON CONFLICT (stream, payload_fingerprint)
            DO UPDATE SET
                payload = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN excluded.payload
                    ELSE public.ingest_queue_receipts.payload
                END,
                claims = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN excluded.claims
                    ELSE public.ingest_queue_receipts.claims
                END,
                status = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN 'accepted'
                    ELSE public.ingest_queue_receipts.status
                END,
                attempt_count = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN 0
                    ELSE public.ingest_queue_receipts.attempt_count
                END,
                accepted_at = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN now()
                    ELSE public.ingest_queue_receipts.accepted_at
                END,
                synced_at = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN NULL
                    ELSE public.ingest_queue_receipts.synced_at
                END,
                last_error = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN NULL
                    ELSE public.ingest_queue_receipts.last_error
                END,
                claim_token = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN NULL
                    ELSE public.ingest_queue_receipts.claim_token
                END,
                next_attempt_at = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN now()
                    ELSE public.ingest_queue_receipts.next_attempt_at
                END,
                updated_at = CASE
                    WHEN public.ingest_queue_receipts.status = 'dead_letter'
                    THEN now()
                    ELSE public.ingest_queue_receipts.updated_at
                END
            WHERE public.ingest_queue_receipts.status = 'dead_letter'
            RETURNING id, status, synced_at
        """),
        {
            "id": str(receipt_id),
            "stream": stream,
            "payload_fingerprint": fingerprint,
            "payload": payload_json,
            "claims": _canonical(claims),
        },
    ).first()
    if row is None:
        row = orm.execute(
            text("""
                SELECT id, status, synced_at
                FROM public.ingest_queue_receipts
                WHERE stream = :stream AND payload_fingerprint = :payload_fingerprint
                  AND status <> 'dead_letter'
            """),
            {"stream": stream, "payload_fingerprint": fingerprint},
        ).first()
        if row is None:
            raise RuntimeError("ingest receipt conflict did not resolve to a durable row")
    else:
        orm.commit()
    receipt = IngestReceipt(
        id=uuid.UUID(str(row.id)),
        status=str(row.status),
        synced_at=row.synced_at,
    )
    if receipt.status != "synced":
        try:
            cache.raw_backend().xadd(
                STREAM_KEY,
                {"receipt_id": str(receipt.id)},
                maxlen=100_000,
                approximate=True,
            )
        except Exception:
            # The PostgreSQL receipt is the durable source. The worker also polls
            # pending receipts, so a Redis wake-up failure cannot lose ingestion.
            logger.exception("Unable to publish ingest wake-up for receipt=%s", receipt.id)
    return receipt
