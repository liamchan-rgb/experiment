#!/usr/bin/env python3
"""Export the first neutral body review from authored, registered source art.

One common source-to-world transform is used for all parts. No alpha-bounds
fitting, component scaling, recolouring or appearance-dependent base selection.
"""
import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/Templates/P1-Neutral/down/r1'
SIZE=(256,256)
MATRIX=(6.25,0,-156.25,0,6.25,-237.5)
ORDER=['body.leg.right','body.leg.left','body.arm.right','body.arm.left',
       'body.torso','head.base','body.hand.right','body.hand.left']


def blank():
    return Image.new('RGBA',SIZE)


def source(name):
    im=Image.open(OUT/'source'/f'{name}.png').convert('RGBA')
    if im.size!=(1254,1254):
        raise ValueError('source canvas is not the calibrated 1254px square')
    # Reserved registration gutter only; the art itself is not trimmed/fitted.
    gutter=Image.new('RGBA',im.size)
    gutter.alpha_composite(im.crop((80,80,1174,1174)),(80,80))
    out=gutter.transform(SIZE,Image.Transform.AFFINE,MATRIX,Image.Resampling.BICUBIC)
    # Common export convention for near-opaque tool PNG interiors. Raw source
    # files remain unchanged; no appearance/part receives a special alpha rule.
    a=np.array(out);a[:,:,3][a[:,:,3]>=250]=255
    return Image.fromarray(a)


def masked(im, points):
    mask=Image.new('L',SIZE)
    ImageDraw.Draw(mask).polygon(points,fill=255)
    a=np.array(im);a[np.array(mask)==0]=0
    return Image.fromarray(a)


def merged(parts):
    out=blank()
    for name in ORDER:
        out.alpha_composite(parts[name])
    return out


def png(im):
    b=io.BytesIO();im.save(b,'PNG');return b.getvalue()


def write_editable(parts,whole):
    node=ET.Element('image',version='0.0.1',w='256',h='256',name='P1 neutral down idle r1')
    stack=ET.SubElement(node,'stack')
    with zipfile.ZipFile(OUT/'neutral-00.ora','w') as z:
        def put(name,data,stored=False):
            info=zipfile.ZipInfo(name,date_time=(2026,10,18,0,0,0))
            info.compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
            z.writestr(info,data)
        put('mimetype','image/openraster',True)
        for i,name in enumerate(reversed(ORDER)):
            src=f'data/{i}.png'
            ET.SubElement(stack,'layer',name=name,src=src,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
            put(src,png(parts[name]))
        put('stack.xml',ET.tostring(node,encoding='utf-8',xml_declaration=True))
        put('mergedimage.png',png(whole))
        put('Thumbnails/thumbnail.png',png(whole.resize((128,128))))
    ns='http://www.w3.org/2000/svg';ink='http://www.inkscape.org/namespaces/inkscape'
    ET.register_namespace('',ns);ET.register_namespace('inkscape',ink)
    svg=ET.Element(f'{{{ns}}}svg',width='256',height='256',viewBox='0 0 256 256')
    for name in ORDER:
        g=ET.SubElement(svg,f'{{{ns}}}g',id=name)
        g.set(f'{{{ink}}}groupmode','layer');g.set(f'{{{ink}}}label',name)
        ET.SubElement(g,f'{{{ns}}}image',x='0',y='0',width='256',height='256',href='data:image/png;base64,'+base64.b64encode(png(parts[name])).decode())
    (OUT/'neutral-00.svg').write_text(ET.tostring(svg,encoding='unicode')+'\n')
    # The actual shared head, with optional technical guides and an empty art
    # layer, is the authoring reference for every future face/hair resource.
    hs=ET.Element(f'{{{ns}}}svg',width='768',height='768',viewBox='0 0 96 96')
    base=ET.SubElement(hs,f'{{{ns}}}g',id='shared-head-reference')
    base.set(f'{{{ink}}}groupmode','layer');base.set(f'{{{ink}}}label','Shared head reference')
    head=parts['head.base'].crop((76,61,172,157))
    ET.SubElement(base,f'{{{ns}}}image',width='96',height='96',href='data:image/png;base64,'+base64.b64encode(png(head)).decode())
    guide=ET.SubElement(hs,f'{{{ns}}}g',id='guides',fill='none',stroke='#427f92',**{'stroke-width':'.25'})
    guide.set(f'{{{ink}}}groupmode','layer');guide.set(f'{{{ink}}}label','Proposed feature guides - hide before export')
    profile=json.loads((ROOT/'Art/Standards/P1-Parts-v1/profile.json').read_text())
    for boxes in profile['headLayouts']['down']['faceRegions'].values():
        for x0,y0,x1,y1 in boxes:
            ET.SubElement(guide,f'{{{ns}}}rect',x=str(x0),y=str(y0),width=str(x1-x0),height=str(y1-y0))
    draw=ET.SubElement(hs,f'{{{ns}}}g',id='new-independent-art')
    draw.set(f'{{{ink}}}groupmode','layer');draw.set(f'{{{ink}}}label','Draw new hair OR facial features here')
    (OUT/'head-authoring.svg').write_text(ET.tostring(hs,encoding='unicode')+'\n')


def main():
    (OUT/'layers/00').mkdir(parents=True,exist_ok=True)
    full=source('full-00')
    # Authoring partitions at anatomical joins, not colour-based segmentation.
    # Complete shoulder-girdle surfaces belong to the common torso; arm roots
    # overlap underneath them. These are source-export masks, not rig fitting.
    right=[(108,132),(113,132),(113,140),(112,149),(110,154),(108,160),
           (108,168),(96,168),(95,163),(98,155),(101,146),(104,138)]
    left=[(250-x,y) for x,y in right]
    parts={'head.base':source('head'),'body.torso':source('torso_fixed'),
           'body.arm.right':masked(full,right),'body.arm.left':masked(full,left),
           'body.hand.right':masked(full,[(94,164),(108,164),(108,178),(94,178)]),
           'body.hand.left':masked(full,[(142,164),(156,164),(156,178),(142,178)])}
    # Hip roots remain complete below a fixed anatomical cut plane, with ample
    # hidden overlap behind the safety shorts; no skin is painted onto clothing.
    for side in ['right','left']:
        parts[f'body.leg.{side}']=masked(source(f'leg-{side}'),[(0,170),(255,170),(255,255),(0,255)])
    whole=merged(parts)
    for name,im in parts.items():
        im.save(OUT/'layers/00'/f'{name}.png')
    whole.save(OUT/'00.png')
    (OUT/'body-crop-debug.png').unlink(missing_ok=True)
    parts['head.base'].crop((76,61,172,157)).save(OUT/'head-down.png')
    write_editable(parts,whole)
    manifest={'schemaVersion':'1.0.0','id':'p1-neutral-down-r1','version':'1.0.0',
              'part':'base','compatibility':{'rig':'p1-chibi-v1','bodyProfile':'p1-standard','actionSet':'locomotion-v1'},
              'mode':'pose-map','slots':ORDER,'directions':['down'],'clips':['idle'],
              'sourceFiles':['neutral-00.ora','neutral-00.svg'],
              'bindings':[{'direction':'down','clip':'idle','frame':0,
                           'layers':{k:f'layers/00/{k}.png' for k in ORDER}}]}
    (OUT/'asset.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    registration={'status':'candidate-not-approved','sourceCanvas':[1254,1254],
                  'sourceToWorld':[.16,0,0,.16,25,38],
                  'sourceGutter':[80,80,1174,1174],
                  'allPartsShareOneTransform':True,'alphaFitOrPerPartResize':False,
                  'commonAlphaExport':'alpha >= 250 becomes 255 for all parts; raw sources unchanged',
                  'handAndArmSource':'full-00.png, fixed anatomical partitions',
                  'shoulderGirdleOwner':'body.torso; arm roots overlap underneath',
                  'hipRootCutY':170,'headLocalCanvas':[96,96],'headLocalOrigin':[76,61],
                  'eyeGuideWorld':{'right':[114,117],'left':[134,117]},
                  'neckGuideWorld':[124,133],'rightWristGuide':[102,165],
                  'leftWristGuide':[148,165],'hipRightGuide':[117,176],
                  'hipLeftGuide':[135,176],
                  'shoulderRightGuide':[110,140],'shoulderLeftGuide':[140,140],
                  'elbowRightGuide':[104,153],'elbowLeftGuide':[146,153],
                  'gripRightGuide':[102,170],'gripLeftGuide':[148,170],
                  'kneeRightGuide':[118,188],'kneeLeftGuide':[134,188],
                  'ankleRightGuide':[116,205],'ankleLeftGuide':[134,205],
                  'soleRightGuide':[117,214],'soleLeftGuide':[134,214],
                  'guidesAreProposedNotApproved':True,'layerOrder':ORDER,
                  'walkingFrames':'not produced; first shared-body proportions need artwork review'}
    (OUT/'registration.json').write_text(json.dumps(registration,ensure_ascii=False,indent=2)+'\n')
    # Review layout: same sprite scale in both assembly and exploded layer view.
    review=Image.new('RGBA',(1200,720),'#dce4df');d=ImageDraw.Draw(review)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    d.text((24,18),'P1 NEUTRAL BODY / DOWN / 00 - REVIEW',font=font,fill='#254345')
    d.text((24,52),'ASSEMBLED - SHARED BASE',font=small,fill='#486567')
    d.text((424,52),'EIGHT INDEPENDENT LAYERS',font=small,fill='#486567')
    d.text((824,52),'HEAD STANDARD / PROPOSED',font=small,fill='#486567')
    for x in [398,798]:d.line((x,80,x,690),fill='#bccfc4',width=1)
    crop=(75,64,175,230)
    sprite=whole.crop(crop).resize((400,664),Image.Resampling.NEAREST)
    review.alpha_composite(sprite,(0,64))
    exploded=blank()
    offsets={'head.base':(0,-10),'body.arm.right':(-12,0),'body.arm.left':(12,0),
             'body.hand.right':(-12,0),'body.hand.left':(12,0),
             'body.leg.right':(-5,8),'body.leg.left':(5,8),'body.torso':(0,0)}
    for name in ORDER:
        exploded.alpha_composite(parts[name],offsets[name])
    review.alpha_composite(exploded.crop(crop).resize((400,664),Image.Resampling.NEAREST),(400,64))
    head=parts['head.base'].crop((76,61,172,157)).resize((384,384),Image.Resampling.NEAREST)
    review.alpha_composite(head,(808,95))
    for x,y in [(38,56),(58,56)]:
        x=808+x*4;y=95+y*4;d.line((x-7,y,x+7,y),fill='#487f94',width=1);d.line((x,y-7,x,y+7),fill='#487f94',width=1)
    for i,line in enumerate(['Head: scalp + ears, no features','Torso: neck + safety innerwear','Arms: shoulder joins -> wrists','Hands: separate grip layers','Legs: complete hips -> bare toes','One base for ALL future appearances','Eye crosses are guides, not artwork']):
        d.text((825,510+i*24),line,font=small,fill='#486567')
    review.convert('RGB').save(OUT/'review.png')
    print('Exported neutral idle candidate: eight 256px layers, shared head tile, ORA/SVG and review.')


if __name__=='__main__':
    main()
