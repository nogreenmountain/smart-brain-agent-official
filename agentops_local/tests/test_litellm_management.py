import hashlib
import importlib.util
import json
from pathlib import Path

import httpx
import pytest


def module():
    spec = importlib.util.spec_from_file_location('litellm_management', Path(__file__).parents[1] / 'ai_usage/litellm_management.py')
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj


def test_create_uses_preselected_key_and_server_owned_inference_permissions():
    calls = []
    secret = 'sk-' + 'a' * 43
    def server(request):
        calls.append(request)
        payload = json.loads(request.content)
        assert payload == {'key': secret, 'user_id': 'employee-A', 'models': ['gpt-6-astra'],
                           'key_alias': 'work-laptop', 'metadata': {'smartbrain_operation_id': 'op-A'},
                           'key_type': 'llm_api', 'blocked': False}
        return httpx.Response(200, json={'key': secret})
    m = module()
    client = m.LiteLLMManagement('https://gateway.example', 'master-synthetic', models=('gpt-6-astra',), transport=httpx.MockTransport(server))
    assert client.create_key(secret=secret, user_id='employee-A', operation_id='op-A', label='work-laptop') == hashlib.sha256(secret.encode()).hexdigest()
    assert len(calls) == 1 and calls[0].url.path == '/key/generate'
    assert calls[0].headers['authorization'] == 'Bearer master-synthetic'


@pytest.mark.parametrize('kind', ['timeout', 'redirect', 'server-error', 'invalid-json', 'different-key', 'oversize'])
def test_uncertain_create_does_not_retry_or_expose_secret(kind):
    calls = []; m = module(); secret = 'sk-' + 'a' * 43
    def server(request):
        calls.append(request)
        if kind == 'timeout': raise httpx.ReadTimeout('secret='+secret, request=request)
        if kind == 'redirect': return httpx.Response(307, headers={'location':'https://attacker.example/key/generate'})
        if kind == 'server-error': return httpx.Response(502, text=secret)
        if kind == 'invalid-json': return httpx.Response(200, text=secret)
        if kind == 'oversize': return httpx.Response(200, json={'key':secret, 'padding':'x'*70000})
        return httpx.Response(200, json={'key':'another-key'})
    client = m.LiteLLMManagement('https://gateway.example','master-synthetic',models=('gpt-6-astra',),transport=httpx.MockTransport(server))
    with pytest.raises(m.ManagementUnavailable) as exc:
        client.create_key(secret=secret,user_id='employee-A',operation_id='op-A',label='test')
    assert secret not in str(exc.value) and len(calls)==1


@pytest.mark.parametrize('changed', [None, 'user_id', 'models', 'operation', 'routes', 'numeric-blocked'])
def test_hash_lookup_requires_exact_server_owned_identity(changed):
    m=module(); calls=[]; ref='a'*64
    info={'user_id':'employee-A','models':['gpt-6-astra'],'metadata':{'smartbrain_operation_id':'op-A'},'blocked':False,'allowed_routes':['llm_api_routes'],'key_type':'llm_api'}
    if changed=='user_id': info['user_id']='employee-B'
    if changed=='models': info['models']=[]
    if changed=='operation': info['metadata']['smartbrain_operation_id']='op-B'
    if changed=='routes': info['allowed_routes']=['*']
    if changed=='numeric-blocked': info['blocked']=1
    def server(request): calls.append(request);return httpx.Response(200,json={'key':ref,'info':info})
    client=m.LiteLLMManagement('https://gateway.example','master',models=('gpt-6-astra',),transport=httpx.MockTransport(server))
    if changed:
        with pytest.raises(m.ManagementUnavailable): client.lookup_key(ref,user_id='employee-A',operation_id='op-A')
    else:
        assert client.lookup_key(ref,user_id='employee-A',operation_id='op-A')=={'exists':True,'blocked':False}
    assert len(calls)==1 and calls[0].url.params['key']==ref


@pytest.mark.parametrize('status', [404,400,401,403,429,500])
def test_only_documented_not_found_is_absence(status):
    m=module()
    client=m.LiteLLMManagement('https://gateway.example','master',models=('gpt-6-astra',),transport=httpx.MockTransport(lambda r:httpx.Response(status,json={'error':'private error'})))
    if status==404: assert client.lookup_key('a'*64,user_id='employee-A',operation_id='op-A') is None
    else:
        with pytest.raises(m.ManagementUnavailable):client.lookup_key('a'*64,user_id='employee-A',operation_id='op-A')


def test_block_verifies_owned_hash_and_readback_before_reporting_stopped():
    m=module(); calls=[]; info={'user_id':'employee-A','models':['gpt-6-astra'],'metadata':{'smartbrain_operation_id':'op-A'},'key_type':'llm_api','allowed_routes':['llm_api_routes'],'blocked':False}
    def server(request):
        calls.append(request)
        if request.url.path=='/key/block':
            assert json.loads(request.content)=={'key':'a'*64};info['blocked']=True;return httpx.Response(200,json={'blocked':True})
        return httpx.Response(200,json={'key':'a'*64,'info':dict(info)})
    client=m.LiteLLMManagement('https://gateway.example','master',models=('gpt-6-astra',),transport=httpx.MockTransport(server))
    assert client.block_key('a'*64,user_id='employee-A',operation_id='op-A') is True
    assert [r.url.path for r in calls]==['/key/info','/key/block','/key/info']


@pytest.mark.parametrize('url', ['http://gateway.example','http://8.8.8.8','https://user:password@gateway.example','https://gateway.example/v1','https://gateway.example?key=secret','https://gateway.example/#fragment'])
def test_invalid_management_endpoint_is_rejected_before_network(url):
    with pytest.raises(ValueError):module().LiteLLMManagement(url,'master',models=('gpt-6-astra',))


def test_active_key_cannot_be_deleted_and_block_failure_cannot_be_called_success():
    m=module();calls=[];info={'user_id':'employee-A','models':['gpt-6-astra'],'metadata':{'smartbrain_operation_id':'op-A'},'key_type':'llm_api','allowed_routes':['llm_api_routes'],'blocked':False}
    def server(request):calls.append(request.url.path);return httpx.Response(200,json={'key':'a'*64,'info':info})
    client=m.LiteLLMManagement('https://gateway.example','master',models=('gpt-6-astra',),transport=httpx.MockTransport(server))
    with pytest.raises(m.ManagementUnavailable):client.delete_blocked_key('a'*64,user_id='employee-A',operation_id='op-A')
    assert calls==['/key/info']
    with pytest.raises(m.ManagementUnavailable):client.block_key('a'*64,user_id='employee-A',operation_id='op-A')


def test_delete_requires_verified_block_and_confirmed_absence():
    m=module();calls=[]
    def server(request):
        calls.append(request.url.path)
        if len(calls)==1:return httpx.Response(200,json={'key':'a'*64,'info':{'user_id':'employee-A','models':['gpt-6-astra'],'metadata':{'smartbrain_operation_id':'op-A'},'key_type':'llm_api','allowed_routes':['llm_api_routes'],'blocked':True}})
        if request.url.path=='/key/delete':assert json.loads(request.content)=={'keys':['a'*64]};return httpx.Response(200,json={})
        return httpx.Response(404,json={})
    client=m.LiteLLMManagement('https://gateway.example','master',models=('gpt-6-astra',),transport=httpx.MockTransport(server))
    assert client.delete_blocked_key('a'*64,user_id='employee-A',operation_id='op-A') is True
    assert calls==['/key/info','/key/delete','/key/info']
