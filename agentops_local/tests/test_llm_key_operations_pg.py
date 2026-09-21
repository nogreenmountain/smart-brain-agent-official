"""Mandatory real PostgreSQL tests, using only the named isolated pilot DB.

Run via the workspace management run_pg_tests.py helper; no production DB and
no paid model calls. Fixtures are retained with unique IDs, never truncated.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).parents[1]


def load():
    name='llm_key_operations'
    spec=importlib.util.spec_from_file_location(name,ROOT/'ai_usage/llm_key_operations.py')
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


@pytest.fixture(scope='module')
def database():
    dsn=os.environ.get('SB_KEY_OPERATIONS_TEST_DSN')
    if not dsn:pytest.fail('Use run_pg_tests.py with the isolated PostgreSQL test database')
    engine=create_engine(dsn,pool_size=8,max_overflow=0)
    assert engine.url.host=='127.0.0.1' and engine.url.database=='sb_key_management_test_r1'
    with engine.begin() as c:
        c.exec_driver_sql('''CREATE SCHEMA IF NOT EXISTS auth;
          CREATE TABLE IF NOT EXISTS public.users(id uuid PRIMARY KEY,is_active boolean DEFAULT true);
          CREATE TABLE IF NOT EXISTS auth.users(id uuid PRIMARY KEY,email text,deleted_at timestamptz,banned_until timestamptz);
          CREATE TABLE IF NOT EXISTS public.ai_gateway_keys(id uuid PRIMARY KEY,user_id uuid NOT NULL,is_active boolean NOT NULL);
          CREATE TABLE IF NOT EXISTS public.ai_gateway_key_allowances(user_id uuid PRIMARY KEY,max_active_keys integer NOT NULL);''')
        c.exec_driver_sql('''ALTER TABLE public.users ADD COLUMN IF NOT EXISTS full_name text;
          ALTER TABLE public.ai_gateway_keys ADD COLUMN IF NOT EXISTS key_prefix text;
          ALTER TABLE public.ai_gateway_keys ADD COLUMN IF NOT EXISTS label text;
          ALTER TABLE public.ai_gateway_keys ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();
          ALTER TABLE public.ai_gateway_keys ADD COLUMN IF NOT EXISTS last_used_at timestamptz;
          ALTER TABLE public.ai_gateway_keys ADD COLUMN IF NOT EXISTS revoked_at timestamptz;
          ALTER TABLE public.ai_gateway_keys ADD COLUMN IF NOT EXISTS hidden_at timestamptz;
          ALTER TABLE public.ai_gateway_keys ALTER COLUMN id SET DEFAULT gen_random_uuid();''')
        migration=(ROOT.parent/'supabase/migrations/20260915000000_llm_key_operations.sql').read_text(encoding='utf-8')
        with c.connection.driver_connection.cursor() as cursor:
            cursor.execute(migration)
    yield engine
    engine.dispose()


class Gateway:
    models=['pilot-mock']
    def __init__(self):self.created=[];self.keys={}
    def create_key(self, *, secret,user_id,operation_id,label):
        import hashlib
        ref=hashlib.sha256(secret.encode()).hexdigest()
        self.created.append({'ref':ref,'user_id':user_id,'operation_id':operation_id})
        self.keys[ref]={'exists':True,'blocked':False}
        return ref
    def lookup_key(self,ref,**identity):return self.keys.get(ref)
    def block_key(self,ref,**identity):self.keys[ref]['blocked']=True;return True
    def delete_blocked_key(self,ref,**identity):self.keys.pop(ref,None);return True
    def close(self):pass


@pytest.fixture
def setup(database):
    uid,instance=str(uuid.uuid4()),str(uuid.uuid4())
    with database.begin() as c:
        c.execute(text('INSERT INTO public.users(id) VALUES(:id)'),{'id':uid})
        c.execute(text("INSERT INTO auth.users(id,email) VALUES(:id,'synthetic@invalid')"),{'id':uid})
        c.execute(text("INSERT INTO public.llm_gateway_instances(id,endpoint_ref,base_url,models,enabled) VALUES(:id,'TEST_GATEWAY','https://model.invalid/v1',CAST(:models AS jsonb),true)"),{'id':instance,'models':json.dumps(['pilot-mock'])})
        c.execute(text('INSERT INTO public.llm_member_rollout(user_id,instance_id,enabled) VALUES(:uid,:iid,true)'),{'uid':uid,'iid':instance})
    m=load();gateway=Gateway();service=m.KeyOperations(sessionmaker(database),gateway,instance_id=instance)
    return uid,instance,gateway,service


def test_creation_commits_mapping_and_delivers_secret_only_once(database,setup):
    uid,instance,gateway,service=setup;operation=str(uuid.uuid4())
    first=service.create(user_id=uid,idempotency_key=operation,label='work laptop')
    assert first['status']=='confirmed' and first['key'].startswith('sk-')
    second=service.create(user_id=uid,idempotency_key=operation,label='work laptop')
    assert second['operation_id']==first['operation_id'] and 'key' not in second
    assert len(gateway.created)==1
    with database.connect() as c:
        row=c.execute(text('SELECT state,reserved_slot FROM public.llm_key_operations WHERE id=:id'),{'id':first['operation_id']}).one()
        assert row.state=='confirmed' and row.reserved_slot is False
        assert c.execute(text('SELECT count(*) FROM public.llm_credential_refs WHERE user_id=:uid AND state=\'active\''),{'uid':uid}).scalar_one()==1


def test_rollout_disabled_does_not_fallback_and_ownership_is_private(database,setup):
    uid,instance,gateway,service=setup
    assert service.creation_enabled(user_id=uid) is True
    created=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='owned')
    assert service.owns_credential(user_id=uid,credential_id=created['credential_id']) is True
    assert service.owns_credential(user_id=str(uuid.uuid4()),credential_id=created['credential_id']) is False
    with database.begin() as c:
        c.execute(text('UPDATE public.llm_gateway_instances SET enabled=false WHERE id=:id'),{'id':instance})
    with pytest.raises(Exception,match='gateway_not_enabled'):
        service.creation_enabled(user_id=uid)
    assert service.owns_credential(user_id=uid,credential_id=created['credential_id']) is True
    with database.begin() as c:
        c.execute(text('UPDATE public.llm_member_rollout SET enabled=false WHERE user_id=:uid'),{'uid':uid})
    with pytest.raises(Exception,match='gateway_not_enabled'):
        service.creation_enabled(user_id=uid)
    assert service.creation_enabled(user_id=str(uuid.uuid4())) is False


def test_shared_quota_counts_pending_and_revoking_until_confirmed(database,setup,monkeypatch):
    uid,instance,gateway,service=setup
    spec=importlib.util.spec_from_file_location('llm_key_quota',ROOT/'ai_usage/llm_key_quota.py')
    quota=importlib.util.module_from_spec(spec);spec.loader.exec_module(quota)
    monkeypatch.setenv('SB_LLM_GATEWAY_MANAGEMENT_ENABLED','1')
    def used():
        with database.connect() as c:
            return c.execute(text('SELECT '+quota.key_count_sql(':uid')),{'uid':uid}).scalar_one()
    gateway.create_key=lambda **kw: (_ for _ in ()).throw(TimeoutError())
    result=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='pending')
    assert used()==1
    with database.connect() as c:
        ref=c.execute(text('SELECT key_hash FROM public.llm_key_operations WHERE id=:id'),{'id':result['operation_id']}).scalar_one()
    gateway.keys[ref]={'exists':True,'blocked':False}
    service.reconcile_create(user_id=uid,operation_id=result['operation_id'])
    assert used()==1
    gateway.block_key=lambda *a,**kw: (_ for _ in ()).throw(TimeoutError())
    revoked=service.revoke(user_id=uid,credential_id=result['credential_id'],idempotency_key=str(uuid.uuid4()))
    assert used()==1
    gateway.keys[ref]['blocked']=True
    service.reconcile_change(user_id=uid,operation_id=revoked['operation_id'])
    assert used()==0


def test_real_rls_denies_credential_reads_and_writes_to_untrusted_role(database,setup):
    from sqlalchemy.exc import DBAPIError
    uid,instance,gateway,service=setup
    service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='private')
    role='llm_test_'+uuid.uuid4().hex
    # Roll back the temporary role and grants; no durable data is deleted.
    with database.connect() as c:
        transaction=c.begin()
        try:
            c.exec_driver_sql('CREATE ROLE '+role+' NOLOGIN')
            c.exec_driver_sql('GRANT USAGE ON SCHEMA public TO '+role)
            c.exec_driver_sql('GRANT SELECT,INSERT,UPDATE,DELETE ON public.llm_gateway_instances,public.llm_member_rollout,public.llm_key_operations,public.llm_credential_refs TO '+role)
            c.exec_driver_sql('SET LOCAL ROLE '+role)
            for table in ('llm_gateway_instances','llm_member_rollout','llm_key_operations','llm_credential_refs'):
                assert c.exec_driver_sql('SELECT count(*) FROM public.'+table).scalar_one()==0
            assert c.execute(text('UPDATE public.llm_credential_refs SET label=\'unauthorized\' WHERE user_id=:uid'),{'uid':uid}).rowcount==0
            with pytest.raises(DBAPIError):
                c.execute(text("INSERT INTO public.llm_gateway_instances(id,endpoint_ref,base_url,models) VALUES(:id,'bad','bad','[\"bad\"]')"),{'id':str(uuid.uuid4())})
        finally:
            transaction.rollback()


def test_pending_operations_can_be_rediscovered_without_writes_after_browser_restart(database,setup):
    uid,instance,gateway,service=setup
    gateway.create_key=lambda **kw: (_ for _ in ()).throw(TimeoutError())
    result=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='reload')
    pending=service.list_operations(user_id=uid)
    assert len(pending)==1 and pending[0]['operation_id']==result['operation_id']
    assert 'key_hash' not in pending[0] and 'key' not in pending[0]
    assert service.list_operations(user_id=str(uuid.uuid4()))==[]


def test_reconciler_batch_waits_for_age_and_never_reissues_native_create(database,setup):
    uid,instance,native,service=setup;original=native.create_key
    def lost(**kw):original(**kw);raise TimeoutError()
    native.create_key=lost
    created=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='worker')
    assert service.reconcile_pending()==[]
    with database.begin() as c:
        c.execute(text("UPDATE public.llm_key_operations SET updated_at=now()-interval '2 minutes' WHERE id=:id"),{'id':created['operation_id']})
    result=service.reconcile_pending()
    assert len(result)==1 and result[0]['status']=='confirmed' and 'key' not in result[0]
    assert len(native.created)==1
    assert service.reconcile_pending()==[]


def test_lost_create_response_is_reconciled_by_hash_without_resubmission(database,setup):
    uid,instance,gateway,service=setup;idem=str(uuid.uuid4());original=gateway.create_key
    def lost(**kwargs): original(**kwargs);raise TimeoutError('response lost')
    gateway.create_key=lost
    result=service.create(user_id=uid,idempotency_key=idem,label='lost-response')
    assert result['status']=='reconciling' and 'key' not in result
    repeated=service.create(user_id=uid,idempotency_key=idem,label='lost-response')
    assert repeated['operation_id']==result['operation_id'] and len(gateway.created)==1
    recovered=service.reconcile_create(user_id=uid,operation_id=result['operation_id'])
    assert recovered['status']=='confirmed' and recovered['error_code']=='secret_not_delivered'
    assert 'key' not in recovered and len(gateway.created)==1
    with database.connect() as c:
        assert c.execute(text('SELECT count(*) FROM public.llm_credential_refs WHERE user_id=:uid'),{'uid':uid}).scalar_one()==1


def test_concurrent_creation_shares_legacy_allowance_and_never_exceeds_it(database,setup):
    from concurrent.futures import ThreadPoolExecutor
    uid,instance,gateway,service=setup
    with database.begin() as c:
        c.execute(text('INSERT INTO public.ai_gateway_key_allowances VALUES(:uid,3)'),{'uid':uid})
        c.execute(text('INSERT INTO public.ai_gateway_keys VALUES(:id,:uid,true)'),{'id':str(uuid.uuid4()),'uid':uid})
    def create(_):
        try:return service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='parallel')['status']
        except Exception as e:return getattr(e,'code',type(e).__name__)
    with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(create,range(6)))
    assert results.count('confirmed')==2 and results.count('key_allowance_exhausted')==4
    assert len(gateway.created)==2


def test_concurrent_duplicate_id_issues_once_and_conflicting_payload_is_rejected(database,setup):
    from concurrent.futures import ThreadPoolExecutor
    uid,instance,gateway,service=setup;idem=str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda _:service.create(user_id=uid,idempotency_key=idem,label='same'),range(6)))
    assert len({r['operation_id'] for r in results})==1 and sum('key' in r for r in results)==1
    assert len(gateway.created)==1
    with pytest.raises(Exception,match='idempotency_conflict'):service.create(user_id=uid,idempotency_key=idem,label='different')


def test_missing_after_timeout_keeps_reserved_slot_and_does_not_prove_failure(database,setup):
    uid,instance,gateway,service=setup
    def lost(**kwargs):raise TimeoutError('unknown delivery')
    gateway.create_key=lost
    result=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='unknown')
    again=service.reconcile_create(user_id=uid,operation_id=result['operation_id'])
    assert again['status']=='reconciling' and len(gateway.created)==0
    with pytest.raises(Exception,match='key_allowance_exhausted'):service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='second')
    with database.connect() as c:assert c.execute(text('SELECT reserved_slot FROM public.llm_key_operations WHERE id=:id'),{'id':result['operation_id']}).scalar_one() is True


def test_revoke_releases_slot_only_after_native_confirmation_and_remove_preserves_mapping(database,setup):
    uid,instance,gateway,service=setup
    key=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='retire')
    stopped=service.revoke(user_id=uid,credential_id=key['credential_id'],idempotency_key=str(uuid.uuid4()))
    assert stopped['status']=='confirmed'
    second=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='replacement')
    assert second['status']=='confirmed'
    removed=service.remove(user_id=uid,credential_id=key['credential_id'],idempotency_key=str(uuid.uuid4()))
    assert removed['status']=='confirmed'
    with database.connect() as c:
        r=c.execute(text('SELECT state,hidden_at FROM public.llm_credential_refs WHERE id=:id'),{'id':key['credential_id']}).one()
        assert r.state=='removed' and r.hidden_at is not None
        assert c.execute(text('SELECT count(*) FROM public.llm_key_operations WHERE credential_id=:id'),{'id':key['credential_id']}).scalar_one()==3


def test_lost_block_response_preserves_quota_until_read_only_recovery(database,setup):
    uid,instance,gateway,service=setup;key=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='revoke-lost')
    original=gateway.block_key;calls=[]
    def lost(*args,**kwargs):calls.append(args);original(*args,**kwargs);raise TimeoutError('lost block response')
    gateway.block_key=lost
    idem=str(uuid.uuid4());result=service.revoke(user_id=uid,credential_id=key['credential_id'],idempotency_key=idem)
    assert result['status']=='reconciling'
    with pytest.raises(Exception,match='key_allowance_exhausted'):service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='too-soon')
    assert service.revoke(user_id=uid,credential_id=key['credential_id'],idempotency_key=idem)['operation_id']==result['operation_id']
    recovered=service.reconcile_change(user_id=uid,operation_id=result['operation_id'])
    assert recovered['status']=='confirmed' and len(calls)==1
    assert service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='now-allowed')['status']=='confirmed'


def test_cross_user_and_disabled_user_reconciliation_never_reaches_gateway(database,setup):
    uid,instance,gateway,service=setup
    def lost(**kwargs):raise TimeoutError('unknown')
    gateway.create_key=lost
    op=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='owned')
    calls=[];gateway.lookup_key=lambda *a,**k:calls.append(a)
    with pytest.raises(Exception,match='operation_not_found'):service.reconcile_create(user_id=str(uuid.uuid4()),operation_id=op['operation_id'])
    with database.begin() as c:c.execute(text('UPDATE public.users SET is_active=false WHERE id=:id'),{'id':uid})
    with pytest.raises(Exception,match='member_unavailable'):service.reconcile_create(user_id=uid,operation_id=op['operation_id'])
    assert calls==[]


def test_native_call_holds_no_business_row_lock_and_inflight_operation_cannot_replay(database,setup):
    uid,instance,gateway,service=setup;idem=str(uuid.uuid4());original=gateway.create_key
    def observe(**kwargs):
        with database.begin() as c:
            c.exec_driver_sql("SET LOCAL lock_timeout='200ms'")
            c.execute(text('SELECT id FROM public.users WHERE id=:id FOR UPDATE'),{'id':uid}).one()
        existing=service.create(user_id=uid,idempotency_key=idem,label='inflight')
        assert existing['status']=='submitted' and 'key' not in existing
        return original(**kwargs)
    gateway.create_key=observe
    assert service.create(user_id=uid,idempotency_key=idem,label='inflight')['status']=='confirmed'
    assert len(gateway.created)==1


def test_lost_delete_response_is_read_back_without_repeating_delete(database,setup):
    uid,instance,gateway,service=setup
    key=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='delete-lost')
    service.revoke(user_id=uid,credential_id=key['credential_id'],idempotency_key=str(uuid.uuid4()))
    original=gateway.delete_blocked_key;calls=[]
    def lost(*a,**k):calls.append(a);original(*a,**k);raise TimeoutError('lost delete')
    gateway.delete_blocked_key=lost
    operation=service.remove(user_id=uid,credential_id=key['credential_id'],idempotency_key=str(uuid.uuid4()))
    assert operation['status']=='reconciling'
    assert service.reconcile_change(user_id=uid,operation_id=operation['operation_id'])['status']=='confirmed'
    assert len(calls)==1


@pytest.mark.parametrize('label',['','   ','x'*101,'bad\nname'])
def test_invalid_labels_never_reserve_or_call_gateway(database,setup,label):
    uid,instance,gateway,service=setup
    with pytest.raises(Exception,match='invalid_label'):service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label=label)
    assert gateway.created==[]


def test_read_summaries_exclude_native_hash_and_secret(database,setup):
    uid,instance,gateway,service=setup;made=service.create(user_id=uid,idempotency_key=str(uuid.uuid4()),label='visible')
    listing=service.list_keys(user_id=uid)
    assert len(listing)==1 and listing[0]['id']==made['credential_id'] and listing[0]['backend']=='litellm'
    assert listing[0]['base_url']=='https://model.invalid/v1'
    assert listing[0]['label']=='visible' and listing[0]['status']=='active'
    assert made['key'] not in json.dumps(listing) and gateway.created[0]['ref'] not in json.dumps(listing)
    summary=service.get_operation(user_id=uid,operation_id=made['operation_id'])
    assert 'key' not in summary and summary['status']=='confirmed'
