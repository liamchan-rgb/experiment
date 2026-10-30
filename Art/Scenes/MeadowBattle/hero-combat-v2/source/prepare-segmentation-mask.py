"""Prepare a transparent inpainting reference from the registered approved art.
Polygons are joint masks only; the approved source files remain unchanged."""
from PIL import Image, ImageDraw
from pathlib import Path
root=Path(__file__).resolve().parents[5]
src=root/'Art/Parts/P1-Battle/right-idle-v3/assembled.png'
out=Path(__file__).resolve().parent
im=Image.open(src).convert('RGBA')
# Shared geometry anchored to P1-Neutral right-idle-r2/registration.json.
regions={
 'arm.near':[(111,138),(117,136),(125,149),(134,156),(143,159),(151,163),(151,169),(141,170),(130,166),(121,161),(115,149)],
 'leg.near':[(127,170),(136,172),(143,180),(149,189),(146,199),(150,208),(151,215),(139,216),(134,207),(135,198),(136,190),(129,184)],
 'leg.far':[(111,172),(120,173),(119,183),(113,191),(106,197),(103,207),(103,215),(91,216),(92,205),(97,195),(103,186)]
}
mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask)
for points in regions.values(): d.polygon(points,fill=255)
# Save mask as a separate geometry artifact; create a transparent-hole reference
# for imagegen to reconstruct only concealed body/outfit pixels underneath joints.
mask.save(out/'joint-masks.png')
im.putalpha(Image.eval(mask,lambda a:255-a).point(lambda a: a))
im.save(out/'registered-underlay-holes.png')
(out/'joint-regions.json').write_text(__import__('json').dumps(regions,indent=2)+'\n')
