"""Real loopback HTTP + isolated PG; synthetic upstream, no production credentials."""
import asyncio
import contextlib
import json
import os
import socket
import uuid

import httpx
import pytest
import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import StreamingResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from agentops.api import personal_gateway_proxy as proxy
from agentops.api import personal_gateway_scope as scope
from agentops.api.routes.v4 import ai_gateway as route
import test_request_project_pg as schema
import test_request_project_proxy as helper

pytestmark = pytest.mark.skipif(not schema.DSN, reason='isolated PostgreSQL not configured')
UID, PID = helper.UID, helper.PID
SECOND, EXCLUDED = uuid.UUID(int=22), uuid.UUID(int=33)
KEY = uuid.UUID(int=9)


@contextlib.asynccontextmanager
async def serve(app):
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(500):
            if server.started:
                break
            if task.done():
                await task
                raise AssertionError('HTTP server exited')
            await asyncio.sleep(.01)
        assert server.started
        yield f'http://127.0.0.1:{port}'
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, 10)
        sock.close()


def test_real_http_pg_staircase_scope_and_queue(monkeypatch):
    seed = schema.engine.__wrapped__()
    setup_engine = next(seed)
    with setup_engine.begin() as conn:
        conn.exec_driver_sql('''
          CREATE SCHEMA auth;
          CREATE TABLE auth.users(id uuid PRIMARY KEY,email text,deleted_at timestamptz,is_anonymous boolean DEFAULT false,banned_until timestamptz);
          ALTER TABLE public.users ADD COLUMN is_active boolean DEFAULT true, ADD COLUMN full_name text;
          ALTER TABLE public.ai_gateway_keys ADD COLUMN user_id uuid, ADD COLUMN key_hash text, ADD COLUMN is_active boolean DEFAULT true;
        ''')
        for uid in [UID, SECOND, EXCLUDED]:
            conn.execute(text('INSERT INTO public.users(id,full_name) VALUES (:uid,\'合成员工\') ON CONFLICT(id) DO UPDATE SET full_name=excluded.full_name'), {'uid':str(uid)})
            conn.execute(text('INSERT INTO auth.users(id,email) VALUES (:uid,\'synthetic@example.invalid\')'), {'uid':str(uid)})
            conn.execute(text('INSERT INTO public.ai_gateway_keys(id,user_id,key_hash) VALUES (:kid,:uid,:hash)'), {'kid':str(KEY if uid==UID else uid),'uid':str(uid),'hash':route.hash_api_key('synthetic-'+str(uid))})
    engine = create_engine(schema.DSN, pool_size=1, max_overflow=3, pool_timeout=.3,
                           connect_args={'application_name':'concurrency-candidate'})
    @contextlib.contextmanager
    def sessions():
        with Session(engine) as orm:
            try:
                yield orm
                orm.commit()
            except BaseException:
                orm.rollback()
                raise

    async def scenario():
        model = FastAPI()
        gate = asyncio.Event()
        gate.set()
        active = peak = calls = 0
        @model.post('/v1/responses')
        async def response(request: Request):
            nonlocal active, peak, calls
            assert 'authorization' not in request.headers
            calls += 1
            active += 1
            peak = max(peak, active)
            try:
                await gate.wait()
                await asyncio.sleep(.02)
                if (await request.json()).get('stream'):
                    async def chunks():
                        yield b'data: {"type":"response.output_text.delta","delta":"synthetic"}\n\n'
                        await asyncio.sleep(.12)
                        yield b'data: {"type":"response.completed","response":{"model":"fixture","output_text":"synthetic result","usage":{"input_tokens":2,"output_tokens":1}}}\n\n'
                    return StreamingResponse(chunks(),media_type='text/event-stream')
                return {'model':'fixture', 'output_text':'简短合成结果', 'usage':{'input_tokens':2,'output_tokens':1}}
            finally:
                active -= 1
        app = scope.build_app(route, {str(UID), str(SECOND)})
        async with serve(model) as upstream:
            monkeypatch.setattr(proxy, 'UPSTREAM_BASE_URL', upstream)
            async with serve(app) as base, httpx.AsyncClient(base_url=base, timeout=10) as client:
                runtime = app.state.personal_gateway_runtime
                runtime.session_factory = sessions
                health = (await client.get('/health')).json()
                assert health['member_count']==2 and health['concurrency']['database_limit']==3
                async def send(uid=UID):
                    return await client.post('/v1/responses', headers={'authorization':'Bearer synthetic-'+str(uid),'x-smartbrain-project-id':PID},
                        json={'model':'fixture','input':'测试提示词'})
                assert (await client.post('/v1/responses', json={})).status_code==401
                assert (await send(EXCLUDED)).status_code==403
                for field, value in [('banned_until', 'now()+interval \'1 hour\''),('deleted_at','now()'),('is_anonymous','true')]:
                    with setup_engine.begin() as conn:
                        conn.exec_driver_sql(f'UPDATE auth.users SET {field}={value} WHERE id=\'{UID}\'')
                    assert (await send()).status_code==403
                    with setup_engine.begin() as conn:
                        conn.exec_driver_sql(f'UPDATE auth.users SET {field}='+('false' if field=='is_anonymous' else 'NULL')+f' WHERE id=\'{UID}\'')
                with setup_engine.begin() as conn:
                    conn.execute(text('UPDATE public.users SET is_active=false WHERE id=:uid'), {'uid':str(UID)})
                assert (await send()).status_code==401
                with setup_engine.begin() as conn:
                    conn.execute(text('UPDATE public.users SET is_active=true WHERE id=:uid'), {'uid':str(UID)})
                assert calls==0
                results = []
                for n in [5,10,20,30]:
                    gate.clear()
                    tasks = [asyncio.create_task(send()) for _ in range(n)]
                    for _ in range(1000):
                        if active==min(n,8) and runtime.admission.waiting==max(n-8,0) and runtime.db_limiter.borrowed_tokens==0:
                            break
                        await asyncio.sleep(.005)
                    assert active==min(n,8) and runtime.admission.waiting==max(n-8,0)
                    assert engine.pool.checkedout()==0, 'model/queue wait retained a DB connection'
                    with setup_engine.connect() as conn:
                        assert conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name='concurrency-candidate' AND state='idle in transaction'")).scalar_one()==0
                    assert (await client.get('/health')).status_code==200
                    gate.set()
                    replies = await asyncio.gather(*tasks)
                    assert all(r.status_code==200 and r.json()['output_text']=='简短合成结果' for r in replies)
                    assert runtime.admission.active==runtime.admission.waiting==0
                    results.append({'concurrent':n,'completed':len(replies),'db_held_during_wait':0})
                assert calls==65 and peak==8
                with setup_engine.connect() as conn:
                    rows=conn.execute(text('SELECT e.request_id,e.total_tokens,e.status_code,e.user_id::text,s.project_id::text FROM public.ai_gateway_events e JOIN public.ai_chat_sessions s ON s.id=e.chat_session_id')).mappings().all()
                    assert len(rows)==65 and len({r['request_id'] for r in rows})==65
                    assert all(r['total_tokens']==3 and r['status_code']==200 and r['user_id']==str(UID) and r['project_id']==PID for r in rows)
                    assert conn.execute(text('SELECT count(*) FROM public.ai_chat_messages')).scalar_one()==130
                # Real HTTP queued request rechecks DB key status before model.
                runtime.admission.max_active=1
                runtime.admission.max_waiting=1
                runtime.admission.timeout=2
                gate.clear()
                first=asyncio.create_task(send())
                while active!=1:
                    await asyncio.sleep(.005)
                queued=asyncio.create_task(send())
                while runtime.admission.waiting!=1:
                    await asyncio.sleep(.005)
                rejected=await send()
                assert rejected.status_code==503 and rejected.headers['retry-after']=='3'
                assert rejected.headers['cache-control']=='no-store'
                with setup_engine.begin() as conn:
                    conn.execute(text('UPDATE public.ai_gateway_keys SET is_active=false WHERE id=:id'), {'id':str(KEY)})
                gate.set()
                assert (await first).status_code==200 and (await queued).status_code==401
                assert calls==66
                with setup_engine.begin() as conn:
                    conn.execute(text('UPDATE public.ai_gateway_keys SET is_active=true WHERE id=:id'), {'id':str(KEY)})
                gate.clear()
                runtime.admission.timeout=.05
                first=asyncio.create_task(send())
                while active!=1:
                    await asyncio.sleep(.005)
                timed=await send()
                assert timed.status_code==503 and timed.json()['detail']=='gateway_queue_timeout'
                gate.set()
                assert (await first).status_code==200
                assert runtime.admission.active==runtime.admission.waiting==0 and engine.pool.checkedout()==0
                # A real socket disconnect must release admission and persist unknown usage.
                gate.clear()
                try:
                    await client.post('/v1/responses', headers={'authorization':'Bearer synthetic-'+str(UID),'x-smartbrain-project-id':PID},
                        json={'model':'fixture','input':'断连合成测试'}, timeout=.15)
                except httpx.ReadTimeout:
                    pass
                else:
                    raise AssertionError('expected client disconnect')
                for _ in range(400):
                    if runtime.admission.active==0 and runtime.db_limiter.borrowed_tokens==0:
                        break
                    await asyncio.sleep(.005)
                assert runtime.admission.active==0 and engine.pool.checkedout()==0
                with setup_engine.connect() as conn:
                    cancelled=conn.execute(text('SELECT status_code,usage_missing,raw_usage FROM public.ai_gateway_events WHERE status_code=499')).mappings().all()
                    assert len(cancelled)==1 and cancelled[0]['usage_missing'] and cancelled[0]['raw_usage']=={}
                gate.set()
                await asyncio.sleep(.05)
                # The total model deadline also terminates a stalled HTTP upstream.
                monkeypatch.setattr(proxy, 'UPSTREAM_TIMEOUT_SECONDS', .05)
                gate.clear()
                failed=await send()
                gate.set()
                assert failed.status_code==502 and runtime.admission.active==0
                with setup_engine.connect() as conn:
                    assert conn.execute(text('SELECT count(*) FROM public.ai_gateway_events WHERE status_code=502 AND usage_missing')).scalar_one()==1
                    assert not conn.execute(text('SELECT content_complete FROM public.ai_gateway_events WHERE status_code=502')).scalar_one(), 'failed response marked complete in ledger'
                gate.set()
                await asyncio.sleep(.05)
                monkeypatch.setattr(proxy,'UPSTREAM_TIMEOUT_SECONDS',.5)
                async with client.stream('POST','/v1/responses',headers={'authorization':'Bearer synthetic-'+str(UID),'x-smartbrain-project-id':PID},json={'model':'fixture','input':'synthetic prompt','stream':True}) as response:
                    assert response.status_code==200
                    chunks=response.aiter_bytes()
                    first=await anext(chunks)
                    assert b'response.output_text.delta' in first
                    assert runtime.admission.active==1 and engine.pool.checkedout()==0
                    assert b'response.completed' in b''.join([chunk async for chunk in chunks])
                for _ in range(200):
                    if runtime.admission.active==0 and runtime.db_limiter.borrowed_tokens==0:break
                    await asyncio.sleep(.005)
                with setup_engine.connect() as conn:
                    streamed=conn.execute(text('SELECT e.status_code,e.total_tokens,e.content_complete,e.user_id::text,s.project_id::text FROM public.ai_gateway_events e JOIN public.ai_chat_sessions s ON s.id=e.chat_session_id ORDER BY e.started_at DESC LIMIT 1')).mappings().one()
                    assert streamed=={'status_code':200,'total_tokens':3,'content_complete':True,'user_id':str(UID),'project_id':PID}
                    assert conn.execute(text('SELECT count(*) FROM public.ai_gateway_events WHERE status_code=200')).scalar_one()==68
                assert runtime.admission.active==runtime.ingress.active==0 and engine.pool.checkedout()==0
                print(json.dumps({'staircase':results,'model_peak':peak,'scope_auth':'real PG hash/account/membership','saved_successes':67,'real_model_requests':0}))
    try:
        asyncio.run(scenario())
    finally:
        engine.dispose()
        with contextlib.suppress(StopIteration):
            next(seed)
