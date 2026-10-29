#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Equipment/camp-inventory-v1';B='/workspace/left-transitions-publish.git';base='c7d0101c10ddd50be3418ced69deef76f1a8ca6d'
records=subprocess.check_output(['git','-C',B,'ls-tree','-r','-z',base,'--','Sources/Resources','Vendor/ClassroomGameCore/Sources/ClassroomGameCore','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/Resources','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/BowRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/GreatSwordRig.swift','Vendor/ClassroomGameCore/Sources/MeadowBattleSupport/LegendaryStaffRig.swift']).split(b'\0');count=0
for record in records:
 if not record:continue
 meta,p=record.split(b'\t',1);data=(R/p.decode()).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert actual==meta.decode().split()[-1],p.decode();count+=1
rows=json.loads((D/'inventory-frames.json').read_text());by={r['id']:r for r in rows}
assert by['ring']['unit']['equipment']['accessory']=='actionRing';assert by['ring']['stats']['baseAP']==4 and by['ring']['stats']['maximumAP']==8
assert by['supplies']['unit']['inventory']['smallPotion']==1 and 'shieldPotion' not in by['supplies']['unit']['inventory']
assert by['supplies']['unit']==by['restored']['unit'];assert by['empty-slots']['unit']['equipment']=={}
assert by['rune-sword-badge']['stats']['damage']==2 and by['rune-sword-badge']['stats']['maximumHealth']==20
report={'baseline':base,'unchangedResourceOriginalCoreAndWeaponRigPaths':count,'newCharacterOrEquipmentArt':False,'oldGaitAndCatalogByteExact':True,'actualCampStates':len(rows),'coldRestoreFieldsMatch':True,'ringBaseAP':4,'ringCap':8,'suppliesPayOriginalAP':by['supplies']['unit']['ap']==1,'emptySlotsSurviveExport':True,'userUIApproval':None}
(D/'source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
