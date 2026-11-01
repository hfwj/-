"""Draw exact external harness endpoints; diagrams do not change the PCB."""
from pathlib import Path
import os,csv
os.environ.setdefault('MPLCONFIGDIR','/tmp/gbuck-wiring-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent; REV=ROOT.parents[1];OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':12,'pdf.fonttype':42})
BG='#f6f8fc';BLUE='#2463a5';RED='#bf3b32';GND='#67707c';GREEN='#248363';PURPLE='#8652a5';ORANGE='#ad6b14'
expected={'J_CTL':['GND','+5V','GND','+3V3','PWM_CTL','IOUT_OC_N','MCU_EN','ARM','FAULT_N','GND','ADC_VIN','ADC_IIN','ADC_VOUT','ADC_IOUT','ADC_IL','GND'],'J_AUX12':['VIN','GND','+12V_DRV','GND'],'J_AUX5':['VIN','GND','+5V','GND'],'J_MON':['ADC_VIN_POST','GND'],'J1':['VIN_EXT','GND'],'J2':['VOUT','GND'],'J_BYP':['FUSED','IN_PRE'],'R_PRE':['FUSED','IN_PRE']}
pins={(r['ref'],r['pin']):r['net'] for r in csv.DictReader((REV/'pcb/hardware-fit-120x90/data/PCB_pin_readback.csv').open(encoding='utf-8-sig'))}
for ref,nets in expected.items():
 for i,net in enumerate(nets,1):assert pins[(ref,str(i))]==net,(ref,i)

def axis(ax):ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
def box(ax,x,y,w,h,label,fc='white',ec='#b9c9dc',fs=12):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.007',fc=fc,ec=ec,lw=1.2));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=fs,color='#253951')
def wire(ax,x0,y0,x1,y1,color=BLUE,direction='right',lw=1.8):
 if direction=='none':ax.plot([x0,x1],[y0,y1],color=color,lw=lw,zorder=1)
 else:
  if direction=='left':x0,y0,x1,y1=x1,y1,x0,y0
  ax.annotate('',xy=(x1,y1),xytext=(x0,y0),arrowprops={'arrowstyle':'-|>','color':color,'lw':lw},zorder=1)
def title(fig,heading,note):
 fig.suptitle(heading,fontsize=23,y=.97,color='#183858',weight='bold');fig.text(.5,.925,note,ha='center',fontsize=12,color='#536477')
def footer(fig,note):fig.text(.5,.025,note,ha='center',va='center',fontsize=11,color='#6b5860')
def save(fig,name,pdf):fig.savefig(OUT/name,dpi=160,facecolor='white');pdf.savefig(fig);plt.close(fig)

with PdfPages(OUT/'External_Wiring_RevC2.pdf') as pdf:
 fig,axs=plt.subplots(2,2,figsize=(17,12));fig.subplots_adjust(left=.04,right=.96,bottom=.09,top=.85,hspace=.28,wspace=.12)
 title(fig,'Rev C.2 板外接线①｜辅助电源、预充与输入/负载','功能接线示意，按端口名称接线；模块焊盘的实际排列以实物标识为准。')
 for ax,ref,volts in [(axs[0,0],'J_AUX12','12V'),(axs[0,1],'J_AUX5','5V')]:
  axis(ax);ax.set_title(ref+' ↔ 外接降压模块（目标'+volts+'）',fontsize=16,color=BLUE,pad=12)
  box(ax,.02,.12,.32,.76,'',fc='#edf3fc');box(ax,.68,.12,.30,.76,'',fc='#f0f8ef')
  ax.text(.18,.83,'主板 '+ref,ha='center',fontsize=13,weight='bold');ax.text(.83,.83,'外接降压模块',ha='center',fontsize=13,weight='bold')
  ll=['1  VIN（预充后）','2  GND','3  '+volts+'返回主板','4  GND'];rr=['IN+','IN−','OUT+  '+volts,'OUT−']
  for i,(left,right) in enumerate(zip(ll,rr)):
   y=.70-i*.16;col=GND if i in (1,3) else RED if i==0 else ORANGE
   ax.text(.18,y,left,ha='center',va='center',fontsize=12);ax.text(.83,y,right,ha='center',va='center',fontsize=12)
   wire(ax,.345,y,.675,y,col,'none' if i in (1,3) else 'right' if i==0 else 'left')
  ax.text(.5,.015,'先单独限流供电调压，断电后再连接主板。',ha='center',fontsize=11,color=RED)
 ax=axs[1,0];axis(ax);ax.set_title('外置R_PRE电阻 + J_BYP旁路开关',fontsize=16,color=BLUE,pad=12)
 for x in [.14,.86]:ax.plot([x,x],[.28,.68],color='#a8b4c2',lw=2,ls='--')
 ax.text(.14,.84,'板内同网：FUSED',ha='center',fontsize=11);ax.text(.86,.84,'板内同网：IN_PRE',ha='center',fontsize=11)
 for x,label in [(.14,'R_PRE.1'),(.86,'R_PRE.2')]:ax.add_patch(Circle((x,.68),.013,color=ORANGE));ax.text(x,.73,label,ha='center',fontsize=11)
 wire(ax,.14,.68,.40,.68,ORANGE,'none');wire(ax,.60,.68,.86,.68,ORANGE,'none');box(ax,.40,.615,.20,.13,'22Ω / 5W',fc='#fff4dc',ec=ORANGE)
 ax.text(.5,.51,'外置固定，单次脉冲耐量≥0.3J',ha='center',fontsize=11)
 for x,label in [(.14,'J_BYP.1'),(.86,'J_BYP.2')]:ax.add_patch(Circle((x,.28),.013,color=GREEN));ax.text(x,.20,label,ha='center',fontsize=11)
 wire(ax,.14,.28,.43,.28,GREEN,'none');wire(ax,.60,.28,.86,.28,GREEN,'none');ax.plot([.43,.57],[.28,.39],color=GREEN,lw=2.6);ax.add_patch(Circle((.60,.28),.009,fc='white',ec=GREEN))
 ax.text(.5,.07,'常开保持型SPST，≥30VDC/3A；初始断开',ha='center',fontsize=11,color=RED)
 ax=axs[1,1];axis(ax);ax.set_title('输入直流电源与假负载',fontsize=16,color=BLUE,pad=12)
 box(ax,.02,.58,.32,.26,'限流直流电源\n15～25V',fc='#edf3fc');box(ax,.68,.58,.30,.26,'主板 J1',fc='#fff4dc')
 for y,l,r,c in [(.76,'+','1 / VIN_EXT',RED),(.64,'−','2 / GND',GND)]:
  ax.text(.31,y,l,ha='right',va='center',fontsize=14);ax.text(.70,y,r,ha='left',va='center',fontsize=12);wire(ax,.35,y,.67,y,c,'none')
 box(ax,.02,.18,.32,.26,'主板 J2',fc='#fff4dc');box(ax,.68,.18,.30,.26,'假负载',fc='#f0f8ef')
 for y,l,r,c in [(.36,'1 / VOUT','+',RED),(.24,'2 / GND','−',GND)]:
  ax.text(.31,y,l,ha='right',va='center',fontsize=12);ax.text(.70,y,r,ha='left',va='center',fontsize=14);wire(ax,.35,y,.67,y,c,'none')
 ax.text(.5,.065,'首次功率测试不接真实电池。',ha='center',fontsize=11,color=RED)
 footer(fig,'接线/插拔时断电并确认电容放电。预充检查正常、输出仍关闭时再闭合实体旁路；软件确认不替代实体开关。')
 save(fig,'Wiring_1_Power.png',pdf)

 fig,ax=plt.subplots(figsize=(15,15));fig.subplots_adjust(left=.035,right=.965,bottom=.04,top=.88);axis(ax)
 title(fig,'Rev C.2 板外接线②｜主板 ↔ STM32核心板','逐脚线束图，不表示核心板的物理排针排列；主板2×8端顶端1/2、底端15/16。')
 ax.text(.18,.97,'主板接口 / 脚号',ha='center',fontsize=16,color=BLUE,weight='bold');ax.text(.82,.97,'STM32F103C8T6核心板',ha='center',fontsize=16,color=BLUE,weight='bold')
 ctl=[('GND','地',GND,'none'),('5V输入','主板5V → 核心板',RED,'right'),('GND','地',GND,'none'),('3.3V输出','核心板3.3V → 主板',ORANGE,'left'),('PA8','PWM',GREEN,'left'),('PB11','IOUT_OC_N',PURPLE,'right'),('PB0','MCU_EN',GREEN,'left'),('PB1','ARM',GREEN,'left'),('PB10','FAULT_N',PURPLE,'right'),('GND','地',GND,'none'),('PA0','输入电压ADC',BLUE,'right'),('PA1','输入电流ADC',BLUE,'right'),('PA2','输出电压ADC',BLUE,'right'),('PA3','输出电流ADC',BLUE,'right'),('PA4','电感电流ADC',BLUE,'right'),('GND','地',GND,'none')]
 connections=[]
 for i,(target,func,col,direction) in enumerate(ctl):connections.append((f'J_CTL.{i+1}',target,func,col,direction))
 connections += [('J_MON.1','PA6','预充后VIN的ADC',BLUE,'right'),('J_MON.2','GND','监测地',GND,'none')]
 for i,(source,target,func,col,direction) in enumerate(connections):
  y=.915-i*.044
  box(ax,.04,y-.017,.28,.034,source,fc='#fff4dc' if source.startswith('J_MON') else '#edf3fc',ec=col,fs=12)
  box(ax,.68,y-.017,.28,.034,target,fc='#f0f8ef',ec=col,fs=12);wire(ax,.33,y,.67,y,col,direction)
  ax.text(.50,y+.009,func,ha='center',va='bottom',fontsize=10.5,color=col,bbox={'fc':'white','ec':'none','pad':1})
 ax.text(.5,.065,'重点：J_CTL.6接PB11，不接地；J_MON.1接PA6；PA6不能接屏幕MISO。',ha='center',fontsize=12,color=RED,weight='bold')
 ax.text(.5,.025,'实际核心板须确认5V脚为输入、3.3V脚为输出，并核对允许负载；ADC脚不能接5V/12V/主输入。',ha='center',fontsize=11,color='#6b5860')
 save(fig,'Wiring_2_STM32.png',pdf)

 fig,axs=plt.subplots(2,1,figsize=(15,14));fig.subplots_adjust(left=.04,right=.96,bottom=.08,top=.86,hspace=.35)
 title(fig,'Rev C.2 板外接线③｜屏幕与SWD下载器','屏幕按信号名接线；括号内编号仅适用于仓库归档的11Pin屏，其他版本不能套用。')
 ax=axs[0];axis(ax);ax.set_title('屏幕 ↔ STM32 / 电源',fontsize=16,color=BLUE,pad=12)
 lcd=[('VCC（11Pin：1）','按实际屏幕要求选5V或3.3V',ORANGE),('GND（11Pin：2、3）','GND，共地',GND),('SCK / CLK（11Pin：7）','PA5',BLUE),('SDA / MOSI（11Pin：8）','PA7',BLUE),('DC / RS（11Pin：9）','PB13',GREEN),('RST / RES（11Pin：10）','PB14',GREEN),('CS（11Pin：11）','PB12',GREEN)]
 for i,(left,right,col) in enumerate(lcd):
  y=.88-i*.115;box(ax,.02,y-.04,.36,.08,left,fc='#edf3fc',ec=col,fs=12);box(ax,.62,y-.04,.36,.08,right,fc='#f0f8ef',ec=col,fs=12);wire(ax,.39,y,.61,y,col,'none')
 ax.text(.5,.025,'归档11Pin屏：4/5/6脚NC不接。5V供电时屏幕J1跳线断开，3.3V时短接；须核实实物版本。',ha='center',fontsize=10.5,color=RED)
 ax=axs[1];axis(ax);ax.set_title('ST-Link ↔ STM32（按下载器说明接参考脚）',fontsize=16,color=BLUE,pad=12)
 swd=[('SWDIO','PA13',BLUE),('SWCLK','PA14',GREEN),('GND','GND',GND),('3.3V参考 / 检测脚','按下载器说明接目标3.3V',ORANGE),('NRST（可选）','NRST',PURPLE)]
 for i,(left,right,col) in enumerate(swd):
  y=.88-i*.15;box(ax,.02,y-.045,.36,.09,left,fc='#edf3fc',ec=col,fs=12);box(ax,.62,y-.045,.36,.09,right,fc='#f0f8ef',ec=col,fs=12);wire(ax,.39,y,.61,y,col,'none')
 ax.text(.5,.13,'BOOT0=0；先烧录POWER=0诊断固件。下载器“参考脚”不自动等同于供电输出。',ha='center',fontsize=11,color=RED)
 ax.text(.5,.025,'USB、调试器和外部电源避免反灌；背光独立BL/LED脚按实际屏幕资料接，未确认先不接。',ha='center',fontsize=11,color=RED)
 footer(fig,'这些是接线要求，未代表实际模块或线束已经验收。原生ERC/DRC、实物电气与功率验证仍待完成。')
 save(fig,'Wiring_3_LCD_SWD.png',pdf)
print('Rendered 3 wiring sheets and PDF; verified 34 mainboard connector/pad nets.')
