import concurrent.futures,subprocess,json,hashlib,time
from pathlib import Path
R=Path('/workspace/experiment');D=Path('/workspace/build90-download');C=D/'loadout-cases';C.mkdir(exist_ok=True)
exe=R/'Vendor/ClassroomGameCore/.build/release/MeadowCampaignReview'
roles=['adventurer','spellblade','dragonKnight']
kits=[w+'-'+p for w in ['trainingSword','huntingBow','greatSword','legendaryStaff'] for p in ['plain','leather-badge','rune-ring']]+['starlight-two','starlight-three','dragon-two','dragon-three','unarmed-rune-ring']
jobs=[(10,str(seed),role,kit) for seed in [0,31827,18446744073709551615] for role in roles for kit in kits]
jobs += [(size,str(seed),role,kit) for size in [4,30] for seed in [0,31827] for role in roles for kit in ['starlight-three','dragon-three']]
assert len(jobs)==177
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert head=='a89417d92ba537f748a140792a21dfa9dac2b703'
(D/'loadout-execution.json').write_text(json.dumps({'sourceCommit':head,'archiveSourceCommit':'ca150c5ea5d36af7db17bd35c25afccd8710b013','binarySHA256':hashlib.sha256(exe.read_bytes()).hexdigest(),'configuration':'Release','platform':'Linux','checkpointed':True,'workers':2,'cases':177,'appSimulatorDeviceRun':False},indent=2)+'\n')
def check(row,job):
 size,seed,role,kit=job;j=row['journey'];assert (j['size'],j['seed'],j['role'],row['loadout']['id'])==(size,seed,role,kit)
def execute(pair):
 i,job=pair;p=C/f'{i:03d}.json'
 if p.exists():
  row=json.loads(p.read_text());check(row,job);return i,row
 size,seed,role,kit=job
 result=subprocess.run([str(exe),'--loadout',kit,'--role',role,'--size',str(size),'--seed',seed],cwd=R,capture_output=True,text=True,timeout=600)
 (C/f'{i:03d}.log').write_text(result.stderr)
 if result.returncode:raise RuntimeError(f'Case {i} failed, see {C}/{i:03d}.log')
 data=json.loads(result.stdout);assert len(data)==1;row=data[0];check(row,job)
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
 (C/f'{i:03d}.log').write_text(result.stderr)
 return i,row
rows={}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for result in concurrent.futures.as_completed([pool.submit(execute,x) for x in enumerate(jobs)]):
  i,row=result.result();rows[i]=row;print(f'{len(rows)}/177 finished {i}: {jobs[i]}',flush=True)
assert len(rows)==177
(D/'loadout-audit.json').write_text(json.dumps([rows[i] for i in range(177)],ensure_ascii=False,indent=2)+'\n')
(D/'loadout-audit.log').write_text(''.join((C/f'{i:03d}.log').read_text() for i in range(177)))
print('COMPLETE: 177 real CLI results saved',flush=True)
