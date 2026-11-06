#!/usr/bin/env python3
"""Rebuild the eight P1 walk poses of the four diagonal directions from each
direction's idle pose with a simple limb rig.

The authored diagonal walks barely moved the legs. Every walk pose is now the
idle pose-map layer of each asset, deformed per slot group:
- legs (body leg, pants, boot): hip follows the body bob, the foot follows a
  planted/swing trajectory along the facing, with a knee bend while swinging;
- arms (arm, sleeve, hand): swing opposite to the legs about the shoulder;
- everything else (torso, outfit, head, weapon): rigid vertical bob.
Head-local art (face, hair) follows the bob through motion.json headToCanvas.

Deterministic and idempotent: only idle layers are read, so re-running gives
the same pixels. Updates the walk PNGs of every asset used by a shipped P1
atlas, motion.json (headToCanvas, joints, sole markers, draw order) and the
P1 sole data in hero-gait.json. Then run rebake-p1-map-atlases.py and
build-p1-head-split.py. Editable .ora/.svg sources are not regenerated.

Usage: python3 -I scripts/build-p1-diagonal-rig-walk.py
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('p1_head_split', ROOT / 'scripts/build-p1-head-split.py')
split = importlib.util.module_from_spec(spec)
spec.loader.exec_module(split)

DIAGONALS = ['down-left', 'down-right', 'up-left', 'up-right']
# Screen direction of one step along each facing (ground diagonal, y halved by the camera).
FORWARD = {'down-left': (-1, .5), 'down-right': (1, .5), 'up-left': (-1, -.5), 'up-right': (1, -.5)}
GROUPS = {
    'R': (['body.leg.right', 'outfit.pants.right', 'outfit.boot.right'], 'hipRight', 'kneeRight', 'ankleRight'),
    'L': (['body.leg.left', 'outfit.pants.left', 'outfit.boot.left'], 'hipLeft', 'kneeLeft', 'ankleLeft'),
}
ARMS = {
    'R': (['body.arm.right', 'outfit.sleeve.right', 'body.hand.right'], 'shoulderRight', 'elbowRight', 'wristRight'),
    'L': (['body.arm.left', 'outfit.sleeve.left', 'body.hand.left'], 'shoulderLeft', 'elbowLeft', 'wristLeft'),
}
# Pose p = walk frame p+1. Phase origin as authored: right contact at 0, right support 0..3, left 4..7.
STRIDE = 11          # px of screen x from mid-stance to contact
LIFT = [0, 0, 0, 0, 0, 3, 5, 2]   # swing-foot lift by pose since its toe-off (pose 4 for the right foot)
KNEE = 3             # forward knee bend at mid-swing
BOB = [1, 0, -1, 0]  # body down at contact, up at passing
ARM = 4              # hand swing, px of screen x


def foot(q):
    """(stride factor -1..1, lift, knee) of the right foot at pose q."""
    q %= 8
    if q <= 4:
        return 1 - q / 2, 0, 0
    return -1 + (q - 4) / 2, LIFT[q], KNEE * math.sin(math.pi * (q - 4) / 4)


def limb_field(top, bottom, d_top, d_bottom, bump=(0, 0)):
    span = max(1e-6, bottom - top)

    def field(y):
        t = min(1, max(0, (y - top) / span))
        return (d_top[0] + t * (d_bottom[0] - d_top[0]) + bump[0] * math.sin(math.pi * t),
                d_top[1] + t * (d_bottom[1] - d_top[1]) + bump[1] * math.sin(math.pi * t))
    return field


def warp(image, field):
    """Each source row moves by field(y); rows are resampled by nearest inverse lookup."""
    src = np.array(image)
    h, w = src.shape[:2]
    out = np.zeros_like(src)
    for y in range(h):
        lo, hi = -64.0, h + 64.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if mid + field(mid)[1] < y:
                lo = mid
            else:
                hi = mid
        s = (lo + hi) / 2
        sy = math.floor(s + .5)
        if not 0 <= sy < h:
            continue
        shift = math.floor(field(s)[0] + .5)
        row = src[sy]
        if shift > 0:
            out[y, shift:] = row[:w - shift]
        elif shift < 0:
            out[y, :shift] = row[-shift:]
        else:
            out[y] = row
    return Image.fromarray(out)


def pose_fields(direction, joints, p):
    fx, fy = FORWARD[direction]
    bob = (0, BOB[p % 4])
    fields = {}
    for side, (slots, hip, _, ankle) in GROUPS.items():
        s, lift, knee = foot(p if side == 'R' else p + 4)
        d_foot = (fx * STRIDE * s, fy * STRIDE * s - lift)
        f = limb_field(joints[hip][1], joints[ankle][1], bob, d_foot, (fx * knee, fy * knee))
        for slot in slots:
            fields[slot] = f
    for side, (slots, shoulder, _, wrist) in ARMS.items():
        # The arm opposite the forward foot swings forward.
        swing = math.cos(2 * math.pi * p / 8) * ARM * (1 if side == 'L' else -1)
        d_hand = (fx * swing, bob[1] + fy * swing * .5 - abs(swing) * .25)
        f = limb_field(joints[shoulder][1], joints[wrist][1], bob, d_hand)
        for slot in slots:
            fields[slot] = f
    rigid = limb_field(-1e6, -1e6 + 1, bob, bob)
    return fields, rigid, bob


def main():
    compositor = split.load_compositor()
    motion_path = split.MOTION
    motion = json.loads(motion_path.read_text())
    frames = {(f['direction'], f['clip'], f['frame']): f for f in motion['frames']}
    gait_path = ROOT / 'Sources/Resources/hero-gait.json'
    gait = json.loads(gait_path.read_text())
    used = {json.loads(split.SELECTION.read_text())['base']}
    for _, body, *_ in split.states(gait):
        used.update(body)
    # Never overwrite a file another (unused) asset also references.
    owners = {}
    for identifier in compositor.entries:
        data, path, _ = compositor.asset(identifier)
        for binding in data['bindings']:
            for relative in binding['layers'].values():
                owners.setdefault((path.parent / relative).resolve(), set()).add(identifier)
    written = 0
    for identifier in sorted(used):
        data, path, bindings = compositor.asset(identifier)
        if data['mode'] != 'pose-map':
            continue
        for direction in DIAGONALS:
            idle = bindings[(direction, 'idle', 0)]['layers']
            joints = frames[(direction, 'idle', 0)]['joints']
            for p in range(8):
                fields, rigid, _ = pose_fields(direction, joints, p)
                for slot, relative in bindings[(direction, 'walk', p + 1)]['layers'].items():
                    target = (path.parent / relative).resolve()
                    assert owners[target] == {identifier}, f'{target} shared by {owners[target]}'
                    with Image.open(path.parent / idle[slot]) as source:
                        image = warp(source.convert('RGBA'), fields.get(slot, rigid))
                    image.save(target, optimize=True)
                    written += 1
    # Motion data: head, joints, soles and draw order follow the same rig.
    for direction in DIAGONALS:
        idle = frames[(direction, 'idle', 0)]
        for p in range(8):
            fields, rigid, bob = pose_fields(direction, idle['joints'], p)
            frame = frames[(direction, 'walk', p + 1)]
            matrix = list(idle['headToCanvas'])
            matrix[5] += bob[1]
            frame['headToCanvas'] = matrix
            frame['drawOrder'] = list(idle['drawOrder'])
            joints = {}
            for name, (x, y) in idle['joints'].items():
                if 'Left' in name or 'Right' in name:
                    side = 'L' if 'Left' in name else 'R'
                    slot = (GROUPS if name.startswith(('hip', 'knee', 'ankle')) else ARMS)[side][0][0]
                    dx, dy = fields[slot](y)
                else:
                    dx, dy = bob
                joints[name] = [round(x + dx, 3), round(y + dy, 3)]
            frame['joints'] = joints
            soles = {}
            for side, (x, y) in idle['soleMarkers'].items():
                dx, dy = fields[GROUPS['L' if side == 'left' else 'R'][0][0]](y)
                soles[side] = [int(math.floor(x + dx + .5)), int(math.floor(y + dy + .5))]
            frame['soleMarkers'] = soles
            frame['support'] = 'right' if p < 4 else 'left'
    motion_path.write_text(json.dumps(motion, indent=2, ensure_ascii=False) + '\n')
    # P1 shadow/foot data: same tick -> column sampling as the original import.
    order = ['down', 'left', 'up', 'right', 'down-right', 'down-left', 'up-left', 'up-right']
    keys = split.KEYS
    for row, direction in enumerate(order):
        if direction not in DIAGONALS:
            continue
        for tick in range(29):
            column = 0 if tick == 0 else 1 + (tick - 1) * 8 // 24 if tick <= 24 else 9 + tick - 25
            clip, n = keys[column]
            f = frames[(direction, clip, n)]
            gait['heroes'][0][row][tick] = {'feet': [[f['soleMarkers'][s][0] / 256, f['soleMarkers'][s][1] / 256, 0]
                                                     for s in ['left', 'right']]}
    gait_path.write_text(json.dumps(gait, separators=(',', ':'), ensure_ascii=False) + '\n')
    print('rig walk layers written:', written)


if __name__ == '__main__':
    main()
