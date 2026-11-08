#!/usr/bin/env python3
"""Require byte-identical independent head sources, packages and review output."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];roots=[R/'Art/Parts/P1-v1/down-left/heads-v1',R/'Art/Templates/P1-Heads/down-left/v1-independent',R/'Art/Review/P1/modular-down-left-heads-v1']
def snapshot():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in {'.png','.gif','.ora','.svg','.json','.txt'} and p.name not in {'delivery.json','reexport-validation.json'}}
before=snapshot()
for name in ['export-down-left-heads.py','verify-down-left-heads.py']:subprocess.run([sys.executable,'scripts/'+name],cwd=R,check=True)
after=snapshot();differences=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert not differences,differences
(roots[-1]/'reexport-validation.json').write_text(json.dumps({'status':'byte-identical','files':len(after),'differentFiles':differences,'artApproval':None,'scope':'Fixed source components/registration,4head-local packages/PNG/ORA/SVG, unchanged-body motion template and52 actual combinations/normal GIFs'},indent=2)+'\n');print('Byte-identical:',len(after))
