from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.ai_usage.gateway import generate_api_key, hash_api_key, mask_api_key, normalize_usage
from agentops.auth.middleware import AuthenticatedRoute
from agentops.common.orm import get_orm_session
from agentops.common import response_cache
from agentops.rag.authz import AuthzError, current_user_id
from agentops.workday.identity import derive_employee_identity
from .ai_chat import AIChatIngestRequest, AIChatMessageInput, _store_chat_session

router = APIRouter(prefix="/ai-gateway", tags=["ai-gateway"], route_class=AuthenticatedRoute)
device_router = APIRouter(prefix="/ai-gateway", tags=["ai-gateway"])


class GatewayKeyResponse(BaseModel):
    id: uuid.UUID
    key: str | None = None
    masked_key: str
    label: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None


class GatewayConversationMessage(BaseModel):
    role: str = Field(..., min_length=1, max_length=20)
    content: str = Field(..., min_length=1, max_length=1_000_000)
    message_id: str | None = Field(None, max_length=200)
    created_at: datetime | None = None
    token_count: int | None = Field(None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GatewayEvent(BaseModel):
    gateway_instance_id: str = Field(default_factory=lambda: os.getenv("SB_GATEWAY_INSTANCE_ID", "gateway-local"), min_length=1, max_length=120)
    event_id: str = Field(..., min_length=8, max_length=200)
    request_id: str | None = Field(None, max_length=200)
    key_id: uuid.UUID | None = None
    model: str = Field("", max_length=200)
    request_model: str = Field("", max_length=200)
    requested_model: str = Field("", max_length=200)
    resolved_model: str = Field("", max_length=200)
    upstream_model: str = Field("", max_length=200)
    provider: str = Field("", max_length=120)
    app_type: str = Field("codex", max_length=40)
    status_code: int = Field(200, ge=100, le=599)
    usage: dict[str, Any] = Field(default_factory=dict)
    raw_usage: dict[str, Any] = Field(default_factory=dict)
    usage_missing: bool | None = None
    token_semantics_version: int = Field(1, ge=0)
    latency_ms: int = Field(0, ge=0, le=86_400_000)
    total_cost_usd: float = Field(0, ge=0)
    error_message: str | None = Field(None, max_length=2000)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    project_id: uuid.UUID | None = None
    conversation_id: str | None = Field(None, max_length=300)
    title: str | None = Field(None, max_length=500)
    task_id: str | None = Field(None, max_length=200)
    task_title: str | None = Field(None, max_length=500)
    trace_id: str | None = Field(None, max_length=200)
    context_complete: bool = False
    messages: list[GatewayConversationMessage] = Field(default_factory=list, max_length=500)
    content_complete: bool = False


class GatewayEventBatch(BaseModel):
    events: list[GatewayEvent] = Field(..., min_length=1, max_length=500)


def _session_user(request: Request) -> uuid.UUID:
    try:
        return current_user_id(request)
    except AuthzError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def _profile(orm: Session, user_id: uuid.UUID):
    row = orm.execute(text("""
        SELECT au.email, pu.full_name
        FROM auth.users au LEFT JOIN public.users pu ON pu.id = au.id
        WHERE au.id = :uid AND COALESCE(pu.is_active, true)
    """), {"uid": str(user_id)}).first()
    if not row or not row.email:
        raise HTTPException(status_code=404, detail="user profile not found")
    return row


@router.post("/keys", response_model=GatewayKeyResponse)
def create_gateway_key(request: Request, orm: Session = Depends(get_orm_session)) -> GatewayKeyResponse:
    user_id = _session_user(request)
    _profile(orm, user_id)
    existing = orm.execute(text("""
        SELECT id, key_prefix, label, is_active, created_at, last_used_at
        FROM public.ai_gateway_keys WHERE user_id=:uid AND is_active ORDER BY created_at DESC LIMIT 1
    """), {"uid": str(user_id)}).first()
    if existing:
        return GatewayKeyResponse(id=existing.id, masked_key=f"{existing.key_prefix}…", label=existing.label,
                                  is_active=existing.is_active, created_at=existing.created_at, last_used_at=existing.last_used_at)
    raw = generate_api_key()
    row = orm.execute(text("""
        INSERT INTO public.ai_gateway_keys (user_id, key_hash, key_prefix)
        VALUES (:uid, :hash, :prefix)
        RETURNING id, label, is_active, created_at, last_used_at
    """), {"uid": str(user_id), "hash": hash_api_key(raw), "prefix": raw[:12]}).first()
    orm.commit()
    return GatewayKeyResponse(id=row.id, key=raw, masked_key=mask_api_key(raw), label=row.label,
                              is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)


@router.get("/keys", response_model=list[GatewayKeyResponse])
def list_gateway_keys(request: Request, orm: Session = Depends(get_orm_session)) -> list[GatewayKeyResponse]:
    user_id = _session_user(request)
    rows = orm.execute(text("""
        SELECT id, key_prefix, label, is_active, created_at, last_used_at
        FROM public.ai_gateway_keys WHERE user_id = :uid ORDER BY created_at DESC
    """), {"uid": str(user_id)}).all()
    if not rows:
        # First authenticated visit provisions the employee's initial key.
        raw = generate_api_key()
        row = orm.execute(text("""
            INSERT INTO public.ai_gateway_keys (user_id, key_hash, key_prefix)
            VALUES (:uid, :hash, :prefix)
            RETURNING id, label, is_active, created_at, last_used_at
        """), {"uid": str(user_id), "hash": hash_api_key(raw), "prefix": raw[:12]}).first()
        orm.commit()
        return [GatewayKeyResponse(id=row.id, key=raw, masked_key=mask_api_key(raw), label=row.label,
                                   is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)]
    return [GatewayKeyResponse(id=r.id, masked_key=f"{r.key_prefix}…", label=r.label,
                               is_active=r.is_active, created_at=r.created_at, last_used_at=r.last_used_at) for r in rows]


@router.post("/keys/{key_id}/rotate", response_model=GatewayKeyResponse)
def rotate_gateway_key(key_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)) -> GatewayKeyResponse:
    user_id = _session_user(request)
    raw = generate_api_key()
    row = orm.execute(text("""
        UPDATE public.ai_gateway_keys
        SET key_hash=:hash, key_prefix=:prefix, is_active=true, revoked_at=NULL
        WHERE id=:id AND user_id=:uid
        RETURNING id, label, is_active, created_at, last_used_at
    """), {"id": str(key_id), "uid": str(user_id), "hash": hash_api_key(raw), "prefix": raw[:12]}).first()
    if not row:
        raise HTTPException(status_code=404, detail="gateway key not found")
    orm.commit()
    return GatewayKeyResponse(id=row.id, key=raw, masked_key=mask_api_key(raw), label=row.label,
                              is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)


@router.post("/keys/{key_id}/revoke", response_model=GatewayKeyResponse)
def revoke_gateway_key(key_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)) -> GatewayKeyResponse:
    user_id = _session_user(request)
    row = orm.execute(text("""
        UPDATE public.ai_gateway_keys SET is_active=false, revoked_at=now()
        WHERE id=:id AND user_id=:uid
        RETURNING id, key_prefix, label, is_active, created_at, last_used_at
    """), {"id": str(key_id), "uid": str(user_id)}).first()
    if not row:
        raise HTTPException(status_code=404, detail="gateway key not found")
    orm.commit()
    return GatewayKeyResponse(id=row.id, masked_key=f"{row.key_prefix}…", label=row.label,
                              is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)


def _gateway_claims(request: Request, orm: Session):
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Gateway API key required")
    raw = header.split(" ", 1)[1].strip()
    row = orm.execute(text("""
        SELECT k.id, k.user_id, au.email, pu.full_name
        FROM public.ai_gateway_keys k
        JOIN auth.users au ON au.id = k.user_id
        LEFT JOIN public.users pu ON pu.id = k.user_id
        WHERE k.key_hash=:hash AND k.is_active AND COALESCE(pu.is_active, true)
    """), {"hash": hash_api_key(raw)}).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or revoked Gateway API key")
    return row


def _materialize_gateway_conversation(
    orm: Session,
    *,
    claim: Any,
    employee_id: str,
    employee_name: str,
    event: GatewayEvent,
    usage: dict[str, int],
) -> uuid.UUID:
    if not event.project_id or not event.conversation_id or not event.messages:
        raise ValueError("complete Gateway conversation context is required")
    chat_body = AIChatIngestRequest(
        project_id=event.project_id,
        source="ai_gateway",
        conversation_id=event.conversation_id,
        title=event.title or "AI Gateway 会话",
        task_id=event.task_id,
        task_title=event.task_title,
        model=event.resolved_model or event.model or event.requested_model,
        status="ok" if 200 <= event.status_code < 400 else "error",
        started_at=event.started_at,
        ended_at=event.completed_at,
        duration_ms=event.latency_ms,
        prompt_tokens=usage["input_tokens"],
        completion_tokens=usage["output_tokens"],
        total_tokens=usage["total_tokens"],
        error_count=0 if 200 <= event.status_code < 400 else 1,
        trace_id=event.trace_id,
        messages=[AIChatMessageInput(**message.model_dump()) for message in event.messages],
        metadata={"gateway_instance_id": event.gateway_instance_id, "gateway_event_id": event.event_id},
    )
    return _store_chat_session(
        orm,
        user_id=claim.user_id,
        employee_id=employee_id,
        employee_name=employee_name,
        body=chat_body,
    )


@device_router.post("/events", status_code=202)
def ingest_gateway_events(request: Request, body: GatewayEventBatch, orm: Session = Depends(get_orm_session)):
    claim = _gateway_claims(request, orm)
    employee_id, employee_name = derive_employee_identity(user_id=claim.user_id, email=claim.email, full_name=claim.full_name)
    accepted = 0
    dates: set[date] = set()
    for event in body.events:
        if not event.trace_id:
            event.trace_id = uuid.uuid4().hex
        event.context_complete = bool(event.project_id and event.conversation_id)
        usage = normalize_usage(event.usage, request_model=event.request_model, app_type=event.app_type)
        usage_date = ((event.completed_at or event.started_at or datetime.now(timezone.utc)).astimezone(timezone(timedelta(hours=8))).date())
        row = orm.execute(text("""
                INSERT INTO public.ai_gateway_events (
                  gateway_instance_id,event_id,request_id,key_id,user_id,employee_id,employee_name,model,request_model,
                  requested_model,resolved_model,upstream_model,provider,app_type,
                  conversation_id,context_complete,
                  status_code,input_tokens,output_tokens,cache_read_tokens,cache_creation_tokens,
                  cached_input_tokens,cache_write_tokens,reasoning_tokens,input_token_semantics,token_semantics_version,
                  total_tokens,usage_missing,raw_usage,total_cost_usd,latency_ms,error_message,usage_date,started_at,completed_at)
                VALUES (:gateway_instance_id,:event_id,:request_id,:key_id,:uid,:eid,:ename,:model,:request_model,
                  :requested_model,:resolved_model,:upstream_model,:provider,:app,:conversation_id,:context_complete,:status,
                  :input,:output,:cache_read,:cache_creation,:cached_input,:cache_write,:reasoning,:semantics,:semantics_version,
                  :total,:usage_missing,CAST(:raw_usage AS jsonb),:cost,:latency,:error,:usage_date,
                  COALESCE(:started_at, now()),:completed_at)
                ON CONFLICT DO NOTHING RETURNING id
            """), {"gateway_instance_id": event.gateway_instance_id, "event_id": event.event_id, "request_id": event.request_id,
                    # Never trust a client-supplied identity; bind the key id
                    # from the authenticated hash lookup above.
                    "key_id": str(claim.id), "uid": str(claim.user_id),
                    "eid": employee_id, "ename": employee_name, "model": event.model, "request_model": event.request_model,
                    "requested_model": event.requested_model or event.request_model or event.model,
                    "resolved_model": event.resolved_model or event.model,
                    "upstream_model": event.upstream_model or event.resolved_model or event.model,
                    "provider": event.provider,
                    "app": event.app_type, "conversation_id": event.conversation_id,
                    "context_complete": event.context_complete, "status": event.status_code, "input": usage["input_tokens"],
                    "output": usage["output_tokens"], "cache_read": usage["cache_read_tokens"],
                    "cache_creation": usage["cache_creation_tokens"], "cached_input": usage["cache_read_tokens"],
                    "cache_write": usage["cache_creation_tokens"], "reasoning": int(event.usage.get("reasoning_tokens", 0) or 0),
                    "semantics": usage["input_token_semantics"], "semantics_version": event.token_semantics_version,
                    "total": usage["total_tokens"], "usage_missing": event.usage_missing if event.usage_missing is not None else not bool(event.usage),
                    "raw_usage": json.dumps(event.raw_usage or event.usage, ensure_ascii=False),
                    "cost": event.total_cost_usd, "latency": event.latency_ms,
                    "error": event.error_message, "usage_date": usage_date, "started_at": event.started_at,
                    "completed_at": event.completed_at}).first()
        if row:
            accepted += 1
            dates.add(usage_date)
            if event.content_complete and event.project_id and event.conversation_id and event.messages:
                try:
                    from agentops.rag.authz import require_member
                    require_member(orm, user_id=claim.user_id, project_id=event.project_id)
                except AuthzError as exc:
                    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
                session_id = _materialize_gateway_conversation(
                    orm, claim=claim, employee_id=employee_id, employee_name=employee_name,
                    event=event, usage=usage,
                )
                orm.execute(text("UPDATE public.ai_gateway_events SET chat_session_id=:session_id, conversation_id=:conversation_id, context_complete=true, content_complete=true, content_sync_status='synced' WHERE id=:id"), {"session_id": str(session_id), "conversation_id": event.conversation_id, "id": str(row.id)})
    orm.execute(text("UPDATE public.ai_gateway_keys SET last_used_at=now() WHERE id=:id"), {"id": str(claim.id)})
    orm.commit()
    if dates:
        orm.execute(text("SELECT public.refresh_ai_usage_leaderboard_daily(CAST(:dates AS date[]))"), {"dates": sorted(dates)})
        orm.execute(text("SELECT public.refresh_ai_gateway_leaderboard_daily(CAST(:dates AS date[]))"), {"dates": sorted(dates)})
        orm.commit()
        try:
            response_cache.bump("leaderboard")
        except Exception:
            pass
    return {"accepted": accepted, "duplicates": len(body.events) - accepted}


@device_router.get("/authorize")
def authorize_gateway_key(request: Request, orm: Session = Depends(get_orm_session)):
    claim = _gateway_claims(request, orm)
    return {"authorized": True, "user_id": str(claim.user_id), "key_id": str(claim.id)}
