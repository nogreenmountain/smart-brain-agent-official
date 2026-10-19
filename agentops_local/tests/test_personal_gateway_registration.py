"""Exercise both gateway scopes with real account SQL; authentication is synthetic."""
import contextlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import APIRouter, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
OLD = '11111111-1111-4111-8111-111111111111'
NEW = '22222222-2222-4222-8222-222222222222'


@pytest.fixture(params=['agentops_local/api', 'deploy/personal-proxy-concurrency'])
def harness(request, monkeypatch):
    path = ROOT / request.param
    spec = importlib.util.spec_from_file_location('registration_scope', path / 'personal_gateway_scope.py')
    scope = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scope)
    engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
    with engine.begin() as conn:
        conn.connection.driver_connection.create_function('now', 0, lambda: '2026-10-19T00:00:00')
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS auth")
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS public")
        conn.exec_driver_sql('CREATE TABLE auth.users(id text PRIMARY KEY, deleted_at text, is_anonymous boolean, banned_until text)')
        conn.exec_driver_sql('CREATE TABLE public.users(id text PRIMARY KEY, is_active boolean)')
        for uid in (OLD, NEW):
            conn.execute(text('INSERT INTO auth.users(id) VALUES (:id)'), {'id': uid})
            conn.execute(text('INSERT INTO public.users(id,is_active) VALUES (:id,true)'), {'id': uid})
    def sessions():
        with Session(engine) as orm:
            yield orm
    def session_user(request):
        user = request.headers.get('x-test-user')
        if not user:
            raise HTTPException(401, 'Authentication required')
        return user
    router = APIRouter()
    @router.get('/ai-gateway/keys')
    def keys():
        return []
    @router.get('/ai-gateway/key-quota')
    def quota():
        return {'max_active_keys': 3}
    @router.post('/ai-gateway/keys', status_code=201)
    def create():
        return {'synthetic': True}
    device_router = APIRouter()
    @device_router.get('/devices/claim')
    def claim():
        return {'synthetic': True}
    route = SimpleNamespace(router=router, device_router=device_router, get_orm_session=sessions,
                            _session_user=session_user, _gateway_claims=lambda req, orm: SimpleNamespace(user_id=session_user(req)))
    proxy = ModuleType('agentops.api.personal_gateway_proxy')
    @contextlib.asynccontextmanager
    async def lifespan(app):
        yield
    async def authorize(req, require):
        with Session(engine) as orm:
            require(session_user(req), orm)
    async def proxy_request(request: Request):
        return {'synthetic': True}
    proxy.gateway_lifespan = lifespan
    proxy.authorize_proxy_scope = authorize
    proxy.proxy_request = proxy_request
    monkeypatch.setitem(sys.modules, 'agentops.api.personal_gateway_proxy', proxy)
    yield SimpleNamespace(scope=scope, route=route, engine=engine, path=path)
    engine.dispose()


def test_new_registered_user_can_list_quota_create_and_use_key(harness):
    with TestClient(harness.scope.build_app(harness.route)) as client:
        headers = {'x-test-user': NEW}
        assert client.get('/v4/ai-gateway/keys', headers=headers).status_code == 200
        assert client.get('/v4/ai-gateway/key-quota', headers=headers).status_code == 200
        assert client.post('/v4/ai-gateway/keys', headers=headers).status_code == 201
        assert client.post('/v1/responses', headers=headers).status_code == 200
        assert client.get('/v4/devices/claim', headers=headers).status_code == 200
        health = client.get('/health').json()
        assert health['membership_policy'] == 'registered_active'
        assert health['member_count'] is None
        assert client.get('/v4/ai-gateway/keys', headers={'x-test-user': OLD}).status_code == 200


@pytest.mark.parametrize('change', [
    "UPDATE public.users SET is_active=false",
    "UPDATE auth.users SET banned_until='2099-01-01'",
    "UPDATE auth.users SET deleted_at='2026-10-18'",
    'UPDATE auth.users SET is_anonymous=true',
    'DELETE FROM auth.users',
    'DELETE FROM public.users',
])
def test_unavailable_accounts_denied_for_browser_device_and_proxy(harness, change):
    with harness.engine.begin() as conn:
        conn.exec_driver_sql(change)
    with TestClient(harness.scope.build_app(harness.route)) as client:
        for method, path in [('GET', '/v4/ai-gateway/keys'), ('POST', '/v4/ai-gateway/keys'),
                             ('GET', '/v4/devices/claim'), ('POST', '/v1/responses')]:
            reply = client.request(method, path, headers={'x-test-user': NEW})
            assert reply.status_code == 403
            assert reply.headers['cache-control'] == 'no-store'


def test_anonymous_denied_and_expired_ban_allowed(harness):
    with harness.engine.begin() as conn:
        conn.exec_driver_sql("UPDATE auth.users SET banned_until='2020-01-01'")
    with TestClient(harness.scope.build_app(harness.route)) as client:
        assert client.get('/v4/ai-gateway/keys').status_code == 401
        assert client.post('/v1/responses').status_code == 401
        assert client.get('/v4/ai-gateway/keys', headers={'x-test-user': NEW}).status_code == 200


def test_explicit_release_allowlist_remains_restrictive(harness):
    with TestClient(harness.scope.build_app(harness.route, {OLD})) as client:
        assert client.get('/v4/ai-gateway/keys', headers={'x-test-user': NEW}).status_code == 403
        assert client.get('/v4/ai-gateway/keys', headers={'x-test-user': OLD}).status_code == 200


def test_production_entry_ignores_stale_release_members(harness, monkeypatch):
    route_module = ModuleType('agentops.api.routes.v4')
    route_module.ai_gateway = harness.route
    monkeypatch.setitem(sys.modules, 'agentops.api.routes.v4', route_module)
    monkeypatch.setitem(sys.modules, 'agentops.api.personal_gateway_scope', harness.scope)
    monkeypatch.setenv('SB_GATEWAY_ALLOWED_USER_IDS', OLD)
    spec = importlib.util.spec_from_file_location('registration_app', harness.path / 'personal_gateway_app.py')
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    with TestClient(entry.app) as client:
        assert client.get('/v4/ai-gateway/keys', headers={'x-test-user': NEW}).status_code == 200
