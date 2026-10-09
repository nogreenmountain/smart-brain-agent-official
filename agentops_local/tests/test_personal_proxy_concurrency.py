import asyncio
import contextlib
import threading
import uuid
from types import SimpleNamespace

import httpx
from fastapi import FastAPI
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from agentops.api import personal_gateway_proxy as proxy


def test_model_wait_releases_pool_and_thirty_requests_finish(monkeypatch):
    async def scenario():
        engine = create_engine('sqlite://', poolclass=QueuePool, pool_size=1,
                               max_overflow=3, pool_timeout=.2,
                               connect_args={'check_same_thread': False})
        saved, auth_threads, open_requests = [], [], set()
        local = threading.local()
        loop_thread = threading.get_ident()
        @contextlib.contextmanager
        def sessions():
            local.request_id = None
            with Session(engine) as orm:
                try:
                    yield orm
                    orm.commit()
                except BaseException:
                    orm.rollback()
                    raise
                finally:
                    open_requests.discard(local.request_id)
        def claims(request, orm):
            orm.execute(text('SELECT 1'))
            auth_threads.append(threading.get_ident())
            local.request_id = request.headers['x-test-request-id']
            open_requests.add(local.request_id)
            return SimpleNamespace(id=uuid.UUID(int=1), user_id=uuid.UUID(int=2),
                                   email='fixture@example.invalid', full_name='fixture')
        def persist(claim, batch, orm):
            orm.execute(text('SELECT 1'))
            saved.extend(batch.events)
            orm.commit()
        class Upstream:
            active = peak = 0
            async def request(self, *args, **kwargs):
                assert kwargs['headers']['x-test-request-id'] not in open_requests
                self.active += 1
                self.peak = max(self.peak, self.active)
                try:
                    await asyncio.sleep(.03)
                    return httpx.Response(200, json={'output_text': 'result', 'usage': {'input_tokens': 1, 'output_tokens': 1}})
                finally:
                    self.active -= 1
        upstream = Upstream()
        monkeypatch.setattr(proxy, '_gateway_claims', claims)
        monkeypatch.setattr(proxy, 'resolve_gateway_project_context', lambda *a, **k: None)
        monkeypatch.setattr(proxy, '_ingest_gateway_events', persist)
        app = FastAPI()
        app.state.personal_gateway_runtime = proxy.GatewayRuntime(
            client=upstream, session_factory=sessions, max_active=8,
            max_waiting=24, queue_timeout=2, db_concurrency=3)
        app.add_api_route('/v1/responses', proxy.proxy_request, methods=['POST'])
        heartbeats = 0
        stop = False
        async def heartbeat():
            nonlocal heartbeats
            while not stop:
                heartbeats += 1
                await asyncio.sleep(.002)
        task = asyncio.create_task(heartbeat())
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
                results = await asyncio.gather(*(client.post('/v1/responses', json={'model': 'fixture', 'input': str(i)}, headers={'authorization': 'Bearer fixture', 'x-test-request-id': str(i)}) for i in range(30)))
            assert all(r.status_code == 200 for r in results)
            assert len(saved) == 30
            assert len({event.request_id for event in saved}) == 30
            assert upstream.peak <= 8
            assert engine.pool.checkedout() == 0
            assert all(t != loop_thread for t in auth_threads)
            assert heartbeats > 15
            assert app.state.personal_gateway_runtime.admission.active == 0
            assert app.state.personal_gateway_runtime.admission.waiting == 0
        finally:
            stop = True
            await task
            engine.dispose()
    asyncio.run(scenario())


def test_fifo_queue_bounds_timeout_and_cancellation():
    from agentops.api.gateway_admission import AdmissionQueue, AdmissionRejected
    async def scenario():
        queue = AdmissionQueue(1, 2, .04)
        release = asyncio.Event()
        order = []
        async def job(n):
            async with queue.slot():
                order.append(n)
                if n == 0:
                    await release.wait()
        first = asyncio.create_task(job(0))
        await asyncio.sleep(0)
        cancelled = asyncio.create_task(job(1))
        next_job = asyncio.create_task(job(2))
        await asyncio.sleep(0)
        try:
            await job(3)
        except AdmissionRejected as error:
            assert error.reason == 'gateway_queue_full'
        else:
            raise AssertionError('unbounded queue')
        cancelled.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cancelled
        release.set()
        await asyncio.gather(first, next_job)
        assert order == [0, 2]
        async with queue.slot():
            try:
                await job(4)
            except AdmissionRejected as error:
                assert error.reason == 'gateway_queue_timeout'
            else:
                raise AssertionError('queue did not expire')
        assert queue.active == queue.waiting == 0
    asyncio.run(scenario())


def _runtime_fixture(monkeypatch, client, *, max_waiting=2, timeout=2):
    saved = []
    @contextlib.contextmanager
    def sessions():
        yield SimpleNamespace()
    monkeypatch.setattr(proxy, '_gateway_claims', lambda request, orm: SimpleNamespace(
        id=uuid.UUID(int=1), user_id=uuid.UUID(int=2), email='fixture@example.invalid', full_name='fixture'))
    monkeypatch.setattr(proxy, 'resolve_gateway_project_context', lambda *a, **k: None)
    monkeypatch.setattr(proxy, '_ingest_gateway_events', lambda claim, batch, orm: saved.extend(batch.events))
    app = FastAPI()
    app.state.personal_gateway_runtime = proxy.GatewayRuntime(client=client,
        session_factory=sessions, max_active=1, max_waiting=max_waiting, queue_timeout=timeout)
    return app, saved


def _request(app, path='/v1/responses', *, disconnected=None):
    sent = False
    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {'type': 'http.request', 'body': b'{"input":"fixture"}', 'more_body': False}
        if disconnected and disconnected.is_set():
            return {'type': 'http.disconnect'}
        await asyncio.sleep(30)
    return Request({'type': 'http', 'method': 'POST', 'path': path,
        'query_string': b'', 'headers': [(b'authorization', b'Bearer fixture')], 'app': app}, receive)


def test_queued_disconnect_never_reaches_model(monkeypatch):
    async def scenario():
        started, release, disconnected = asyncio.Event(), asyncio.Event(), asyncio.Event()
        class Client:
            calls = 0
            async def request(self, *a, **kw):
                self.calls += 1
                started.set()
                await release.wait()
                return httpx.Response(200, json={'output_text': 'fixture'})
        client = Client()
        app, saved = _runtime_fixture(monkeypatch, client)
        first = asyncio.create_task(proxy.proxy_request(_request(app)))
        await started.wait()
        queued = asyncio.create_task(proxy.proxy_request(_request(app, disconnected=disconnected)))
        await asyncio.sleep(.02)
        disconnected.set()
        await asyncio.sleep(.15)
        assert queued.done(), 'disconnected queue item must release before a slot opens'
        try:
            await queued
        except HTTPException as error:
            assert error.status_code == 499
        release.set()
        await first
        assert client.calls == 1 and len(saved) == 1
        assert app.state.personal_gateway_runtime.admission.active == 0
    asyncio.run(scenario())


def test_repeated_cancel_waits_for_database_thread_to_close():
    async def scenario():
        started, release = threading.Event(), threading.Event()
        closed = []
        @contextlib.contextmanager
        def sessions():
            try:
                yield None
            finally:
                closed.append(True)
        def blocked(orm):
            started.set()
            assert release.wait(2)
        runtime = proxy.GatewayRuntime(client=None, session_factory=sessions)
        task = asyncio.create_task(runtime.database(blocked))
        while not started.is_set():
            await asyncio.sleep(.002)
        task.cancel()
        await asyncio.sleep(.01)
        task.cancel()
        await asyncio.sleep(.01)
        premature = task.done()
        release.set()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert not premature
        assert closed == [True]
        assert runtime.db_limiter.borrowed_tokens == 0
    asyncio.run(scenario())


def test_queue_rechecks_revoked_key_before_upstream(monkeypatch):
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        class Client:
            calls = 0
            async def request(self, *a, **kw):
                self.calls += 1
                started.set()
                await release.wait()
                return httpx.Response(200, json={'output_text': 'fixture'})
        client = Client()
        app, saved = _runtime_fixture(monkeypatch, client)
        original = proxy._gateway_claims
        revoked = False
        def claims(request, orm):
            if revoked:
                raise HTTPException(401, 'revoked')
            return original(request, orm)
        monkeypatch.setattr(proxy, '_gateway_claims', claims)
        first = asyncio.create_task(proxy.proxy_request(_request(app)))
        await started.wait()
        queued = asyncio.create_task(proxy.proxy_request(_request(app)))
        await asyncio.sleep(.01)
        revoked = True
        release.set()
        await first
        try:
            await queued
        except HTTPException as error:
            assert error.status_code == 401
        else:
            raise AssertionError('revoked key forwarded')
        assert client.calls == 1 and len(saved) == 1
    asyncio.run(scenario())


def test_http_queue_status_is_retryable_and_upstream_failure_releases_slot(monkeypatch):
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()
        class Client:
            fail = False
            async def request(self, *a, **kw):
                if self.fail:
                    raise httpx.ReadTimeout('fixture')
                started.set()
                await release.wait()
                return httpx.Response(200, content=b'data: {"usage":{"input_tokens":1,"output_tokens":1}}\n\n', headers={'content-type':'text/event-stream'})
        upstream = Client()
        app, saved = _runtime_fixture(monkeypatch, upstream, max_waiting=0)
        app.add_api_route('/v1/responses', proxy.proxy_request, methods=['POST'])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
            first = asyncio.create_task(client.post('/v1/responses', headers={'authorization':'Bearer fixture'}, json={'input':'fixture'}))
            await started.wait()
            rejected = await client.post('/v1/responses', headers={'authorization':'Bearer fixture'}, json={'input':'fixture'})
            assert rejected.status_code == 503
            assert rejected.headers['retry-after'] == '3'
            assert rejected.json()['detail'] == 'gateway_queue_full'
            release.set()
            response = await first
            assert response.headers['content-type'].startswith('text/event-stream')
            assert response.content.startswith(b'data:')
            upstream.fail = True
            failed = await client.post('/v1/responses', headers={'authorization':'Bearer fixture'}, json={'input':'fixture'})
            assert failed.status_code == 502
            assert saved[-1].status_code == 502 and saved[-1].usage_missing
            assert app.state.personal_gateway_runtime.admission.active == 0
    asyncio.run(scenario())


def test_application_lifespan_closes_shared_client(monkeypatch):
    async def scenario():
        instances = []
        class Client:
            closed = False
            def __init__(self, **kw):
                self.limits = kw['limits']
                instances.append(self)
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                self.closed = True
        monkeypatch.setattr(proxy.httpx, 'AsyncClient', Client)
        app = FastAPI()
        async with proxy.gateway_lifespan(app):
            assert app.state.personal_gateway_runtime.client is instances[0]
            assert instances[0].limits.max_connections == 8
        assert len(instances) == 1 and instances[0].closed
        assert not hasattr(app.state, 'personal_gateway_runtime')
    asyncio.run(scenario())


def test_active_disconnect_cancels_model_and_records_unknown_usage(monkeypatch):
    async def scenario():
        started, disconnected, cancelled = asyncio.Event(), asyncio.Event(), asyncio.Event()
        class Client:
            async def request(self, *a, **kw):
                started.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    cancelled.set()
        app, saved = _runtime_fixture(monkeypatch, Client())
        task = asyncio.create_task(proxy.proxy_request(_request(app, disconnected=disconnected)))
        await started.wait()
        disconnected.set()
        await asyncio.sleep(.15)
        assert task.done()
        try:
            await task
        except HTTPException as error:
            assert error.status_code == 499
        assert cancelled.is_set()
        assert len(saved) == 1 and saved[0].status_code == 499 and saved[0].usage_missing
        assert app.state.personal_gateway_runtime.admission.active == 0
    asyncio.run(scenario())


def test_oversized_request_is_rejected_before_model(monkeypatch):
    async def scenario():
        class Client:
            async def request(self, *a, **kw):
                raise AssertionError('oversized request forwarded')
        app, saved = _runtime_fixture(monkeypatch, Client())
        app.state.personal_gateway_runtime.max_body_bytes = 4
        try:
            await proxy.proxy_request(_request(app))
        except HTTPException as error:
            assert error.status_code == 413
        else:
            raise AssertionError('unbounded request memory')
        assert saved == []
        assert app.state.personal_gateway_runtime.admission.active == 0
    asyncio.run(scenario())


def test_immediate_response_finishes_disconnect_watcher(monkeypatch):
    async def scenario():
        class Client:
            async def request(self, *a, **kw):
                return httpx.Response(200, json={'output_text':'instant'})
        app, saved = _runtime_fixture(monkeypatch, Client())
        disconnected = asyncio.Event()
        task = asyncio.create_task(proxy.proxy_request(_request(app, disconnected=disconnected)))
        await asyncio.sleep(.2)
        completed = task.done()
        disconnected.set()
        result = await asyncio.wait_for(task, 1)
        assert completed, 'instant upstream response stalled during disconnect watcher cleanup'
        assert result.status_code == 200 and len(saved) == 1
    asyncio.run(scenario())
