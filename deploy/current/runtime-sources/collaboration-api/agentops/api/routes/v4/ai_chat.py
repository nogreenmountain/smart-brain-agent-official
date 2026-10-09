from __future__ import annotations

import json
import hashlib
import logging
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.auth.middleware import AuthenticatedRoute
from agentops.common.orm import get_orm_session
from agentops.common import response_cache
from agentops import ingest_queue
from agentops.rag.audit import record_audit
from agentops.rag.authz import AuthzError, current_user_id, require_member
from agentops.workday.domain import business_day_utc_bounds
from agentops.workday.identity import derive_employee_identity
from agentops.ai_usage import chat_access
from employee_telemetry.bundle import (
    secret_from_environment,
    verify_telemetry_token,
)


class PrivateChatReadRoute(AuthenticatedRoute):
    def get_route_handler(self):
        handler=super().get_route_handler()
        if self.endpoint.__name__!='list_ai_chat_sessions':return handler
        async def private_handler(request):
            headers={'Cache-Control':'no-store','Pragma':'no-cache'}
            try:
                response=await handler(request)
            except chat_access.DailyAccessError as error:
                raise HTTPException(status_code=error.status_code,detail=error.detail,headers=headers) from error
            except HTTPException as error:
                error.headers={**(error.headers or {}),**headers};raise
            except RequestValidationError as error:
                return JSONResponse(status_code=422,content={'detail':jsonable_encoder(error.errors())},headers=headers)
            except Exception:
                logger.error('Private project conversation read failed')
                return JSONResponse(status_code=500,content={'detail':'Conversation request failed'},headers=headers)
            response.headers.update(headers);return response
        return private_handler


router = APIRouter(route_class=PrivateChatReadRoute)
device_router = APIRouter()
logger = logging.getLogger(__name__)

AIChatSource = Literal[
    "cc_switch",
    "chatgpt_web",
    "chatgpt_desktop",
    "openai_compliance",
    "smartbrain",
    "ai_gateway",
]
AIChatStatus = Literal["ok", "error", "partial"]
AIChatRole = Literal["user", "assistant", "system", "tool"]


def _sanitize_database_unsafe_unicode(value: Any) -> Any:
    if isinstance(value, str):
        return "".join(
            "\ufffd"
            if character == "\x00" or 0xD800 <= ord(character) <= 0xDFFF
            else character
            for character in value
        )
    if isinstance(value, dict):
        return {
            str(_sanitize_database_unsafe_unicode(str(key))):
                _sanitize_database_unsafe_unicode(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_database_unsafe_unicode(item) for item in value]
    return value


class _DatabaseSafeInput(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def sanitize_database_unsafe_unicode(cls, value: Any) -> Any:
        return _sanitize_database_unsafe_unicode(value)


class AIChatMessageInput(_DatabaseSafeInput):
    role: AIChatRole
    content: str = Field(..., min_length=1, max_length=1_000_000)
    message_id: str | None = Field(None, max_length=200)
    created_at: datetime | None = None
    token_count: int | None = Field(None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIChatIngestRequest(_DatabaseSafeInput):
    project_id: uuid.UUID
    source: AIChatSource
    conversation_id: str | None = Field(None, max_length=300)
    title: str | None = Field(None, max_length=500)
    task_id: str | None = Field(None, max_length=200)
    task_title: str | None = Field(None, max_length=500)
    model: str | None = Field(None, max_length=200)
    status: AIChatStatus = "ok"
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = Field(None, ge=0)
    prompt_tokens: int = Field(0, ge=0)
    completion_tokens: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)
    cost: float = Field(0, ge=0)
    error_count: int = Field(0, ge=0)
    trace_id: str | None = Field(None, max_length=200)
    messages: list[AIChatMessageInput] = Field(..., min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIChatIngestResponse(BaseModel):
    delivery_status: Literal["accepted", "synced"] = "synced"
    receipt_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None
    project_id: uuid.UUID
    employee_id: str
    employee_name: str
    source: AIChatSource
    message_count: int
    status: AIChatStatus


class AIChatMessage(BaseModel):
    role: AIChatRole
    content: str
    message_id: str | None = None
    created_at: datetime | None = None
    token_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIChatSession(BaseModel):
    id: uuid.UUID
    owner_user_id: uuid.UUID
    project_id: uuid.UUID
    employee_id: str
    employee_name: str
    source: AIChatSource
    conversation_id: str | None
    title: str | None
    task_id: str
    task_title: str | None
    model: str | None
    status: AIChatStatus
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    error_count: int
    trace_id: str | None
    message_count: int
    messages: list[AIChatMessage] | None = None
    created_at: datetime
    updated_at: datetime


class AIChatSessionListResponse(BaseModel):
    project_id: uuid.UUID
    owner_user_id: uuid.UUID | None = None
    employee_id: str | None
    date: date | None
    timezone: Literal["Asia/Shanghai"] = "Asia/Shanghai"
    sessions: list[AIChatSession]


def _sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return str(_sanitize_database_unsafe_unicode(value))


def _sanitize_json(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, dict):
        return {
            str(_sanitize_text(str(key))): _sanitize_json(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_json(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json(item) for item in value]
    return value


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(_sanitize_json(value or {}), default=str, ensure_ascii=False)


def _profile_for_user(orm: Session, user_id: uuid.UUID):
    return orm.execute(
        text("""
            SELECT au.email, pu.full_name
            FROM auth.users au
            LEFT JOIN public.users pu ON pu.id = au.id
            WHERE au.id = :uid
        """),
        {"uid": str(user_id)},
    ).first()


def _record_ai_chat_audit(
    orm: Session,
    request: Request,
    *,
    user_id: uuid.UUID,
    action: str,
    project_id: uuid.UUID,
    source: str | None,
    result_status: str,
    employee_id: str | None = None,
    session_id: uuid.UUID | None = None,
) -> None:
    metadata: dict[str, Any] = {
        "source": source,
        "result_status": result_status,
    }
    if employee_id:
        metadata["employee_id"] = employee_id
    if session_id:
        metadata["session_id"] = str(session_id)
    record_audit(
        orm,
        user_id=user_id,
        action=action,
        resource_type="project",
        resource_id=str(project_id),
        metadata=metadata,
        request=request,
    )


def _resolve_employee(orm: Session, user_id: uuid.UUID) -> tuple[str, str]:
    profile = _profile_for_user(orm, user_id)
    if profile is None or not profile.email:
        raise HTTPException(status_code=404, detail="user profile not found")
    return derive_employee_identity(
        user_id=user_id,
        email=profile.email,
        full_name=profile.full_name,
    )


def _total_tokens(body: AIChatIngestRequest) -> int:
    if body.total_tokens:
        return body.total_tokens
    return body.prompt_tokens + body.completion_tokens


def _chat_content_fingerprint(body: AIChatIngestRequest) -> str:
    canonical = body.model_dump(mode="json", exclude={"project_id"})
    encoded = json.dumps(
        _sanitize_json(canonical),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _queued_session_id(receipt_id: uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"agentops://ai-chat/ingest-receipts/{receipt_id}",
    )


def _refresh_leaderboard_days(orm: Session, usage_dates: list[date]) -> None:
    if not usage_dates:
        return
    orm.execute(
        text("SELECT public.refresh_ai_usage_leaderboard_daily(CAST(:dates AS date[]))"),
        {"dates": sorted(set(usage_dates))},
    )


def _invalidate_leaderboard_cache() -> None:
    try:
        response_cache.bump("leaderboard")
    except Exception:
        logger.exception("Failed to invalidate leaderboard cache after AI chat ingest")


def _capture_cc_input(orm, *, session_id, user_id, body, fingerprint, receipt_id=None):
    if body.source=='cc_switch' and os.getenv('SB_CC_INPUT_REVISIONS_ENABLED','false').lower()=='true':
        from agentops.ai_usage.cc_input_revisions import capture
        revision_id = capture(orm,session_id=session_id,owner_user_id=user_id,project_id=body.project_id,fingerprint=fingerprint)
        if receipt_id is not None:
            from agentops.cc_queue_contracts import record_completion
            record_completion(orm,receipt_id=receipt_id,revision_id=revision_id,fingerprint=fingerprint)


def _store_chat_session(
    orm: Session,
    *,
    user_id: uuid.UUID,
    employee_id: str,
    employee_name: str,
    body: AIChatIngestRequest,
    ingest_receipt_id: uuid.UUID | None = None,
    commit: bool = True,
) -> uuid.UUID:
    user_id = uuid.UUID(str(user_id))
    gateway_instance = body.metadata.get("gateway_instance_id") if body.source == "ai_gateway" else None
    if body.source == "ai_gateway" and (
        not isinstance(gateway_instance, str) or not gateway_instance.strip()
    ):
        raise ValueError("Gateway conversation requires an explicit instance")
    now = datetime.now(timezone.utc)
    started_at = body.started_at or now
    task_id = body.task_id or "unassigned"
    task_title = body.task_title or ("未标记任务" if task_id == "unassigned" else None)
    receipt_replay = body.conversation_id is None and ingest_receipt_id is not None
    session_id = (
        _queued_session_id(ingest_receipt_id)
        if receipt_replay
        else uuid.uuid4()
    )
    content_fingerprint = _chat_content_fingerprint(body)
    previous_usage_date: date | None = None
    if body.conversation_id:
        # Serialize the entire read/replace transaction, including the first
        # insert where SELECT FOR UPDATE has no existing row to lock.
        orm.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:identity, 0))"),
            {"identity": json.dumps(["chat-owner-v2", str(body.project_id), body.source,
                str(user_id), gateway_instance or "", body.conversation_id], separators=(",", ":"))},
        )
        existing = orm.execute(
            text("""
                SELECT id, content_fingerprint, started_at
                FROM public.ai_chat_sessions
                WHERE project_id = :project_id
                  AND source = :source
                  AND user_id = CAST(:user_id AS uuid)
                  AND identity_version = 2
                  AND COALESCE(gateway_instance_id, '') = :instance
                  AND external_conversation_id = :conversation_id
                FOR UPDATE
            """),
            {
                "project_id": str(body.project_id),
                "source": _sanitize_text(body.source),
                "user_id": str(user_id),
                "instance": gateway_instance or "",
                "conversation_id": _sanitize_text(body.conversation_id),
            },
        ).first()
        if existing is not None and existing.content_fingerprint == content_fingerprint:
            _capture_cc_input(orm,session_id=existing.id,user_id=user_id,body=body,fingerprint=content_fingerprint,receipt_id=ingest_receipt_id)
            if commit:
                orm.commit()
                _invalidate_leaderboard_cache()
            return uuid.UUID(str(existing.id))
        if existing is not None and existing.started_at is not None:
            previous_usage_date = existing.started_at.astimezone(
                timezone(timedelta(hours=8))
            ).date()
    elif receipt_replay:
        # The receipt row is the durable idempotency boundary for queued
        # conversation-less events. A transaction-scoped advisory lock closes
        # the rare overlap where an expired lease is reclaimed while the old
        # worker is still committing the same business event.
        orm.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"smartbrain:ai-chat-receipt:{ingest_receipt_id}"},
        )
        existing = orm.execute(
            text("""
                SELECT id, user_id, project_id, source, content_fingerprint, started_at
                FROM public.ai_chat_sessions
                WHERE id = :session_id
                FOR UPDATE
            """),
            {"session_id": str(session_id)},
        ).first()
        if existing is not None:
            if (str(existing.user_id) != str(user_id)
                or str(existing.project_id) != str(body.project_id) or existing.source != body.source):
                raise RuntimeError("queued AI chat receipt owner or scope changed during replay")
            if existing.content_fingerprint != content_fingerprint:
                raise RuntimeError("queued AI chat receipt payload changed during replay")
            _capture_cc_input(orm,session_id=existing.id,user_id=user_id,body=body,fingerprint=content_fingerprint,receipt_id=ingest_receipt_id)
            if commit:
                orm.commit()
                _invalidate_leaderboard_cache()
            return uuid.UUID(str(existing.id))
    params = {
        "id": str(session_id),
        "project_id": str(body.project_id),
        "user_id": str(user_id),
        "employee_id": _sanitize_text(employee_id),
        "employee_name": _sanitize_text(employee_name),
        "source": _sanitize_text(body.source),
        "conversation_id": _sanitize_text(body.conversation_id),
        "title": _sanitize_text(body.title),
        "task_id": _sanitize_text(task_id),
        "task_title": _sanitize_text(task_title),
        "model": _sanitize_text(body.model),
        "status": _sanitize_text(body.status),
        "started_at": started_at,
        "ended_at": body.ended_at,
        "duration_ms": body.duration_ms,
        "prompt_tokens": body.prompt_tokens,
        "completion_tokens": body.completion_tokens,
        "total_tokens": _total_tokens(body),
        "cost": body.cost,
        "error_count": body.error_count,
        "trace_id": _sanitize_text(body.trace_id),
        "metadata": _json_dumps(body.metadata),
        "content_fingerprint": content_fingerprint,
        "gateway_instance_id": gateway_instance,
        "gateway_event_id": body.metadata.get("gateway_event_id") if body.source == "ai_gateway" else None,
        "context_complete": body.source == "ai_gateway",
        "content_complete": body.source == "ai_gateway",
        "context_source": "gateway_headers" if body.source == "ai_gateway" else None,
    }
    stored = orm.execute(
        text("""
            INSERT INTO public.ai_chat_sessions (
                id, project_id, user_id, employee_id, employee_name,
                source, external_conversation_id, title, task_id, task_title,
                model, status, started_at, ended_at, duration_ms,
                prompt_tokens, completion_tokens, total_tokens, cost,
                error_count, trace_id, metadata, content_fingerprint,
                gateway_instance_id, gateway_event_id, context_complete,
                content_complete, context_source, identity_version
            )
            VALUES (
                :id, :project_id, :user_id, :employee_id, :employee_name,
                :source, :conversation_id, :title, :task_id, :task_title,
                :model, :status, :started_at, :ended_at, :duration_ms,
                :prompt_tokens, :completion_tokens, :total_tokens, :cost,
                :error_count, :trace_id, CAST(:metadata AS jsonb), :content_fingerprint,
                :gateway_instance_id, :gateway_event_id, :context_complete,
                :content_complete, :context_source, 2
            )
            ON CONFLICT (project_id, source, user_id, (COALESCE(gateway_instance_id, '')), external_conversation_id)
                WHERE external_conversation_id IS NOT NULL AND identity_version = 2
            DO UPDATE SET
                employee_id = EXCLUDED.employee_id,
                employee_name = EXCLUDED.employee_name,
                title = EXCLUDED.title,
                task_id = EXCLUDED.task_id,
                task_title = EXCLUDED.task_title,
                model = EXCLUDED.model,
                status = EXCLUDED.status,
                started_at = EXCLUDED.started_at,
                ended_at = EXCLUDED.ended_at,
                duration_ms = EXCLUDED.duration_ms,
                prompt_tokens = EXCLUDED.prompt_tokens,
                completion_tokens = EXCLUDED.completion_tokens,
                total_tokens = EXCLUDED.total_tokens,
                cost = EXCLUDED.cost,
                error_count = EXCLUDED.error_count,
                trace_id = EXCLUDED.trace_id,
                metadata = EXCLUDED.metadata,
                content_fingerprint = EXCLUDED.content_fingerprint,
                gateway_instance_id = EXCLUDED.gateway_instance_id,
                gateway_event_id = EXCLUDED.gateway_event_id,
                context_complete = EXCLUDED.context_complete,
                content_complete = EXCLUDED.content_complete,
                context_source = EXCLUDED.context_source,
                updated_at = now()
            RETURNING id
        """),
        params,
    ).first()
    stored_id = getattr(stored, "id", None)
    if stored_id is not None:
        session_id = uuid.UUID(str(stored_id))

    orm.execute(
        text("DELETE FROM public.ai_chat_messages WHERE session_id = :session_id"),
        {"session_id": str(session_id)},
    )
    for index, message in enumerate(body.messages):
        orm.execute(
            text("""
                INSERT INTO public.ai_chat_messages (
                    session_id, sequence_index, role, external_message_id,
                    content, token_count, message_created_at, metadata
                )
                VALUES (
                    :session_id, :sequence_index, :role, :message_id,
                    :content, :token_count, :message_created_at,
                    CAST(:metadata AS jsonb)
                )
            """),
            {
                "session_id": str(session_id),
                "sequence_index": index,
                "role": _sanitize_text(message.role),
                "message_id": _sanitize_text(message.message_id),
                "content": _sanitize_text(message.content),
                "token_count": message.token_count,
                "message_created_at": message.created_at,
                "metadata": _json_dumps(message.metadata),
            },
        )
    _capture_cc_input(orm,session_id=session_id,user_id=user_id,body=body,fingerprint=content_fingerprint,receipt_id=ingest_receipt_id)
    shanghai = timezone(timedelta(hours=8))
    refreshed_dates = [started_at.astimezone(shanghai).date()]
    if previous_usage_date is not None:
        refreshed_dates.append(previous_usage_date)
    _refresh_leaderboard_days(orm, refreshed_dates)
    if commit:
        orm.commit()
        _invalidate_leaderboard_cache()
    return session_id


def _mark_chatgpt_web_monitor_installed(
    orm: Session,
    *,
    user_id: uuid.UUID,
    employee_id: str,
    employee_name: str,
    body: AIChatIngestRequest,
) -> None:
    if body.source != "chatgpt_web":
        return
    seen_at = datetime.now(timezone.utc)
    components = {
        "chatgpt_web_extension": {
            "name": "chatgpt_web_extension",
            "status": "installed",
            "version": None,
            "last_seen_at": seen_at.isoformat(),
            "details": {"source": "ai_chat_ingest"},
        },
        "browser_shortcut": {
            "name": "browser_shortcut",
            "status": "installed",
            "version": None,
            "last_seen_at": seen_at.isoformat(),
            "details": {"source": "ai_chat_ingest"},
        },
    }
    row = orm.execute(
        text("""
            SELECT device_id
            FROM public.ai_monitor_devices
            WHERE project_id = :project_id
              AND employee_id = :employee_id
            ORDER BY last_seen_at DESC, updated_at DESC
            LIMIT 1
        """),
        {
            "project_id": str(body.project_id),
            "employee_id": employee_id,
        },
    ).first()
    if row:
        orm.execute(
            text("""
                UPDATE public.ai_monitor_devices
                SET user_id = :user_id,
                    employee_name = :employee_name,
                    components = components || CAST(:components AS jsonb),
                    last_seen_at = :last_seen_at,
                    updated_at = now()
                WHERE project_id = :project_id
                  AND employee_id = :employee_id
                  AND device_id = :device_id
            """),
            {
                "project_id": str(body.project_id),
                "user_id": str(user_id),
                "employee_id": employee_id,
                "employee_name": employee_name,
                "device_id": row.device_id,
                "components": _json_dumps(components),
                "last_seen_at": seen_at,
            },
        )
    else:
        orm.execute(
            text("""
                INSERT INTO public.ai_monitor_devices (
                    project_id, user_id, employee_id, employee_name,
                    device_id, device_name, installer_version, os,
                    components, last_seen_at
                )
                VALUES (
                    :project_id, :user_id, :employee_id, :employee_name,
                    :device_id, :device_name, NULL, NULL,
                    CAST(:components AS jsonb), :last_seen_at
                )
                ON CONFLICT (project_id, employee_id, device_id)
                DO UPDATE SET
                    user_id = excluded.user_id,
                    employee_name = excluded.employee_name,
                    components = public.ai_monitor_devices.components || excluded.components,
                    last_seen_at = excluded.last_seen_at,
                    updated_at = now()
            """),
            {
                "project_id": str(body.project_id),
                "user_id": str(user_id),
                "employee_id": employee_id,
                "employee_name": employee_name,
                "device_id": f"chatgpt-web-{employee_id}"[:200],
                "device_name": "ChatGPT Web AI Monitor",
                "components": _json_dumps(components),
                "last_seen_at": seen_at,
            },
        )
    orm.commit()


@router.post("/ai-chat/ingest", response_model=AIChatIngestResponse)
def ingest_ai_chat(
    request: Request,
    body: AIChatIngestRequest,
    orm: Session = Depends(get_orm_session),
) -> AIChatIngestResponse:
    if body.source == "cc_switch":
        raise HTTPException(status_code=410, detail="legacy_monitor_retired: CC Switch 自报采集已停用，请使用个人 API Key 的 Gateway。")
    try:
        user_id = current_user_id(request)
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    employee_id, employee_name = _resolve_employee(orm, user_id)
    try:
        session_id = _store_chat_session(
            orm,
            user_id=user_id,
            employee_id=employee_id,
            employee_name=employee_name,
            body=body,
        )
        _mark_chatgpt_web_monitor_installed(
            orm,
            user_id=user_id,
            employee_id=employee_id,
            employee_name=employee_name,
            body=body,
        )
    except Exception as error:
        logger.exception("AI chat ingest failed for project=%s", body.project_id)
        try:
            orm.rollback()
        except Exception:
            pass
        _record_ai_chat_audit(
            orm,
            request,
            user_id=user_id,
            action="ai_chat_ingest",
            project_id=body.project_id,
            source=body.source,
            result_status="service_error",
            employee_id=employee_id,
        )
        raise HTTPException(status_code=503, detail="ai chat ingest unavailable") from error

    _record_ai_chat_audit(
        orm,
        request,
        user_id=user_id,
        action="ai_chat_ingest",
        project_id=body.project_id,
        source=body.source,
        result_status="ok",
        employee_id=employee_id,
        session_id=session_id,
    )
    return AIChatIngestResponse(
        session_id=session_id,
        project_id=body.project_id,
        employee_id=employee_id,
        employee_name=employee_name,
        source=body.source,
        message_count=len(body.messages),
        status=body.status,
    )


def _device_claims(request: Request) -> dict[str, Any]:
    request_state = getattr(request, "state", None)
    worker_claims = getattr(request_state, "ingest_worker_claims", None)
    if worker_claims is not None:
        return dict(worker_claims)
    authorization = str(request.headers.get("authorization") or "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="device credential is required")
    try:
        claims = verify_telemetry_token(
            token.strip(),
            secret=secret_from_environment(),
        )
        uuid.UUID(str(claims.get("sub") or ""))
        uuid.UUID(str(claims.get("project_id") or ""))
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=401, detail="device credential is invalid or expired") from error
    return claims


def _require_cc_ingest_authorization(orm, *, user_id, project_id):
    """Reauthorize signed admission/queued work and hold permission rows until commit."""
    row=orm.execute(text('''SELECT u.id FROM public.project_members m
        JOIN public.users u ON u.id=m.user_id
        JOIN auth.users a ON a.id=u.id
        JOIN public.projects p ON p.id=m.project_id
        WHERE m.user_id=CAST(:owner AS uuid) AND m.project_id=CAST(:project AS uuid)
          AND u.is_active IS TRUE
        FOR SHARE OF m,u,a,p'''),{'owner':str(user_id),'project':str(project_id)}).first()
    if row is None:
        raise HTTPException(status_code=403,detail='An active project member is required for CC input')


@device_router.post("/ai-chat/device-ingest", response_model=AIChatIngestResponse)
def device_ingest_ai_chat(
    request: Request,
    body: AIChatIngestRequest,
    orm: Session = Depends(get_orm_session),
) -> AIChatIngestResponse:
    raise HTTPException(status_code=410, detail="legacy_monitor_retired: 旧 Monitor 采集已停用，请使用个人 API Key 的 Gateway。")
    claims = _device_claims(request)
    if body.source != "cc_switch":
        raise HTTPException(status_code=422, detail="device ingest source must be cc_switch")
    if str(body.project_id) != str(claims["project_id"]):
        raise HTTPException(status_code=403, detail="project is outside the device credential scope")
    user_id = uuid.UUID(str(claims["sub"]))

    employee_id = str(claims["employee_id"])
    employee_name = str(claims["employee_name"])
    request_state = getattr(request, "state", None)
    transaction_owned = bool(getattr(request_state, 'process_ingest_now', False)
        and getattr(request_state, 'ingest_business_transaction', False))
    from agentops import cc_queue_contracts
    try:
        processing_contract = cc_queue_contracts.intake_protocol(orm)
    except Exception as error:
        orm.rollback()
        raise HTTPException(status_code=503, detail='CC intake unavailable') from error
    if transaction_owned and os.getenv('SB_CC_INPUT_REVISIONS_ENABLED','false').lower() != 'true':
        raise HTTPException(status_code=503, detail='CC queued consumption disabled')
    if os.getenv('SB_CC_INPUT_REVISIONS_ENABLED','false').lower() == 'true':
        _require_cc_ingest_authorization(orm,user_id=user_id,project_id=body.project_id)
    if ingest_queue.enabled() and not getattr(request_state, "process_ingest_now", False):
        try:
            if cc_queue_contracts.enabled() and processing_contract is None:
                raise RuntimeError('CC queue contract migration required')
            receipt = ingest_queue.enqueue(
                orm,
                stream="ai-chat",
                payload=body.model_dump(mode="json"),
                claims=claims,
                processing_contract=processing_contract,
            )
        except Exception as error:
            orm.rollback()
            raise HTTPException(status_code=503,detail='CC queued intake unavailable') from error
        return AIChatIngestResponse(
            delivery_status="synced" if receipt.status == "synced" else "accepted",
            receipt_id=receipt.id,
            session_id=None,
            project_id=body.project_id,
            employee_id=employee_id,
            employee_name=employee_name,
            source=body.source,
            message_count=len(body.messages),
            status=body.status,
        )
    try:
        ingest_receipt_id = getattr(request_state, "ingest_receipt_id", None)
        session_id = _store_chat_session(
            orm,
            user_id=user_id,
            employee_id=employee_id,
            employee_name=employee_name,
            body=body,
            commit=not transaction_owned,
            ingest_receipt_id=(
                uuid.UUID(str(ingest_receipt_id))
                if ingest_receipt_id is not None
                else None
            ),
        )
    except Exception as error:
        if transaction_owned:
            logger.error("CC queued ingest failed; project=%s", body.project_id)
        else:
            logger.exception("Device AI chat ingest failed for project=%s", body.project_id)
        try:
            orm.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=503, detail="device AI chat ingest unavailable") from error

    if not transaction_owned:
        _record_ai_chat_audit(
            orm,
            request,
            user_id=user_id,
            action="ai_chat_ingest",
            project_id=body.project_id,
            source=body.source,
            result_status="ok",
            employee_id=employee_id,
            session_id=session_id,
        )
    return AIChatIngestResponse(
        session_id=session_id,
        project_id=body.project_id,
        employee_id=employee_id,
        employee_name=employee_name,
        source=body.source,
        message_count=len(body.messages),
        status=body.status,
    )


def _row_to_session(row) -> AIChatSession:
    raw_messages = row.messages
    messages = None
    if raw_messages is not None:
        messages = [AIChatMessage.model_validate(item) for item in raw_messages]
    return AIChatSession(
        id=row.id,
        owner_user_id=row.user_id,
        project_id=row.project_id,
        employee_id=row.employee_id,
        employee_name=row.employee_name,
        source=row.source,
        conversation_id=row.external_conversation_id,
        title=row.title,
        task_id=row.task_id,
        task_title=row.task_title,
        model=row.model,
        status=row.status,
        started_at=row.started_at,
        ended_at=row.ended_at,
        duration_ms=row.duration_ms,
        prompt_tokens=row.prompt_tokens,
        completion_tokens=row.completion_tokens,
        total_tokens=row.total_tokens,
        cost=float(row.cost or 0),
        error_count=row.error_count,
        trace_id=row.trace_id,
        message_count=row.message_count,
        messages=messages,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get(
    "/ai-chat/sessions/{project_id}",
    response_model=AIChatSessionListResponse,
)
def list_ai_chat_sessions(
    request: Request,
    project_id: uuid.UUID,
    employee_id: str | None = Query(None, min_length=1, max_length=200),
    work_date: date | None = Query(None, alias="date"),
    source: AIChatSource | None = Query(None),
    include_messages: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    orm: Session = Depends(get_orm_session),
) -> AIChatSessionListResponse:
    try:
        user_id = current_user_id(request)
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    try:
        project_role = require_member(
            orm,
            user_id=user_id,
            project_id=project_id,
        )
    except AuthzError as error:
        _record_ai_chat_audit(
            orm,
            request,
            user_id=user_id,
            action="ai_chat_list",
            project_id=project_id,
            source=source,
            result_status="forbidden",
            employee_id=employee_id,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    selected=chat_access.resolve_project_selection(orm,caller_user_id=user_id,project_id=project_id,
        requested_owner=employee_id)
    effective_employee_id=selected.employee_id if selected else None
    conditions = ["s.project_id = :project_id", "s.identity_version = 2", f'''EXISTS (
        SELECT 1 FROM {chat_access.FROM_SQL} WHERE viewer.id=CAST(:caller AS uuid)
          AND owner_profile.id=s.user_id AND project.id=s.project_id AND {chat_access.READABLE_SQL})''']
    params: dict[str, Any] = {"project_id": str(project_id), "caller":str(user_id), "limit": limit}
    if selected:
        conditions.append("s.user_id = CAST(:owner AS uuid)")
        params["owner"] = selected.user_id
    if source:
        conditions.append("s.source = :source")
        params["source"] = source
    if work_date:
        start_utc, end_utc = business_day_utc_bounds(work_date)
        conditions.append("s.started_at >= :start_utc AND s.started_at < :end_utc")
        params["start_utc"] = start_utc
        params["end_utc"] = end_utc

    messages_sql = "NULL::jsonb AS messages"
    if include_messages:
        messages_sql = """
            (
                SELECT COALESCE(
                    jsonb_agg(
                        jsonb_build_object(
                            'role', m.role,
                            'content', m.content,
                            'message_id', m.external_message_id,
                            'created_at', m.message_created_at,
                            'token_count', m.token_count,
                            'metadata', m.metadata
                        )
                        ORDER BY m.sequence_index
                    ),
                    '[]'::jsonb
                )
                FROM public.ai_chat_messages m
                WHERE m.session_id = s.id
            ) AS messages
        """

    rows = orm.execute(
        text(f"""
            SELECT
                s.id,
                s.user_id,
                s.project_id,
                s.employee_id,
                s.employee_name,
                s.source,
                s.external_conversation_id,
                s.title,
                s.task_id,
                s.task_title,
                s.model,
                s.status,
                s.started_at,
                s.ended_at,
                s.duration_ms,
                s.prompt_tokens,
                s.completion_tokens,
                s.total_tokens,
                s.cost,
                s.error_count,
                s.trace_id,
                (
                    SELECT count(*)::int
                    FROM public.ai_chat_messages m
                    WHERE m.session_id = s.id
                ) AS message_count,
                {messages_sql},
                s.created_at,
                s.updated_at
            FROM public.ai_chat_sessions s
            WHERE {" AND ".join(conditions)}
            ORDER BY s.started_at DESC, s.created_at DESC
            LIMIT :limit
        """),
        params,
    ).all()
    _record_ai_chat_audit(
        orm,
        request,
        user_id=user_id,
        action="ai_chat_list",
        project_id=project_id,
        source=source,
        result_status="ok",
        employee_id=effective_employee_id,
    )
    return AIChatSessionListResponse(
        project_id=project_id,
        owner_user_id=selected.user_id if selected else None,
        employee_id=effective_employee_id,
        date=work_date,
        sessions=[_row_to_session(row) for row in rows],
    )
