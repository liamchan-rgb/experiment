"""Bakes the sprite atlases (8 facings x [8 walk frames + 2 standing frames]) and their metadata for every loadout."""
import json, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from PIL import Image
from render import frame, SIZE, FOOT, PX, PITCH
from rig import LOADOUTS, STRIDE

OUT = Path(__file__).resolve().parents[2] / 'Art/Review/P1/hd2d-proc-v1'
WALK, IDLE = 8, 2
NAMES = ['up', 'up-left', 'left', 'down-left', 'down', 'down-right', 'right', 'up-right']   # facing k: yaw = k * 45 degrees

def job(a):
    name, k, i = a
    img, attach = frame(name, k * np.pi / 4, t=i / WALK) if i < WALK else frame(name, k * np.pi / 4, breath=(i - WALK) / IDLE)
    return name, k, i, img, attach

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(n, k, i) for n in LOADOUTS for k in range(8) for i in range(WALK + IDLE)]
    with Pool(4) as pool: results = pool.map(job, jobs, chunksize=4)
    for name in LOADOUTS:
        atlas = Image.new('RGBA', (SIZE[0] * (WALK + IDLE), SIZE[1] * 8), (0, 0, 0, 0)); meta = {}
        for n, k, i, img, attach in results:
            if n != name: continue
            atlas.alpha_composite(Image.fromarray(img), (i * SIZE[0], k * SIZE[1])); meta[f'{NAMES[k]}/{i}'] = attach
        atlas.save(OUT / f'{name}-atlas.png')
        sheet = Image.new('RGBA', atlas.size, (58, 78, 62, 255)); sheet.alpha_composite(atlas); sheet.convert('RGB').save(OUT / f'{name}-sheet.png')
        json.dump(dict(cell=SIZE, foot=FOOT, pixelsPerUnit=PX, cameraPitchDegrees=round(float(np.degrees(PITCH)), 1), rows=NAMES, walkFrames=WALK, idleFrames=IDLE,
                       strideUnits=STRIDE, walkCycleDistancePixels=round(2 * STRIDE * PX, 2), attach=meta), open(OUT / f'{name}-atlas.json', 'w'), indent=1)
    print('baked', len(results))
