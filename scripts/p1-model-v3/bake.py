#!/usr/bin/env python3
"""Bake P1 model v3 into the existing part pipeline (all 8 facings, all 13 cells).

For every facing and cell (idle, start x2, jog x8, stop x2) the skeleton is
posed, each asset's slots are rendered on their own (with depth-sorted draw
order recorded in motion.json), and written over that asset's pose-map PNG.
The existing head (head.base + head-local face/hair) and back weapons are kept
pixel-exact and moved with the neck. Then run:
  python3 -I scripts/rebake-p1-map-atlases.py
  python3 -I scripts/build-p1-head-split.py

Idempotent: the original idle head/weapon art and idle motion data are
snapshotted once into Art/Integration/P1-model-v3/reference/ and always read from there.
"""
import json
import math
import shutil
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import model, body, outfits, scene, clips
from common import ROOT, comp, split

REF = ROOT / 'Art/Integration/P1-model-v3/reference'
FACINGS = ['down', 'down-left', 'left', 'up-left', 'up', 'up-right', 'right', 'down-right']
WEAPONS = ['p1-eight-way-weapon-v1', 'p1-hunting-bow-v1', 'p1-b2-greatsword-v1', 'p1-b2-legendarystaff-v1']
MODEL_ASSETS = list(outfits.ASSETS)
CELLS = [('idle', 0)] + [('walk-start', 1), ('walk-start', 2)] + [('walk', n) for n in range(1, 9)] + [('walk-stop', 1), ('walk-stop', 2)]


def snapshot():
    """Original idle head and weapon art + idle motion, captured once."""
    meta = REF / 'idle-motion.json'
    if meta.exists():
        return json.loads(meta.read_text())
    REF.mkdir(parents=True, exist_ok=True)
    frames = {}
    for facing in FACINGS:
        f = comp.frames[(facing, 'idle', 0)]
        frames[facing] = {'joints': f['joints'], 'headToCanvas': f['headToCanvas'], 'drawOrder': f['drawOrder']}
        data, path, bindings = comp.asset(scene.BASE)
        shutil.copy(path.parent / bindings[(facing, 'idle', 0)]['layers']['head.base'], REF / f'{facing}-head.base.png')
        for w in WEAPONS:
            data, path, bindings = comp.asset(w)
            shutil.copy(path.parent / bindings[(facing, 'idle', 0)]['layers']['weapon.back'], REF / f'{facing}-{w}.png')
    meta.write_text(json.dumps(frames, indent=1) + '\n')
    return frames


def shifted(path, dx, dy):
    a = np.array(Image.open(path).convert('RGBA'))
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    ys, xs = slice(max(0, dy), min(h, h + dy)), slice(max(0, dx), min(w, w + dx))
    yr, xr = slice(max(0, -dy), min(h, h - dy)), slice(max(0, -dx), min(w, w - dx))
    out[ys, xs] = a[yr, xr]
    return Image.fromarray(out)


def project(facing, v):
    fx, fz = body.FACING[facing]
    W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
    p = W @ v
    return [round(model.CENTER_X + p[0], 2), round(model.GROUND_Y - p[1] + .5 * p[2], 2)]


def sole(J, side, facing):
    Fm = body.rot_x(J['foot' + side])
    return J['ankle' + side] + Fm @ np.array([0, -9.0, 2.5])


def main():
    ref = snapshot()
    motion = json.loads(split.MOTION.read_text())
    mframes = {(f['direction'], f['clip'], f['frame']): f for f in motion['frames']}
    written = 0
    for facing in FACINGS:
        idle_neck = ref[facing]['joints']['neck']
        for clip, n in CELLS:
            J = body.skeleton(clips.pose(clip, n))
            rendered = scene.render_assets(J, facing, MODEL_ASSETS)
            nx, ny = scene.neck_screen(J, facing)
            dx, dy = int(round(nx - idle_neck[0])), int(round(ny - idle_neck[1]))
            # draw order from a state that owns every slot (coat skirt included)
            layers_for_order = {}
            for a in [scene.BASE, scene.LOWER, 'p1-eight-way-wayfarer-v1']:
                for slot, v in rendered[a].items():
                    if v[0][..., 3].any():
                        layers_for_order[slot] = v
            order = scene.full_order(scene.draw_order(layers_for_order, facing), facing)
            every = set(ref[facing]['drawOrder'])
            for a in MODEL_ASSETS + WEAPONS:
                every.update(comp.asset(a)[0]['slots'])
            order += [s for s in ref[facing]['drawOrder'] if s not in order]
            order += sorted(s for s in every if s not in order)
            # pose-map PNGs
            for a in MODEL_ASSETS:
                data, path, bindings = comp.asset(a)
                for slot, rel in bindings[(facing, clip, n)]['layers'].items():
                    if slot == 'head.base':
                        image = shifted(REF / f'{facing}-head.base.png', dx, dy)
                    elif slot in rendered[a]:
                        image = Image.fromarray(rendered[a][slot][0])
                    else:
                        image = Image.new('RGBA', (256, 256))
                    image.save(path.parent / rel, optimize=True); written += 1
            for w in WEAPONS:
                data, path, bindings = comp.asset(w)
                rel = bindings[(facing, clip, n)]['layers']['weapon.back']
                shifted(REF / f'{facing}-{w}.png', dx, dy).save(path.parent / rel, optimize=True); written += 1
            # motion data
            f = mframes[(facing, clip, n)]
            m = list(ref[facing]['headToCanvas']); m[4] += dx; m[5] += dy
            f['headToCanvas'] = m
            f['drawOrder'] = order
            names = {'hip': 'hip', 'knee': 'knee', 'ankle': 'ankle', 'shoulder': 'shoulder', 'elbow': 'elbow', 'wrist': 'wrist'}
            joints = {k + ('Right' if s == 'R' else 'Left'): project(facing, J[k + s]) for k in names for s in 'RL'}
            joints['neck'] = [round(nx, 2), round(ny, 2)]
            f['joints'] = joints
            f['soleMarkers'] = {('right' if s == 'R' else 'left'): [int(round(v)) for v in project(facing, sole(J, s, facing))] for s in 'RL'}
            if clip == 'walk':
                f['support'] = 'right' if n <= 4 else 'left'
        print(facing, 'done', flush=True)
    split.MOTION.write_text(json.dumps(motion, indent=2, ensure_ascii=False) + '\n')
    # hero-gait: soles for shadows, entry phases, uniform timing
    gait_path = ROOT / 'Sources/Resources/hero-gait.json'
    gait = json.loads(gait_path.read_text())
    order = ['down', 'left', 'up', 'right', 'down-right', 'down-left', 'up-left', 'up-right']
    for row, facing in enumerate(order):
        for tick in range(29):
            column = 0 if tick == 0 else 1 + (tick - 1) * 8 // 24 if tick <= 24 else 9 + tick - 25
            clip, n = split.KEYS[column]
            sm = mframes[(facing, clip, n)]['soleMarkers']
            gait['heroes'][0][row][tick] = {'feet': [[sm[s][0] / 256, sm[s][1] / 256, 0] for s in ['left', 'right']]}
    gait['modularP1']['directions'] = [{'entryPhase': clips.ENTRY_PHASE, 'exitPhase': clips.EXIT_PHASE} for _ in order]
    gait['modularP1']['timing'] = 'uniform'
    gait_path.write_text(json.dumps(gait, separators=(',', ':'), ensure_ascii=False) + '\n')
    print('pose-map layers written:', written)


if __name__ == '__main__':
    main()
