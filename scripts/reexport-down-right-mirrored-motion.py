#!/usr/bin/env python3
"""Reproduce source-UV reflection, lighting, head registration and all outputs."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];P=R/'Art/Templates/P1-Neutral/down-right/walk-r1-mirrored-down-left';D=R/'Art/Review/P1/neutral-down-right-r1-mirror';L=R/'Art/Templates/P1-Neutral/down-left/walk-r1'
def snapshot():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in [P,D] for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.png','.gif','.ora','.svg','.json'} and p.name not in {'delivery.json','reexport-validation.json'}}
before=snapshot()
commands=[['scripts/capture-down-diagonal-pose-uv.py',str(L.relative_to(R)),str((P/'source/approved-left-uv').relative_to(R))],['scripts/author-down-right-mirror-lighting.py',str(P.relative_to(R))],['scripts/register-down-right-head.py'],['scripts/export-down-right-mirrored-motion.py',str(P.relative_to(R)),'--review',str(D.relative_to(R))],['scripts/verify-down-right-mirrored-motion.py']]
for args in commands:subprocess.run([sys.executable,*args],cwd=R,check=True)
after=snapshot();differences=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert not differences,differences
(D/'reexport-validation.json').write_text(json.dumps({'status':'byte-identical','files':len(after),'differentFiles':differences,'artApproval':None,'scope':'Approved-source UV capture without modifying source, fixed colour bake, head UV raster registration, all13 mirrored layered poses/ORA/SVG/motion, actual compositor and normal GIFs'},indent=2)+'\n');print('Byte-identical:',len(after))
