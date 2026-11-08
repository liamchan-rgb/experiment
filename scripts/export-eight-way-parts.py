#!/usr/bin/env python3
"""Bake fixed registered source parts into one eight-direction data contract.

This is an offline authoring exporter. The generic compositor remains unchanged.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT=Path(__file__).resolve().parents[1]
INTEGRATION=ROOT/'Art/Integration/P1-modular-eight-way-v1'
PARTS=ROOT/'Art/Parts/P1-v1/eight-way-v1'

def module(name, file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def translated(im,offset):
    out=Image.new('RGBA',im.size);out.paste(im,tuple(offset));return out
def support(label):
    if label=='left-late-swing':return 'right'
    if label=='right-late-swing':return 'left'
    return label.split('-')[0]

REG={'down':[4,-1],'down-left':[1,1],'left':[3,0],'up-left':[0,0],
     'up':[0,2],'up-right':[1,0],'right':[-2,0],'down-right':[0,1]}
ORDER={d:([8,1,2,3,4,5,6,7] if d=='down' else
          [5,6,7,8,1,2,3,4] if d in ['down-left','left','up-left','up'] else
          [1,2,3,4,5,6,7,8]) for d in REG}
BODY=['body.leg.right','body.leg.left','body.arm.right','body.arm.left',
      'body.torso','head.base','body.hand.right','body.hand.left']
TOP=['outfit.torso','outfit.sleeve.left','outfit.sleeve.right','outfit.hem.front']
LOWER=['outfit.pants.right','outfit.boot.right','outfit.pants.left','outfit.boot.left']
FACE=['face.eyes','face.brows','face.nose','face.mouth']
REPAIRED=['down-left','down-right','up-left','up-right','up']

class Sources:
    def __init__(self,cfg):
        self.cfg=cfg;self.assets={};self.used={};self.images={}
        self.motions={d:json.loads((ROOT/x['motion']).read_text()) for d,x in cfg['directions'].items()}
    def manifest(self,d,role):
        k=d,role
        if k not in self.assets:
            x=self.cfg['directions'][d]
            if role not in x['roles']:return None
            cat=json.loads((ROOT/x['catalog']).read_text())
            p=ROOT/next(a['manifest'] for a in cat['assets'] if a['id']==x['roles'][role])
            self.used[str(p.relative_to(ROOT))]=sha(p)
            self.assets[k]=(json.loads(p.read_text()),p)
        return self.assets[k]
    def layer(self,d,role,clip,frame,slot):
        asset=self.manifest(d,role)
        if asset is None:return Image.new('RGBA',(96,96) if role.startswith('face-') else (256,256))
        data,p=asset
        b=next(b for b in data['bindings'] if (b['direction'],b['clip'],b['frame'])==(d,clip,frame))
        if slot not in b['layers']:return Image.new('RGBA',(96,96) if data['mode']=='head-local' else (256,256))
        p=p.parent/b['layers'][slot]
        if p not in self.images:
            self.used[str(p.relative_to(ROOT))]=sha(p)
            self.images[p]=Image.open(p).convert('RGBA')
        return self.images[p].copy()
    def frame(self,d,clip,n):return next(f for f in self.motions[d]['frames'] if (f['clip'],f['frame'])==(clip,n))

def native_index(clip,n):return n if clip in ['idle','walk'] else (8+n if clip=='walk-start' else 10+n)

def prepare_hems(src):
    """Semantic matte extraction from tool-painted sheets; original body is unused."""
    result={};records=[]
    for d in ['down-left','up-left','up']:
        suffix='coat-original.png' if d=='down-left' else 'coat-clean-original.png'
        p=INTEGRATION/'source'/f'{d}-{suffix}'
        sheet=Image.open(p).convert('RGBA')
        assert sheet.size==(1254,1254)
        sheet=sheet.resize((1024,1024),Image.Resampling.NEAREST)
        for clip,n in [('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]:
            idx=native_index(clip,n);x=idx%4*256;y=idx//4*256
            a=np.array(sheet.crop((x,y,x+256,y+256)));rgb=a[:,:,:3].astype(float);r,g,b=rgb.transpose(2,0,1)
            yy,xx=np.indices((256,256));area=(yy>=156)&(yy<201)&(xx>=95)&(xx<163)&(a[:,:,3]>=128)
            blue=(b-r>10)&(b>g*1.02)&(b>r*1.15)&area
            # Retain connected navy fabric, its gold piping and one-pixel ink edge.
            labels,count=nd.label(blue)
            sizes=np.bincount(labels.ravel());keep=np.where(sizes>=5)[0];keep=keep[keep!=0]
            blue=np.isin(labels,keep)
            gold=(r>g*1.12)&(g>b*1.2)&(r>65)&area&nd.binary_dilation(blue,iterations=2)
            cloth=blue|gold
            ink=(np.max(rgb,axis=2)<65)&area&nd.binary_dilation(cloth,iterations=1)
            matte=cloth|ink
            # Exact source hands remain above fabric, including any far-side hand.
            for side in ['left','right']:
                hand=np.array(src.layer(d,'base',clip,n,'body.hand.'+side))[:,:,3]>8
                matte &= ~hand
            a[~matte]=0;a[matte,3]=255
            hem=Image.fromarray(a)
            # The new fabric overlaps the retained upper torso; no gold edge is cropped.
            torso=np.array(src.layer(d,'wayfarer',clip,n,'outfit.torso'))
            bob=round(src.frame(d,clip,n)['joints']['neck'][1]-src.frame(d,'idle',0)['joints']['neck'][1])
            cut=162+bob
            # Existing matte below the handoff supplies only seam underlap. Its RGB is
            # sampled from the nearest authored navy pixels, never a drawn new silhouette.
            under=(torso[:,:,3]>0)&(yy>=cut)&(yy<175+bob)
            for side in ['left','right']:
                under &= np.array(src.layer(d,'base',clip,n,'body.hand.'+side))[:,:,3]<=8
            distance,nearest=nd.distance_transform_edt(~blue,return_indices=True)
            under &= distance<7
            ha=np.array(hem);missing=under&(ha[:,:,3]==0)
            ha[missing,:3]=a[nearest[0][missing],nearest[1][missing],:3]
            ha[missing,3]=torso[missing,3]
            hem=Image.fromarray(ha)
            result[(d,clip,n)]=hem
            records.append({'direction':d,'clip':clip,'frame':n,'source':str(p.relative_to(ROOT)),
                            'sourceCell':idx,'torsoHandoffY':cut,'hemPixelCount':int((ha[:,:,3]>0).sum())})
    # Reflection changes the viewing geometry, not the physical fixed lighting.
    # Reuse the target direction's existing navy palette for mirrored fabric RGB.
    for left,right in [('down-left','down-right'),('up-left','up-right')]:
        palettes=[]
        for f in src.motions[right]['frames']:
            a=np.array(src.layer(right,'wayfarer',f['clip'],f['frame'],'outfit.torso'))
            r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
            m=(b-r>10)&(b>g*1.02)&(a[:,:,3]>128)
            palettes.extend(a[m,:3].tolist())
        palette=np.unique(np.array(palettes,dtype=np.uint8),axis=0).astype(float)
        for (d,clip,n),hem in list(result.items()):
            if d!=left:continue
            a=np.array(hem.transpose(Image.Transpose.FLIP_LEFT_RIGHT));r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
            m=(b-r>10)&(b>g*1.02)&(a[:,:,3]>0)
            colors=a[m,:3].astype(float)
            a[m,:3]=palette[np.argmin(((colors[:,None]-palette[None])**2).sum(axis=2),axis=1)].astype('uint8')
            for side in ['left','right']:
                a[np.array(src.layer(right,'base',clip,n,'body.hand.'+side))[:,:,3]>8]=0
            result[(right,clip,n)]=Image.fromarray(a)
    write(INTEGRATION/'hem-extraction.json',{'rule':'fixed whole atlas1254->1024 nearest; semantic matte, piping retained; no per-sprite fitting',
                                         'nativeSources':records,'reflections':{'down-right':'down-left','up-right':'up-left'}})
    return result

def export():
    cfg=json.loads((INTEGRATION/'authoring.json').read_text());src=Sources(cfg)
    hems=prepare_hems(src);editable=module('wardrobe_editable','export-wardrobe-part.py').editable
    roles=['base','forester','wayfarer','lower','hair-chestnut','hair-silver','face-blue','face-amber','weapon']
    slots={r:(BODY if r=='base' else TOP if r in ['forester','wayfarer'] else LOWER if r=='lower' else
              ['hair.front'] if r.startswith('hair-') else FACE if r.startswith('face-') else ['weapon.back']) for r in roles}
    assets={}
    for role in roles:
        folder=PARTS/role;folder.mkdir(parents=True,exist_ok=True)
        write(folder/'authoring.json',{'sourceIntegration':str(INTEGRATION.relative_to(ROOT)),'role':role,
              'registration':REG,'cyclicWalkSourceOrder':ORDER,'artApproval':None,
              'method':'source pixels plus fixed parent translation; head local unchanged; new hem/UR weapon overrides in integration provenance'})
        assets[role]={'schemaVersion':'1.0.0','id':'p1-eight-way-'+role+'-v1','version':'1.0.0',
                      'part':'base' if role=='base' else 'hair' if role.startswith('hair-') else 'face' if role.startswith('face-') else 'weapon' if role=='weapon' else 'outfit',
                      'compatibility':src.motions['down']['compatibility'],'mode':'head-local' if role.startswith(('hair-','face-')) else 'pose-map',
                      'slots':slots[role],'directions':list(REG),'clips':['idle','walk','walk-start','walk-stop'],
                      'sourceFiles':['authoring.json'],'bindings':[]}
        if role=='weapon':assets[role]['carryProfile']='back-scabbard'
    motion={'schemaVersion':'1.0.0','rig':'p1-chibi-v1','status':'eight-way-authoring-candidate','artApproval':None,
            'canvas':[256,256],'compatibility':src.motions['down']['compatibility'],'durationMs':120,
            'cycleFrames':list(range(1,9)),'alphaFitOrPerPartResize':False,'frames':[],
            'phaseOrigin':'physical right support contact; phases0..3 right,4..7 left',
            'transitionScope':'specified original idle->start01/02->native walk01 and native walk08->stop01/02->idle only',
            'directionRegistration':'fixed idle-neck translation to128,132; not hip/bounds alignment'}
    records=[];lower_proof=0
    for d,info in cfg['directions'].items():
        info.update(registration=REG[d],walkSourceOrder=ORDER[d],entryPhase=ORDER[d].index(1),exitPhase=ORDER[d].index(8))
        for clip,n in [('idle',0)]+[('walk',i) for i in range(1,9)]+[('walk-start',1),('walk-start',2),('walk-stop',1),('walk-stop',2)]:
            native=ORDER[d][n-1] if clip=='walk' else n
            f=copy.deepcopy(src.frame(d,clip,native));f['frame']=n;f['sourcePose']={'clip':clip,'frame':native}
            dx,dy=REG[d];f['headToCanvas'][4]+=dx;f['headToCanvas'][5]+=dy
            f['joints']={k:[v[0]+dx,v[1]+dy] for k,v in f.get('joints',{}).items()}
            f['soleMarkers']={k:[v[0]+dx,v[1]+dy] for k,v in f.get('soleMarkers',{}).items()}
            for socket in f.get('sockets',{}).values():socket['position']=[socket['position'][0]+dx,socket['position'][1]+dy]
            f['sourceSupportLabel']=f['support'];f['support']=support(f['support'])
            if clip=='walk':assert f['support']==('right' if n<=4 else 'left'),(d,n,f['support'])
            f['directionRegistration']=[dx,dy]
            if 'bodyTranslation' in f:f['bodyTranslation']=[f['bodyTranslation'][0]+dx,f['bodyTranslation'][1]+dy]
            draw=f['drawOrder']
            if 'outfit.hem.front' not in draw:draw.insert(draw.index('outfit.torso')+1,'outfit.hem.front')
            if d in REPAIRED:
                draw.remove('outfit.hem.front');draw.insert(draw.index('outfit.torso'),'outfit.hem.front')
            for slot in FACE:
                if slot not in draw:draw.insert(draw.index('hair.front'),slot)
            if d=='up-right':
                draw.remove('weapon.back');draw.insert(draw.index('head.base'),'weapon.back')
            motion['frames'].append(f)
            for role in roles:
                folder=PARTS/role;parts={};binding={'direction':d,'clip':clip,'frame':n,'layers':{}}
                for slot in slots[role]:
                    source_role='forester' if role=='lower' and d=='down' else role
                    im=src.layer(d,source_role,clip,native,slot)
                    if role=='lower' and d=='down':
                        other=src.layer(d,'wayfarer',clip,native,slot)
                        assert im.tobytes()==other.tobytes(),(d,clip,native,slot,'lower must really be common')
                        lower_proof+=1
                    if role=='wayfarer' and d in REPAIRED:
                        if slot=='outfit.hem.front':im=hems[d,clip,native]
                        elif slot=='outfit.torso':
                            a=np.array(im);bob=round(src.frame(d,clip,native)['joints']['neck'][1]-src.frame(d,'idle',0)['joints']['neck'][1]);a[162+bob:]=0;im=Image.fromarray(a)
                    if role=='weapon' and d=='up-right':
                        old=ROOT/'Art/Parts/P1-v1/upper/wardrobe-v1/back-scabbard';data=json.loads((old/'asset.json').read_text())
                        b=next(b for b in data['bindings'] if (b['direction'],b['clip'],b['frame'])==(d,clip,native));p=old/b['layers'][slot]
                        src.used[str(p.relative_to(ROOT))]=sha(p);src.used[str((old/'asset.json').relative_to(ROOT))]=sha(old/'asset.json')
                        im=Image.open(p).convert('RGBA')
                    if assets[role]['mode']=='pose-map':im=translated(im,REG[d])
                    parts[slot]=im;p=Path('png')/d/clip/f'{n:02}'/(slot+'.png');(folder/p).parent.mkdir(parents=True,exist_ok=True);im.save(folder/p);binding['layers'][slot]=p.as_posix()
                assets[role]['bindings'].append(binding)
                edit=folder/'editable';edit.mkdir(exist_ok=True);name=f'{d}-{clip}-{n:02}';editable(edit,name,parts)
                assets[role]['sourceFiles']+=['editable/'+name+'.ora','editable/'+name+'.svg']
            records.append({'direction':d,'clip':clip,'frame':n,'sourceFrame':native,'registration':REG[d],'support':f['support']})
    for role,data in assets.items():write(PARTS/role/'asset.json',data)
    motion['baseManifestSHA256']=sha(PARTS/'base/asset.json')
    write(INTEGRATION/'catalog.json',{'assets':[{'id':a['id'],'manifest':str((PARTS/r/'asset.json').relative_to(ROOT))} for r,a in assets.items()]})
    write(INTEGRATION/'motion.json',motion)
    write(INTEGRATION/'source/consumed-inputs.json',src.used)
    write(INTEGRATION/'mapping.json',{'poses':records,'downCommonLowerLayerProofs':lower_proof,'singleBodyID':assets['base']['id'],
          'swordOverride':'UR uses original anatomical right-shoulder diagonal13poses, not reflected left shoulder; later in drawOrder before head',
          'registration':REG,'walkSourceOrder':ORDER})
    cfg['status']='eight-way-authoring-candidate';write(INTEGRATION/'authoring.json',cfg)
    print(json.dumps({'packages':len(assets),'poses':len(records),'commonLowerProofs':lower_proof,'consumedFiles':len(src.used)}))

if __name__=='__main__':export()
