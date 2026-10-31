"""Draw placement diagrams from native-verified PCB geometry; never alter the PCB."""
from pathlib import Path
import os,json,sys,math,csv
os.environ.setdefault('MPLCONFIGDIR','/tmp/gbuck-diode-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle,Circle
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
OUT=Path(__file__).resolve().parent
REV=OUT.parents[1]
PCB=REV/'pcb/hardware-fit-120x90'
sys.path.insert(0,str(REV/'schematic/tools'))
from native_common import read_project,attrs
m=json.loads((PCB/'data/build_manifest.json').read_text())
meta,docs,_=read_project(PCB/'native/GBUCK_RevC2_120x90_PCB_review.eprj2')
a=attrs(docs[m['pcb']]); parts=m['parts']; checked=0
for (kind,cid),c in docs[m['pcb']].items():
 if kind!='COMPONENT':continue
 ref=a[cid]['Designator'];v=parts[ref]
 assert abs(v['x']-c['x']*.0254)<1e-6 and abs(v['y']-c['y']*.0254)<1e-6 and v['angle']==c['angle'],ref
 checked+=1
assert checked==120
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'font.size':10,'pdf.fonttype':42})
rs={r:v for r,v in parts.items() if r.startswith('D')}
assert len(rs)==10

def trans(x,y,v):
 t=math.radians(v['angle']);return(v['x']+x*math.cos(t)-y*math.sin(t),v['y']+x*math.sin(t)+y*math.cos(t))
def rect(ax,x,y,w,h,v,**kw):
 pts=[trans(x+dx,y+dy,v) for dx,dy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
 ax.add_patch(Polygon(pts,**kw))
def draw(ax,limits,selected):
 ax.set_facecolor('#eff5f3')
 ax.add_patch(Rectangle((0,0),120,90,facecolor='#e2eeea',edgecolor='#154638',lw=1.8,zorder=0))
 for r,v in parts.items():
  spec=m['specs'][v['package']];w,h=spec['body_mm'];on=r in selected
  col='#a35d00' if on else '#98afa6'
  rect(ax,0,0,w,h,v,facecolor=('#ffe4a3' if on else '#d5e1dc'),edgecolor=col,lw=1.2 if on else .5,zorder=2)
  for p in spec['pads']:
   rect(ax,p['x'],p['y'],p['w'],p['h'],v,facecolor='#ffb537' if on else '#bacdc3',edgecolor=col,lw=.35,zorder=3)
   if p['hole']:
    xx,yy=trans(p['x'],p['y'],v);ax.add_patch(Circle((xx,yy),min(p['w'],p['h'])/5,color='#fff',zorder=4))
  if on:
   for p in spec['pads']:
    xx,yy=trans(p['x'],p['y'],v)
    if r in ('D1','D_FREE','D_BOOT'):
     kpin='2' if r=='D_BOOT' else '1'
     label=p['num']+('/K' if p['num']==kpin else '/A')
     off=2.0 if r!='D_FREE' or p['num']=='1' else -2.0
    else:
     label=p['num'];off=1.0 if p['num']=='3' else -1.0
    ax.text(xx,yy+off,label,ha='center',va='bottom' if off>0 else 'top',fontsize=9,color='#a02922',weight='bold',zorder=7,clip_on=True)
  if not on and not r.startswith('TP'):
   ax.text(v['x'],v['y']+h/2+1,r,ha='center',va='bottom',fontsize=6,color='#647c72',zorder=5,clip_on=True)
 for x,y in m['mounting_holes_mm']:ax.add_patch(Circle((x,y),1.6,color='white',ec='#769487'))
 ax.set(xlim=limits[:2],ylim=limits[2:],aspect='equal',xlabel='X / mm',ylabel='Y / mm')
 ax.grid(alpha=.16)
bom={x['位号']:x for x in csv.DictReader((REV/'results/data/bom-2026-10-27/bom_by_reference_120.csv').open(encoding='utf-8-sig'))}
def val(ref):
 s=bom[ref]['采购规格/建议']
 if '；' in s:s=s.split('；',1)[1]
 return s.replace('，低ESR，105℃',' 低ESR').replace('，±5%','').replace('，DNP','').replace('，',' ')

def footer(fig):
 fig.text(.5,.025,'元件面俯视，与仓库PCB预览同向；按工程坐标绘制，非实物照片。原生ERC/DRC未完成，仅供位置核对。',ha='center',fontsize=10,color='#55685f')

with PdfPages(OUT/'Diodes_RevC2.pdf') as pdf:
 fig,ax=plt.subplots(figsize=(16,12));fig.subplots_adjust(left=.07,right=.97,bottom=.09,top=.87)
 draw(ax,(-2,122,-2,92),rs)
 for r,v in rs.items():
  ax.text(v['x'],v['y']+1.5,r,ha='center',va='bottom',fontsize=6.2,color='#8e4800',weight='bold',bbox={'fc':'#fff9eb','ec':'none','alpha':.85,'pad':.5},zorder=8)
 for name,box in [('A 功率 / 自举',(33,88,44,73)),('B 保护 / ADC',(52,110,3,44))]:
  x0,x1,y0,y1=box;ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#3279aa',ls='--',lw=1));ax.text(x0,y1+1,name,color='#24618a',fontsize=10)
 fig.suptitle('Rev C.2 二极管位置总览 | 120 × 90 mm',fontsize=23,y=.97)
 fig.text(.5,.91,'黄色：二极管焊盘及本体位置   ·   A=阳极，K=阴极 / 色条端   ·   三脚器件按脚号核对',ha='center',fontsize=12)
 footer(fig);fig.savefig(OUT/'Diodes_Overview.png',dpi=180);pdf.savefig(fig);plt.close(fig)
 groups=[('A','功率与自举区',(33,88,44,73),{r:v for r,v in rs.items() if r in ('D1','D_FREE','D_BOOT')}),('B','保护与ADC区',(52,110,3,44),{r:v for r,v in rs.items() if r not in ('D1','D_FREE','D_BOOT')})]
 assert sum(len(g[3]) for g in groups)==10
 for letter,title,lim,sel in groups:
  fig=plt.figure(figsize=(16,10));ax=fig.add_axes([.26,.17,.48,.66]);draw(ax,lim,sel)
  ordered=sorted(sel,key=lambda r:(sel[r]['x'],sel[r]['y']));half=(len(ordered)+1)//2
  for side,refs in [('left',ordered[:half]),('right',ordered[half:])]:
   refs=sorted(refs,key=lambda r:(-sel[r]['y'],sel[r]['x']))
   for i,r in enumerate(refs):
    v=sel[r];yy=.80-i*(.59/max(1,len(refs)-1));xx=.235 if side=='left' else .765
    text=r+'\n'+('SR560 / SMB\n1=K，2=A' if r in ('D1','D_FREE') else 'UF4007 / DO-41\n1=A，2=K' if r=='D_BOOT' else 'BAT54 / SOT-23\n1=A，2=NC，3=K' if r=='D_POR' else 'BAT54S / SOT-23\n1=A1，2=K2，3=共点')
    fig.text(xx,yy,text,ha='right' if side=='left' else 'left',va='center',fontsize=10.5,color='#753e00',bbox={'boxstyle':'round,pad=.35','fc':'#fff6df','ec':'#d4aa58'})
    ax.annotate('',xy=(v['x'],v['y']),xycoords='data',xytext=(xx,yy),textcoords=fig.transFigure,arrowprops={'arrowstyle':'-','color':'#a36d20','lw':.8},annotation_clip=False,zorder=9)
    ax.plot(v['x'],v['y'],'o',ms=3,color='#9b4b00',zorder=12)
  fig.suptitle(f'{letter} | Rev C.2 {title}二极管位置与型号与方向',fontsize=23,y=.96)
  fig.text(.5,.89,'引线末端圆点为器件中心；红字标出焊盘脚号与A/K。BAT54与BAT54S不可混装。',ha='center',fontsize=11)
  footer(fig);fig.savefig(OUT/f'Diodes_{letter}.png',dpi=180);pdf.savefig(fig);plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(15,7));fig.subplots_adjust(top=.76,bottom=.2,wspace=.25)
 for ax,ref,title in [(axes[0],'D_ADC1','BAT54S：D_ADC1～D_ADC6'),(axes[1],'D_POR','BAT54：D_POR')]:
  v=parts[ref];spec=m['specs'][v['package']]
  ax.add_patch(Rectangle((-1.45,-.65),2.9,1.3,fc='#ffe4a3',ec='#a35d00'))
  labels={'1':'1 = A1','2':'2 = K2','3':'3 = K1 / A2（共点）'} if ref=='D_ADC1' else {'1':'1 = A','2':'2 = NC（不接）','3':'3 = K'}
  for p in spec['pads']:
   ax.add_patch(Rectangle((p['x']-p['w']/2,p['y']-p['h']/2),p['w'],p['h'],fc='#ffb537',ec='#a35d00'))
   ax.text(p['x'],p['y']+(1 if p['num']=='3' else -1),labels[p['num']],ha='center',va='bottom' if p['num']=='3' else 'top',fontsize=12,color='#8c2828')
  ax.set(xlim=(-3,3),ylim=(-3,3),aspect='equal');ax.axis('off');ax.set_title(title,fontsize=17)
 fig.suptitle('SOT-23 焊盘方向放大图 | 元件面俯视',fontsize=24)
 fig.text(.5,.85,'当前板上这7只器件均为0°：单脚在上，双脚在下；左下1，右下2，上方3。',ha='center',fontsize=13)
 fig.text(.5,.12,'BAT54S内部为 1(A1) → 二极管 → 3(K1/A2) → 二极管 → 2(K2)。\n实物字码不能单独证明型号；按厂家完整料号、顶视图及管脚功能核对，不凭文字朝向判断。',ha='center',fontsize=12)
 fig.savefig(OUT/'Diodes_Pinout.png',dpi=180);pdf.savefig(fig);plt.close(fig)
with (OUT/'diode_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['位号','工程原参数','采购规格/建议','X_mm','Y_mm','旋转_deg','PCB封装'])
 for r,v in rs.items():w.writerow([r,v['value'],bom[r]['采购规格/建议'],v['x'],v['y'],v['angle'],v['package']])
print('Verified 120 native positions; rendered all 10 diode references; all fitted.')
