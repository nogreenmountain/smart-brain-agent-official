"""Real gateway endpoints and PostgreSQL; only browser-session decoding is synthetic.

No production credentials, model endpoint, or database are permitted in this fixture.
"""
import asyncio
import contextlib
import os
import socket
from types import SimpleNamespace
import uuid

import httpx
import pytest
import uvicorn
from fastapi import HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from agentops.api import personal_gateway_proxy as proxy
from agentops.api import personal_gateway_scope as scope
from agentops.api.routes.v4 import ai_gateway as route
from agentops.auth.middleware import AuthenticatedRoute

DSN = os.getenv('SB_REGISTRATION_TEST_DSN')
pytestmark = pytest.mark.skipif(not DSN, reason='isolated registration PostgreSQL not configured')
OLD, NEW, THIRD = (uuid.UUID(int=x) for x in (101, 102, 103))


@contextlib.asynccontextmanager
async def serve(app):
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.setblocking(False)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(500):
            if server.started:
                break
            if task.done():
                await task
            await asyncio.sleep(.01)
        assert server.started
        yield f'http://127.0.0.1:{port}'
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, 10)
        sock.close()


def test_new_account_key_lifecycle_and_live_boundaries(monkeypatch):
    engine = create_engine(DSN, pool_size=1, max_overflow=3,
                           connect_args={'options': '-c statement_timeout=5000 -c lock_timeout=2000'})
    assert engine.url.database.startswith('sb_registration_test_')
    assert engine.url.host == '127.0.0.1'
    with engine.begin() as conn:
        conn.exec_driver_sql('''
          CREATE SCHEMA auth;
          CREATE TABLE auth.users(id uuid PRIMARY KEY,email text,deleted_at timestamptz,is_anonymous boolean DEFAULT false,banned_until timestamptz);
          CREATE TABLE public.users(id uuid PRIMARY KEY,is_active boolean DEFAULT true,full_name text,is_system_admin boolean DEFAULT false);
          CREATE TABLE public.ai_gateway_keys(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),user_id uuid NOT NULL REFERENCES public.users,key_hash text NOT NULL UNIQUE,key_prefix text NOT NULL,label text NOT NULL,is_active boolean DEFAULT true,created_at timestamptz DEFAULT now(),last_used_at timestamptz,revoked_at timestamptz,hidden_at timestamptz);
          CREATE TABLE public.ai_gateway_key_allowances(user_id uuid PRIMARY KEY,max_active_keys integer NOT NULL);
        ''')
        for uid in (OLD, NEW, THIRD):
            conn.execute(text("INSERT INTO auth.users(id,email) VALUES (:uid,'synthetic@example.invalid')"), {'uid': str(uid)})
            conn.execute(text("INSERT INTO public.users(id,full_name) VALUES (:uid,'Synthetic member')"), {'uid': str(uid)})
        conn.execute(text("INSERT INTO public.ai_gateway_keys(user_id,key_hash,key_prefix,label) VALUES (:uid,:hash,'synthetic','Existing')"),
                     {'uid': str(OLD), 'hash': route.hash_api_key('synthetic-existing-key')})
    @contextlib.contextmanager
    def sessions():
        with Session(engine) as orm:
            try:
                yield orm
                orm.commit()
            except BaseException:
                orm.rollback()
                raise
    def dependency():
        with sessions() as orm:
            yield orm
    def synthetic_session(self, request):
        user = request.headers.get('x-test-user')
        if not user:
            raise HTTPException(401, 'Authentication required')
        return SimpleNamespace(user_id=uuid.UUID(user))
    calls = []
    async def synthetic_response(request: Request):
        # The real async scope has already validated the Key and current account.
        calls.append(str(request.state.gateway_claim.user_id))
        return {'synthetic': True}
    monkeypatch.setattr(AuthenticatedRoute, '_get_session', synthetic_session)
    monkeypatch.setattr(proxy, 'proxy_request', synthetic_response)
    monkeypatch.delenv('SB_LLM_GATEWAY_MANAGEMENT_ENABLED', raising=False)
    monkeypatch.setenv('SB_GATEWAY_ALLOWED_USER_IDS', str(OLD))
    async def scenario():
        app = scope.build_app(route)
        app.dependency_overrides[route.get_orm_session] = dependency
        async with serve(app) as base, httpx.AsyncClient(base_url=base, timeout=10) as client:
            app.state.personal_gateway_runtime.session_factory = sessions
            headers = {'x-test-user': str(NEW)}
            assert (await client.get('/v4/ai-gateway/keys')).status_code == 401
            assert (await client.get('/v4/ai-gateway/keys', headers=headers)).json() == []
            created = await client.post('/v4/ai-gateway/keys', headers=headers, json={'label': 'New member fixture'})
            assert created.status_code == 200
            key = created.json()
            assert key['max_active_keys'] == 1
            listed = (await client.get('/v4/ai-gateway/keys', headers=headers)).json()
            assert len(listed) == 1 and listed[0]['id'] == key['id'] and listed[0]['key'] is None
            assert (await client.post('/v4/ai-gateway/keys', headers=headers, json={})).status_code == 409
            # Existing account and Key continue to work; new Key authenticates to proxy.
            bearer = {'authorization': 'Bearer ' + key['key']}
            assert (await client.post('/v1/responses', headers=bearer, json={})).status_code == 200
            assert (await client.post('/v1/responses', headers={'authorization': 'Bearer synthetic-existing-key'}, json={})).status_code == 200
            assert (await client.post('/v1/responses', headers={'authorization': 'Bearer invalid'}, json={})).status_code == 401
            assert calls == [str(NEW), str(OLD)]
            other = {'x-test-user': str(THIRD)}
            assert (await client.get('/v4/ai-gateway/keys', headers=other)).json() == []
            assert (await client.post('/v4/ai-gateway/keys/' + key['id'] + '/revoke', headers=other)).status_code == 404
            for table, field, value, reset in [
                ('auth.users', 'banned_until', "now()+interval '1 hour'", 'NULL'),
                ('auth.users', 'deleted_at', 'now()', 'NULL'),
                ('auth.users', 'is_anonymous', 'true', 'false'),
                ('public.users', 'is_active', 'false', 'true'),
            ]:
                with engine.begin() as conn:
                    conn.execute(text(f'UPDATE {table} SET {field}={value} WHERE id=:uid'), {'uid': str(NEW)})
                assert (await client.get('/v4/ai-gateway/keys', headers=headers)).status_code == 403
                assert (await client.post('/v4/ai-gateway/keys', headers=headers, json={})).status_code == 403
                assert (await client.post('/v1/responses', headers=bearer, json={})).status_code in (401, 403)
                with engine.begin() as conn:
                    conn.execute(text(f'UPDATE {table} SET {field}={reset} WHERE id=:uid'), {'uid': str(NEW)})
            assert calls == [str(NEW), str(OLD)]
            # A new member racing six create requests still receives one default slot.
            concurrent = await asyncio.gather(*[client.post('/v4/ai-gateway/keys', headers=other, json={}) for _ in range(6)])
            assert sorted(r.status_code for r in concurrent) == [200, 409, 409, 409, 409, 409]
            assert (await client.post('/v4/ai-gateway/keys/' + key['id'] + '/revoke', headers=headers)).status_code == 200
            assert (await client.post('/v1/responses', headers=bearer, json={})).status_code == 401
            assert (await client.post('/v4/ai-gateway/keys', headers=headers, json={})).status_code == 200
            # No profile and unknown auth identity must not create any Key.
            missing = {'x-test-user': str(uuid.UUID(int=999))}
            assert (await client.post('/v4/ai-gateway/keys', headers=missing, json={})).status_code == 403
            health = (await client.get('/health')).json()
            assert health['membership_policy'] == 'registered_active' and health['member_count'] is None
            assert health['concurrency']['max_active'] == 8
            assert health['concurrency']['max_waiting'] == 24
            assert health['concurrency']['database_limit'] == 3
            assert engine.pool.checkedout() == 0
            with engine.connect() as conn:
                assert conn.execute(text('SELECT count(*) FROM public.ai_gateway_keys')).scalar_one() == 4
                assert conn.execute(text('SELECT count(*) FROM public.ai_gateway_keys WHERE is_active')).scalar_one() == 3
    try:
        asyncio.run(scenario())
    finally:
        engine.dispose()
