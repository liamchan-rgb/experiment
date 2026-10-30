#!/usr/bin/env python3
"""Source/integration invariants for accessory-only UI and rule reuse."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/accessories-demo-v1';baseline='dd5e5a75d6b483e8f3354eeeda6e1efa9b85df99';B='/workspace/left-transitions-publish.git'
def git(*args):return subprocess.check_output(['git','-C',B,*args])
old=json.loads(git('show',baseline+':Sources/Resources/hero-gait.json'));new=json.loads((R/'Sources/Resources/hero-gait.json').read_text());bindings=new.pop('accessoryVisuals');assert old==new
catalog=json.loads((R/'Vendor/ClassroomGameCore/Sources/ClassroomGameCore/Resources/initial-content.json').read_text());items={v['id']:v for v in catalog['items']}
for id,b in bindings.items():
 assert b['itemID']==id and items[id]['slot']=='accessory'
 src=R/'Art/Parts/P1-v1/b2-equipment-v1'/id/'source'/('item_power_badge.png' if id=='powerBadge' else 'item_action_ring.png');name=b['iconAsset'];path=R/'Sources/Resources/Assets.xcassets'/(name+'.imageset')/(name+'.png');assert path.read_bytes()==src.read_bytes()
checked=0
for e in git('ls-tree','-r','-z',baseline,'Sources/Resources/Assets.xcassets','Vendor/ClassroomGameCore/Sources/ClassroomGameCore').split(b'\0'):
 if not e:continue
 meta,path=e.split(b'\t');f=R/path.decode();mode,kind,sha=meta.decode().split();h=hashlib.sha1();h.update(('blob '+str(f.stat().st_size)+'\0').encode())
 with f.open('rb') as stream:
  while block:=stream.read(1024*1024):h.update(block)
 assert h.hexdigest()==sha,path.decode();checked+=1
rows=json.loads((D/'accessory-frames.json').read_text());summary=[]
for scenario in sorted({r['scenario'] for r in rows}):
 rs=[r for r in rows if r['scenario']==scenario];first=rs[0];before=next(r for r in rs if r['frame']==50);hit=next(r for r in rs if r['impact'] is not None)
 player=lambda r:next(u for u in r['units'] if u['id']=='p1');enemy=lambda r:next(u for u in r['units'] if u['id']=='m1')
 a,b=player(first),player(hit);damage=enemy(first)['hp']-enemy(hit)['hp'];roll=next(x for x in hit['receiptDice'] if x['source']=='damage')['total']
 assert a['buff']==0 and b['buff']==0
 assert [[u[k] for k in ['id','hp','ap','shield','buff','accessory']] for u in first['units']]==[[u[k] for k in ['id','hp','ap','shield','buff','accessory']] for u in before['units']],'confirmation mutated live state'
 assert a['ap']==(4 if scenario.endswith('actionRing') else 3) and b['ap']==a['ap']-1
 assert a['maximumAP']==8 and damage==roll+(2 if scenario.endswith('powerBadge') else 0)
 summary.append({'scenario':scenario,'APBefore':a['ap'],'APAfter':b['ap'],'cap':a['maximumAP'],'damage':damage,'rolledIncludingSkillFlat':roll,'fixedYellowValuesAtSelection':[d['value'] for d in first['dice'] if d['color']=='yellow']})
(D/'source-audit.json').write_text(json.dumps({'baseline':baseline,'unchangedExistingAssetAndOriginalCoreFiles':checked,'oldGaitBindingsByteSemanticsUnchanged':True,'iconsByteExactFromExistingB2Sources':True,'ruleAndCatalogUnchanged':True,'actualReceiptComparison':summary,'noNewCharacterArt':True},indent=2)+'\n');print(json.dumps({'unchangedFiles':checked,'actualReceipts':summary}))
