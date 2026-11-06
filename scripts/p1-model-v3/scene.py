"""Render every slot of a posed frame, depth-sort the slots, and attach the existing head and back weapon art."""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import model, body, outfits
from common import comp, layers, selection

HEAD_SLOTS = ['hair.back', 'head.base', 'face.eyes', 'face.brows', 'face.nose', 'face.mouth', 'hair.front']
BASE, LOWER = 'p1-eight-way-base-v1', 'p1-eight-way-lower-v1'


def neck_screen(J, facing):
    fx, fz = body.FACING[facing]
    W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
    n = W @ J['neck']
    return model.CENTER_X + n[0], model.GROUND_Y - n[1] + .5 * n[2]


def head_offset(J, facing):
    """Integer translation that moves the existing idle head/weapon art onto this frame's neck."""
    x, y = neck_screen(J, facing)
    ix, iy = comp.frames[(facing, 'idle', 0)]['joints']['neck']
    return int(round(x - ix)), int(round(y - iy))


def render_assets(J, facing, assets):
    """{asset: {slot: (rgba, depth)}} for the given asset ids."""
    F = outfits.Frame(J, facing)
    built = {a: outfits.ASSETS[a](F) for a in assets}
    out = {}
    for a in assets:
        occ_assets = outfits.OCCLUDED_BY.get(a, outfits.DEFAULT_OCCLUDERS + [a])
        out[a] = {}
        for slot, shapes in built[a].items():
            occ = [s for b in occ_assets if b in built for sl, ss in built[b].items() if not (b == a and sl == slot) for s in ss]
            if shapes:
                rgba, depth, _ = model.render(shapes, occluders=occ)
            else:
                rgba, depth = np.zeros((256, 256, 4), np.uint8), np.full((256, 256), -1e9)
            out[a][slot] = (rgba, depth)
    return out


def draw_order(slot_layers, facing):
    """Topological order of body slots from pairwise depth over their overlaps."""
    idle_order = comp.frames[(facing, 'idle', 0)]['drawOrder']
    names = list(slot_layers)
    rank = {s: (idle_order.index(s) if s in idle_order else 99) for s in names}
    before = {s: set() for s in names}      # s must be drawn after every slot in before[s]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra, da = slot_layers[a]; rb, db = slot_layers[b]
            m = (ra[..., 3] > 0) & (rb[..., 3] > 0)
            if m.sum() < 3:
                continue
            diff = float(np.mean(da[m] - db[m]))
            if abs(diff) < .2:
                continue
            (before[a] if diff > 0 else before[b]).add(b if diff > 0 else a)
    order, done = [], set()
    while len(order) < len(names):
        ready = [s for s in names if s not in done and before[s] <= done]
        if not ready:   # break a cycle at the slot whose idle order is earliest
            ready = [min((s for s in names if s not in done), key=lambda s: rank[s])]
        s = min(ready, key=lambda s: rank[s])
        order.append(s); done.add(s)
    return order


def full_order(body_order, facing):
    idle_order = comp.frames[(facing, 'idle', 0)]['drawOrder']
    behind_weapon = idle_order.index('weapon.back') == 0 if 'weapon.back' in idle_order else True
    order = ['hair.back', 'outfit.hem.back'] + (['weapon.back'] if behind_weapon else [])
    order += body_order
    if not behind_weapon:
        order.append('weapon.back')
    order += [s for s in HEAD_SLOTS if s != 'hair.back']
    return order


def compose(J, facing, outfit='forester', weapon='trainingSword', armor=None, rendered=None):
    """Full character for preview, using the same layering the baked parts will use."""
    import importlib.util
    split = sys.modules.get('common').split
    body_assets = [BASE, LOWER] + ([split.ARMORS[armor]] if armor else [split.OUTFITS[outfit]])
    rendered = rendered or render_assets(J, facing, body_assets)
    slot_layers = {}
    for a in body_assets:
        for slot, v in rendered[a].items():
            if v[0][..., 3].any():
                slot_layers[slot] = v
    order = full_order(draw_order(slot_layers, facing), facing)
    dx, dy = head_offset(J, facing)
    idle = dict(layers(facing, 'idle', 0, selection(outfit, weapon, armor)))
    canvas = Image.new('RGBA', (256, 256))
    for slot in order:
        if slot in slot_layers:
            canvas.alpha_composite(Image.fromarray(slot_layers[slot][0]))
        elif slot in idle and (slot in HEAD_SLOTS or slot == 'weapon.back'):
            canvas.alpha_composite(Image.fromarray(np.roll(np.array(idle[slot]), (dy, dx), (0, 1))))
    return canvas, order
