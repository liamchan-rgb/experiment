#!/usr/bin/env python3
"""Reproduce fixed-source lighting, eight independent packages and208 actual assemblies byte for byte."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];roots=[R/'Art/Parts/P1-v1/down-right/appearance-v1',R/'Art/Templates/P1-Wardrobe/down-right/v1-independent',R/'Art/Review/P1/modular-down-right-appearance-v1']
def snapshot():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.png','.gif','.ora','.svg','.json','.txt'} and p.name not in {'delivery.json','reexport-validation.json'}}
before=snapshot()
for name in ['author-down-right-appearance-lighting.py','export-down-right-appearance.py','verify-down-right-appearance.py']:subprocess.run([sys.executable,'scripts/'+name],cwd=R,check=True)
after=snapshot();diff=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert not diff,diff
(roots[-1]/'reexport-validation.json').write_text(json.dumps({'status':'byte-identical','files':len(after),'differentFiles':diff,'artApproval':None,'scope':'Original source reflection, semantic/head-local registration, fixed-light RGB,8packages,PNG/ORA/SVG,208 actual compositions and normal GIFs'},indent=2)+'\n');print('Byte-identical:',len(after))
