"""Deterministic wiring sheets (SVG + multipage PDF), not native .ms14 files."""
from pathlib import Path
from math import sin,pi
from html import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'diagrams'
W,H=1700,1000
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

class Sheet:
    def __init__(self,pdf,name,title):
        self.pdf,self.name=pdf,name;self.svg=[]
        self.text(45,950,title,24)
        self.text(45,914,'Rev B PDF reconstruction | Functional equivalents | Not a manufacturer model or native Multisim schematic',14)
    def line(self,x1,y1,x2,y2,color='#19384c',width=2):
        self.svg.append(f'<line x1="{x1}" y1="{H-y1}" x2="{x2}" y2="{H-y2}" stroke="{color}" stroke-width="{width}"/>')
        self.pdf.setStrokeColor(color);self.pdf.setLineWidth(width);self.pdf.line(x1,y1,x2,y2)
    def text(self,x,y,s,size=15,color='#19384c'):
        self.svg.append(f'<text x="{x}" y="{H-y}" font-size="{size}" fill="{color}" font-family="Arial,Noto Sans CJK SC,sans-serif">{escape(s)}</text>')
        self.pdf.setFillColor(color);self.pdf.setFont('STSong-Light',size);self.pdf.drawString(x,y,s)
    def box(self,x,y,w,h,label,sub=''):
        for a,b,c,d in [(x,y,x+w,y),(x+w,y,x+w,y+h),(x+w,y+h,x,y+h),(x,y+h,x,y)]:self.line(a,b,c,d)
        self.text(x+12,y+h-28,label,16)
        if sub:
            for i,t in enumerate(sub.split('\n')):self.text(x+12,y+h-55-22*i,t,13)
    def dot(self,x,y):
        self.svg.append(f'<circle cx="{x}" cy="{H-y}" r="4" fill="#19384c"/>');self.pdf.setFillColor('#19384c');self.pdf.circle(x,y,4,fill=1,stroke=0)
    def ground(self,x,y):
        self.line(x,y,x,y-12)
        for i,w in enumerate([16,10,4]):self.line(x-w,y-12-6*i,x+w,y-12-6*i)
    def source(self,x,y):
        self.svg.append(f'<circle cx="{x}" cy="{H-y}" r="20" fill="white" stroke="#19384c" stroke-width="2"/>')
        self.pdf.setStrokeColor('#19384c');self.pdf.setFillColor('white');self.pdf.circle(x,y,20,fill=1,stroke=1)
        self.text(x+6,y-5,'+',13);self.text(x-15,y-5,'-',13)
        self.line(x-20,y,x-55,y);self.ground(x-55,y)
    def resistor(self,x,y,length,label,vertical=False):
        if vertical:
            self.line(x,y,x,y-12);self.box(x-10,y-length+12,20,length-24,'');self.line(x,y-length+12,x,y-length)
            self.text(x+17,y-length/2,label,13)
        else:
            self.line(x,y,x+12,y);self.box(x+12,y-10,length-24,20,'');self.line(x+length-12,y,x+length,y);self.text(x,y+24,label,13)
    def cap(self,x,y,length,label):
        mid=y-length/2;self.line(x,y,x,mid+5);self.line(x-17,mid+5,x+17,mid+5);self.line(x-17,mid-5,x+17,mid-5);self.line(x,mid-5,x,y-length);self.text(x+22,mid,label,13)
    def diode(self,x,y,length,label):
        self.line(x,y,x+15,y);a=x+15;b=x+length-15
        self.line(a,y-15,a,y+15);self.line(a,y-15,b,y);self.line(a,y+15,b,y);self.line(b,y-16,b,y+16);self.line(b,y,x+length,y);self.text(x,y+30,label,13)
    def inductor(self,x,y,length,label):
        prev=(x,y)
        for i in range(1,101):
            cur=(x+length*i/100,y+15*abs(sin(4*pi*i/100)));self.line(*prev,*cur);prev=cur
        self.text(x,y+32,label,13)
    def finish(self):
        self.text(45,42,'Generated 2026-10-22 | Pin order and model assumptions: ../README.md | COM must be connected to SPICE ground 0',12)
        (OUT/f'{self.name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>'+''.join(self.svg)+'</svg>')
        self.pdf.showPage()

def main():
    OUT.mkdir(exist_ok=True)
    p=canvas.Canvas(str(OUT/'Multisim14_仿真电路接线图.pdf'),pagesize=(W,H))
    s=Sheet(p,'01_power_stage','01  主功率接线 / Main power stage')
    s.text(40,840,'VIN_EXT');s.line(60,760,110,760);s.resistor(110,760,100,'F1 eq 20mΩ');s.line(210,760,240,760);s.diode(240,760,90,'D1 SS56 eq');s.line(330,760,370,760);s.text(340,805,'V_SHUNT_IN')
    s.resistor(370,760,100,'RS_IN 50mΩ');s.line(470,760,700,760);s.text(490,805,'VIN');s.dot(510,760);s.dot(600,760)
    for x,label in [(510,'C1 470uF'),(600,'C2 1uF')]:s.cap(x,760,170,label);s.ground(x,590)
    s.line(700,760,700,675);s.box(650,575,100,100,'QH','44mΩ SW eq\nCds=250pF');s.line(700,575,700,480);s.text(660,705,'IRF540N -> XQH equivalent')
    s.line(590,625,650,625);s.text(550,650,'G_H');s.text(765,625,'Body diode: A=SW, K=VIN',13)
    s.dot(700,480);s.text(710,450,'SW');s.line(700,480,700,390);s.box(650,290,100,100,'QL','44mΩ SW eq\nCds=250pF');s.line(700,290,700,210);s.ground(700,210);s.line(590,340,650,340);s.text(550,365,'G_L');s.text(765,335,'Body diode: A=GND, K=SW',13)
    s.line(700,480,820,480);s.inductor(820,480,100,'L1 220uH');s.line(920,480,940,480);s.resistor(940,480,95,'DCR 150mΩ');s.line(1035,480,1070,480);s.text(1030,525,'L_RAW');s.resistor(1070,480,100,'RS_L 25mΩ');s.line(1170,480,1290,480);s.text(1190,525,'V_CAP');s.dot(1190,480);s.dot(1290,480)
    s.cap(1190,480,130,'C3 470uF');s.resistor(1190,350,90,'ESR 80mΩ',True);s.ground(1190,260)
    s.cap(1290,480,170,'C4 10uF');s.ground(1290,310)
    s.line(1290,480,1340,480);s.resistor(1340,480,100,'RS_OUT 50mΩ');s.line(1440,480,1620,480);s.text(1460,525,'VOUT');s.dot(1470,480);s.dot(1620,480)
    s.resistor(1470,480,170,'R_BL 2.2kΩ',True);s.ground(1470,310);s.resistor(1620,480,170,'RL 20/8/5Ω',True);s.ground(1620,310)
    s.box(75,220,475,200,'模型与原图的差别 / Model substitutions','QH/QL channels = voltage-controlled switches + body diodes\nGate networks and real bootstrap topology: sheet 02\nF1/contact 20mΩ and C3 ESR 80mΩ are assumptions\nC4 has no DC-bias derating in this model\nM1/M2 auxiliary input power equivalent: inside .lib')
    s.text(75,145,'电流采样极性：U2 IN+ = V_SHUNT_IN, IN- = VIN; U3 IN+ = V_CAP, IN- = VOUT',15)
    s.text(75,112,'U4 IN+ = L_RAW, IN- = V_CAP.  25mΩ × gain 20 = 0.5V/A; zero = V3A/2.',15)
    s.finish()
    s=Sheet(p,'02_driver','02  浮动高侧驱动、自举与互锁 / Floating driver and bootstrap')
    s.text(75,825,'这是IR2104功能替代电路，不是厂家IR2104模型。高侧必须相对SW驱动，禁止把高侧栅极只接对地12V。',18)
    s.line(110,740,280,740);s.text(80,775,'+12V_DRV');s.diode(280,740,110,'D_BOOT UF4007 eq');s.line(390,740,790,740);s.text(670,775,'VB');s.dot(790,740)
    s.cap(120,740,60,'C5 100nF');s.ground(120,680)
    s.cap(220,740,60,'C6 10uF');s.ground(220,680)
    s.cap(790,740,240,'C_BOOT 1uF');s.line(790,500,790,420);s.text(805,425,'SW');s.dot(790,420)
    s.line(560,740,560,680);s.box(500,600,120,80,'S_HUP','Ron = 50Ω');s.line(560,600,560,550);s.dot(560,550);s.text(525,565,'HO');s.line(560,550,920,550);s.resistor(920,550,110,'RG_H 10Ω');s.line(1030,550,1230,550);s.text(1080,590,'G_H -> QH gate')
    s.line(560,550,560,500);s.box(500,420,120,80,'S_HDN','Ron = 25Ω');s.line(560,420,790,420)
    s.cap(1100,550,130,'C_GH_EQ 4.7nF');s.line(790,420,1100,420);s.resistor(1230,550,130,'R_GSH 10kΩ',True);s.line(1100,420,1230,420)
    s.text(1120,365,'Measure GH_MON = V(G_H,SW)',14)
    s.box(100,455,280,180,'PWM + deadtime equivalent','0..1V sawtooth, F=100kHz\nHigh window: DEAD/T < CAR < DUTY\nLow window: CAR > DUTY+DEAD/T\nDisable: both gates pulled low\nDEAD=520ns (assumed)')
    s.line(380,580,500,640);s.text(400,620,'HC',12);s.line(380,510,500,460);s.text(405,465,'1-HC',12)
    s.line(560,325,560,300);s.text(510,345,'+12V_DRV');s.box(500,220,120,80,'S_LUP','Ron = 50Ω');s.line(560,220,560,190);s.dot(560,190);s.text(515,195,'LO');s.line(560,190,920,190);s.resistor(920,190,110,'RG_L 10Ω');s.line(1030,190,1230,190);s.text(1100,225,'G_L -> QL gate')
    s.box(690,100,120,70,'S_LDN','Ron = 25Ω');s.line(560,190,750,190);s.line(750,190,750,170);s.ground(750,100)
    s.line(425,260,500,260);s.text(430,278,'LC',13)
    s.line(640,135,690,135);s.text(640,154,'1-LC',13)
    s.cap(1100,190,90,'C_GL_EQ 4.7nF');s.ground(1100,100);s.resistor(1350,190,90,'R_GSL 10kΩ',True);s.line(1230,190,1350,190);s.ground(1350,100)
    s.text(75,120,'All switches: control voltage 0/1V. Channel gate threshold 6V is an assumption.',14)
    s.text(75,88,'Gate capacitance/driver impedance are simulation aids, not procurement changes.',14)
    s.finish()
    s=Sheet(p,'03_control_sense','03  采样、闭环与保护 / Sensing, continuous control and protection')
    s.box(65,660,250,150,'电压环 / CV','VSET × soft-start - 11×ADC_VOUT\nPI: Kp=0.5, Ki=50\nAnti-windup: 500/s')
    s.box(385,660,270,150,'电流目标限幅','IREF = LIMIT(PI+FF,-0.3,ISET)\nISET=1V represents 1A\nFF=Cout × dVset/dt')
    s.box(730,660,290,150,'电感电流环 / IL','ILmeas=2×(ADC_IL - V3A/2)\nPI: Kp=0.15, Ki=200\nFeedforward: V_CAP/VIN')
    s.box(1095,660,235,150,'PWM','DUTY = LIMIT(raw,0.08,0.88)\nCompare with 100kHz CAR\nDeadtime + enable -> driver')
    for x1,x2 in [(315,385),(655,730),(1020,1095)]:s.line(x1,735,x2,735)
    s.box(1400,660,235,150,'功率级 / Plant','See sheet 01 and 02\nVOUT + inductor current\nSources of feedback')
    s.line(1330,735,1400,735)
    s.box(65,420,500,175,'电流测量 / Current measurement','U2: IIN_RAW = 20 × V(RS_IN) = 1V/A\nU3: IOUT_RAW = 20 × V(RS_OUT) = 1V/A\nU4: IL_BI = V3A/2 + 20 × V(RS_L) = V3A/2+0.5V/A\nEach ADC branch: 1kΩ + 4.7nF to GND\nAmplifier output 0..V3A; raw pole ~0.4us (assumed)')
    s.box(625,420,430,175,'电压采样 / Voltage measurement','VIN_EXT --100k-- VIN_DIV --10k-- GND\nVIN_DIV --1k-- ADC_VIN; 4.7nF to GND\nVOUT --10k-- VOUT_DIV --1k-- GND\nVOUT_DIV --1k-- ADC_VOUT; 4.7nF to GND\nV3 ->10Ω->V3A; 1uF+100nF+10uF to GND')
    s.box(1115,420,520,175,'参考网络 / References (all 100nF to GND)','V3A --10k-- VREF_POS --33k--1k-- GND\nV3A --33k--1k-- VREF_NEG --10k-- GND\nV3A --23k-- VREF_OV --10k-- GND\nAt V3A=3.3V: POS=2.55V, NEG=0.75V, OV=1.00V\nActual V3A is lower because R_VDDA carries current')
    s.box(65,175,500,170,'比较器功能等效 / Fault comparators','IL_BI > VREF_POS -> FAULT_N low\nIL_BI < VREF_NEG -> FAULT_N low\nVOUT_DIV > VREF_OV -> FAULT_N low\nOutputs wired-OR, 10k pull-up to 3.3V\n1.3us output RC = assumption, not guaranteed delay')
    s.box(650,175,475,170,'锁存与使能 / Latch and enable','POR holds reset until 4ms (functional approximation)\nFAULT_N low asynchronously clears SAFE\nARM rising edge sets SAFE after fault clears\nDRV_EN = SAFE AND MCU_EN\nFAULT cleared alone does not restart switching')
    s.box(1210,175,425,170,'重要边界 / Not validated','Continuous PI is not F103 firmware\nNo LCD/key/ADC sampling-time simulation\nNo actual HC74/HC14 setup/hold/ramp validation\nNo vendor transistor/Miller/saturation model\nNo native Multisim 14 execution on this host')
    s.line(565,255,650,255)
    s.finish()
    s=Sheet(p,'04_multisim_testbench','04  Multisim首个可搭建电路 / 17-pin component testbench')
    s.box(590,180,440,640,'GBUCK_REVB_EQ','Import .lib with Component Wizard\nSimulation-only custom component\nCOM must connect to ground 0')
    left=[('VIN_EXT',730,'DC 25V'),('VSET',650,'DC 10V (10V target)'),('ISET',570,'DC 1V (1A target)'),('ARM',490,'PULSE 0->3.3V at 5ms, 10us wide'),('MCU_EN',410,'0 until 5.1ms, then 3.3V'),('COM',240,'Ground 0')]
    for name,y,label in left:
        s.line(360,y,590,y);s.text(400,y+12,name,15);s.text(60,y+30,label,14)
        if name!='COM':s.source(330,y);s.line(350,y,360,y)
    s.ground(360,240)
    right=[('VOUT',730),('FAULT_N',680),('IL_BI',630),('ADC_IL',580),('ADC_VIN',530),('ADC_IIN',480),('ADC_VOUT',430),('ADC_IOUT',380),('GH_MON',330),('GL_MON',280),('BOOT_MON',230)]
    for name,y in right:s.line(1030,y,1220,y);s.text(1060,y+10,name,14)
    s.resistor(1280,730,160,'RL = 8Ω',True);s.line(1220,730,1280,730);s.ground(1280,570)
    s.box(1320,300,320,255,'示波器与探针 / Probes','VOUT -> voltage waveform\nADC_IOUT -> load + bleed, 1V/A\nIL_BI -> actual zero V3A/2\nGH_MON -> high-side VGS buffer\nGL_MON -> low-side VGS buffer\nBOOT_MON -> VB-SW\nFAULT_N high normally')
    s.text(65,115,'Transient: 0..80ms, maximum step 100ns. Choose zero initial capacitor voltage/inductor current (UIC).',17)
    s.text(65,80,'Expected: about 8V / 1A. The input 25V is supplied only to VIN_EXT; no separate external 12V/5V rails are needed.',16)
    s.finish();p.save();print(OUT/'Multisim14_仿真电路接线图.pdf')

if __name__=='__main__':main()
