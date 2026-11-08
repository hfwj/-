from pathlib import Path
import json,csv,shutil,zipfile,hashlib
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
P=Path('projects/2026-electronics-contest/g-buck');R=P/'partition-r5';B=P/'self-aux-r4';project=R/'schematic/pro/GBUCK_System_R5'
rows=list(csv.DictReader((R/'schematic/System_BOM_R5.csv').open(encoding='utf-8-sig')));selected=[r for r in rows if r['板'] in ['Control','Auxiliary']];assert len(rows)==81 and len(selected)==36
expected={b:json.loads((R/'references/generated'/b/'results/data/expected_mainboard_pins.json').read_text()) for b in ['Control','Auxiliary']}
main=json.loads((P/'aux-posts-r3/references/generated/GBUCK_Main_R3/results/data/expected_mainboard_pins.json').read_text());expected['Mainboard']=main
pins=[{'板':b,'位号':r,'脚号':n,'网络':v} for b,rr in expected.items() for r,nn in rr.items() for n,v in nn.items()];assert len(pins)==291
external=list(csv.DictReader((B/'results/data/External_Connections_R4.csv').open(encoding='utf-8-sig')))
for r in external:
 a,b=r['起点接线柱'],r['终点接线柱'];x,y=r['起点板'],r['终点板']
 if '.' in a:
  ar,an=a.split('.');br,bn=b.split('.');assert expected[x][ar][an]==expected[y][br][bn]==r['网络']
 else:assert set(expected[x][a].values())==set(expected[y][b].values())=={r['网络']}
blocks=[]
for b in ['Control','Auxiliary']:
 d=json.loads((R/'results/data'/f'{b}_blocks.json').read_text())
 for z in d['zones']:blocks.append({'板':b,'区号':z['number'],'功能':z['title'],'位号':' '.join(r for r,c in d['components'].items() if c['zone']==z['number'])})
groups={}
for r in selected:
 key=tuple(r[k] for k in ['厂家型号','立创料号','推荐规格','封装','SMT库别'])
 if key not in groups:groups[key]={'位号':[],'数量':0,**{k:r[k] for k in ['厂家型号','立创料号','推荐规格','封装','SMT库别']}}
 groups[key]['位号'].append(r['板']+'.'+r['位号']);groups[key]['数量']+=1
for g in groups.values():g['位号']=' '.join(g['位号'])
def csvwrite(file,data):
 with file.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=data[0].keys(),lineterminator='\n');w.writeheader();w.writerows(data)
csvwrite(R/'schematic/Control_BOM_R5.csv',[r for r in selected if r['板']=='Control']);csvwrite(R/'schematic/Auxiliary_BOM_R5.csv',[r for r in selected if r['板']=='Auxiliary']);csvwrite(R/'schematic/Two_Boards_BOM_Grouped.csv',list(groups.values()));csvwrite(R/'results/data/All_Pins_R5.csv',pins);csvwrite(R/'results/data/External_Connections_R5.csv',external)
wb=Workbook();wb.remove(wb.active)
for title,data in [('主控板25件',[r for r in selected if r['板']=='Control']),('辅助板11件',[r for r in selected if r['板']=='Auxiliary']),('两板采购汇总',list(groups.values())),('功能分区',blocks),('逐引脚表',pins),('板间接线',external),('全系统81件',rows)]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='234B61')
 for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(12,max(len(str(c.value or '')) for c in col)*1.1))
 for rr in ws:
  for c in rr:c.alignment=Alignment(vertical='top',wrap_text=True)
 for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=60
wb.save(R/'schematic/Control_Auxiliary_BOM_R5.xlsx')
for source,target in [('r5_schema.json','schema_check.json'),('r5_viewer.json','viewer_check.json'),('r5_browser.json','browser_check.json')]:shutil.copy('/tmp/'+source,R/'results/data'/target)
for name in ['Control_Blocks','Auxiliary_Blocks','Mainboard_6_Blocks']:shutil.copy('/tmp/R5_'+name+'.png',R/'schematic/previews'/('Pro_Viewer_'+name+'.png'))
schema=json.loads((R/'results/data/schema_check.json').read_text());view=json.loads((R/'results/data/viewer_check.json').read_text());browser=json.loads((R/'results/data/browser_check.json').read_text());assert schema['valid'] and not browser['errors']
for r in view['results']:assert not r['report']['badLines'] and not r['report']['unknownTypes'] and r['report']['placeholders']==0 and not r['diagnostics']
report='''# R5：主控板六区、辅助降压板三区原理图

2026-11-08。工程格式为嘉立创EDA专业版文件夹式`.eprj3`。本次按用户确认保留通孔件，以“贴片＋插件由工厂焊接”为装配目标，不再要求全部器件为贴片封装；具体代焊能力仍以料号匹配及订单审核为准。

## 分区

主控板（独立PCB，25件/116脚）：01供电输入与去耦；02 MCU最小系统、复位与启动；03主板接口与I2C上拉；04 PCD8544液晶接口与去耦；05按键与上拉；06 SWD下载调试。

辅助降压板（独立PCB，11件/34脚）：01输入接线柱与输入滤波；02同步Buck与自举；03 3.3V输出滤波与接线柱。图页右下为拼装核对说明，无新增器件。

框内绿色线为真实导线；跨框同名网络连接；NC明确不接，不得把多个NC连接在一起。分区图不是PCB布局。

## 打开文件

各板独立包：GBUCK_Control_R5_EPRJ3.zip、GBUCK_Auxiliary_R5_EPRJ3.zip。解压后分别打开同名文件夹内的.eprj3文件，必须保留sch目录。全系统包GBUCK_System_R5_EPRJ3.zip含主功率板、主控板、辅助板三张图页/三块独立板，打开GBUCK_System_R5/GBUCK_System_R5.eprj3。

主控六区PDF：schematic/previews/Control/Control_Blocks.pdf；辅助三区PDF：schematic/previews/Auxiliary/Auxiliary_Blocks.pdf。BOM Excel含两板明细、两板采购汇总、分区、全部291脚、板间接线及全系统81件参考页。

## 拼装

主板J4P/J4N→辅助板J1P/J1N，分别为VIN_SYS（15–25V）/GND；辅助板J2P/J2N→主控JPP/JPN，分别为3.3V/GND。每只板凳柱四脚同网。

主控J1↔主板J3采用10芯直通排线：1 +3V3、2 GND、3 SCL、4 SDA、5 VSET_DRV、6 CC_OUT、7 ISENSE、8 VOUT_ADC、9 RUN、10 GND。5/6仅测试，不接主控GPIO驱动；3.3V电源只有辅助板一处供给。SWD.1为电平参考，不将调试器电源与辅源并联。

## 修改影响

比较基准：0f47932/R4自设计辅源原理图和BOM。本次重画主控、辅源的图页布局、符号位置和导线表达，保留两板全部36件150脚的原网络映射（主控含22个NC）。主功率板几何/引脚/网络不变，仅清除接线柱元数据中已取消的统一≥5A采购要求，不改变L1的Isat≥5A要求。全系统81件291脚、27个NC不变。

BOM/器件：主控R16–R21补选10k/1%/0805/C17414；C15–C19及C21补选100nF/50V/X7R/0805/C49678。标称阻容值不变，新增推荐精度/耐压/封装选择，尚未绑定封装。R14/R15补充4.7k/1%/0805参数；C20/C22补充≥10V/0805候选约束，完整料号仍待核。主控J1按主板同类C5665通孔2x5简牛列入建议BOM，脚序不变。

所有板凳柱取消统一≥5A采购要求，按各路连续电流、已知瞬态、保护和机械要求核定；具体厂家型号、孔距/孔径仍待选。按键、液晶接口、SWD等未确定完整型号的项目如实保留待核状态，不能把此BOM视为全部料号已完成采购匹配。JLCD仅为液晶接口，PCD8544成品液晶模块本体不在此接口BOM项内部。

本次原理图分区不要求调整已完成PCB（当前尚无PCB）；实际PCB应按噪声/电流路径布置，不必照抄图页框位置。补充推荐封装需在后续PCB阶段绑定并核对引脚/焊盘映射。

模型/固件：无改动，无新增动态仿真或实测。辅源0.3A目标、偏压降容、启动/温升/纹波、主板7V高端余量和瞬时电流结论均沿用R4，不能由静态连线结果推导其已验收。

## 检查

实际专业版符号/导线网络核对：主控25件116脚108段导线PASS；辅助11件34脚39段导线PASS。与R4逐脚对照一致；四条板间电源线及10针排线映射一致。官方Schema校验通过；官方只读查看器三张图页0坏行、0未知图元、0占位符、0诊断，Chromium实际加载无页面脚本错误。PDF/PNG分区预览已生成。

上述不等于嘉立创原生编辑器打开/保存或ERC/DRC验证；封装未绑定，PCB未设计，实际代焊和实物未验收，不能直接制板。

## 复现

在仓库根目录运行python projects/2026-electronics-contest/g-buck/partition-r5/tools/build_partition_r5.py；SVG预览在schematic/previews中。正式交付为schematic/pro目录中的专业版工程，references/generated中的标准版JSON仅为转换输入与核对记录。
'''
(R/'reports/分区与修改影响.md').write_text(report);(project/'打开与分区说明.md').write_text(report)
readme='''# R5：主控板六区＋辅助降压板三区

[主控板eprj3工程](downloads/GBUCK_Control_R5_EPRJ3.zip) · [辅助板eprj3工程](downloads/GBUCK_Auxiliary_R5_EPRJ3.zip) · [两板BOM Excel](schematic/Control_Auxiliary_BOM_R5.xlsx) · [三板完整工程](downloads/GBUCK_System_R5_EPRJ3.zip)

[主控六区PDF](schematic/previews/Control/Control_Blocks.pdf) · [辅助三区PDF](schematic/previews/Auxiliary/Auxiliary_Blocks.pdf) · [修改与接线说明](reports/分区与修改影响.md)

两板仍独立制作，共36件150脚；全系统81件291脚。分区内使用实际导线，跨区同名网络相连。保留全部引脚网络及标称值、板间接口和固件/模型。BOM补全部分主控0805阻容建议选型，不代表封装已绑定。

按用户确认保留通孔接口和板凳柱，由工厂贴片＋插件焊接，是否可代焊须按实际料号审核；部分器件型号/机械图仍待核实。取消接线柱统一≥5A采购要求，L1的Isat≥5A不变。

解压各包，打开对应文件夹内.eprj3，保留sch目录。官方格式/查看器和静态网络核对通过；未做原生编辑保存/ERC/DRC、PCB或实测，不能直接制板。
''';(R/'README.md').write_text(readme)
# Two standalone board projects accompany the combined project, each with exactly one index.
for b in ['Control','Auxiliary']:
 src=R/'references/generated'/b/'schematic/pro'/('GBUCK_'+b+'_R5');dst=R/'schematic/pro'/('GBUCK_'+b+'_R5');shutil.copytree(src,dst,dirs_exist_ok=True);(dst/'打开与分区说明.md').write_text(report)
 with zipfile.ZipFile(R/'downloads'/('GBUCK_'+b+'_R5_EPRJ3.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(dst.rglob('*')):
   if f.is_file():z.write(f,str(f.relative_to(dst.parent)))
  z.write(R/'schematic'/('Control_BOM_R5.csv' if b=='Control' else 'Auxiliary_BOM_R5.csv'),'BOM.csv');z.write(R/'schematic/Control_Auxiliary_BOM_R5.xlsx','Control_Auxiliary_BOM_R5.xlsx');z.write(R/'schematic/previews'/b/(b+'_Blocks.pdf'),b+'_Blocks.pdf');z.write(R/'results/data'/f'{b}_connectivity.json','checks/connectivity.json')
with zipfile.ZipFile(R/'downloads/GBUCK_System_R5_EPRJ3.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(project.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(project.parent)))
 z.write(R/'schematic/Control_Auxiliary_BOM_R5.xlsx','BOM/Control_Auxiliary_BOM_R5.xlsx');z.write(R/'schematic/System_BOM_R5.csv','BOM/System_BOM_R5.csv')
 for b in ['Control','Auxiliary']:z.write(R/'schematic/previews'/b/(b+'_Blocks.pdf'),'PDF/'+b+'_Blocks.pdf')
 for f in (R/'results/data').glob('*'):
  if f.is_file():z.write(f,'checks/'+f.name)
for f in (R/'downloads').glob('*.zip'):
 with zipfile.ZipFile(f) as z:assert z.testzip() is None
(R/'results/data/assembly_check.json').write_text(json.dumps({'baseline':'0f47932 R4','total_components':81,'total_pins':291,'control':{'components':25,'pins':116,'zones':6},'auxiliary':{'components':11,'pins':34,'zones':3},'pin_maps_unchanged':True,'external_power_links_unchanged':4,'IDC_pins_unchanged':10,'native_editor_erc':False,'PCB':False,'footprints_bound':False,'hardware_test':False},ensure_ascii=False,indent=2))
f=Path('AGENTS.md');s=f.read_text();a=s.index('## Wiring connection and assembly preferences');b=s.index('## EDA delivery format preference',a);s=s[:a]+'''## Wiring connection and assembly preferences

Latest explicit user clarification (2026-11-08): “保留通孔件，工厂全部焊接（推荐）” in response to whether to retain bench solder posts and shrouded headers for JLC mixed SMT + through-hole assembly. This supersedes the earlier requirement for every board-mounted part to be SMT. Keep SMD circuitry and suitable through-hole power clip posts, signal headers, buttons and connectors; the goal is factory-completed soldering. Verify actual part numbers and order-specific assembly support before saying every part can be factory assembled. Do not infer that soldering includes firmware loading, inter-board cable assembly, or functional commissioning. An SMT part need not be in the Basic library; never substitute library classification for assembly capability.

The former >=5A procurement target for bench posts remains cancelled. Select ratings for each rail's continuous current, transients, fault protection, thermal derating, voltage and clip forces; do not apply a fixed 5A threshold to all power posts. This does not change the power inductor L1's separate Isat>=5A requirement. System input remains15–25V; auxiliary output3.3V. Do not invent part numbers, package dimensions or assembly acceptance. Preserve historical designs and document real BOM, pin and footprint impacts.

'''+s[b:];f.write_text(s)
f=Path('README.md');s=f.read_text();s=s if '2026-11-08：[R5主控六区' in s else s.replace('## 项目目录\n','## 项目目录\n\n2026-11-08：[R5主控六区＋辅助降压三区原理图及BOM](projects/2026-electronics-contest/g-buck/partition-r5/README.md) · [eprj3完整工程](projects/2026-electronics-contest/g-buck/partition-r5/downloads/GBUCK_System_R5_EPRJ3.zip)。两板36件150脚，重画分区及实际连线，保留R4网络/标称值；补全部分0805建议选型，固件/模型不改。用户确认保留通孔件，由工厂贴片＋插件焊接，替代此前全SMT要求；实际料号/订单审核、封装/PCB/实测仍待完成。\n',1)
s=s.replace('装配要求更新（2026-11-08）：后续板载元件全部采用可回流焊的SMT封装，包括电源夹持触点、信号连接器、电解电容、按键和调试接口；取消此前接线柱统一≥5A要求，按各路电流及故障条件选型，电压/间距另按实际电源核对。现有R4仍含通孔件，尚未按本要求完成硬件改版。本次相对0f47932仅更新设计约定，原理图、BOM、PCB、模型和固件未修改。','装配要求更新（2026-11-08，最新确认）：保留适合的通孔件，目标由工厂完成“贴片＋插件”焊接；不再要求所有元件均为SMT。取消接线柱统一≥5A门槛，按各路负载及保护选型；工厂能否焊接须逐料号/订单审核。');f.write_text(s)
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(R.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print('R5 package complete: two independent board archives, combined archive, 36-item BOM + 81-item reference')
