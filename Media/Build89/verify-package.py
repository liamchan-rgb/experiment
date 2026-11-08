import json,zipfile,plistlib,hashlib,stat,struct,re,subprocess
from pathlib import Path
R=Path('/workspace/experiment');D=Path('/workspace/build89-download');M=R/'Media/Build89'
def gh(path):return json.loads(subprocess.check_output(['gh','api',path]))
source=json.loads((D/'source.json').read_text());run=gh('repos/liamchan-rgb/experiment/actions/runs/'+str(source['runID']))
assert run['conclusion']=='success' and run['head_sha']==source['sourceCommit']
jobs=gh('repos/liamchan-rgb/experiment/actions/runs/'+str(run['id'])+'/attempts/'+str(run['run_attempt'])+'/jobs')
assert all(j['conclusion']=='success' for j in jobs['jobs'])
for title in ['Validate and test pure rules and generation','Archive without running application or simulator','Audit complete journeys using pure rules only']:
 assert any(s['name']==title and s['conclusion']=='success' for j in jobs['jobs'] for s in j['steps'])
artifacts=gh('repos/liamchan-rgb/experiment/actions/runs/'+str(run['id'])+'/artifacts')['artifacts']
artifact=next(a for a in artifacts if a['id']==source['artifactID'])
assert artifact['workflow_run']['head_sha']==source['sourceCommit'] and not artifact['expired']
outer=D/'artifact.zip';digest=hashlib.sha256(outer.read_bytes()).hexdigest();assert artifact['digest']=='sha256:'+digest
with zipfile.ZipFile(outer) as z:
 assert z.testzip() is None
 z.extractall(D/'artifact')
a=D/'artifact';ipa=a/'MeadowJourney-b89.ipa';assert ipa.exists()
log=(a/'map-tests.log').read_text();archive=(a/'archive.log').read_text()
assert re.search(r'Executed 253 tests, with 0 failures',log),log[-2500:]
assert '** ARCHIVE SUCCEEDED **' in archive
workflow=(D/'workflow.log').read_text()
for marker in ['PASS: production WalkCycle','MeadowBattleEncounter checks passed','Battle VFX checks passed','PASS:8specified paths']:assert marker in workflow,marker
checks={};retained={}
with zipfile.ZipFile(ipa) as z,zipfile.ZipFile(D/'MeadowJourney-b88.ipa') as old:
 assert z.testzip() is None
 checks['CRC']=True
 assert all(i.extract_version<=20 and not i.extra for i in z.infolist())
 with ipa.open('rb') as raw:
  for entry in z.infolist():
   raw.seek(entry.header_offset);header=raw.read(30)
   signature,version,flags,compression,mt,md,crc,packed,unpacked,nlen,elen=struct.unpack('<IHHHHHIIIHH',header)
   assert signature==0x04034b50 and version<=20 and elen==0 and compression==0 and not flags&1
 checks['classicZIP2WithoutExtras']=True
 prefix='Payload/MeadowJourney.app/'
 info=plistlib.loads(z.read(prefix+'Info.plist'))
 assert info['CFBundleShortVersionString']=='1.6.62' and info['CFBundleVersion']=='89'
 assert info['CFBundleSupportedPlatforms']==['iPhoneOS']
 checks['version']='1.6.62/89'
 exe=z.read(prefix+info['CFBundleExecutable']);assert struct.unpack('<II',exe[:8])==(0xfeedfacf,0x100000c)
 assert exe!=old.read(prefix+info['CFBundleExecutable'])
 checks['executableDiffersFromBuild88']=True
 checks['executableSHA256']=hashlib.sha256(exe).hexdigest()
 mode=z.getinfo(prefix+info['CFBundleExecutable']).external_attr>>16;assert mode&0o755==0o755
 checks['arm64ExecutablePermissions']=oct(mode)
 assert z.getinfo(prefix+'Assets.car').file_size>0
 assert any(n.endswith('.metallib') for n in z.namelist())
 car=z.read(prefix+'Assets.car')
 for name in ['Slime','Wolf','GoblinArcher','StoneGuardian','CaveTroll','RuinDragon']:
  for clip in ['Motion','Death']:assert ('MeadowMonster'+name+clip).encode() in car
 for name in ['MeadowMonsterVisuals','MeadowBattleHeroConfiguration','BattleVFXConfig','MeadowBattleHeroConfigurationV2','MeadowBattleWardenMotion','MeadowBattleHeroAnimationV2']:assert name.encode() in car
 assert car==old.read(prefix+'Assets.car')
 checks['MetalAssets12MonsterAtlases6DatasetsAndFullCatalogUnchanged']=True
 retained[prefix+'Assets.car']=hashlib.sha256(car).hexdigest()
 names=[n for n in z.namelist() if n.endswith(('SceneMap.json','hero-gait.json','initial-content.json'))]
 assert len(names)>=3
 for n in names:
  assert z.read(n)==old.read(n),n
  retained[n]=hashlib.sha256(z.read(n)).hexdigest()
for file in ['encounters-default.json','encounters-max.json']:
 native=json.loads((a/file).read_text());local=json.loads((D/file).read_text())
 assert len(native)==len(local)
 for x,y in zip(native,local):
  assert x['nodeID']==y['nodeID'] and x['band']==y['band'] and x['templates']==y['templates']
  assert abs(x['distance']-y['distance'])<1e-8
 checks[file]='Mac/Linux roster identical; road distance error <1e-8'
def equivalent(x,y):
 if isinstance(x,dict):
  assert x.keys()==y.keys()
  for key in x:equivalent(x[key],y[key])
 elif isinstance(x,list):
  assert len(x)==len(y)
  for a,b in zip(x,y):equivalent(a,b)
 elif isinstance(x,float) or isinstance(y,float):assert abs(x-y)<1e-8
 else:assert x==y,(x,y)
for name in ['balance-default.json','balance-max.json','journey-audit.json','guidance-default.json','guidance-max.json']:
 equivalent(json.loads((a/name).read_text()),json.loads((D/name).read_text()))
 checks[name]='Mac/Linux saved readouts and provisions equivalent; physical distance error <1e-8'
M.mkdir(parents=True,exist_ok=True)
for name,data in [('native-run.json',run),('workflow-jobs.json',jobs),('artifact.json',artifact)]:
 (M/name).write_text(json.dumps(data,indent=2)+'\n')
for n in ['map-tests.log','archive.log','encounters-default.json','encounters-max.json','balance-default.json','balance-max.json','guidance-default.json','guidance-max.json','journey-audit.json','journey-audit.log']:(M/n).write_bytes((a/n).read_bytes())
(M/'workflow.log').write_bytes((D/'workflow.log').read_bytes())
for short in ['tests','road-motion','battle-encounter','battle-effects','modular-locomotion']:
 path=Path('/tmp/build89-'+short+'.log')
 if path.exists():(M/('linux-'+short+'.log')).write_bytes(path.read_bytes())
(M/'journey-summary.json').write_bytes((D/'journey-summary.json').read_bytes())
(M/'layout-check.json').write_bytes((D/'layout-check.json').read_bytes())
(M/'earlier-candidate.json').write_bytes((D/'earlier-candidate.json').read_bytes())
(M/'verify-package.py').write_bytes(Path(__file__).read_bytes())
report={**source,'version':'1.6.62','build':89,'runAttempt':run['run_attempt'],'artifactSHA256':digest,'ipaBytes':ipa.stat().st_size,'ipaSHA256':hashlib.sha256(ipa.read_bytes()).hexdigest(),'tests':253,'checks':checks,'preservedBuild88Resources':retained,'appSimulatorDeviceRun':False}
(M/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
