"""Offline mirror of MeadowPostProcess.metal for parameter review (approximation)."""
import sys, numpy as np
from PIL import Image, ImageFilter
S=dict(focus=.5,clear=.22,smallR=.38,largeR=.60,tS=.0025,tL=.0065,th=.58,knee=.22,bS=.020,bL=.050,
       kS=.40,kL=.28,curve=.40,sat=1.10,warm=.030,cool=.022,vig=.34,vin=.45,vout=1.05,
       haze=(214/255,198/255,170/255,.10),shaft=.085,period=260,drift=.16,scol=(1,225/255,170/255),scale=2.0)
def blur(a,sigma):
    r=max(1,int(np.ceil(sigma*3))); k=np.exp(-np.arange(-r,r+1)**2/(2*sigma*sigma)); k/=k.sum()
    pad=np.pad(a,((r,r),(0,0),(0,0)),mode='edge'); a=sum(k[i]*pad[i:i+a.shape[0]] for i in range(2*r+1))
    pad=np.pad(a,((0,0),(r,r),(0,0)),mode='edge'); return sum(k[i]*pad[:,i:i+a.shape[1]] for i in range(2*r+1))
def down(a,f):
    H,W=a.shape[0]//f*f,a.shape[1]//f*f; return a[:H,:W].reshape(H//f,f,W//f,f,3).mean((1,3))
def up(a,W,H):
    out=np.zeros((H,W,3),np.float32)
    for ch in range(3):
        im=Image.fromarray(a[...,ch].astype(np.float32),mode='F').resize((W,H),Image.BILINEAR); out[...,ch]=np.asarray(im)
    return out
def ss(e0,e1,x): t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)
def luma(c): return c[...,0]*.2126+c[...,1]*.7152+c[...,2]*.0722
def run(src,t=0.0,s=S):
    c=np.asarray(Image.open(src).convert('RGB'),dtype=np.float32)/255
    H,W=c.shape[:2]; y,x=np.mgrid[0:H,0:W]; uv=np.stack([(x+.5)/W,(y+.5)/H],-1)
    # blurs on a 1/4 proxy then upsampled, like the GPU chain
    small=lambda a,f,sg: up(blur(down(a,f),sg),W,H)
    tS=small(c,4,s['tS']*H/4); tL=small(c,8,s['tL']*H/8)
    l=luma(c); br=c*ss(s['th'],s['th']+s['knee'],l)[...,None]
    bS=small(br,8,s['bS']*H/8); bL=small(br,16,s['bL']*H/16)
    d=np.abs(uv[...,1]-s['focus']); a1=ss(s['clear'],s['smallR'],d)[...,None]; a2=ss(s['smallR'],s['largeR'],d)[...,None]
    o=c*(1-a1)+tS*a1; o=o*(1-a2)+tL*a2
    g=np.clip(bS*s['kS']+bL*s['kL'],0,1); o=1-(1-o)*(1-g)
    far=(1-ss(0,.48,uv[...,1]))**2; hz=np.array(s['haze'][:3]); o=o+(hz-o)*(s['haze'][3]*far)[...,None]
    wx=x/s['scale']; wy=y/s['scale']; n=np.array([1,.62]); n=n/np.linalg.norm(n)
    sv=(wx*n[0]+wy*n[1])/s['period']; tt=t*s['drift']
    band=(.5+.5*np.sin(2*np.pi*sv+tt))**7+.55*(.5+.5*np.sin(2*np.pi*sv*.43-tt*.6+1.7))**9
    band*=.65+.35*np.sin(sv*1.9+tt*.37+wy*.004)
    o=o+np.array(s['scol'])*(s['shaft']*band*(1-.55*uv[...,1])*(.45+.55*luma(o)))[...,None]
    o=o*(1-s['curve'])+o*o*(3-2*o)*s['curve']; L=luma(o)[...,None]; o=L+(o-L)*s['sat']
    L=luma(o); o=o+(ss(.45,1,L)*s['warm'])[...,None]*np.array([1,.35,-.8])+((1-ss(0,.5,L))*s['cool'])[...,None]*np.array([-.6,-.05,1])
    asp=W/H; q=np.stack([(uv[...,0]-.5)*asp,uv[...,1]-.5],-1); r=np.linalg.norm(q,axis=-1)/np.hypot(.5*asp,.5)
    o=o*(1-s['vig']*ss(s['vin'],s['vout'],r))[...,None]
    return Image.fromarray((np.clip(o,0,1)*255+.5).astype(np.uint8))
if __name__=='__main__':
    src,dst=sys.argv[1],sys.argv[2]; run(src).save(dst)
