"""Render whole-character review GIFs from the registered production layers.
This is a deterministic pose-preview renderer; it does not edit source artwork."""
from pathlib import Path
from PIL import Image
import math

ROOT = Path(__file__).resolve().parents[4]
ASSETS = ROOT / 'Sources/Resources/Assets.xcassets'
OUT = Path(__file__).resolve().parent
NAMES = ['MeadowBattleHeroWeapon','MeadowBattleHeroBody','MeadowBattleHeroWardrobe','MeadowBattleHeroHair','MeadowBattleHeroFace','MeadowBattleHeroNearHand','MeadowBattleHeroFarHand']
LAYERS = {n: Image.open(ASSETS / f'{n}.imageset/{n}.png').convert('RGBA') for n in NAMES}

def lerp(a,b,t): return a+(b-a)*t
def mixpoint(a,b,t): return (lerp(a[0],b[0],t),lerp(a[1],b[1],t))
# (progress, rootXY, lean, crouch, sword, hand, head, guard, flash, recoil)
KEYS = {
'idle':[(0,(0,0),0,0,0,0,0,0,0,0),(.5,(0,0),-.012,-1,-.025,-.01,.008,0,0,0),(1,(0,0),0,0,0,0,0,0,0,0)],
'attack':[(0,(0,0),0,0,0,0,0,0,0,0),(.14,(-3,0),-.10,4,-.56,-.20,-.04,0,0,0),(.28,(1,0),-.16,6,-.75,-.30,-.06,0,0,0),(.45,(9,-2),.15,1,.30,.16,.06,0,.25,0),(.54,(11,-2),.22,0,.82,.25,.08,0,1,0),(.62,(11,-2),.15,1,.72,.22,.05,0,.55,0),(.82,(4,0),.04,1,.25,.08,.02,0,0,0),(1,(0,0),0,0,0,0,0,0,0,0)],
'guard':[(0,(0,0),0,0,0,0,0,0,0,0),(.24,(-1,1),-.04,3,-.65,-.22,-.025,1,0,0),(.76,(-1,1),-.04,3,-.65,-.22,-.025,1,0,0),(1,(0,0),0,0,0,0,0,0,0,0)],
'hit':[(0,(0,0),0,0,0,0,0,0,0,0),(.18,(-6,1),-.24,5,-.34,-.16,-.10,0,1,1),(.34,(-4,0),-.16,3,-.22,-.10,-.07,0,.55,.65),(.68,(-2,0),-.06,1,-.08,-.04,-.025,0,0,.2),(1,(0,0),0,0,0,0,0,0,0,0)],
'victory':[(0,(0,0),0,0,0,0,0,0,0,0),(.25,(0,0),-.04,1,-.45,-.12,-.02,0,0,0),(.62,(1,-2),.02,-1,-1.24,-.42,.02,0,.2,0),(1,(1,-2),.02,-1,-1.12,-.38,.02,0,0,0)],
'defeat':[(0,(0,0),0,0,0,0,0,0,0,0),(.25,(-3,1),-.12,4,.35,.12,-.05,0,.4,.5),(.7,(-5,5),-.34,9,.52,.16,-.12,0,0,.2),(1,(-5,5),-.34,9,.52,.16,-.12,0,0,.2)]}

def sample(name,p):
    seq=KEYS[name]; i=next((j for j,k in enumerate(seq) if k[0]>=p),len(seq)-1); a,b=seq[max(0,i-1)],seq[i]; f=0 if b[0]==a[0] else (p-a[0])/(b[0]-a[0])
    vals=[lerp(a[j],b[j],f) for j in range(2,10)]; root=mixpoint(a[1],b[1],f)
    lean,crouch,sword,hand,head,ward,flash,recoil=vals
    rootx,rooty=root
    trans={
      'MeadowBattleHeroBody':((0,crouch),(132,167),lean), 'MeadowBattleHeroWardrobe':((0,crouch),(132,167),lean),
      'MeadowBattleHeroHair':((0,crouch),(132,167),lean),'MeadowBattleHeroFace':((0,crouch),(132,167),lean),
      'MeadowBattleHeroNearHand':((-ward*2,crouch*.5),(146,164),hand+ward*.1),
      'MeadowBattleHeroFarHand':((-ward,crouch*.5),(104,171),-ward*.12),
      'MeadowBattleHeroWeapon':((rootx*.35,rooty+crouch*.15),(143,159),sword+hand)}
    out=Image.new('RGBA',(256,256),(0,0,0,0))
    for n in NAMES:
      layer=LAYERS[n]; off,pivot,angle=trans[n]
      layer=layer.rotate(-math.degrees(angle),resample=Image.Resampling.NEAREST,center=pivot)
      # The host scene applies rootOffset to the actor and matching shadow.
      root_shift=(round(rootx),round(rooty))
      shifted=Image.new('RGBA',(256,256),(0,0,0,0)); shifted.alpha_composite(layer,(round(off[0])+root_shift[0],round(off[1])+root_shift[1]))
      out.alpha_composite(shifted)
    return out

# Gameplay speed: 120 ms per frame. Attack is sampled over 1.2 s with readable
# contact hold; idle loops one second; short reactive clips loop twice in review.
for clip, duration in [('idle',1200),('attack',1200),('guard',960),('hit',960),('victory',1200),('defeat',1200)]:
    count=round(duration/120); frames=[]
    for i in range(count):
      p=(i/count) if clip in ('idle','guard') else min(1,i/(count-1))
      canvas=Image.new('RGBA',(320,320),(242,237,218,255))
      pose=sample(clip,p).resize((256,256),Image.Resampling.NEAREST)
      canvas.alpha_composite(pose,(32,32)); frames.append(canvas)
    frames[0].save(OUT/f'{clip}.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,disposal=2,optimize=False)
print('Rendered six full-character GIFs at 120 ms/frame from the registered layer sources.')
