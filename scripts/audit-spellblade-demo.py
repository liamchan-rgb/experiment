#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,hashlib,sys
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/spellblade-demo-v1';B=R;baseline='6371e680b640e83be57c50e0dd01814d82f98eed'
if subprocess.run(['git','-C',B,'cat-file','-e',baseline+'^{commit}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','-C',B,'fetch','--quiet','--no-tags','--depth=1','origin',baseline],check=True)
asset_audit=json.loads(subprocess.check_output([sys.executable,str(R/'scripts/verify-rune-vfx-assets.py')]))
assert asset_audit['totalFrames']==40 and asset_audit['allChecksPassed']
count=0
for row in subprocess.check_output(['git','-C',B,'ls-tree','-r','-z',baseline,'--','Sources/Resources','Vendor/ClassroomGameCore/Sources/ClassroomGameCore','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/BowRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/GreatSwordRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/LegendaryStaffRig.swift']).split(b'\0'):
 if not row:continue
 meta,p=row.split(b'\t',1);rel=p.decode()
 if rel.startswith('Sources/Resources/Assets.xcassets/MeadowRuneSlash') and rel.split('/')[3].startswith('MeadowRuneSlash'):
  continue
 data=(R/rel).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==meta.decode().split()[-1],rel;count+=1
rows=json.loads((D/'spellblade-frames.json').read_text());reports=[]
light_requests={(r['kind'],r['frame']):r for r in json.loads((D/'spellblade-light-requests.json').read_text())}
for scenario in dict.fromkeys(r['scenario'] for r in rows):
 group=[r for r in rows if r['scenario']==scenario];before=next(r for r in group if r['frame']==49);hit_index=next(i for i,r in enumerate(group) if r['impact'] is not None);hit=group[hit_index];pre=group[hit_index-1]
 units=lambda r:{u['id']:u for u in r['units']};a,b,c=units(before),units(hit),units(pre)
 fields=['id','hp','maxHP','baseAP','maximumAP','attributeDamage','shield','gameHP','gameShield','ap','buff','buffRounds','weaponID','armorID','vitalsVisible','accessory']
 assert {k:{f:v.get(f) for f in fields} for k,v in a.items()}=={k:{f:v.get(f) for f in fields} for k,v in c.items()},'Live resources mutated before contact: '+scenario
 assert before['hover'] and not hit['hover'];assert all(d.get('value') is not None for d in group[50]['dice'])
 assert hit['statusCueAt']>hit['time'] and hit['statusCueAge']>=hit['age'],'Positive status presentation must wait for the VFX second half: '+scenario
 cue=next(r for r in group if r['time']>=hit['statusCueAt']);v=units(cue)
 hit_request=light_requests[(scenario+'-p1',hit['frame'])]
 cue_request=light_requests[(scenario+'-p1',cue['frame'])]
 assert not any(label['text'].startswith('＋') or label['text'].startswith('盾 ＋') for label in hit['damageLabels']),'Healing/shield feedback appeared at damage contact: '+scenario
 assert 'recoveryAge' not in hit_request and 'birth' not in hit_request,'Recovery/shield light request appeared at damage contact: '+scenario
 if scenario.startswith('runeSlash'):
  roll=next(d for d in hit['receiptDice'] if d['source']=='damage');assert roll['formula']=={'sides':12,'count':2,'flat':2}
  layers=hit['runes'].get('spriteLayers',[])
  assert any(vfx['asset']=='MeadowRuneSlashAttack11' for vfx in layers) and hit['travel']['x']>0,'Authored attack peak must coincide with the melee receipt'
  assert hit['runes']['motes'] and hit['runes']['glows'],'Hit particles and contact light must start with the receipt'
  assert {'white','cyan','blue','gold'} <= {m['color'] for r in group for m in r['runes']['motes']},'Rune Slash hit debris must use the authored palette'
  assert any(m.get('groundAge') is not None for r in group for m in r['runes']['motes']),'Rune Slash particles must reach the ground'
  peak=next(vfx for vfx in layers if vfx['asset']=='MeadowRuneSlashAttack11')
  point=hit['hitPoints']['m1'];assert abs(peak['center']['x']-(point['x']-52))<1e-6 and abs(peak['center']['y']-(point['y']-20))<1e-6
  assert len(roll['values'])==2;bonus=2+(3 if scenario.endswith('buffed') else 0)
  assert a['m1']['gameHP']-b['m1']['gameHP']==min(a['m1']['gameHP'],roll['total']+bonus)
  assert b['p1']['gameHP']-a['p1']['gameHP']==4 and b['p1']['gameShield']==max(a['p1']['gameShield'],4)
  assert b['p1']['hp']==c['p1']['hp'] and b['p1']['shield']==c['p1']['shield'],'Rune Slash positive status display must remain held at contact'
  assert v['p1']['hp']==v['p1']['gameHP'] and v['p1']['shield']==v['p1']['gameShield']
  assert any(label['text']=='＋4' and abs(label['at']-hit['statusCueAt'])<1e-6 for label in cue['damageLabels'])
  assert cue_request.get('recoveryAge',1)<0.021, 'Rune Slash healing should begin at the status cue'
  if b['p1']['gameShield']>a['p1']['gameShield']:
   assert cue_request.get('birth',1)<0.021, 'New Rune Slash shield should begin at the status cue'
  else:
   assert cue_request.get('birth') is None, 'An unchanged full shield must not be born again'
  assert cue_request['shield']==v['p1']['shield'] and cue_request['shield']>0
  assert b['p2']['gameHP']==a['p2']['gameHP'] and b['p2']['gameShield']==a['p2']['gameShield']
  assert hit['recipients']==[{'unitID':'p1','heal':4,'shield':4,'buff':0}]
 elif scenario=='runeWard':
  assert not hit['receiptDice'];assert b['p1']['gameHP']-a['p1']['gameHP']==8 and b['p2']['gameHP']==18
  assert b['p1']['gameShield']==b['p2']['gameShield']==6
  assert b['p1']['hp']==c['p1']['hp'] and b['p2']['hp']==c['p2']['hp']
  assert b['p1']['shield']==c['p1']['shield'] and b['p2']['shield']==c['p2']['shield']
  assert v['p1']['hp']==v['p1']['gameHP'] and v['p2']['shield']==v['p2']['gameShield']
  assert hit['runes'].get('spriteLayers') and not hit['runes']['strokes'],'Rune Ward cast art plays once at node level; status feedback starts after it reaches the second half'
  assert cue_request.get('recoveryAge',1)<0.021 and cue_request.get('birth',1)<0.021 and cue_request['shield']>0
 else:
  assert not hit['receiptDice'];assert b['p1']['buff']==b['p2']['buff']==3
  assert b['p1']['gameShield']==b['p2']['gameShield']==4 and b['p1']['buffRounds']==b['p2']['buffRounds']==2
  assert b['p1']['shield']==c['p1']['shield'] and b['p2']['shield']==c['p2']['shield']
  assert v['p1']['shield']==v['p1']['gameShield'] and v['p2']['shield']==v['p2']['gameShield']
  assert cue_request.get('birth',1)<0.021 and cue_request['shield']>0
 if scenario.endswith('lethal'):
  assert b['m1']['hp']==0 and not b['m1']['vitalsVisible'];assert b['m1']['deathAge']==0
  assert any(label['text']=='−3' and label['at']==hit['time'] for label in hit['damageLabels'])
 reports.append({'scenario':scenario,'hitTime':hit['time'],'statusCueAt':hit['statusCueAt'],'actorAPBefore':a['p1']['ap'],'actorAPAfter':b['p1']['ap'],'casterHealCommittedAtHit':b['p1']['gameHP']-a['p1']['gameHP'],'casterHealDisplayedAtCue':v['p1']['hp']-b['p1']['hp'],'targetDamage':a['m1']['gameHP']-b['m1']['gameHP'],'correctEffectScopes':True})
report={'baseline':baseline,'unchangedOriginalResourceCoreAndWeaponPaths':count,'sourcePacks':asset_audit['sourcePacks'],'runtimeFrameAssets':asset_audit['totalFrames'],'sourceAndRuntimeFramesPixelExact':asset_audit['allChecksPassed'],'ruleCatalogAndCampSaveFormatUnchanged':True,'characterOrWeaponImagesRegenerated':False,'actualReceiptChecks':reports,'frames':len(rows),'allChecksPassed':True,'newArtApproval':None}
(D/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
