#!/usr/bin/env python3
"""Offline UI illustration using actual camp projections/layout and existing atlas cells.
Not UIKit, App, simulator or device capture. Does not edit game images.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
R=Path(__file__).resolve().parents[1];D=R/'Art/Review/Equipment/camp-inventory-v1';D.mkdir(parents=True,exist_ok=True)
A=R/'Sources/Resources/Assets.xcassets';gait=json.loads((R/'Sources/Resources/hero-gait.json').read_text())
rows=json.loads((D/'inventory-frames.json').read_text())
C={'bg':'#0b160f','panel':'#192b21','card':'#293e2d','gold':'#eac668','ink':'#f9edc4','muted':'#bbcba9','border':'#777346'}
FONT='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
def font(n):return ImageFont.truetype(FONT,round(n),index=2)
def image(name):return Image.open(A/(name+'.imageset')/(name+'.png')).convert('RGBA')
def icon(id):
 v=gait.get('equipmentVisuals',{}).get(id) or gait.get('armorVisuals',{}).get(id) or gait.get('accessoryVisuals',{}).get(id)
 name=v['iconAsset'] if v else {'smallPotion':'MeadowPartySmallPotion','largePotion':'MeadowPartyLargePotion','shieldPotion':'MeadowPartyShieldPotion','revivalStone':'MeadowPartyRevivalStone'}.get(id)
 return image(name) if name else None
def hero(row,frame):
 load=next(x for x in gait['modularP1']['loadouts'] if x['id']==row['appearanceID']);e=row['unit']['equipment'];w=e.get('weapon') or 'none';armor=e.get('armor')
 name=load.get('armorAtlasNames',{}).get(armor,{}).get(w,load['weaponAtlasNames'][w])[0]
 atlas=image(name);cell=atlas.height//4;return atlas.crop((frame*cell,0,(frame+1)*cell,cell))
def wrap(text,n,width):
 out=[]
 for paragraph in text.split('\n'):
  line=''
  for ch in paragraph:
   if line and font(n).getlength(line+ch)>width:out.append(line);line=ch
   else:line+=ch
  out.append(line)
 return out
def render(row,device='pad',frame=0):
 size=(1194,834) if device=='pad' else (844,390);layout=row[device];out=Image.new('RGBA',size,C['bg']);draw=ImageDraw.Draw(out)
 def box(rect,fill=C['panel'],outline=C['border'],radius=12):
  x,y,w,h=[rect[k] for k in ('x','y','width','height')];draw.rounded_rectangle((x,y,x+w,y+h),radius,fill=fill,outline=outline,width=1)
 def txt(x,y,text,n=17,color=C['ink'],width=None):
  lines=wrap(text,n,width) if width else text.split('\n')
  for i,line in enumerate(lines):draw.text((round(x),round(y+i*(n+5))),line,font=font(n),fill=color)
  return len(lines)*(n+5)
 def button(x,y,w,h,text,n=18,enabled=True):
  draw.rounded_rectangle((round(x),round(y),round(x+w),round(y+h)),6,fill=C['gold'] if enabled else '#837748')
  tx=x+(w-font(n).getlength(text))/2;txt(tx,y+(h-n-5)/2,text,n,C['panel'])
 for name in ['header','equipment','bag','detail']:box(layout[name])
 r=layout['header'];x,y,w=r['x'],r['y'],r['width'];txt(x+12,y+2,'行囊与装备',25)
 txt(x+12,y+31,'P1 · 营地 · 已保存',15);button(x+w-118,y+9,108,38,'返回林地');button(x+w-184,y+9,60,38,'导出');button(x+w-250,y+9,60,38,'导入')
 r=layout['equipment'];w,h=round(r['width']),round(r['height']);pane=Image.new('RGBA',(w,round(564+max(0,min(240,max(133,h*.30))-133))+2),C['panel']);pd=ImageDraw.Draw(pane)
 def pt(x,y,text,n=17):pd.text((round(x),round(y)),text,font=font(n),fill=C['ink'])
 hh=min(240,max(133,h*.30));shift=hh-133;im=hero(row,frame);im.thumbnail((w-24,round(hh)),Image.Resampling.NEAREST);pane.alpha_composite(im,(round((w-im.width)/2),9))
 pd.rounded_rectangle((12,147+shift,w-12,183+shift),6,fill=C['gold']);pd.text(((w-font(18).getlength('查看站姿' if frame else '查看步态'))/2,152+shift),'查看站姿' if frame else '查看步态',font=font(18),fill=C['panel'])
 titles=[x['title'] for x in gait['modularP1']['loadouts']]
 for i,title in enumerate(titles):
  xx=12+i*(w-24)/2;pd.rounded_rectangle((xx,191+shift,xx+(w-24)/2,223+shift),4,fill='#675931' if gait['modularP1']['loadouts'][i]['id']==row['appearanceID'] else '#203529');pt(xx+8,195+shift,title,16)
 u=row['unit'];stats=row['stats'];pt(12,232+shift,f'生命 {u["health"]}/{stats["maximumHealth"]}')
 pd.rectangle((12,259+shift,w-12,275+shift),fill='#07110b');pd.rectangle((13,260+shift,13+(w-26)*u['health']/stats['maximumHealth'],274+shift),fill='#45d27b')
 pt(12,282+shift,'行动')
 side=min(18,(w-24)/8);gap=min(9,max(0,((w-24)-side*8)/8))
 for j in range(8):
  cx=12+side/2+j*(side+gap);cy=308+shift+side/2;d=side/2;pd.polygon([(cx,cy-d),(cx+d,cy),(cx,cy+d),(cx-d,cy)],fill=C['gold'] if j<u['ap'] else '#303c28',outline=C['gold'])
 pt(12,335+shift,f'额外伤害＋{stats["damage"]} · 金币 {u["coins"]}',16)
 catalog=json.loads((R/'Vendor/ClassroomGameCore/Sources/ClassroomGameCore/Resources/initial-content.json').read_text());names={i['id']:i['name'] for i in catalog['items']}
 for i,(slot,title) in enumerate([('weapon','武器'),('armor','护甲'),('accessory','饰品')]):
  yy=370+shift+i*61;pd.rounded_rectangle((12,yy,w-12,yy+54),5,outline=C['border']);pt(20,yy+2,title,17);pt(20,yy+26,names.get(u['equipment'].get(slot),'空手' if slot=='weapon' else '未装备'),17)
 out.alpha_composite(pane.crop((0,0,w,h)),(round(r['x']),round(r['y'])))
 # Inventory list uses the exact production filtering and quantity projection.
 r=layout['bag'];x,y,w,h=[r[k] for k in ('x','y','width','height')];titles={'all':'全部物品','weapon':'武器','armor':'护甲','accessory':'饰品','supplies':'道具'};button(x+10,y+9,w-20,38,titles[row['filter']])
 draw.polygon([(x+w-37,y+24),(x+w-25,y+24),(x+w-31,y+31)],fill=C['panel'])
 listimg=Image.new('RGBA',(round(w-16),max(1,len(row['entries'])*86)),C['panel']);ld=ImageDraw.Draw(listimg)
 for i,e in enumerate(row['entries']):
  yy=i*86;ld.rounded_rectangle((0,yy,w-17,yy+78),6,fill=C['card'],outline=C['gold'] if e['id']==row['selected'] else C['border'],width=2 if e['id']==row['selected'] else 1)
  im=icon(e['id'])
  if im:im.thumbnail((42,48),Image.Resampling.LANCZOS);listimg.alpha_composite(im,(round(8+(42-im.width)/2),round(yy+15+(48-im.height)/2)))
  for j,line in enumerate(wrap(e['name'],18,w-80)[:2]):ld.text((58,yy+7+j*23),line,font=font(18),fill=C['ink'])
  ld.text((58,yy+51),f'背包 ×{e["quantity"]}'+(' · 已装备' if e['equipped'] else ''),font=font(15),fill=C['ink'])
 out.alpha_composite(listimg.crop((0,0,round(w-16),round(h-63))),(round(x+8),round(y+55)))
 if len(row['entries'])*86>h-63:draw.rounded_rectangle((x+w-6,y+65,x+w-3,y+min(h-15,145)),2,fill=C['muted'])
 r=layout['detail'];x,y,w,h=[r[k] for k in ('x','y','width','height')];d=row['detail'];content=Image.new('RGBA',(round(w),1000),C['panel']);cd=ImageDraw.Draw(content);yy=12
 im=icon(d['id'])
 if im:im.thumbnail((68,68),Image.Resampling.LANCZOS);content.alpha_composite(im,(round((w-im.width)/2),yy))
 yy+=78
 def line(text,n=17):
  nonlocal yy
  lines=wrap(text,n,w-24)
  for j,l in enumerate(lines):cd.text((12,yy+j*(n+5)),l,font=font(n),fill=C['ink'])
  yy+=max(24,len(lines)*(n+5))+9
 line(d['name'],22);line(f'背包 ×{d["quantity"]}'+(' · 当前装备' if d['equipped'] else ''),16);line(d['summary'],18);line('使用效果' if d['category']=='supplies' else '换装对比',18)
 if d['category']=='supplies':
  cd.rounded_rectangle((12,yy,w-12,yy+36),4,fill='#293e2d');cd.text((25,yy+5),'P1                P2',font=font(16),fill=C['ink']);yy+=46
 for value in d['comparison']:line(value,16)
 if d['reason']:line(d['reason'],16)
 cd.rounded_rectangle((12,yy,w-12,yy+44),6,fill=C['gold']);cd.text(((w-font(18).getlength('立即保存'))/2,yy+8),'立即保存',font=font(18),fill=C['panel'])
 out.alpha_composite(content.crop((0,0,round(w),round(h-66))),(round(x),round(y)))
 button(x+12,y+h-54,w-24,44,d['actionTitle'],enabled=d['enabled'])
 if yy+54>h-66:draw.rounded_rectangle((x+w-6,y+12,x+w-3,y+min(h-76,90)),2,fill=C['muted'])
 r=layout['footer'];txt(r['x'],r['y'],'林地演练使用独立补给，不扣除营地背包。',15)
 # Separate annotation outside the actual device viewport.
 final=Image.new('RGB',(size[0],size[1]+28),C['bg']);final.paste(out.convert('RGB'),(0,0));fd=ImageDraw.Draw(final);fd.text((12,size[1]+3),'Build65 · 离线布局／原资源合成 · 非UIKit／实机录屏',font=font(15),fill=C['muted']);return final
for row in rows:
 for device in ['pad','phone']:render(row,device).save(D/(row['id']+'-'+device+'.png'))
main=next(r for r in rows if r['id']=='ring');frames=[render(main,'pad',i) for i in range(1,9)];palette=Image.new('RGB',(frames[0].width*4,frames[0].height*2))
for i,f in enumerate(frames):palette.paste(f,(i%4*f.width,i//4*f.height))
p=palette.quantize(colors=256);encoded=[f.quantize(palette=p,dither=Image.Dither.NONE) for f in frames];encoded[0].save(D/'inventory-normal.gif',save_all=True,append_images=encoded[1:],duration=120,loop=0,disposal=2,optimize=False)
render(main).save(D/'inventory-standing.png')
# Save all actual decoded normal-speed frames in full-page 1x screenshots.
gif=Image.open(D/'inventory-normal.gif');assert gif.n_frames==8
for i in range(gif.n_frames):gif.seek(i);assert gif.info['duration']==120;gif.convert('RGB').save(D/f'inventory-decoded-{i:02}.png')
native=[hero(main,i) for i in range(1,9)]
bounds=[im.getbbox() for im in native];union=(min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds))
crops=[im.crop(union) for im in native];cw,ch=crops[0].size;board=Image.new('RGB',(4*(cw*3+18),2*(ch*2+40)),C['bg'])
for i,im in enumerate(crops):
 xx=(i%4)*(cw*3+18);yy=(i//4)*(ch*2+40);board.paste(im,(xx,yy),im);bigger=im.resize((cw*2,ch*2),Image.Resampling.NEAREST);board.paste(bigger,(xx+cw+4,yy),bigger)
board.save(D/'native-eight-frames-1x2x.png')
report={'scope':'Offline UI illustration using actual production camp projection/layout and unchanged native atlas cells. Not UIKit/App/device.','normalFrames':8,'frameMs':120,'durationMs':960,'states':len(rows),'padAndPhoneStandingPNGs':len(rows)*2,'characterArtChanged':False,'userUIApproval':None}
(D/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
