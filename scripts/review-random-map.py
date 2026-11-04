#!/usr/bin/env python3
"""Offline review from Swift-generated layout, production smoothed roads/motion,
and unchanged project sprites. Atmosphere/shadows/UI are approximations, not an
application screenshot, Metal render, device capture or performance measurement.
"""
from pathlib import Path
import json, math, os
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Art/Review/Map/random-map-v1'
ASSETS=ROOT/'Sources/Resources/Assets.xcassets'
@lru_cache(None)
def font(n):
    choices=[os.environ.get('MEADOW_REVIEW_FONT',''),'/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc','/System/Library/Fonts/PingFang.ttc']
    selected=next((p for p in choices if p and Path(p).is_file()),None)
    if not selected:raise RuntimeError('Set MEADOW_REVIEW_FONT to a CJK font file')
    return ImageFont.truetype(selected,n)
@lru_cache(None)
def asset(name):return Image.open(ASSETS/(name+'.imageset')/(name+'.png')).convert('RGBA')
cache={}
def prepare(n,seed):
    name=f'map-{n}-{seed}'
    data=json.loads((OUT/'data'/f'{name}.json').read_text())
    geometry=json.loads((OUT/'data'/f'{name}-geometry.json').read_text())
    ground=asset('MeadowGround').resize((1600,1160)).crop((160,220,1440,940))
    mask=Image.new('L',ground.size);draw=ImageDraw.Draw(mask)
    for road in geometry['roads']:draw.line([tuple(p) for p in road['points']],fill=180,width=40,joint='curve')
    mask=mask.filter(ImageFilter.GaussianBlur(3))
    ground=Image.composite(Image.new('RGBA',ground.size,(125,108,70,255)),ground,mask)
    mask2=Image.new('L',ground.size);draw=ImageDraw.Draw(mask2)
    for road in geometry['roads']:draw.line([tuple(p) for p in road['points']],fill=75,width=19,joint='curve')
    ground=Image.composite(Image.new('RGBA',ground.size,(171,150,96,255)),ground,mask2)
    props=[]
    anchors={'OakA':.09,'OakB':.09,'Pines':.09,'CampTent':.10,'Shrub':.04,'Flowers':.04}
    for p in data['props']:
        key=p['asset'];im=asset(key);w=round(p['width']);h=round(w*im.height/im.width)
        im=im.resize((w,h),Image.Resampling.LANCZOS)
        props.append((p['y'],im,(round(p['x']-w/2),round(p['y']-h*(1-anchors.get(key,.10))))))
        shadow=Image.new('RGBA',ground.size);d=ImageDraw.Draw(shadow)
        x,y=p['x'],p['y'];d.ellipse((x-w*.35,y-3,x+w*.65,y+w*.20),fill=(8,21,11,55))
        ground.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(3)))
    return data,ground,props

def hero(h):
    i=h['index'];f=h['facing'];frame=h['frame'];diag=f>=4;row=f-4 if diag else f
    if i==0:
        col=0 if frame==0 else 9+frame-25 if frame>=25 else 1+(frame-1)//3
    else:col=frame
    key=(i,diag,col,row)
    if key not in cache:
        sheet=asset(f'Hero{i+1}'+('Diagonals' if diag else 'Directions'))
        cell=sheet.height//4
        cache[key]=sheet.crop((col*cell,row*cell,(col+1)*cell,(row+1)*cell)).resize((64,64),Image.Resampling.NEAREST)
    return cache[key]

def draw_map(prepared,heroes=()):
    data,ground,props=prepared;im=ground.copy();objects=list(props)
    for h in heroes:
        sprite=hero(h);x,y=h['x'],h['y']
        d=ImageDraw.Draw(im);d.ellipse((x-9,y-3,x+9,y+3),fill=(18,28,16,140))
        objects.append((y,sprite,(round(x-32),round(y-56))))
    for _,img,pos in sorted(objects,key=lambda x:x[0]):im.alpha_composite(img,pos)
    d=ImageDraw.Draw(im)
    names={'start':'起','combat':'战','boss':'首','reward':'奖','empty':'空'}
    colors={'start':'#e8c95c','combat':'#c55c4f','boss':'#ac71bc','reward':'#6cba81','empty':'#8e9a91'}
    for node in data['map']['nodes']:
        x,y=node['x']*1280,node['y']*720
        cy=y-24 if node['kind']!='start' else y
        d.ellipse((x-13,cy-13,x+13,cy+13),fill='#26392c',outline=colors[node['kind']],width=2)
        d.text((x,cy),names[node['kind']],font=font(15),fill='#f7e5b3',anchor='mm')
    for h in heroes:d.text((h['x'],h['y']+12),f"P{h['index']+1}",font=font(10),fill='#fff0c2',stroke_width=1,stroke_fill='#1a2e21',anchor='mm')
    return im

def caption(im,text):
    im=im.convert('RGB');d=ImageDraw.Draw(im);d.rectangle((0,0,im.width,39),fill='#192c20')
    d.text((14,7),text,font=font(18),fill='#e5d49c');return im

def main():
    OUT.mkdir(parents=True,exist_ok=True);tiles=[]
    for n in (4,10,30):
        prepared=prepare(n,31827);p=prepared[0]['spawn']
        heroes=json.loads((OUT/'data'/f'map-{n}-31827-geometry.json').read_text())['initialHeroes']
        image=caption(draw_map(prepared,heroes),f'{n}节点 · 种子31827 · 离线合成预览')
        image.save(OUT/f'map-{n}-overview.png');tiles.append(image.resize((640,360)))
    board=Image.new('RGB',(1920,360))
    for i,t in enumerate(tiles):board.paste(t,(i*640,0))
    board.save(OUT/'comparison.png')
    prepared=prepare(10,31827);samples=json.loads((OUT/'data/walk-samples.json').read_text())
    first,last=samples[0]['heroes'][0],samples[-1]['heroes'][0]
    cx=(first['x']+last['x'])/2;cy=(first['y']+last['y'])/2-70
    left=max(0,min(480,round(cx-400)));top=max(0,min(270,round(cy-225)))
    frames=[]
    for sample in samples:
        image=draw_map(prepared,sample['heroes']).crop((left,top,left+800,top+450)).resize((960,540),Image.Resampling.LANCZOS)
        frames.append(caption(image,'随机林地行走 · 生产路径/动作数据 · 离线合成'))
    palette=frames[0].quantize(colors=256)
    quant=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    quant[0].save(OUT/'walk-normal.gif',save_all=True,append_images=quant[1:],duration=20,loop=0,optimize=True,disposal=1)
    contact=Image.new('RGB',(1280,720),'#17291e')
    for i,index in enumerate(range(0,400,25)):
        contact.paste(frames[index].resize((320,180)),((i%4)*320,(i//4)*180))
    contact.save(OUT/'walk-contact.png')
    (OUT/'review.json').write_text(json.dumps({'kind':'offline existing-resource composition','scope':'4/10/30 nodes;9 Swift adapter geometry exports;400 production motion samples at20ms','notDeviceOrUIKitCapture':True,'shadowAtmosphereRoadMaterialApproximate':True,'newCharacterArtwork':False,'normalGifFrames':400,'normalGifFrameMs':20,'nativeUIRuntimeVerified':False,'artApproval':None},ensure_ascii=False,indent=2)+'\n')
    print('Rendered three overviews, comparison, normal 400x20ms walk GIF and contact sheet')
if __name__=='__main__':main()
