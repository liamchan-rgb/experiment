#!/usr/bin/env python3
"""Check provenance links and file properties for the side-view pose concept."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
manifest_path=ROOT/'asset-manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
errors=[]
def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
image_path=ROOT/manifest['artwork']['path']
with Image.open(image_path) as opened:
    image=opened.convert('RGBA')
    dimensions=list(image.size)
    alpha=image.getchannel('A')
    alpha_extrema=list(alpha.getextrema())
    alpha_bbox=list(alpha.getbbox()) if alpha.getbbox() else None
if digest(image_path)!=manifest['artwork']['sha256']:
    errors.append('candidate image SHA-256 mismatch')
if dimensions!=manifest['canvasPx']:
    errors.append('image dimensions do not match manifest')
if image.mode!='RGBA' or alpha_extrema[0]!=0 or alpha_bbox is None:
    errors.append('candidate must be a visible RGBA image with transparency')
prompt_path=ROOT/manifest['artwork']['generatedFromPrompt']
if digest(prompt_path)!=manifest['artwork']['promptSHA256']:
    errors.append('generation prompt SHA-256 mismatch')
reference_results=[]
for ref in manifest['references']:
    path=REPO/ref['path']
    actual=digest(path) if path.is_file() else None
    ok=actual==ref['sha256']
    reference_results.append({'path':ref['path'],'sha256':actual,'matchesManifest':ok})
    if not ok:
        errors.append(f"reference missing or SHA-256 mismatch: {ref['path']}")
result={
 'status':'passed-technical-source-check-only' if not errors else 'failed',
 'checks':{
   'rgbaPNG':image.mode=='RGBA','dimensionsPx':dimensions,
   'hasTransparency':alpha_extrema[0]==0,'alphaBoundsLTRB':alpha_bbox,
   'promptSHA256Matches':digest(prompt_path)==manifest['artwork']['promptSHA256'],
   'referenceHashesMatch':all(item['matchesManifest'] for item in reference_results),
   'productionScaleValidated':False,'artApproval':False
 },
 'imageSHA256':digest(image_path),
 'references':reference_results,
 'errors':errors,
 'notes':'This checks saved files and provenance links only; camera fit, grip, production registration and visual quality require human review.'
}
(ROOT/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'errors':errors,'dimensionsPx':dimensions},ensure_ascii=False))
if errors: raise SystemExit(1)
