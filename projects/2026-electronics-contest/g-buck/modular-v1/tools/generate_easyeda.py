import json,uuid,csv,math,html,zipfile,shutil
from pathlib import Path
from collections import defaultdict
import sys
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()/'generated_easyeda'
for folder in ['standard_json','previews','checks']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
serial=0
def gid():
 global serial;serial+=1;return 'gge'+str(serial)
def uid():return uuid.uuid4().hex
def fmt(n):return str(round(n,3)).rstrip('0').rstrip('.') if isinstance(n,float) else str(n)
def coords(a):return ' '.join(fmt(v) for p in a for v in p)
BLUE='#000080';RED='#880000';GREEN='#008000'
class Sheet:
 def __init__(self,name,title,w,h):
  self.name,self.title,self.w,self.h=name,title,w,h;self.shapes=[];self.svg=[];self.parts={};self.pinpos={};self.expected={};self.notes=[]
  self.text(50,45,title,22)
  self.text(50,75,'G题 / 四块板独立制作 / DRAFT：未经实物验证 / 同名网络相连 / NC 为不连接',12)
 def txtshape(self,x,y,t,size=10,mark='L',anchor='start',color=BLUE):
  return f'T~{mark}~{x}~{y}~0~{color}~Arial~{size}pt~~~~comment~{t}~1~{anchor}~{gid()}~0~'
 def svgtxt(self,x,y,t,size=10,anchor='start',color=BLUE):
  self.svg.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{html.escape(str(t))}</text>')
 def text(self,x,y,t,size=10):self.shapes.append(self.txtshape(x,y,t,size));self.svgtxt(x,y,t,size)
 def section(self,x,y,t):
  self.text(x,y,t,15)
 def poly(self,ps,color=RED,width=1,local=None):
  shape=f'PL~{coords(ps)}~{color}~{width}~0~none~{gid()}~0'
  (local if local is not None else self.shapes).append(shape)
  self.svg.append(f'<polyline points="{coords(ps)}" fill="none" stroke="{color}" stroke-width="{width}"/>')
 def rect(self,x,y,w,h,local=None):
  (local if local is not None else self.shapes).append(f'R~{x}~{y}~~~{w}~{h}~{RED}~1~0~none~{gid()}~0~')
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{RED}"/>')
 def wire(self,*ps):
  self.shapes.append(f'W~{coords(ps)}~{GREEN}~1~0~none~{gid()}~0')
  self.svg.append(f'<polyline points="{coords(ps)}" fill="none" stroke="{GREEN}" stroke-width="1.3"/>')
 def label(self,x,y,net,anchor='start'):
  self.shapes.append(f'N~{x}~{y}~0~{BLUE}~{net}~{gid()}~{anchor}~{x}~{y-4}~Arial~9pt~0')
  self.svgtxt(x,y-4,net,10,anchor)
 def junction(self,x,y):
  self.shapes.append(f'J~{x}~{y}~2~{GREEN}~{gid()}~0');self.svg.append(f'<circle cx="{x}" cy="{y}" r="2" fill="{GREEN}"/>')
 def nc(self,x,y):
  self.shapes.append(f'O~{x}~{y}~{gid()}~M {x-3} {y-3} L {x+3} {y+3} M {x+3} {y-3} L {x-3} {y+3}~#33cc33~0')
  self.svg.append(f'<path d="M{x-3},{y-3}L{x+3},{y+3}M{x+3},{y-3}L{x-3},{y+3}" fill="none" stroke="#33aa33"/>')
 def stub(self,x,y,net,dx=65):
  if net=='NC':self.nc(x,y);return
  X=x+dx;self.wire((x,y),(X,y));self.label(X,y,net,'start' if dx>0 else 'end')
 def pin(self,sh,ref,num,name,x,y,X,Y,show=True):
  dx,dy=X-x,Y-y;rot=180 if dx>0 else 0 if dx<0 else 270 if dy<0 else 90
  if dx>0:nx,ny,anc=X+4,Y+3,'start';px,py,panc=x+8,y-4,'start'
  elif dx<0:nx,ny,anc=X-4,Y+3,'end';px,py,panc=x-8,y-4,'end'
  else:nx,ny,anc=X+4,Y,'start';px,py,panc=x+4,y,'start'
  sh.append(f'P~show~0~{num}~{x}~{y}~{rot}~{gid()}~0^^{x}~{y}^^M {x} {y} L {X} {Y}~{RED}^^{int(show)}~{nx}~{ny}~0~{name}~{anc}~Arial~8pt~{BLUE}^^{int(show)}~{px}~{py}~0~{num}~{panc}~Arial~7pt~{BLUE}^^0~{X}~{Y}^^0~M {X} {Y} L {X} {Y}')
  self.svg.append(f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Y}" stroke="{RED}"/>')
  if show:self.svgtxt(nx,ny,name,9,anc);self.svgtxt(px,py,num,8,panc)
  self.pinpos[(ref,str(num))]=(x,y)
 def lib(self,ref,value,x,y,sh,recommend='',kind='U'):
  cp={'package':'','nameAlias':'Value','name':value,'Manufacturer Part':value if kind=='U' else '', 'spicePre':kind,'Contributor':'Custom_G_Draft','Recommended footprint':recommend,'Status':'DRAFT - footprint unbound'}
  para='`'.join(str(a) for kv in cp.items() for a in kv)
  self.shapes.append(f'LIB~{x}~{y}~{para}~~0~{gid()}~~{uid()}~0~~yes~yes#@$'+'#@$'.join(sh))
  self.parts[ref]={'reference':ref,'value':value,'recommended_footprint':recommend,'footprint_bound':False,'pins':{}}
 def chip(self,ref,value,x,y,w,left,right,recommend='',spacing=25):
  sh=[];h=30+spacing*max(len(left),len(right));self.rect(x,y,w,h,sh)
  sh.extend([self.txtshape(x,y-24,ref,12,'P'),self.txtshape(x,y-8,value,10,'N')]);self.svgtxt(x,y-24,ref,12);self.svgtxt(x,y-8,value,10)
  todo=[]
  for side,arr in [('L',left),('R',right)]:
   for i,(num,name,net) in enumerate(arr):
    yy=y+20+i*spacing;xx=x-20 if side=='L' else x+w+20;X=x if side=='L' else x+w
    self.pin(sh,ref,num,name,xx,yy,X,yy);todo.append((num,net,xx,yy,-65 if side=='L' else 65))
  self.lib(ref,value,x,y,sh,recommend)
  for num,net,xx,yy,dx in todo:
   self.expected[(ref,str(num))]=net;self.parts[ref]['pins'][str(num)]=net;self.stub(xx,yy,net,dx)
  return self.pinpos
 def passive(self,ref,val,x,y,a,b,kind='R',vertical=False,recommend=''):
  sh=[]
  if vertical:p1=(x,y-30);p2=(x,y+30);q1=(x,y-10);q2=(x,y+10)
  else:p1=(x-30,y);p2=(x+30,y);q1=(x-10,y);q2=(x+10,y)
  # Diodes retain the package's actual 1=A, 3=K; NC pad 2 is explicit.
  n2=3 if kind=='D' else 2
  self.pin(sh,ref,1,'A' if kind=='D' else '1',*p1,*q1,False)
  self.pin(sh,ref,n2,'K' if kind=='D' else '2',*p2,*q2,False)
  if kind=='C':
   if vertical:
    self.poly([(x-9,y-3),(x+9,y-3)],local=sh);self.poly([(x-9,y+3),(x+9,y+3)],local=sh);self.poly([q1,(x,y-3)],local=sh);self.poly([(x,y+3),q2],local=sh)
   else:
    self.poly([(x-3,y-9),(x-3,y+9)],local=sh);self.poly([(x+3,y-9),(x+3,y+9)],local=sh);self.poly([q1,(x-3,y)],local=sh);self.poly([(x+3,y),q2],local=sh)
  elif kind=='L':
   pts=[(x-10,y)]+[(x-10+i/2,y-7*abs(math.sin(i/2*math.pi/5))) for i in range(41)]
   self.poly(pts,local=sh)
  elif kind=='K':
   self.poly([(x-10,y),(x+7,y-10)],local=sh);self.poly([(x+10,y),(x+10,y-2)],local=sh)
  elif kind=='D':
   self.poly([(x-10,y-8),(x-10,y+8),(x+8,y),(x-10,y-8)],local=sh);self.poly([(x+8,y-9),(x+8,y+9)],local=sh);self.poly([(x+8,y),(x+10,y)],local=sh)
   self.pin(sh,ref,2,'NC',x,y+35,x,y+25,False)
  else:self.rect(x-5 if vertical else x-10,y-10 if vertical else y-5,10 if vertical else 20,20 if vertical else 10,sh)
  tx,ty=(x+14,y-6) if vertical else (x-20,y-25)
  sh.extend([self.txtshape(tx,ty,ref,10,'P'),self.txtshape(tx,ty+14,val,9,'N')]);self.svgtxt(tx,ty,ref,10);self.svgtxt(tx,ty+14,val,9)
  self.lib(ref,val,x,y,sh,recommend,kind)
  for num,net,pt in [(1,a,p1),(n2,b,p2)]:
   self.expected[(ref,str(num))]=net;self.parts[ref]['pins'][str(num)]=net
   if vertical:
    dy=-30 if num==1 else 30;end=(pt[0],pt[1]+dy);self.wire(pt,end);self.label(*end,net)
   else:self.stub(*pt,net,-55 if num==1 else 55)
  if kind=='D':self.expected[(ref,'2')]='NC';self.parts[ref]['pins']['2']='NC';self.nc(x,y+35)
 def connector(self,ref,value,x,y,nets,recommend=''):
  self.chip(ref,value,x,y,85,[(i+1,str(i+1),net) for i,net in enumerate(nets)],[],recommend,20)
 def save(self):
  data={'head':{'docType':'1','editorVersion':'6.5.51','newgId':True,'c_para':{'Prefix Start':'1'},'c_spiceCmd':None,'x':'0','y':'0','hasIdFlag':False},'canvas':f'CA~{self.w}~{self.h}~#FFFFFF~yes~#CCCCCC~5~{self.w}~{self.h}~line~5~pixel~5~0~0','shape':self.shapes,'BBox':{'x':0,'y':0,'width':self.w,'height':self.h},'colors':{}}
  project={'editorVersion':'6.5.51','docType':'5','title':self.title,'description':'Independent board schematic. DRAFT, no PCB or bound footprints.','colors':{},'schematics':[{'docType':'1','title':self.name,'description':'','dataStr':data}]}
  (ROOT/'standard_json'/f'{self.name}.json').write_text(json.dumps(project,ensure_ascii=False,indent=2))
  (ROOT/'previews'/f'{self.name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/><g font-family="Noto Sans CJK SC,Arial,sans-serif">'+''.join(self.svg)+'</g></svg>')
  return data
BUS=['+3V3','GND','SCL','SDA','VSET_DRV','CC_OUT','ISENSE','VOUT_ADC','RUN','GND']
sheets=[]
# Board A
A=Sheet('A_Power_Sense','A 板：TPS54302 主降压与输入输出采样',1700,1320);sheets.append(A)
A.section(60,120,'主功率：输入 15~25V；标称 10V / 0.98A；整机输入电流包含辅助电源')
A.connector('J1','INPUT 15-25V',170,170,['RAW+','GND'],'TerminalBlock_2P_5.08mm')
A.passive('F1','2A fuse',320,190,'RAW+','FUSED',recommend='Fuse holder - select actual part')
A.passive('RS1','0.05R 1% 1W',480,190,'FUSED','VIN_SYS',recommend='R2512, Kelvin route')
A.wire((350,190),(450,190));A.wire((510,190),(550,190),(550,300),(580,300))
A.chip('U1','TPS54302DDCR',600,280,150,[(3,'VIN','VIN_SYS'),(1,'GND','GND'),(5,'EN','EN_A'),(4,'FB','FB')],[(2,'SW','SW'),(6,'BOOT','BOOT')],'SOT-23-THIN-6 (DDC)',30)
# Output power chain
A.passive('L1','22uH Isat>=5A',920,300,'SW','VREG','L',recommend='Inductor, DCR<=80mR, select exact part')
A.wire((770,300),(890,300))
A.passive('RS2','0.05R 1% 1W',1210,300,'VREG','OUT+',recommend='R2512, Kelvin route')
A.wire((950,300),(1180,300))
A.passive('C4','100nF 16V',840,390,'BOOT','SW','C')
A.passive('C5','22uF 25V X7R',1020,410,'VREG','GND','C',True,'C1210, effective Cout total>=22uF')
A.passive('C6','22uF 25V X7R',1150,410,'VREG','GND','C',True,'C1210, effective Cout total>=22uF')
A.wire((1020,300),(1020,380));A.wire((1150,300),(1150,380));A.junction(1020,300);A.junction(1150,300)
for ref,x,val in [('C1',170,'100uF 50V'),('C2',280,'10uF 50V X7R'),('C3',390,'100nF 50V')]:A.passive(ref,val,x,390,'VIN_SYS','GND','C',True)
A.connector('J2','OUTPUT LOAD',1430,280,['OUT+','GND'],'TerminalBlock_2P_5.08mm')
A.section(60,560,'高侧电流采样：RS1 / RS2 必须分别引出 Kelvin 采样线')
A.chip('U3','INA226AIDGSR',230,610,170,[(10,'IN+','FUSED'),(9,'IN-','VIN_SYS'),(8,'VBUS','RAW+'),(1,'A1','GND'),(2,'A0','GND')],[(6,'VS','+3V3'),(7,'GND','GND'),(5,'SCL','SCL'),(4,'SDA','SDA'),(3,'ALERT','NC')],'VSSOP-10 (DGS)')
A.chip('U2','INA180A1IDBVR',840,610,175,[(3,'IN+','VREG'),(4,'IN-','OUT+'),(2,'GND','GND')],[(5,'VS','+3V3'),(1,'OUT','ISENSE')],'SOT-23-5 DBV, pinout A')
A.connector('J3','TO BOARD B',1450,580,BUS,'2x5 keyed header, assign exact footprint')
A.connector('J4','TO AUX D',1450,880,['VIN_SYS','GND'],'1x2 2.54mm')
A.section(60,850,'局部反馈与设定注入：FB 不通过排线；板间只传 VSET_DRV / CC_OUT')
for args in [
 ('R1','100k 0.1%',260,920,'VREG','FB','R'),('R2','5.49k 0.1%',670,920,'FB','GND','R'),('R3','56k 0.1%',1080,920,'VSET_DRV','FB','R'),
 ('D1','BAT54 (1=A,3=K)',260,1020,'CC_OUT','CC_K','D'),('R4','10k 1%',670,1020,'CC_K','FB','R'),('R5','1k',1080,1020,'RUN','EN_A','R'),
 ('R6','100k',260,1120,'EN_A','GND','R'),('R7','100k 0.1%',670,1120,'OUT+','VOUT_ADC','R'),('R8','10k 0.1%',1080,1120,'VOUT_ADC','GND','R')]:A.passive(*args)
for args in [('C7','10nF',260,1220,'VOUT_ADC','GND'),('C8','100nF',670,1220,'+3V3','GND'),('C9','100nF',1080,1220,'+3V3','GND')]:A.passive(*args,'C')
A.text(1370,1080,'C8 贴 U2.5 / U2.2',10);A.text(1370,1110,'C9 贴 U3.6 / U3.7',10)
A.text(60,1290,'U2 必须使用 INA180A1，禁止直接换 INA180B1。输入上限按本方案限定 25V，主芯片额定上限 28V。',11)
# Board B
B=Sheet('B_CC_DAC','B 板：模拟恒流与数字设定',1700,1320);sheets.append(B)
B.chip('U4','MCP4728-E/UN',250,180,180,[(1,'VDD','+3V3'),(10,'VSS','GND'),(2,'SCL','SCL'),(3,'SDA','SDA'),(4,'LDAC','GND'),(5,'RDY/BSY','RDY')],[(6,'VOUTA','DAC_V'),(7,'VOUTB','DAC_I'),(8,'VOUTC','NC'),(9,'VOUTD','NC')],'MSOP-10')
B.chip('U5','MCP6002-I/SN',920,180,200,[(3,'INA+','I_FILT'),(2,'INA-','I_ERR'),(5,'INB+','V_FILT'),(6,'INB-','VSET_DRV'),(4,'VSS','GND')],[(1,'OUTA','CC_OUT'),(7,'OUTB','VSET_DRV'),(8,'VDD','+3V3')],'SOIC-8')
B.connector('J1','TO BOARD A',1470,180,BUS,'2x5 keyed header')
B.connector('J2','TO BOARD C',1470,600,BUS,'2x5 keyed header')
B.section(60,470,'电压设定缓冲：U5 的 7脚直接反馈至6脚；由 VOUTA 调整恒压值')
for args in [('R10','1k',270,560,'DAC_V','V_FILT','R'),('C12','100nF',700,560,'V_FILT','GND','C'),('R9','100k',1130,560,'RDY','+3V3','R')]:B.passive(*args)
B.section(60,670,'电流环：U5.1 -> R13 -> C14 -> U5.2；D2 阳极接 I_ERR，阴极接 CC_OUT')
for args in [('R11','1k',270,760,'ISENSE','I_FILT','R'),('C13','10nF',700,760,'I_FILT','GND','C'),('R12','100k 1%',1130,760,'DAC_I','I_ERR','R'),('R13','1k 1%',270,880,'CC_OUT','COMP','R'),('C14','1uF X7R',700,880,'COMP','I_ERR','C'),('D2','BAT54 (1=A,3=K)',1130,880,'I_ERR','CC_OUT','D'),('C10','100nF',270,1020,'+3V3','GND','C'),('C11','100nF',700,1020,'+3V3','GND','C')]:B.passive(*args)
B.text(60,1130,'C10 贴 U4 的 1/10脚；C11 贴 U5 的 8/4脚。两只插座逐脚同名连接。',12)
B.text(60,1170,'电流升高 -> CC_OUT 升高 -> A板 D1 导通 -> 降压恒流。C14=1uF 为补偿起始值，必须做负载阶跃验证。',12)
B.text(60,1210,'DAC A 取 VDD 参考，默认约1.4092V；DAC B 取内部2.048V参考 / 增益1，默认0.980V。',12)
B.text(60,1250,'按键设置范围建议：7.0~10.0V / 0.20~0.98A；不含已经编译、验证的 MCU 固件。',12)
# Board C
C=Sheet('C_MCU_LCD','C 板：STM32F103C8T6、PCD8544 液晶和按键',2050,1810);sheets.append(C)
pin_names={1:'VBAT',2:'PC13',3:'PC14',4:'PC15',5:'PD0',6:'PD1',7:'NRST',8:'VSSA',9:'VDDA',10:'PA0',11:'PA1',12:'PA2',13:'PA3',14:'PA4',15:'PA5',16:'PA6',17:'PA7',18:'PB0',19:'PB1',20:'PB2/BOOT1',21:'PB10',22:'PB11',23:'VSS1',24:'VDD1',25:'PB12',26:'PB13',27:'PB14',28:'PB15',29:'PA8',30:'PA9',31:'PA10',32:'PA11',33:'PA12',34:'PA13',35:'VSS2',36:'VDD2',37:'PA14',38:'PA15',39:'PB3',40:'PB4',41:'PB5',42:'PB6',43:'PB7',44:'BOOT0',45:'PB8',46:'PB9',47:'VSS3',48:'VDD3'}
np={1:'+3V3',7:'NRST',8:'GND',9:'+3V3',10:'VOUT_ADC',11:'ISENSE',14:'LCD_CE',15:'LCD_CLK',17:'LCD_DIN',18:'LCD_DC',19:'LCD_RST',20:'BOOT1',23:'GND',24:'+3V3',29:'RUN',30:'KEY_SET',31:'KEY_UP',32:'KEY_DOWN',34:'SWDIO',35:'GND',36:'+3V3',37:'SWCLK',42:'SCL',43:'SDA',44:'BOOT0',47:'GND',48:'+3V3'}
C.chip('U6','STM32F103C8T6',630,180,300,[(i,pin_names[i],np.get(i,'NC')) for i in range(1,25)],[(i,pin_names[i],np.get(i,'NC')) for i in range(25,49)],'LQFP-48 7x7mm pitch0.5mm')
C.connector('JLCD','PCD8544 LCD',1480,180,['LCD_RST','LCD_CE','LCD_DC','LCD_DIN','LCD_CLK','+3V3','NC','GND'],'Module header: verify actual silkscreen order')
C.connector('J1','TO BOARD B',1790,510,BUS,'2x5 keyed header')
C.connector('JP','3V3 FROM D',1480,600,['+3V3','GND'],'1x2 2.54mm')
C.connector('JSWD','SWD DEBUG',1480,760,['+3V3','SWDIO','GND','SWCLK'],'1x4 2.54mm, voltage reference only')
C.section(60,950,'最小系统：内部 8MHz HSI；不装外部晶振；未用脚 NC，软件设为模拟输入')
for args in [('R14','4.7k',270,1040,'SCL','+3V3','R'),('R15','4.7k',750,1040,'SDA','+3V3','R'),('R16','10k',1230,1040,'NRST','+3V3','R'),('C15','100nF',1710,1040,'NRST','GND','C'),('R17','10k',270,1160,'BOOT0','GND','R'),('R18','10k',750,1160,'BOOT1','GND','R')]:C.passive(*args)
C.section(60,1250,'按键：K1 选择设定项，K2 增加，K3 减少；按下接地；软件消抖')
for ref,val,x,y,a,b,kind in [('R19','10k',270,1340,'KEY_SET','+3V3','R'),('R20','10k',750,1340,'KEY_UP','+3V3','R'),('R21','10k',1230,1340,'KEY_DOWN','+3V3','R')]:C.passive(ref,val,x,y,a,b,kind)
for ref,x,net in [('K1',270,'KEY_SET'),('K2',750,'KEY_UP'),('K3',1230,'KEY_DOWN')]:C.passive(ref,'NO momentary',x,1450,net,'GND','K',recommend='2-pin normally-open switch; verify physical contacts')
for i,(ref,x,y,val) in enumerate([('C16',270,1570,'100nF'),('C17',750,1570,'100nF'),('C18',1230,1570,'100nF'),('C19',1710,1570,'100nF'),('C20',270,1680,'4.7uF'),('C21',750,1680,'100nF'),('C22',1230,1680,'1uF')]):C.passive(ref,val,x,y,'+3V3','GND','C')
C.text(60,1760,'C16/C17/C18/C19 分别紧贴 U6.24 / U6.36 / U6.48 / U6.9；C20 主控旁；C21/C22 液晶旁。',12)
C.text(60,1790,'上电保持 RUN=0；初始化与 DAC 写入成功后 RUN=1。LCD 固定显示 Ui/Ii/Uo/Io/SV/SI。SWD 下载器不对板供电。',12)
# D board
D=Sheet('D_Aux_Power','D 板：3.3V 辅助电源（题目允许成品辅源）',1100,740);sheets.append(D)
D.connector('J1','INPUT FROM A.J4',170,210,['VIN_SYS','GND'],'1x2 2.54mm')
D.chip('M1','Aux buck module: 15-25V to 3.3V',530,220,220,[(1,'IN+','VIN_SYS'),(2,'IN-','GND')],[(3,'OUT+','+3V3'),(4,'OUT-','GND')],'Purchased auxiliary module; custom pin mapping only')
D.connector('J2','OUTPUT TO C.JP',920,410,['+3V3','GND'],'1x2 2.54mm')
D.text(60,550,'仅作为 MCU、液晶、采样和 DAC 的辅助供电，禁止代替 A 板主功率电路。',13)
D.text(60,590,'可选 MP1584EN 辅源小板；上机前独立调整到 3.30V，输出额定电流不小于0.3A。',13)
D.text(60,630,'M1 的 1/2/3/4 是本图自定义端口号，实际接模块 IN+/IN-/OUT+/OUT- 丝印。',13)
D.text(60,670,'所有板均由同一输入取电；本方案不接真实电池。',13)
# Files
all_data={s.name:s.save() for s in sheets}
with open(ROOT/'pin_connections.csv','w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['Board','Reference','Part','Pin','Net'])
 for s in sheets:
  for r,p in s.parts.items():
   for n,net in p['pins'].items():w.writerow([s.name,r,p['value'],n,net])
with open(ROOT/'BOM.csv','w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['Board','Reference','Part_or_value','Recommended_footprint','Footprint_bound'])
 for s in sheets:
  for r,p in s.parts.items():w.writerow([s.name,r,p['value'],p['recommended_footprint'],p['footprint_bound']])
(ROOT/'expected_pins.json').write_text(json.dumps({s.name:{r:p['pins'] for r,p in s.parts.items()} for s in sheets},indent=2))
print(json.dumps({s.name:{'components':len(s.parts),'pins':len(s.expected),'shapes':len(s.shapes)} for s in sheets},indent=2))
