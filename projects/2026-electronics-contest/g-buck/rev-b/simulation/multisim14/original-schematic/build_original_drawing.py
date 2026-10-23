"""Reconstruct per-component drawing aids from the user's PDF net appendix.

Outputs PDF/SVG and pin tables, not a native Multisim schematic or solver model.
"""
from pathlib import Path
import csv,hashlib,json,re,sys,zipfile
from collections import Counter
import fitz
from reportlab.pdfgen import canvas

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
sys.path.insert(0,str(ROOT.parent))
from draw_circuits import Sheet,W,H

SOURCE=PROJECT/'references/G题同步Buck完整原理图_RevB.pdf'
PAGES=[
 ('01_power','主功率与负载','J1 F1 D1 RS_IN C1 C2 QH QL L1 RS_L C3 C4 RS_OUT R_BL J2 TP1 TP2 TP3 TP4 TP5 TP6 TP7'),
 ('02_driver','IR2104驱动、自举与辅助电源','U1 D_BOOT C_BOOT RG_H RG_L R_GSH R_GSL C5 C6 R_IN_PD R_SD_PD R_PWM J_AUX12 J_AUX5'),
 ('03_sense','电流采样与模拟电源','U2 U3 U4 C_U2 C_U3 C_U4 R_VDDA C_A1 C_A2 C_A3 TP8 TP10'),
 ('04_adc','电压分压、ADC滤波与钳位','R1 R2 R4 R5 R3 R6 R7 R8 R_IL_ADC C7 C8 C9 C10 C_IL_ADC D_ADC1 D_ADC2 D_ADC3 D_ADC4 D_ADC5'),
 ('05_protection','参考电压、LM393与故障汇合','U5 U9 R9 R10A R10B R15A R15B R16 R11 R12 R13 C_REF_POS C_REF_NEG C_REF_OV C_U5 C_U9 TP9'),
 ('06_logic','复位、锁存与驱动使能','U6 U7 U8 R14 C11 C_U6 C_U7 C_U8 R_EN_PD R_ARM_PD D_POR'),
 ('07_control','STM32接口与仿真输入边界','J_CTL'),
]
VALUES={
 'F1':'2A fuse','D1':'SS56','RS_IN':'50mOhm','RS_OUT':'50mOhm','RS_L':'25mOhm',
 'C1':'470uF / 50V','C2':'1uF / 50V','C3':'470uF / 35V','C4':'10uF / 35V',
 'QH':'IRF540NPbF','QL':'IRF540NPbF','L1':'220uH; DCR <= 0.15 Ohm','R_BL':'2.2kOhm',
 'U1':'IR2104PbF','U2':'INA240A1D','U3':'INA181A1DBV','U4':'INA240A1D',
 'U5':'LM393DR','U9':'LM393DR','U6':'SN74HC74DR','U7':'SN74HC08DR','U8':'SN74HC14DR',
 'D_BOOT':'UF4007','C_BOOT':'1uF / 25V','RG_H':'10Ohm','RG_L':'10Ohm',
 'R_GSH':'10kOhm','R_GSL':'10kOhm','C5':'100nF','C6':'10uF / 25V',
 'R_IN_PD':'10kOhm','R_SD_PD':'100kOhm','R_PWM':'100Ohm','R_VDDA':'10Ohm',
 'C_A1':'1uF','C_A2':'100nF','C_A3':'10uF / 25V',
 'R1':'100kOhm / 0.1%','R2':'10kOhm / 0.1%','R4':'10kOhm / 0.1%','R5':'1kOhm / 0.1%',
 'R9':'10kOhm / 0.1%','R10A':'33kOhm / 0.1%','R10B':'1kOhm / 0.1%',
 'R15A':'33kOhm / 0.1%','R15B':'1kOhm / 0.1%','R16':'10kOhm / 0.1%',
 'R11':'23kOhm','R12':'10kOhm','R13':'10kOhm','R14':'10kOhm',
 'C11':'100nF','R_EN_PD':'10kOhm','R_ARM_PD':'10kOhm','D_POR':'BAT54',
 'J1':'INPUT 2P','J2':'OUTPUT 2P','J_AUX12':'AUX12 4P','J_AUX5':'AUX5 4P','J_CTL':'CONTROL 2x8',
}
for ref in ['R3','R6','R7','R8','R_IL_ADC']:VALUES[ref]='1kOhm'
for ref in ['C7','C8','C9','C10','C_IL_ADC']:VALUES[ref]='4.7nF'
for ref in ['C_U'+str(n) for n in range(2,10)]+['C_REF_POS','C_REF_NEG','C_REF_OV']:VALUES[ref]='100nF'
for n in range(1,6):VALUES[f'D_ADC{n}']='BAT54S (dual series)'
for n in range(1,11):VALUES[f'TP{n}']='Test point'
def readable_units(text):
    for old,new in [('mOhm','mΩ'),('kOhm','kΩ'),('Ohm','Ω'),('uF','μF'),('uH','μH')]:text=text.replace(old,new)
    return text
VALUES={k:readable_units(v) for k,v in VALUES.items()}

PIN_NAMES={
 'U1':['VCC','IN','/SD','COM','LO','VS','HO','VB'],
 'U2':['IN-','GND','REF2','NC','OUT','VS','REF1','IN+'],
 'U3':['OUT','GND','IN+','IN-','REF','VS'],
 'U4':['IN-','GND','REF2','NC','OUT','VS','REF1','IN+'],
 'U5':['OUT A','IN- A','IN+ A','GND','IN+ B','IN- B','OUT B','VCC'],
 'U9':['OUT A','IN- A','IN+ A','GND','IN+ B','IN- B','OUT B','VCC'],
 'U6':['/CLR1','D1','CLK1','/PRE1','Q1','/Q1','GND','/Q2','Q2','/PRE2','CLK2','D2','/CLR2','VCC'],
 'U7':['1A','1B','1Y','2A','2B','2Y','GND','3Y','3A','3B','4Y','4A','4B','VCC'],
 'U8':['1A','1Y','2A','2Y','3A','3Y','GND','4Y','4A','5Y','5A','6Y','6A','VCC'],
 'QH':['G','D','S'],'QL':['G','D','S'],'D1':['K','A'],'D_BOOT':['A','K'],
 'D_POR':['A','NC','K'],
}
for n in range(1,6):PIN_NAMES[f'D_ADC{n}']=['A1','K2','K1/A2']
for ref in ['C1','C3','C6','C_A3']:PIN_NAMES[ref]=['+','-']
NC={'U2.4','U4.4','U9.7','U6.6','U6.8','U6.9','U7.6','U7.8','U7.11','U8.6','U8.8','U8.10','U8.12','D_POR.2'}


def extract():
    doc=fitz.open(SOURCE);nets={};pin_nets={};current=None
    for page in doc[8:10]:
        text=page.get_text().split('全部连接端点\n',1)[1].split('器件依据：',1)[0]
        for line in text.splitlines():
            line=line.strip()
            if not line:continue
            if re.fullmatch(r'[+A-Z][A-Z0-9_+]*',line):
                current=line;assert current not in nets;nets[current]=[]
            else:
                assert current
                for pin in re.split('[，,]',line):
                    pin=pin.strip()
                    if not pin:continue
                    assert re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*\.\d+',pin),pin
                    assert pin not in pin_nets,pin
                    nets[current].append(pin);pin_nets[pin]=current
    assert not (NC & set(pin_nets))
    for pin in NC:pin_nets[pin]='NC'
    refs={p.split('.')[0] for p in pin_nets}
    assert refs==set(VALUES) and len(refs)==96
    covered=[r for _,_,members in PAGES for r in members.split()]
    assert len(covered)==96 and set(covered)==refs
    for ref in refs:
        count=len(PIN_NAMES[ref]) if ref in PIN_NAMES else (16 if ref=='J_CTL' else 4 if ref.startswith('J_AUX') else 1 if ref.startswith('TP') else 2)
        assert {p for p in pin_nets if p.startswith(ref+'.')}=={f'{ref}.{n}' for n in range(1,count+1)},ref
    return nets,pin_nets


class Drawing(Sheet):
    def text(self,x,y,s,size=15,color='#19384c'):
        super().text(x,y,readable_units(s),size,color)
    def __init__(self,pdf,name,title,pins):
        self.pdf,self.name,self.svg,self.pins,self.seen=pdf,name,[],pins,[]
        self.text(40,952,title,25)
        self.text(40,915,'原图逐元件重绘参考 | 位号、数值、网络来自Rev B PDF | 未生成或验证原生.ms14文件',16)
    def mark(self,ref,n,x,y,display=True):
        pin=f'{ref}.{n}';net=self.pins[pin];self.seen.append(pin)
        self.dot(x,y)
        if display:self.text(x+5,y+9,f'{n}: {net}',12)
        return net
    def tag(self,x,y,net):
        self.dot(x,y);self.text(x+5,y+10,net,13,color='#15678c')
    def note(self,y,text):self.text(45,y,text,15)
    def finish(self):
        self.note(40,'同名网络需用真实导线/连接器相连，文字标注本身不是连线。GND接全局地0；NC悬空。日期：2026-10-23')
        (ROOT/'diagrams'/f'{self.name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>'+''.join(self.svg)+'</svg>',encoding='utf-8')
        self.pdf.showPage()
    def two(self,ref,x,y,length=100,vertical=False,annotate=True):
        # Start = physical pin 1 except D1, whose original pin 2 is the anode.
        a,b=(2,1) if ref=='D1' else (1,2)
        value=VALUES[ref];label=ref+' '+value if annotate else ''
        if ref.startswith('C'):
            if vertical:
                self.cap(x,y,length,ref if annotate else '')
                if annotate:self.text(x-22,y-length-52,value,11)
                if ref in ['C1','C3','C6','C_A3']:self.text(x-28,y-length/2+15,'+',13)
            else:
                self.line(x,y,x+length/2-5,y);self.line(x+length/2-5,y-16,x+length/2-5,y+16)
                self.line(x+length/2+5,y-16,x+length/2+5,y+16);self.line(x+length/2+5,y,x+length,y)
                if ref in ['C1','C3','C6','C_A3']:self.text(x+length/2-25,y+20,'+',13)
                if annotate:self.text(x,y+28,label,13)
        elif ref=='L1':self.inductor(x,y,length,ref+' 220uH' if annotate else '')
        elif ref.startswith('D'):self.diode(x,y,length,label)
        else:self.resistor(x,y,length,label,vertical)
        end=(x,y-length) if vertical else (x+length,y)
        self.mark(ref,a,x,y,False);self.mark(ref,b,*end,False)
    def mos(self,ref,x,y):
        self.line(x,y+65,x,y+30);self.line(x,y+30,x-12,y+30)
        self.line(x-12,y-30,x-12,y+30);self.line(x-12,y-30,x,y-30);self.line(x,y-30,x,y-65)
        self.line(x-35,y-30,x-35,y+30);self.line(x-90,y,x-35,y)
        self.text(x+35,y+10,ref+' IRF540N',15)
        self.text(x+35,y-17,'G1 / D2 / S3',13)
        self.mark(ref,1,x-90,y);self.mark(ref,2,x,y+65);self.mark(ref,3,x,y-65)
    def point(self,ref,x,y):
        self.line(x,y,x+35,y);self.mark(ref,1,x,y,False)
        self.text(x,y+22,ref+' = '+self.pins[ref+'.1'],13)
    def card(self,ref,x,top):
        self.text(x+8,top,ref+'  '+VALUES[ref],15)
        if ref.startswith('TP'):
            self.point(ref,x+35,top-50);return
        pins=sorted((int(p.split('.')[1]),net) for p,net in self.pins.items() if p.startswith(ref+'.'))
        if ref.startswith('U') or ref.startswith('J'):
            half=(len(pins)+1)//2;spacing=29 if len(pins)>8 else 33
            y0=top-52;bottom=y0-(half-1)*spacing-22
            self.box(x+165,bottom,175,y0-bottom+22,'')
            for n,net in pins:
                left=n<=half;i=n-1 if left else len(pins)-n;y=y0-i*spacing
                name=PIN_NAMES.get(ref,[])[n-1] if ref in PIN_NAMES else ''
                if left:
                    self.line(x+148,y,x+165,y);self.text(x+173,y-4,f'{n} {name}'.strip(),12)
                    self.mark(ref,n,x+148,y,False);self.text(x+5,y-4,net,12,color='#15678c')
                else:
                    self.line(x+340,y,x+356,y);self.text(x+255,y-4,f'{name} {n}'.strip(),12)
                    self.mark(ref,n,x+356,y,False);self.text(x+365,y-4,net,12,color='#15678c')
            return
        if ref.startswith('D_ADC'):
            y=top-50
            self.diode(x+75,y,105,'');self.line(x+180,y,x+290,y);self.diode(x+290,y,105,'')
            for n,px in [(1,x+75),(3,x+235),(2,x+395)]:
                self.mark(ref,n,px,y,False)
                self.text(px-45,y-30 if n==3 else y+25,f'{n}: {self.pins[ref+"."+str(n)]}',12)
            self.line(x+235,y,x+235,y-18)
            return
        if ref=='D_POR':
            self.diode(x+165,top-65,120,'')
            self.mark(ref,1,x+165,top-65,False);self.mark(ref,3,x+285,top-65,False)
            self.text(x+5,top-70,'1 A: FAULT_N',12);self.text(x+320,top-70,'3 K: POR_OK',12)
            self.mark(ref,2,x+230,top-115,False);self.text(x+185,top-140,'2: NC',12)
            return
        self.two(ref,x+180,top-65,110,annotate=False)
        a,b=(2,1) if ref=='D1' else (1,2)
        self.text(x+5,top-70,f'{a}: '+self.pins[f'{ref}.{a}'],12,color='#15678c')
        self.text(x+325,top-70,f'{b}: '+self.pins[f'{ref}.{b}'],12,color='#15678c')


def power(s):
    s.note(865,'按实物引脚名称G/D/S接线；Multisim符号的显示编号及SPICE端口次序可能与TO-220脚号不同。')
    s.two('F1',100,760,100);s.two('D1',250,760,95);s.two('RS_IN',390,760,110)
    for a,b in [(50,100),(200,250),(345,390),(500,740)]:s.line(a,760,b,760)
    s.tag(50,760,'VIN_EXT');s.tag(220,760,'FUSED');s.tag(350,760,'V_SHUNT_IN');s.tag(530,760,'VIN')
    for ref,x in [('C1',500),('C2',600)]:s.two(ref,x,760,160,True);s.ground(x,600)
    s.mos('QH',740,650);s.line(740,760,740,715);s.line(740,585,740,470)
    s.mos('QL',740,350);s.line(740,470,740,415);s.ground(740,285);s.tag(740,470,'SW')
    s.line(740,470,850,470);s.two('L1',850,470,110);s.line(960,470,1000,470)
    s.tag(975,470,'L_RAW');s.two('RS_L',1000,470,100);s.line(1100,470,1350,470);s.tag(1130,470,'V_CAP')
    for ref,x in [('C3',1160),('C4',1280)]:s.two(ref,x,470,150,True);s.ground(x,320)
    s.two('RS_OUT',1350,470,100);s.line(1450,470,1615,470);s.tag(1470,470,'VOUT')
    s.two('R_BL',1500,470,150,True);s.ground(1500,320)
    s.resistor(1630,470,150,'',True);s.line(1615,470,1630,470);s.ground(1630,320)
    s.text(1495,590,'External RL: 20 / 8 / 5 Ohm',13)
    s.mark('J1',1,50,760,False);s.text(45,795,'J1.1');s.mark('J1',2,90,530);s.ground(90,530)
    s.mark('J2',1,1615,470,False);s.text(1555,525,'J2.1');s.mark('J2',2,1615,230);s.ground(1615,230)
    s.note(245,'F1=2A保险丝；RL为外加测试负载。L1的DCR、C3的ESR需另行设置并记录，不能重复计入。')
    for i in range(1,8):s.point(f'TP{i}',65+230*(i-1),160)
    s.note(90,'QH体二极管A=SW、K=VIN；QL体二极管A=GND、K=SW。选用完整MOS模型时不要再外加重复体二极管。')


NOTES={
 1:['U1.3 /SD低电平关闭两路；高侧VS接SW，C_BOOT接VB与SW。HO经10Ohm到G_H，LO经10Ohm到G_L。',
    'M1/M2实体模块接J_AUX12/J_AUX5；分块仿真可用12V、5V电源替代，须标注其功耗未计入整机。'],
 2:['U2/U4采用INA240A1D的SOIC-8物理引脚；U4 REF1接+3V3_A，REF2接GND，零点为模拟电源的一半。',
    'R_VDDA连接+3V3与+3V3_A，不要用同名电源端口绕过10Ohm滤波电阻。'],
 3:['BAT54S用两个串联肖特基二极管实现时：低侧A=GND、K=ADC；高侧A=ADC、K=+3V3。',
    '五路ADC各有独立1kOhm与4.7nF；比较器从原始IL_BI、VOUT_DIV取样，不接滤波后的ADC节点。'],
 4:['U5/U9为开集电极输出：U5.1、U5.7、U9.1并到FAULT_N，仅经R13上拉+3V3；芯片供电+5V。',
    '标称+3V3_A=3.3V时，VREF_POS=2.55V、VREF_NEG=0.75V、VREF_OV=1.00V。U9.7悬空。'],
 5:['U6 Q1=SAFE_OK；U7第一路实现DRV_EN=SAFE_OK AND MCU_EN。FAULT_N低时异步清零，解除后需新ARM上升沿。',
    'HC系列电源为3.3V；U8两级施密特反相实现POR。未用输入固定到原图指定电平，NC输出悬空。'],
}


def draw(pins):
    (ROOT/'diagrams').mkdir(exist_ok=True)
    pdf=canvas.Canvas(str(ROOT/'原始原理图_Multisim逐元件绘制参考.pdf'),pagesize=(W,H))
    rendered=[]
    for index,(name,title,refs_text) in enumerate(PAGES):
        refs=refs_text.split();s=Drawing(pdf,name,f'{index+1:02d}  {title}',pins)
        if index==0:power(s)
        elif index==6:
            s.card('J_CTL',70,830)
            s.text(650,835,'外部控制板：按原图保留接口；没有固件模型时不能宣称STM32闭环已仿真。',19)
            for i,line in enumerate([
                'J_CTL.2为+5V输入；J_CTL.4为核心板+3V3回送；仿真替代电源不得并接同轨的其他理想源。',
                'PA8 -> PWM_CTL；PB0 -> MCU_EN；PB1 -> ARM；PB10 <- FAULT_N。',
                'PA0..PA4依次接ADC_VIN、ADC_IIN、ADC_VOUT、ADC_IOUT、ADC_IL。',
                'LCD原图：SCK=PA5，MOSI=PA7，CS=PB12，DC=PB13，RST=PB14；VCC=+3V3。',
                '按键：PB5/PB6/PB7/PB8各经10kOhm上拉+3V3，按键按下接GND；位于外部控制板。',
                '分块仿真电源：VIN_EXT=15..25V；+12V_DRV=12V；+5V=5V；+3V3=3.3V；负端均接GND。',
                '仅测功率级时，可断开控制板输出，用PWM源接PWM_CTL、使能源接MCU_EN、脉冲接ARM。',
                '固定占空比只验证驱动及功率级；CV/CC自动切换需要反馈控制模型或实际固件执行。',
                '12V/5V/3.3V理想替代电源不包含模块、MCU、LCD等的真实损耗；不能据此核验整机85%效率。',
                '原图来源：references/G题同步Buck完整原理图_RevB.pdf，第1..7页及第9..10页网络附录。',
                '本图供Multisim手工放置、接线、核对；实际数据库有无IR2104/INA模型仍需在本机确认。',
            ]):s.text(650,780-i*51,line,15)
            s.note(110,'控制板替代信号、理想辅助电源及测试负载均为测试夹具，不计入96个主板器件。')
        else:
            large=[r for r in refs if r.startswith('U') or r.startswith('J')]
            small=[r for r in refs if r not in large]
            for i,ref in enumerate(large):s.card(ref,35+(i%3)*555,840-(i//3)*250)
            start=840-(335 if index==5 else 235) if large else 840
            for i,ref in enumerate(small):s.card(ref,35+(i%3)*555,start-(i//3)*100)
            for i,line in enumerate(NOTES[index]):s.note(112-i*29,line)
        assert set(s.seen)=={p for p in pins if p.split('.')[0] in refs},(name,set(pins)-set(s.seen))
        assert len(s.seen)==len(set(s.seen)),name
        rendered.extend(s.seen);s.finish()
    pdf.save()
    assert len(rendered)==len(pins) and set(rendered)==set(pins)
    return len(rendered)


def write_csv(path,fields,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def candidate(ref):
    if ref in ['QH','QL']:return '搜索IRF540N/IRF540；确认带仿真模型，按G/D/S名称映射'
    if ref.startswith('U'):
        if ref in ['U6','U7','U8']:return '搜索74HC74/74HC08/74HC14对应型号；核对3.3V供电、隐藏电源脚、模拟/数字接口'
        if ref in ['U5','U9']:return '搜索LM393；确认开集电极输出；两个单元共用电源脚'
        return '搜索'+VALUES[ref]+'；若无模型需另行导入可用模型，符号不能替代仿真模型'
    if ref.startswith('D_ADC'):return 'BAT54S；也可拆成两只肖特基，严格按三节点关系接线'
    if ref.startswith('D'):return '按型号搜索带模型二极管；核对A/K，不以符号编号代替物理脚号'
    if ref.startswith('TP'):return '网络标识及探针；不必放实际测试点器件'
    if ref.startswith('J'):return '连接器或连接端标记；仅标识不能替代真实连线'
    if ref=='F1':return '保险丝；若用导线/低阻替代，记录假设且不声称熔断保护已验证'
    return '基础电阻/电容/电感，数值按本表设置；寄生参数另行记录'


def main():
    nets,pins=extract();rendered=draw(pins)
    groups={r:(i+1,title) for i,(_,title,members) in enumerate(PAGES) for r in members.split()}
    rows=[]
    for ref in VALUES:
        page,title=groups[ref]
        rows.append({'reference':ref,'original_value':VALUES[ref],'drawing_page':page,'module':title,'multisim_selection':candidate(ref)})
    write_csv(ROOT/'原图元件与Multisim选择.csv',list(rows[0]),rows)
    rows=[]
    for pin,net in sorted(pins.items(),key=lambda x:(x[0].split('.')[0],int(x[0].split('.')[1]))):
        ref,n=pin.split('.');names=PIN_NAMES.get(ref,[])
        rows.append({'reference':ref,'physical_pin':n,'pin_function':names[int(n)-1] if names else '',
                     'network':net,'drawing_page':groups[ref][0],'source':'PDF pinout + net appendix' if net=='NC' else 'PDF pages 9-10 net appendix'})
    write_csv(ROOT/'逐引脚接线表.csv',list(rows[0]),rows)
    write_csv(ROOT/'逐网络连接表.csv',['network','endpoints'],[{'network':n,'endpoints':' ; '.join(ps)} for n,ps in nets.items()])
    checks={'date':'2026-10-23','source_pdf_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'bom_docx_sha256':hashlib.sha256((PROJECT/'references/G题同步Buck完整物料清单_RevB_变化标注版.docx').read_bytes()).hexdigest(),
            'source_pdf_pages':10,'network_table_source_pages':[9,10],
            'board_component_count':len(VALUES),'board_network_count':len(nets),
            'connected_pin_count':len(pins)-len(NC),'nc_pin_count':len(NC),'drawing_pin_count':rendered,
            'all_96_board_components_covered_once':True,'all_physical_pins_drawn_once':True,
            'all_connected_endpoints_match_pdf_appendix':True,
            'original_sources_modified':False,'native_multisim_file_generated':False,
            'native_multisim_simulation_verified':False,'manufacturer_models_included':False}
    (ROOT/'source_and_drawing_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    archive=PROJECT/'downloads/Multisim14_按原图逐元件绘制资料包.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(ROOT))
        z.write(SOURCE,'references/'+SOURCE.name)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps(checks,indent=2))
    print(archive)


if __name__=='__main__':main()
