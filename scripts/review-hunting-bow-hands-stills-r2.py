from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parents[1];p=R/'scripts/review-hunting-bow-hands-r2.py';ns={'__file__':str(p)};exec(compile(p.read_text().split("if '--stills' in sys.argv:")[0],str(p),'exec'),ns);D=ns['D']
for t,label in [(0,'standing'),(.5,'rolling'),(2.06,'impact'),(2.3,'landed'),(1.8,'held'),(3.2,'retired')]:
 row=min((r for r in ns['rows'] if r['scenario']=='bow'),key=lambda r:abs(r['time']-t));ns['ui'](row,ns['scene'](row)).save(D/('bow-'+label+'.png'))
 if label in ['standing','held']:
  u=next(u for u in row['units'] if u['id']=='p1');sp=ns['gear_render'](u['clip'],u['progress'],'huntingBow');im=Image.new('RGBA',(256,256),'#20372a');im.alpha_composite(sp)
  im.resize((768,768),Image.Resampling.NEAREST).save(D/('pose-a-'+label+'.png'))
report=json.loads((D/'pixel-components.json').read_text());legacy=True
for issue in report['smallComponents']:
 old=ns['namespace']['render'](issue['clip'],issue['progress'])
 for x,y,_,_,size in issue['islands']:
  if old.getpixel((x,y))[3]<64:legacy=False
report['allSmallPixelsAlsoPresentInOriginalLowerBody']=legacy;report['smallPixelMinY']=min(v[1] for x in report['smallComponents'] for v in x['islands']);report['attackAndIdleSmallComponents']=sum(x['clip'] in ['attack','idle'] for x in report['smallComponents']);(D/'pixel-components.json').write_text(json.dumps(report,indent=2)+'\n');print('old lower-body pixel provenance',legacy)
