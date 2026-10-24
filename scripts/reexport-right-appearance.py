#!/usr/bin/env python3
"""Require byte identity for tool-RGB baking,8 independent packages and208 real compositions."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];roots=['Art/Parts/P1-v1/right/appearance-v1','Art/Templates/P1-Wardrobe/right/v1-independent','Art/Review/P1/modular-right-appearance-v1'];D=R/roots[-1]
def snapshot():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in (R/root).rglob('*') if p.is_file() and p.suffix in ['.png','.gif','.ora','.svg','.json','.txt'] and p.name not in ['delivery.json','reexport-validation.json']}
before=snapshot()
for script in ['author-right-appearance-lighting.py','export-right-appearance.py','verify-right-appearance.py']:subprocess.run([sys.executable,str(R/'scripts'/script)],check=True)
after=snapshot();different=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)];assert not different,different
result={'status':'byte-identical','files':len(before),'differentFiles':different,'artApproval':None,'scope':'Right independent heads/clothes/lower/back carry,static tool RGB sources,208 actual compositions and normal GIFs'};(D/'reexport-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
