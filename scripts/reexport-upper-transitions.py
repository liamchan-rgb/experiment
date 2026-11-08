#!/usr/bin/env python3
"""Re-export both upper-diagonal transition templates and check source invariance."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/P1/neutral-upper-transitions-r6';L=R/'Art/Templates/P1-Neutral/up-left/walk-r6-transitions';P=R/'Art/Templates/P1-Neutral/up-right/walk-r6-transitions'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files():return {str(p.relative_to(R)):sha(p) for folder in [L,P] for p in folder.rglob('*') if p.is_file() and p.suffix in ['.json','.png','.ora','.svg']}
def oldfiles():return {str(p.relative_to(R)):sha(p) for folder in [L.parent/'walk-r5-coupled-clothing',P.parent/'walk-r5-mirrored-up-left'] for p in folder.rglob('*') if p.is_file()}
def run(*args):subprocess.run(['python',*map(str,args)],cwd=R,check=True)
def export():
 run(R/'scripts/export-neutral-coupled-clothing.py',L,'--review',D/'up-left')
 run(R/'scripts/capture-neutral-pose-uv.py',L,P/'source/approved-left-uv')
 run(R/'scripts/export-neutral-mirrored-pose-map.py',P,'--review',D/'up-right')
 run(R/'scripts/preview-upper-transitions.py')
old=oldfiles();export();before=files();gifs={str(p.relative_to(R)):sha(p) for p in D.rglob('*.gif')};export();after=files();assert before==after,'Non-deterministic source/template export';assert old==oldfiles(),'Accepted source template modified';assert gifs=={p:sha(R/p) for p in gifs},'Preview bytes changed';run(R/'scripts/verify-upper-transitions.py')
result={'status':'byte-identical-reexport','templateFiles':len(before),'approvedSourceFilesUnchanged':len(old),'gifFiles':len(gifs),'files':before,'approvedSourceFiles':old,'gifHashes':gifs,'artApproval':None};(D/'reexport-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','templateFiles','approvedSourceFilesUnchanged','gifFiles']}))
