"""Production approval routes against an isolated PostgreSQL schema.

Only browser session decoding is synthetic; no production account or Key is used.
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
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from agentops.api.personal_gateway_scope import build_app
from agentops.api.routes.v4 import ai_gateway as route
from agentops.auth.middleware import AuthenticatedRoute

DSN = os.getenv('SB_APPROVAL_TEST_DSN')
pytestmark = pytest.mark.skipif(not DSN, reason='isolated approval PostgreSQL not configured')
REVIEWER, MEMBER, OTHER_ADMIN = (uuid.UUID(int=x) for x in (201, 202, 203))


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


@pytest.fixture
def environment(monkeypatch):
    engine = create_engine(DSN, pool_size=1, max_overflow=3,
                           connect_args={'options': '-c statement_timeout=5000 -c lock_timeout=2000'})
    assert engine.url.database.startswith('sb_approval_test_') and engine.url.host == '127.0.0.1'
    with engine.begin() as db:
        db.exec_driver_sql('''
            DROP SCHEMA IF EXISTS auth CASCADE;
            DROP TABLE IF EXISTS ai_gateway_key_requests,ai_gateway_key_allowances,ai_gateway_keys,users CASCADE;
            CREATE SCHEMA auth;
            CREATE TABLE auth.users(id uuid PRIMARY KEY,email text,deleted_at timestamptz,
                is_anonymous boolean DEFAULT false,banned_until timestamptz);
            CREATE TABLE public.users(id uuid PRIMARY KEY,is_active boolean DEFAULT true,
                full_name text,is_system_admin boolean DEFAULT false);
            CREATE TABLE ai_gateway_keys(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id uuid NOT NULL REFERENCES users,key_hash text NOT NULL UNIQUE,
                key_prefix text NOT NULL,label text NOT NULL,is_active boolean DEFAULT true,
                created_at timestamptz DEFAULT now(),last_used_at timestamptz,revoked_at timestamptz,hidden_at timestamptz);
            CREATE TABLE ai_gateway_key_allowances(user_id uuid PRIMARY KEY REFERENCES users,
                max_active_keys integer NOT NULL DEFAULT 1 CHECK(max_active_keys BETWEEN 1 AND 100),
                updated_at timestamptz NOT NULL DEFAULT now());
            CREATE TABLE ai_gateway_key_requests(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id uuid NOT NULL REFERENCES users,reviewer_id uuid REFERENCES users,
                requested_limit integer CHECK(requested_limit BETWEEN 2 AND 100),
                reason text NOT NULL CHECK(length(btrim(reason)) BETWEEN 1 AND 2000),
                status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','cancelled')),
                review_comment text NOT NULL DEFAULT '',created_at timestamptz NOT NULL DEFAULT now(),
                reviewed_at timestamptz,reviewed_by_user_id uuid REFERENCES users,
                requested_total integer NOT NULL CHECK(requested_total>=2),reviewed_by uuid);
        ''')
        for uid in (REVIEWER, MEMBER, OTHER_ADMIN):
            email = 'hanshangbo@local.dev' if uid == REVIEWER else 'synthetic@example.invalid'
            db.execute(text('INSERT INTO auth.users(id,email) VALUES (:id,:email)'), {'id': uid, 'email': email})
            db.execute(text("INSERT INTO users(id,full_name,is_system_admin) VALUES (:id,'Synthetic member',:admin)"),
                       {'id': uid, 'admin': uid != MEMBER})

    def dependency():
        with Session(engine) as db:
            try:
                yield db
            finally:
                db.rollback()

    def synthetic_session(self, request):
        value = request.headers.get('x-test-user')
        if not value:
            raise HTTPException(401, 'Authentication required')
        return SimpleNamespace(user_id=uuid.UUID(value))

    monkeypatch.setattr(AuthenticatedRoute, '_get_session', synthetic_session)
    monkeypatch.delenv('SB_LLM_GATEWAY_MANAGEMENT_ENABLED', raising=False)
    app = build_app(route)
    app.dependency_overrides[route.get_orm_session] = dependency
    try:
        yield engine, app
    finally:
        engine.dispose()


@pytest.mark.parametrize('decision', ['approve', 'reject'])
@pytest.mark.parametrize('comment', [None, '', '   ', '  reviewed  '], ids=['omitted', 'empty', 'spaces', 'text'])
def test_optional_review_comment_and_resulting_quota(environment, decision, comment):
    engine, app = environment

    async def scenario():
        async with serve(app) as base, httpx.AsyncClient(base_url=base, timeout=10) as client:
            member = {'x-test-user': str(MEMBER)}
            reviewer = {'x-test-user': str(REVIEWER)}
            assert (await client.post('/v4/ai-gateway/keys', headers=member, json={})).status_code == 200
            submitted = await client.post('/v4/ai-gateway/key-requests', headers=member,
                                          json={'requested_total': 2, 'reason': 'Synthetic second device'})
            assert submitted.status_code == 201
            request_id = submitted.json()['id']
            body = {'decision': decision}
            if comment is not None:
                body['comment'] = comment
            response = await client.post(f'/v4/ai-gateway/key-requests/{request_id}/review',
                                         headers=reviewer, json=body)
            assert response.status_code == 200
            expected = 'approved' if decision == 'approve' else 'rejected'
            assert response.json()['status'] == expected
            assert response.json()['review_comment'] == (comment or '').strip()
            with engine.connect() as db:
                row = db.execute(text('SELECT status,review_comment,reviewed_by,reviewed_at FROM ai_gateway_key_requests')).one()
                assert (row.status, row.review_comment, row.reviewed_by) == (expected, (comment or '').strip(), REVIEWER)
                assert row.reviewed_at is not None
                allowance = db.execute(text('SELECT max_active_keys FROM ai_gateway_key_allowances WHERE user_id=:id'), {'id': MEMBER}).scalar()
                assert allowance == (2 if decision == 'approve' else None)
            second = await client.post('/v4/ai-gateway/keys', headers=member, json={})
            assert second.status_code == (200 if decision == 'approve' else 409)
            assert (await client.post('/v4/ai-gateway/keys', headers=member, json={})).status_code == 409
            replay = await client.post(f'/v4/ai-gateway/key-requests/{request_id}/review', headers=reviewer, json=body)
            assert replay.status_code == 409
            assert (await client.get('/v4/ai-gateway/key-requests/review', headers=reviewer)).json() == []
    asyncio.run(scenario())


def test_review_permissions_and_parallel_decision(environment):
    engine, app = environment

    async def scenario():
        async with serve(app) as base, httpx.AsyncClient(base_url=base, timeout=10) as client:
            member = {'x-test-user': str(MEMBER)}
            reviewer = {'x-test-user': str(REVIEWER)}
            submitted = await client.post('/v4/ai-gateway/key-requests', headers=member,
                                          json={'requested_total': 2, 'reason': 'Synthetic request'})
            url = '/v4/ai-gateway/key-requests/' + submitted.json()['id'] + '/review'
            body = {'decision': 'approve', 'comment': 'reviewed'}
            assert (await client.post(url, json=body)).status_code == 401
            for headers in (member, {'x-test-user': str(OTHER_ADMIN)}):
                assert (await client.post(url, headers=headers, json=body)).status_code == 403
            responses = await asyncio.gather(*[client.post(url, headers=reviewer, json=body) for _ in range(2)])
            assert sorted(r.status_code for r in responses) == [200, 409]
            with engine.connect() as db:
                assert db.execute(text('SELECT max_active_keys FROM ai_gateway_key_allowances')).scalar_one() == 2
                assert db.execute(text('SELECT count(*) FROM ai_gateway_keys')).scalar_one() == 0
    asyncio.run(scenario())


def test_review_write_failure_keeps_pending_and_does_not_grant_quota(environment):
    engine, app = environment
    with engine.begin() as db:
        db.exec_driver_sql("""
            CREATE FUNCTION reject_test_review() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN RAISE EXCEPTION 'synthetic review failure'; END $$;
            CREATE TRIGGER reject_test_review BEFORE UPDATE ON ai_gateway_key_requests
            FOR EACH ROW EXECUTE FUNCTION reject_test_review();
        """)

    async def scenario():
        async with serve(app) as base, httpx.AsyncClient(base_url=base, timeout=10) as client:
            submitted = await client.post('/v4/ai-gateway/key-requests', headers={'x-test-user': str(MEMBER)},
                                          json={'requested_total': 2, 'reason': 'Synthetic rollback'})
            url = '/v4/ai-gateway/key-requests/' + submitted.json()['id'] + '/review'
            reviewer = {'x-test-user': str(REVIEWER)}
            response = await client.post(url, headers=reviewer, json={'decision': 'approve'})
            assert response.status_code == 500
            with engine.connect() as db:
                assert db.execute(text('SELECT count(*) FROM ai_gateway_key_allowances')).scalar_one() == 0
                row = db.execute(text('SELECT status,reviewed_at,reviewed_by FROM ai_gateway_key_requests')).one()
                assert tuple(row) == ('pending', None, None)
            with engine.begin() as db:
                db.exec_driver_sql('DROP TRIGGER reject_test_review ON ai_gateway_key_requests; DROP FUNCTION reject_test_review()')
            assert (await client.post(url, headers=reviewer, json={'decision': 'approve'})).status_code == 200
    asyncio.run(scenario())


def test_approval_does_not_reduce_an_existing_allowance(environment):
    engine, app = environment
    with engine.begin() as db:
        db.execute(text('INSERT INTO ai_gateway_key_allowances(user_id,max_active_keys) VALUES (:id,5)'), {'id': MEMBER})

    async def scenario():
        async with serve(app) as base, httpx.AsyncClient(base_url=base, timeout=10) as client:
            submitted = await client.post('/v4/ai-gateway/key-requests', headers={'x-test-user': str(MEMBER)},
                                          json={'requested_total': 2, 'reason': 'Synthetic prior approval'})
            response = await client.post('/v4/ai-gateway/key-requests/' + submitted.json()['id'] + '/review',
                                         headers={'x-test-user': str(REVIEWER)}, json={'decision': 'approve'})
            assert response.status_code == 200
            with engine.connect() as db:
                assert db.execute(text('SELECT max_active_keys FROM ai_gateway_key_allowances')).scalar_one() == 5
    asyncio.run(scenario())
