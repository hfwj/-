"""Build Chinese tutorial figures, editable DOCX, PDF, and arithmetic evidence.
Run from the repository root. All curves are ideal teaching illustrations.
"""
from pathlib import Path
import csv, hashlib, html, json, re, subprocess, zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.font_manager import FontProperties
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, LongTable, TableStyle, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
import fitz

P=Path('projects/2026-electronics-contest/g-buck');R=P/'power-explainer-r7-v1';BASE=P/'bluepill-carrier-r7'
for d in ['results/figures','results/data','references','downloads']:(R/d).mkdir(parents=True,exist_ok=True)
fontpath=subprocess.check_output(['fc-match','-f','%{file}','Noto Sans CJK SC'],text=True).strip()
font=FontProperties(fname=fontpath)
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':14})
BLUE='#174C73';GREEN='#167D68';RED='#B34D35';PALE='#EAF2F8'
def label(ax,x,y,s,size=16,color=BLUE,ha='center'):
    ax.text(x,y,s,ha=ha,va='center',fontsize=size,fontproperties=font,color=color)
def box(ax,x,y,w,h,s,color=BLUE,fill=PALE,size=16):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.03,rounding_size=0.12',edgecolor=color,facecolor=fill,lw=1.7))
    label(ax,x+w/2,y+h/2,s,size,color)
def arrow(ax,a,b,color=GREEN):
    ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'-|>','color':color,'lw':2,'mutation_scale':16})
def save(fig,name):
    fig.savefig(R/'results/figures'/name,dpi=190,bbox_inches='tight',facecolor='white');plt.close(fig)

# 1. Physical energy path and distinct command path; auxiliary input really follows RS1.
fig,ax=plt.subplots(figsize=(12,6));ax.set(xlim=(0,12),ylim=(0,6));ax.axis('off')
box(ax,.1,4.3,2.2,1.1,'15～25V输入\nF1、RS1')
box(ax,3.1,4.3,2.5,1.1,'U1同步Buck\nL1、C5/C6')
box(ax,6.5,4.3,2.1,1.1,'RS2\n输出采样')
box(ax,9.5,4.3,2.2,1.1,'OUT+\n电阻负载')
for a,b in [((2.3,4.85),(3.1,4.85)),((5.6,4.85),(6.5,4.85)),((8.6,4.85),(9.5,4.85))]:arrow(ax,a,b)
label(ax,6.05,5.55,'VREG',15);label(ax,6,3.9,'以上是主功率板上的能量通路',15)
box(ax,.2,1.7,2.3,1.1,'独立辅助板\n3.3V供电')
box(ax,3.2,.2,3.0,1.15,'主控底板＋可拔核心板\n按键、显示、测量处理',size=14)
box(ax,6.8,1.7,4.4,1.15,'主功率板内：DAC＋双运放\n电压设定、模拟恒流环')
ax.plot([1.2,1.2],[4.3,2.8],color=GREEN,lw=2);arrow(ax,(1.2,3.2),(1.2,2.8))
arrow(ax,(2.5,2.25),(3.2,.8));label(ax,2.8,1.8,'供电',13)
arrow(ax,(6.2,.8),(8.1,1.7));label(ax,7.7,.65,'I2C设定',14)
arrow(ax,(9,2.85),(4.4,4.3),RED);label(ax,8.3,3.45,'给FB的模拟控制',14,RED)
label(ax,6,5.9,'先分清：能量通路、设定命令、自动调节',19)
save(fig,'01_system.png')

# 2. States as deliberately simplified paths (not a substitute wiring diagram).
fig,ax=plt.subplots(figsize=(12,5.6));ax.set(xlim=(0,12),ylim=(0,5.6));ax.axis('off')
label(ax,6,5.25,'U1内的两个开关轮流工作，L1电流保持原方向',19)
for y,title,left,middle in [(3.45,'状态A：高侧导通、低侧关断','输入VIN_SYS','内部高侧MOS'),(1.15,'状态B：高侧关断、低侧续流','公共GND','内部低侧MOS')]:
    label(ax,.25,y+1.05,title,16,ha='left')
    for x,w,s in [(0.2,2.2,left),(3.05,2.6,middle),(6.3,2.05,'SW → L1'),(9,2.65,'VREG → RS2\n→负载→GND')]:box(ax,x,y,w,.8,s,size=15)
    for a,b in [((2.4,y+.4),(3.05,y+.4)),((5.65,y+.4),(6.3,y+.4)),((8.35,y+.4),(9,y+.4))]:arrow(ax,a,b,RED)
    label(ax,6,y-.32,'电感电流上升：V_L约为VIN_SYS − VREG' if y>2 else '电感电流下降：V_L约为−VREG',15)
label(ax,6,.1,'教学简图：省略电容支路、开关死区和轻载特殊状态；D1/D2不在功率续流通路中。',13)
save(fig,'02_buck_states.png')

# 3. Control connections, precise polarity/direction indicated in labels.
fig,ax=plt.subplots(figsize=(12,6));ax.set(xlim=(0,12),ylim=(0,6));ax.axis('off')
label(ax,6,5.6,'U1看FB是否偏高，不会直接看屏幕设定',19)
box(ax,.2,3.7,2.15,1.05,'VREG\n真实输出信息');box(ax,3.1,3.7,2.2,1.05,'R1=100kΩ')
box(ax,6.1,3.7,1.6,1.05,'FB\n约0.596V');box(ax,8.6,3.7,3.0,1.05,'U1内部控制\n调整开关送能')
for a,b in [((2.35,4.2),(3.1,4.2)),((5.3,4.2),(6.1,4.2)),((7.7,4.2),(8.6,4.2))]:arrow(ax,a,b)
box(ax,5.65,1.6,2.5,1,'R2=5.49kΩ\n下端接GND');arrow(ax,(6.9,3.7),(6.9,2.6))
box(ax,.2,.2,3.5,1.2,'VSET_DRV经R3=56kΩ\n命令越高，输出越低',size=15)
arrow(ax,(3.7,.8),(6.1,3.7),RED)
box(ax,8.7,.2,3.0,1.2,'CC_OUT经D1＋R4\n电流过大时注入FB',size=15)
arrow(ax,(10.2,1.4),(7.7,3.7),RED)
label(ax,6,5.05,'红色箭头是控制信号注入方向，不是负载功率电流',13,RED)
save(fig,'03_feedback.png')

fig,ax=plt.subplots(figsize=(12,5));ax.set(xlim=(0,12),ylim=(0,5));ax.axis('off')
label(ax,6,4.6,'一圈走完：电流偏大，最后被拉回来',19)
items=[(.2,2.9,'实际电流偏大\nRS2压差增大'),(4.2,2.9,'U2输出升高\nISENSE升高'),(8.2,2.9,'U5A输出升高\nCC_OUT升高'),(8.2,.8,'D1介入、FB注入增加\nU1减少送能'),(4.2,.8,'输出电压下降'),(.2,.8,'同一电阻下\n电流下降')]
for x,y,s in items:box(ax,x,y,3.5,1.05,s,size=15)
for a,b in [((3.7,3.425),(4.2,3.425)),((7.7,3.425),(8.2,3.425)),((9.95,2.9),(9.95,1.85)),((8.2,1.325),(7.7,1.325)),((4.2,1.325),(3.7,1.325)),((1.95,1.85),(1.95,2.9))]:arrow(ax,a,b)
label(ax,6,.23,'当前参考：DAC_I约0.95V → 恒流目标约0.95A；比较与补偿在主板模拟电路内完成。',13)
save(fig,'04_current_loop.png')

fig,ax=plt.subplots(figsize=(10,5.1));vset=10
for limit,color,style in [(1,BLUE,'-'),(.95,RED,'--')]:
    ax.plot([0,limit,limit],[vset,vset,0],style,color=color,lw=2.3,label=f'电流上限 {limit:g}A')
ax.set(xlim=(0,1.28),ylim=(0,11),xlabel='输出电流 / A',ylabel='输出电压 / V')
for x,y,s in [(.5,10,'20Ω：约10V / 0.5A'),(.95,7.6,'8Ω：约7.60V / 0.95A'),(.95,4.75,'5Ω：约4.75V / 0.95A')]:
    ax.plot(x,y,'o',color=GREEN);ax.annotate(s,(x,y),xytext=(-195,-22 if y>9 else 8),textcoords='offset points',fontproperties=font,fontsize=12,arrowprops={'arrowstyle':'-','color':GREEN})
ax.set_title('理想静态输出特性：水平段恒压，竖直段恒流',fontproperties=font,pad=14)
ax.grid(alpha=.2);ax.legend(prop=font,loc='lower left');save(fig,'05_cv_cc.png')

# Arithmetic checks are not dynamic or transistor-level simulations.
fb=.596;r1=100000;r2=5490;r3=56000;rs=.05;gain=20;switch=400000;L=22e-6
offset=fb*(1+r1/r2+r1/r3);slope=r1/r3
calc={'kind':'algebra_and_ideal_CCM_examples_only_not_hardware_or_dynamic_simulation','VFB_assumed_V':fb,'VREG_offset_V':offset,'VREG_gain_per_VSET':-slope,
 'VSET_for_VREG_V':{str(v):(offset-v)/slope for v in [10,8,7]},'VSET_for_10V_load_at_0p5A_V':(offset-10.025)/slope,
 'ISENSE_V_per_A':gain*rs,'DAC_A_LSB_V':2.048*2/4096,'DAC_B_LSB_V':2.048/4096,
 'integrator_R12_C14_ms':{str(c):100000*c*1e-6 for c in [220,160,120]},
 'inductor_ripple_25V_to_10V_A':10*(1-10/25)/(L*switch),
 'first_peak_estimates_A':{'VREG10V_to8ohm':10/(8+rs),'0p95A_8_to5ohm':.95*(8+rs)/(5+rs),'1A_8_to5ohm':(8+rs)/(5+rs)},
 'efficiency_example_25V_8ohm_1A_85pct_input_A':8/.85/25}
assert abs(calc['VSET_for_VREG_V']['7']-3.089)<.001
assert abs(calc['ISENSE_V_per_A']-1)<1e-12
assert abs(calc['first_peak_estimates_A']['0p95A_8_to5ohm']-1.514)<.001
assert calc['integrator_R12_C14_ms']=={'220':22.,'160':16.,'120':12.}
(R/'results/data/arithmetic_checks.json').write_text(json.dumps(calc,ensure_ascii=False,indent=2))
sources=[BASE/'schematic/pro/GBUCK_System_R7/sch/Mainboard/Mainboard_6_Blocks.esch2',BASE/'schematic/System_BOM_R7.csv',P/'aux-posts-r3/references/generated/GBUCK_Main_R3/results/data/expected_mainboard_pins.json',P/'rev-b/references/G题要求摘录.txt',P/'modular-v1-1/reports/C14偏压与7V余量补充核对.md']
manifest={'design_baseline':'3c3574c R7','documentation_only':True,'native_ERC_new_run':False,'hardware_tests':False,'sources':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]}
(R/'references/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
pins=json.loads(sources[2].read_text());assert pins['U1']=={'3':'VIN_SYS','1':'GND','5':'EN_A','4':'FB','2':'SW','6':'BOOT'}
assert pins['C5']['1']==pins['C6']['1']==pins['RS2']['1']=='VREG'
assert pins['D1']['1']=='CC_OUT' and pins['D1']['3']=='CC_K' and pins['D2']['1']=='I_ERR'
assert pins['U5']['3']=='I_FILT' and pins['U5']['2']=='I_ERR' and pins['U5']['7']=='VSET_DRV'
main=[x for x in csv.DictReader(sources[1].open(encoding='utf-8-sig')) if x['板']=='Mainboard'];assert len(main)==45
with (R/'results/data/Mainboard_BOM_Reference_R7.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=main[0]);w.writeheader();w.writerows(main)

# One Markdown source -> Word and PDF. No browser/Office conversion is claimed.
md=R/'reports/主功率电路从零讲解_R7.md';lines=md.read_text().splitlines()
doc=Document();sec=doc.sections[0];sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.7)
normal=doc.styles['Normal'];normal.font.name='Noto Sans CJK SC';normal.font.size=Pt(10.5);normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.25
for name in ['Title','Heading 1','Heading 2','Heading 3']:
    style=doc.styles[name];style.font.name='Noto Sans CJK SC';style._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');style.font.color.rgb=RGBColor.from_string('174C73')
foot=sec.footer.paragraphs[0];foot.alignment=1;foot.add_run('G题主功率电路讲解 · R7 · ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
styles={'body':ParagraphStyle('body',fontName='STSong-Light',fontSize=10.5,leading=17,spaceAfter=7,wordWrap='CJK'),
 'title':ParagraphStyle('title',fontName='STSong-Light',fontSize=21,leading=30,spaceAfter=17,textColor=colors.HexColor(BLUE),wordWrap='CJK'),
 'h1':ParagraphStyle('h1',fontName='STSong-Light',fontSize=15,leading=21,spaceBefore=12,spaceAfter=8,keepWithNext=True,textColor=colors.HexColor(BLUE),wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='STSong-Light',fontSize=12,leading=18,spaceBefore=8,spaceAfter=6,keepWithNext=True,textColor=colors.HexColor(BLUE),wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='STSong-Light',fontSize=9,leading=13,wordWrap='CJK'),
 'caption':ParagraphStyle('caption',fontName='STSong-Light',fontSize=9,leading=14,spaceAfter=9,alignment=TA_CENTER,wordWrap='CJK')}
story=[];pagew,pageh=A4;usable=pagew-88
def plain(s):return s.replace('**','').replace('`','')
def markup(s):
    s=html.escape(s);s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s);return s.replace('`','')
def wrun(p,s):
    for n,c in enumerate(re.split(r'\*\*(.*?)\*\*',s)):
        run=p.add_run(c.replace('`',''));run.bold=n%2==1
i=0;table_count=0;image_count=0
while i<len(lines):
    line=lines[i].strip();i+=1
    if not line:continue
    if line.startswith('|'):
        data=[line];
        while i<len(lines) and lines[i].strip().startswith('|'):data.append(lines[i].strip());i+=1
        rows=[[plain(c.strip()) for c in x.strip('|').split('|')] for x in data if not re.match(r'^\|[\s:|\-]+\|$',x)]
        n=len(rows[0]);table=doc.add_table(rows=1,cols=n);table.style='Table Grid';table_count+=1
        for j,t in enumerate(rows[0]):table.rows[0].cells[j].text=t
        for rr in rows[1:]:
            cells=table.add_row().cells
            for j,t in enumerate(rr):cells[j].text=t
        for j,row in enumerate(table.rows):
            trpr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
            if j==0:repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(3)
                    for run in p.runs:run.font.size=Pt(9);run.bold=j==0
        doc.add_paragraph()
        pdfrows=[[Paragraph(markup(t),styles['cell']) for t in rr] for rr in rows]
        weights=([.2,.39,.41] if n==3 else [.2,.2,.3,.3] if n==4 else [1/n]*n)
        t=LongTable(pdfrows,colWidths=[usable*w for w in weights],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6EEF5')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#9FB3C0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,9)]);continue
    image_match=re.match(r'!\[(.*?)\]\((.*?)\)',line)
    if image_match:
        caption,path=image_match.groups();path=(md.parent/path).resolve();image_count+=1
        doc.add_picture(str(path),width=Inches(6.45));p=doc.add_paragraph(caption);p.alignment=1
        iw,ih=ImageReader(str(path)).getSize();im=Image(str(path),width=usable,height=usable*ih/iw)
        story.append(KeepTogether([im,Paragraph(markup(caption)+'（教学示意，非实测）',styles['caption'])]));continue
    if line.startswith('#'):
        level=len(line)-len(line.lstrip('#'));text=line[level:].strip();doc.add_heading(plain(text),0 if level==1 else level-1)
        story.append(Paragraph(markup(text),styles['title' if level==1 else 'h1' if level==2 else 'h2']));continue
    p=doc.add_paragraph();wrun(p,line);story.append(Paragraph(markup(line),styles['body']))
name='G_Buck_Mainboard_Explained_R7';word=R/'reports'/(name+'.docx');pdf=R/'reports'/(name+'.pdf')
doc.save(word)
def footer(canvas,d):
    canvas.saveState();canvas.setFont('STSong-Light',8);canvas.setFillColor(colors.HexColor('#587284'));canvas.drawString(44,25,'G题主功率电路 · R7教学说明 · 非实测验收报告');canvas.drawRightString(pagew-44,25,str(d.page));canvas.restoreState()
SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=42,bottomMargin=43,title='G题主功率电路从零讲解 R7',author='G题项目文档').build(story,onFirstPage=footer,onLaterPages=footer)
with fitz.open(pdf) as pp:
    texts=[p.get_text() for p in pp];pages=len(pp)
    assert pages>=10 and all(len(t.strip())>30 for t in texts)
    joined=''.join(texts);assert '恒流' in joined and 'VREG' in joined and '0.95' in joined
    for f in (R/'results/figures').glob('PDF_Page_*.png'):f.unlink()
    for n in [0, min(3,pages-1),pages-1]:pp[n].get_pixmap(matrix=fitz.Matrix(1.1,1.1)).save(R/'results/figures'/f'PDF_Page_{n+1:02d}.png')
with zipfile.ZipFile(word) as z:assert z.testzip() is None;assert len([x for x in z.namelist() if x.startswith('word/media/')])==5
validation={'status':'PASS','baseline':'3c3574c R7','docx_container_valid':True,'pdf_pages':pages,'markdown_tables':table_count,'teaching_figures':image_count,'arithmetic_assertions_passed':True,'selected_pin_topology_assertions_passed':True,'PDF_has_extractable_Chinese':True,'native_ERC_or_hardware_test':False,'schematic_BOM_firmware_models_modified':False}
(R/'results/data/document_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2))
with zipfile.ZipFile(R/'downloads/G_Buck_Mainboard_Explained_R7_Package.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in [word,pdf]:z.write(f,f.name)
    z.write(md,str(md.relative_to(R)))
    if (R/'README.md').exists():z.write(R/'README.md','README.md')
    for d in ['results/data','results/figures','references','tools']:
        for f in sorted((R/d).rglob('*')):
            if f.is_file():z.write(f,str(f.relative_to(R)))
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(R.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print(json.dumps(validation,ensure_ascii=False,indent=2))
