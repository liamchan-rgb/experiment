#!/usr/bin/env python3
"""Build the registered left Wayfarer coat pose-map from immutable source art."""
import json, math, sys, importlib.util
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('wardrobe_helper', ROOT/'scripts'/'export-wardrobe-part.py')
helper=importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
editable=helper.editable


def place(im, matrix):
    a,b,c,d,tx,ty=matrix
    det=a*d-b*c
    if abs(det)<1e-9: raise ValueError('singular transform')
    inv=(d/det,-c/det,(c*ty-d*tx)/det,-b/det,a/det,(b*tx-a*ty)/det)
    return im.transform((256,256),Image.Transform.AFFINE,inv,Image.Resampling.NEAREST)


def affine_between(p0,p1,q0,q1):
    vx,vy=p1[0]-p0[0],p1[1]-p0[1]
    wx,wy=q1[0]-q0[0],q1[1]-q0[1]
    vl=math.hypot(vx,vy); wl=math.hypot(wx,wy)
    scale=wl/vl
    ang=math.atan2(wy,wx)-math.atan2(vy,vx)
    cs,sn=math.cos(ang)*scale,math.sin(ang)*scale
    a,b,c,d=cs,sn,-sn,cs
    return [a,b,c,d,q0[0]-a*p0[0]-c*p0[1],q0[1]-b*p0[0]-d*p0[1]]


def translation(dx,dy): return [1,0,0,1,dx,dy]


def polygon_mask(poly):
    m=Image.new('L',(256,256)); ImageDraw.Draw(m).polygon([tuple(p) for p in poly],fill=255)
    return m


def mask_image(im, mask):
    out=im.copy(); out.putalpha(ImageChops.multiply(out.getchannel('A'),mask)); return out


def underlap(layer, body_layer, fill, outline=(15,24,38,255), grow=2):
    # Fill any visible arm/torso pixels missed by the generated art, with a
    # 2px concealed overlap and a one-pixel tailored outline at the edge.
    alpha=body_layer.getchannel('A')
    k=2*grow+1
    expanded=alpha.filter(ImageFilter.MaxFilter(k))
    if grow>1:
        core=alpha.filter(ImageFilter.MaxFilter(3))
    else: core=alpha
    # The outlines stay within the expanded garment silhouette.
    edge=ImageChops.subtract(expanded,core)
    back=Image.new('RGBA',(256,256),fill); back.putalpha(expanded)
    ink=Image.new('RGBA',(256,256),outline); ink.putalpha(edge)
    back.alpha_composite(ink)
    back.alpha_composite(layer)
    return back


def remove_stray_light_seam(layer, cuff_y):
    # Pale pixels above the wrist are the source lapel crossing a sleeve, not
    # exposed skin or cuff trim. Remove that small seam before arm underlap.
    rgba=layer.load()
    for y in range(cuff_y):
        for x in range(layer.width):
            r,g,b,a=rgba[x,y]
            if a and r>150 and g>115 and b>65:
                rgba[x,y]=(r,g,b,0)
    return layer


def frame_slot(folder, slot, frame):
    return Image.open(folder / 'png' / f'{frame:02}' / f'{slot}.png').convert('RGBA')


def export(folder=HERE):
    cfg=json.loads((folder/'authoring.json').read_text())
    source=Image.open(folder/cfg['source']).convert('RGBA')
    if source.size != tuple(cfg['sourceCanvas']) or source.mode!='RGBA':
        raise ValueError('generated source must remain full-canvas RGBA')
    if source.getpixel((0,0))[3] != 0:
        raise ValueError('generated source has a nontransparent canvas corner')
    scale=cfg['registration']['sourceScale']; tx,ty=cfg['registration']['sourceTranslation']
    coat=source.transform((256,256),Image.Transform.AFFINE,
        (1/scale,0,-tx/scale,0,1/scale,-ty/scale),Image.Resampling.NEAREST)
    pose_data=cfg['poses']; idle=pose_data[0]
    alpha=coat.getchannel('A')
    if alpha.getbbox() is None: raise ValueError('coat art is empty after fixed registration')
    masks={s:polygon_mask(poly) for s,poly in cfg['partitionPolygonsCanvas'].items()}
    # Trim the far sleeve region to the actual blue cloth panel; the generated
    # source's collar/torso edge otherwise moves as a pale shard when the arm
    # is posed. The cuff remains part of this sleeve panel.
    right_sleeve_trim=Image.new('L',(256,256)); ImageDraw.Draw(right_sleeve_trim).polygon(
        [(132,145),(140,145),(145,150),(148,168),(146,179),(141,183),(135,181),(132,174),(129,160),(129,150)],fill=255)
    masks['outfit.sleeve.right']=right_sleeve_trim
    far_cuff=Image.new('L',(256,256)); cp=far_cuff.load(); src=coat.load()
    for y in range(181,190):
        for x in range(124,142):
            r,g,b,a=src[x,y]
            if a and ((r>145 and g>105 and b>65) or (r<45 and g<45 and b<45) or (40<r<135 and g<115 and b<110)):
                cp[x,y]=255
    masks['outfit.sleeve.right']=ImageChops.lighter(masks['outfit.sleeve.right'],far_cuff)
    # The source lapel piping crosses the near sleeve partition at the armpit.
    # Cut that source-only sliver before the sleeve is posed; the underlap then
    # supplies continuous blue cloth over the exact common arm silhouette.
    near_seam=Image.new('L',(256,256)); nd=ImageDraw.Draw(near_seam); nd.polygon([(109,138),(117,139),(118,158),(116,163),(109,160)],fill=255); nd.polygon([(114,160),(120,160),(120,176),(114,176)],fill=255)
    masks['outfit.sleeve.left']=ImageChops.subtract(masks['outfit.sleeve.left'],near_seam)
    sleeve_union=ImageChops.lighter(masks['outfit.sleeve.left'],masks['outfit.sleeve.right'])
    hem_union=ImageChops.lighter(masks['outfit.hem.front'],masks['outfit.hem.back'])
    # Keep sleeve cuffs owned by the sleeve slots. At the skirt root, remove
    # only the source's non-blue cuff pixels; preserve continuous blue coat
    # fabric below the belt so the skirt is not cut into a gap.
    cuff_material=Image.new('L',(256,256)); cm=cuff_material.load(); px=coat.load()
    for y in range(181,190):
        for x in range(124,142):
            r,g,b,a=px[x,y]
            if a and not (b>45 and b>r*1.35 and b>g*1.05): cm[x,y]=255
    for hem_slot in ('outfit.hem.front','outfit.hem.back'):
        masks[hem_slot]=ImageChops.subtract(masks[hem_slot],sleeve_union)
        masks[hem_slot]=ImageChops.subtract(masks[hem_slot],cuff_material)
    torso_mask=ImageChops.subtract(masks['outfit.torso'],ImageChops.lighter(sleeve_union,hem_union))
    torso_mask=ImageChops.subtract(torso_mask,near_seam)
    masks['outfit.torso']=torso_mask
    raw={s:mask_image(coat,masks[s]) for s in cfg['slots']}
    # Rebuild the small flat-blue skirt area beneath the removed detached cuff
    # so the tail remains continuous after the semantic slot split.
    skirt_patch=Image.new('RGBA',(256,256),(35,66,128,0)); ImageDraw.Draw(skirt_patch).polygon(
        [(124,181),(140,181),(142,183),(141,188),(138,190),(126,190)],fill=(35,66,128,255))
    for hem_slot in ('outfit.hem.front','outfit.hem.back'):
        raw[hem_slot].alpha_composite(skirt_patch)
    out_png=folder/'png'
    (folder/'editable').mkdir(exist_ok=True)
    bindings=[]
    # Snapshot the art-side reference layers into this package for repeatable
    # coverage masks. Only their alpha geometry is used; no body pixels export.
    body_root=ROOT/'Art/Templates/P1-Neutral/left/walk-r3-complete-transitions/source/visible-layers'
    # Colors sampled from the generated coat material, not from the body.
    navy=(35,66,128,255); ink=(15,24,38,255)
    for p in pose_data:
        i=p['frame']; dest=out_png/f'{i:02}'; dest.mkdir(parents=True,exist_ok=True)
        parts={}
        # Torso follows the common shoulder/neck registration. Motion is read
        # from the authored joints; this rig holds shoulder roots in place.
        sh0=idle['shoulders']; sh=p['shoulders']
        dx=sum(sh['near-left'][0]-sh0['near-left'][0] for _ in [0])
        dy=round(((sh['near-left'][1]-sh0['near-left'][1])+(sh['far-right'][1]-sh0['far-right'][1]))/2)
        torso=place(raw['outfit.torso'],translation(dx,dy))
        body_torso=Image.open(body_root/f'{i:02}'/'body.torso.png').convert('RGBA')
        parts['outfit.torso']=underlap(torso,body_torso,navy,ink,2)
        # Each sleeve is transformed from the authored idle shoulder/wrist to
        # this pose, then checked against actual visible arm pixels.
        for slot in ('outfit.sleeve.right','outfit.sleeve.left'):
            spec=cfg['sleeveSourceBones'][slot]; key=spec['rigKey']
            arm0=idle['arms'][key]; arm=p['arms'][key]
            mat=affine_between(spec['sourceShoulder'],spec['sourceWrist'],
                               arm['shoulder'],arm['wrist'])
            sleeve=place(raw[slot],mat)
            sleeve=remove_stray_light_seam(sleeve,160 if slot.endswith('right') else 165)
            body_arm=Image.open(body_root/f'{i:02}'/f'{key}.png').convert('RGBA')
            parts[slot]=underlap(sleeve,body_arm,navy,ink,2)
        # Split tails hinge below the belt, shortening the authored full-length
        # pattern to sit just above the knees, then sway opposite each other.
        base=cfg['tailPivot']; swing=math.radians(cfg['tailSwingDegrees'][i])
        for slot,sign in [('outfit.hem.front',1),('outfit.hem.back',-1)]:
            art=raw[slot]
            pivot=(124,176) if slot.endswith('front') else (134,176)
            # First shorten the tails while preserving their registered roots.
            sy=cfg['tailLengthScale']; short=place(art,[1,0,0,sy,0,pivot[1]*(1-sy)])
            angle=swing*sign
            c,s=math.cos(angle),math.sin(angle)
            mat=[c,s,-s,c,pivot[0]-c*pivot[0]+s*pivot[1],pivot[1]-s*pivot[0]-c*pivot[1]]
            parts[slot]=place(short,mat)
        # Explicit ordinary pose-map slot order, independent of body ownership.
        parts={s:parts[s] for s in cfg['slots']}
        for slot,im in parts.items(): im.save(dest/f'{slot}.png')
        editable(folder/'editable',f'{i:02}',parts)
        if i==0: idle_parts=parts
        if i==0: clip,frame='idle',0
        elif i<=8: clip,frame='walk',i
        elif i<=10: clip,frame='walk-start',i-8
        else: clip,frame='walk-stop',i-10
        bindings.append({'direction':'left','clip':clip,'frame':frame,
                         'layers':{s:f'png/{i:02}/{s}.png' for s in cfg['slots']}})
    manifest={'schemaVersion':'1.0.0','id':cfg['id'],'version':'1.0.0','part':'outfit',
      'compatibility':cfg['compatibility'],'mode':'pose-map','slots':cfg['slots'],
      'directions':['left'],'clips':['idle','walk','walk-start','walk-stop'],
      'bindings':bindings,'sourceFiles':cfg['sourceFiles']+['authoring.json']+
       [f'png/{i:02}/{slot}.png' for i in range(13) for slot in cfg['slots']]+
       [f'editable/{i:02}.{ext}' for i in range(13) for ext in ('ora','svg')]}
    (folder/'asset.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Layered self-audit GIF: only garment layers on transparency, normal 120ms.
    frames=[]
    for i in range(13):
        im=Image.new('RGBA',(256,256),(24,35,34,255))
        for slot in cfg['slots']: im.alpha_composite(frame_slot(folder,slot,i))
        frames.append(im.convert('P',palette=Image.Palette.ADAPTIVE))
    review=folder/'review'; review.mkdir(exist_ok=True)
    frames[0].save(review/'layered-coat-13poses-120ms.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2)
    # Full-body inspection uses the companion shared lower outfit as read-only
    # art, interleaved with the immutable body and this package's upper layers.
    whole=[]
    lower_root=ROOT/'Art/Parts/P1-v1/left/traveler-lower-v1/png'
    order=['weapon.back','outfit.hem.back','body.leg.right','body.leg.left',
      'outfit.pants.right','outfit.pants.left','outfit.boot.right','outfit.boot.left',
      'outfit.hem.front','body.arm.right','outfit.sleeve.right','body.hand.right',
      'outfit.torso','head.base','body.arm.left','outfit.sleeve.left','body.hand.left']
    for i in range(13):
        canvas=Image.new('RGBA',(256,256),(24,35,34,255))
        for slot in order:
            if slot == 'weapon.back':
                canvas.alpha_composite(Image.open(ROOT/'Art/Parts/P1-v1/left/back-scabbard-v1/png/weapon.back.png').convert('RGBA'))
            elif slot.startswith('outfit.') and slot not in ('outfit.pants.right','outfit.pants.left','outfit.boot.right','outfit.boot.left'):
                canvas.alpha_composite(frame_slot(folder,slot,i))
            elif slot.startswith('outfit.'):
                canvas.alpha_composite(Image.open(lower_root/f'{i:02}'/f'{slot}.png').convert('RGBA'))
            else:
                path=body_root/f'{i:02}'/f'{slot}.png'
                canvas.alpha_composite(Image.open(path).convert('RGBA'))
        whole.append(canvas.convert('P',palette=Image.Palette.ADAPTIVE))
    whole[0].save(review/'fullbody-left-wayfarer-13poses-120ms.gif',save_all=True,append_images=whole[1:],duration=120,loop=0,disposal=2)
    # Static 2x and 1x idle registration diagnostics.
    whole_rgba=Image.new('RGBA',(256,256),(24,35,34,255))
    for slot in order:
        path=body_root/'00'/f'{slot}.png' if not slot.startswith('outfit.') and slot != 'weapon.back' else None
        lower_slot=slot in ('outfit.pants.right','outfit.pants.left','outfit.boot.right','outfit.boot.left')
        if slot == 'weapon.back': layer=Image.open(ROOT/'Art/Parts/P1-v1/left/back-scabbard-v1/png/weapon.back.png').convert('RGBA')
        elif lower_slot: layer=Image.open(ROOT/'Art/Parts/P1-v1/left/traveler-lower-v1/png/00'/f'{slot}.png').convert('RGBA')
        else: layer=Image.open(path).convert('RGBA') if path else frame_slot(folder,slot,0)
        whole_rgba.alpha_composite(layer)
    whole_rgba.resize((256,256),Image.Resampling.NEAREST).save(review/'idle-1x.png')
    whole_rgba.resize((512,512),Image.Resampling.NEAREST).save(review/'idle-2x.png')
    print(json.dumps({'asset':cfg['id'],'bindings':len(bindings),'slots':len(cfg['slots']),
                      'generatedAlpha':source.getchannel('A').getextrema(),'backgroundAlpha':source.getpixel((0,0))[3]}))

if __name__=='__main__': export()
