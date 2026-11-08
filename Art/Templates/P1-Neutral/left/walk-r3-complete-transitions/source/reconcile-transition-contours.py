#!/usr/bin/env python3
"""Offline authoring aid: assign source contours to their anatomical part.

The exporter reads the resulting fixed pixel table. It never runs this aid,
changes source colours, or performs runtime segmentation.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_propagation, distance_transform_edt, label

folder = Path(__file__).resolve().parents[1]
config = json.loads((folder/'authoring.json').read_text())
original = json.loads((folder/'source/transition-ownership-before-contour-review.json').read_text())
slots = config['drawOrder']
yy, xx = np.indices((256, 256))
wrists = {'left': [[134,166],[142,164],[133,165],[129,166]],
          'right': [[115,162],[108,160],[111,160],[139,162]]}
hands = {'left': [[135,171],[145,169],[134,170],[129,171]],
         'right': [[114,165],[103,164],[108,165],[140,166]]}
arm_regions = [
    [(123,134),(134,134),(138,143),(141,151),(141,162),(137,168),(129,168),(127,153),(123,144)],
    [(123,134),(132,134),(138,140),(142,146),(145,153),(148,160),(145,165),(139,166),(134,155),(125,145)],
    [(123,134),(132,134),(136,140),(140,150),(139,160),(137,166),(130,166),(129,153),(124,146)],
    [(124,134),(134,134),(137,144),(137,153),(134,161),(132,166),(123,167),(125,156),(125,147),(121,141)],
]
hand_regions = [
    [(130,166),(141,166),(142,171),(139,175),(132,175),(129,171)],
    [(140,162),(148,162),(150,167),(148,171),(143,172),(139,169)],
    [(131,164),(140,164),(141,170),(136,174),(129,172),(128,168)],
    [(123,164),(136,164),(136,174),(132,176),(123,174),(121,169)],
]
reports = []
for offset, pose in enumerate(config['poses'][9:]):
    index = offset+9
    image = np.array(Image.open(folder/f'registered/{index:02}.png').convert('RGBA'))
    r, g, b, alpha = [image[:, :, k].astype(int) for k in range(4)]
    visible = (alpha > 0) & (yy >= 129)
    old = np.full((256, 256), slots.index('body.torso'), int)
    for entry in original['poses'][offset]['ownershipOverrides']:
        for x, y in entry['pixels']:
            old[y, x] = slots.index(entry['slot'])
    torso_region = (yy >= 132) & (yy <= 181) & (xx >= 105) & (xx <= 143)
    white = torso_region & (r > 140) & (g > 130) & (b > 95) & (r-g < 28) & (g-b < 36) & (alpha >= 128)
    loose = torso_region & (r > 120) & (g > 110) & (b > 90) & (r-g < 26) & (g-b < 36) & (alpha >= 128)
    white = binary_propagation(white, mask=loose)
    gray = torso_region & (yy >= 159) & (np.maximum.reduce([r,g,b])-np.minimum.reduce([r,g,b]) < 18)
    gray &= (np.maximum.reduce([r,g,b]) < 150) & (np.maximum.reduce([r,g,b]) > 30) & (alpha >= 128)
    clothing = white | gray | ((yy >= 129) & (yy <= 134) & visible)
    skin = (r-g > 12) & (g-b > 18) & (r > 110) & (g > 65) & (alpha >= 128) & visible & ~clothing
    groups = [['body.arm.left','body.hand.left'], ['body.arm.right','body.hand.right'],
              ['body.leg.left'], ['body.leg.right']]
    seeds = [clothing]
    for group in groups:
        sample = skin & np.isin(old, [slots.index(slot) for slot in group])
        components, count = label(sample, np.ones((3,3)))
        sizes = np.bincount(components.ravel())
        sizes[0] = 0
        assert count and sizes.max(), (pose['id'], group)
        seeds.append(components == sizes.argmax())
    owners = np.argmin(np.stack([distance_transform_edt(~seed) for seed in seeds]), axis=0)
    chosen = np.full((256,256), slots.index('body.torso'), int)
    for k, group in enumerate(groups, 1):
        chosen[owners == k] = slots.index(group[0])
    for side in ['left','right']:
        wrist, hand = wrists[side][offset], hands[side][offset]
        dx, dy = hand[0]-wrist[0], hand[1]-wrist[1]
        beyond = (xx-wrist[0])*dx + (yy-wrist[1])*dy >= 0
        arm_index = slots.index('body.arm.'+side)
        chosen[(chosen == arm_index) & beyond] = slots.index('body.hand.'+side)
    # Explicit anatomical boundaries resolve adjacent ink where nearest filled
    # material is ambiguous (hands touching shorts, overlapping near/far arms).
    def assign_polygon(points, slot):
        raster = Image.new('L', (256,256))
        ImageDraw.Draw(raster).polygon(points, fill=255)
        selected = (np.array(raster)>0) & visible & ~white & ~gray
        chosen[selected] = slots.index(slot)
    if offset == 3:
        assign_polygon([(138,140),(141,145),(143,153),(145,160),(143,163),(138,163)], 'body.arm.right')
        assign_polygon([(137,160),(144,160),(146,165),(143,169),(137,168),(136,164)], 'body.hand.right')
    assign_polygon(arm_regions[offset], 'body.arm.left')
    assign_polygon(hand_regions[offset], 'body.hand.left')
    if offset == 0:
        assign_polygon([(111,159),(115,159),(115,165),(111,165)], 'body.hand.right')
    pose['ownershipOverrides'] = [
        {'slot': slot, 'pixels': [[int(x),int(y)] for y,x in zip(*np.where(visible & (chosen == k)))]}
        for k,slot in enumerate(slots) if slot != 'head.base' and np.any(visible & (chosen == k))]
    for side in ['left','right']:
        region = visible & (chosen == slots.index('body.leg.'+side)) & (alpha >= 128)
        components, count = label(region, np.ones((3,3)))
        sizes = np.bincount(components.ravel()); sizes[0] = 0
        region = components == sizes.argmax()
        bottom = int(np.where(region)[0].max())
        row = np.where(region[bottom])[0]
        pose['soleMarkers'][side] = [int(row[len(row)//2]), bottom]
    reports.append({'pose':pose['id'], 'reassignedVisiblePixels':int((visible & (old != chosen)).sum()),
                    'sourceRGBAChanged':False})
config['transitionContourReview'] = 'Source contours assigned with their limb/hand, not default torso; fixed coordinates reviewed as full slot plates.'
(folder/'authoring.json').write_text(json.dumps(config, indent=2)+'\n')
(folder/'source/transition-contour-review.json').write_text(json.dumps(reports, indent=2)+'\n')
print(reports)
