from pathlib import Path
import json,csv,shutil,hashlib,zipfile
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path('projects/2026-electronics-contest/g-buck/aux-posts-r3');project=R/'schematic/pro/GBUCK_System_R3'
rows=list(csv.DictReader((R/'schematic/System_BOM_R3.csv').open(encoding='utf-8-sig')))
expected={}
for stage in (R/'references/generated').iterdir():
 b={'GBUCK_Main_R3':'Mainboard','GBUCK_Control_R3':'Control','GBUCK_Aux_R3':'Auxiliary'}[stage.name]
 expected[b]=json.loads((stage/'results/data/expected_mainboard_pins.json').read_text())
 shutil.copy(stage/'results/data/pro_connectivity_report.json',R/'results/data'/f'{b}_connectivity.json')
links=[('Mainboard','J4P','Auxiliary','J1P','VIN_SYS','15–25V辅源输入正极'),('Mainboard','J4N','Auxiliary','J1N','GND','辅源输入负极'),('Auxiliary','J2P','Control','JPP','+3V3','辅源3.3V输出正极'),('Auxiliary','J2N','Control','JPN','GND','辅源输出负极')]
external=[]
for src,sr,dst,dr,net,role in links:
 assert set(expected[src][sr].values())==set(expected[dst][dr].values())=={net}
 assert set(expected[src][sr])==set(expected[dst][dr])=={'1','2','3','4'}
 external.append({'起点板':src,'起点接线柱':sr,'终点板':dst,'终点接线柱':dr,'网络':net,'用途':role,'连接方式':'鳄鱼夹导线连接两柱；每柱四焊脚同网，任选横梁夹持位置'})
for n in range(1,11):
 net=expected['Mainboard']['J3'][str(n)];assert expected['Control']['J1'][str(n)]==net
 external.append({'起点板':'Mainboard','起点接线柱':'J3.'+str(n),'终点板':'Control','终点接线柱':'J1.'+str(n),'网络':net,'用途':'保留10芯IDC排线；5/6仅测试，不接主控驱动','连接方式':'同脚号直通；负载电流不走排线'})
pinrows=[{'板':b,'位号':r,'脚号':n,'网络':net} for b,parts in expected.items() for r,pins in parts.items() for n,net in pins.items()]
assert len(pinrows)==277 and len(rows)==75
for name,data in [('External_Connections_R3.csv',external),('All_Pins_R3.csv',pinrows)]:
 with (R/'results/data'/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=data[0].keys(),lineterminator='\n');w.writeheader();w.writerows(data)
wb=Workbook();wb.remove(wb.active)
for title,data in [('全系统BOM',rows),('主板BOM',[r for r in rows if r['板']=='Mainboard']),('主控板BOM',[r for r in rows if r['板']=='Control']),('辅助板BOM',[r for r in rows if r['板']=='Auxiliary']),('板间连接',external),('逐引脚表',pinrows)]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='234B61')
 for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(12,max(len(str(c.value or '')) for c in col)*1.1))
 for row in ws:
  for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
 for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=55
wb.save(R/'schematic/System_BOM_R3.xlsx')
report={'status':'PASS','boards':3,'components':75,'pins':277,'no_connect_pins':27,'auxiliary_power_links_verified':4,'IDC_pin_links_verified':10,'bench_posts_total':12,'new_bench_posts':8,'removed_2pin_power_headers':4,'retained_non_interface_pin_maps_unchanged':True,'native_client_open_save':'NOT TESTED','native_erc_drc':'NOT RUN','physical_post_model_footprint':'TBD','firmware_models':'UNCHANGED'}
(R/'results/data/assembly_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
shutil.copy('/tmp/r3_schema_final.json',R/'results/data/schema_check.json');shutil.copy('/tmp/r3_viewer.json',R/'results/data/viewer_check.json');shutil.copy('/tmp/r3_browser.json',R/'results/data/browser_check.json')
for title in ['Aux_Power','MCU_LCD','Mainboard_6_Blocks']:shutil.copy('/tmp/R3_'+title+'.png',R/'schematic/previews'/(title+'.png'))
notes=['# R3：辅助供电接口改板凳式焊接接线柱','2026-11-08。一个.eprj3工程内含三块独立板：Mainboard（主功率＋CC）、Control（主控显示）、Auxiliary（辅助供电）。三个板子不会合成一块PCB。',
'完整解压GBUCK_System_R3_EPRJ3.zip，在支持文件夹工程的嘉立创EDA专业版中打开GBUCK_System_R3/GBUCK_System_R3.eprj3，必须保留同目录sch文件夹。',
'## 新接口接线',
'主板J4P（VIN_SYS，15–25V）→辅助板J1P；主板J4N（GND）→辅助板J1N。',
'辅助板J2P（+3V3）→主控板JPP；辅助板J2N（GND）→主控板JPN。',
'主控板J1仍用10芯直通排线接主板J3；其中1脚3.3V、2/10脚GND给主板控制部分供电。SCL/SDA、采样和RUN不变；5/6仅预留测试，不能由主控GPIO驱动。',
'每只接线柱只有一个电极，拟选四脚同体导通款，四脚全部接同一网络，不是四路接口。图中1–4脚为符号约定，最终脚号和孔位需按厂家图核对。',
'鳄鱼夹导线用于上述4条外部电源连接；正负极做清晰丝印，15–25V与3.3V分区。只能使用一个3.3V辅助电源，不把独立稳压输出并联。',
'## 影响（比较基准662d5ce主板R2，以及V1.1主控/辅助板）',
'原理图：主板J4改J4P/J4N；辅助板J1改J1P/J1N、J2改J2P/J2N；主控JP改JPP/JPN。四只双针接口变为八只单极四脚柱。原理图实际更新三个板，保留器件的脚号/网络、主功率拓扑、阻容值和所有电压等级不变。',
'数量：主板44→45件/135→141脚；主控24→25件/110→116脚；辅助板3→5件/8→20脚。总计71→75件，253→277脚；新增加8只板凳柱，替换4只双针接口。全系统板凳柱共12只（原输入/输出4只加本次8只）。75件包含1项成品辅源模块M1，不代表其内部器件数量。',
'BOM/PCB：新增接线柱须选型和重画封装，三块板均需调整接口位置、正负极间距和焊盘承力。采购要求≥5A仅为目标，厂家型号/商城料号/额定承流/脚距/孔径未核实；绝不能据通用名称直接制板。信号插座保持，主板基础库选型沿用R2（17件已核实）；主控/辅源非接口器件沿用V1.1，本轮未重新选型或核实SMT库别。',
'辅助模块M1沿用15–25V输入→3.3V输出的成品降压模块定义，输出需满足负载要求（原方案要求≥0.3A）；本轮未确定厂家型号/机械尺寸。图上1/2/3/4为自定义IN+/IN-/OUT+/OUT-端口号，须对应实物丝印。',
'模型/固件：不修改控制、保护模型、算法或固件，未新增动态仿真/实测。软件不得把7V设定下限当作恒流输出下限。现有结构不保证任意瞬间输出电流≤1A。',
'## 核对',
'专业版实际符号/导线网络核对：主板45件141脚、主控25件116脚、辅助5件20脚，全部PASS；总计75件277脚27个NC。4条板间电源连接和10针排线脚序全部一致。',
'官方Schema校验3825条记录通过；官方easyeda/easyeda-viewer解析三个图页，0坏行/0未知图元/0占位符/0诊断。Chromium实际打开三页并截图，无页面脚本错误。只读查看器验证不等于原生编辑器打开/保存或ERC；原生客户端/ERC/DRC、PCB、实物仍未验证。',
'## 文件',
'schematic/pro/GBUCK_System_R3：原生工程；schematic/System_BOM_R3.xlsx：三板BOM及连接表；results/data：逐脚、静态核对及板间连接；schematic/previews：实际查看器截图。references/source和references/generated保留转换基准与中间输入，非最终交付格式。',
'复现：在仓库根目录执行python projects/2026-electronics-contest/g-buck/aux-posts-r3/tools/build_system_r3.py。此脚本使用仓库内保留的R2和V1.1基准及官方格式转换器逻辑。格式规范与验证器来源沿用mainboard-r2/references/pro_format_sources.json。']
md='\n\n'.join(notes)+'\n';(R/'reports/辅助电源接线柱修改与接线说明.md').write_text(md);(project/'打开及接线说明.md').write_text(md)
readme='''# G题R3：辅助电源连接也采用板凳式焊接接线柱

[下载专业版eprj3完整工程](downloads/GBUCK_System_R3_EPRJ3.zip) · [BOM Excel](schematic/System_BOM_R3.xlsx) · [接线/修改说明](reports/辅助电源接线柱修改与接线说明.md) · [接线PDF](reports/Connection_Guide_R3.pdf)

解压后打开`GBUCK_System_R3/GBUCK_System_R3.eprj3`，保留`sch`目录。工程包含三块独立板的三张图页；不是一块三合一PCB。

| 从哪里 | 接到哪里 | 电源 |
|---|---|---|
| 主板J4P | 辅助板J1P | VIN_SYS，15–25V |
| 主板J4N | 辅助板J1N | GND |
| 辅助板J2P | 主控板JPP | +3V3 |
| 辅助板J2N | 主控板JPN | GND |

每只接线柱四脚接同一网络；10芯排线连接主板J3↔主控J1保持不变。四只双针电源接口改为八只板凳柱；主板45件、主控25件、辅助5件，共75件/277脚。除接口符号/封装需求外，保留网络、电路参数、模型及固件不变。

接线柱厂家型号、额定承流和机械尺寸待定，≥5A为采购要求，不能直接制板。三板BOM及真实专业版导线静态检查、官方格式和查看器通过；原生编辑保存/ERC/DRC及实测未验证。

[主板实际显示](schematic/previews/Mainboard_6_Blocks.png) · [主控实际显示](schematic/previews/MCU_LCD.png) · [辅助板实际显示](schematic/previews/Aux_Power.png)
''';(R/'README.md').write_text(readme)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));c=canvas.Canvas(str(R/'reports/Connection_Guide_R3.pdf'),pagesize=(595.28,841.89));y=790;pg=1
for para in notes[:-1]:
 size=14 if para.startswith('#') else 10;line='';lines=[]
 for ch in para.lstrip('# '):
  if line and pdfmetrics.stringWidth(line+ch,'STSong-Light',size)>499:lines.append(line);line=ch
  else:line+=ch
 if line:lines.append(line)
 for line in lines:
  if y<55:c.setFont('STSong-Light',9);c.drawString(48,28,f'R3辅助电源接线 / {pg}');c.showPage();pg+=1;y=790
  c.setFont('STSong-Light',size);c.drawString(48,y,line);y-=size+5
 y-=6
c.setFont('STSong-Light',9);c.drawString(48,28,f'R3辅助电源接线 / {pg}');c.save()
f=Path('README.md');s=f.read_text();s=s.replace('## 项目目录\n','## 项目目录\n\n2026-11-08：[G题R3：三板辅助供电接口改板凳式焊接接线柱](projects/2026-electronics-contest/g-buck/aux-posts-r3/README.md) · [专业版eprj3整包](projects/2026-electronics-contest/g-buck/aux-posts-r3/downloads/GBUCK_System_R3_EPRJ3.zip)。主板J4、辅源输入/输出、主控JP四个接口改八只单极四脚柱；75件/277脚核对通过，主功率/控制参数、模型及固件不变；封装待定，原生ERC/实测未验证。\n',1);f.write_text(s)
with zipfile.ZipFile(R/'downloads/GBUCK_System_R3_EPRJ3.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(project.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(project.parent)))
 z.write(R/'schematic/System_BOM_R3.xlsx','BOM/System_BOM_R3.xlsx');z.write(R/'schematic/System_BOM_R3.csv','BOM/System_BOM_R3.csv');z.write(R/'reports/Connection_Guide_R3.pdf','Connection_Guide_R3.pdf')
 for f in (R/'results/data').glob('*'):
  if f.is_file():z.write(f,'checks/'+f.name)
 for f in (R/'schematic/previews').glob('*.png'):z.write(f,'previews/'+f.name)
with zipfile.ZipFile(R/'downloads/GBUCK_System_R3_EPRJ3.zip') as z:assert z.testzip() is None
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(R.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print('PACKAGED R3: 75 components / 277 pins / 3 boards; ZIP PASS')
