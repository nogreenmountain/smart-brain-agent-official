"""Authenticated OpenAI-compatible proxy for registered personal API keys.

The edge route must terminate here before reaching the model gateway.  This
module deliberately buffers the upstream response: it keeps JSON and SSE
wire-compatible while allowing one immutable usage/work-record event to be
written after the upstream call completes.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from agentops.api.routes.v4.ai_gateway import (
    GatewayConversationMessage,
    GatewayEvent,
    GatewayEventBatch,
    _gateway_claims,
    _ingest_gateway_events,
)
from agentops.api.routes.v4.project_agents import resolve_gateway_project_context
from agentops.common.orm import get_orm_session
from agentops.ai_usage.gateway import extract_usage_from_sse

logger = logging.getLogger(__name__)
UPSTREAM_BASE_URL = os.getenv("SB_PERSONAL_UPSTREAM_URL", "http://192.168.10.146:9000").rstrip("/")
UPSTREAM_TIMEOUT_SECONDS = float(os.getenv("SB_PERSONAL_UPSTREAM_TIMEOUT_SECONDS", "120"))
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
        and key.lower() not in {"authorization", "x-smartbrain-project-context"}
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
            content = _text_content(item.get("content"))
            if content:
                messages.append(GatewayConversationMessage(role=role, content=content[:1_000_000]))
    elif "input" in payload:
        raw_input = payload.get("input")
        if isinstance(raw_input, list):
            for item in raw_input:
                if isinstance(item, dict):
                    content = _text_content(item.get("content") or item.get("input") or item.get("text"))
                    role = _display_role(item.get("role"), "user")
                else:
                    content = _text_content(item)
                    role = "user"
                if role is not None and content:
                    messages.append(GatewayConversationMessage(role=role, content=content[:1_000_000]))
        else:
            content = _text_content(raw_input)
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


async def proxy_request(
    request: Request,
    orm: Session = Depends(get_orm_session),
) -> Response:
    # The scope dependency has already checked the key. The fallback keeps the
    # endpoint safe when mounted directly in a unit test or another app.
    claim = getattr(request.state, "gateway_claim", None) or _gateway_claims(request, orm)
    token = bearer_token(request.headers)
    del token  # validation above and _gateway_claims are the only key consumers
    request_body = await request.body()
    project_context = request.headers.get("x-smartbrain-project-context")
    project_id = resolve_gateway_project_context(
        orm,
        user_id=claim.user_id,
        key_id=claim.id,
        token=project_context,
    )
    try:
        request_payload = json.loads(request_body.decode("utf-8")) if request_body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        request_payload = {}
    if not isinstance(request_payload, dict):
        request_payload = {}
    upstream_path = request.url.path[len("/v1"):] or "/"
    if not upstream_path.startswith("/"):
        upstream_path = "/" + upstream_path
    upstream_url = f"{UPSTREAM_BASE_URL}/v1{upstream_path}"
    started_at = datetime.now(timezone.utc)
    started_clock = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT_SECONDS, follow_redirects=False) as client:
            upstream = await client.request(
                request.method,
                upstream_url,
                content=request_body,
                headers=upstream_headers(request.headers),
                params=request.query_params,
            )
    except httpx.HTTPError as error:
        logger.warning("Personal API upstream unavailable: %s", type(error).__name__)
        event = event_for_response(
            body=b"{}",
            request_payload=request_payload,
            response_content_type="application/json",
            status_code=502,
            started_at=started_at,
            latency_ms=int((time.monotonic() - started_clock) * 1000),
            request_id=request.headers.get("x-client-request-id"),
            project_id=project_id,
        )
        try:
            _ingest_gateway_events(claim, GatewayEventBatch(events=[event]), orm)
        except Exception:
            logger.exception("Personal API upstream failure event persistence failed")
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
        _ingest_gateway_events(claim, GatewayEventBatch(events=[event]), orm)
    except Exception:
        # Never fabricate a successful usage row. The upstream response remains
        # usable, while the error is visible in service logs for reconciliation.
        logger.exception("Personal API usage event persistence failed")
    headers = _response_headers(upstream.headers)
    headers["x-smartbrain-gateway-authenticated"] = "true"
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)
