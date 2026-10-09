"""Run only against an explicitly configured, isolated database containing synthetic data."""
import os
import ast
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi import Depends, HTTPException

from agentops_local.project_memory import conversations as service
from agentops_local.rag.authz import AuthzError, current_user_id, is_system_admin, require_member

DSN = os.getenv('SB_MEMORY_TEST_DSN')
pytestmark = pytest.mark.skipif(not DSN, reason='isolated PG DSN not configured')
ROOT = Path(__file__).parents[2]


@pytest.fixture(scope='module')
def engine():
    assert callable(getattr(service, 'save_project_conversation', None)), 'dedicated save service required'
    engine = create_engine(DSN)
    assert engine.url.database == 'sb_memory_no_adapter_test_r1', 'refuse non-test database'
    with engine.begin() as conn:
        conn.execute(text('CREATE SCHEMA IF NOT EXISTS auth'))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS auth.users (
            id uuid PRIMARY KEY,email text,deleted_at timestamptz,banned_until timestamptz,is_anonymous boolean DEFAULT false);
            CREATE TABLE IF NOT EXISTS public.users (id uuid PRIMARY KEY REFERENCES auth.users(id),
            full_name text,nickname text,is_active boolean DEFAULT true,is_system_admin boolean DEFAULT false);
            CREATE TABLE IF NOT EXISTS public.projects(id uuid PRIMARY KEY,name text);
            CREATE TABLE IF NOT EXISTS public.project_members(project_id uuid REFERENCES public.projects(id),
            user_id uuid REFERENCES public.users(id),role text,PRIMARY KEY(project_id,user_id));
            CREATE TABLE IF NOT EXISTS public.documents(id uuid PRIMARY KEY);'''))
        conn.execute(text("ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS environment text DEFAULT 'development', ADD COLUMN IF NOT EXISTS department_id text DEFAULT 'research', ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now(), ADD COLUMN IF NOT EXISTS completed_at timestamptz"))
        wiki = (ROOT/'supabase/migrations/20260730000000_add_project_wiki.sql').read_text(encoding='utf-8')
        # Use the original full table definitions, without unrelated compiler tables.
        conn.execute(text(wiki[wiki.index('CREATE TABLE IF NOT EXISTS public.project_wiki_pages'):wiki.index('CREATE TABLE IF NOT EXISTS public.project_wiki_links')]))
        conn.execute(text("ALTER TABLE public.project_wiki_pages ADD COLUMN IF NOT EXISTS memory_kind text DEFAULT 'reference', ADD COLUMN IF NOT EXISTS verification_status text DEFAULT 'generated', ADD COLUMN IF NOT EXISTS tags jsonb DEFAULT '[]'::jsonb"))
        old = (ROOT/'supabase/migrations/20260923000000_project_agents_context_conversations.sql').read_text(encoding='utf-8')
        conn.execute(text(old[old.index('CREATE TABLE IF NOT EXISTS public.project_conversation_records'):old.index('CREATE TABLE IF NOT EXISTS public.ai_gateway_key_requests')]))
    migration = (ROOT/'supabase/migrations/20261008000000_company_memory_conversation_submissions.sql').read_text(encoding='utf-8')
    with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as conn:
        conn.exec_driver_sql(migration)
        conn.exec_driver_sql(migration)  # replay must preserve records and schema
    yield engine
    engine.dispose()


@pytest.fixture
def actors(engine):
    uid, pid, other = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    with engine.begin() as conn:
        for who in (uid, other):
            conn.execute(text("INSERT INTO auth.users(id,email) VALUES (:id,'synthetic@example.invalid')"), {'id': who})
            conn.execute(text("INSERT INTO public.users(id,full_name) VALUES (:id,'合成成员')"), {'id': who})
        conn.execute(text("INSERT INTO public.projects(id,name) VALUES (:id,'合成项目')"), {'id': pid})
        conn.execute(text("INSERT INTO public.project_members VALUES (:pid,:uid,'developer')"), {'pid': pid, 'uid': uid})
    return uid, pid, other


def submit(engine, uid, pid, payload=None):
    payload = payload or service.validate_submission(submission_id=str(uuid.uuid4()), title='合成记录',
        messages=[{'role': 'user', 'content': '完成页面任务'}, {'role': 'assistant', 'content': '合成验证已通过'}], task_result='合成结果')
    with Session(engine) as orm, orm.begin():
        return service.save_project_conversation(orm, user_id=uid, project_id=pid, submission=payload)


def read_routes(engine, uid, pid):
    # Execute the actual ledger/stats route bodies and response models against
    # PG, without importing unrelated ingest/model clients or opening a server.
    names = {'KnowledgeLedgerUser','KnowledgeLedgerProject','KnowledgeLedgerPermissions',
        'KnowledgeLedgerSummary','KnowledgeLedgerDocument','KnowledgeLedgerResponse',
        '_ledger_user','get_knowledge_ledger','WikiUploadStatsMember','WikiUploadStatsResponse',
        'wiki_upload_stats','_require_member_or_http','_user_id'}
    namespace = dict(uuid=uuid, Literal=Literal, BaseModel=BaseModel, Field=Field,
        Depends=Depends, get_orm_session=lambda:None, Request=object, Session=Session,
        HTTPException=HTTPException, AuthzError=AuthzError, current_user_id=current_user_id,
        require_member=require_member, is_system_admin=is_system_admin, text=text, DepartmentId=str)
    for filename in ('knowledge.py','project_agents.py'):
        tree=ast.parse((ROOT/'agentops_local/api/routes/v4'/filename).read_text(encoding='utf-8'))
        nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
        for node in nodes:
            node.decorator_list=[]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),filename,'exec'),namespace)
    request=SimpleNamespace(state=SimpleNamespace(session=SimpleNamespace(user_id=uid)))
    with Session(engine) as orm:
        ledger=namespace['get_knowledge_ledger'](request=request, project_id=pid,category='conversation_record',orm=orm)
        stats=namespace['wiki_upload_stats'](project_id=pid,request=request,orm=orm)
    return ledger,stats


def test_upload_stats_count_saved_conversations_even_when_wiki_fails(engine, actors, monkeypatch):
    uid,pid,_=actors
    def failed_publication(*args,**kwargs):raise SQLAlchemyError('synthetic unavailable wiki')
    monkeypatch.setattr(service,'_publish_wiki',failed_publication)
    payload=service.validate_submission(submission_id=str(uuid.uuid4()),title='短摘要',messages=[{'role':'user','content':'合成请求'},{'role':'assistant','content':'合成结果'}])
    first=submit(engine,uid,pid,payload);again=submit(engine,uid,pid,payload)
    assert first['status']=='saved' and first['wiki_status']=='failed' and first['record_id']==again['record_id']
    _,stats=read_routes(engine,uid,pid)
    assert stats.total==1 and len(stats.members)==1 and stats.members[0].count==1 and stats.members[0].ratio==1


def test_conversation_page_contains_only_short_visible_task_summary(engine, actors):
    uid,pid,_=actors
    payload=service.validate_submission(submission_id=str(uuid.uuid4()),title='简短摘要',messages=[{'role':'user','content':'修复统计标题'},{'role':'assistant','content':'已改为对话上传统计'}],task_result='已改为对话上传统计')
    result=submit(engine,uid,pid,payload)
    with engine.connect() as conn:
        content=conn.execute(text('SELECT markdown_content FROM public.project_wiki_pages WHERE id=:id'),{'id':result['wiki_page_id']}).scalar_one()
    assert '修复统计标题' in content and content.count('已改为对话上传统计')==1
    assert all(value not in content for value in ['上传成员','上传时间','模型来源','记录编号','用量：','unknown',str(uid),str(pid)])
    assert len(content)<300


def test_save_retry_list_stats_and_unknown_tokens_are_consistent(engine, actors):
    uid, pid, _ = actors
    payload = service.validate_submission(submission_id=str(uuid.uuid4()), title='合成记录', messages=[{'role': 'user', 'content': '合成正文'}])
    first = submit(engine, uid, pid, payload)
    again = submit(engine, uid, pid, payload)
    assert first['record_id'] == again['record_id']
    assert first['wiki_status'] == 'published'
    assert first['uploaded_by'] == {'user_id': str(uid), 'name': '合成成员'}
    assert first['total_tokens'] is None and first['token_status'] == 'unknown'
    ledger,stats=read_routes(engine,uid,pid)
    assert len(ledger.documents)==1 and str(ledger.documents[0].asset_id)==first['record_id']
    assert str(ledger.documents[0].document_id)==first['wiki_page_id']
    assert ledger.documents[0].approval_status=='approved'
    assert stats.total==1 and stats.members[0].user_id==uid
    with engine.connect() as conn:
        record = conn.execute(text('SELECT * FROM public.project_conversation_records WHERE project_id=:p'), {'p': pid}).mappings().one()
        assert record['messages'] == payload.messages
        assert record['record_source'] == 'company_memory' and record['attempt_count'] == 1
        assert record['model_source'] == 'unknown' and record['task_result'] == ''
        assert record['completed_at'] is None  # submission time is not model completion time
        page = conn.execute(text('SELECT * FROM public.project_wiki_pages WHERE id=:id'), {'id': record['wiki_page_id']}).mappings().one()
        assert page['memory_kind'] == 'conversation_record' and page['verification_status'] == 'generated'
        assert page['created_by_user_id'] == uid
        assert conn.execute(text("SELECT count(*) FROM public.project_conversation_records WHERE project_id=:p AND wiki_status='published' GROUP BY user_id"), {'p': pid}).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM public.project_wiki_page_versions WHERE page_id=:id'), {'id': page['id']}).scalar_one() == 1


def test_conflicting_content_is_rejected_and_other_user_cannot_reuse_record(engine, actors):
    uid, pid, other = actors
    sid = str(uuid.uuid4())
    payload = service.validate_submission(submission_id=sid, title='合成', messages=[{'role': 'user', 'content': '一'}])
    record = submit(engine, uid, pid, payload)
    changed = service.validate_submission(submission_id=sid, title='合成', messages=[{'role': 'user', 'content': '二'}])
    with pytest.raises(ValueError, match='conflict'):
        submit(engine, uid, pid, changed)
    with pytest.raises(AuthzError):
        submit(engine, other, pid, payload)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO public.project_members VALUES (:p,:u,'developer')"), {'p': pid, 'u': other})
    assert submit(engine, other, pid, payload)['record_id'] != record['record_id']


@pytest.mark.parametrize('condition', ['inactive', 'deleted', 'banned', 'anonymous', 'reader', 'outsider'])
def test_account_and_writer_boundaries(engine, actors, condition):
    uid, pid, other = actors
    statements = {
        'inactive': "UPDATE public.users SET is_active=false WHERE id=:u",
        'deleted': "UPDATE auth.users SET deleted_at=now() WHERE id=:u",
        'banned': "UPDATE auth.users SET banned_until=now()+interval '1 day' WHERE id=:u",
        'anonymous': "UPDATE auth.users SET is_anonymous=true WHERE id=:u",
        'reader': "UPDATE public.project_members SET role='business_user' WHERE user_id=:u",
        'outsider': "DELETE FROM public.project_members WHERE user_id=:u",
    }
    with engine.begin() as conn:
        conn.execute(text(statements[condition]), {'u': uid})
    with pytest.raises(AuthzError):
        submit(engine, uid, pid)
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM public.project_conversation_records WHERE project_id=:p'), {'p': pid}).scalar_one() == 0


def test_wiki_failure_preserves_record_and_retry_publishes_once(engine, actors, monkeypatch):
    uid, pid, _ = actors
    payload = service.validate_submission(submission_id=str(uuid.uuid4()), title='重试', messages=[{'role': 'assistant', 'content': '合成结果'}])
    original = service._publish_wiki
    def fail(*a, **kw):
        raise SQLAlchemyError('private database detail must not escape')
    monkeypatch.setattr(service, '_publish_wiki', fail)
    failed = submit(engine, uid, pid, payload)
    assert failed['status'] == 'saved' and failed['wiki_status'] == 'failed'
    assert failed['wiki_error'] == 'wiki_publish_failed'
    ledger,stats=read_routes(engine,uid,pid)
    assert ledger.documents[0].approval_status=='rejected' and stats.total==1
    monkeypatch.setattr(service, '_publish_wiki', original)
    success = submit(engine, uid, pid, payload)
    assert success['record_id'] == failed['record_id'] and success['wiki_status'] == 'published'
    with engine.connect() as conn:
        assert conn.execute(text('SELECT attempt_count FROM public.project_conversation_records WHERE id=:id'), {'id': success['record_id']}).scalar_one() == 2


def test_concurrent_retries_create_only_one_record_and_page(engine, actors):
    uid, pid, _ = actors
    payload = service.validate_submission(submission_id=str(uuid.uuid4()), title='并发', messages=[{'role': 'user', 'content': '合成'}])
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(lambda _: submit(engine, uid, pid, payload), range(4)))
    assert len({r['record_id'] for r in receipts}) == 1
    assert len({r['wiki_page_id'] for r in receipts}) == 1


def test_rls_blocks_direct_reads_even_with_explicit_select_grant(engine, actors):
    uid,pid,_=actors
    submit(engine,uid,pid)
    with engine.begin() as conn:
        conn.execute(text('GRANT USAGE ON SCHEMA public TO sb_memory_reader_r1'))
        conn.execute(text('GRANT SELECT ON public.project_conversation_records,public.project_conversation_record_attempts TO sb_memory_reader_r1'))
        assert conn.execute(text('SELECT count(*) FROM public.project_conversation_records')).scalar_one()>0
        conn.execute(text('SET LOCAL ROLE sb_memory_reader_r1'))
        assert conn.execute(text('SELECT count(*) FROM public.project_conversation_records')).scalar_one()==0
        assert conn.execute(text('SELECT count(*) FROM public.project_conversation_record_attempts')).scalar_one()==0


def test_retry_repairs_missing_wiki_page_without_duplicate_record(engine, actors):
    uid,pid,_=actors
    payload=service.validate_submission(submission_id=str(uuid.uuid4()),title='页面恢复',messages=[{'role':'user','content':'合成内容'}])
    first=submit(engine,uid,pid,payload)
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM public.project_wiki_pages WHERE id=:id'),{'id':first['wiki_page_id']})
    repaired=submit(engine,uid,pid,payload)
    assert repaired['record_id']==first['record_id']
    assert repaired['wiki_status']=='published' and repaired['wiki_page_id']
    assert repaired['wiki_page_id']!=first['wiki_page_id']
    ledger,stats=read_routes(engine,uid,pid)
    assert len(ledger.documents)==1 and stats.total==1
