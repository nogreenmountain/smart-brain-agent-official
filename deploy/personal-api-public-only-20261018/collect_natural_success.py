"""Accept only newly completed production requests; never asks for/reads raw keys."""
import json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/'.artifacts/personal-api-public-only-20261018-r1'
OUTPUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(HERE.parents[1]/'.artifacts/ai-workspace-records-scroll-20261008'))
from remote_io import remote
PROGRAM=r'''
import hashlib,json,pathlib,subprocess,sys,urllib.request,urllib.error
root=pathlib.Path('/srv/smartbrain/releases/personal-api-public-only-20261018-r1')
sys.path.insert(0,str(root/'release-tooling'))
import relay_release_core as core
stage=json.loads((root/'evidence/release-stage.json').read_text())
assert stage['stage']=='awaiting_smoke'
new=stage['new_id'];since=stage['awaiting_smoke_at']
c=json.loads(subprocess.check_output(['docker','inspect',new]))[0]
assert c['State']['Running'] and c['Image']=='sha256:28cd0714f8ebdb214ad259444e4a9123b1d5d6ec4b89bf93fd48a40bd19e1cb1'
code='SINCE='+repr(since)+'\n'+r"""
import json
from sqlalchemy import text
from agentops.common.orm import session_scope
with session_scope() as db:
 db.execute(text('SET TRANSACTION READ ONLY'))
 db.execute(text("SET LOCAL statement_timeout='5s'"));db.execute(text("SET LOCAL lock_timeout='2s'"))
 keys=dict(db.execute(text("SELECT count(*) AS rows,md5(string_agg((to_jsonb(k)-'last_used_at'-'updated_at')::text,',' ORDER BY id)) AS fingerprint FROM public.ai_gateway_keys k")).mappings().one())
 success=dict(db.execute(text("SELECT count(*) AS count,md5(string_agg(request_id::text,',' ORDER BY request_id)) AS request_digest,max(completed_at) AS latest FROM public.ai_gateway_events WHERE app_type='personal_api' AND status_code=200 AND content_complete AND started_at>=CAST(:since AS timestamptz) AND completed_at>=CAST(:since AS timestamptz)"),{'since':SINCE}).mappings().one())
 db.rollback()
print(json.dumps({'credentials':keys,'success':success},default=str))
"""
p=subprocess.run(['docker','exec','-i',new,'/app/.venv/bin/python','-'],input=code,text=True,capture_output=True,timeout=20)
assert p.returncode==0,'natural aggregation failed'
data=json.loads(p.stdout);assert data['credentials']=={'rows':42,'fingerprint':'ff1303631e132bee1c6bd06334c410db'},'credential identity changed'
if data['success']['count']==0:
 print(json.dumps({'status':'awaiting-natural-success','new_id':new,'credential_fingerprint_unchanged':True}));sys.exit(0)
try:
 with urllib.request.urlopen('http://192.168.10.146:9000/v1/models',timeout=8) as response:status=response.status
except urllib.error.HTTPError as e:status=e.code
assert status==403
now=core.utc_now()
receipt={'schema':core.AUTH_SMOKE_SCHEMA,'release':core.RELEASE,'observed_at':now.isoformat(),'new_container_id':new,'verification_kind':'natural_completed_request','successful_completed_requests':data['success']['count'],'public_gateway_authenticated':True,'credential_fingerprint_unchanged':True,'direct_windows_models_status':403,'request_id_sha256':hashlib.sha256(data['success']['request_digest'].encode()).hexdigest(),'smoke_summary_sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()}
core.validate_auth_smoke_receipt(receipt,now=now,awaiting_at=core.parse_timestamp(since,'awaiting'),new_container_id=new)
core.atomic_write_json(root/'evidence/authenticated-smoke-receipt.json',receipt)
print(json.dumps({'status':'natural-success-receipt-installed','receipt':receipt},sort_keys=True))
'''
result=json.loads(remote(PROGRAM,timeout=40))
(OUTPUT/'natural-success-observation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,sort_keys=True))
