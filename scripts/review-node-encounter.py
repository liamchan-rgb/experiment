"""Offline card layout reference from real readouts/PNGs. Never a UIKit capture."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,sys
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Map/encounter-preview-v1';D.mkdir(parents=True,exist_ok=True)
report=json.load(open(sys.argv[1]));previews=report['previews']
fontpath='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
def font(n):return ImageFont.truetype(fontpath,n)
ink='#faedc4';gold='#ebc46b'
def card(value):
 h=min(430,110+109*max(1,len(value['monsters'])));im=Image.new('RGBA',(430,h),'#1a2b21');draw=ImageDraw.Draw(im);draw.rounded_rectangle((0,0,429,h-1),14,outline='#998a56')
 title=('首领预览 · ' if value['boss'] else '怪物预览 · ')+value['title'];draw.text((12,9),title,font=font(19),fill=ink);draw.text((391,8),'×',font=font(21),fill=gold)
 for i,m in enumerate(value['monsters']):
  name=m['templateID'];asset='MeadowMonster'+name[0].upper()+name[1:]+'Motion';folder=R/'Sources/Resources/Assets.xcassets'/(asset+'.imageset')
  sheet=Image.open(next(folder.glob('*.png'))).convert('RGBA');tile=sheet.crop((0,0,384,256));tile=tile.crop(tile.getbbox());tile.thumbnail((82,68),Image.Resampling.NEAREST)
  y=44+i*109;im.alpha_composite(tile,(12+(82-tile.width)//2,y+(100-tile.height)//2))
  draw.text((104,y),m['name'],font=font(17),fill=ink);draw.text((104,y+24),f"生命 {m['health']}/{m['maximumHealth']}",font=font(16),fill=ink)
  draw.rectangle((104,y+47,416,y+53),fill='#0b120e');draw.rectangle((104,y+47,104+int(312*m['health']/max(1,m['maximumHealth'])),y+53),fill='#3ac764')
  draw.text((104,y+60),f"护盾 {m['shield']} · 普攻 {m['attack']} · 行动",font=font(14),fill=ink)
  for k in range(m['baseAP']):
   x=356+k*15;draw.polygon([(x,y+64),(x+5,y+69),(x,y+74),(x-5,y+69)],fill=gold)
  draw.text((104,y+83),'技能：'+('、'.join(m['skills']) or '无'),font=font(14),fill=ink)
 draw.text((12,h-54),f"{len(value['monsters'])}只存活 · 抵达后可开战",font=font(15),fill=ink);draw.text((12,h-33),'也可继续路过此地点',font=font(15),fill=ink)
 draw.rounded_rectangle((296,h-53,418,h-15),7,fill='#847747');draw.text((315,h-46),'开始战斗',font=font(18),fill='#233527')
 return im.convert('RGB')
values=[next(x for x in previews if len(x['monsters'])==3),next(x for x in previews if x['boss'])]
board=Image.new('RGB',(900,490),'#102117');d=ImageDraw.Draw(board);d.text((12,8),'节点预览 · 离线排版参考（非App截图）',font=font(19),fill=gold)
for i,v in enumerate(values):board.paste(card(v),(10+i*450,45))
board.save(D/'preview-cards.png');board.resize((1800,980),Image.Resampling.NEAREST).save(D/'preview-cards-2x.png')
(D/'review.json').write_text(json.dumps({'scope':'offline card reference; UIKit font/layout approximate, not runtime capture','input':Path(sys.argv[1]).name,'threeMonstersAndBoss':True,'sourceMonsterFramesUnchanged':True,'appSimulatorDeviceRun':False},ensure_ascii=False,indent=2)+'\n')
print(D/'preview-cards.png')
