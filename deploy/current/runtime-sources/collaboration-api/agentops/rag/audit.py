"""
Audit logging for sensitive actions.

Design notes:
  - We log METADATA only, never the query text or document content.
  - We tolerate failures: audit logging never fails a user request.
  - We capture ip_address from request.client.host when available.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any, Optional

from fastapi import BackgroundTasks, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.common import cache
from agentops.common.orm import get_orm_session

logger = logging.getLogger(__name__)


def _client_ip(request: Optional[Request]) -> Optional[str]:
    if request is None or request.client is None:
        return None
    return request.client.host


def record_audit(
    orm: Session,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Insert one audit row. Never raises — failures are logged but do not
    propagate to the caller, so a broken audit table cannot break the API.
    """
    try:
        orm.execute(
            text("""
                INSERT INTO public.audit_logs
                    (user_id, action, resource_type, resource_id, metadata, ip_address)
                VALUES (:uid, :act, :rtype, :rid, CAST(:meta AS jsonb), :ip)
            """),
            {
                "uid": str(user_id) if user_id else None,
                "act": action,
                "rtype": resource_type,
                "rid": str(resource_id) if resource_id else None,
                "meta": _json_dumps(metadata or {}),
                "ip": ip_address if ip_address is not None else _client_ip(request),
            },
        )
        orm.commit()
    except Exception as e:
        logger.warning("audit insert failed (action=%s): %s", action, e)
        try:
            orm.rollback()
        except Exception:
            pass


def _record_audit_in_new_session(
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    metadata: dict[str, Any],
    ip_address: Optional[str],
) -> None:
    """Write a non-blocking read audit with a session owned by the task."""
    session_generator = None
    try:
        session_generator = get_orm_session()
        orm = next(session_generator)
        record_audit(
            orm,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            ip_address=ip_address,
        )
    except Exception as error:
        logger.warning("background audit failed (action=%s): %s", action, error)
    finally:
        if session_generator is not None:
            try:
                session_generator.close()
            except Exception:
                pass


def schedule_deduplicated_audit(
    background_tasks: BackgroundTasks,
    *,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
    dedup_ttl_seconds: int = 60,
) -> bool:
    """Queue a best-effort audit and suppress identical read noise briefly."""
    audit_metadata = dict(metadata or {})
    client_ip = _client_ip(request)
    fingerprint_payload = {
        "user_id": str(user_id) if user_id else None,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "metadata": audit_metadata,
        "ip_address": client_ip,
    }
    fingerprint = hashlib.sha256(
        _json_dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    dedup_key = f"audit-dedup:{fingerprint}"

    try:
        if not cache.set_if_absent(dedup_key, dedup_ttl_seconds, "1"):
            return False
    except Exception as error:
        logger.warning("audit deduplication unavailable (action=%s): %s", action, error)

    try:
        background_tasks.add_task(
            _record_audit_in_new_session,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=audit_metadata,
            ip_address=client_ip,
        )
    except Exception as error:
        logger.warning("audit scheduling failed (action=%s): %s", action, error)
        try:
            cache.delete(dedup_key)
        except Exception:
            pass
        return False
    return True


def _json_dumps(d: dict, *, sort_keys: bool = False) -> str:
    import json
    return json.dumps(d, default=str, ensure_ascii=False, sort_keys=sort_keys)
