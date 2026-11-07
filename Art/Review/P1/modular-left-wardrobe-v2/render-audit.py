#!/usr/bin/env python3
"""Render independent left loadouts and inspect real compositor contributions."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CANDIDATE = ROOT/'Art/Templates/P1-Wardrobe/left/v2-painted-poses'
BODY = ROOT/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def flatten(image, scale=1):
    result = Image.new('RGBA',image.size,'#17372c')
    result.alpha_composite(image)
    return result.convert('RGB').resize((image.width*scale,image.height*scale),Image.Resampling.NEAREST)


def gif(images, path, durations=None):
    frames = [flatten(image,2) for image in images]
    atlas = Image.new('RGB',(frames[0].width*len(frames),frames[0].height))
    for i,image in enumerate(frames):
        atlas.paste(image,(i*image.width,0))
    palette = atlas.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    frames = [frame.quantize(palette=palette,dither=Image.Dither.NONE) for frame in frames]
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations or 120,loop=0,disposal=2)


def components(image):
    """Find visible 8-connected islands, preserving their full-canvas coordinates."""
    remaining = set(map(tuple,np.argwhere(np.array(image.getchannel('A'))>=32)))
    result = []
    while remaining:
        seed = remaining.pop()
        stack,points = [seed],[seed]
        while stack:
            y,x = stack.pop()
            for dy,dx in itertools.product([-1,0,1],repeat=2):
                point = (y+dy,x+dx)
                if point in remaining:
                    remaining.remove(point);stack.append(point);points.append(point)
        ys,xs = zip(*points)
        result.append({'pixels':len(points),'bbox':[min(xs),min(ys),max(xs)+1,max(ys)+1]})
    return sorted(result,key=lambda item:item['pixels'],reverse=True)


def main():
    compositor = module('parts',ROOT/'scripts/compose-character-parts.py')
    cfg = json.loads((CANDIDATE/'loadouts.json').read_text())
    engine = compositor.Compositor(ROOT,CANDIDATE/'catalog.json',CANDIDATE/'motion.json')
    reference = json.loads((CANDIDATE/'base-invariance.json').read_text())
    original_motion = json.loads((BODY/'motion.json').read_text())
    assert digest(BODY/'asset.json') == reference['bodyManifestSHA256']
    assert digest(BODY/'motion.json') == reference['bodyMotionSHA256']
    assert digest(ROOT/'scripts/compose-character-parts.py') == reference['genericCompositorSHA256']
    for filename,sha in reference['frames'].items():
        assert digest(BODY/'frames'/filename) == sha
    bare_images,hand_masks = [],[]
    for i,(original,current) in enumerate(zip(original_motion['frames'],engine.motion['frames'])):
        assert {k:v for k,v in original.items() if k!='drawOrder'} == {k:v for k,v in current.items() if k!='drawOrder'}
        assert [slot for slot in current['drawOrder'] if slot in original['drawOrder']] == original['drawOrder']
        rendered = engine.render(cfg['base'],[],'left',current['clip'],current['frame'])
        assert np.array_equal(np.array(rendered),np.array(Image.open(BODY/f'frames/{i:02}.png')))
        bare_images.append(np.array(rendered))
        bare_layers = engine.layers(cfg['base'],[],'left',current['clip'],current['frame'])
        hand_mask = np.zeros((256,256),dtype=bool)
        for n,(slot,layer) in enumerate(bare_layers):
            if slot.startswith('body.hand.'):
                contribution = np.array(layer.getchannel('A'),dtype=float)/255
                for _,above in bare_layers[n+1:]:
                    contribution *= 1-np.array(above.getchannel('A'),dtype=float)/255
                hand_mask |= contribution>=.99
        hand_masks.append(hand_mask)
    renders,records,coverage,hand_checks = {},[],[],[]
    for hair,face,style,carried in itertools.product(cfg['hair'],cfg['face'],cfg['style'],cfg['weapon']):
        selected = [value for value in [cfg['hair'][hair],cfg['face'][face],cfg['weapon'][carried]] if value]
        selected += cfg['style'][style]
        name = '__'.join([hair,face,style,carried])
        directory = OUT/'combinations'/name
        directory.mkdir(parents=True,exist_ok=True)
        images = []
        for i,frame in enumerate(engine.motion['frames']):
            layers = engine.layers(cfg['base'],selected,'left',frame['clip'],frame['frame'])
            image = engine.render(cfg['base'],selected,'left',frame['clip'],frame['frame'])
            path = directory/f"{frame['clip']}-{frame['frame']:02}.png"
            image.save(path)
            records.append({'combination':name,'storageIndex':i,'clip':frame['clip'],'frame':frame['frame'],
                            'path':str(path.relative_to(OUT)),'sha256':digest(path)})
            images.append(image)
            if style != 'plain':
                changed = np.any(np.array(image)!=bare_images[i],axis=2)&hand_masks[i]
                hand_checks.append({'combination':name,'storageIndex':i,'changedVisibleOpaqueHandPixels':int(changed.sum())})
                for slot in ['body.arm.left','body.arm.right','body.leg.left','body.leg.right','body.torso']:
                    index = next(n for n,(key,_) in enumerate(layers) if key==slot)
                    contribution = np.array(layers[index][1].getchannel('A'),dtype=float)/255
                    for _,above in layers[index+1:]:
                        contribution *= 1-np.array(above.getchannel('A'),dtype=float)/255
                    if slot == 'body.torso':
                        # Only the shared anatomical neck opening is excluded.
                        contribution[128:138,120:133] = 0
                    coverage.append({'combination':name,'storageIndex':i,'slot':slot,
                                     'pixelsAbove5Percent':int((contribution>.05).sum()),
                                     'maximumContribution':float(contribution.max())})
        renders[(hair,face,style,carried)] = images
        gif(images[1:9],directory/'walk-120ms.gif')
    checks = []
    for hair,face,style in itertools.product(cfg['hair'],cfg['face'],cfg['style']):
        for i,frame in enumerate(engine.motion['frames']):
            empty = np.array(renders[(hair,face,style,'empty')][i])
            carried = np.array(renders[(hair,face,style,'back')][i])
            selected = [v for v in [cfg['hair'][hair],cfg['face'][face],cfg['weapon']['back']] if v]+cfg['style'][style]
            layers = dict(engine.layers(cfg['base'],selected,'left',frame['clip'],frame['frame']))
            weapon = np.array(layers['weapon.back'].getchannel('A')) > 0
            hands = (np.array(layers['body.hand.left'].getchannel('A'))>=250)|(np.array(layers['body.hand.right'].getchannel('A'))>=250)
            changed = np.any(empty!=carried,axis=2)
            checks.append({'hair':hair,'face':face,'style':style,'storageIndex':i,
                           'changedPixelsOutsideWeapon':int((changed&~weapon).sum()),
                           'changedOpaqueHandPixels':int((changed&hands).sum())})
    green = renders[('chestnut','blue','forester','back')]
    blue = renders[('chestnut','blue','wayfarer','back')]
    pairs = []
    for a,b in zip(green,blue):
        pair = Image.new('RGBA',(512,256))
        pair.alpha_composite(a,(0,0));pair.alpha_composite(b,(256,0))
        pairs.append(pair)
    flatten(pairs[0],2).save(OUT/'outfits-comparison-2x.png')
    gif(pairs[1:9],OUT/'outfits-comparison-120ms.gif')
    sequence = [0,9,10]+list(range(1,9))*2+[11,12,0]
    gif([pairs[i] for i in sequence],OUT/'start-stop-comparison-120ms.gif',[480]+[120]*20+[480])
    flatten(green[0]).save(OUT/'idle-review-1x.png')
    flatten(green[0],2).save(OUT/'idle-review-2x.png')
    gif(green[1:9],OUT/'walk-120ms.gif')
    gif([green[i] for i in sequence],OUT/'start-stop-120ms.gif',[480]+[120]*20+[480])
    board = Image.new('RGB',(1024,1024),'#17372c')
    for i,image in enumerate(green):
        board.paste(flatten(image),(i%4*256,i//4*256))
        frame = engine.motion['frames'][i]
        ImageDraw.Draw(board).text((i%4*256+5,i//4*256+5),f"{frame['clip']} {frame['frame']:02}",fill='white')
    board.save(OUT/'thirteen-poses-fullbody-1x.png')
    board.resize((2048,2048),Image.Resampling.NEAREST).save(OUT/'thirteen-poses-fullbody-2x.png')
    blue_board = Image.new('RGB',(1024,1024),'#17372c')
    for i,image in enumerate(blue):
        blue_board.paste(flatten(image),(i%4*256,i//4*256))
        frame = engine.motion['frames'][i]
        ImageDraw.Draw(blue_board).text((i%4*256+5,i//4*256+5),f"{frame['clip']} {frame['frame']:02}",fill='white')
    blue_board.save(OUT/'wayfarer-thirteen-poses-fullbody-1x.png')
    blue_board.resize((2048,2048),Image.Resampling.NEAREST).save(OUT/'wayfarer-thirteen-poses-fullbody-2x.png')
    heads = Image.new('RGB',(768,512),'#17372c')
    for n,(hair,face) in enumerate(itertools.product(['chestnut','silver','teal'],['blue','amber'])):
        heads.paste(flatten(renders[(hair,face,'forester','back')][0]),(n%3*256,n//3*256))
    heads.save(OUT/'head-combinations-fullbody-1x.png')
    heads.resize((1536,1024),Image.Resampling.NEAREST).save(OUT/'head-combinations-fullbody-2x.png')
    islands = []
    for style in ['forester','wayfarer']:
        for i,image in enumerate(renders[('none','none',style,'empty')]):
            # Hide independent hair/face/weapon so intentional loose hair tips or
            # an exposed sword hilt cannot hide detached clothing/boot fragments.
            detached = [item for item in components(image)[1:] if item['bbox'][1]>130]
            islands.append({'style':style,'storageIndex':i,'detachedBelowNeck':detached})
    island_failures = [item for item in islands if item['detachedBelowNeck']]
    hand_failures = [item for item in hand_checks if item['changedVisibleOpaqueHandPixels']]
    failures = [item for item in coverage if item['pixelsAbove5Percent']]
    toggle_failures = [item for item in checks if item['changedPixelsOutsideWeapon'] or item['changedOpaqueHandPixels']]
    report = {'status':'offline contribution evidence; visual approval separate','artApproval':None,
              'combinations':len(renders),'poses':len(records),'records':records,'bodyInvariance':True,
              'genericCompositorUnchanged':True,'coverage':coverage,'coverageFailures':failures,
              'weaponToggleChecks':checks,'weaponToggleFailures':toggle_failures,
              'clothingIslandChecks':islands,'clothingIslandFailures':island_failures,
              'handPreservationChecks':hand_checks,'handPreservationFailures':hand_failures,
              'coverageAllowance':'Only anatomical neck opening x120..132,y128..137; all other torso/arms/legs measured after real compositing.',
              'scope':'Left13 authored poses only; no arbitrary interruption, runtime/device or IPA.'}
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'combinations':len(renders),'poses':len(records),'coverageFailures':len(failures),
                      'weaponToggleFailures':len(toggle_failures),'clothingIslandFailures':len(island_failures),'handPreservationFailures':len(hand_failures)}))
    if failures or toggle_failures or island_failures or hand_failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
