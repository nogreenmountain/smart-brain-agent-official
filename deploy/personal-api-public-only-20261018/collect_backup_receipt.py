"""Read-only receipt for the exact newly completed online backup."""
import base64, json, pathlib, sys
HERE=pathlib.Path(__file__).resolve().parent
OUTPUT=HERE.parents[1]/'.artifacts/personal-api-public-only-20261018-r1'
OUTPUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(HERE.parents[1]/'.artifacts/ai-workspace-records-scroll-20261008'))
from remote_io import remote
core64=base64.b64encode((HERE/'relay_release_core.py').read_bytes()).decode()
runner64=base64.b64encode((HERE/'relay_remote_runner.py').read_bytes()).decode()
program=f'''import base64,types,sys
core=types.ModuleType('relay_release_core');sys.modules['relay_release_core']=core
exec(compile(base64.b64decode({core64!r}),'reviewed-core','exec'),core.__dict__)
runner=types.ModuleType('release_readonly');exec(compile(base64.b64decode({runner64!r}),'reviewed-runner','exec'),runner.__dict__)
'''+r'''
import hashlib,json,pathlib,subprocess,re
ops=runner.RealOps();state=ops.backup_state();core.validate_backup_systemd_state(state)
assert state['InvocationID']=='11735eb839e54c2b8799b3d424cbfd80'
root=pathlib.Path('/srv/smartbrain-backups/backups');batch=root/'20261018T112315Z'
start=json.loads(pathlib.Path('/srv/smartbrain/acceptance/personal-api-public-only-20261018-backup/start-intent.json').read_text())
assert start['capacity_exit']==0 and start['checker_sha256']==core.EXPECTED_CAPACITY_CHECKER_SHA256
journal=subprocess.check_output(['journalctl','_SYSTEMD_INVOCATION_ID='+state['InvocationID'],'-o','json','--no-pager'],text=True)
budget=[];ok=0
for line in journal.splitlines():
 d=json.loads(line);m=d.get('MESSAGE','');match=re.fullmatch(r'backup capacity passed: transient budget=(\d+) bytes, configured reserves retained',m)
 if match:budget.append(int(match[1]))
 if m.endswith(': OK'):ok+=1
assert budget and len(set(budget))==1
# The real backup sources deploy/ubuntu/.env (not stack.conf).
config=runner.CAPACITY_CHECKER.parent/'.env'
assert config.stat().st_mtime < core.parse_timestamp(start['at'],'preflight').timestamp()
p=subprocess.run(['bash','-c','set -a; . "$1"; exec python3 -c "$2"','read-reserve',str(config),"import os;print(int(os.environ.get('MIN_BACKUP_FREE_GB','300')))"],capture_output=True,text=True,check=True)
reserve=int(p.stdout)*1024**3
required=reserve+budget[0]
assert start['free']>=required
registered=ops.verify_backup_registration();assert registered==20
core.validate_static_capacity(ops.read_static_capacity(),now=core.utc_now())
sums=(batch/'SHA256SUMS').read_text().splitlines()
assert ok>=len(sums),'backup self checksum evidence incomplete'
small=0
for line in sums:
 digest,name=line.split(None,1);name=name.lstrip('*').lstrip('./');path=batch/name
 assert path.resolve().is_relative_to(batch.resolve()) and path.is_file()
 if path.stat().st_size<=4*1024**2:
  assert hashlib.sha256(path.read_bytes()).hexdigest()==digest;small+=1
now=core.utc_now()
r={'schema':core.FRESH_BACKUP_SCHEMA,'release':core.RELEASE,'issued_at':now.isoformat(),'completed_at':now.isoformat(),'invocation_id':state['InvocationID'],
 'exec_main_start_timestamp_monotonic':state['ExecMainStartTimestampMonotonic'],'exec_main_exit_timestamp_monotonic':state['ExecMainExitTimestampMonotonic'],
 'backup_dir':str(batch),'backup_state_sha256':core.sha256_file(batch/'backup-state.json'),'sha256sums_sha256':core.sha256_file(batch/'SHA256SUMS'),
 'registered_services':registered,'dynamic_capacity':{'checker_sha256':start['checker_sha256'],'checked_at':start['at'],'exit_code':0,'free_bytes':start['free'],'required_bytes':required},
 'self_checksum_ok':ok,'checksum_entries':len(sums),'independent_small_files':small,'scope':'online backup; no frozen/full restore acceptance'}
core.validate_fresh_backup_receipt(r,state,now=now,backup_root=root)
print(json.dumps(r,sort_keys=True))
'''
result=json.loads(remote(program,timeout=120))
(OUTPUT/'fresh-backup-receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,sort_keys=True))
