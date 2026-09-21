from __future__ import annotations

import json
import logging
import hmac
import os
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.ai_usage import gateway_content, gateway_tokens
from agentops.ai_usage.gateway import generate_api_key, hash_api_key, mask_api_key, normalize_usage
from agentops.auth.middleware import AuthenticatedRoute
from agentops.common.orm import get_orm_session
from agentops.common import response_cache
from agentops.rag.authz import AuthzError, current_user_id
from agentops.workday.identity import derive_employee_identity
from .ai_chat import AIChatIngestRequest, AIChatMessageInput, _store_chat_session

def _key_response_headers(response: Response) -> None:
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'


def _private_gateway_handler(handler):
    async def private_handler(request):
        headers = {'Cache-Control': 'no-store', 'Pragma': 'no-cache'}
        try:
            response = await handler(request)
        except HTTPException as error:
            error.headers = {**(error.headers or {}), **headers}
            raise
        except RequestValidationError as error:
            return JSONResponse(status_code=422, content={'detail': jsonable_encoder(error.errors())}, headers=headers)
        except Exception as error:
            logging.getLogger(__name__).error('Private Gateway request failed (%s)', type(error).__name__)
            return JSONResponse(status_code=500, content={'detail': 'Private Gateway request unavailable'}, headers=headers)
        response.headers.update(headers)
        return response
    return private_handler


class PrivateGatewayRoute(AuthenticatedRoute):
    def get_route_handler(self):
        return _private_gateway_handler(super().get_route_handler())


class PrivateGatewayDeviceRoute(APIRoute):
    # Service/receipt authentication stays in the endpoint; this route does not
    # add browser-session authentication to server-to-server delivery.
    def get_route_handler(self):
        return _private_gateway_handler(super().get_route_handler())


router = APIRouter(prefix="/ai-gateway", tags=["ai-gateway"], route_class=PrivateGatewayRoute,
                   dependencies=[Depends(_key_response_headers)])
device_router = APIRouter(prefix="/ai-gateway", tags=["ai-gateway"],route_class=PrivateGatewayDeviceRoute)


class GatewayKeyResponse(BaseModel):
    id: uuid.UUID
    key: str | None = None
    masked_key: str
    label: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
    max_active_keys: int = 1


class GatewayKeyCreate(BaseModel):
    label: str = Field('SmartBrain Gateway', min_length=1, max_length=100)

    @field_validator('label')
    @classmethod
    def validate_label(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError('Key name must not be blank or contain control characters')
        return value


class GatewayKeyRename(GatewayKeyCreate):
    label: str = Field(..., min_length=1, max_length=100)


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
    request_message_count: int | None = Field(None, ge=0, le=500, strict=True)
    context_source: Literal['client_conversation','independent_request'] | None = None

    @model_validator(mode='after')
    def validate_message_provenance(self):
        if (self.request_message_count is None) != (self.context_source is None):
            raise ValueError('Message boundary and context source must be recorded together')
        if self.request_message_count is not None:
            # Gateways may enforce their own bounded journal and therefore
            # capture fewer messages than the original request boundary.
            # Preserve the event instead of rejecting the whole delivery;
            # the boundary is clamped to the captured prefix.
            if self.request_message_count > len(self.messages):
                self.request_message_count = len(self.messages)
            if self.content_complete and self.request_message_count == len(self.messages):
                raise ValueError('Complete response must include captured response messages')
        return self


class GatewayEventBatch(BaseModel):
    events: list[GatewayEvent] = Field(..., min_length=1, max_length=500)


def _session_user(request: Request) -> uuid.UUID:
    try:
        return current_user_id(request)
    except AuthzError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


# Apply the same live predicate before list pagination, cursor resolution and
# body reads. Missing/invalid project provenance is preserved but not disclosed.
# Compare project text rather than casting an untrusted JSON field to UUID.
_HISTORY_READABLE_SQL = """
    EXISTS (SELECT 1 FROM public.users viewer JOIN auth.users au ON au.id=viewer.id
            WHERE viewer.id=a.user_id AND viewer.is_active IS TRUE)
    AND jsonb_typeof(a.event_payload)='object'
    AND a.event_payload ? 'project_id'
    AND (a.event_payload->'project_id'='null'::jsonb OR EXISTS (
        SELECT 1 FROM public.projects p JOIN public.project_members pm ON pm.project_id=p.id
        WHERE p.id::text=a.event_payload->>'project_id' AND pm.user_id=a.user_id
    ))
"""


@router.get('/history')
def personal_gateway_history(request: Request, limit: int = Query(25, ge=1, le=50),
                             before: uuid.UUID | None = None,
                             orm: Session = Depends(get_orm_session)):
    """Read only the caller's delivered, immutable request snapshots.

    The admission is the content source and the event is the token source.
    This deliberately does not rewrite the legacy project chat projection.
    """
    owner = _session_user(request)
    params = {'owner': str(owner), 'limit': limit + 1}
    cursor_condition = ''
    if before is not None:
        anchor = orm.execute(text(f'''
            SELECT a.admitted_at FROM public.ai_gateway_admissions a
            WHERE a.id = :before AND a.user_id = :owner AND a.delivered_at IS NOT NULL
              AND {_HISTORY_READABLE_SQL}
        '''), {'before': str(before), 'owner': str(owner)}).first()
        if anchor is None:
            raise HTTPException(status_code=404, detail='History cursor not found')
        params.update(before=str(before), before_time=anchor.admitted_at)
        cursor_condition = 'AND (a.admitted_at, a.id) < (:before_time, :before)'
    rows = orm.execute(text(f'''
        SELECT a.id, a.gateway_instance_id, a.admitted_at,
               {gateway_content.METADATA_SQL} AS event_payload,
               jsonb_array_length(a.event_payload->'messages') AS message_count,
               e.input_tokens, e.output_tokens, e.total_tokens, e.usage_missing, e.status_code,
               e.cache_read_tokens,e.cache_creation_tokens,e.reasoning_tokens,e.input_token_semantics,
               {gateway_tokens.REPORTED_SQL} AS reported_tokens
        FROM public.ai_gateway_admissions a
        JOIN public.ai_gateway_events e
          ON e.event_id = a.id::text AND e.gateway_instance_id = a.gateway_instance_id
         AND e.user_id = a.user_id
        WHERE a.user_id = :owner AND a.delivered_at IS NOT NULL
          AND {_HISTORY_READABLE_SQL}
          {cursor_condition}
        ORDER BY a.admitted_at DESC, a.id DESC
        LIMIT :limit
    '''), params).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = []
    for row in rows:
        payload = row.event_payload
        if isinstance(payload, str):
            payload = json.loads(payload)
        conversation = payload.get('conversation_id')
        project = payload.get('project_id')
        identity = [str(owner), row.gateway_instance_id, project,
                    'conversation' if conversation else 'request', conversation or str(row.id)]
        group_id = uuid.uuid5(uuid.NAMESPACE_URL, 'smartbrain:gateway-history:v1:' +
                             json.dumps(identity, ensure_ascii=True, separators=(',', ':')))
        items.append({
            'request_id': str(row.id), 'conversation_group_id': str(group_id),
            'conversation_id': conversation, 'project_id': project,
            'gateway_instance_id': row.gateway_instance_id, 'admitted_at': row.admitted_at,
            'title': payload.get('title'),
            'model': payload.get('resolved_model') or payload.get('model') or payload.get('requested_model'),
            'content_complete': payload.get('content_complete') is True and 200 <= row.status_code < 400,
            'context_source': payload.get('context_source') or 'legacy_unknown',
            'request_message_count': payload.get('request_message_count'),
            'message_count': row.message_count or 0, 'status_code': row.status_code,
            'input_tokens': None if row.usage_missing else row.input_tokens,
            'output_tokens': None if row.usage_missing else row.output_tokens,
            'total_tokens': None if row.usage_missing else row.total_tokens, 'usage_missing': bool(row.usage_missing),
            **gateway_tokens.from_ledger(row),
        })
    return {'items': items, 'next_cursor': str(rows[-1].id) if has_more else None}


@router.get('/history/{request_id}')
def personal_gateway_history_detail(request: Request, request_id: uuid.UUID,
                                    orm: Session = Depends(get_orm_session)):
    owner = _session_user(request)
    row = orm.execute(text(f'''
        SELECT {gateway_content.METADATA_SQL} || jsonb_build_object(
            'messages',CASE WHEN {gateway_content.MESSAGE_BYTES_SQL} <= {gateway_content.INLINE_MESSAGE_BYTES}
                THEN a.event_payload->'messages' ELSE NULL END,
            'messages_truncated',{gateway_content.MESSAGE_BYTES_SQL} > {gateway_content.INLINE_MESSAGE_BYTES}) AS event_payload,
            e.status_code
        FROM public.ai_gateway_admissions a
        JOIN public.ai_gateway_events e
          ON e.event_id = a.id::text AND e.gateway_instance_id = a.gateway_instance_id
         AND e.user_id = a.user_id
        WHERE a.id = :request_id AND a.user_id = :owner AND a.delivered_at IS NOT NULL
          AND {_HISTORY_READABLE_SQL}
    '''), {'request_id': str(request_id), 'owner': str(owner)}).first()
    if row is None:
        raise HTTPException(status_code=404, detail='History request not found')
    payload = row.event_payload
    if isinstance(payload, str):
        payload = json.loads(payload)
    return {
        'request_id': str(request_id), 'messages': payload.get('messages'),
        'messages_truncated': payload.get('messages_truncated') is True,
        'status_code': row.status_code,
        'context_source': payload.get('context_source') or 'legacy_unknown',
        'request_message_count': payload.get('request_message_count'),
        'content_complete': payload.get('content_complete') is True and 200 <= row.status_code < 400,
    }


def _profile(orm: Session, user_id: uuid.UUID):
    row = orm.execute(text("""
        SELECT au.email, pu.full_name
        FROM auth.users au LEFT JOIN public.users pu ON pu.id = au.id
        WHERE au.id = :uid AND COALESCE(pu.is_active, true)
    """), {"uid": str(user_id)}).first()
    if not row or not row.email:
        raise HTTPException(status_code=404, detail="user profile not found")
    return row


def _llm_service(orm):
    if os.getenv('SB_LLM_GATEWAY_MANAGEMENT_ENABLED') != '1':
        return None
    from agentops.ai_usage.llm_key_runtime import build_service
    return _llm_call(build_service, orm=orm)


def _llm_contract(request):
    if request.headers.get('x-smartbrain-gateway-contract') != '2':
        raise HTTPException(409, '请更新客户端后再创建或管理新网关密钥')
    try:
        return str(uuid.UUID(request.headers.get('idempotency-key', '')))
    except ValueError:
        raise HTTPException(422, '需要有效的 Idempotency-Key') from None


def _llm_call(method, **kwargs):
    try:
        return method(**kwargs)
    except Exception as error:
        raise HTTPException(getattr(error, 'status_code', 503),
                            getattr(error, 'code', 'gateway_management_unavailable')) from None


def _llm_created_response(service, user_id, result):
    if result.get('key'):
        keys = _llm_call(service.list_keys, user_id=str(user_id))
        key = next((k for k in keys if k['id'] == result['credential_id']), None)
        if key is not None:
            return JSONResponse(status_code=201, content={**key, 'key': result['key'], 'operation_id': result['operation_id']})
    summary = {k:v for k,v in result.items() if k != 'key'}
    if summary.get('status') == 'confirmed':
        summary['error_code'] = 'secret_not_delivered'
    return JSONResponse(status_code=202, content={'kind': 'operation', **summary})


def _llm_change(orm, request, user_id, key_id, action):
    service = _llm_service(orm)
    if service is None:
        return None
    try:
        if not _llm_call(service.owns_credential, user_id=str(user_id), credential_id=str(key_id)):
            return None
        if action not in ('revoke', 'remove'):
            raise HTTPException(409, 'gateway_change_not_supported')
        idem = _llm_contract(request)
        result = _llm_call(getattr(service, action), user_id=str(user_id), credential_id=str(key_id), idempotency_key=idem)
        if result['status'] == 'confirmed':
            if action == 'remove':
                return Response(status_code=204)
            keys = _llm_call(service.list_keys, user_id=str(user_id))
            key = next((k for k in keys if k['id'] == str(key_id)), None)
            if key is not None:
                return JSONResponse(content=key)
        return JSONResponse(status_code=202, content={'kind': 'operation', **result})
    finally:
        service.close()


@router.post("/keys", response_model=GatewayKeyResponse)
def create_gateway_key(request: Request, body: GatewayKeyCreate | None = None,
                       orm: Session = Depends(get_orm_session)) -> GatewayKeyResponse:
    user_id = _session_user(request)
    _profile(orm, user_id)
    service = _llm_service(orm)
    if service is not None:
        try:
            if _llm_call(service.creation_enabled, user_id=str(user_id)):
                idem = _llm_contract(request)
                result = _llm_call(service.create, user_id=str(user_id), idempotency_key=idem,
                                   label=(body or GatewayKeyCreate()).label)
                return _llm_created_response(service, user_id, result)
        finally:
            service.close()
    # Serialize count+insert on the member row, including an empty key list.
    locked_user = orm.execute(text("""
        SELECT id FROM public.users
        WHERE id=:uid AND COALESCE(is_active, true) FOR UPDATE
    """), {"uid": str(user_id)}).first()
    if not locked_user:
        raise HTTPException(status_code=404, detail="user profile not found")
    count = orm.execute(text("""
        SELECT COUNT(*) AS active_count FROM public.ai_gateway_keys
        WHERE user_id=:uid AND is_active
    """), {"uid": str(user_id)}).first()
    if os.getenv('SB_LLM_GATEWAY_MANAGEMENT_ENABLED') == '1':
        from agentops.ai_usage.llm_key_quota import key_count_sql
        count = orm.execute(text('SELECT ' + key_count_sql(':uid') + ' AS active_count'), {'uid': str(user_id)}).first()
    allowance = orm.execute(text('''
        SELECT max_active_keys FROM public.ai_gateway_key_allowances WHERE user_id=:uid
    '''), {'uid': str(user_id)}).first()
    limit = int(allowance.max_active_keys) if allowance else 1
    if count.active_count >= limit:
        raise HTTPException(status_code=409, detail="默认只能有一个 API Key；新增请提交原因，等待 hanshangbo 审批")
    raw = generate_api_key()
    row = orm.execute(text("""
        INSERT INTO public.ai_gateway_keys (user_id, key_hash, key_prefix, label)
        VALUES (:uid, :hash, :prefix, :label)
        RETURNING id, label, is_active, created_at, last_used_at
    """), {"uid": str(user_id), "hash": hash_api_key(raw), "prefix": raw[:12],
           "label": (body or GatewayKeyCreate()).label}).first()
    orm.commit()
    return GatewayKeyResponse(id=row.id, key=raw, masked_key=mask_api_key(raw), label=row.label,
                              is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)


@router.get("/keys", response_model=list[GatewayKeyResponse])
def list_gateway_keys(request: Request, orm: Session = Depends(get_orm_session)) -> list[GatewayKeyResponse]:
    user_id = _session_user(request)
    rows = orm.execute(text("""
        SELECT id, key_prefix, label, is_active, created_at, last_used_at,
               COALESCE((SELECT max_active_keys FROM public.ai_gateway_key_allowances WHERE user_id=:uid), 1) AS max_active_keys
        FROM public.ai_gateway_keys WHERE user_id = :uid AND hidden_at IS NULL ORDER BY created_at DESC
    """), {"uid": str(user_id)}).all()
    result = [GatewayKeyResponse(id=r.id, masked_key=f"{r.key_prefix}…", label=r.label,
                               is_active=r.is_active, created_at=r.created_at, last_used_at=r.last_used_at,
                               max_active_keys=int(r.max_active_keys)) for r in rows]
    service = _llm_service(orm)
    if service is not None:
        try:
            added = _llm_call(service.list_keys, user_id=str(user_id))
            return JSONResponse(content=jsonable_encoder(result) + added)
        finally:
            service.close()
    return result


@router.get('/operations/{operation_id}')
def get_gateway_operation(operation_id: uuid.UUID, request: Request,
                          orm: Session = Depends(get_orm_session)):
    user_id = _session_user(request)
    service = _llm_service(orm)
    if service is None:
        raise HTTPException(404, 'operation_not_found')
    try:
        return _llm_call(service.get_operation, user_id=str(user_id), operation_id=str(operation_id))
    finally:
        service.close()


@router.get('/operations')
def list_gateway_operations(request: Request, orm: Session = Depends(get_orm_session)):
    user_id = _session_user(request)
    service = _llm_service(orm)
    if service is None:
        return []
    try:
        return _llm_call(service.list_operations, user_id=str(user_id))
    finally:
        service.close()


@router.patch("/keys/{key_id}", response_model=GatewayKeyResponse)
def rename_gateway_key(key_id: uuid.UUID, body: GatewayKeyRename, request: Request,
                       orm: Session = Depends(get_orm_session)) -> GatewayKeyResponse:
    user_id = _session_user(request)
    result = _llm_change(orm, request, user_id, key_id, 'rename')
    if result is not None:
        return result
    row = orm.execute(text("""
        UPDATE public.ai_gateway_keys SET label=:label
        WHERE id=:id AND user_id=:uid AND is_active
        RETURNING id, key_prefix, label, is_active, created_at, last_used_at
    """), {"id": str(key_id), "uid": str(user_id), "label": body.label}).first()
    if not row:
        raise HTTPException(status_code=404, detail="active gateway key not found")
    orm.commit()
    return GatewayKeyResponse(id=row.id, masked_key=f"{row.key_prefix}…", label=row.label,
                              is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)


@router.post("/keys/{key_id}/rotate", response_model=GatewayKeyResponse)
def rotate_gateway_key(key_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)) -> GatewayKeyResponse:
    user_id = _session_user(request)
    result = _llm_change(orm, request, user_id, key_id, 'rotate')
    if result is not None:
        return result
    raw = generate_api_key()
    row = orm.execute(text("""
        UPDATE public.ai_gateway_keys
        SET key_hash=:hash, key_prefix=:prefix
        WHERE id=:id AND user_id=:uid AND is_active
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
    result = _llm_change(orm, request, user_id, key_id, 'revoke')
    if result is not None:
        return result
    row = orm.execute(text("""
        UPDATE public.ai_gateway_keys SET is_active=false, revoked_at=COALESCE(revoked_at, now())
        WHERE id=:id AND user_id=:uid
        RETURNING id, key_prefix, label, is_active, created_at, last_used_at
    """), {"id": str(key_id), "uid": str(user_id)}).first()
    if not row:
        raise HTTPException(status_code=404, detail="gateway key not found")
    orm.commit()
    return GatewayKeyResponse(id=row.id, masked_key=f"{row.key_prefix}…", label=row.label,
                              is_active=row.is_active, created_at=row.created_at, last_used_at=row.last_used_at)


@router.delete("/keys/{key_id}", status_code=204)
def delete_revoked_gateway_key(key_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)) -> Response:
    user_id = _session_user(request)
    result = _llm_change(orm, request, user_id, key_id, 'remove')
    if result is not None:
        return result
    row = orm.execute(text("""
        UPDATE public.ai_gateway_keys
        SET hidden_at=COALESCE(hidden_at, now())
        WHERE id=:id AND user_id=:uid AND is_active=false
        RETURNING id
    """), {"id": str(key_id), "uid": str(user_id)}).first()
    if not row:
        raise HTTPException(status_code=404, detail="只能删除已撤销的 gateway key 记录")
    orm.commit()
    return Response(status_code=204)


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


def _trusted_gateway(request: Request) -> str:
    """Separate service identity; config contains SHA256 digests, never raw tokens."""
    try:
        configured = json.loads(os.getenv('SB_GATEWAY_TRUSTED_INSTANCES', '{}'))
        if not isinstance(configured, dict) or not configured:
            raise ValueError('no trusted instances')
        if any(not isinstance(value, str) or len(value) != 64
               or any(char not in '0123456789abcdef' for char in value) for value in configured.values()):
            raise ValueError('invalid credential digest')
    except (ValueError, TypeError):
        raise HTTPException(status_code=503, detail='Trusted gateway delivery not configured') from None
    instance = request.headers.get('x-smartbrain-gateway-id', '')
    raw = request.headers.get('x-smartbrain-gateway-token', '')
    expected = configured.get(instance, '0' * 64)
    matched = hmac.compare_digest(hash_api_key(raw), expected)
    if not raw or instance not in configured or not matched:
        raise HTTPException(status_code=401, detail='Trusted gateway credentials required')
    return instance


class GatewayAdmissionRequest(BaseModel):
    request_sha256: str = Field(..., pattern=r'^[0-9a-f]{64}$')


@device_router.post('/admissions', dependencies=[Depends(_key_response_headers)])
def admit_gateway_request(request: Request, body: GatewayAdmissionRequest,
                          orm: Session = Depends(get_orm_session)):
    instance = _trusted_gateway(request)
    claim = _gateway_claims(request, orm)
    admission_id = uuid.uuid4()
    receipt = generate_api_key('sbr')
    orm.execute(text('''
        INSERT INTO public.ai_gateway_admissions
          (id, gateway_instance_id, key_id, user_id, request_sha256, receipt_hash)
        VALUES (:id, :gateway_instance_id, :key_id, :user_id, :request_sha256, :receipt_hash)
    '''), {'id': str(admission_id), 'gateway_instance_id': instance, 'key_id': str(claim.id),
           'user_id': str(claim.user_id), 'request_sha256': body.request_sha256,
           'receipt_hash': hash_api_key(receipt)})
    orm.commit()
    return {'authorized': True, 'user_id': str(claim.user_id), 'key_id': str(claim.id),
            'request_id': str(admission_id), 'event_id': str(admission_id), 'receipt': receipt}


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
        commit=False,
    )


@device_router.post("/events", status_code=202)
def ingest_gateway_events(request: Request, body: GatewayEventBatch, orm: Session = Depends(get_orm_session)):
    if os.getenv('SB_GATEWAY_LEGACY_EVENTS_ENABLED', 'true').lower() in {'0', 'false', 'no', 'off'}:
        raise HTTPException(status_code=410, detail='Employee self-reporting retired; trusted gateway delivery required')
    claim = _gateway_claims(request, orm)
    return _ingest_gateway_events(claim, body, orm)


class TrustedGatewayEvent(BaseModel):
    receipt: str = Field(..., min_length=16, max_length=200)
    request_sha256: str = Field(..., pattern=r'^[0-9a-f]{64}$')
    event: GatewayEvent


@device_router.post('/trusted-events', status_code=202, dependencies=[Depends(_key_response_headers)])
def ingest_trusted_gateway_event(request: Request, body: TrustedGatewayEvent,
                                orm: Session = Depends(get_orm_session)):
    instance = _trusted_gateway(request)
    # No active-key filter: the receipt proves admission before revocation.
    # The service credential and instance binding are independently mandatory.
    claim = orm.execute(text('''
        SELECT a.id AS admission_id, a.key_id AS id, a.user_id,
               a.request_sha256, a.event_sha256, au.email, pu.full_name
        FROM public.ai_gateway_admissions a
        JOIN auth.users au ON au.id=a.user_id
        JOIN public.users pu ON pu.id=a.user_id
        WHERE a.receipt_hash=:receipt_hash AND a.gateway_instance_id=:gateway_instance_id
        FOR UPDATE OF a
    '''), {'receipt_hash': hash_api_key(body.receipt), 'gateway_instance_id': instance}).first()
    if not claim:
        raise HTTPException(status_code=401, detail='Invalid gateway receipt')
    event = body.event
    if (event.gateway_instance_id != instance or event.event_id != str(claim.admission_id)
            or event.request_id != str(claim.admission_id)
            or body.request_sha256 != claim.request_sha256):
        raise HTTPException(status_code=409, detail='Event does not match admitted request')
    event.key_id = claim.id
    serialized = event.model_dump(mode='json')
    if event.request_message_count is None:
        # Existing accepted receipts predate these fields. Adding null defaults
        # would change their immutable hash and strand ACK-lost old journals.
        serialized.pop('request_message_count')
        serialized.pop('context_source')
    payload = json.dumps(serialized, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    payload_hash = hash_api_key(payload)
    if claim.event_sha256 and claim.event_sha256 != payload_hash:
        raise HTTPException(status_code=409, detail='Admitted event is immutable')
    if not claim.event_sha256:
        # Preserve incomplete/personal messages even before their downstream
        # consumer supports them; acceptance and token ledger commit together.
        orm.execute(text('''
            UPDATE public.ai_gateway_admissions
            SET event_sha256=:event_sha256, event_payload=CAST(:event_payload AS jsonb), delivered_at=now()
            WHERE id=:id
        '''), {'id': str(claim.admission_id), 'event_sha256': payload_hash, 'event_payload': payload})
    return _ingest_gateway_events(claim, GatewayEventBatch(events=[event]), orm)


def _ingest_gateway_events(claim: Any, body: GatewayEventBatch, orm: Session):
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
                    "cache_write": usage["cache_creation_tokens"], "reasoning": usage["reasoning_tokens"],
                    "semantics": usage["input_token_semantics"], "semantics_version": event.token_semantics_version,
                    "total": usage["total_tokens"], "usage_missing": bool(event.usage_missing or usage['usage_missing']),
                    "raw_usage": json.dumps(event.raw_usage or event.usage, ensure_ascii=False),
                    "cost": event.total_cost_usd, "latency": event.latency_ms,
                    "error": event.error_message, "usage_date": usage_date, "started_at": event.started_at,
                    "completed_at": event.completed_at}).first()
        if row:
            accepted += 1
            dates.add(usage_date)
            if event.project_id:
                try:
                    from agentops.rag.authz import require_member
                    require_member(orm, user_id=claim.user_id, project_id=event.project_id)
                except AuthzError as exc:
                    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
            if event.content_complete and event.project_id and event.conversation_id and event.messages:
                session_id = _materialize_gateway_conversation(
                    orm, claim=claim, employee_id=employee_id, employee_name=employee_name,
                    event=event, usage=usage,
                )
                orm.execute(text("UPDATE public.ai_gateway_events SET chat_session_id=:session_id, conversation_id=:conversation_id, context_complete=true, content_complete=true, content_sync_status='synced' WHERE id=:id"), {"session_id": str(session_id), "conversation_id": event.conversation_id, "id": str(row.id)})
    orm.execute(text("UPDATE public.ai_gateway_keys SET last_used_at=now() WHERE id=:id"), {"id": str(claim.id)})
    if dates:
        orm.execute(text("SELECT public.refresh_ai_usage_leaderboard_daily(CAST(:dates AS date[]))"), {"dates": sorted(dates)})
        orm.execute(text("SELECT public.refresh_ai_gateway_leaderboard_daily(CAST(:dates AS date[]))"), {"dates": sorted(dates)})
    # An acknowledgement covers the receipt, event and aggregates together.
    # A failed refresh must leave the request safely retryable, not partially committed.
    orm.commit()
    if dates:
        try:
            response_cache.bump("leaderboard")
        except Exception:
            pass
    return {"accepted": accepted, "duplicates": len(body.events) - accepted}


@device_router.get("/authorize", dependencies=[Depends(_key_response_headers)])
def authorize_gateway_key(request: Request, orm: Session = Depends(get_orm_session)):
    claim = _gateway_claims(request, orm)
    return {"authorized": True, "user_id": str(claim.user_id), "key_id": str(claim.id)}
