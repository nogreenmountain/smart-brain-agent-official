"""Authenticated OpenAI-compatible proxy for registered personal API keys.

The edge route must terminate here before reaching the model gateway.  This
module deliberately buffers the upstream response: it keeps JSON and SSE
wire-compatible while allowing one immutable usage/work-record event to be
written after the upstream call completes.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import partial
from typing import Any

import httpx
import anyio
from fastapi import HTTPException, Request, Response
from sqlalchemy import text

from agentops.api.routes.v4.ai_gateway import (
    GatewayConversationMessage,
    GatewayEvent,
    GatewayEventBatch,
    _gateway_claims,
    _ingest_gateway_events,
)
from agentops.api.routes.v4.project_agents import resolve_gateway_project_context
from agentops.common.orm import session_scope
from agentops.api.gateway_admission import AdmissionQueue, AdmissionRejected
from agentops.ai_usage.gateway import extract_usage_from_sse
from agentops.ai_usage.request_project import agents_instructions, project_from_request
from agentops.rag.authz import AuthzError, require_member

logger = logging.getLogger(__name__)
UPSTREAM_BASE_URL = os.getenv("SB_PERSONAL_UPSTREAM_URL", "http://192.168.10.146:9000").rstrip("/")
UPSTREAM_TIMEOUT_SECONDS = float(os.getenv("SB_PERSONAL_UPSTREAM_TIMEOUT_SECONDS", "120"))


@dataclass(frozen=True)
class GatewayIdentity:
    id: uuid.UUID
    user_id: uuid.UUID
    email: str | None
    full_name: str | None


class GatewayRuntime:
    def __init__(self, *, client, session_factory=session_scope, max_active=8,
                 max_waiting=24, queue_timeout=60, db_concurrency=3):
        self.client, self.session_factory = client, session_factory
        self.admission = AdmissionQueue(max_active, max_waiting, queue_timeout)
        self.ingress = AdmissionQueue(max_active + max_waiting, 0, queue_timeout)
        self.max_body_bytes = 16 * 1024 * 1024
        self.db_limiter = anyio.CapacityLimiter(db_concurrency)

    def _with_session(self, operation, args):
        with self.session_factory() as orm:
            return operation(orm, *args)

    async def database(self, operation, *args):
        task = asyncio.create_task(anyio.to_thread.run_sync(
            partial(self._with_session, operation, args), limiter=self.db_limiter))
        cancelled = False
        while True:
            try:
                result = await asyncio.shield(task)
                break
            except asyncio.CancelledError:
                # Repeated cancellation cannot detach a thread-held session.
                if task.cancelled():
                    raise
                cancelled = True
            except BaseException:
                if cancelled:
                    raise asyncio.CancelledError from None
                raise
        if cancelled:
            raise asyncio.CancelledError
        return result


@asynccontextmanager
async def gateway_lifespan(app):
    active = int(os.getenv('SB_PERSONAL_MAX_ACTIVE', '8'))
    waiting = int(os.getenv('SB_PERSONAL_MAX_WAITING', '24'))
    timeout = float(os.getenv('SB_PERSONAL_QUEUE_TIMEOUT_SECONDS', '60'))
    if not 1 <= active <= 64 or not 0 <= waiting <= 256 or not 0 < timeout <= 600:
        raise ValueError('Invalid personal gateway limits')
    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS, follow_redirects=False,
            limits=httpx.Limits(max_connections=active, max_keepalive_connections=active)) as client:
        app.state.personal_gateway_runtime = GatewayRuntime(client=client,
            max_active=active, max_waiting=waiting, queue_timeout=timeout)
        try:
            yield
        finally:
            del app.state.personal_gateway_runtime


def gateway_runtime(request):
    runtime = getattr(request.app.state, 'personal_gateway_runtime', None)
    if runtime is None:
        raise HTTPException(503, 'gateway_runtime_unavailable', headers={'Retry-After': '3'})
    return runtime


def _identity(orm, request):
    row = _gateway_claims(request, orm)
    check = getattr(request.state, 'gateway_account_check', None)
    if check:
        check(row.user_id, orm)
    return GatewayIdentity(row.id, row.user_id, row.email, row.full_name)


async def authorize_proxy_scope(request, require_user):
    request.state.gateway_account_check = require_user
    request.state.gateway_claim = await gateway_runtime(request).database(_identity, request)


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def bearer_token(headers: Any) -> str:
    value = headers.get("authorization", "")
    if not value.lower().startswith("bearer ") or not value.split(" ", 1)[1].strip():
        raise HTTPException(status_code=401, detail="Gateway API key required")
    return value.split(" ", 1)[1].strip()


def upstream_headers(headers: Any) -> dict[str, str]:
    """Copy client headers without forwarding the personal credential."""
    result = {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
        and key.lower() not in {"authorization", "x-smartbrain-project-context", "x-smartbrain-project-id"}
    }
    result["x-smartbrain-gateway-proxy"] = "personal-api"
    return result


def _text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(
            part
            for item in value
            for part in [_text_content(item.get("text") if isinstance(item, dict) and "text" in item else item)]
            if part
        )
    if isinstance(value, dict):
        return _text_content(value.get("text") or value.get("content") or value.get("input") or "")
    return str(value) if value is not None else ""


def _display_role(value: Any, default: str) -> str | None:
    """Return only roles safe to show in a user-facing work record.

    System/developer prompts and tool messages can contain internal agent
    instructions, credentials, or execution context. They remain part of the
    upstream request for model execution, but must not be copied into the
    human-readable conversation projection.
    """
    role = str(value or default).lower()
    return role if role in {"user", "assistant"} else None


def _visible_request_text(value: Any) -> str:
    if isinstance(value, list):
        return '\n'.join(text for item in value for text in [_visible_request_text(item)] if text)
    content = _text_content(value)
    return '' if agents_instructions(content) is not None else content


def request_messages(payload: dict[str, Any]) -> list[GatewayConversationMessage]:
    messages: list[GatewayConversationMessage] = []
    raw_messages = payload.get("messages")
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            role = _display_role(item.get("role"), "user")
            if role is None:
                continue
            content = _visible_request_text(item.get("content"))
            if content:
                messages.append(GatewayConversationMessage(role=role, content=content[:1_000_000]))
    elif "input" in payload:
        raw_input = payload.get("input")
        if isinstance(raw_input, list):
            for item in raw_input:
                if isinstance(item, dict):
                    content = _visible_request_text(item.get("content") or item.get("input") or item.get("text"))
                    role = _display_role(item.get("role"), "user")
                else:
                    content = _visible_request_text(item)
                    role = "user"
                if role is not None and content:
                    messages.append(GatewayConversationMessage(role=role, content=content[:1_000_000]))
        else:
            content = _visible_request_text(raw_input)
            if content:
                messages.append(GatewayConversationMessage(role="user", content=content[:1_000_000]))
    return messages


def response_messages(payload: dict[str, Any]) -> list[GatewayConversationMessage]:
    messages: list[GatewayConversationMessage] = []
    choices = payload.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message") or choice.get("delta") or {}
            content = _text_content(message.get("content") if isinstance(message, dict) else message)
            role = _display_role(message.get("role") if isinstance(message, dict) else None, "assistant")
            if role is not None and content:
                messages.append(GatewayConversationMessage(role=role, content=content[:1_000_000]))
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = _text_content(item.get("content") or item.get("text") or item.get("output_text"))
            role = _display_role(item.get("role"), "assistant")
            if role is not None and content:
                messages.append(GatewayConversationMessage(role=role, content=content[:1_000_000]))
    if not messages and payload.get("output_text"):
        messages.append(GatewayConversationMessage(role="assistant", content=_text_content(payload["output_text"])[:1_000_000]))
    return messages


def decode_payload(content: bytes, content_type: str) -> dict[str, Any]:
    if "text/event-stream" in content_type:
        found = extract_usage_from_sse(content.decode("utf-8", errors="replace"))
        return found if isinstance(found, dict) else {}
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def event_for_response(
    *,
    body: bytes,
    request_payload: dict[str, Any],
    response_content_type: str,
    status_code: int,
    started_at: datetime,
    latency_ms: int,
    request_id: str | None = None,
    project_id: uuid.UUID | None = None,
) -> GatewayEvent:
    response_payload = decode_payload(body, response_content_type)
    usage = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
    if not usage and isinstance(response_payload.get("response"), dict):
        usage = response_payload["response"].get("usage") or {}
    messages = request_messages(request_payload) + response_messages(response_payload)
    if not messages:
        messages = [GatewayConversationMessage(role="assistant", content="个人 API 请求已完成，但上游未返回可记录的正文。")]
    # The client request ID is only a transport hint.  It must not become the
    # ledger id: desktop clients can reuse it across retries or an entire
    # session, while ``ai_gateway_events`` has a unique index on
    # (gateway_instance_id, request_id).  Generate the id at the trusted
    # Gateway boundary so every completed proxy call can be recorded.  Keep
    # the argument for compatibility with callers from the previous release.
    del request_id
    event_id = uuid.uuid4().hex
    model = str(response_payload.get("model") or request_payload.get("model") or "unknown")[:200]
    return GatewayEvent(
        event_id=event_id,
        request_id=event_id,
        model=model,
        request_model=str(request_payload.get("model") or model)[:200],
        requested_model=str(request_payload.get("model") or model)[:200],
        resolved_model=model,
        upstream_model=model,
        provider="personal-upstream",
        app_type="personal_api",
        status_code=status_code,
        usage=usage,
        raw_usage=usage,
        usage_missing=not bool(usage),
        latency_ms=max(0, min(latency_ms, 86_400_000)),
        error_message=None if status_code < 400 else f"upstream status {status_code}",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        conversation_id=event_id,
        title="个人 API 请求",
        task_id="personal-api",
        task_title="个人 API",
        trace_id=event_id,
        content_complete=True,
        project_id=project_id,
        messages=messages,
    )


def _response_headers(headers: Any) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "content-length"
    }


def _authorize_project(orm, request, request_payload):
    # Recheck after queuing; account/key/project access may have changed.
    claim = _identity(orm, request)
    project_context = request.headers.get("x-smartbrain-project-context")
    project_id = resolve_gateway_project_context(
        orm,
        user_id=claim.user_id,
        key_id=claim.id,
        token=project_context,
    )
    requested_project = project_from_request(request.headers, request_payload)
    if requested_project and project_id and requested_project != project_id:
        raise HTTPException(422, 'conflicting_project_ids')
    project_id = requested_project or project_id
    if project_id:
        if orm.execute(text('SELECT id FROM public.projects WHERE id=:pid'), {'pid': str(project_id)}).first() is None:
            raise HTTPException(404, 'project_not_found')
        try:
            require_member(orm, user_id=claim.user_id, project_id=project_id)
        except AuthzError as error:
            raise HTTPException(error.status_code, error.detail) from error
    return claim, project_id


def _save_event(orm, claim, event):
    return _ingest_gateway_events(claim, GatewayEventBatch(events=[event]), orm)


async def proxy_request(request: Request) -> Response:
    bearer_token(request.headers)
    runtime = gateway_runtime(request)
    try:
        async with runtime.ingress.slot():
            # Cap buffered requests before reading or entering the wait queue.
            parts, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > runtime.max_body_bytes:
                    raise HTTPException(413, 'gateway_request_too_large')
                parts.append(chunk)
            body = b''.join(parts)
            async with runtime.admission.slot(disconnected=request.is_disconnected):
                if await request.is_disconnected():
                    raise HTTPException(499, 'gateway_client_disconnected')
                return await _proxy_admitted(request, runtime, body)
    except AdmissionRejected as error:
        raise HTTPException(499 if error.reason == 'gateway_client_disconnected' else 503, error.reason,
                            headers={'Retry-After': '3', 'Cache-Control': 'no-store'}) from None


async def _upstream_request(request, runtime, url, body):
    stopped = asyncio.Event()
    async def watch():
        while not stopped.is_set() and not await request.is_disconnected():
            await asyncio.sleep(.05)
    model = asyncio.create_task(runtime.client.request(request.method, url,
        content=body, headers=upstream_headers(request.headers), params=request.query_params))
    disconnect = asyncio.create_task(watch())
    try:
        async with asyncio.timeout(UPSTREAM_TIMEOUT_SECONDS):
            done, _ = await asyncio.wait({model, disconnect}, return_when=asyncio.FIRST_COMPLETED)
            if model in done:
                return await model
            raise HTTPException(499, 'gateway_client_disconnected')
    except TimeoutError:
        raise httpx.ReadTimeout('Gateway model deadline exceeded') from None
    finally:
        # Starlette's is_disconnected uses a cancellation scope. It can consume
        # a concurrent task.cancel(), so stop the observer explicitly.
        stopped.set()
        if not model.done():
            model.cancel()
        await asyncio.gather(model, disconnect, return_exceptions=True)


async def _proxy_admitted(request, runtime, request_body):
    try:
        request_payload = json.loads(request_body.decode('utf-8')) if request_body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        request_payload = {}
    if not isinstance(request_payload, dict):
        request_payload = {}
    claim, project_id = await runtime.database(_authorize_project, request, request_payload)
    upstream_path = request.url.path[len("/v1"):] or "/"
    if not upstream_path.startswith("/"):
        upstream_path = "/" + upstream_path
    upstream_url = f"{UPSTREAM_BASE_URL}/v1{upstream_path}"
    started_at = datetime.now(timezone.utc)
    started_clock = time.monotonic()
    try:
        upstream = await _upstream_request(request, runtime, upstream_url, request_body)
    except (httpx.HTTPError, HTTPException, asyncio.CancelledError) as error:
        cancelled = isinstance(error, asyncio.CancelledError) or (
            isinstance(error, HTTPException) and error.status_code == 499)
        status = 499 if cancelled else 502
        if not cancelled:
            logger.warning("Personal API upstream unavailable: %s", type(error).__name__)
        event = event_for_response(
            body=b"{}",
            request_payload=request_payload,
            response_content_type="application/json",
            status_code=status,
            started_at=started_at,
            latency_ms=int((time.monotonic() - started_clock) * 1000),
            request_id=request.headers.get("x-client-request-id"),
            project_id=project_id,
        )
        try:
            await runtime.database(_save_event, claim, event)
        except Exception:
            logger.exception("Personal API upstream failure event persistence failed")
        if cancelled:
            raise
        raise HTTPException(status_code=502, detail="Personal API upstream unavailable") from error

    event = event_for_response(
        body=upstream.content,
        request_payload=request_payload,
        response_content_type=upstream.headers.get("content-type", ""),
        status_code=upstream.status_code,
        started_at=started_at,
        latency_ms=int((time.monotonic() - started_clock) * 1000),
        request_id=request.headers.get("x-client-request-id"),
        project_id=project_id,
    )
    try:
        await runtime.database(_save_event, claim, event)
    except Exception:
        # Never fabricate a successful usage row. The upstream response remains
        # usable, while the error is visible in service logs for reconciliation.
        logger.exception("Personal API usage event persistence failed")
    headers = _response_headers(upstream.headers)
    headers["x-smartbrain-gateway-authenticated"] = "true"
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)
