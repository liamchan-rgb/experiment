#!/usr/bin/env python3
"""Require byte-identical outputs from preserved source through actual assembly."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/down-left/walk-r1';D=R/'Art/Review/P1/neutral-down-left-r1'
def snapshot():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in [P,D] for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.png','.gif','.ora','.svg','.json'} and p.name not in {'delivery.json','reexport-validation.json'} and 'rejected-internal-assemblies' not in p.parts}
before=snapshot()
for args in [['scripts/author-down-left-neutral.py'],['scripts/export-down-left-motion.py',str(P.relative_to(R)),'--review',str(D.relative_to(R))],['scripts/verify-down-left-motion.py']]:subprocess.run([sys.executable,*args],cwd=R,check=True)
after=snapshot();different=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert not different,different
(D/'reexport-validation.json').write_text(json.dumps({'status':'byte-identical','files':len(after),'differentFiles':different,'artApproval':None,'scope':'Source registration/ownership, all13 layered poses/ORA/SVG/motion, actual compositor images, normal GIFs and technical checks; artwork review remains separate'},indent=2)+'\n');print('Byte-identical:',len(after))
