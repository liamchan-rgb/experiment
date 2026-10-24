#!/usr/bin/env python3
"""Check source re-export, manifests, actual layered outputs and delivery timings."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
STAGE = ROOT/'Art/Templates/P1-Wardrobe/left/v1-independent'
PARTS = ROOT/'Art/Parts/P1-v1/left'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generated():
    return {str(path.relative_to(ROOT)):digest(path)
            for path in PARTS.rglob('*')
            if path.suffix in {'.png','.ora','.svg'}
            and not {'source','previews','review'}.intersection(path.relative_to(PARTS).parts)}


def run(path,*args):
    completed = subprocess.run([sys.executable,str(path),*args],cwd=ROOT,
                               check=True,capture_output=True,text=True)
    return completed.stdout.strip()


def main():
    catalog = json.loads((STAGE/'catalog.json').read_text())
    before = generated()
    exports = [PARTS/path/'export.py' for path in
               ['heads-v1','forester-v1','wayfarer-v1','back-scabbard-v1']]
    for exporter in exports:
        run(exporter)
    first = generated()
    assert before == first,'Delivered editable/PNG output differs from canonical source re-export'
    for exporter in exports:
        run(exporter)
    assert first == generated(),'Second source re-export differs'
    checks = [{'manifest':asset['manifest'],
               'result':run(ROOT/'scripts/check-character-part.py',asset['manifest'])}
              for asset in catalog['assets']]
    render = run(OUT/'render-audit.py')
    audit = json.loads((OUT/'audit.json').read_text())
    assert not (audit['coverageFailures'] or audit['weaponToggleFailures'] or audit['clothingIslandFailures'])
    timing = {}
    for name,count,durations in [
        ('walk-120ms.gif',8,[120]*8),
        ('outfits-comparison-120ms.gif',8,[120]*8),
        ('start-stop-120ms.gif',22,[480]+[120]*20+[480]),
        ('start-stop-comparison-120ms.gif',22,[480]+[120]*20+[480])]:
        with Image.open(OUT/name) as image:
            assert image.n_frames == count
            actual = []
            for i in range(image.n_frames):
                image.seek(i);actual.append(image.info['duration'])
            assert actual == durations
            assert image.info['loop'] == 0
        timing[name] = {'frames':count,'durationsMs':actual,'sha256':digest(OUT/name)}
    report = {'status':'passed-offline-technical-checks','artApproval':None,
              'assetManifests':checks,'generatedArtFiles':len(first),
              'twoReexportsByteIdentical':True,'generatedArtSHA256':first,
              'renderSummary':json.loads(render),'gifTiming':timing,
              'bodyAndGenericCompositorUnchanged':audit['bodyInvariance'] and audit['genericCompositorUnchanged'],
              'scope':'Only left-facing 13 authored poses. No runtime, simulator, device or IPA verification.'}
    (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'manifests':len(checks),'generatedArtFiles':len(first),
                      'twoReexportsByteIdentical':True,'render':json.loads(render)}))


if __name__ == '__main__':
    main()
