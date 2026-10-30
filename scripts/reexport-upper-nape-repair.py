#!/usr/bin/env python3
"""Check repeatable leg-art export and unchanged neutral / previous appearance resources."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1];P=R/'Art/Parts/P1-v1/upper/nape-v3';T=R/'Art/Templates/P1-Wardrobe/upper/v3-nape-repair';D=R/'Art/Review/P1/modular-upper-wardrobe-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(roots):return {str(p.relative_to(R)):sha(p) for root in roots for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ['.png','.gif','.ora','.svg','.json'] and p.name not in ['delivery.json','reexport-validation.json']}
def main():
 baseline=json.loads((D/'preserved-files.json').read_text());before=snapshot([P,T,D])
 for script in ['export-upper-nape-repair.py','verify-upper-nape-repair.py']:
  subprocess.run([sys.executable,str(R/'scripts'/script)],check=True,cwd=R)
 after=snapshot([P,T,D]);changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)];assert not changed,changed
 assert all(sha(R/p)==h for p,h in baseline.items()),'Original accepted source or previous appearance resource changed'
 result={'status':'byte-identical-reexport','filesChecked':len(before),'previousNeutralAndWardrobeFilesUnchanged':len(baseline),'files':after,'artApproval':None,'continuousPlayerViewed':False}
 (D/'reexport-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
if __name__=='__main__':main()
