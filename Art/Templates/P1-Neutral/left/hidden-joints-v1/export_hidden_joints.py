#!/usr/bin/env python3
"""Export fixed, hidden anatomical caps for the P1 left neutral base.

This is an offline authoring export. It writes only underlays, geometry, and QA data.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops

OUT=Path(__file__).resolve().parent
DEFAULT_BASE=OUT.parent/'walk-r3-complete-transitions'

# Fixed 256px canvas guides for the original nine r2 poses. Four later
# transition guides can be appended here when their reviewed geometry arrives.
LIMBS=[
 {'left': {'wrist':[128,170],'knee':[128,195],'ankle':[124,211]}, 'right':{'wrist':[140,166],'knee':[119,194],'ankle':[112,208]}},
 {'left': {'wrist':[147,170],'knee':[117,198],'ankle':[111,212]}, 'right':{'wrist':[97,162],'knee':[141,190],'ankle':[153,203]}},
 {'left': {'wrist':[142,168],'knee':[119,197],'ankle':[113,211]}, 'right':{'wrist':[103,160],'knee':[143,189],'ankle':[151,201]}},
 {'left': {'wrist':[127,170],'knee':[122,198],'ankle':[119,207]}, 'right':{'wrist':[108,164],'knee':[137,195],'ankle':[127,215]}},
 {'left': {'wrist':[99,154],'knee':[114,191],'ankle':[111,207]}, 'right':{'wrist':[148,165],'knee':[145,196],'ankle':[158,211]}},
 {'left': {'wrist':[101,160],'knee':[116,192],'ankle':[111,207]}, 'right':{'wrist':[147,165],'knee':[145,196],'ankle':[157,211]}},
 {'left': {'wrist':[104,161],'knee':[119,195],'ankle':[121,211]}, 'right':{'wrist':[146,166],'knee':[147,199],'ankle':[151,214]}},
 {'left': {'wrist':[116,169],'knee':[121,198],'ankle':[124,214]}, 'right':{'wrist':[142,167],'knee':[143,194],'ankle':[138,207]}},
 {'left': {'wrist':[144,168],'knee':[119,193],'ankle':[112,208]}, 'right':{'wrist':[100,160],'knee':[140,194],'ankle':[151,211]}},
 {'left': {'wrist':[136,168],'knee':[128,195],'ankle':[127,211]}, 'right':{'wrist':[113,162],'knee':[119,194],'ankle':[112,209]}},
 {'left': {'wrist':[144,165],'knee':[118,194],'ankle':[108,209]}, 'right':{'wrist':[103,161],'knee':[131,194],'ankle':[135,208]}},
 {'left': {'wrist':[135,166],'knee':[119,193],'ankle':[104,208]}, 'right':{'wrist':[108,162],'knee':[130,193],'ankle':[128,207]}},
 {'left': {'wrist':[132,168],'knee':[127,195],'ankle':[127,211]}, 'right':{'wrist':[140,163],'knee':[121,194],'ankle':[119,211]}},
]
PHASES=['idle','left-near-contact','left-support','right-far-passing','right-far-late-swing','right-far-contact','right-far-support-left-recovery','left-near-passing','left-near-late-swing','walk-start-01','walk-start-02','walk-stop-01','walk-stop-02']
SLOTS=['body.torso','body.arm.right','body.arm.left','body.hand.right','body.hand.left','body.leg.right','body.leg.left']
DRAW_ORDER=['body.leg.right','body.leg.left','body.arm.right','body.hand.right','body.torso','head.base','body.arm.left','body.hand.left']


def visible_layer_dir(base):
    """Prefer the immutable pre-underlay slot snapshot when present."""
    snapshot=base/'source/visible-layers'
    return snapshot if snapshot.is_dir() else base/'layers'


def visible_frame_dir(base):
    """Prefer the immutable pre-underlay composite snapshot when present."""
    snapshot=base/'source/visible-frames'
    return snapshot if snapshot.is_dir() else base/'frames'


def capsule(mask,a,b,radius):
    draw=ImageDraw.Draw(mask); ax,ay=a; bx,by=b
    steps=max(abs(bx-ax),abs(by-ay),1)*4; r=int(round(radius))
    for i in range(steps+1):
        x=round(ax+(bx-ax)*i/steps); y=round(ay+(by-ay)*i/steps)
        draw.ellipse((x-r,y-r,x+r,y+r),fill=255)


def chain(mask,points,radius):
    for a,b in zip(points,points[1:]): capsule(mask,a,b,radius)


def patch_color(image,box,predicate,fallback):
    crop=image.crop(box).convert('RGBA')
    colors=[p[:3] for p in crop.getdata() if p[3]>=200 and predicate(p[:3])]
    if not colors: return list(fallback)
    return list(Counter(colors).most_common(1)[0][0])


def skin_color(hand_path,fallback):
    im=Image.open(hand_path).convert('RGBA')
    # Fixed source-slot swatch selection, performed once by the offline exporter.
    # It reads only the anatomically matching hand slot, never torso/short pixels.
    pixels=[p[:3] for p in im.getdata() if p[3]>=200 and p[0]>p[1]>p[2] and p[0]>150 and p[1]>35 and p[2]<185]
    return list(Counter(pixels).most_common(1)[0][0]) if pixels else list(fallback)


def build_pose(base,layer_root,i,auth_pose,transition_pose=None):
    layerdir=layer_root/f'{i:02}'
    source=Image.open(base/f'registered/{i:02}.png').convert('RGBA')
    cfg=auth_pose['joints']; l=LIMBS[i]
    # The separately authored transition record is the latest source for hand
    # centers and sole markers. Keep joints (including hips) from r3 authoring.
    hand_markers=(transition_pose or {}).get('handMarkers') or {}
    sole_markers=(transition_pose or {}).get('soleMarkers') or auth_pose['soleMarkers']
    # Fixed pose-facing side labels: left is near, right is far.
    arms={
      'body.arm.left': {'shoulder':cfg['shoulderLeft'],'elbow':cfg['elbowLeft'],'wrist':hand_markers.get('left',l['left']['wrist'])},
      'body.arm.right':{'shoulder':cfg['shoulderRight'],'elbow':cfg['elbowRight'],'wrist':hand_markers.get('right',l['right']['wrist'])},
    }
    legs={
      'body.leg.left': {'hip':cfg['hipLeft'],'root':[cfg['hipLeft'][0],cfg['hipLeft'][1]+3],'knee':l['left']['knee'],'ankle':l['left']['ankle']},
      'body.leg.right':{'hip':cfg['hipRight'],'root':[cfg['hipRight'][0],cfg['hipRight'][1]+3],'knee':l['right']['knee'],'ankle':l['right']['ankle']},
    }
    torso=Image.open(layerdir/'body.torso.png').convert('RGBA')
    fallback_skin=[252,203,156]
    materials={
      'skin.near':skin_color(layerdir/'body.hand.left.png',fallback_skin),
      'skin.far':skin_color(layerdir/'body.hand.right.png',[239,153,102]),
      'skin.neck':patch_color(torso,(123,128,128,137),lambda c:c[0]>140 and c[0]>c[1]>c[2],[252,203,156]),
      'cloth.vest':patch_color(torso,(112,138,129,169),lambda c:c[0]>180 and c[1]>175 and c[2]>145,[249,235,216]),
      'cloth.shorts':patch_color(torso,(113,170,137,180),lambda c:max(c)-min(c)<40 and max(c)<130,[66,58,63]),
    }
    phase=PHASES[i] if i<len(PHASES) else auth_pose.get('id',auth_pose.get('support','unlabeled-transition'))
    return {'frame':i,'phase':phase,
      'guideSources':{'shouldersElbowsAndHips':'authoring.json joints','transitionHandsAndSoles':'source/transition-authoring.json' if transition_pose else 'authoring.json / fixed pose guide'},
      'neck':cfg['neck'],'shoulders':{'near-left':cfg['shoulderLeft'],'far-right':cfg['shoulderRight']},
      'arms':arms,'hips':{'near-left':cfg['hipLeft'],'far-right':cfg['hipRight']},'legs':legs,
      'soleMarkers':sole_markers,'materials':materials}


def make_masks(pose):
    masks={s:Image.new('L',(256,256),0) for s in SLOTS}
    # Torso-only garment and neck material. The polygons stay inside fixed torso
    # anatomy and never copy source arm/hand pixels from the flattened source.
    d=ImageDraw.Draw(masks['body.torso'])
    d.polygon([(119,130),(130,130),(132,136),(130,143),(130,164),(134,171),(131,177),(117,177),(113,171),(114,145),(116,137)],fill=255)
    # Neck root is a separate skin island; garment islands below are kept away
    # from the arm-colored outer shoulder bands.
    d.line((125,128,125,137),fill=255,width=7)
    d.ellipse((121,132,129,139),fill=255)
    # Separate garment islands prevent arm-shaped ownership leaks through the armpit.
    d.polygon([(118,136),(129,136),(131,141),(130,163),(133,169),(129,172),(117,170),(114,165),(115,145)],fill=255)
    d.polygon([(117,170),(132,170),(135,174),(132,179),(119,179),(115,176)],fill=255)
    # Arm capsules use only skin swatches extracted from the matching hand slot.
    for slot,arm in pose['arms'].items():
        chain(masks[slot],[arm['shoulder'],arm['elbow'],arm['wrist']],6 if slot.endswith('right') else 5)
        x,y=arm['shoulder']; ImageDraw.Draw(masks[slot]).ellipse((x-5,y-5,x+5,y+5),fill=255)
    for side,slot in [('left','body.hand.left'),('right','body.hand.right')]:
        x,y=pose['arms'][f'body.arm.{side}']['wrist']
        ImageDraw.Draw(masks[slot]).ellipse((x-4,y-4,x+4,y+4),fill=255)
    # Continuous upper-leg root capsules. The seam stress probe checks hips only;
    # knee/ankle motion is deliberately outside this validation claim.
    for slot,leg in pose['legs'].items():
        chain(masks[slot],[leg['hip'],leg['knee']],7 if slot.endswith('right') else 6)
        x,y=leg['hip']; ImageDraw.Draw(masks[slot]).ellipse((x-7,y-5,x+7,y+7),fill=255)
    return masks


def later_opaque_mask(layer_root,frame,slot):
    order=DRAW_ORDER
    selected=order[order.index(slot):]
    occluder=Image.new('L',(256,256),0)
    for name in selected:
        path=layer_root/f'{frame:02}/{name}.png'
        a=Image.open(path).convert('RGBA').getchannel('A').point(lambda v:255 if v>=250 else 0)
        occluder=ImageChops.lighter(occluder,a)
    return occluder


def material_fill(mask,color):
    fill=Image.new('RGBA',(256,256),tuple(color)+ (255,))
    fill.putalpha(mask)
    return fill


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',type=Path,default=DEFAULT_BASE,help='pose base containing authoring.json, registered/, visible layers/layers, and visible frames/frames')
    parser.add_argument('--exclude-indices',default='',help='comma-separated source pose indices to omit while those poses are under art revision')
    args=parser.parse_args(); base=args.base.resolve()
    excluded={int(v) for v in args.exclude_indices.split(',') if v.strip()}
    cfg=json.load(open(base/'authoring.json'))
    transition_path=base/'source/transition-authoring.json'
    transition_by_id={}
    if transition_path.is_file():
        transition_cfg=json.load(open(transition_path))
        transition_by_id={p.get('id'):p for p in transition_cfg.get('poses',[]) if p.get('id')}
    selected=[i for i in range(len(cfg['poses'])) if i not in excluded]
    layer_root=visible_layer_dir(base)
    frame_root=visible_frame_dir(base)
    if len(cfg['poses'])>len(LIMBS):
        raise SystemExit(f'{len(cfg["poses"])} poses found but only {len(LIMBS)} reviewed pose guides exist; append transition guides before export')
    for folder in OUT.joinpath('underlays').glob('*'):
        if folder.is_dir() and folder.name.isdigit() and int(folder.name) not in selected:
            import shutil; shutil.rmtree(folder)
    OUT.joinpath('underlays').mkdir(exist_ok=True)
    poses=[]; results=[]
    for i in selected:
        auth_pose=cfg['poses'][i]
        if i>=len(PHASES): raise SystemExit('pose phase labels must be extended with the new transition geometry')
        # Keep the in-module guides authoritative and pose count explicit.
        transition_pose=transition_by_id.get(auth_pose.get('id'))
        pose=build_pose(base,layer_root,i,auth_pose,transition_pose); poses.append(pose)
        masks=make_masks(pose)
        layerdir=layer_root/f'{i:02}'
        (OUT/f'underlays/{i:02}').mkdir(parents=True,exist_ok=True)
        under={}
        for slot in SLOTS:
            if slot=='body.torso': color=pose['materials']['cloth.vest']
            elif slot in ('body.arm.left','body.hand.left','body.leg.left'): color=pose['materials']['skin.near']
            elif slot in ('body.arm.right','body.hand.right','body.leg.right'): color=pose['materials']['skin.far']
            else: color=pose['materials']['cloth.shorts']
            if slot=='body.torso':
                # Lower pelvis island uses shorts cloth; upper torso islands use vest cloth.
                alpha=masks[slot]
                shorts=Image.new('L',(256,256),0); ImageDraw.Draw(shorts).polygon([(117,170),(132,170),(135,174),(132,179),(119,179),(115,176)],fill=255)
                neck=Image.new('L',(256,256),0); ImageDraw.Draw(neck).line((125,128,125,137),fill=255,width=7); ImageDraw.Draw(neck).ellipse((121,132,129,139),fill=255)
                vest_alpha=ImageChops.subtract(ImageChops.subtract(alpha,shorts),neck)
                cap=material_fill(vest_alpha,pose['materials']['cloth.vest'])
                cap.alpha_composite(material_fill(ImageChops.multiply(alpha,shorts),pose['materials']['cloth.shorts']))
                cap.alpha_composite(material_fill(ImageChops.multiply(alpha,neck),pose['materials']['skin.neck']))
            else:
                cap=material_fill(masks[slot],color)
            # Only hidden underpaint survives: the original visible art or a later
            # opaque slot must cover it at this fixed pose. This preserves r2 RGBA.
            alpha=ImageChops.multiply(cap.getchannel('A'),later_opaque_mask(layer_root,i,slot))
            cap.putalpha(alpha); cap.save(OUT/f'underlays/{i:02}/{slot}.png'); under[slot]=cap
        original=Image.open(frame_root/f'{i:02}.png').convert('RGBA')
        composite=Image.new('RGBA',(256,256)); order=cfg.get('drawOrder',DRAW_ORDER)
        visible_same=0; added=0
        for slot in order:
            if slot!='head.base': composite.alpha_composite(under[slot])
            composite.alpha_composite(Image.open(layerdir/f'{slot}.png').convert('RGBA'))
        for y in range(256):
          for x in range(256):
            a=original.getpixel((x,y)); b=composite.getpixel((x,y))
            if a[3]:
              if a!=b: raise RuntimeError(f'visible RGBA changed at frame {i}, {x},{y}: {a} != {b}')
              visible_same+=1
            elif b[3]: added+=1
        # Joint-only perturbation check: arms at shoulder/elbow/wrist; legs at hip.
        # Knee and ankle points are excluded because their old locations are expected to move.
        offset=[(dx,dy) for r in (1,2) for dx,dy in [(-r,-r),(0,-r),(r,-r),(-r,0),(r,0),(-r,r),(0,r),(r,r)]]
        stress=[]
        for slot,points in [
          ('body.arm.left',[pose['arms']['body.arm.left'][k] for k in ('shoulder','wrist')]),
          ('body.arm.right',[pose['arms']['body.arm.right'][k] for k in ('shoulder','wrist')]),
          ('body.leg.left',[pose['legs']['body.leg.left']['hip']]),
          ('body.leg.right',[pose['legs']['body.leg.right']['hip']])]:
            moving=Image.open(layerdir/f'{slot}.png').convert('RGBA')
            region={(x,y) for cx,cy in points for x in range(max(0,cx-1),min(256,cx+2)) for y in range(max(0,cy-1),min(256,cy+2)) if original.getpixel((x,y))[3]>=250}
            trials=[]
            for dx,dy in offset:
                shifted=moving.transform((256,256),Image.Transform.AFFINE,(1,0,-dx,0,1,-dy),Image.Resampling.NEAREST)
                test=Image.new('RGBA',(256,256))
                for name in order:
                    if name!='head.base': test.alpha_composite(under[name])
                    part=shifted if name==slot else Image.open(layerdir/f'{name}.png').convert('RGBA')
                    test.alpha_composite(part)
                holes=sum(test.getpixel((x,y))[3]==0 for x,y in region)
                trials.append({'offset':[dx,dy],'newTransparentPixelsAtJointContacts':holes})
            stress.append({'slot':slot,'testedJoints':['shoulder','wrist'] if 'arm.' in slot else ['hip-root'],'testedVisiblePixels':len(region),'maxNewTransparentPixels':max(t['newTransparentPixelsAtJointContacts'] for t in trials),'trials':trials})
        expected_colors={
          'body.torso':{tuple(pose['materials'][k]) for k in ('skin.neck','cloth.vest','cloth.shorts')},
          'body.arm.left':{tuple(pose['materials']['skin.near'])},'body.hand.left':{tuple(pose['materials']['skin.near'])},'body.leg.left':{tuple(pose['materials']['skin.near'])},
          'body.arm.right':{tuple(pose['materials']['skin.far'])},'body.hand.right':{tuple(pose['materials']['skin.far'])},'body.leg.right':{tuple(pose['materials']['skin.far'])}}
        material_check={}
        for slot in SLOTS:
            art=Image.open(OUT/f'underlays/{i:02}/{slot}.png').convert('RGBA')
            used={p[:3] for p in art.getdata() if p[3]>0}
            material_check[slot]={'onlyAuthoredPartPalette':used.issubset(expected_colors[slot]),'colors':sorted([list(c) for c in used])}
            if not material_check[slot]['onlyAuthoredPartPalette']:
                raise RuntimeError(f'wrong source-part palette in {slot}, frame {i}: {used}')
        results.append({'frame':i,'originalVisibleRGBAExact':True,'preservedNontransparentPixels':visible_same,'newlyVisiblePixels':added,'samePartMaterialPaletteExact':material_check,'jointContactStress':stress})
    geometry={'schemaVersion':'1.2.0','id':'p1-neutral-left-hidden-joints-v1','base':str(base.relative_to(OUT.parent)) if base.is_relative_to(OUT.parent) else str(base),'visibleInputs':{'layers':str(layer_root.relative_to(base)),'frames':str(frame_root.relative_to(base))},'canvas':[256,256],
      'registration':{'sourceCanvas':[1254,1254],'scale':0.194,'translation':[4.72,6.4]},
      'generation':'All anatomy is authored as fixed masks. For transition poses, hand centers and sole markers come from source/transition-authoring.json; shoulder, elbow, and hip joints come from r3 authoring.json. Skin caps use a deterministic swatch from the matching immutable pre-underlay visible hand slot; vest and shorts use pixels from the pre-underlay torso-slot local garment regions. When source/visible-layers and source/visible-frames exist they are preferred, so already merged underlays never affect palette selection, occlusion masks, composite checks, or joint probes. No flattened composite pixel is copied into a different anatomy slot.',
      'slotOrder':'same-slot underlay immediately before original slot; respect source drawOrder; far right limbs remain behind torso; near left arm remains over torso',
      'geometry':{'body.torso':'central neck/vest/waist/pelvis islands; excludes arm-shaped source fragments; shorts use a separate lower pelvis island','body.arm.left':'shoulderLeft→elbowLeft→wristLeft connected radius-5 skin cap, swatch from body.hand.left','body.arm.right':'shoulderRight→elbowRight→wristRight connected radius-6 skin cap, swatch from body.hand.right','body.hand.left':'radius-4 wrist cuff, same-side skin swatch','body.hand.right':'radius-4 wrist cuff, same-side skin swatch','body.leg.left':'hip-to-knee radius-6 upper-leg root cap, same-side skin swatch','body.leg.right':'hip-to-knee radius-7 upper-leg root cap, same-side skin swatch'},
      'occlusion':'Only cap pixels covered by an opaque later visible slot are exported. This preserves the fixed-pose original composite exactly and prevents the near shoulder cap from painting over the vest.',
      'probeScope':'±1/±2px eight-direction translation of each arm at shoulder/wrist contacts and each leg at hip-root only; counts gaps in opaque core pixels only. Antialiased outline pixels, knees, and ankles are excluded. Source poses omitted for art revision are listed by --exclude-indices. This is not an arbitrary-action or eight-direction completion claim.',
      'poses':poses}
    (OUT/'geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')
    (OUT/'verification.json').write_text(json.dumps({'method':'underlay then original slot in source drawOrder; compare all original nontransparent RGBA from the immutable visible frame snapshot when available; palette selection, later-slot occlusion, and joint probes use immutable visible layer snapshots when available; assert torso palette contains only neck/vest/short swatches and each limb slot only its matching-side skin swatch; local arm shoulder/wrist and leg hip-root shift probes count only opaque contact-core pixels, excluding antialiased outer contours and knee/ankle old locations','visibleInputs':{'layers':str(layer_root.relative_to(base)),'frames':str(frame_root.relative_to(base))},'frames':results},indent=2)+'\n')

if __name__=='__main__': main()
