"""Read-only proof that the known gateway's retained TCP connection is idle."""
import json, subprocess, sys

PROGRAM = r'''
import datetime,json,re,subprocess,urllib.request
cid='7e700797f7cc3981d41466cda2ae6af6c84d063308ab49cc4567b0fdbe231b20'
c=json.loads(subprocess.check_output(['docker','inspect',cid]))[0]
assert c['State']['Running'] and c['State']['StartedAt']=='2026-10-17T13:44:51.228032986Z'
ip=c['NetworkSettings']['Networks']['smartbrain_app']['IPAddress']
with urllib.request.urlopen('http://'+ip+':8000/health',timeout=5) as r:h=json.load(r)
q=h['concurrency']
assert h['status']=='ok' and all(q[k]==0 for k in ['active','waiting','database_in_use'])
assert q['max_active']==8 and q['max_waiting']==24 and q['database_limit']==3
s=subprocess.check_output(['nsenter','-t',str(c['State']['Pid']),'-n','ss','-Htin','dst','192.168.10.146:9000'],text=True,timeout=5)
lines=s.splitlines();assert len(lines)==2
f=lines[0].split();assert f[0]=='ESTAB' and f[1:3]==['0','0'] and f[4]=='192.168.10.146:9000'
port=int(f[3].rsplit(':',1)[1]);counts={}
for key in ['bytes_sent','bytes_received','lastsnd','lastrcv']:
 m=re.search(r'\b'+key+r':(\d+)',lines[1]);assert m;counts[key]=int(m.group(1))
assert counts['lastsnd']>=1800000 and counts['lastrcv']>=1800000
print(json.dumps({'cid':cid,'source_port':port,'active':0,'waiting':0,'database_in_use':0,'send_queue':0,'receive_queue':0,'counts':counts,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
'''

if __name__ == '__main__':
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','smartbrain-prod','sudo','-n','python3','-'], input=PROGRAM.encode(), capture_output=True, timeout=30)
    if result.returncode:
        print(json.dumps({'verified':False}))
        sys.exit(1)
    data=json.loads(result.stdout)
    print(json.dumps(data,sort_keys=True))
