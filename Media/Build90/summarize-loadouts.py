import json,collections
from pathlib import Path
D=Path('/workspace/build90-download')
rows=json.loads((D/'loadout-audit.json').read_text())
assert len(rows)==177
key=lambda r:(r['journey']['size'],r['journey']['seed'],r['journey']['role'],r['loadout']['id'])
assert len({key(r) for r in rows})==177
outcomes=collections.Counter(r['journey']['outcome'] for r in rows)
assert not set(outcomes)-{'victory','defeat','needsMovementCoins','goalNotMet'}
assert not outcomes['goalNotMet']
ids={'trainingSword-plain','huntingBow-leather-badge','greatSword-rune-ring','legendaryStaff-rune-ring','starlight-three','dragon-three','unarmed-rune-ring'}
smoke=[r for r in rows if r['journey']['size']==10 and r['journey']['seed']=='31827' and r['loadout']['id'] in ids]
smoke += [r for r in rows if r['journey']['size']==30 and r['journey']['seed']=='0' and r['loadout']['id'] in {'starlight-three','dragon-three'}]
assert len(smoke)==27
(D/'loadout-smoke.json').write_text(json.dumps(smoke,ensure_ascii=False,indent=2)+'\n')
actions=collections.Counter()
for r in rows:actions.update(r['journey']['actionsUsed'])
summary={'cases':177,'nativeSampleCases':27,'roles':sorted({r['journey']['role'] for r in rows}),'loadouts':len({r['loadout']['id'] for r in rows}),'outcomes':dict(outcomes),'byRole':{role:dict(collections.Counter(r['journey']['outcome'] for r in rows if r['journey']['role']==role)) for role in sorted({r['journey']['role'] for r in rows})},'actions':sum(r['journey']['actions'] for r in rows),'resumes':sum(r['journey']['resumes'] for r in rows),'stagedRestarts':sum(r['journey']['stagedRestarts'] for r in rows),'species':sorted({s for r in rows for s in r['journey']['foughtSpecies']}),'actionsUsed':dict(actions),'scope':'controlled starting equipment; fixed original mean-effect strategy, real dice/items/paid movement; not human win rate, natural equipment progression, or artwork approval','appSimulatorDeviceRun':False}
(D/'loadout-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
