#!/usr/bin/env python3
"""Require byte identity when rebuilding right neutral layers, attachments and GIF review evidence."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];roots=['Art/Templates/P1-Neutral/right/walk-r1-mirror','Art/Review/P1/neutral-right-r1-mirror'];D=R/roots[1]
def snapshot():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for root in roots for p in (R/root).rglob('*') if p.is_file() and p.suffix in ['.png','.gif','.ora','.svg','.json','.txt'] and p.name not in ['delivery.json','reexport-validation.json']}
before=snapshot()
for n in ['export-right-neutral-mirror.py','verify-right-neutral-mirror.py']:subprocess.run([sys.executable,str(R/'scripts'/n)],check=True)
after=snapshot();different=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)];assert not different,different
result={'status':'byte-identical','files':len(before),'differentFiles':different,'artApproval':None,'scope':'13 mirrored neutral poses,104 semantic layers,static head,tool-sampled skin ramps,rig/attachments and normal GIFs'};(D/'reexport-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
