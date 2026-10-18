#!/usr/bin/env python3
"""Check independent art packages, without fitting or repairing their artwork.

This checks the draft contract. It is not an art-approval tool or an importer.
"""
import argparse
import json
from pathlib import Path

import jsonschema
import numpy as np
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT/'Art/Standards/P1-Parts-v1'


def region_mask(size, boxes, transform=None):
    mask = Image.new('L', size)
    draw = ImageDraw.Draw(mask)
    for x0,y0,x1,y1 in boxes:
        points = [(x0,y0),(x1-1,y0),(x1-1,y1-1),(x0,y1-1)]
        if transform:
            a,b,c,d,tx,ty=transform
            points=[(round(a*x+c*y+tx),round(b*x+d*y+ty)) for x,y in points]
        draw.polygon(points,fill=255)
    return mask


def safe_file(folder, value):
    relative=Path(value)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('path must be relative and must not contain ..')
    target=(folder/relative).resolve()
    if not target.is_relative_to(folder.resolve()):
        raise ValueError('path or symlink escapes package')
    if not target.is_file():
        raise ValueError('file missing')
    return target


def check_asset(path, schema_only=False, production=False):
    path=Path(path)
    errors=[]
    schema=json.loads((STANDARD/'asset.schema.json').read_text())
    profile=json.loads((STANDARD/'profile.json').read_text())
    try:
        asset=json.loads(path.read_text())
    except (OSError,ValueError) as e:
        return [str(e)]
    for e in jsonschema.Draft202012Validator(schema).iter_errors(asset):
        errors.append('/'.join(map(str,e.absolute_path))+': '+e.message)
    if errors:
        return errors
    part,mode=asset['part'],asset['mode']
    spec=profile['parts'][part]
    if mode not in spec['modes']:
        errors.append(f'{part} cannot use {mode}')
    if not set(asset['slots']) <= set(spec['slots']):
        errors.append('slot ownership violation: resource contains another part type')
    if part=='base' and set(asset['slots'])!=set(spec['slots']):
        errors.append('base body must supply every body/head/hand/leg slot')
    if part=='weapon':
        if 'gripProfile' not in asset:
            errors.append('weapon must declare its grip profile')
    elif 'gripProfile' in asset:
        errors.append('gripProfile only belongs to weapons')
    if mode=='socket':
        if part!='weapon':
            errors.append('socket mode is reserved for rigid weapons')
        if asset['slots'] != [asset['socket'].replace('grip.','weapon.')]:
            errors.append('weapon slot must match anatomical grip socket')
        if not all(0<=n<limit for n,limit in zip(asset['pivot'],asset['canvas'])):
            errors.append('pivot outside declared canvas')
    expected={(direction,clip,frame) for direction in asset['directions']
              for clip in asset['clips'] for frame in profile['clips'][clip]}
    actual=set()
    for binding in asset['bindings']:
        key=(binding['direction'],binding['clip'],binding['frame'])
        if key in actual:
            errors.append(f'duplicate binding {key}')
        actual.add(key)
        if set(binding['layers'])!=set(asset['slots']):
            errors.append(f'{key}: layers differ from declared slots')
    if expected!=actual:
        errors.append(f'coverage mismatch: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}')
    if production:
        if profile['status']!='locked':
            errors.append('production rejected: neutral body/head profile is not locked')
        if set(asset['directions'])!=set(profile['directions']) or set(asset['clips'])!={'idle','walk'}:
            errors.append('production requires all eight directions and idle/walk coverage')
    if schema_only or errors:
        return errors
    for value in asset['sourceFiles']:
        try:
            safe_file(path.parent,value)
        except ValueError as e:
            errors.append(f'source {value}: {e}')
    motion=json.loads((STANDARD/'motion-down.draft.json').read_text())
    frames={(f['direction'],f['clip'],f['frame']):f for f in motion['frames']}
    cache={}
    visible=False
    for binding in asset['bindings']:
        key=(binding['direction'],binding['clip'],binding['frame'])
        layout=profile['headLayouts'].get(binding['direction'])
        for slot,value in binding['layers'].items():
            try:
                target=safe_file(path.parent,value)
                if target not in cache:
                    with Image.open(target) as im:
                        if im.format!='PNG' or im.mode!='RGBA':
                            raise ValueError('must be an RGBA PNG')
                        cache[target]=im.copy()
                image=cache[target]
                size=asset['canvas'] if mode=='socket' else profile['headCanvas'] if mode=='head-local' else profile['canvas']
                if image.size!=tuple(size):
                    raise ValueError(f'canvas {image.size} must be {tuple(size)}; no auto-fit allowed')
                alpha=image.getchannel('A')
                visible |= alpha.getextrema()[1]>16
                w,h=image.size
                if any(alpha.crop(box).getextrema()[1]>8 for box in [(0,0,w,1),(0,h-1,w,h),(0,0,1,h),(w-1,0,w,h)]):
                    raise ValueError('visible content touches canvas edge; padding/clipping review required')
                if slot.startswith('face.') or slot=='hair.front':
                    if layout is None:
                        raise ValueError('head layout for this direction has not been defined')
                    if slot.startswith('face.'):
                        mask=region_mask(image.size,layout['faceRegions'][slot])
                        if ImageChops.subtract(alpha,mask).getextrema()[1]>8:
                            raise ValueError('face pixels outside standard feature regions; no face skin/jaw patch')
                    else:
                        transform=None
                        if mode=='pose-map':
                            if key not in frames:
                                raise ValueError('pose-map hair requires a calibrated head transform for this pose')
                            transform=frames[key]['headToCanvas']
                        mask=region_mask(image.size,layout['hairFrontKeepClear'],transform)
                        if ImageChops.multiply(alpha,mask).getextrema()[1]>16:
                            raise ValueError('front hair covers a protected eye window')
                if mode=='socket':
                    if key not in frames:
                        raise ValueError('socket transform for this direction/pose is not defined')
                    socket=frames[key]['sockets'][asset['socket']]
                    if socket['angleDeg'] is None:
                        raise ValueError('socket orientation has not been calibrated')
                    px,py=asset['pivot']
                    if alpha.getpixel((int(px),int(py)))<128:
                        raise ValueError('grip point falls outside solid handle artwork')
                    ys,xs=np.where(np.array(alpha)>8)
                    angle=np.deg2rad(socket['angleDeg'])
                    c,s=np.cos(angle),np.sin(angle)
                    x,y=socket['position']
                    dx=x+c*(xs-px)-s*(ys-py)
                    dy=y+s*(xs-px)+c*(ys-py)
                    if len(xs) and (dx.min()<2 or dy.min()<2 or dx.max()>253 or dy.max()>253):
                        raise ValueError('attached weapon crosses cell safety margin')
            except (OSError,ValueError) as e:
                errors.append(f'{key} {slot} {value}: {e}')
    if not visible:
        errors.append('package contains no visible artwork')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--schema-only',action='store_true',help='validate declarations, not supplied artwork')
    parser.add_argument('--production',action='store_true',help='require a locked rig and complete 8-direction coverage')
    args=parser.parse_args()
    if args.schema_only and args.production:
        parser.error('--production cannot skip artwork checks')
    errors=check_asset(args.manifest,args.schema_only,args.production)
    print(json.dumps({'manifest':str(args.manifest),'passed':not errors,
                      'scope':'declarations only' if args.schema_only else 'package file/region checks',
                      'artApproval':None,'errors':errors},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))


if __name__=='__main__':
    main()
