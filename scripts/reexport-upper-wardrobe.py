#!/usr/bin/env python3
"""Prove wardrobe reproducibility and preserve the accepted neutral source."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
D=R/'Art/Review/P1/modular-upper-wardrobe-v1'
roots=[R/'Art/Parts/P1-v1/upper/wardrobe-v1',R/'Art/Templates/P1-Wardrobe/upper/v1-independent',D]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot():
 return {str(p.relative_to(R)):sha(p) for root in roots for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ['.png','.gif','.ora','.svg','.json'] and p.name not in ['reexport-validation.json','delivery.json']}
def main():
 accepted=json.loads((R/'Art/Review/P1/neutral-upper-transitions-r6/reexport-validation.json').read_text())['files']
 before=snapshot()
 for script in ['export-upper-wardrobe.py','verify-upper-wardrobe.py']:
  subprocess.run([sys.executable,str(R/'scripts'/script)],check=True,cwd=R)
 after=snapshot();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
 assert not changed,changed
 assert all(sha(R/p)==h for p,h in accepted.items()),'Accepted neutral source changed'
 result={'status':'byte-identical-reexport','filesChecked':len(before),'acceptedNeutralFilesUnchanged':len(accepted),'files':after,'limits':['Reproducibility is not user art approval or continuous-player review']}
 (D/'reexport-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='files'}))
if __name__=='__main__':main()
