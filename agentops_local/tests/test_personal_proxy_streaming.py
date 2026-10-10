"""Real HTTP streaming regressions, synthetic upstream and no production DB."""
import asyncio
import json
import os
import time

import httpx
import pytest
from fastapi import FastAPI
from starlette.responses import StreamingResponse

from agentops.api import personal_gateway_proxy as proxy
from test_personal_proxy_concurrency import _runtime_fixture
from test_personal_proxy_http_pg import serve


def test_real_default_timeout_boundary(monkeypatch):
    """Set SB_STREAM_TEST_DURATION=130 for a real wall-clock acceptance run."""
    async def scenario():
        duration=float(os.getenv('SB_STREAM_TEST_DURATION','.3'))
        model=FastAPI()
        @model.post('/v1/responses')
        async def respond():
            async def chunks():
                started=time.monotonic()
                while time.monotonic()-started<duration:
                    yield b'data: {"type":"response.output_text.delta","delta":"synthetic"}\n\n'
                    await asyncio.sleep(min(1,duration/4))
                yield b'data: {"type":"response.completed","response":{"model":"fixture","output_text":"synthetic result","usage":{"input_tokens":2,"output_tokens":1}}}\n\n'
            return StreamingResponse(chunks(),media_type='text/event-stream')
        assert proxy.UPSTREAM_TIMEOUT_SECONDS==120 and proxy.MAX_STREAM_SECONDS==1800
        async with serve(model) as base,httpx.AsyncClient(timeout=120) as upstream:
            monkeypatch.setattr(proxy,'UPSTREAM_BASE_URL',base)
            app,saved=_runtime_fixture(monkeypatch,upstream)
            app.add_api_route('/v1/responses',proxy.proxy_request,methods=['POST'])
            async with serve(app) as url,httpx.AsyncClient(timeout=10) as client:
                started=time.monotonic()
                async with client.stream('POST',url+'/v1/responses',json={'stream':True},headers={'authorization':'Bearer fixture'}) as r:
                    assert r.status_code==200
                    chunks=r.aiter_bytes()
                    first=await anext(chunks)
                    first_ms=round((time.monotonic()-started)*1000)
                    assert first_ms<1000
                    body=first+b''.join([chunk async for chunk in chunks])
                elapsed=round(time.monotonic()-started,2)
                for _ in range(100):
                    if saved and app.state.personal_gateway_runtime.admission.active==0:break
                    await asyncio.sleep(.01)
                assert b'response.completed' in body and len(saved)==1 and saved[0].status_code==200
                assert saved[0].content_complete and saved[0].raw_usage=={'input_tokens':2,'output_tokens':1}
                print(json.dumps({'synthetic_stream_seconds':elapsed,'first_byte_ms':first_ms,'idle_timeout_seconds':120,'total_limit_seconds':1800,'real_model_requests':0}))
    asyncio.run(scenario())


def test_healthy_stream_delivers_before_eof_and_survives_old_total_deadline(monkeypatch):
    async def scenario():
        model = FastAPI()
        finished = asyncio.Event()
        @model.post('/v1/responses')
        async def respond():
            async def chunks():
                for _ in range(6):
                    yield b'event: response.output_text.delta\ndata: {"type":"response.output_text.delta","delta":"fixture"}\n\n'
                    await asyncio.sleep(.035)
                yield b'event: response.completed\ndata: {"type":"response.completed","response":{"model":"fixture","output_text":"fixture","usage":{"input_tokens":2,"output_tokens":1}}}\n\n'
                finished.set()
            return StreamingResponse(chunks(), media_type='text/event-stream')
        monkeypatch.setattr(proxy, 'UPSTREAM_TIMEOUT_SECONDS', .10)
        async with serve(model) as base, httpx.AsyncClient(timeout=.10) as upstream:
            monkeypatch.setattr(proxy, 'UPSTREAM_BASE_URL', base)
            app, saved = _runtime_fixture(monkeypatch, upstream)
            app.add_api_route('/v1/responses', proxy.proxy_request, methods=['POST'])
            async with serve(app) as url, httpx.AsyncClient(timeout=2) as client:
                started=time.monotonic()
                async with client.stream('POST',url+'/v1/responses',json={'model':'fixture','input':'synthetic','stream':True},headers={'authorization':'Bearer fixture'}) as response:
                    assert response.status_code==200, 'healthy progressing SSE was killed by total deadline'
                    stream=response.aiter_bytes()
                    first=await anext(stream)
                    assert not finished.is_set(), 'proxy buffered until EOF'
                    assert time.monotonic()-started < .10
                    runtime=app.state.personal_gateway_runtime
                    assert runtime.admission.active==1, 'stream released concurrency permit before EOF'
                    assert runtime.ingress.active==1
                    assert runtime.db_limiter.borrowed_tokens==0
                    body=first+b''.join([chunk async for chunk in stream])
                for _ in range(100):
                    if len(saved)==1 and runtime.admission.active==0:break
                    await asyncio.sleep(.01)
                assert b'response.completed' in body
                assert len(saved)==1 and saved[0].status_code==200
                assert saved[0].raw_usage=={'input_tokens':2,'output_tokens':1}
                assert saved[0].content_complete
                assert runtime.admission.active==runtime.ingress.active==0
    asyncio.run(scenario())


def test_stream_disconnect_holds_budget_until_cleanup_then_queue_progresses(monkeypatch):
    async def scenario():
        model=FastAPI()
        upstream_closed=asyncio.Event()
        @model.post('/v1/responses')
        async def respond():
            async def chunks():
                try:
                    yield b'data: {"type":"response.output_text.delta","delta":"partial"}\n\n'
                    await asyncio.sleep(5)
                finally:upstream_closed.set()
            return StreamingResponse(chunks(),media_type='text/event-stream')
        async with serve(model) as base,httpx.AsyncClient() as upstream:
            monkeypatch.setattr(proxy,'UPSTREAM_BASE_URL',base)
            app,saved=_runtime_fixture(monkeypatch,upstream,max_waiting=0)
            app.add_api_route('/v1/responses',proxy.proxy_request,methods=['POST'])
            async with serve(app) as url,httpx.AsyncClient(timeout=2) as client:
                async with client.stream('POST',url+'/v1/responses',json={'stream':True},headers={'authorization':'Bearer fixture'}) as r:
                    await anext(r.aiter_bytes())
                    assert app.state.personal_gateway_runtime.admission.active==1
                    rejected=await client.post(url+'/v1/responses',json={'stream':True},headers={'authorization':'Bearer fixture'})
                    assert rejected.status_code==503 and rejected.headers['retry-after']=='3'
                runtime=app.state.personal_gateway_runtime
                for _ in range(100):
                    if saved and runtime.admission.active==0:break
                    await asyncio.sleep(.01)
                assert len(saved)==1 and saved[0].status_code==499
                assert saved[0].usage_missing and not saved[0].content_complete
                assert runtime.admission.active==runtime.ingress.active==0
                assert await asyncio.wait_for(upstream_closed.wait(),1)
    asyncio.run(scenario())


def test_stream_capture_is_bounded_without_truncating_wire(monkeypatch):
    async def scenario():
        model=FastAPI()
        wire=b'data: '+b'x'*1000+b'\n\ndata: [DONE]\n\n'
        @model.post('/v1/chat/completions')
        async def respond():
            async def chunks():yield wire
            return StreamingResponse(chunks(),media_type='text/event-stream')
        monkeypatch.setattr(proxy,'MAX_STREAM_RECORD_BYTES',100)
        async with serve(model) as base,httpx.AsyncClient() as upstream:
            monkeypatch.setattr(proxy,'UPSTREAM_BASE_URL',base)
            app,saved=_runtime_fixture(monkeypatch,upstream)
            app.add_api_route('/v1/chat/completions',proxy.proxy_request,methods=['POST'])
            async with serve(app) as url,httpx.AsyncClient(timeout=2) as client:
                r=await client.post(url+'/v1/chat/completions',json={'stream':True},headers={'authorization':'Bearer fixture'})
                assert r.status_code==200 and r.content==wire
                for _ in range(100):
                    if saved:break
                    await asyncio.sleep(.01)
                assert len(saved)==1 and not saved[0].content_complete and saved[0].usage_missing
                assert app.state.personal_gateway_runtime.admission.active==0
    asyncio.run(scenario())


@pytest.mark.parametrize('mode', ['idle', 'deadline', 'eof', 'provider_failed'])
def test_interrupted_stream_records_failure_and_releases_resources(monkeypatch, mode):
    async def scenario():
        model=FastAPI()
        closed=asyncio.Event()
        @model.post('/v1/responses')
        async def respond():
            async def chunks():
                try:
                    yield b'data: {"type":"response.output_text.delta","delta":"partial"}\n\n'
                    if mode=='idle':await asyncio.sleep(5)
                    elif mode=='deadline':
                        while True:
                            await asyncio.sleep(.02)
                            yield b': ping\n\n'
                    elif mode=='provider_failed':
                        yield b'data: {"type":"response.failed","response":{"status":"failed","error":{"code":"server_is_overloaded"},"usage":{"input_tokens":2,"output_tokens":1}}}\n\n'
                finally:closed.set()
            return StreamingResponse(chunks(),media_type='text/event-stream')
        monkeypatch.setattr(proxy,'UPSTREAM_TIMEOUT_SECONDS',.10)
        monkeypatch.setattr(proxy,'MAX_STREAM_SECONDS',.13)
        async with serve(model) as base,httpx.AsyncClient(timeout=.10) as upstream:
            monkeypatch.setattr(proxy,'UPSTREAM_BASE_URL',base)
            app,saved=_runtime_fixture(monkeypatch,upstream)
            app.add_api_route('/v1/responses',proxy.proxy_request,methods=['POST'])
            async with serve(app) as url,httpx.AsyncClient(timeout=2) as client:
                interrupted=False
                try:
                    await client.post(url+'/v1/responses',json={'model':'fixture','stream':True},headers={'authorization':'Bearer fixture'})
                except httpx.RemoteProtocolError:interrupted=True
                if mode!='provider_failed':assert interrupted, 'partial stream looked like a clean success'
                runtime=app.state.personal_gateway_runtime
                for _ in range(100):
                    if saved and runtime.admission.active==0:break
                    await asyncio.sleep(.01)
                assert len(saved)==1
                assert saved[0].status_code==502, 'failed stream recorded as HTTP 200 success'
                assert not saved[0].content_complete
                if mode!='provider_failed':assert saved[0].usage_missing and saved[0].raw_usage=={}
                assert runtime.admission.active==runtime.ingress.active==runtime.db_limiter.borrowed_tokens==0
                assert await asyncio.wait_for(closed.wait(),1)
    asyncio.run(scenario())
