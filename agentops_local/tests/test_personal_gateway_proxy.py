import json
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from agentops.api import personal_gateway_proxy as proxy
from agentops.api.personal_gateway_proxy import (
    bearer_token,
    event_for_response,
    build_upstream_url,
    normalize_upstream_base_url,
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


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("http://192.168.10.146:9000", "http://192.168.10.146:9000"),
        ("http://192.168.10.146:9000/", "http://192.168.10.146:9000"),
        ("http://192.168.10.146:9000/v1", "http://192.168.10.146:9000"),
        ("http://192.168.10.146:9000/v1/", "http://192.168.10.146:9000"),
    ],
)
def test_upstream_base_url_accepts_root_or_v1(configured, expected) -> None:
    assert normalize_upstream_base_url(configured) == expected


@pytest.mark.parametrize("base", [
    "http://192.168.10.146:9000",
    "http://192.168.10.146:9000/v1",
])
def test_upstream_url_has_exactly_one_v1_segment(base) -> None:
    assert build_upstream_url(base, "/responses") == "http://192.168.10.146:9000/v1/responses"


@pytest.mark.parametrize(
    "configured",
    ["", "localhost:9000", "http://user:secret@host:9000", "http://host:9000/v1?x=1"],
)
def test_upstream_base_url_rejects_unsafe_values(configured) -> None:
    with pytest.raises(ValueError):
        normalize_upstream_base_url(configured)


def test_smartbrain_relay_requires_the_trusted_normalized_root(monkeypatch) -> None:
    monkeypatch.setattr(proxy, "UPSTREAM_AUTH_MODE", "smartbrain_relay")
    monkeypatch.setattr(proxy, "UPSTREAM_BASE_URL", "http://192.168.10.146:9000/v1/")
    assert proxy._validate_upstream_configuration() == "smartbrain_relay"
    monkeypatch.setattr(proxy, "UPSTREAM_BASE_URL", "http://127.0.0.1:9000")
    with pytest.raises(ValueError, match="trusted SmartBrain relay"):
        proxy._validate_upstream_configuration()


def test_smartbrain_relay_rejects_a_different_concrete_request_target() -> None:
    with pytest.raises(ValueError, match="trusted relay"):
        proxy._validate_upstream_target(
            "http://127.0.0.1:9000/v1/responses", auth_mode="smartbrain_relay"
        )
    with pytest.raises(ValueError, match="/v1 API"):
        proxy._validate_upstream_target(
            "http://192.168.10.146:9000/internal/responses", auth_mode="smartbrain_relay"
        )
    with pytest.raises(ValueError, match="query or fragment"):
        proxy._validate_upstream_target(
            "http://192.168.10.146:9000/v1/responses?leak=1", auth_mode="smartbrain_relay"
        )


def test_upstream_headers_opaque_mode_never_forward_personal_key() -> None:
    headers = upstream_headers({
        "authorization": "Bearer sbk_secret",
        "host": "edge",
        "content-type": "application/json",
        "x-client-request-id": "request-1",
    }, auth_mode="opaque")
    assert "authorization" not in {key.lower() for key in headers}
    assert "host" not in {key.lower() for key in headers}
    assert headers["content-type"] == "application/json"


def test_upstream_headers_smartbrain_relay_forwards_only_validated_authorization() -> None:
    headers = upstream_headers({
        "authorization": "Bearer sbk_secret",
        "host": "edge",
        "content-type": "application/json",
        "x-smartbrain-project-context": "project-secret",
        "x-smartbrain-project-id": "project-id",
        "x-api-key": "forged-key",
        "x-openai-api-key": "forged-key",
        "x-client-request-id": "request-1",
    }, auth_mode="smartbrain_relay", validated_authorization="Bearer sbk_secret")
    assert headers["authorization"] == "Bearer sbk_secret"
    assert "host" not in {key.lower() for key in headers}
    assert "x-smartbrain-project-context" not in {key.lower() for key in headers}
    assert "x-smartbrain-project-id" not in {key.lower() for key in headers}
    assert "x-api-key" not in {key.lower() for key in headers}
    assert "x-openai-api-key" not in {key.lower() for key in headers}
    assert headers["content-type"] == "application/json"


def test_smartbrain_relay_requires_a_locally_validated_authorization() -> None:
    with pytest.raises(ValueError, match="validated authorization"):
        upstream_headers({"authorization": "Bearer sbk_secret"}, auth_mode="smartbrain_relay")


def test_smartbrain_relay_request_forwards_validated_auth_for_json_and_stream(monkeypatch) -> None:
    class Request:
        method = "POST"
        headers = {
            "Authorization": "Bearer sbk_test",
            "X-API-Key": "forged-key",
            "X-SmartBrain-Project-Id": "forged-project",
        }
        query_params = httpx.QueryParams()

        async def is_disconnected(self):
            return False

    class Client:
        def __init__(self):
            self.seen = []

        async def request(self, method, url, *, content, headers, params):
            self.seen.append((url, headers, False))
            return httpx.Response(200, json={"output_text": "ok"})

        def build_request(self, method, url, *, content, headers, params):
            return httpx.Request(method, url, content=content, headers=headers, params=params)

        async def send(self, outgoing, *, stream):
            self.seen.append((str(outgoing.url), dict(outgoing.headers), stream))
            return httpx.Response(200, content=b"{}")

    async def scenario():
        client = Client()
        runtime = SimpleNamespace(client=client)
        request = Request()
        await proxy._upstream_request(
            request, runtime, "http://192.168.10.146:9000/v1/responses", b"{}",
            validated_authorization="Bearer sbk_test",
        )
        streamed = await proxy._upstream_request(
            request, runtime, "http://192.168.10.146:9000/v1/responses", b"{}",
            streaming=True, validated_authorization="Bearer sbk_test",
        )
        await streamed.aclose()
        assert len(client.seen) == 2
        for _url, headers, _stream in client.seen:
            assert headers["authorization"] == "Bearer sbk_test"
            assert "x-api-key" not in {key.lower() for key in headers}
            assert "x-smartbrain-project-id" not in {key.lower() for key in headers}

    monkeypatch.setattr(proxy, "UPSTREAM_AUTH_MODE", "smartbrain_relay")
    monkeypatch.setattr(proxy, "UPSTREAM_BASE_URL", "http://192.168.10.146:9000/v1")
    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["", "relay", "unknown"])
def test_upstream_headers_rejects_unknown_auth_mode(mode) -> None:
    with pytest.raises(ValueError, match="SB_PERSONAL_UPSTREAM_AUTH_MODE"):
        upstream_headers({}, auth_mode=mode)


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
def _chat_event(messages, response_text, *, status_code=200):
    return event_for_response(
        body=json.dumps({
            "model": "gpt-6-astra",
            "choices": [{"message": {"role": "assistant", "content": response_text}}],
            "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
        }).encode(),
        request_payload={"model": "gpt-6-astra", "messages": messages},
        response_content_type="application/json",
        status_code=status_code,
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        latency_ms=5,
    )


def test_event_records_only_this_turn_from_chat_history() -> None:
    event = _chat_event([
        {"role": "user", "content": "question 1"},
        {"role": "assistant", "content": "answer 1"},
        {"role": "user", "content": "question 2"},
    ], "answer 2")
    assert [(item.role, item.content) for item in event.messages] == [
        ("user", "question 2"),
        ("assistant", "answer 2"),
    ]


def test_event_records_first_turn_in_full() -> None:
    event = _chat_event([{"role": "user", "content": "question 1"}], "answer 1")
    assert [(item.role, item.content) for item in event.messages] == [
        ("user", "question 1"),
        ("assistant", "answer 1"),
    ]


def test_event_records_multi_turn_tail_only() -> None:
    event = _chat_event([
        {"role": "user", "content": "question 1"},
        {"role": "assistant", "content": "answer 1"},
        {"role": "user", "content": "question 2"},
        {"role": "assistant", "content": "answer 2"},
        {"role": "user", "content": "question 3"},
    ], "answer 3")
    assert [(item.role, item.content) for item in event.messages] == [
        ("user", "question 3"),
        ("assistant", "answer 3"),
    ]


def test_event_records_responses_input_incremental_tail() -> None:
    event = event_for_response(
        body=json.dumps({
            "model": "gpt-6-astra",
            "output_text": "answer 2",
            "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
        }).encode(),
        request_payload={"model": "gpt-6-astra", "input": [
            {"role": "user", "content": "question 1"},
            {"role": "assistant", "content": "answer 1"},
            {"role": "user", "content": "question 2"},
        ]},
        response_content_type="application/json",
        status_code=200,
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        latency_ms=5,
    )
    assert [(item.role, item.content) for item in event.messages] == [
        ("user", "question 2"),
        ("assistant", "answer 2"),
    ]


def test_event_tail_fallback_when_history_ends_with_assistant() -> None:
    event = _chat_event([
        {"role": "user", "content": "question 1"},
        {"role": "assistant", "content": "answer 1"},
    ], "answer 2")
    assert [(item.role, item.content) for item in event.messages] == [
        ("user", "question 1"),
        ("assistant", "answer 2"),
    ]


def test_event_incremental_tail_keeps_internal_roles_filtered() -> None:
    event = _chat_event([
        {"role": "system", "content": "private agent instructions"},
        {"role": "user", "content": "question 1"},
        {"role": "assistant", "content": "answer 1"},
        {"role": "tool", "content": "private tool output"},
        {"role": "user", "content": "question 2"},
    ], "answer 2")
    assert [(item.role, item.content) for item in event.messages] == [
        ("user", "question 2"),
        ("assistant", "answer 2"),
    ]


def test_error_response_keeps_only_incremental_prompt() -> None:
    event = _chat_event([
        {"role": "user", "content": "question 1"},
        {"role": "assistant", "content": "answer 1"},
        {"role": "user", "content": "question 2"},
    ], "", status_code=400)
    assert event.status_code == 400
    assert [(item.role, item.content) for item in event.messages] == [("user", "question 2")]
