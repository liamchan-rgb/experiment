#!/usr/bin/env python3
"""Re-export actual down transition assets and compositions and require byte identity."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];roots=['Art/Templates/P1-Neutral/down/walk-r7-transitions','Art/Parts/P1-v1/down/transitions-v1','Art/Templates/P1-Wardrobe/down/v10-transitions','Art/Review/P1/modular-down-transitions-v1'];D=R/roots[-1]
def snapshot():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in (R/root).rglob('*') if p.is_file() and p.suffix in ['.png','.gif','.ora','.svg','.json','.txt'] and p.name not in ['delivery.json','reexport-validation.json']}
before=snapshot()
for script in ['export-down-transitions.py','verify-down-transitions.py']:subprocess.run([sys.executable,str(R/'scripts'/script)],check=True)
after=snapshot();different=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)];assert not different,different
result={'status':'byte-identical','files':len(before),'differentFiles':different,'artApproval':None,'scope':'Retained old9 body and appearance poses plus4 explicit common-motion transitions,468 actual compositions and normal GIFs'};(D/'reexport-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
