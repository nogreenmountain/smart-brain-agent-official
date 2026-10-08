import json

import httpx
import pytest
from fastapi import HTTPException

from agentops.api.personal_gateway_proxy import (
    bearer_token,
    event_for_response,
    request_messages,
    response_messages,
    upstream_headers,
)


def test_missing_or_empty_bearer_is_rejected() -> None:
    with pytest.raises(HTTPException) as missing:
        bearer_token({})
    assert missing.value.status_code == 401
    with pytest.raises(HTTPException) as empty:
        bearer_token({"authorization": "Bearer   "})
    assert empty.value.status_code == 401


def test_upstream_headers_never_forward_personal_key() -> None:
    headers = upstream_headers({
        "authorization": "Bearer sbk_secret",
        "host": "edge",
        "content-type": "application/json",
        "x-client-request-id": "request-1",
    })
    assert "authorization" not in {key.lower() for key in headers}
    assert "host" not in {key.lower() for key in headers}
    assert headers["content-type"] == "application/json"


def test_responses_payload_is_projected_to_usage_and_messages() -> None:
    request_payload = {"model": "gpt-6-astra", "input": "hello"}
    response_body = json.dumps({
        "id": "resp_1",
        "model": "gpt-6-astra",
        "output_text": "world",
        "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
    }).encode()
    event = event_for_response(
        body=response_body,
        request_payload=request_payload,
        response_content_type="application/json",
        status_code=200,
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        latency_ms=12,
    )
    assert event.app_type == "personal_api"
    assert event.usage["input_tokens"] == 3
    assert [item.content for item in event.messages] == ["hello", "world"]
    assert event.content_complete is True


def test_client_request_id_cannot_collapse_personal_usage_events() -> None:
    kwargs = {
        "body": b'{"model":"gpt-6-astra","usage":{"input_tokens":1,"output_tokens":1}}',
        "request_payload": {"model": "gpt-6-astra", "messages": [{"role": "user", "content": "hello"}]},
        "response_content_type": "application/json",
        "status_code": 200,
        "started_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "latency_ms": 1,
        "request_id": "desktop-session-request-id",
    }
    first = event_for_response(**kwargs)
    second = event_for_response(**kwargs)
    assert first.request_id != "desktop-session-request-id"
    assert second.request_id != "desktop-session-request-id"
    assert first.request_id != second.request_id
    assert first.event_id != second.event_id


def test_invalid_upstream_response_is_still_recorded_as_error() -> None:
    event = event_for_response(
        body=b'{"error":{"message":"bad request"}}',
        request_payload={"model": "gpt-6-astra", "messages": [{"role": "user", "content": "hello"}]},
        response_content_type="application/json",
        status_code=400,
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        latency_ms=5,
    )
    assert event.status_code == 400
    assert event.error_message == "upstream status 400"
    assert event.usage_missing is True
    assert event.messages[0].role == "user"


def test_request_messages_supports_openai_chat_and_responses_inputs() -> None:
    chat = request_messages({"messages": [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]})
    responses = request_messages({"input": [{"role": "user", "content": "hi"}]})
    assert [item.content for item in chat] == ["hi"]
    assert [item.content for item in responses] == ["hi"]


def test_internal_request_roles_are_not_projected_to_work_record() -> None:
    messages = request_messages({
        "messages": [
            {"role": "system", "content": "private agent instructions"},
            {"role": "developer", "content": "private application instructions"},
            {"role": "tool", "content": "private tool output"},
            {"role": "user", "content": "visible question"},
            {"role": "assistant", "content": "visible history"},
        ],
    })
    assert [(item.role, item.content) for item in messages] == [
        ("user", "visible question"),
        ("assistant", "visible history"),
    ]


def test_internal_response_roles_are_not_projected_to_work_record() -> None:
    messages = response_messages({
        "choices": [
            {"message": {"role": "tool", "content": "private tool output"}},
            {"message": {"role": "assistant", "content": "visible answer"}},
        ],
        "output": [
            {"role": "system", "content": "private output context"},
            {"role": "assistant", "content": "visible output"},
        ],
    })
    assert [(item.role, item.content) for item in messages] == [
        ("assistant", "visible answer"),
        ("assistant", "visible output"),
    ]
