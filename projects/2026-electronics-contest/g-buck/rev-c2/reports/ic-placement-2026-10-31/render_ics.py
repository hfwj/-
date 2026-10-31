"""Draw placement diagrams from native-verified PCB geometry; never alter the PCB."""
from pathlib import Path
import os,json,sys,math,csv
os.environ.setdefault('MPLCONFIGDIR','/tmp/gbuck-ic-mpl')
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
rs={r:v for r,v in parts.items() if r in ('U2','U3','U4','U5','U6','U7','U8','U9')}
assert len(rs)==8

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
   p=next(p for p in spec['pads'] if p['num']=='1');xx,yy=trans(p['x'],p['y'],v)
   ax.plot(xx,yy,'o',ms=5,color='#c82a25',zorder=8)
   ax.text(xx-1.2,yy,'1',ha='right',va='center',fontsize=10,color='#a02922',weight='bold',zorder=8,clip_on=True)
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


functions={'U2':'输入电流采样 / 增益20','U3':'输出电流采样 / 增益20','U4':'电感电流采样 / 增益20','U5':'双比较器 / 保护检测','U9':'双比较器 / 保护检测','U6':'双D触发器 / 安全锁存','U7':'四路二输入与门 / 使能','U8':'六路施密特反相器 / 上电复位'}
models={'U2':'INA240A1D','U4':'INA240A1D','U3':'INA181A1DBV','U5':'LM393DR','U9':'LM393DR','U6':'SN74HC74DR','U7':'SN74HC08DR','U8':'SN74HC14DR'}
packages={'SOIC8_150':'SOIC-8','SOIC14_150':'SOIC-14','SOT23_6':'SOT-23-6'}
with PdfPages(OUT/'ICs_RevC2.pdf') as pdf:
 fig,ax=plt.subplots(figsize=(16,12));fig.subplots_adjust(left=.07,right=.97,bottom=.09,top=.87)
 draw(ax,(-2,122,-2,92),rs)
 for ref,v in rs.items():ax.text(v['x'],v['y']+2.5,ref+' '+models[ref],ha='center',va='bottom',fontsize=8,color='#8e4800',weight='bold',bbox={'fc':'#fff9eb','ec':'none','alpha':.9,'pad':.5},zorder=8)
 for name,box in [('A 采样芯片',(40,112,49,90)),('B 比较 / 逻辑',(22,80,13,43))]:
  x0,x1,y0,y1=box;ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#3279aa',ls='--',lw=1));ax.text(x0,y1+1,name,color='#24618a',fontsize=10)
 fig.suptitle('Rev C.2 采样、比较及逻辑芯片位置总览',fontsize=23,y=.97)
 fig.text(.5,.91,'黄色：本次8只贴片芯片   ·   红点：PCB的1脚焊盘   ·   灰色U1为IR2184驱动，另装',ha='center',fontsize=12)
 footer(fig);fig.savefig(OUT/'ICs_Overview.png',dpi=180);pdf.savefig(fig);plt.close(fig)
 groups=[('A','采样芯片',(40,112,49,90),{r:v for r,v in rs.items() if r in ('U2','U3','U4')}),('B','比较及逻辑芯片',(22,80,13,43),{r:v for r,v in rs.items() if r not in ('U2','U3','U4')})]
 assert sum(len(g[3]) for g in groups)==8
 for letter,title,lim,sel in groups:
  fig=plt.figure(figsize=(16,10));ax=fig.add_axes([.26,.17,.48,.66]);draw(ax,lim,sel)
  ordered=sorted(sel,key=lambda r:(sel[r]['x'],sel[r]['y']));half=(len(ordered)+1)//2
  for side,refs in [('left',ordered[:half]),('right',ordered[half:])]:
   refs=sorted(refs,key=lambda r:(-sel[r]['y'],sel[r]['x']))
   for i,r in enumerate(refs):
    v=sel[r];yy=.80-i*(.59/max(1,len(refs)-1));xx=.235 if side=='left' else .765
    text=r+'  '+models[r]+'\n'+packages[v['package']]+'\n'+functions[r]
    fig.text(xx,yy,text,ha='right' if side=='left' else 'left',va='center',fontsize=11,color='#753e00',bbox={'boxstyle':'round,pad=.35','fc':'#fff6df','ec':'#d4aa58'})
    ax.annotate('',xy=(v['x'],v['y']),xycoords='data',xytext=(xx,yy),textcoords=fig.transFigure,arrowprops={'arrowstyle':'-','color':'#a36d20','lw':.8},annotation_clip=False,zorder=9)
  fig.suptitle(f'{letter} | Rev C.2 {title}位置、型号与1脚方向',fontsize=23,y=.96)
  fig.text(.5,.89,'红点=1脚焊盘。U2/U4及U5/U9、U6/U7/U8的1脚在左上；U3的1脚在左下。',ha='center',fontsize=11)
  footer(fig);fig.savefig(OUT/f'ICs_{letter}.png',dpi=180);pdf.savefig(fig);plt.close(fig)
 fig,axes=plt.subplots(1,3,figsize=(16,8));fig.subplots_adjust(top=.75,bottom=.23,wspace=.25)
 for ax,ref,title in [(axes[0],'U2','SOIC-8：U2/U4/U5/U9'),(axes[1],'U6','SOIC-14：U6/U7/U8'),(axes[2],'U3','SOT-23-6：U3')]:
  spec=m['specs'][parts[ref]['package']];w,h=spec['body_mm'];ax.add_patch(Rectangle((-w/2,-h/2),w,h,fc='#ffe4a3',ec='#a35d00'))
  p1=next(p for p in spec['pads'] if p['num']=='1')
  ax.plot(p1['x']*.5,p1['y']*.8,'o',ms=7,color='#c82a25')
  for p in spec['pads']:
   ax.add_patch(Rectangle((p['x']-p['w']/2,p['y']-p['h']/2),p['w'],p['h'],fc='#ffb537',ec='#a35d00'))
   if ref=='U3':ax.text(p['x'],p['y']+(.8 if p['y']>0 else -.8),p['num'],ha='center',va='bottom' if p['y']>0 else 'top',fontsize=13,color='#8c2828')
   else:ax.text(p['x']+(1.2 if p['x']>0 else -1.2),p['y'],p['num'],ha='left' if p['x']>0 else 'right',va='center',fontsize=12,color='#8c2828')
  ax.set(xlim=(-6,6),ylim=(-6,6),aspect='equal');ax.axis('off');ax.set_title(title,fontsize=14)
 fig.suptitle('芯片脚位方向放大图 | 元件面俯视',fontsize=24)
 fig.text(.5,.85,'红点表示1脚对应角；本图为PCB要求方向，须以实物厂家1脚标识核对后安装。',ha='center',fontsize=13)
 fig.text(.5,.13,'不要按表面文字朝向判断，也不要把所有圆形模痕都当作1脚点。\nINA240A1D是SOIC-8；INA181A1DBV是SOT-23-6；74HC74 / 74HC08 / 74HC14功能不同，不可互换。',ha='center',fontsize=12)
 fig.savefig(OUT/'ICs_Pin1.png',dpi=180);pdf.savefig(fig);plt.close(fig)
with (OUT/'ic_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['位号','采购型号','工程原标注','功能','X_mm','Y_mm','旋转_deg','PCB封装'])
 for r,v in rs.items():w.writerow([r,models[r],v['value'],functions[r],v['x'],v['y'],v['angle'],v['package']])
print('Verified 120 native positions; rendered all 8 requested ICs with pin-1 markers.')
