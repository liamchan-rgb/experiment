#!/usr/bin/env python3
"""Require reproducible garment registration and all208 actual compositions."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];roots=[R/'Art/Parts/P1-v1/down-left/wardrobe-v1',R/'Art/Templates/P1-Wardrobe/down-left/v1-independent',R/'Art/Review/P1/modular-down-left-wardrobe-v1']
def snapshot():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.png','.gif','.ora','.svg','.json','.txt'} and p.name not in {'delivery.json','reexport-validation.json'}}
before=snapshot()
for name in ['export-down-left-wardrobe.py','verify-down-left-wardrobe.py']:subprocess.run([sys.executable,'scripts/'+name],cwd=R,check=True)
after=snapshot();diff=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert not diff,diff
(roots[-1]/'reexport-validation.json').write_text(json.dumps({'status':'byte-identical','files':len(after),'differentFiles':diff,'artApproval':None,'scope':'Registered clothing RGB/anatomical matte,4packages/PNG/ORA/SVG/motion,208 actual combinations and normal GIFs'},indent=2)+'\n');print('Byte-identical:',len(after))
