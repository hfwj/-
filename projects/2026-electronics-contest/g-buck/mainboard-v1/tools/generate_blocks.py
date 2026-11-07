"""Mainboard A+CC, six functional zones; EasyEDA Std native wires and pins."""
from pathlib import Path
import json,csv,io,uuid,math,html,sys
OUT=Path(sys.argv[1]).resolve()
BASE=Path(sys.argv[2]).resolve()
for f in ['schematic/native','schematic/previews','results/data']:(OUT/f).mkdir(parents=True,exist_ok=True)
old=json.loads((BASE/'results/data/expected_pins.json').read_text())
expected={r:dict(p) for r,p in old['A_Power_Sense'].items() if r!='J3'}
expected.update({('J3' if r=='J2' else r):dict(p) for r,p in old['B_CC_DAC'].items() if r!='J1'})
assert len(expected)==42 and sum(map(len,expected.values()))==123
bom={}
for r in csv.DictReader(io.StringIO((BASE/'schematic/BOM.csv').read_text(encoding='utf-8-sig'))):
 b,ref=r['Board'],r['Reference']
 if b=='A_Power_Sense' and ref!='J3':bom[ref]=r
 if b=='B_CC_DAC' and ref!='J1':bom['J3' if ref=='J2' else ref]=r
W,H=3000,3240
BLUE,RED,GREEN='#173d70','#8b2323','#14803c'
class Drawing:
 def __init__(self):self.shapes=[];self.svg=[];self.ids=0;self.ox=0;self.oy=0;self.positions={};self.zones=[];self.parts={}
 def id(self):self.ids+=1;return 'gge'+str(self.ids)
 def xy(self,x,y):return (x+self.ox,y+self.oy)
 def textshape(self,x,y,t,size=11,mark='L',anchor='start',color=BLUE):return f'T~{mark}~{x}~{y}~0~{color}~Arial~{size}pt~~~~comment~{t}~1~{anchor}~{self.id()}~0~'
 def svgtxt(self,x,y,t,size=11,anchor='start',color=BLUE):self.svg.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{html.escape(str(t))}</text>')
 def text(self,x,y,t,size=11):
  x,y=self.xy(x,y);self.shapes.append(self.textshape(x,y,t,size));self.svgtxt(x,y,t,size)
 def poly(self,points,color=RED,local=None,width=1):
  p=[self.xy(*v) for v in points];s=' '.join(str(q) for v in p for q in v)
  (local if local is not None else self.shapes).append(f'PL~{s}~{color}~{width}~0~none~{self.id()}~0')
  self.svg.append(f'<polyline points="{s}" fill="none" stroke="{color}" stroke-width="{width}"/>')
 def rect(self,x,y,w,h,local=None,color=RED):
  x,y=self.xy(x,y);(local if local is not None else self.shapes).append(f'R~{x}~{y}~~~{w}~{h}~{color}~1~0~none~{self.id()}~0~')
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{color}"/>')
 def wire(self,*points):
  p=[self.xy(*v) for v in points];s=' '.join(str(q) for v in p for q in v)
  self.shapes.append(f'W~{s}~{GREEN}~1~0~none~{self.id()}~0');self.svg.append(f'<polyline points="{s}" fill="none" stroke="{GREEN}" stroke-width="1.5"/>')
 def label(self,x,y,n,anchor='start'):
  x,y=self.xy(x,y);self.shapes.append(f'N~{x}~{y}~0~{BLUE}~{n}~{self.id()}~{anchor}~{x}~{y-5}~Arial~10pt~0');self.svgtxt(x,y-5,n,12,anchor)
 def port(self,x,y,n,to=None):
  if to:self.wire((x,y),to)
  self.label(x,y,n)
 def dot(self,x,y):
  x,y=self.xy(x,y);self.shapes.append(f'J~{x}~{y}~2~{GREEN}~{self.id()}~0');self.svg.append(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{GREEN}"/>')
 def nc(self,x,y):
  x,y=self.xy(x,y);self.shapes.append(f'O~{x}~{y}~{self.id()}~M {x-4} {y-4} L {x+4} {y+4} M {x+4} {y-4} L {x-4} {y+4}~#33aa33~0');self.svg.append(f'<path d="M{x-4},{y-4}L{x+4},{y+4}M{x+4},{y-4}L{x-4},{y+4}" stroke="#33aa33"/>')
 def zone(self,num,title,x,y):
  self.ox,self.oy=x,y;self.zones.append({'number':num,'title':title,'x':x,'y':y,'width':1460,'height':1020})
  self.rect(5,5,1450,1010,color='#6b879c');self.text(30,45,f'{num:02d}  {title}',22)
  self.text(30,75,'同一块主板上的功能区；绿色为实际导线；跨区同名网络相连；NC为不连接。',12)
 def p(self,r,n):
  x,y=self.positions[(r,str(n))];return x-self.ox,y-self.oy
 def pin(self,sh,r,n,name,a,b,visible=True):
  x,y=self.xy(*a);X,Y=self.xy(*b);dx,dy=X-x,Y-y
  rot=180 if dx>0 else 0 if dx<0 else 90 if dy>0 else 270
  if dx>0:nx,ny,anc=X+5,Y+4,'start';px,py,panc=x+8,y-5,'start'
  elif dx<0:nx,ny,anc=X-5,Y+4,'end';px,py,panc=x-8,y-5,'end'
  else:nx,ny,anc=X+5,Y+3,'start';px,py,panc=x+5,y-8,'start'
  sh.append(f'P~show~0~{n}~{x}~{y}~{rot}~{self.id()}~0^^{x}~{y}^^M {x} {y} L {X} {Y}~{RED}^^{int(visible)}~{nx}~{ny}~0~{name}~{anc}~Arial~9pt~{BLUE}^^1~{px}~{py}~0~{n}~{panc}~Arial~8pt~{BLUE}^^0~{X}~{Y}^^0~M {X} {Y} L {X} {Y}')
  self.svg.append(f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Y}" stroke="{RED}"/>');self.svgtxt(px,py,n,10,panc)
  if visible:self.svgtxt(nx,ny,name,11,anc)
  self.positions[r,str(n)]=(x,y)
 def lib(self,r,value,x,y,sh):
  xx,yy=self.xy(x,y);pkg=bom[r].get('Recommended_footprint','')
  cp={'package':'','nameAlias':'Value','name':value,'Manufacturer Part':value if r.startswith('U') else '', 'spicePre':r[0],'Contributor':'G_Mainboard_Grouped','Recommended footprint':pkg,'Status':'DRAFT - no PCB / no assigned footprint'}
  par='`'.join(t for a in cp.items() for t in a)
  sh=[self.textshape(xx,yy-30,r,13,'P'),self.textshape(xx,yy-12,value,11,'N')]+sh
  self.svgtxt(xx,yy-30,r,13);self.svgtxt(xx,yy-12,value,11)
  self.shapes.append(f'LIB~{xx}~{yy}~{par}~~0~{self.id()}~~{uuid.uuid5(uuid.NAMESPACE_URL,"G-mainboard-blocks-v1/"+r).hex}~0~~yes~yes#@$'+'#@$'.join(sh))
  self.parts[r]={'value':value,'zone':self.zones[-1]['number'],'pins':expected[r]}
 def chip(self,r,x,y,w,h,pins):
  sh=[];self.rect(x,y,w,h,sh)
  for n,name,a,b in pins:self.pin(sh,r,n,name,a,b)
  self.lib(r,bom[r]['Part_or_value'],x,y,sh)
  for n,name,a,b in pins:
   if expected[r][str(n)]=='NC':self.nc(*a)
 def passive(self,r,x,y,kind='R',vertical=False):
  sh=[];v=bom[r]['Part_or_value'];a=(x,y-30) if vertical else (x-30,y);b=(x,y+30) if vertical else (x+30,y);i=(x,y-10) if vertical else (x-10,y);j=(x,y+10) if vertical else (x+10,y)
  if r in ['R9','R13','C14']:a,b=b,a;i,j=j,i
  n2=3 if kind=='D' else 2
  self.pin(sh,r,1,'A' if kind=='D' else '1',a,i,False);self.pin(sh,r,n2,'K' if kind=='D' else '2',b,j,False)
  if kind=='C':
   if vertical:
    self.poly([i,(x,y-3)],local=sh);self.poly([(x,y+3),j],local=sh);self.poly([(x-10,y-3),(x+10,y-3)],local=sh);self.poly([(x-10,y+3),(x+10,y+3)],local=sh)
   else:
    self.poly([i,(x-3,y)],local=sh);self.poly([(x+3,y),j],local=sh);self.poly([(x-3,y-10),(x-3,y+10)],local=sh);self.poly([(x+3,y-10),(x+3,y+10)],local=sh)
  elif kind=='L':self.poly([(x-10+k/2,y-7*abs(math.sin(k/2*math.pi/5))) for k in range(41)],local=sh)
  elif kind=='D':
   self.poly([(x-10,y-8),(x-10,y+8),(x+8,y),(x-10,y-8)],local=sh);self.poly([(x+8,y-10),(x+8,y+10)],local=sh);self.poly([(x+8,y),j],local=sh)
   self.pin(sh,r,2,'NC',(x,y+35),(x,y+25),False)
  else:self.rect(x-5 if vertical else x-10,y-10 if vertical else y-5,10 if vertical else 20,20 if vertical else 10,sh)
  self.lib(r,v,x+15 if vertical else x-15,y if vertical else y-15,sh)
  if r=='C1':self.text(x+14,y-13,'+',15)
  if kind=='D':self.nc(x,y+35)
 def connector(self,r,x,y,nets,right=False):
  pins=[]
  for i,n in enumerate(nets):
   a=(x+120,y+35+i*30) if right else (x-20,y+35+i*30);b=(x+100,a[1]) if right else (x,a[1]);pins.append((i+1,str(i+1),a,b))
  self.chip(r,x,y,100,30*len(nets)+30,pins)
D=Drawing();D.text(35,40,'G题：主功率＋CC 合板 / 六个功能区引脚连线图',26);D.text(35,70,'基准 Modular V1.1；42个主板器件；删除两只A/B互连插座；未绑定封装、未做PCB/原生ERC或台架验证。',13)
# 1 Input, input monitor, external connectors
D.zone(1,'输入保护、输入采样与接口',20,100)
D.connector('J1',120,180,['RAW+','GND'],True)
D.passive('F1',400,215);D.passive('RS1',620,215)
D.wire(D.p('J1',1),D.p('F1',1));D.wire(D.p('F1',2),D.p('RS1',1));D.wire(D.p('RS1',2),(1130,215))
D.connector('J4',1150,180,['VIN_SYS','GND'])
D.wire(D.p('J4',1),(1130,215));D.label(900,215,'VIN_SYS')
D.wire(D.p('J1',2),(240,780),(1420,780));D.label(1150,780,'GND')
D.wire(D.p('J4',2),(1420,245),(1420,780))
D.chip('U3',680,430,200,260,[(9,'IN-',(660,470),(680,470)),(10,'IN+',(660,510),(680,510)),(8,'VBUS',(660,550),(680,550)),(1,'A1',(720,710),(720,690)),(2,'A0',(760,710),(760,690)),(7,'GND',(800,710),(800,690)),(6,'VS',(900,470),(880,470)),(5,'SCL',(900,550),(880,550)),(4,'SDA',(900,590),(880,590)),(3,'ALERT',(900,630),(880,630))])
D.wire((720,215),(720,350),(600,350),(600,470),D.p('U3',9));D.dot(720,215)
D.wire((500,215),(500,510),D.p('U3',10));D.dot(500,215);D.label(500,215,'FUSED')
D.wire((300,215),(300,550),D.p('U3',8));D.dot(300,215);D.label(300,215,'RAW+')
for n in [1,2,7]:x,y=D.p('U3',n);D.wire((x,y),(x,780));D.dot(x,780)
D.wire(D.p('U3',6),(1100,470));D.port(1030,420,'+3V3',(1030,470))
D.passive('C9',1100,520,'C',True);D.wire((1100,470),D.p('C9',1));D.wire(D.p('C9',2),(1100,780));D.dot(1100,780)
D.port(970,550,'SCL',D.p('U3',5));D.port(970,590,'SDA',D.p('U3',4))
D.connector('J3',1290,450,list(expected['J3'].values()))
for n,net in expected['J3'].items():x,y=D.p('J3',n);D.wire((x,y),(1240,y));D.label(1240,y,net,'end')
D.text(50,860,'J3接主控显示板（沿用原B板J2脚序）；J4给独立辅源板供电。',13)
D.text(50,890,'RS1两端单独引Kelvin采样线；INA226测量含辅源在内的整机输入电流。',13)
D.text(50,920,'主功率电流只经过J1/J2，不经过J3控制排线。',13)
# 2 Buck
D.zone(2,'同步Buck主功率与输出端',1510,100)
D.chip('U1',600,230,180,220,[(3,'VIN',(580,270),(600,270)),(1,'GND',(650,470),(650,450)),(5,'EN',(580,350),(600,350)),(4,'FB',(580,410),(600,410)),(2,'SW',(800,270),(780,270)),(6,'BOOT',(800,330),(780,330))])
D.port(120,270,'VIN_SYS',(580,270))
for ref,x in [('C1',200),('C2',330),('C3',460)]:
 D.passive(ref,x,360,'C',True);D.wire((x,270),D.p(ref,1));D.wire(D.p(ref,2),(x,550));D.dot(x,270)
D.passive('L1',900,270,'L');D.wire(D.p('U1',2),D.p('L1',1))
D.passive('RS2',1100,270);D.wire(D.p('L1',2),D.p('RS2',1));D.label(960,270,'VREG')
D.connector('J2',1330,235,['OUT+','GND']);D.wire(D.p('RS2',2),D.p('J2',1));D.label(1190,270,'OUT+')
D.wire(D.p('J2',2),(1310,550),(200,550))
D.wire(D.p('U1',1),(650,550));D.dot(650,550);D.label(680,550,'GND')
for ref,x in [('C5',950),('C6',1050)]:
 D.passive(ref,x,400,'C',True);D.wire((x,270),D.p(ref,1));D.wire(D.p(ref,2),(x,550));D.dot(x,270);D.dot(x,550)
D.passive('C4',860,330,'C');D.wire(D.p('U1',6),D.p('C4',1));D.wire(D.p('C4',2),(910,330),(910,290),(840,290),(840,270));D.dot(840,270);D.label(815,270,'SW');D.label(800,330,'BOOT')
D.port(520,350,'EN_A',D.p('U1',5));D.port(520,410,'FB',D.p('U1',4))
D.text(50,690,'C2/C3、U1及地组成最小输入环路；C4紧贴BOOT与SW；FB走线远离SW与L1。',13)
D.text(50,725,'输出电容在RS2前；R1取VREG反馈，负载端电压比VREG低约0.05×Io。',13)
D.text(50,760,'L1：22uH / Isat≥5A；C5+C6须按直流偏压后的有效容量复核。',13)
D.text(50,795,'U1脚序：1 GND / 2 SW / 3 VIN / 4 FB / 5 EN / 6 BOOT。',13)
# 3 feedback
D.zone(3,'恒压反馈、恒流注入与使能',20,1140)
D.passive('R1',650,250,vertical=True);D.port(650,150,'VREG',D.p('R1',1));D.wire(D.p('R1',2),(650,360))
D.passive('R2',650,480,vertical=True);D.wire((650,360),D.p('R2',1));D.wire(D.p('R2',2),(650,650),(1270,650));D.label(900,650,'GND')
D.passive('R3',400,360);D.port(160,360,'VSET_DRV',D.p('R3',1));D.wire(D.p('R3',2),(850,360));D.label(850,360,'FB');D.dot(650,360)
D.passive('D1',330,550,'D');D.passive('R4',480,550);D.port(160,550,'CC_OUT',D.p('D1',1));D.wire(D.p('D1',3),D.p('R4',1));D.label(390,550,'CC_K');D.wire(D.p('R4',2),(580,550),(580,360));D.dot(580,360)
D.passive('R5',1080,260);D.port(900,260,'RUN',D.p('R5',1));D.wire(D.p('R5',2),(1270,260));D.label(1270,260,'EN_A')
D.passive('R6',1130,400,vertical=True);D.wire((1130,260),D.p('R6',1));D.wire(D.p('R6',2),(1130,650));D.dot(1130,260);D.dot(1130,650)
D.text(50,760,'CC_OUT升高时D1导通，向FB注入电流，使主Buck自动降压进入恒流。',13)
D.text(50,795,'R6保证RUN断开时默认关断；这不是DAC有效性硬件联锁。',13)
D.text(50,830,'FB、CC_OUT、VSET_DRV均在同一主板内连接；不得将FB引到主控排线。',13)
D.text(50,865,'D1采用BAT54：1阳极、3阴极、2不接；不能用BAT54A/C/S直接代替。',13)
# 4 Output sense
D.zone(4,'输出电流及输出电压采样',1510,1140)
D.chip('U2',650,220,200,260,[(3,'IN+',(630,260),(650,260)),(4,'IN-',(630,310),(650,310)),(2,'GND',(700,500),(700,480)),(5,'VS',(750,200),(750,220)),(1,'OUT',(870,300),(850,300))])
D.port(300,200,'VREG',(450,200));D.wire((450,200),(450,260),D.p('U2',3))
D.port(300,310,'OUT+',D.p('U2',4));D.port(1200,300,'ISENSE',D.p('U2',1))
D.port(750,150,'+3V3',D.p('U2',5));D.passive('C8',1050,150,'C');D.wire((750,150),D.p('C8',1));D.wire(D.p('C8',2),(1300,150),(1300,850))
D.wire(D.p('U2',2),(700,550),(1300,550));D.dot(1300,550);D.label(900,550,'GND')
D.passive('R7',400,600,vertical=True);D.wire((300,310),(300,570),D.p('R7',1))
D.passive('R8',400,780,vertical=True);D.wire(D.p('R7',2),(400,690),D.p('R8',1));D.wire(D.p('R8',2),(400,850),(1300,850))
D.passive('C7',650,780,'C',True);D.wire((400,690),(1000,690));D.label(1000,690,'VOUT_ADC');D.wire((650,690),D.p('C7',1));D.wire(D.p('C7',2),(650,850));D.dot(650,690);D.dot(650,850);D.dot(400,690)
D.text(50,920,'INA180A1脚号必须保持：1 OUT / 2 GND / 3 IN+ / 4 IN- / 5 VS。',13)
D.text(50,955,'RS2=50mΩ、增益20，标称ISENSE=1V/A；分压标称VOUT_ADC=Uo/11。',13)
# 5 DAC
D.zone(5,'DAC电压/电流设定与电压滤波',20,2180)
D.chip('U4',500,220,250,350,[(1,'VDD',(480,260),(500,260)),(10,'VSS',(550,590),(550,570)),(2,'SCL',(480,340),(500,340)),(3,'SDA',(480,390),(500,390)),(4,'LDAC',(600,590),(600,570)),(5,'RDY/BSY',(480,480),(500,480)),(6,'VOUTA',(770,260),(750,260)),(7,'VOUTB',(770,350),(750,350)),(8,'VOUTC',(770,410),(750,410)),(9,'VOUTD',(770,450),(750,450))])
D.port(180,150,'+3V3',(1000,150));D.wire((400,150),(400,260),D.p('U4',1))
D.passive('C10',260,300,'C',True);D.wire((260,150),D.p('C10',1));D.wire(D.p('C10',2),(260,650),(1200,650));D.label(900,650,'GND')
D.wire(D.p('U4',10),(550,650));D.wire(D.p('U4',4),(600,650));D.dot(550,650);D.dot(600,650)
D.port(420,340,'SCL',D.p('U4',2));D.port(420,390,'SDA',D.p('U4',3))
D.passive('R9',350,490,vertical=True);D.wire((350,150),D.p('R9',2));D.wire(D.p('R9',1),(350,560),(400,560),(400,480),D.p('U4',5));D.label(400,560,'RDY')
D.passive('R10',1000,260);D.wire(D.p('U4',6),D.p('R10',1));D.label(820,260,'DAC_V')
D.passive('C12',1120,400,'C',True);D.wire(D.p('R10',2),(1300,260));D.label(1300,260,'V_FILT');D.wire((1120,260),D.p('C12',1));D.wire(D.p('C12',2),(1120,650));D.dot(1120,260);D.dot(1120,650)
D.port(900,350,'DAC_I',D.p('U4',7))
D.text(50,760,'U4标准7位I2C地址0x60；LDAC接地；SCL/SDA上拉仍放在外部主控板。',13)
D.text(50,795,'A：内参考2.048V/G2，10V起始码1409；B：内参考/G1，0.95A起始码1900。',13)
D.text(50,830,'以上为校准起点；保持RUN低，写入/读回并确认模拟电压后才启动主功率。',13)
D.text(50,865,'不新增7V必须可设置要求；若保留7V，DAC高端与缓冲余量仍须验证。',13)
# 6 CC and voltage buffer; U5 one native component, two functional triangles.
D.zone(6,'CC恒流补偿与设定缓冲',1510,2180)
sh=[]
D.poly([(720,260),(720,440),(940,350),(720,260)],local=sh);D.poly([(720,660),(720,840),(940,750),(720,660)],local=sh)
for n,name,a,b in [(3,'INA+',(680,300),(720,300)),(2,'INA-',(680,400),(720,400)),(1,'OUTA',(960,350),(940,350)),(8,'VDD',(820,230),(820,300)),(4,'VSS',(820,470),(820,400)),(5,'INB+',(680,700),(720,700)),(6,'INB-',(680,800),(720,800)),(7,'OUTB',(960,750),(940,750))]:D.pin(sh,'U5',n,name,a,b)
D.lib('U5','MCP6002-I/SN',720,260,sh);D.text(790,345,'U5A',13);D.text(790,745,'U5B',13)
D.passive('R11',350,300);D.port(100,300,'ISENSE',D.p('R11',1));D.wire(D.p('R11',2),D.p('U5',3));D.label(610,300,'I_FILT')
D.passive('C13',500,210,'C',True);D.wire(D.p('C13',1),(550,180),(550,300));D.port(450,240,'GND',D.p('C13',2));D.dot(550,300)
D.passive('R12',350,400);D.port(100,400,'DAC_I',D.p('R12',1));D.wire(D.p('R12',2),D.p('U5',2));D.label(570,400,'I_ERR')
D.wire(D.p('U5',1),(1350,350));D.label(1350,350,'CC_OUT')
D.passive('R13',1050,500);D.passive('C14',730,500,'C');D.wire((1200,350),(1200,500),D.p('R13',1));D.wire(D.p('R13',2),D.p('C14',1));D.wire(D.p('C14',2),(600,500),(600,400));D.dot(600,400);D.dot(1200,350);D.label(920,500,'COMP')
D.passive('D2',900,600,'D');D.wire((600,500),(600,600),D.p('D2',1));D.wire(D.p('D2',3),(1200,600),(1200,500));D.dot(600,500);D.dot(1200,500)
D.port(820,150,'+3V3',D.p('U5',8));D.passive('C11',1100,180,'C',True);D.wire((820,150),D.p('C11',1));D.port(1250,210,'GND',D.p('C11',2));D.port(820,480,'GND',D.p('U5',4))
D.port(500,700,'V_FILT',D.p('U5',5));D.wire(D.p('U5',7),(1350,750));D.label(1350,750,'VSET_DRV');D.wire((1150,750),(1150,900),(620,900),(620,800),D.p('U5',6));D.dot(1150,750)
D.text(50,945,'U5A/U5B为同一只8脚MCP6002；C14=220nF X7R，选型建议≥25V/0805。',12)
D.text(50,975,'C14两端为I_ERR与COMP，不是负载端；补偿与瞬态1A上限尚未实物验证。',12)
assert D.parts.keys()==expected.keys(),(D.parts.keys()-expected.keys(),expected.keys()-D.parts.keys())
for ref,pins in expected.items():assert set(pins)=={n for r,n in D.positions if r==ref},ref
head={'docType':'1','editorVersion':'6.5.51','newgId':True,'c_para':{'Prefix Start':'1'},'c_spiceCmd':None,'x':'0','y':'0','hasIdFlag':False}
data={'head':head,'canvas':f'CA~{W}~{H}~#FFFFFF~yes~#CCCCCC~5~{W}~{H}~line~5~pixel~5~0~0','shape':D.shapes,'BBox':{'x':0,'y':0,'width':W,'height':H},'colors':{}}
project={'editorVersion':'6.5.51','docType':'5','title':'G题主板：主功率+CC / 六功能区已连线','description':'One physical mainboard. Six schematic zones. No PCB or assigned footprints.','colors':{},'schematics':[{'docType':'1','title':'Mainboard_Functional_Blocks','description':'','dataStr':data}]}
(OUT/'schematic/native/Mainboard_Functional_Blocks.json').write_text(json.dumps(project,ensure_ascii=False,indent=2))
def svg(x,y,w,h):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x} {y} {w} {h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/><g font-family="Noto Sans CJK SC,Arial,sans-serif">'+''.join(D.svg)+'</g></svg>'
(OUT/'schematic/previews/Mainboard_All.svg').write_text(svg(0,0,W,H))
for z in D.zones:(OUT/'schematic/previews'/f'{z["number"]:02d}_Block.svg').write_text(svg(z['x'],z['y'],z['width'],z['height']))
(OUT/'results/data/expected_mainboard_pins.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
(OUT/'results/data/component_blocks.json').write_text(json.dumps(D.parts,ensure_ascii=False,indent=2))
with open(OUT/'results/data/Pin_Net_Table.csv','w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Block','Reference','Part','Pin','Net'])
 for ref,v in D.parts.items():
  for n,net in v['pins'].items():w.writerow([v['zone'],ref,v['value'],n,net])
with open(OUT/'schematic/BOM_mainboard.csv','w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Block','Reference','Value','Footprint_status'])
 for ref,v in D.parts.items():w.writerow([v['zone'],ref,v['value'],'UNBOUND'])
(OUT/'results/data/block_summary.json').write_text(json.dumps({'components':42,'pins':123,'zones':D.zones,'removed_connectors':['old A.J3 to B','old B.J1 to A'],'external_control_connector':'old B.J2 renamed mainboard J3, same 10-pin mapping'},ensure_ascii=False,indent=2))
print('Generated 42 components / 123 pins / six wired functional zones')
