#!/usr/bin/env python3
"""Render every eight-way loadout and export normal-rate offline review artifacts."""
from pathlib import Path
import hashlib,importlib.util,itertools,json
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
I=ROOT/'Art/Integration/P1-modular-eight-way-v1';D=ROOT/'Art/Review/P1/modular-eight-way-v1'
def module(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
    export=module('eight_export','export-eight-way-parts.py');comp=module('eight_comp','compose-character-parts.py');preview=module('eight_preview','export-neutral-direction.py')
    cfg=json.loads((I/'authoring.json').read_text());src=export.Sources(cfg);eng=comp.Compositor(ROOT,I/'catalog.json',I/'motion.json');directions=list(cfg['directions'])
    base='p1-eight-way-base-v1';records=[];images={};checks={'bodyLayerIdentity':0,'downCommonLowerProofs':json.loads((I/'mapping.json').read_text())['downCommonLowerLayerProofs'],'phaseMappings':0,'handContribution':0,'weaponToggleIsolation':0,'adjacentTurnSupportCases':0,'unchangedWholeCompositions':0,'noNewUnderbodyExposure':0}
    artifacts=D/'poses';artifacts.mkdir(parents=True,exist_ok=True)
    def selection(style,hair,face,carry):return ['p1-eight-way-'+x+'-v1' for x in [style,'lower','hair-'+hair,'face-'+face]+(['weapon'] if carry=='back' else [])]
    combos=list(itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber'],['empty','back']))
    mains=[('forester','chestnut','blue','back'),('wayfarer','silver','amber','back')]
    source_frames={}
    # Check the authored body itself, independent of any appearance occlusion.
    for f in eng.motion['frames']:
        d,clip,n=f['direction'],f['clip'],f['frame'];native=f['sourcePose']['frame']
        for slot,im in eng.layers(base,[],d,clip,n):
            expected=export.translated(src.layer(d,'base',clip,native,slot),cfg['directions'][d]['registration'])
            assert im.tobytes()==expected.tobytes(),(d,clip,n,slot,'body changed')
            checks['bodyLayerIdentity']+=1
        if clip=='walk':
            assert f['support']==('right' if n<=4 else 'left');checks['phaseMappings']+=1
    for combo in combos:
        style,hair,face,carry=combo;label='-'.join(combo)
        for f in eng.motion['frames']:
            d,clip,n=f['direction'],f['clip'],f['frame'];im=eng.render(base,selection(*combo),d,clip,n)
            images[(combo,d,clip,n)]=im
            records.append({'loadout':label,'direction':d,'clip':clip,'frame':n,'rgbaSHA256':hashlib.sha256(im.tobytes()).hexdigest()})
            if combo in mains:
                folder=artifacts/label/d;folder.mkdir(parents=True,exist_ok=True);im.save(folder/f'{clip}-{n:02}.png')
            # Compare visible original hands, not a count of alpha components.
            native=f['sourcePose']['frame'];x=cfg['directions'][d]
            if d not in source_frames:source_frames[d]=comp.Compositor(ROOT,ROOT/x['catalog'],ROOT/x['motion'])
            source_engine=source_frames[d]
            roles=x['roles'];sel=[roles[style],roles['hair-'+hair]]+([roles['lower']] if 'lower' in roles else [])+([roles['face-'+face]] if 'face-'+face in roles else [])+([roles['weapon']] if carry=='back' else [])
            old_layers=source_engine.layers(roles['base'],sel,d,clip,native)
            new_layers=eng.layers(base,selection(*combo),d,clip,n)
            original=Image.new('RGBA',(256,256))
            for _,layer in old_layers:original.alpha_composite(layer)
            original=export.translated(original,x['registration'])
            changed=(style=='wayfarer' and d in export.REPAIRED) or (d=='up-right' and carry=='back')
            if not changed:
                assert im.tobytes()==original.tobytes(),(combo,d,clip,n,'unrelated pixels changed')
                checks['unchangedWholeCompositions']+=1
            def contribution(layers,slot):
                at=next(i for i,(s,_) in enumerate(layers) if s==slot)
                alpha=np.array(layers[at][1])[:,:,3]/255.
                for _,upper in layers[at+1:]:alpha*=1-np.array(upper)[:,:,3]/255.
                return alpha
            # Preserve the actual source neck opening: only reject extra visible
            # safety-body contribution, rather than a blanket neck rectangle.
            for slot in ['body.torso','body.leg.left','body.leg.right']:
                old=contribution(old_layers,slot)
                mask=Image.fromarray((old*255).astype('uint8')).convert('RGBA')
                old=np.array(export.translated(mask,x['registration']))[:,:,0]/255.
                new=contribution(new_layers,slot)
                assert not np.any(new>old+.05),(combo,d,clip,n,slot,'new exposed safety-body')
                checks['noNewUnderbodyExposure']+=1
            # Contribution is the opacity left after layers above the hand.
            for hand in ['body.hand.left','body.hand.right']:
                at=next(i for i,(slot,_) in enumerate(old_layers) if slot==hand)
                alpha=np.array(old_layers[at][1])[:,:,3]/255.
                for _,upper in old_layers[at+1:]:alpha*=1-np.array(upper)[:,:,3]/255.
                mask=export.translated(Image.fromarray((alpha*255).astype('uint8')).convert('RGBA'),x['registration'])
                # Convert through L explicitly; translation's RGBA alpha is not contribution.
                m=np.array(mask)[:,:,0]>250
                old=Image.new('RGBA',(256,256))
                for _,layer in old_layers:old.alpha_composite(layer)
                old=export.translated(old,x['registration']);a,b=np.array(im),np.array(old)
                # New right-up weapon is allowed to cover a hand only if its own alpha does.
                if d=='up-right' and carry=='back':
                    weapon=next(layer for slot,layer in eng.layers(base,selection(*combo),d,clip,n) if slot=='weapon.back');m &= np.array(weapon)[:,:,3]==0
                assert np.array_equal(a[m],b[m]),(combo,d,clip,n,hand,'visible hand changed')
                checks['handContribution']+=1
    for style,hair,face in itertools.product(['forester','wayfarer'],['chestnut','silver'],['blue','amber']):
        a=(style,hair,face,'empty');b=(style,hair,face,'back')
        for f in eng.motion['frames']:
            d,clip,n=f['direction'],f['clip'],f['frame'];weapon=next(im for slot,im in eng.layers(base,selection(*b),d,clip,n) if slot=='weapon.back')
            m=np.array(weapon)[:,:,3]==0
            assert np.array_equal(np.array(images[a,d,clip,n])[m],np.array(images[b,d,clip,n])[m]);checks['weaponToggleIsolation']+=1
    # All adjacent directed turns at every phase; origin advances globally rather
    # than resetting to native frame01. Metadata check, not device locomotion test.
    for combo in combos:
        for j,d in enumerate(directions):
            for neighbor in [directions[(j-1)%8],directions[(j+1)%8]]:
                for n in range(1,9):
                    assert eng.frames[d,'walk',n]['support']==eng.frames[neighbor,'walk',n]['support'];checks['adjacentTurnSupportCases']+=1
    def grid(combo,clip,n):
        out=Image.new('RGBA',(1024,512));draw=ImageDraw.Draw(out)
        for j,d in enumerate(directions):
            out.alpha_composite(images[combo,d,clip,n],(j%4*256,j//4*256));draw.text((j%4*256+6,j//4*256+6),d,fill='white')
        return out
    for combo in mains:
        style=combo[0]
        for scale in [1,2]:preview.flatten(grid(combo,'idle',0),scale).save(D/f'{style}-idle-{scale}x.png')
        preview.gif([grid(combo,'walk',n) for n in range(1,9)],D/f'{style}-eight-way-walk-120ms.gif')
        # Native entry/exit paths are maintained despite cyclic global phase origins.
        startstop=[]
        keys=[('idle',0),('walk-start',1),('walk-start',2)]+[('native-walk',n) for n in list(range(1,9))*2]+[('walk-stop',1),('walk-stop',2),('idle',0)]
        for clip,n in keys:
            out=Image.new('RGBA',(1024,512));draw=ImageDraw.Draw(out)
            for j,d in enumerate(directions):
                local='walk' if clip=='native-walk' else clip;frame=cfg['directions'][d]['walkSourceOrder'].index(n)+1 if clip=='native-walk' else n
                out.alpha_composite(images[combo,d,local,frame],(j%4*256,j//4*256));draw.text((j%4*256+6,j//4*256+6),d,fill='white')
            startstop.append(out)
        preview.gif(startstop,D/f'{style}-specified-start-stop-120ms.gif',[480]+[120]*20+[480])
        for d in directions:
            poses=[images[combo,d,f['clip'],f['frame']] for f in eng.motion['frames'] if f['direction']==d]
            out=Image.new('RGBA',(1024,1024));draw=ImageDraw.Draw(out)
            fs=[f for f in eng.motion['frames'] if f['direction']==d]
            for j,(im,f) in enumerate(zip(poses,fs)):
                out.alpha_composite(im,(j%4*256,j//4*256));draw.text((j%4*256+4,j//4*256+4),f"{f['clip']} {f['frame']} / native {f['sourcePose']['frame']}",fill='white')
            for scale in [1,2]:preview.flatten(out,scale).save(D/f'{style}-{d}-all13-{scale}x.png')
    # Two outfits side by side turn CW then CCW without resetting gait phase.
    turn=[];turn_records=[]
    for rotation in [directions,directions[::-1]]:
        for j,d in enumerate(rotation):
            for k in range(4):
                phase=len(turn)%8+1;out=Image.new('RGBA',(512,256));draw=ImageDraw.Draw(out)
                for col,combo in enumerate(mains):out.alpha_composite(images[combo,d,'walk',phase],(col*256,0));draw.text((col*256+5,5),f'{combo[0]} / {d} / phase {phase-1}',fill='white')
                turn_records.append({'direction':d,'phase':phase-1});turn.append(out)
    preview.gif(turn,D/'turn-comparison-120ms.gif')
    # Whole standing cross-combination sheet:16loadouts x8directions.
    for j,combo in enumerate(combos):preview.flatten(grid(combo,'idle',0),2).save(D/f"standing-{'-'.join(combo)}-2x.png")
    write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    write(D/'composition-index.json',records);write(D/'turn-sequence.json',turn_records)
    write(D/'validation.json',{'status':'technical-checks-pass-art-review-pending','artApproval':None,'packages':9,'loadouts':len(combos),'directions':8,'posesPerDirection':13,'actualCompositions':len(records),'checks':checks,'runtimeIntegrated':False,'ipaBuilt':False})
    print(json.dumps({'actualCompositions':len(records),'checks':checks}))
if __name__=='__main__':main()
