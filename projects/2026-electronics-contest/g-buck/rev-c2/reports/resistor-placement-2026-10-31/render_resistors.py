"""Draw placement diagrams from native-verified PCB geometry; never alter the PCB."""
from pathlib import Path
import os,json,sys,math,csv
os.environ.setdefault('MPLCONFIGDIR','/tmp/gbuck-resistor-mpl')
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
rs={r:v for r,v in parts.items() if r.startswith('R')}
assert len(rs)==43

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
  col=('#b54a3c' if r=='R_SN' else '#a35d00') if on else '#98afa6'
  rect(ax,0,0,w,h,v,facecolor=('#ffe4a3' if on else '#d5e1dc'),edgecolor=col,lw=1.2 if on else .5,zorder=2)
  for p in spec['pads']:
   rect(ax,p['x'],p['y'],p['w'],p['h'],v,facecolor='#ffb537' if on else '#bacdc3',edgecolor=col,lw=.35,zorder=3)
   if p['hole']:
    xx,yy=trans(p['x'],p['y'],v);ax.add_patch(Circle((xx,yy),min(p['w'],p['h'])/5,color='#fff',zorder=4))
  if not on and not r.startswith('TP'):
   ax.text(v['x'],v['y']+h/2+1,r,ha='center',va='bottom',fontsize=6,color='#647c72',zorder=5,clip_on=True)
 for x,y in m['mounting_holes_mm']:ax.add_patch(Circle((x,y),1.6,color='white',ec='#769487'))
 ax.set(xlim=limits[:2],ylim=limits[2:],aspect='equal',xlabel='X / mm',ylabel='Y / mm')
 ax.grid(alpha=.16)
def val(v):return v['value'].split(' / ')[0]
def footer(fig):
 fig.text(.5,.025,'元件面俯视，与仓库PCB预览同向；按工程坐标绘制，非实物照片。原生ERC/DRC未完成，仅供位置核对。',ha='center',fontsize=10,color='#55685f')

with PdfPages(OUT/'Resistors_RevC2.pdf') as pdf:
 fig,ax=plt.subplots(figsize=(16,12));fig.subplots_adjust(left=.07,right=.97,bottom=.09,top=.87)
 draw(ax,(-2,122,-2,92),rs)
 for r,v in rs.items():
  ax.text(v['x'],v['y']+1.5,r,ha='center',va='bottom',fontsize=6.2,color='#8e4800',weight='bold',bbox={'fc':'#fff9eb','ec':'none','alpha':.85,'pad':.5},zorder=8)
 for name,box in [('A 功率 / 驱动',(12,116,49,84)),('B 保护 / 逻辑',(22,74,15,46)),('C ADC / 采样',(74,116,10,48))]:
  x0,x1,y0,y1=box;ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#3279aa',ls='--',lw=1));ax.text(x0,y1+1,name,color='#24618a',fontsize=10)
 fig.suptitle('Rev C.2 电阻位置总览 | 120 × 90 mm',fontsize=23,y=.97)
 fig.text(.5,.91,'黄色：电阻焊盘及本体位置   ·   R_PRE：外置电阻的接线焊盘   ·   R_SN：默认不装',ha='center',fontsize=12)
 footer(fig);fig.savefig(OUT/'Resistors_Overview.png',dpi=180);pdf.savefig(fig);plt.close(fig)
 groups=[('A','功率与驱动区',(12,116,49,84),{r:v for r,v in rs.items() if v['y']>48}),('B','保护与逻辑区',(22,74,15,46),{r:v for r,v in rs.items() if v['y']<=48 and v['x']<76}),('C','ADC与采样区',(74,116,10,48),{r:v for r,v in rs.items() if v['y']<=48 and v['x']>=76})]
 assert sum(len(g[3]) for g in groups)==43
 for letter,title,lim,sel in groups:
  fig=plt.figure(figsize=(16,10));ax=fig.add_axes([.26,.17,.48,.66]);draw(ax,lim,sel)
  ordered=sorted(sel,key=lambda r:(sel[r]['x'],sel[r]['y']));half=(len(ordered)+1)//2
  for side,refs in [('left',ordered[:half]),('right',ordered[half:])]:
   refs=sorted(refs,key=lambda r:(-sel[r]['y'],sel[r]['x']))
   for i,r in enumerate(refs):
    v=sel[r];yy=.80-i*(.59/max(1,len(refs)-1));xx=.235 if side=='left' else .765
    extra='（不装）' if r=='R_SN' else '（外置）' if r=='R_PRE' else ''
    text=r+'  '+val(v)+extra
    if '0.1%' in v['value']:text+='  ±0.1%'
    ax.annotate(text,xy=(v['x'],v['y']),xycoords='data',xytext=(xx,yy),textcoords=fig.transFigure,ha='right' if side=='left' else 'left',va='center',fontsize=11.5,color='#753e00',bbox={'boxstyle':'round,pad=.35','fc':'#fff6df','ec':'#d4aa58'},arrowprops={'arrowstyle':'-','color':'#a36d20','lw':.8},annotation_clip=False,zorder=10)
    ax.plot(v['x'],v['y'],'o',ms=3,color='#9b4b00',zorder=12)
  fig.suptitle(f'{letter} | Rev C.2 {title}电阻位置与阻值',fontsize=23,y=.96)
  fig.text(.5,.89,'引线末端圆点对应器件中心；浅灰元件用于定位。没有“±0.1%”标注的精度请查采购清单。',ha='center',fontsize=11)
  footer(fig);fig.savefig(OUT/f'Resistors_{letter}.png',dpi=180);pdf.savefig(fig);plt.close(fig)
with (OUT/'resistor_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['位号','参数','X_mm','Y_mm','旋转_deg','PCB封装'])
 for r,v in rs.items():w.writerow([r,v['value'],v['x'],v['y'],v['angle'],v['package']])
print('Verified 120 native positions; rendered all 43 resistor references: 42 fitted + R_SN DNP.')
