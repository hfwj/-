from pathlib import Path
import csv,json,hashlib,zipfile
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
P=Path('projects/2026-electronics-contest/g-buck/mainboard-v1');O=P/'reports/bom-r2-bench-posts';O.mkdir(parents=True,exist_ok=True)
base=P/'reports/manual-drawing-2026-11-08'
rows=list(csv.DictReader((base/'BOM_ByReference.csv').open(encoding='utf-8-sig')))
rows=[r for r in rows if r['位号'] not in ('J1','J2')]
for r in rows:
 if r['位号'] in ('R6','R9','R12'):
  r.update({'厂家型号':'0603WAF1003T5E','立创料号':'C25803','封装':'0603','SMT库别':'基础库（官网已核实）','推荐规格':'100kΩ ±1% 100mW 75V','来源':'https://jlcpcb.com/partdetail/C25803','备注':'替代旧推荐0805 C17407（现官网为扩展库）；阻值/精度不变，封装改0603，最大3.3V时功耗约0.109mW'})
 if r['位号']=='C14':r['SMT库别']='库别待核实（不计基础库）';r['备注']='保留0805/50V选择；当前未核实官网Basic状态；需核对直流偏压有效容值'
for ref,zone,net,old in [('J1P',1,'RAW+','J1.1'),('J1N',1,'GND','J1.2'),('J2P',2,'OUT+','J2.1'),('J2N',2,'GND','J2.2')]:
 rows.append(dict(zip(rows[0],['']*len(rows[0]))));rows[-1].update({'功能区':str(zone),'位号':ref,'原标称':old,'推荐规格':'单极四脚板凳式焊接接线柱，设计采购要求≥5A','厂家型号':'待定：四脚同体导通、横梁可供鳄鱼夹夹持','立创料号':'','封装':'THT四脚，孔距/孔径/高度待厂家尺寸图','SMT库别':'非SMT/通孔手焊','备注':f'替代{old}；四焊脚均接{net}；不得按四路连接器使用；未核实厂家额定电流，不能直接下单','核对日期':'2026-11-08','来源':''})
rows.sort(key=lambda r:(int(r['功能区']),r['位号']))
assert len(rows)==44 and len(set(r['位号'] for r in rows))==44
basic=[r for r in rows if r['SMT库别']=='基础库（官网已核实）'];assert len(basic)==17
# Only connector pin mapping changes. The old native schematic is deliberately archived unchanged.
pins=list(csv.DictReader((P/'results/data/Pin_Net_Table.csv').open(encoding='utf-8-sig')))
pins=[r for r in pins if r['Reference'] not in ('J1','J2')]
for ref,zone,net in [('J1P',1,'RAW+'),('J1N',1,'GND'),('J2P',2,'OUT+'),('J2N',2,'GND')]:
 for pin in range(1,5):pins.append({'Block':str(zone),'Reference':ref,'Part':'四脚同体导通接线柱（型号待定）','Pin':str(pin),'Net':net})
assert len(pins)==135
# numbering 1..4 is a proposed symbol convention until the mechanical part is fixed.
groups={}
for r in rows:
 key=tuple(r[k] for k in ['厂家型号','立创料号','推荐规格','封装','SMT库别'])
 if key not in groups:groups[key]={'位号':[],'数量':0,**{k:r[k] for k in ['厂家型号','立创料号','推荐规格','封装','SMT库别','来源']},'备注':r['备注']}
 groups[key]['位号'].append(r['位号']);groups[key]['数量']+=1
for g in groups.values():g['位号']=' '.join(g['位号'])
# connector group remarks must not incorrectly assign every pole to RAW+.
for g in groups.values():
 if 'J1P' in g['位号']:g['备注']='共4只、每只单极；J1P→RAW+，J1N→GND，J2P→OUT+，J2N→GND；每只四脚同网。厂家/电流额定/尺寸待核实。'
grouped=list(groups.values())
def csvwrite(name,data):
 with (O/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=data[0].keys(),lineterminator='\n');w.writeheader();w.writerows(data)
csvwrite('BOM_ByReference_R2.csv',rows);csvwrite('BOM_Grouped_R2.csv',grouped);csvwrite('Proposed_Pin_Map_R2.csv',pins)
notes=[
'基准：4c03a35仓库中的42件手绘BOM（e09c173生成）。本版为主功率＋CC合板BOM R2，日期2026-11-08。',
'器件数量：44件。J1/J2两只双位绿色螺丝端子删除，改成J1P、J1N、J2P、J2N四只单极板凳式焊接接线柱。每只拟选四脚同体导通款；1–4脚编号仅为拟用符号约定，实物及厂家编号尚待核对。',
'端子网络：J1P四脚→RAW+；J1N四脚→GND；J2P四脚→OUT+；J2N四脚→GND。切勿把输入正极接在FUSED/VIN_SYS以绕过保险丝和采样电阻。',
'接线柱采购条件：裸露横梁供鳄鱼夹夹持，通孔焊接；明确额定电流≥5A，厂家材质/镀层、尺寸、焊接工艺需复核。采购型号、立创料号、孔距、孔径未查实，列为待定，禁止用PCB-1之类泛称直接决定封装。该清单不是全料号可下单BOM。',
'接口范围：J3主控10针接口、J4辅助供电2针接口保留；仅本版电源输入/输出采用板凳式接线柱。主控及辅助电源板本体不在本BOM内。',
'基础库优先：17件已核实官网Basic，共5种料号：C49678×7、C1710×2、C17513×4、C17414×1、C25803×3。官网分类为JLCPCB查询结果，国内嘉立创实际订单、库存、基础库归类须下单前再次确认；不承诺全器件为基础库。',
'R6/R9/R12：旧推荐0805 C17407→0603 C25803；仍为100kΩ/1%，额定功率125→100mW。控制域最高3.3V时约0.109mW，功率余量充足。仅这三只普通100k改0603；R1/R7仍为100kΩ/0.1%/0805。',
'保留R2=5.49kΩ/0.1%、R3=56kΩ/0.1%、R8=10kΩ/0.1%；不为基础库降低采样/反馈精度，也不改成相近标称值。U1–U5、RS1/RS2及其余阻容标称参数不变。',
'C14保留220nF/50V/X7R/0805，C5378当前库别未核实，不再作为基础库候选计数。未直接改小封装以避免增加偏压降容不确定性。',
'C5/C6仍各22µF/25V/X7R/1210，候选C309062；在实际最高输出偏压下两只有效容量合计≥22µF需曲线或带偏压实测确认。L1仍需原厂焊盘图；不能凭外形名称定封装。',
'原理图影响：主电路电气网络/标称阻容值不变，但接口符号由两个2针拆为四个单极4脚，拟用逐脚记录从123变135；旧JSON未重画，不能直接与本BOM配套下板。新版连接表是拟用映射，不是已验证网表。',
'器件/PCB影响：新接线柱须重画符号和专用封装，并调整板边空间、正负极夹持间距与焊盘承力；R6/R9/R12需改0603封装。其它未变选型沿用上一版建议，不等于已完成封装绑定。',
'仿真/固件：不改模型、控制算法或固件。本轮仅静态BOM核对44件、合并数量一致、40只保留器件的网络映射不变；未开展原生ERC/DRC、实测、环路或效率验收。',
'来源：每项目录链接见Excel。已核实Basic：jlcpcb.com/partdetail/C49678、/C17513、/C17414、/C25803；C1710使用完整路径 https://jlcpcb.com/partdetail/2062-CL21B103KBANNNC/C1710。旧C17407当前Extended证据：https://jlcpcb.com/partdetail/uni_royal_uniroyal_elec-C17407/C17407。'
]
zone_names=['输入保护、输入采样与接口','同步Buck主功率与输出','恒压反馈、恒流注入与使能','输出电流/电压采样','DAC电压/电流设定与滤波','CC恒流补偿与设定缓冲']
zones=[{'区域':i,'功能':n,'位号':' '.join(r['位号'] for r in rows if int(r['功能区'])==i),'数量':sum(int(r['功能区'])==i for r in rows)} for i,n in enumerate(zone_names,1)]
wb=Workbook();wb.remove(wb.active)
for title,data in [('按位号BOM',rows),('合并采购BOM',grouped),('仅已核实基础库',basic),('六区划分',zones),('拟用连接映射',pins),('修改及待核对', [{'序号':i,'说明':n} for i,n in enumerate(notes,1)])]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='25485C')
 for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(12,max(len(str(c.value or '')) for c in col)*1.1))
 for row in ws:
  for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
 for i in range(2,ws.max_row+1):ws.row_dimensions[i].height=60 if title!='修改及待核对' else 90
wb.save(O/'Mainboard_BOM_R2.xlsx')
md=['# 主板BOM R2：板凳式接线柱 / SMT基础库优先',*notes,'## 六区划分']+[f"{z['区域']} {z['功能']}：{z['位号']}（{z['数量']}件）" for z in zones]+['## 合并BOM']
for g in grouped:md += [f"{g['位号']} / 数量{g['数量']}：{g['推荐规格']}",f"{g['厂家型号']} | {g['立创料号'] or '待定'} | {g['封装']} | {g['SMT库别']}",g['备注']]
(O/'README.md').write_text('\n\n'.join(md),encoding='utf-8')
d=Document();st=d.styles['Normal'];st.font.name='Microsoft YaHei';st._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');st.font.size=Pt(10)
for line in md:
 if line.startswith('#'):d.add_heading(line.lstrip('# '),0 if line.startswith('# ') else 1)
 else:d.add_paragraph(line)
d.save(O/'Mainboard_BOM_R2.docx')
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));c=canvas.Canvas(str(O/'Mainboard_BOM_R2.pdf'),pagesize=(595.28,841.89));y=790;page=1
for para in md:
 size=14 if para.startswith('#') else 10;line='';lines=[]
 for char in para.lstrip('# '):
  if line and pdfmetrics.stringWidth(line+char,'STSong-Light',size)>499:lines.append(line);line=char
  else:line+=char
 if line:lines.append(line)
 for line in lines:
  if y<55:
   c.setFont('STSong-Light',9);c.drawString(48,28,f'主板BOM R2 / 第{page}页');c.showPage();page+=1;y=790
  c.setFont('STSong-Light',size);c.drawString(48,y,line);y-=size+5
 y-=6
c.setFont('STSong-Light',9);c.drawString(48,28,f'主板BOM R2 / 第{page}页');c.save()
oldpins=list(csv.DictReader((P/'results/data/Pin_Net_Table.csv').open(encoding='utf-8-sig')))
assert [r for r in pins if not r['Reference'].startswith(('J1','J2'))]==[r for r in oldpins if r['Reference'] not in ('J1','J2')]
(O/'validation.json').write_text(json.dumps({'references':44,'grouped_quantity':sum(g['数量'] for g in grouped),'basic_confirmed':17,'proposed_pin_records':135,'retained_components':40,'retained_pin_mapping_unchanged':True,'native_schematic_updated':False,'terminal_part_and_footprint_verified':False,'native_erc':False,'hardware_measurement':False},ensure_ascii=False,indent=2))
(O/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(O.iterdir()) if f.name!='SHA256SUMS.txt'))
print('PASS',len(rows),'refs,',len(pins),'proposed pins,',len(basic),'basic; PDF pages',page)
