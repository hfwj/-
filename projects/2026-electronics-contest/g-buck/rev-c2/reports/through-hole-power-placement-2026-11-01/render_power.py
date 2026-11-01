"""Draw placement diagrams from native-verified PCB geometry; never alter the PCB."""
from pathlib import Path
import os,json,sys,math,csv
os.environ.setdefault('MPLCONFIGDIR','/tmp/gbuck-power-mpl')
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
refs=('F1','C1','C3','RS_IN','RS_OUT','RS_L','QH','QL','L1','D1','D_FREE','R_BL','U1','D_BOOT','R_PRE','J1','J2','J_BYP','J_MON','J_AUX12','J_AUX5','J_CTL')
rs={r:parts[r] for r in refs}
assert len(rs)==22

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
    xx,yy=trans(p['x'],p['y'],v);label=p['num']
    if r in ('C1','C3'):label='+' if p['num']=='1' else '−'
    elif r in ('QH','QL'):label={'1':'G','2':'D','3':'S'}[p['num']]
    elif r in ('D1','D_FREE','D_BOOT'):
     label=p['num']+('/K' if p['num']==('2' if r=='D_BOOT' else '1') else '/A')
    elif r=='U1' and p['num']!='1':continue
    elif r=='J_CTL' and p['num'] not in ('1','2','15','16'):continue
    off=0 if r.startswith('J') else (1.6 if not (r=='D_FREE' and p['num']=='2') else -1.8)
    ax.text(xx,yy+off,label,ha='center',va='center' if off==0 else ('bottom' if off>0 else 'top'),fontsize=7.5,color='#a02922',weight='bold',zorder=8,clip_on=True)
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



labels={
'F1':'2A快断 / 5×20mm\n管夹间距须实物试装',
'C1':'470µF / 50V\n电解，注意正负极','C3':'470µF / 35V\n电解，注意正负极',
'RS_IN':'50mΩ / M型 / P10','RS_OUT':'50mΩ / M型 / P10','RS_L':'25mΩ / U型 / P5',
'QH':'IRF540N / TO-220\n1=G，2=D，3=S','QL':'IRF540N / TO-220\n1=G，2=D，3=S',
'L1':'220µH / 立式 / P10','D1':'SR560 / SMB贴片\n1=K，2=A','D_FREE':'SR560 / SMB贴片\n1=K，2=A','R_BL':'2.2kΩ / ≥0.25W / 1206',
'U1':'IR2184PbF / DIP-8\n1脚左上，按脚号核对','D_BOOT':'UF4007 / DO-41\n色环端K朝右','R_PRE':'外置22Ω / 5W\n图示是接线焊盘',
'J1':'输入端 / P2.54\n1=VIN_EXT，2=GND','J2':'输出端 / P2.54\n1=VOUT，2=GND',
'J_BYP':'外接常开保持型旁路开关\n跨接预充电阻两端','J_MON':'监测端 / P2.54\n1→PA6，2→GND',
'J_AUX12':'外接12V降压模块\n1=VIN，2=GND，3=12V，4=GND',
'J_AUX5':'外接5V降压模块\n1=VIN，2=GND，3=5V，4=GND',
'J_CTL':'控制排针 / 2×8 / P2.54\n1/2在上，15/16在下'}
groups=[('A','主功率器件',(12,120,39,87),{r:rs[r] for r in refs[:12]}),('B','驱动、自举与外置预充',(12,69,45,70),{r:rs[r] for r in refs[12:15]}),('C','直插端子与排针',(0,120,0,90),{r:rs[r] for r in refs[15:]})]
assert sum(len(g[3]) for g in groups)==22
with PdfPages(OUT/'ThroughHole_Power_RevC2.pdf') as pdf:
 fig,ax=plt.subplots(figsize=(16,12));fig.subplots_adjust(left=.07,right=.97,bottom=.09,top=.87);draw(ax,(-2,122,-2,92),rs)
 for ref,v in rs.items():ax.text(v['x'],v['y']+2,ref,ha='center',va='bottom',fontsize=8,color='#8e4800',weight='bold',bbox={'fc':'#fff9eb','ec':'none','alpha':.9,'pad':.5},zorder=9)
 fig.suptitle('Rev C.2 直插件、外接接口与功率器件位置总览',fontsize=23,y=.97)
 fig.text(.5,.91,'黄色：本次22个位号；含D1/D_FREE/R_BL贴片功率件。R_PRE为外置电阻接线焊盘。',ha='center',fontsize=12)
 footer(fig);fig.savefig(OUT/'Power_Overview.png',dpi=160);pdf.savefig(fig);plt.close(fig)
 for letter,title,lim,sel in groups:
  fig=plt.figure(figsize=(17,11));ax=fig.add_axes([.27,.17,.46,.66]);draw(ax,lim,sel)
  ordered=sorted(sel,key=lambda r:(sel[r]['x'],sel[r]['y']));half=(len(ordered)+1)//2
  for side,rr in [('left',ordered[:half]),('right',ordered[half:])]:
   rr=sorted(rr,key=lambda r:(-sel[r]['y'],sel[r]['x']))
   for i,r in enumerate(rr):
    v=sel[r];yy=.80-i*(.59/max(1,len(rr)-1));xx=.25 if side=='left' else .75
    fig.text(xx,yy,r+'\n'+labels[r],ha='right' if side=='left' else 'left',va='center',fontsize=10.5,color='#753e00',bbox={'boxstyle':'round,pad=.35','fc':'#fff6df','ec':'#d4aa58'})
    ax.annotate('',xy=(v['x'],v['y']),xycoords='data',xytext=(xx,yy),textcoords=fig.transFigure,arrowprops={'arrowstyle':'-','color':'#a36d20','lw':.8},annotation_clip=False,zorder=9)
  fig.suptitle(f'{letter} | Rev C.2 {title}位置与安装方向',fontsize=23,y=.96)
  fig.text(.5,.89,'按焊盘脚号接线；上电前核对极性。QH/QL金属背板均为漏极，共用散热片时必须电气绝缘。',ha='center',fontsize=11)
  footer(fig);fig.savefig(OUT/f'Power_{letter}.png',dpi=160);pdf.savefig(fig);plt.close(fig)
 fig,axes=plt.subplots(1,3,figsize=(18,10));fig.subplots_adjust(top=.78,bottom=.2,wspace=.35)
 for ax,ref,title in [(axes[0],'U1','U1：IR2184 DIP-8'),(axes[1],'QH','QH / QL：IRF540N'),(axes[2],'J_CTL','J_CTL：2×8排针')]:
  spec=m['specs'][parts[ref]['package']];w,h=spec['body_mm'];ax.add_patch(Rectangle((-w/2,-h/2),w,h,fc='#ffe4a3',ec='#a35d00'))
  for p in spec['pads']:
   ax.add_patch(Rectangle((p['x']-p['w']/2,p['y']-p['h']/2),p['w'],p['h'],fc='#ffb537',ec='#a35d00'))
   if ref=='QH':ax.text(p['x'],p['y']-2,p['num']+'='+{'1':'G','2':'D','3':'S'}[p['num']],ha='center',va='top',fontsize=12,color='#8c2828')
   elif ref=='U1':
    fn={'1':'IN','2':'SD#','3':'COM','4':'LO','5':'VCC','6':'VS','7':'HO','8':'VB'}[p['num']]
    ax.text(p['x']+(-1.4 if p['x']<0 else 1.4),p['y'],p['num']+' '+fn,ha='right' if p['x']<0 else 'left',va='center',fontsize=11,color='#8c2828')
   else:ax.text(p['x']+(-1.4 if p['x']<0 else 1.4),p['y'],p['num'],ha='right' if p['x']<0 else 'left',va='center',fontsize=12,color='#8c2828')
  if ref=='U1':ax.plot(-2,3.8,'o',color='#c82a25',ms=7)
  ax.set(xlim=(-8,8),ylim=(-12,12),aspect='equal');ax.axis('off');ax.set_title(title,fontsize=16)
 fig.suptitle('关键脚位放大图 | PCB元件面俯视',fontsize=24)
 fig.text(.5,.85,'这是板上焊盘方向；MOS管实物按厂家脚号核对，不能只凭外壳朝向判断。U1不能用IR2104直接替换。',ha='center',fontsize=13)
 fig.text(.5,.11,'J_CTL排针：左列奇数，右列偶数；顶端1/2。第6脚接PB11，第4脚为3.3V，第2脚为5V。\nJ_AUX12/J_AUX5在位置图中从下到上为1→4；模块自身的焊盘位置不一定按这个顺序排列。',ha='center',fontsize=13)
 fig.savefig(OUT/'Power_Pinout.png',dpi=160);pdf.savefig(fig);plt.close(fig)
with (OUT/'power_positions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['位号','工程参数','装配说明','X_mm','Y_mm','旋转_deg','PCB封装'])
 for r,v in rs.items():w.writerow([r,v['value'],labels[r].replace('\n','；'),v['x'],v['y'],v['angle'],v['package']])
print('Verified 120 native positions; rendered all 22 selected through-hole/interface/power references.')
