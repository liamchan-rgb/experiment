#!/usr/bin/env python3
"""Keep editable SVG image layers identical to their final transparent PNGs."""
from pathlib import Path
import base64,sys

def sync_editable_pngs(folder):
 folder=Path(folder);count=0
 for png in (folder/'png').rglob('*.png'):
  direction,clip,frame,name=png.relative_to(folder/'png').parts
  slot=Path(name).stem;editable=folder/'editable'/f'{direction}-{clip}-{frame}-{slot}.svg'
  if not editable.is_file():raise FileNotFoundError(editable)
  data=base64.b64encode(png.read_bytes()).decode('ascii')
  editable.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><g id="'+slot+'"><image width="256" height="256" href="data:image/png;base64,'+data+'"/></g></svg>')
  count+=1
 return count

if __name__=='__main__':
 print(sum(sync_editable_pngs(Path(p)) for p in sys.argv[1:]),'editable images synchronized')
