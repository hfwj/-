import csv,json,hashlib,zipfile,shutil
from pathlib import Path
from collections import Counter
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import simpleSplit
P=Path('projects/2026-electronics-contest/g-buck/mainboard-v1')
O=P/'reports/manual-drawing-2026-11-08';O.mkdir(parents=True,exist_ok=True)
parts=json.loads((P/'results/data/component_blocks.json').read_text())
zones=['输入保护、输入采样与接口','同步Buck主功率与输出','恒压反馈、恒流注入与使能','输出电流/电压采样','DAC电压/电流设定与滤波','CC恒流补偿与设定缓冲']
# refs, recommended model, code, specification, package, library evidence, notes
G=[
('J1 J2','WJ500V-5.08-2P','C8465','2位接线端子','THT P5.08mm','非SMT/手焊','按原厂机械图；1正极、2GND，勿混用5.00mm'),
('J3','2.54-2*5P简牛 BOOMELE','C5665','带防呆10针连接器','THT 2x5 P2.54mm','非SMT/手焊','核对1脚三角标记和外壳尺寸'),
('J4','2.54mm 1x2直插排针','','2针辅助供电接口','THT 1x2 P2.54mm','非SMT/手焊','参数选型；未指定商城料号；1 VIN_SYS，2 GND'),
('F1','0466002.NRHF','C3105','2A 63V保险丝','1206保险丝','待核实库别','非自恢复保险；不提供精确1A限流'),
('RS1 RS2','RL2512FK-070R05L','C876461','0.05Ω ±1% 1W','2512','待核实库别','电流取样两端用Kelvin引线'),
('U1','TPS54302DDCR','C311983','同步Buck 4.5–28V/3A','SOT-23-THIN6 / DDC','待核实库别','不得用通用SOT23-6直接代替DDC焊盘'),
('U2','INA180A1IDBVR','C122228','电流检测增益20','SOT-23-5 / DBV','待核实库别','必须A1；B1脚序不同，A2增益不同'),
('U3','INA226AIDGSR','C49851','输入电流/电压监测','VSSOP-10 / DGS P0.5mm','待核实库别','不能与MSOP外形想当然互换'),
('U4','MCP4728-E/UN','C108207','四通道DAC','MSOP-10 P0.5mm','扩展库（官网）','C/D通道不用；3.3V供电'),
('U5','MCP6002T-I/SN','C7377','双运放','SOIC-8 3.9mm P1.27mm','扩展库（官网）','原MCP6002-I/SN加T仅卷带包装；同一只IC两个单元'),
('D1 D2','BAT54,215 Nexperia','C85084','单肖特基二极管','SOT-23','待核实库别','1=A，3=K，2=NC；不用BAT54A/C/S'),
('L1','ZD0850-220M','C46956554','22µH ±20% 额定4A Isat5A DCR80mΩ','8.8x8.2mm型号专用焊盘','待核实库别','焊盘尺寸需查原厂图；不能按名称选通用8x8封装'),
('C1','50YXF100MEFC8X11.5','C88728','100µF 50V 铝电解','THT D8x11.5mm P3.5mm','非SMT/手焊','注意极性，1正极、2GND'),
('C2','CL31B106KBHNNNE','C89632','10µF 50V X7R ±10%','1206','扩展库（官网）','输入最高25V，保留50V耐压'),
('C5 C6','CL32B226KAJNNNE','C309062','22µF 25V X7R ±10%','1210','待核实库别','有条件候选：10V偏压下两只合计有效容量需≥22µF；需曲线或实测'),
('C3 C4 C8 C9 C10 C11 C12','CC0805KRX7R9BB104','C49678','100nF 50V X7R ±10%','0805','基础库（官网已核实）','统一7只；C4由16V额定提升50V，标称容值不变'),
('C7 C13','CL21B103KBANNNC','C1710','10nF 50V X7R ±10%','0805','基础库（官网已核实）','输出分压滤波和电流滤波'),
('C14','CL21B224KBFNNNE','C5378','220nF 50V X7R ±10%','0805','基础库候选/待官网复核','不得仅凭第三方历史Basic标记下单；核对有效容值'),
('R1 R7','RT0805BRD07100KL','C122537','100kΩ ±0.1% 1/8W','0805','待核实库别','保留采样/反馈精度，不换1%凑基础库'),
('R2','RT0805BRD075K49L','C865577','5.49kΩ ±0.1% 1/8W','0805','待核实库别','不改5.49k标称值'),
('R3','TC0550B5602T5G','C2989136','56kΩ ±0.1% 1/8W','0805','待核实库别','56k，不能替换为56.2k'),
('R8','RT0805BRD0710KL','C110775','10kΩ ±0.1% 1/8W','0805','待核实库别','保留输出电压采样精度'),
('R4','0805W8F1002T5E','C17414','10kΩ ±1% 1/8W','0805','基础库（官网已核实）','保持原规格'),
('R5 R10 R11 R13','0805W8F1001T5E','C17513','1kΩ ±1% 1/8W','0805','基础库（官网已核实）','保持原标称值'),
('R6 R9 R12','0805W8F1003T5E','C17407','100kΩ ±1% 1/8W','0805','基础库候选/待官网复核','不涉及R1/R7精密100k；R12为补偿电阻')]
rows=[]
for refs,model,code,spec,pkg,status,note in G:
 for ref in refs.split():
  rows.append({'功能区':parts[ref]['zone'],'位号':ref,'原标称':parts[ref]['value'],'推荐规格':spec,'厂家型号':model,'立创料号':code,'封装':pkg,'SMT库别':status,'备注':note,'核对日期':'2026-11-08','来源':('https://jlcpcb.com/partdetail/'+code if code else '')})
assert len(rows)==42 and {r['位号'] for r in rows}==set(parts)
assert sum(len(v['pins']) for v in parts.values())==123
rows.sort(key=lambda r:(r['功能区'],list(parts).index(r['位号'])))
def writecsv(path,data):
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
writecsv(O/'BOM_ByReference.csv',rows)
grouped=[{'位号':r,'数量':len(r.split()),'型号':m,'料号':c,'规格':s,'封装':p,'库别':t,'备注':n,'目录链接':'https://jlcpcb.com/partdetail/'+c if c else ''} for r,m,c,s,p,t,n in G]
writecsv(O/'BOM_Grouped.csv',grouped)
shutil.copy(P/'results/data/Pin_Net_Table.csv',O/'Pin_Net_Table.csv')
counts=Counter(r['SMT库别'] for r in rows)
wb=Workbook();wb.remove(wb.active)
for title,data in [('按位号BOM',rows),('合并采购BOM',grouped),('逐引脚连接',list(csv.DictReader((O/'Pin_Net_Table.csv').open(encoding='utf-8-sig')))),('六功能区',[{'区域':i+1,'功能':name,'器件':' '.join(k for k,v in parts.items() if v['zone']==i+1)} for i,name in enumerate(zones)])]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for cell in ws[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='244761')
 for col in ws.columns:
  letter=col[0].column_letter;ws.column_dimensions[letter].width=min(62,max(12,max(len(str(c.value or '')) for c in col)*1.3))
 for row in ws:
  for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
 for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=48
wb.save(O/'Mainboard_BOM.xlsx')
intro=['基准：fb6e66e 主功率＋CC六区合板，42个器件/123个引脚。供用户在嘉立创EDA手动画图，主控和辅助电源板不在此BOM内。',
'库别以SMT基础库为优先。官网已核实基础库14件；基础库候选4件（C17407三件、C5378一件），未将候选计为已确认。其余保留满足电气要求的型号，分列扩展库、待核实和通孔手焊。库别/库存会变化，下单时按所用嘉立创SMT平台重新筛选。JLCPCB官网标签不能替代国内下单平台当日结果。',
'器件搜索：优先输入C料号，再逐项核对厂家完整型号、封装和脚序。0805/1206/1210/2512均为英制；不要选成公制0805。库中符号存在不代表SMT基础库，也不代表此工程已绑定封装。']
impact=['原理图：不更改连接、脚序、标称阻容值或42件数量；保留原JSON和旧BOM。新增推荐选型文件供手绘。',
'器件/封装：推荐普通阻容0805，采样电阻2512；C2为1206，C5/C6为1210。100nF统一50V，C4原16V提升50V。U5采用带T的卷带包装，同电气型号/同封装。尚未绑定EDA封装或制作PCB；L1、连接器等需核对厂家机械图。',
'模型/固件：无改动，无新增动态仿真或实测。本次完成器件覆盖、数量和引脚表静态核对，不构成原生ERC/DRC、环路稳定或效率验收。']
checks=['电源：输入15–25V；外部辅助板提供稳定3.3V，所有模块共地。J3的5/6脚为模拟信号，不允许主控GPIO推挽驱动。',
'C5/C6需核对直流偏压下有效容量；44µF标称合计不等于有效容量。C14属于3.3V控制域，不能按输出5–7V直接当作其偏压；仍需核对偏压、容差。',
'7V是软件设定范围选项，不是硬件最低工作电压；恒流时输出可低于7V。保留7V设定需实测DAC/运放高端余量。',
'当前结构不保证任意瞬间电流≤1A；缩小C14不能消除输出电容造成的负载阶跃首峰。2A保险丝不能替代精确输出限流。',
'布板：输入电容靠U1 VIN/GND；C4靠BOOT/SW；SW铜区短小，避开FB/I_ERR；反馈从VREG取样。两只采样电阻Kelvin取样；模拟区远离L1和SW，优先连续地平面。这里只给分区建议，不给已验证板框尺寸。',
'最终逐项核对123脚（含5个NC）。NC是明确不接，不是统一接到名为NC的网络。SDA/SCL上拉须核对外部主控板是否已提供，禁止无依据增加或重复上拉。']
D=Document();style=D.styles['Normal'];style.font.name='Microsoft YaHei';style._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');style.font.size=Pt(10)
for sec in D.sections:sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.65)
D.add_heading('G题主板功能分区与BOM手绘指南',0);D.add_paragraph('SMT基础库优先版 | 2026-11-08')
for s in intro:D.add_paragraph(s)
D.add_heading('六区划分',1)
t=D.add_table(rows=1,cols=3);t.style='Table Grid'
for c,v in zip(t.rows[0].cells,['区','功能','位号']):c.text=v
for i,name in enumerate(zones,1):
 cs=t.add_row().cells
 for c,v in zip(cs,[str(i),name,'、'.join(k for k,v in parts.items() if v['zone']==i)]):c.text=v
D.add_paragraph('推荐位置：左侧输入保护；上侧功率路径从输入→U1→L1→RS2→输出；下侧依次采样、DAC和CC。六区仍是一块主板，同名网络跨区相连。')
D.add_heading('与基准比较的影响',1)
for s in impact:D.add_paragraph(s)
D.add_page_break();D.add_heading('合并采购BOM',1);D.add_paragraph('完整逐位号BOM和可筛选库别见配套Excel。以下保留满足电气要求的候选型号；待核实不等于基础库。')
for refs,m,c,s,p,t,n in G:
 D.add_heading(refs+' — '+s,2);D.add_paragraph(f'{m} | {c or "按参数搜索"} | {p} | {t}\n{n}')
D.add_page_break();D.add_heading('按功能区逐引脚连线',1)
for i,name in enumerate(zones,1):
 D.add_heading(f'{i:02d} {name}',2)
 table=D.add_table(rows=1,cols=2);table.style='Table Grid';table.rows[0].cells[0].text='位号 / 型号';table.rows[0].cells[1].text='脚号 → 网络'
 for ref,obj in parts.items():
  if obj['zone']==i:
   cells=table.add_row().cells;cells[0].text=ref+' '+obj['value'];cells[1].text='；'.join(f'{p} → {n}' for p,n in obj['pins'].items())
 D.add_paragraph('')
D.add_heading('手绘与布板核对',1)
for s in checks:D.add_paragraph(s)
D.add_heading('选型来源与证据范围',1)
D.add_paragraph('型号目录核对日期：2026-11-08。逐条目录链接在Excel/CSV。基础库已确认：C49678、C1710、C17513、C17414。C17407/C5378仅有第三方Basic记录且官网页面未成功复核。其余未明确写官网库别的条目不应按基础库计算。')
D.add_paragraph('基础库查询：https://jlcpcb.com/parts/basic_parts\n第三方交叉核对：https://lrks.github.io/jlcpcb-economic-parts/\nL1规格来源：https://item.szlcsc.com/49125430.html\n本文件不提供实时价格、库存保证或一键下单承诺。')
D.save(O/'Mainboard_Manual.docx')
# Markdown mirrors all selected data and pin maps; PDF uses the same text, paginated with CJK.
md=['# G题主板功能分区与BOM手绘指南','2026-11-08 / SMT基础库优先版',*intro,'## 修改影响',*impact,'## 六个功能区']
for i,name in enumerate(zones,1):
 md += [f'### {i:02d} {name}']
 for ref,obj in parts.items():
  if obj['zone']==i:md.append(ref+' ['+obj['value']+']：'+'；'.join(f'{p}→{n}' for p,n in obj['pins'].items()))
md+=['## 合并采购BOM']
for r,m,c,s,p,t,n in G:md += [f'{r}（{len(r.split())}件）：{s}',f'{m} / {c or "按参数搜索"} / {p} / {t}',n,('https://jlcpcb.com/partdetail/'+c if c else '')]
md+=['## 手绘与布板核对',*checks,'## 来源','基础库：https://jlcpcb.com/parts/basic_parts','第三方候选记录：https://lrks.github.io/jlcpcb-economic-parts/','L1：https://item.szlcsc.com/49125430.html','完整BOM：Mainboard_BOM.xlsx；连接表：Pin_Net_Table.csv。']
(O/'README.md').write_text('\n\n'.join(md),encoding='utf-8')
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
c=canvas.Canvas(str(O/'Mainboard_Manual.pdf'),pagesize=(595.28,841.89));c.setTitle('G题主板功能分区与BOM手绘指南');y=790;page=1
def wrap_cjk(text,size,width):
 lines=[];line=''
 for char in text:
  if pdfmetrics.stringWidth(line+char,'STSong-Light',size)>width and line:
   lines.append(line);line=char
  else:line+=char
 if line:lines.append(line)
 return lines
for para in md:
 heading=para.startswith('#');text=para.lstrip('# ');size=14 if heading else 10
 for line in wrap_cjk(text,size,499):
  if y<54:
   c.setFont('STSong-Light',9);c.drawString(48,28,f'G题主板 / 2026-11-08 / 第{page}页');c.showPage();page+=1;y=790
  c.setFont('STSong-Light',size);c.drawString(48,y,line);y-=size+5
 y-=6
c.setFont('STSong-Light',9);c.drawString(48,28,f'G题主板 / 2026-11-08 / 第{page}页');c.save()
(O/'validation.json').write_text(json.dumps({'baseline':'fb6e66e','references':len(rows),'pins':123,'confirmed_basic_references':14,'basic_candidate_references':4,'status_counts':dict(counts),'netlist_changed':False,'native_erc':False,'hardware_test':False},ensure_ascii=False,indent=2))
print('Created',O,'PDF pages',page,'counts',dict(counts))
