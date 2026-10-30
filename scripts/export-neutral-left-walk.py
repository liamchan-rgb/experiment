#!/usr/bin/env python3
"""Package authored left-facing neutral poses with explicit anatomical ownership.

Source registration, seam masks and pose order are authored data. Head art is
shared across the whole cycle. This is an offline art exporter, not runtime
fitting or appearance-dependent repair.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask(points):
    im = Image.new('L', (256, 256))
    ImageDraw.Draw(im).polygon([tuple(p) for p in points], fill=255)
    return im


def flatten(im, scale=1):
    bg = Image.new('RGBA', im.size, '#17372c')
    bg.alpha_composite(im)
    return bg.convert('RGB').resize((im.width*scale, im.height*scale), Image.Resampling.NEAREST)


def gif(images, path, durations=None):
    frames = [flatten(im, 2) for im in images]
    atlas = Image.new('RGB', (frames[0].width*len(frames), frames[0].height))
    for i, im in enumerate(frames):
        atlas.paste(im, (i*im.width, 0))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    frames = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations or 120, loop=0, disposal=2)


def export(folder, review):
    cfg = json.loads((folder/'authoring.json').read_text())
    spec = importlib.util.spec_from_file_location('editable', ROOT/'scripts/export-wardrobe-part.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    spec = importlib.util.spec_from_file_location('compose', ROOT/'scripts/compose-character-parts.py')
    compose = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compose)
    for d in ['layers', 'frames', 'editable', 'registered']:
        (folder/d).mkdir(parents=True, exist_ok=True)
    review.mkdir(parents=True, exist_ok=True)

    registered = []
    for i, pose in enumerate(cfg['poses']):
        source = Image.open(folder/pose['source']).convert('RGBA')
        if list(source.size) != pose['sourceCanvas']:
            raise ValueError(f'source canvas changed: {i}')
        source.putalpha(source.getchannel('A').point(lambda a:255 if a>=250 else a))
        s, tx, ty = pose['sourceScale'], *pose['sourceTranslation']
        art = source.transform((256,256), Image.Transform.AFFINE,
                               (1/s,0,-tx/s,0,1/s,-ty/s), Image.Resampling.NEAREST)
        for point in pose.get('sourceDiscardPixels', []):
            point = tuple(point)
            if art.getpixel(point)[3] > 8:
                raise ValueError('pose registration cleanup cannot remove visible artwork')
            art.putpixel(point, (0,0,0,0))
        art.save(folder/'registered'/f'{i:02}.png')
        registered.append(art)

    head_mask = mask(cfg['headPartition'])
    common_head = registered[0].copy()
    common_head.putalpha(ImageChops.multiply(common_head.getchannel('A'), head_mask))
    for point in cfg.get('headMotion', {}).get('sourceDiscardPixels', []):
        if common_head.getpixel(tuple(point))[3] > 8:
            raise ValueError('head registration cleanup cannot remove visible artwork')
        common_head.putpixel(tuple(point),(0,0,0,0))
    neck_underlap = None
    if cfg.get('headMotion', {}).get('neckUnderlap'):
        neck_underlap = Image.open(folder/cfg['headMotion']['neckUnderlap']).convert('RGBA')
        if neck_underlap.size != (256,256):
            raise ValueError('neck underlap must use the fixed pose canvas')
    frames, bindings, motion_frames, checks = [], [], [], []
    for i, pose in enumerate(cfg['poses']):
        art = registered[i]
        # Exclude the generated per-pose head. The exact idle head is reused.
        remainder = ImageChops.invert(mask(pose.get('headPartition', cfg['headPartition'])))
        pieces = {}
        for slot in cfg['ownershipPriority']:
            selected = ImageChops.multiply(remainder, mask(pose['partitions'][slot]))
            part = art.copy()
            part.putalpha(ImageChops.multiply(part.getchannel('A'), selected))
            pieces[slot] = part
            remainder = ImageChops.subtract(remainder, selected)
        torso = art.copy()
        torso.putalpha(ImageChops.multiply(torso.getchannel('A'), remainder))
        pieces['body.torso'] = torso
        # Fixed, reviewed authoring corrections transfer the original pixel;
        # they never repaint or repair a runtime image. This keeps tiny edge
        # fragments with their limb without widening a seam into another part.
        overridden = set()
        excluded_head = mask(pose.get('headPartition', cfg['headPartition']))
        for correction in pose.get('ownershipOverrides', []):
            slot = correction['slot']
            if slot not in pieces:
                raise ValueError(f'invalid ownership override slot: {slot}')
            for point in correction['pixels']:
                if len(point) != 2 or not all(isinstance(v, int) and 0 <= v < 256 for v in point):
                    raise ValueError('ownership override must name an integer canvas pixel')
                point = tuple(point)
                if point in overridden or excluded_head.getpixel(point):
                    raise ValueError('duplicate ownership override or override inside shared head')
                overridden.add(point)
                original = art.getpixel(point)
                if original[3] == 0:
                    raise ValueError('ownership override cannot invent a source pixel')
                for owner, part in pieces.items():
                    part.putpixel(point, original if owner == slot else (0,0,0,0))
        if neck_underlap is not None:
            torso_with_underlap = neck_underlap.copy()
            torso_with_underlap.alpha_composite(pieces['body.torso'])
            pieces['body.torso'] = torso_with_underlap
        for slot, relative in pose.get('underlays', {}).items():
            if slot not in pieces:
                raise ValueError(f'invalid anatomical underlay slot: {slot}')
            underlay = Image.open(folder/relative).convert('RGBA')
            if underlay.size != (256,256):
                raise ValueError('anatomical underlays require the registered pose canvas')
            underlay.alpha_composite(pieces[slot])
            pieces[slot] = underlay
        head_motion = cfg.get('headMotion')
        if head_motion:
            angle = math.radians(head_motion['angleDeg'][i])
            a,b,c,d = math.cos(angle),-math.sin(angle),math.sin(angle),math.cos(angle)
            px,py = head_motion['pivot']
            dx,dy = head_motion['translation'][i]
            matrix = [a,b,c,d,px-a*px-c*py+dx,py-b*px-d*py+dy]
        else:
            dx,dy = pose.get('headTranslation',[0,0])
            matrix = [1,0,0,1,dx,dy]
        head = compose.place(common_head, matrix, (256,256))
        pieces['head.base'] = head
        directory = folder/'layers'/f'{i:02}'
        directory.mkdir(exist_ok=True)
        parts = {slot:pieces[slot] for slot in cfg['drawOrder']}
        paths = {}
        for slot, part in parts.items():
            path = directory/f'{slot}.png'
            part.save(path)
            paths[slot] = str(path.relative_to(folder))
        whole = helper.editable(folder/'editable',f'{i:02}',parts)
        whole.save(folder/'frames'/f'{i:02}.png')
        expected = art.copy()
        expected.putalpha(ImageChops.multiply(art.getchannel('A'), ImageChops.invert(mask(pose.get('headPartition',cfg['headPartition'])))))
        if neck_underlap is not None:
            background = neck_underlap.copy()
            background.alpha_composite(expected)
            expected = background
        expected.alpha_composite(head)
        actual_pixels, expected_pixels = np.array(whole), np.array(expected)
        visible = (actual_pixels[:,:,3] != 0) | (expected_pixels[:,:,3] != 0)
        diff = int((np.any(actual_pixels!=expected_pixels,axis=2) & visible).sum())
        if diff:
            raise ValueError(f'ownership changed expected pixels at {i}: {diff}')
        checks.append({'frame':i,'sourceNonHeadRGBARecompositionDifferencePixels':diff,'sha256':digest(folder/'frames'/f'{i:02}.png')})
        clip = pose.get('clip','idle' if i == 0 else 'walk')
        frame = pose.get('frame',i)
        bindings.append({'direction':'left','clip':clip,'frame':frame,'layers':paths})
        motion_frames.append({'direction':'left','clip':clip,'frame':frame,'facing':[-1,0],
                              'headToCanvas':[*matrix[:4],matrix[0]*76+matrix[2]*61+matrix[4],matrix[1]*76+matrix[3]*61+matrix[5]],
                              'drawOrder':cfg['drawOrder'],'joints':pose['joints'],'soleMarkers':pose['soleMarkers'],
                              'support':pose['support'],'sockets':{},'artApproval':None})
        frames.append(whole)
    manifest={'schemaVersion':'1.0.0','id':cfg.get('id','p1-neutral-left-walk-r1'),'version':cfg.get('version','1.0.0'),'part':'base',
              'compatibility':cfg['compatibility'],'mode':'pose-map','slots':cfg['drawOrder'],
              'directions':['left'],'clips':list(dict.fromkeys(b['clip'] for b in bindings)),'bindings':bindings,
              'sourceFiles':['authoring.json']+[str(p.relative_to(folder)) for d in ['source','editable'] for p in sorted((folder/d).rglob('*')) if p.is_file()]}
    (folder/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n')
    motion={'schemaVersion':'1.0.0','rig':'p1-chibi-v1','status':'left-neutral-candidate-awaiting-user-review',
            'artApproval':None,'canvas':[256,256],'compatibility':cfg['compatibility'],
            'baseManifestSHA256':digest(folder/'asset.json'),'durationMs':120,'cycleFrames':list(range(1,9)),
            'alphaFitOrPerPartResize':False,'frames':motion_frames}
    (folder/'motion.json').write_text(json.dumps(motion,indent=2)+'\n')
    strip = Image.new('RGBA',(256*len(frames),256))
    board = Image.new('RGB',(768,768),'#17372c')
    for i,im in enumerate(frames):
        strip.alpha_composite(im,(i*256,0))
        if i >= 9:
            continue
        x,y=i%3*256,i//3*256
        board.paste(flatten(im),(x,y))
        ImageDraw.Draw(board).text((x+5,y+5),f'{i:02}',fill='white')
    strip.save(folder/'strip.png')
    board.save(review/'nine-poses-fullbody-1x.png')
    board.resize((1536,1536),Image.Resampling.NEAREST).save(review/'nine-poses-fullbody-2x.png')
    flatten(frames[0]).save(review/'idle-review-1x.png')
    flatten(frames[0],2).save(review/'idle-review-2x.png')
    lookup={(b['clip'],b['frame']):im for b,im in zip(bindings,frames)}
    walk=[lookup[('walk',n)] for n in range(1,9)]
    gif(walk,review/'walk-120ms.gif')
    sequence=[lookup[('idle',0)]]
    sequence += [lookup[('walk-start',n)] for n in [1,2] if ('walk-start',n) in lookup]
    sequence += walk*2
    sequence += [lookup[('walk-stop',n)] for n in [1,2] if ('walk-stop',n) in lookup]
    sequence += [lookup[('idle',0)]]
    gif(sequence,review/'start-stop-120ms.gif',[480]+[120]*(len(sequence)-2)+[480])
    if len(frames)>9:
        extra=Image.new('RGB',(256*len(frames[9:]),256),'#17372c')
        draw=ImageDraw.Draw(extra)
        for offset,(binding,im) in enumerate(zip(bindings[9:],frames[9:])):
            extra.paste(flatten(im),(offset*256,0))
            draw.text((offset*256+5,5),f"{binding['clip']} {binding['frame']:02}",fill='white')
        extra.save(review/'transition-poses-fullbody-1x.png')
        extra.resize((extra.width*2,512),Image.Resampling.NEAREST).save(review/'transition-poses-fullbody-2x.png')
    (review/'pixel-audit.json').write_text(json.dumps({'status':'technical checks only; visual review required',
        'artApproval':None,'checks':checks,'headSource':'idle00 shared artwork; authored neck-pivot motion' if cfg.get('headMotion') else 'idle00 exact shared layer',
        'limits':['left neutral candidate only','ownership masks do not establish full hidden anatomy','no apparel or runtime integration']},indent=2)+'\n')
    print(json.dumps({'poses':len(frames),'layers':len(bindings)*8,'pixelDifferences':sum(c['sourceNonHeadRGBARecompositionDifferencePixels'] for c in checks)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path)
    p.add_argument('--review',type=Path,required=True)
    args=p.parse_args()
    export(args.folder,args.review)
