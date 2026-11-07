#!/usr/bin/env python3
"""Check the two supplied rune VFX packs against source archives and Xcode assets."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image, ImageChops
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'Sources/Resources/Assets.xcassets'
SPECS=[
    {'kind':'slash','zip':ROOT/'Art/Parts/BattleVFX/rune-slash-v2/source-pack.zip','dir':'Art/Parts/BattleVFX/rune-slash-v2','sha256':'1deda544b19ca5102603363f968b648b19015d4bae9642178af72bdd35732f2f','sheet_zip':'rune_slash_attack_spritesheet.png','sheet_copy':'rune_slash_attack_spritesheet.png','prefix_zip':'rune_slash_attack/frame_','prefix_copy':'frames/frame_','asset':'MeadowRuneSlashAttack'},
    {'kind':'ward','zip':ROOT/'Art/Parts/BattleVFX/rune-ward-v1/source-pack.zip','dir':'Art/Parts/BattleVFX/rune-ward-v1','sha256':'98036771fc2d8b67772902e625a3d3998a115aeff257be7d12f46f74c80b740c','sheet_zip':'rune_ward_deliverables/rune_ward_cast/rune_ward_cast_spritesheet.png','sheet_copy':'rune_ward_cast_spritesheet.png','prefix_zip':'rune_ward_deliverables/rune_ward_cast/frames/rune_ward_cast_','prefix_copy':'frames/frame_','asset':'MeadowRuneWardCast'},
]

def same(a,b,where):
    assert a.mode==b.mode=='RGBA' and a.size==b.size, f'{where}: mode/size mismatch {a.mode}/{a.size} versus {b.mode}/{b.size}'
    assert ImageChops.difference(a,b).getbbox() is None, f'{where}: pixels differ'

def rgba(image,where):
    assert image.mode=='RGBA',f'{where}: expected RGBA, got {image.mode}'
    return image

def main():
    report=[]
    for spec in SPECS:
        source=spec['zip'];assert source.is_file(),f'missing source archive: {source}'
        digest=hashlib.sha256(source.read_bytes()).hexdigest();assert digest==spec['sha256'],f'{spec["kind"]}: source archive SHA-256 mismatch'
        folder=ROOT/spec['dir']
        with ZipFile(source) as archive:
            assert archive.testzip() is None,f'{spec["kind"]}: source archive CRC failure'
            names=set(archive.namelist());sheet=rgba(Image.open(archive.open(spec['sheet_zip'])),spec['sheet_zip'])
            assert sheet.size==(1280,1024),f'{spec["kind"]}: unexpected sheet size {sheet.size}'
            archived=[];bounds=[]
            for index in range(20):
                if spec['kind']=='slash':name=f'{spec["prefix_zip"]}{index:03}.png';copy=f'{spec["prefix_copy"]}{index:03}.png'
                else:name=f'{spec["prefix_zip"]}{index+1:03}.png';copy=f'{spec["prefix_copy"]}{index:03}.png'
                assert name in names,f'{spec["kind"]}: missing source frame {name}'
                frame=rgba(Image.open(archive.open(name)),name);assert frame.size==(256,256),f'{name}: unexpected size {frame.size}'
                x,y=(index%5)*256,(index//5)*256
                same(frame,sheet.crop((x,y,x+256,y+256)),name+' sheet crop')
                copy_frame=rgba(Image.open(folder/copy),str(folder/copy));same(frame,copy_frame,name+' archived copy')
                asset_name=f'{spec["asset"]}{index+1:02}'
                image_dir=CATALOG/f'{asset_name}.imageset'
                contents=json.loads((image_dir/'Contents.json').read_text())
                assert contents['images'][0]['filename']==asset_name+'.png',asset_name+' catalog filename'
                app=rgba(Image.open(image_dir/(asset_name+'.png')),asset_name);same(frame,app,name+' runtime catalog')
                alpha=frame.getchannel('A');bounds.append(alpha.getbbox())
                archived.append({'asset':asset_name,'size':list(frame.size),'alphaBounds':list(alpha.getbbox()) if alpha.getbbox() else None})
            final=rgba(Image.open(archive.open((f'{spec["prefix_zip"]}019.png' if spec['kind']=='slash' else f'{spec["prefix_zip"]}020.png'))),spec['kind']+' final frame')
            assert final.getchannel('A').getbbox() is None,f'{spec["kind"]}: ending frame must be fully transparent'
            report.append({'kind':spec['kind'],'sourceArchiveSHA256':digest,'frames':archived,'sheetSize':[1280,1024],'runtimeCatalogPixelExact':True,'finalFrameTransparent':True})
    print(json.dumps({'sourcePacks':report,'totalFrames':40,'allChecksPassed':True},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
