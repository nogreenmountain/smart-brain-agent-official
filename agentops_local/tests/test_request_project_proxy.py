import asyncio
import contextlib
import json
import uuid
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from starlette.requests import Request

from agentops.api import personal_gateway_proxy as proxy
from agentops.api.routes.v4 import ai_gateway as gateway

PID = 'dfaefd9a-8e5e-4775-bc18-e3d551c651e4'
UID = uuid.UUID('11111111-1111-4111-8111-111111111111')


class Orm:
    def __init__(self, *, member=True):
        self.member = member

    def execute(self, statement, params=None):
        sql = str(statement)
        if 'FROM public.project_members' in sql:
            value = SimpleNamespace(role='developer') if self.member else None
        elif 'FROM public.users' in sql:
            value = SimpleNamespace(is_system_admin=False)
        elif 'INSERT INTO public.ai_gateway_events' in sql:
            value = SimpleNamespace(id=uuid.uuid4())
        else:
            value = SimpleNamespace(id=uuid.UUID(PID), name='合成项目')
        return SimpleNamespace(first=lambda: value)

    def commit(self):
        pass


def invoke_proxy(monkeypatch, *, member=True, project_header=PID, agents=None, persist=False, user_id=UID, upstream_calls=None):
    events, calls = [], upstream_calls if upstream_calls is not None else []
    payload = {'model': 'synthetic', 'input': [{'role': 'user', 'content': 'visible request'}]}
    if agents:
        payload['input'].insert(0, {'role': 'user', 'content': agents})
    body = json.dumps(payload).encode()
    headers = [(b'authorization', b'Bearer synthetic-key')]
    if project_header is not None:
        headers.append((b'x-smartbrain-project-id', project_header.encode()))
    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}
    request = Request({'type': 'http', 'method': 'POST', 'path': '/v1/responses', 'query_string': b'', 'headers': headers}, receive)
    request.state.gateway_claim = SimpleNamespace(id=uuid.uuid4(), user_id=user_id, email='synthetic@example.invalid', full_name='合成')
    class Client:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def request(self, *args, **kwargs):
            calls.append(kwargs)
            return httpx.Response(200, json={'model': 'synthetic', 'output_text': 'visible result', 'usage': {'input_tokens': 2, 'output_tokens': 1, 'total_tokens': 3}})
    monkeypatch.setattr(proxy, 'resolve_gateway_project_context', lambda *a, **k: None)
    monkeypatch.setattr(proxy, '_gateway_claims', lambda request, orm: request.state.gateway_claim)
    if not persist:
        monkeypatch.setattr(proxy, '_ingest_gateway_events', lambda claim, batch, orm: events.extend(batch.events))
    async def run():
        @contextlib.contextmanager
        def sessions():
            yield Orm(member=member)
        app = FastAPI()
        app.state.personal_gateway_runtime = proxy.GatewayRuntime(client=Client(), session_factory=sessions)
        request.scope['app'] = app
        return await proxy.proxy_request(request)
    result = asyncio.run(run())
    return result, events, calls


def test_header_project_is_attached_and_not_forwarded_upstream(monkeypatch):
    result, events, calls = invoke_proxy(monkeypatch)
    assert result.status_code == 200
    assert events[0].project_id == uuid.UUID(PID)
    assert events[0].usage['total_tokens'] == 3
    assert 'x-smartbrain-project-id' not in calls[0]['headers']


def test_project_nonmember_is_rejected_before_model_call(monkeypatch):
    calls = []
    with pytest.raises(HTTPException) as error:
        invoke_proxy(monkeypatch, member=False, upstream_calls=calls)
    assert error.value.status_code == 403
    assert calls == []


def test_agents_project_is_attached_without_storing_rules(monkeypatch):
    agents = f'# AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {PID} -->\n</INSTRUCTIONS>'
    _, events, _ = invoke_proxy(monkeypatch, project_header=None, agents=agents)
    assert events[0].project_id == uuid.UUID(PID)
    assert [m.content for m in events[0].messages] == ['visible request', 'visible result']


def test_attributed_personal_calls_do_not_publish_raw_wiki(monkeypatch):
    calls = []
    event = proxy.event_for_response(body=b'{"output_text":"visible result","usage":{"input_tokens":2,"output_tokens":1}}', request_payload={'input': 'visible request'}, response_content_type='application/json', status_code=200, started_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc), latency_ms=1, project_id=uuid.UUID(PID))
    monkeypatch.setattr(gateway, '_materialize_project_conversation_record', lambda *a, **k: calls.append('wiki'))
    monkeypatch.setattr(gateway, '_materialize_gateway_conversation', lambda *a, **k: calls.append('legacy-project') or uuid.uuid4())
    monkeypatch.setattr(gateway, '_materialize_personal_api_conversation', lambda *a, **k: calls.append('personal') or uuid.uuid4())
    monkeypatch.setattr(gateway.response_cache, 'bump', lambda *a: None)
    gateway._ingest_gateway_events(SimpleNamespace(id=uuid.uuid4(), user_id=UID, email='synthetic@example.invalid', full_name='合成'), gateway.GatewayEventBatch(events=[event]), Orm())
    assert calls == ['personal']
    assert event.context_complete is False


def test_rules_in_a_text_part_are_removed_without_losing_visible_text(monkeypatch):
    agents = f'# AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {PID} -->\n</INSTRUCTIONS>'
    _, events, _ = invoke_proxy(monkeypatch, project_header=None, agents=[{'type': 'input_text', 'text': agents}, {'type': 'input_text', 'text': 'kept extra request'}])
    assert [m.content for m in events[0].messages] == ['kept extra request', 'visible request', 'visible result']
