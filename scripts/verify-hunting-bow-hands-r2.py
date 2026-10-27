from pathlib import Path
import json,numpy as np
from scipy.ndimage import label,find_objects
R=Path(__file__).resolve().parents[1];p=R/'scripts/review-hunting-bow-hands-r2.py';ns={'__file__':str(p)};exec(compile(p.read_text().split("if '--stills' in sys.argv:")[0],str(p),'exec'),ns)
issues=[]
for clip in ['idle','attack','guard','hit','victory','defeat']:
 for i in range(121):
  im=ns['gear_render'](clip,i/120,'huntingBow');a=np.asarray(im.getchannel('A'))>=64;l,n=label(a,np.ones((3,3)));sizes=np.bincount(l.ravel());islands=[(j,int(size)) for j,size in enumerate(sizes) if j and size<12]
  if islands:
   objects=find_objects(l);bounds=[(objects[j-1][1].start,objects[j-1][0].start,objects[j-1][1].stop,objects[j-1][0].stop,size) for j,size in islands]
   issues.append({'clip':clip,'progress':i/120,'islands':bounds})
result={'samples':726,'alphaThreshold':64,'connectivity':8,'smallComponents':issues,'scope':'Supplementary visible-alpha component scan, not art approval.'}
(ns['D']/'pixel-components.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'samples':726,'issueCount':len(issues),'first':issues[:6]},indent=2))
