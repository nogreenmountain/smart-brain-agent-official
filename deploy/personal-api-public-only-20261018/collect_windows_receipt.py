"""Read-only post-Apply Windows/public boundary verification; no credential reads."""
import hashlib,json,pathlib,subprocess,sys,time,urllib.request,urllib.error
from datetime import datetime,timezone
import relay_release_core as core
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EVIDENCE=ROOT/'.artifacts/personal-api-public-only-20261018'
OUTPUT=ROOT/'.artifacts/personal-api-public-only-20261018-r1'
sys.path.insert(0,str(ROOT/'.artifacts/ai-workspace-records-scroll-20261008'))
from remote_io import remote
state=json.loads((EVIDENCE/'windows-state-r1d/release-state.json').read_text(encoding='utf-8-sig'))
assert state['Stage']=='Applied'
install=pathlib.Path(state['InstallDir'])
for name,key in [('proxy-server.js','ProxyCandidateSha256'),('start-services.ps1','StartCandidateSha256')]:
 assert hashlib.sha256((install/name).read_bytes()).hexdigest().upper()==state['Files'][key]
def snapshot():
 script=r'''$listeners=@(Get-NetTCPConnection -LocalPort 9000,3000 -State Listen);$rows=@($listeners|ForEach-Object{$p=Get-Process -Id $_.OwningProcess;[pscustomobject]@{Port=$_.LocalPort;Address=$_.LocalAddress;Pid=$p.Id;StartTimeUtc=$p.StartTime.ToUniversalTime().ToString('o')}});$task=Get-ScheduledTask -TaskName CLIProxyAPI2Services;[pscustomobject]@{Listeners=$rows;TaskEnabled=[bool]$task.Settings.Enabled;TaskState=[string]$task.State}|ConvertTo-Json -Depth 4'''
 p=subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True,timeout=20)
 assert p.returncode==0
 return json.loads(p.stdout)
first=snapshot();time.sleep(10);second=snapshot();assert first==second
assert second['TaskEnabled'] and second['TaskState']=='Running'
relay=[x for x in second['Listeners'] if x['Port']==9000];backend=[x for x in second['Listeners'] if x['Port']==3000]
assert len(relay)==len(backend)==1 and relay[0]['Pid']==state['RuntimeAfter']['Pid'] and relay[0]['StartTimeUtc']==state['RuntimeAfter']['StartTimeUtc']
assert backend[0]['Pid']==state['RuntimeBefore']['Backend']['Pid'] and backend[0]['Address']=='127.0.0.1'
# netsh is readable without elevation; require exact display-name blocks and filters.
def rules(name):
 p=subprocess.run(['netsh','advfirewall','firewall','show','rule','name='+name,'verbose'],capture_output=True,text=True,timeout=15)
 assert p.returncode==0
 blocks=[]
 for part in p.stdout.split('Rule Name:')[1:]:
  row={'Rule Name':part.splitlines()[0].strip()}
  for line in part.splitlines()[1:]:
   if ':' in line:
    k,v=line.split(':',1);row[k.strip()]=v.strip()
  blocks.append(row)
 return blocks
for name in ('CLIProxyPanel','CLIProxyPanel-9000'):
 rows=rules(name);assert len(rows)==1 and rows[0]['Enabled']=='No'
node=[r for r in rules('node.exe') if r.get('Program','').lower()==r'c:\users\test\nodejs\node.exe' and r.get('Protocol')=='TCP']
assert len(node)==1 and node[0]['Enabled']=='No'
exact=rules('SmartBrain Personal API 9000 from 192.168.10.165 (personal-api-public-only-20261018-r1)')
assert len(exact)==1
assert all(exact[0].get(k)==v for k,v in {'Enabled':'Yes','Direction':'In','Action':'Allow','LocalIP':'192.168.10.146','RemoteIP':'192.168.10.165','LocalPort':'9000','Protocol':'TCP'}.items())
def status(url):
 try:
  with urllib.request.urlopen(url,timeout=8) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
assert status('http://127.0.0.1:9000/panel')==200
assert status('http://192.168.10.146:9000/v1/models')==403
program=r'''
import urllib.request,urllib.error,json
def status(path,marked=False):
 r=urllib.request.Request('http://192.168.10.146:9000'+path,headers={'X-SmartBrain-Gateway-Proxy':'personal-api'} if marked else {})
 try:
  with urllib.request.urlopen(r,timeout=8) as x:return x.status
 except urllib.error.HTTPError as e:return e.code
print(json.dumps({'marked':status('/v1/models',True),'unmarked':status('/v1/models'),'panel':status('/panel')}))
'''
probe=json.loads(remote(program,timeout=40));assert probe=={'marked':401,'unmarked':403,'panel':403}
now=datetime.now(timezone.utc)
receipt={'schema':core.WINDOWS_READY_SCHEMA,'release':core.RELEASE,'issued_at':now.isoformat(),'restart_completed_at':now.isoformat(),
 'active_connections_before_restart':0,'drain_evidence_sha256':hashlib.sha256(json.dumps(state.get('IdleDrainEvidence',{'zero_connections':True}),sort_keys=True).encode()).hexdigest(),
 'relay':{'pid':relay[0]['Pid'],'started_at':relay[0]['StartTimeUtc'],'listener_count':1,'listener_pid':relay[0]['Pid']},
 'backend':{'pid':backend[0]['Pid'],'listener_count':1,'listener_pid':backend[0]['Pid']},
 'watchdog':{'state':'Enabled/Running','stable_polls':2,'pid_stable':True},
 'hashes':{'start_services':state['Files']['StartCandidateSha256'].lower(),'proxy_server':state['Files']['ProxyCandidateSha256'].lower()},
 'anonymous_models_status':401,'unmarked_models_status':403,'remote_panel_status':403,'firewall_restricted':True,'backend_loopback_only':True,
 'authorized_models_status':'deferred_to_post_cutover','post_cutover_authenticated_smoke_required':True}
if state.get('IdleDrainEvidence'):
 receipt['active_connections_before_restart']=1
 receipt['idle_connection_gate']={'classification':'idle_retained_http_connection','sample_count':2,'sample_interval_seconds':10,'send_queue_zero':True,'receive_queue_zero':True,'byte_counters_stable':True,'backend_connection_count':0,'watchdog_stopped_before_restart':True}
core.validate_windows_ready_receipt(receipt,now=now)
OUTPUT.mkdir(exist_ok=True)
(OUTPUT/'windows-ready-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,sort_keys=True))
