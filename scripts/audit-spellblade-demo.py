#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Battle/spellblade-demo-v1';B='/workspace/left-transitions-publish.git';baseline='a4cd5af0c4180136b14136fd1524ebc7fe32b71c'
count=0
for row in subprocess.check_output(['git','-C',B,'ls-tree','-r','-z',baseline,'--','Sources/Resources','Vendor/ClassroomGameCore/Sources/ClassroomGameCore','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/BowRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/GreatSwordRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/LegendaryStaffRig.swift']).split(b'\0'):
 if not row:continue
 meta,p=row.split(b'\t',1);data=(R/p.decode()).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==meta.decode().split()[-1],p.decode();count+=1
rows=json.loads((D/'spellblade-frames.json').read_text());reports=[]
for scenario in dict.fromkeys(r['scenario'] for r in rows):
 group=[r for r in rows if r['scenario']==scenario];before=next(r for r in group if r['frame']==49);hit=next(r for r in group if r['impact'] is not None);pre=group[group.index(hit)-1]
 units=lambda r:{u['id']:u for u in r['units']};a,b,c=units(before),units(hit),units(pre)
 fields=['id','hp','maxHP','baseAP','maximumAP','attributeDamage','shield','ap','buff','buffRounds','weaponID','armorID','vitalsVisible','accessory']
 # Pose, idle breathing and monster preparation are animated before contact;
 # live equipment/resources/status remain unchanged until the receipt commits.
 assert {k:{f:v.get(f) for f in fields} for k,v in a.items()}=={k:{f:v.get(f) for f in fields} for k,v in c.items()},'Live resources mutated before contact: '+scenario
 assert before['hover'] and not hit['hover'];assert all(d.get('value') is not None for d in group[50]['dice'])
 if scenario.startswith('runeSlash'):
  roll=next(d for d in hit['receiptDice'] if d['source']=='damage');assert roll['formula']=={'sides':12,'count':2,'flat':2}
  assert len(roll['values'])==2;bonus=2+(3 if scenario.endswith('buffed') else 0)
  assert a['m1']['hp']-b['m1']['hp']==min(a['m1']['hp'],roll['total']+bonus)
  assert b['p1']['hp']-a['p1']['hp']==4 and b['p1']['shield']==4
  assert b['p2']['hp']==a['p2']['hp'] and b['p2']['shield']==a['p2']['shield']
  assert hit['recipients']==[{'unitID':'p1','heal':4,'shield':4,'buff':0}]
 elif scenario=='runeWard':
  assert not hit['receiptDice'];assert b['p1']['hp']-a['p1']['hp']==8 and b['p2']['hp']==18
  assert b['p1']['shield']==b['p2']['shield']==6
 else:
  assert not hit['receiptDice'];assert b['p1']['buff']==b['p2']['buff']==3
  assert b['p1']['shield']==b['p2']['shield']==4 and b['p1']['buffRounds']==b['p2']['buffRounds']==2
 if scenario.endswith('lethal'):
  assert b['m1']['hp']==0 and not b['m1']['vitalsVisible'];assert b['m1']['deathAge']==0
  assert any(label['text']=='−3' and label['at']==hit['time'] for label in hit['damageLabels'])
 reports.append({'scenario':scenario,'hitTime':hit['time'],'actorAPBefore':a['p1']['ap'],'actorAPAfter':b['p1']['ap'],'casterHeal':b['p1']['hp']-a['p1']['hp'],'targetDamage':a['m1']['hp']-b['m1']['hp'],'correctEffectScopes':True})
report={'baseline':baseline,'unchangedOriginalResourceCoreAndWeaponPaths':count,'ruleCatalogAndGaitUnchanged':True,'characterOrWeaponImagesRegenerated':False,'originalCampSaveFormatUnchanged':True,'actualReceiptChecks':reports,'frames':len(rows),'newArtApproval':None}
(D/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
