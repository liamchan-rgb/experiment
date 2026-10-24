#!/usr/bin/env python3
"""Reproduce source ownership, shared rig/UVs, poses/layers/editables and GIFs byte for byte."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/up/walk-r1-layered';D=R/'Art/Review/P1/neutral-up-layered-r1'
def snapshot():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in [P,D] for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.png','.gif','.ora','.svg','.json','.txt'} and p.name not in {'delivery.json','reexport-validation.json'}}
before=snapshot()
for name in ['author-up-layered-neutral.py','export-up-layered-motion.py','verify-up-layered-motion.py']:subprocess.run([sys.executable,'scripts/'+name],cwd=R,check=True)
after=snapshot();diff=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert not diff,diff
(D/'reexport-validation.json').write_text(json.dumps({'status':'byte-identical','files':len(after),'differentFiles':diff,'artApproval':None,'scope':'Neutral source/foot RGB ownership,13 poses/104 layers/91UV maps,editableORA/SVG,actual compositor outputs and normal GIFs'},indent=2)+'\n');print('Byte-identical:',len(after))
