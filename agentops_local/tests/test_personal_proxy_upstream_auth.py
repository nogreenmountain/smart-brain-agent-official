"""Upstream credential-boundary regression tests.

These tests never contact the Windows relay or a model provider.  They exercise
the real proxy request helper with a fake httpx client so the two transport
paths (buffered JSON and streaming) cannot silently diverge.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx

from agentops.api import personal_gateway_proxy as proxy


class _Request:
    method = "POST"
    headers = {
        "Authorization": "Bearer sbk_fixture",
        "Content-Type": "application/json",
        "X-SmartBrain-Project-Context": "sbc_attacker_supplied",
        "X-SmartBrain-Project-ID": "project-attacker_supplied",
        "X-API-Key": "forged-header-key",
        "X-OpenAI-API-Key": "forged-header-key",
    }
    query_params = {"client": "fixture"}

    async def is_disconnected(self) -> bool:
        return False


class _FakeClient:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def build_request(self, method, url, *, content=None, headers=None, params=None):
        request = httpx.Request(method, url, content=content, headers=headers, params=params)
        self.requests.append(request)
        return request

    async def send(self, request, *, stream=False):
        assert stream is True
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b"data: [DONE]\n",
            request=request,
        )

    async def request(self, method, url, *, content=None, headers=None, params=None):
        request = httpx.Request(method, url, content=content, headers=headers, params=params)
        self.requests.append(request)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"ok":true}',
            request=request,
        )


def _run_upstream(monkeypatch, *, mode: str, streaming: bool) -> httpx.Request:
    async def scenario() -> httpx.Request:
        client = _FakeClient()
        runtime = SimpleNamespace(client=client)
        request = _Request()
        response = await proxy._upstream_request(
            request,
            runtime,
            "http://192.168.10.146:9000/v1/responses",
            b'{"model":"fixture","input":"hello"}',
            streaming=streaming,
            validated_authorization="Bearer sbk_fixture",
        )
        await response.aclose()
        assert len(client.requests) == 1
        return client.requests[0]

    monkeypatch.setattr(proxy, "UPSTREAM_AUTH_MODE", mode)
    monkeypatch.setattr(proxy, "UPSTREAM_BASE_URL", proxy.TRUSTED_SMARTBRAIN_RELAY_URL)
    return asyncio.run(scenario())


def test_smartbrain_relay_forwards_validated_key_on_buffered_json_path(monkeypatch):
    request = _run_upstream(monkeypatch, mode="smartbrain_relay", streaming=False)
    assert request.headers["authorization"] == "Bearer sbk_fixture"
    assert "x-smartbrain-project-context" not in request.headers
    assert "x-smartbrain-project-id" not in request.headers
    assert "x-api-key" not in request.headers
    assert "x-openai-api-key" not in request.headers
    assert "sbk_fixture" not in str(request.url)
    assert b"sbk_fixture" not in request.content


def test_smartbrain_relay_forwards_validated_key_on_streaming_path(monkeypatch):
    request = _run_upstream(monkeypatch, mode="smartbrain_relay", streaming=True)
    assert request.headers["authorization"] == "Bearer sbk_fixture"
    assert "x-smartbrain-project-context" not in request.headers
    assert "x-smartbrain-project-id" not in request.headers
    assert "x-api-key" not in request.headers
    assert "x-openai-api-key" not in request.headers
    assert "sbk_fixture" not in str(request.url)
    assert b"sbk_fixture" not in request.content


def test_opaque_upstream_never_receives_personal_key(monkeypatch):
    request = _run_upstream(monkeypatch, mode="opaque", streaming=False)
    assert "authorization" not in request.headers
    assert "sbk_fixture" not in str(request.url)
    assert b"sbk_fixture" not in request.content
