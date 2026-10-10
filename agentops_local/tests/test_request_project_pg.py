import os
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from agentops.api import personal_gateway_proxy as proxy
import test_request_project_proxy as helper

DSN = os.getenv('SB_REQUEST_PROJECT_TEST_DSN')
pytestmark = pytest.mark.skipif(not DSN, reason='isolated request attribution PG not configured')


@pytest.fixture(scope='module')
def engine():
    engine = create_engine(DSN)
    assert engine.url.database.startswith('sb_request_project_test_')
    with engine.begin() as conn:
        conn.exec_driver_sql('''
          CREATE TABLE public.users (id uuid PRIMARY KEY,is_system_admin boolean NOT NULL DEFAULT false);
          CREATE TABLE public.projects (id uuid PRIMARY KEY,name text NOT NULL);
          CREATE TABLE public.project_members (project_id uuid REFERENCES public.projects,user_id uuid REFERENCES public.users,role text,PRIMARY KEY(project_id,user_id));
          CREATE TABLE public.ai_gateway_keys (id uuid PRIMARY KEY,last_used_at timestamptz);
          CREATE TABLE public.ai_gateway_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),gateway_instance_id text,event_id text,request_id text,key_id uuid,user_id uuid,employee_id text,employee_name text,
            model text,request_model text,requested_model text,resolved_model text,upstream_model text,provider text,app_type text,conversation_id text,context_complete boolean DEFAULT false,
            status_code int,input_tokens bigint,output_tokens bigint,cache_read_tokens bigint,cache_creation_tokens bigint,cached_input_tokens bigint,cache_write_tokens bigint,reasoning_tokens bigint,
            input_token_semantics int,token_semantics_version int,total_tokens bigint,usage_missing boolean,raw_usage jsonb,total_cost_usd numeric,latency_ms int,error_message text,usage_date date,started_at timestamptz,completed_at timestamptz,
            chat_session_id uuid,content_complete boolean DEFAULT false,content_sync_status text,UNIQUE(gateway_instance_id,request_id));
          CREATE TABLE public.ai_chat_sessions (
            id uuid PRIMARY KEY,project_id uuid REFERENCES public.projects,user_id uuid REFERENCES public.users,employee_id text,employee_name text,source text,external_conversation_id text,title text,task_id text,task_title text,
            model text,status text,started_at timestamptz,ended_at timestamptz,duration_ms int,prompt_tokens bigint,completion_tokens bigint,total_tokens bigint,cost numeric,error_count int,trace_id text,metadata jsonb,
            updated_at timestamptz DEFAULT now(),context_complete boolean DEFAULT false);
          CREATE UNIQUE INDEX chat_identity ON public.ai_chat_sessions(project_id,source,employee_id,external_conversation_id) WHERE external_conversation_id IS NOT NULL;
          CREATE TABLE public.ai_chat_messages (id uuid DEFAULT gen_random_uuid() PRIMARY KEY,session_id uuid REFERENCES public.ai_chat_sessions,sequence_index int,role text,external_message_id text,content text,token_count int,message_created_at timestamptz,metadata jsonb);
          CREATE FUNCTION public.refresh_ai_usage_leaderboard_daily(date[]) RETURNS integer LANGUAGE sql AS 'SELECT 0';
          CREATE FUNCTION public.refresh_ai_gateway_leaderboard_daily(date[]) RETURNS integer LANGUAGE sql AS 'SELECT 0';
        ''')
        for uid in [helper.UID, uuid.UUID('22222222-2222-4222-8222-222222222222')]:
            conn.execute(text('INSERT INTO public.users(id) VALUES (:id)'), {'id':str(uid)})
        for pid,name in [(helper.PID,'合成项目'), ('00000000-0000-0000-0000-000000000000','无项目')]:
            conn.execute(text('INSERT INTO public.projects(id,name) VALUES (:id,:name)'), {'id':pid,'name':name})
        conn.execute(text('INSERT INTO public.project_members(project_id,user_id,role) VALUES (:pid,:uid,\'business_user\')'), {'pid':helper.PID,'uid':str(helper.UID)})
    yield engine
    engine.dispose()


@pytest.fixture
def orm(engine, monkeypatch):
    with Session(engine) as orm:
        monkeypatch.setattr(helper, 'Orm', lambda **kwargs: orm)
        yield orm


def test_real_pg_saves_project_and_keeps_requests_separate(orm, monkeypatch):
    for _ in range(2):
        response, _, _ = helper.invoke_proxy(monkeypatch, persist=True)
        assert response.status_code == 200
    rows=orm.execute(text('SELECT e.request_id,e.context_complete,e.total_tokens,s.project_id::text,s.metadata,p.name FROM public.ai_gateway_events e JOIN public.ai_chat_sessions s ON s.id=e.chat_session_id JOIN public.projects p ON p.id=s.project_id ORDER BY e.started_at')).mappings().all()
    assert len(rows)==2 and len({r['request_id'] for r in rows})==2
    assert all(r['project_id']==helper.PID and r['name']=='合成项目' and r['total_tokens']==3 and not r['context_complete'] for r in rows)
    assert all(r['metadata']['project_attribution']['source']=='authenticated_request' for r in rows)


def test_real_pg_agents_context_only_keeps_visible_messages(orm, monkeypatch):
    agents=f'# AGENTS.md instructions for /project\n<INSTRUCTIONS>\n<!-- smartbrain-project-id: {helper.PID} -->\n</INSTRUCTIONS>'
    helper.invoke_proxy(monkeypatch, project_header=None, agents=agents, persist=True)
    texts=orm.execute(text('SELECT content FROM public.ai_chat_messages')).scalars().all()
    assert texts and all('AGENTS.md' not in t and 'smartbrain-project-id' not in t for t in texts)


@pytest.mark.parametrize('header,uid,status', [
    (helper.PID, uuid.UUID('22222222-2222-4222-8222-222222222222'), 403),
    ('33333333-3333-4333-8333-333333333333', helper.UID, 404),
    ('invalid', helper.UID, 400),
])
def test_real_pg_unauthorized_or_invalid_projects_do_not_call_model(orm, monkeypatch, header, uid, status):
    calls=[]
    before=orm.execute(text('SELECT count(*) FROM public.ai_gateway_events')).scalar_one()
    with pytest.raises(HTTPException) as error:
        helper.invoke_proxy(monkeypatch, persist=True, project_header=header, user_id=uid, upstream_calls=calls)
    assert error.value.status_code==status and calls==[]
    assert orm.execute(text('SELECT count(*) FROM public.ai_gateway_events')).scalar_one()==before
