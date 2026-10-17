#!/usr/bin/env python3
"""Bake whole-frame, independently articulated two-leg walks.

The legacy image-half displacement cannot represent knees or planted feet.
This offline rig uses individually masked thigh, calf and rigid shoe artwork,
solves a two-bone chain in ground coordinates, and packs 24 complete poses.
No limb deformation or texture upload occurs in the running game.
"""
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy.ndimage import label, binary_dilation

FRAME_COUNT = 24
CELL = 256
# leg center, toe extent; traced against each direction's original idle art.
LEGS = [
    [[(113, 94, 124), (137, 126, 155)], [(130, 113, 146)] * 2,
     [(114, 96, 125), (140, 128, 160)], [(130, 113, 146)] * 2,
     [(125, 104, 137), (152, 139, 172)], [(104, 80, 116), (128, 116, 148)],
     [(106, 82, 119), (132, 120, 151)], [(125, 104, 139), (152, 140, 172)]],
    [[(114, 97, 128), (142, 131, 160)], [(132, 113, 148)] * 2,
     [(113, 94, 126), (141, 128, 161)], [(132, 113, 148)] * 2,
     [(119, 102, 133), (148, 135, 168)], [(109, 87, 119), (129, 119, 145)],
     [(117, 93, 128), (139, 127, 153)], [(124, 108, 136), (149, 134, 170)]],
    [[(110, 96, 121), (135, 125, 151)], [(124, 108, 140)] * 2,
     [(112, 95, 124), (140, 128, 158)], [(124, 108, 140)] * 2,
     [(125, 110, 141), (155, 142, 177)], [(96, 75, 110), (130, 115, 145)],
     [(104, 85, 118), (138, 123, 153)], [(125, 111, 140), (154, 140, 176)]]
]
HEADINGS = [(0, 1), (-1, 0), (0, -1), (1, 0), (2**-.5, 2**-.5),
            (-2**-.5, 2**-.5), (-2**-.5, -2**-.5), (2**-.5, -2**-.5)]

def figure(cell):
    alpha = np.asarray(cell.getchannel('A')) > 80
    rows = np.flatnonzero(alpha.any(axis=1))
    bands = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
    band = max(bands, key=len)
    cell = cell.crop((0, int(band[0]), cell.width, int(band[-1]) + 1))
    return cell.crop(cell.getchannel('A').point(lambda a: 255 if a > 80 else 0).getbbox())

def legacy_rows(root, hero):
    raw = root / 'Art/Generated/LivingScene'
    result = []
    for name in [f'hero{hero}-gait-v1.2.png', f'hero{hero}-diagonal-v1.3.png']:
        source = Image.open(raw / name).convert('RGBA')
        cells = [figure(source.crop((c * source.width // 4, r * source.height // 4,
                                    (c + 1) * source.width // 4, (r + 1) * source.height // 4)))
                 for r in range(4) for c in range(4)]
        scale = 160 / max(c.height for c in cells)
        for row in range(4):
            # Original complete idle provides a stable head, coat and equipment.
            src = cells[row * 4]
            src = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.NEAREST)
            idle = Image.new('RGBA', (CELL, CELL))
            idle.alpha_composite(src, ((CELL - src.width) // 2, 224 - src.height))
            result.append(idle)
    return result

def bone(part, src_a, src_b, dst_a, dst_b):
    """Foreshorten only along the bone; keep its width and its own alpha mask."""
    v, w = src_b - src_a, dst_b - dst_a
    source_length, target_length = np.linalg.norm(v), np.linalg.norm(w)
    if target_length < .3:
        return Image.new('RGBA', (CELL, CELL))
    e, q = v / source_length, w / target_length
    n, m = np.array([-e[1], e[0]]), np.array([-q[1], q[0]])
    matrix = np.outer(q, e) * target_length / source_length + np.outer(m, n)
    offset = dst_a - matrix @ src_a
    inverse = np.linalg.inv(matrix)
    shift = -inverse @ offset
    return part.transform((CELL, CELL), Image.Transform.AFFINE,
                          (*inverse[0], shift[0], *inverse[1], shift[1]), Image.Resampling.BICUBIC)

def clean_gutter(image):
    """Remove tiny matte remnants, never an actual detached hand or boot."""
    rgba = np.array(image)
    components, count = label(rgba[:, :, 3] > 32, np.ones((3, 3)))
    if count <= 1: return image
    sizes = np.bincount(components.ravel()); sizes[0] = 0
    largest = int(sizes.argmax())
    other = np.delete(sizes[1:], largest - 1)
    if other.max(initial=0) > 64:
        raise ValueError('A real limb became disconnected; fix its matte or rig')
    keep = binary_dilation(components == largest, structure=np.ones((3, 3)))
    rgba[:, :, 3] *= keep
    return Image.fromarray(rgba)

def planted_shoe(shoe, ankle, destination, phase, forward_x):
    """Heel strike, flat weight bearing, toe release, then swing recovery.

    Roll about the contact point so a planted heel/toe does not skate. This is
    a rigid shoe transform, independent of the knee's projected bone length.
    """
    heel = ankle + np.array([-forward_x * 8, 7])
    toe = ankle + np.array([forward_x * 13, 7])
    if phase < .08:
        pitch, pivot = .10 * (1 - phase / .08), heel
    elif phase < .38:
        pitch, pivot = 0, ankle
    elif phase < .5:
        pitch, pivot = -.14 * (phase - .38) / .12, toe
    else:
        swing = (phase - .5) * 2
        eased = swing * swing * (3 - 2 * swing)
        pitch = -.14 + .24 * eased
        if swing < .2:
            blend = swing / .2
            pivot = toe * (1 - blend) + ankle * blend
        elif swing > .8:
            blend = (swing - .8) / .2
            pivot = ankle * (1 - blend) + heel * blend
        else:
            pivot = ankle
    angle = -pitch * forward_x
    direction = np.array([-math.sin(angle), math.cos(angle)])
    return bone(shoe, pivot, pivot + [0, 1], pivot + destination - ankle,
                pivot + destination - ankle + direction)

def prepare_gait_assets(root, save_asset, manifest):
    metadata = {'format': 1, 'frames': FRAME_COUNT, 'columns': FRAME_COUNT + 1, 'cell': CELL, 'heroes': []}
    for hero in range(3):
        idles = legacy_rows(root, hero + 1)
        poses, hero_metadata = [], []
        for facing, idle in enumerate(idles):
            if facing == 3:
                # Preserve the approved complete left profile, including costume.
                left = poses[1]
                poses.append([p.transpose(Image.Transpose.FLIP_LEFT_RIGHT) for p in left])
                reflected = json.loads(json.dumps(hero_metadata[1]))
                for entry in reflected:
                    for foot in entry['feet']: foot[0] = 1 - foot[0]
                hero_metadata.append(reflected)
                continue
            specs = LEGS[hero][facing]
            cut = (194 if facing in [0, 4, 5, 6, 7] else 193) if hero == 2 else (181 if facing in [0, 2] else 182)
            knee_y = 204 if hero == 2 else 199
            body = idle.copy()
            body_draw = ImageDraw.Draw(body)
            pieces = []
            for leg, (cx, toe_left, toe_right) in enumerate(specs):
                remove_y = max(185, cut)
                # Remove each old leg below its own garment opening. Skirt,
                # sword, coat tails and bags outside the leg matte stay intact.
                if facing == 1:
                    body_draw.rectangle((min(s[1] for s in specs) - 18, remove_y, max(s[2] for s in specs), 226), fill=0)
                else:
                    polygon = [(cx - 10, remove_y), (cx + 10, remove_y),
                               (toe_right, 200), (toe_right, 226), (toe_left, 226),
                               (toe_left, 200)]
                    body_draw.polygon(polygon, fill=0)
                mask = Image.new('L', (CELL, CELL)); md = ImageDraw.Draw(mask)
                md.polygon([(cx - 10, cut), (cx + 10, cut),
                            (toe_right, 200), (toe_right, 226), (toe_left, 226),
                            (toe_left, 200)], fill=255)
                part = Image.new('RGBA', (CELL, CELL)); part.paste(idle, (0, 0), mask)
                upper, calf, shoe = part.copy(), part.copy(), part.copy()
                ImageDraw.Draw(upper).rectangle((0, knee_y + 5, CELL, CELL), fill=0)
                cd = ImageDraw.Draw(calf); cd.rectangle((0, 0, CELL, knee_y - 6), fill=0); cd.rectangle((0, 217, CELL, CELL), fill=0)
                ImageDraw.Draw(shoe).rectangle((0, 0, CELL, 209), fill=0)
                # A second profile leg is behind the first, not another copy of
                # a whole sprite. Its reduced light also preserves the overlap.
                if facing == 1 and leg == 0:
                    upper = ImageEnhance.Brightness(upper).enhance(.80)
                    calf = ImageEnhance.Brightness(calf).enhance(.80)
                    shoe = ImageEnhance.Brightness(shoe).enhance(.80)
                pieces.append((upper, calf, shoe, np.array([cx, cut], float),
                               np.array([cx, knee_y], float), np.array([cx, 217], float)))
            body = clean_gutter(body)
            dx, dy = HEADINGS[facing]
            forward = np.array([dx, dy * 2, 0.]); forward /= np.linalg.norm(forward)
            right = np.array([forward[1], -forward[0], 0.])
            project = lambda p: np.array([p[0], .5 * p[1] - .8660254 * p[2]])
            side_order = [-1, 1] if facing in [0, 1, 4, 5] else [1, -1]
            frames = [idle if facing != 1 else idles[1]]
            info = [{'feet': [[(s[0]) / CELL, 224 / CELL, 0] for s in specs]}]
            for frame in range(FRAME_COUNT):
                phase = frame / FRAME_COUNT
                bob = -1.0 * math.cos(4 * math.pi * phase)
                image = Image.new('RGBA', (CELL, CELL))
                legs, feet = [], []
                for leg, (upper, calf, shoe, hip, knee, ankle) in enumerate(pieces):
                    t = (phase + leg * .5) % 1
                    # Stance covers exactly half a cycle: constant backward
                    # foot motion cancels forward actor motion without skating.
                    if t < .5:
                        f, lift = 24 - 96 * t, 0
                    else:
                        s = (t - .5) * 2
                        f = -24 + 48 * (s * s * (3 - 2 * s))
                        lift = 10 * math.sin(math.pi * s) ** 1.3
                    hip3 = np.array([0., 0., 38 + bob])
                    ankle3 = forward * f + np.array([0., 0., lift])
                    v = ankle3 - hip3; length = np.linalg.norm(v); e = v / length
                    bend = forward - e * np.dot(forward, e); bend /= np.linalg.norm(bend)
                    knee3 = (hip3 + ankle3) / 2 + bend * math.sqrt(max(0, 23**2 - (length / 2)**2))
                    # Rest offsets belong to individual garment openings. An
                    # anatomical leg remains the same leg throughout the cycle.
                    anchor = np.array([hip[0], 217.])
                    if facing == 1: anchor[0] += (-3 if leg == 0 else 3)
                    dh, dk, da = [anchor + project(p) for p in [hip3, knee3, ankle3]]
                    limb = Image.new('RGBA', (CELL, CELL))
                    limb.alpha_composite(bone(upper, hip, knee, dh, dk))
                    limb.alpha_composite(bone(calf, knee, ankle, dk, da))
                    # Shoes retain their shape and flat sole; they do not inherit
                    # calf foreshortening or stretch into a point at passing.
                    limb.alpha_composite(planted_shoe(shoe, ankle, da, t, forward[0]))
                    depth = right[1] * side_order[leg]
                    legs.append((depth, limb))
                    feet.append([float(da[0] / CELL), float((224 + project(forward * f)[1]) / CELL), float(lift / CELL)])
                for _, limb in sorted(legs, key=lambda item: item[0]): image.alpha_composite(limb)
                image.alpha_composite(body, (0, round(-bob)))
                frames.append(clean_gutter(image)); info.append({'feet': feet})
            poses.append(frames); hero_metadata.append(info)
        metadata['heroes'].append(hero_metadata)
        for group, suffix in enumerate(['Directions', 'Diagonals']):
            atlas = Image.new('RGBA', ((FRAME_COUNT + 1) * CELL, 4 * CELL))
            for row in range(4):
                for column, frame in enumerate(poses[group * 4 + row]):
                    atlas.alpha_composite(frame, (column * CELL, row * CELL))
            name = f'Hero{hero + 1}{suffix}'
            save_asset(name, atlas)
            manifest[name].update({'frames': FRAME_COUNT, 'columns': FRAME_COUNT + 1,
                'source': 'original direction artwork + independently articulated offline leg rig',
                'runtimeRig': '24 whole-frame poses; rigid shoes, two-bone knees, distance-locked stance; no runtime limb warp'})
    (root / 'Sources/Resources/hero-gait.json').write_text(json.dumps(metadata, separators=(',', ':')) + '\n')
    return metadata
