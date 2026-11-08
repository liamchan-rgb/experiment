import json,zipfile,plistlib,hashlib,struct,re,subprocess
from collections import Counter
from pathlib import Path
R=Path('/workspace/experiment');D=Path('/workspace/build93-download');M=R/'Media/Build93'
def gh(path):return json.loads(subprocess.check_output(['gh','api',path]))
s=json.loads((D/'source.json').read_text());run=gh('repos/liamchan-rgb/experiment/actions/runs/'+str(s['runID']))
assert run['conclusion']=='success' and run['head_sha']==s['sourceCommit']
jobs=gh('repos/liamchan-rgb/experiment/actions/runs/'+str(run['id'])+'/attempts/'+str(run['run_attempt'])+'/jobs')
assert all(j['conclusion'] in ['success','skipped'] for j in jobs['jobs'])
assert any(j['name']=='archive' and j['conclusion']=='success' for j in jobs['jobs'])
for title in ['Validate and test pure rules and generation','Audit complete journeys using pure rules only','Archive without running application or simulator']:
 assert any(x['name']==title and x['conclusion']=='success' for j in jobs['jobs'] for x in j['steps'])
art=next(x for x in gh('repos/liamchan-rgb/experiment/actions/runs/'+str(run['id'])+'/artifacts')['artifacts'] if x['id']==s['artifactID'])
assert art['workflow_run']['head_sha']==s['sourceCommit'] and not art['expired']
outer=D/'artifact.zip';digest=hashlib.sha256(outer.read_bytes()).hexdigest();assert art['digest']=='sha256:'+digest
with zipfile.ZipFile(outer) as z:
 assert z.testzip() is None
 z.extractall(D/'artifact')
a=D/'artifact';ipa=a/'MeadowJourney-b93.ipa';assert ipa.exists()
assert re.search(r'Executed 281 tests, with 0 failures',(a/'map-tests.log').read_text())
assert '** ARCHIVE SUCCEEDED **' in (a/'archive.log').read_text()
for marker in ['PASS: production WalkCycle','MeadowBattleEncounter checks passed','Battle VFX checks passed','PASS:8specified paths']:assert marker in (D/'workflow.log').read_text(),marker
counts=json.loads((a/'matrix-count-check.json').read_text());assert counts=={'baseline':27,'loadouts':27,'party':24,'partyPreview':16,'uniqueCasesMatched':True}
party=json.loads((a/'party-matrix.json').read_text())
classes=['adventurer','ranger','spellblade','dragonKnight']
expected={(10,'31827',x,y) for x in classes for y in classes}|{(n,'0',x,y) for n in [4,30] for x,y in [('adventurer','adventurer'),('ranger','ranger'),('spellblade','dragonKnight'),('dragonKnight','spellblade')]}
actual=[(r['journey']['size'],r['journey']['seed'],r['configuration']['playerClassID'],r['configuration']['companionClassID']) for r in party]
assert len(actual)==24 and len(set(actual))==24 and set(actual)==expected
assert all(r['journey']['role']==r['configuration']['playerClassID'] for r in party)
checks={'swiftTests':281,'fourRegressionsPassed':True,'deviceReleaseArchivePassed':True,'strictMatrixCounts':counts}
retained={}
with zipfile.ZipFile(ipa) as z,zipfile.ZipFile('/workspace/build92-download/artifact/MeadowJourney-b92.ipa') as old:
 assert z.testzip() is None
 checks['CRC']=True
 assert all(i.extract_version<=20 and not i.extra for i in z.infolist())
 with ipa.open('rb') as raw:
  for entry in z.infolist():
   raw.seek(entry.header_offset);h=raw.read(30)
   signature,version,flags,compression,mt,md,crc,packed,unpacked,nlen,elen=struct.unpack('<IHHHHHIIIHH',h)
   assert signature==0x04034b50 and version<=20 and elen==0 and compression==0 and not flags&1
 checks['classicZIP2WithoutExtras']=True
 prefix='Payload/MeadowJourney.app/'
 info=plistlib.loads(z.read(prefix+'Info.plist'))
 assert info['CFBundleShortVersionString']=='1.6.66' and info['CFBundleVersion']=='93' and info['CFBundleSupportedPlatforms']==['iPhoneOS']
 checks['version']='1.6.66/93'
 checks['buildSDK']={k:info.get(k) for k in ['DTSDKName','DTXcode','DTXcodeBuild','MinimumOSVersion']}
 exe=z.read(prefix+info['CFBundleExecutable']);assert struct.unpack('<II',exe[:8])==(0xfeedfacf,0x100000c)
 assert exe!=old.read(prefix+info['CFBundleExecutable'])
 mode=z.getinfo(prefix+info['CFBundleExecutable']).external_attr>>16;assert mode&0o755==0o755
 checks['arm64ExecutablePermissions']=oct(mode);checks['executableSHA256']=hashlib.sha256(exe).hexdigest()
 metal=[n for n in z.namelist() if n.endswith('.metallib')];assert metal and all(z.getinfo(n).file_size>0 for n in metal)
 assert all(z.read(n)[:4]==b'MTLB' for n in metal)
 checks['MetalLibraries']={n:hashlib.sha256(z.read(n)).hexdigest() for n in metal}
 car=z.read(prefix+'Assets.car');assert car
 for name in ['Slime','Wolf','GoblinArcher','StoneGuardian','CaveTroll','RuinDragon']:
  for clip in ['Motion','Death']:assert ('MeadowMonster'+name+clip).encode() in car
 for name in ['MeadowMonsterVisuals','MeadowBattleHeroConfiguration','BattleVFXConfig','MeadowBattleHeroConfigurationV2','MeadowBattleWardenMotion','MeadowBattleHeroAnimationV2']:assert name.encode() in car
 checks['compiledAssetCatalogSHA256']=hashlib.sha256(car).hexdigest()
 checks['compiledCatalogMatchesBuild92Bytes']=car==old.read(prefix+'Assets.car')
 checks['12MonsterAtlasesAnd6Datasets']=True
 names=[n for n in z.namelist() if n.endswith(('SceneMap.json','hero-gait.json','initial-content.json'))];assert len(names)>=3
 for n in names:
  assert z.read(n)==old.read(n),n
  retained[n]=hashlib.sha256(z.read(n)).hexdigest()
resources=json.loads((a/'resource-sources.json').read_text());assert resources==json.loads((D/'resource-sources.json').read_text()) and len(resources)>100
baseline=json.loads((R/'Downloads/MeadowJourney-build92.json').read_text())['sourceCommit']
assert subprocess.check_output(['git','diff','--name-only',baseline,s['sourceCommit'],'--','Sources/Resources'],cwd=R,text=True).strip()==''
checks['sourceResourceFilesUnchangedFromBuild92']=len(resources)
assets=json.loads((a/'asset-catalog.json').read_text());assert isinstance(assets,list) and len(assets)>12
checks['systemAssetutilParsedCatalogEntries']=len(assets)
def eq(x,y,path='root'):
 if isinstance(x,dict):
  assert x.keys()==y.keys(),path
  for k in x:eq(x[k],y[k],path+'.'+k)
 elif isinstance(x,list):
  assert len(x)==len(y),(path,len(x),len(y))
  for i,(u,v) in enumerate(zip(x,y)):eq(u,v,path+f'[{i}]')
 elif isinstance(x,float) or isinstance(y,float):assert abs(x-y)<1e-8,(path,x,y)
 else:assert x==y,(path,x,y)
files=['encounters-default.json','encounters-max.json','balance-default.json','balance-max.json','guidance-default.json','guidance-max.json','equipment-default.json','equipment-max.json','journey-audit.json','loadout-smoke.json']
for n in files+['party-matrix.json','party-preview.json']:
 eq(json.loads((a/n).read_text()),json.loads((D/n).read_text()))
 checks[n]=('Native equal preserved Build92 reference' if n.startswith('party-') else 'Native/current rules equal Build92 reference')+'; numeric distance error <1e-8'
M.mkdir(parents=True,exist_ok=True)
for n,data in [('native-run.json',run),('workflow-jobs.json',jobs),('artifact.json',art)]: (M/n).write_text(json.dumps(data,indent=2)+'\n')
for n in files+['party-matrix.json','party-preview.json','party-matrix.log','map-tests.log','archive.log','journey-audit.log','loadout-smoke.log','matrix-count-check.json','resource-sources.json','asset-catalog.json']:(M/n).write_bytes((a/n).read_bytes())
(M/'workflow.log').write_bytes((D/'workflow.log').read_bytes())
for name in ['tests','readout-tests','road-motion','battle-encounter','battle-effects','modular-locomotion']:
 p=Path('/workspace/build93-'+name+'.log')
 if p.exists():(M/('linux-'+name+'.log')).write_bytes(p.read_bytes())
(M/'reference-party-matrix.json').write_bytes((D/'party-matrix.json').read_bytes())
(M/'reference-party-preview.json').write_bytes((D/'party-preview.json').read_bytes())

(M/'verify-package.py').write_bytes(Path(__file__).read_bytes())
base=json.loads((a/'journey-audit.json').read_text());loadouts=json.loads((a/'loadout-smoke.json').read_text())
summary={'baselineCases':len(base),'baselineOutcomes':dict(Counter(x['outcome'] for x in base)),'loadoutCases':len(loadouts),'loadoutOutcomes':dict(Counter(x['journey']['outcome'] for x in loadouts)),'baselineActions':sum(x['actions'] for x in base),'loadoutActions':sum(x['journey']['actions'] for x in loadouts),'scope':'27 default and 27 loadout cases compared to Build92; 24 party journeys compared to Build92 reference; not human win rate','appSimulatorDeviceRun':False}
party=json.loads((a/'party-matrix.json').read_text())
summary.update({'partyCases':len(party),'partyOutcomes':dict(Counter(x['journey']['outcome'] for x in party)),'partyActions':sum(x['journey']['actions'] for x in party),'partyResumes':sum(x['journey']['resumes'] for x in party),'partyStagedRestarts':sum(x['journey']['stagedRestarts'] for x in party)})
(M/'journey-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
r={**s,'version':'1.6.66','build':93,'runAttempt':run['run_attempt'],'artifactSHA256':digest,'ipaBytes':ipa.stat().st_size,'ipaSHA256':hashlib.sha256(ipa.read_bytes()).hexdigest(),'tests':281,'checks':checks,'preservedBuild92JSON':retained,'resourceBaselineSource':baseline,'appSimulatorDeviceRun':False}
(M/'verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
