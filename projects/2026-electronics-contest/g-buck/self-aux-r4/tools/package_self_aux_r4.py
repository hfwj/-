from pathlib import Path
import json,csv,shutil,hashlib,zipfile
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
P=Path('projects/2026-electronics-contest/g-buck');R=P/'self-aux-r4';B=P/'aux-posts-r3';project=R/'schematic/pro/GBUCK_System_R4'
rows=list(csv.DictReader((R/'schematic/System_BOM_R4.csv').open(encoding='utf-8-sig')));aux=[r for r in rows if r['板']=='Auxiliary'];assert len(rows)==81 and len(aux)==11
expected={}
for b,name in [('Mainboard','GBUCK_Main_R3'),('Control','GBUCK_Control_R3')]:expected[b]=json.loads((B/'references/generated'/name/'results/data/expected_mainboard_pins.json').read_text())
expected['Auxiliary']=json.loads((R/'references/aux-conversion/results/data/expected_mainboard_pins.json').read_text())
pins=[{'板':b,'位号':r,'脚号':n,'网络':net} for b,parts in expected.items() for r,pp in parts.items() for n,net in pp.items()];assert len(pins)==291
external=list(csv.DictReader((B/'results/data/External_Connections_R3.csv').open(encoding='utf-8-sig')))
for r in external:
 src=r['起点接线柱'];dst=r['终点接线柱'];b=r['起点板'];d=r['终点板']
 if '.' in src:ref,n=src.split('.');r2,n2=dst.split('.');assert expected[b][ref][n]==expected[d][r2][n2]==r['网络']
 else:assert set(expected[b][src].values())==set(expected[d][dst].values())=={r['网络']}
for file,data in [('Auxiliary_BOM_R4.csv',aux),('All_Pins_R4.csv',pins),('External_Connections_R4.csv',external)]:
 with (R/'results/data'/file).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=data[0].keys(),lineterminator='\n');w.writeheader();w.writerows(data)
wb=Workbook();wb.remove(wb.active)
for title,data in [('辅源BOM',aux),('全系统BOM',rows),('逐引脚',pins),('板间连接',external)]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='254B61')
 for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(12,max(len(str(c.value or '')) for c in col)*1.1))
 for rr in ws:
  for c in rr:c.alignment=Alignment(vertical='top',wrap_text=True)
 for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=60
wb.save(R/'schematic/System_BOM_R4.xlsx')
for f,g in [('r4_schema.json','schema_check.json'),('r4_viewer.json','viewer_check.json'),('r4_browser.json','browser_check.json')]:shutil.copy('/tmp/'+f,R/'results/data'/g)
for title in ['Aux_Power','MCU_LCD','Mainboard_6_Blocks']:shutil.copy('/tmp/R4_'+title+'.png',R/'schematic/previews'/(title+'.png'))
schema=json.loads((R/'results/data/schema_check.json').read_text());view=json.loads((R/'results/data/viewer_check.json').read_text());browser=json.loads((R/'results/data/browser_check.json').read_text());assert schema['valid'] and not browser['errors'] and view['openableDocuments']==3
for v in view['results']:assert not v['report']['badLines'] and not v['report']['unknownTypes'] and v['report']['placeholders']==0 and not v['diagnostics']
source={'checked':'2026-11-08','datasheet':'https://www.ti.com/lit/ds/symlink/tps560430.pdf','sections':['5/6 variants and pin map','7.5 fixed3.3V limits and current limit','8.4.5 FPWM','9.2 Table1 3.3V/1.1MHz:12uH/22uF','9.2.2.6 input capacitor','10 input bulk capacitor for cable-fed supply','11 layout'],'IC_catalog':'https://jlcpcb.com/partdetail/TexasInstruments-TPS560430X3FDBVR/C2071721','IC_library_class':'Extended','L_catalog':'https://item.szlcsc.com/44450897.html','capacitors':'C23,C24,C25,C26 reuse previously checked selections; C27 manufacturer candidate EEE-FK1H220P, LCSC code not verified','C27_supplier':'https://www.digikey.in/en/products/detail/panasonic-industry/EEE-FK1H220P/766187','C27_manufacturer_page_check':'not accessible; footprint/ESR/ripple rating still need manufacturer confirmation','hardware_test':False}
(R/'references/selection_sources.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
notes=['# R4 自设计辅助电源：3.3V固定输出 / SMT','2026-11-08。用TPS560430X3FDBVR替换成品辅源M1。完整.eprj3仍包含主板、主控板、辅助板三块独立PCB。',
'## 方案与简化','系统输入15–25V，输出固定3.3V。芯片工作输入范围4–36V、标称600mA；本版整板设计目标0.3A，未将芯片标称能力视作整板已验证指标。系统主功率器件限制未变，不能把整机输入上限提高到36V。',
'TPS560430X3F为1.1MHz强制PWM固定3.3V型号，内置同步MOS管、软启动和补偿；不加外置续流二极管、MOS管、反馈分压或补偿网络。轻载也固定PWM，取舍是轻载效率可能低于PFM版；纹波/效率仍需实测。不能用没有X3F后缀的可调版直接替换。',
'核心6个贴片器件：U7、L2、C23、C24、C25、C26。另保留C27输入22uF/50V贴片铝电解作板间导线供电缓冲/阻尼候选，共7个贴片器件；4只板凳柱仍为通孔手焊。C27不能单凭标称容量保证抑制一切热插拔尖峰，需实测输入波形。',
'## 位号与接线','U7：1 CB→CB_AUX；2 GND→GND；3 FB→+3V3；4 EN→VIN_SYS；5 VIN→VIN_SYS；6 SW→SW_AUX。固定3.3V版直接从输出反馈，不装分压电阻。',
'L2=12uH，SW_AUX→+3V3。C25=100nF/50V，自举端CB_AUX↔SW_AUX，不能接成CB对地。',
'C23=10uF/50V/X7R和C24=100nF/50V/X7R均接VIN_SYS↔GND；C27=22uF/50V贴片电解接VIN_SYS↔GND，1脚正极、2脚负极。C26=22uF/25V/X7R接+3V3↔GND。',
'J1P/J1N接主板J4P/J4N；J2P/J2N接主控JPP/JPN。每柱四脚同网。主控J1↔主板J3的10芯排线与3.3V供电路径保持R3，不增加独立3.3V源并联。',
'## BOM与器件约束','U7：TPS560430X3FDBVR，C2071721，SOT-23-6/DBV，官网扩展库。L2：ZNR6028ST120M，C42429312，12uH±20%、额定/饱和2A、DCR80mΩ，焊盘必须查该型号。',
'C23沿用C89632/1206；C24/C25用基础库C49678/0805；C26沿用C309062/1210。C27候选EEE-FK1H220P，SMD铝电解，立创料号/精确焊盘/ESR和纹波额定尚待厂家资料核对。不可把未核实项当作可直接下单BOM。',
'C23在25V偏压下有效陶瓷容量目标≥2.2uF；C26在3.3V偏压下有效容量设计目标≥15uF。均需偏压曲线或实测复核。C26标称22uF和L2标称12uH参考厂家3.3V/1.1MHz典型LC表，但本版选型和负载瞬态未实测验证。',
'## 静态计算与布局','理想CCM、25V输入、3.3V输出、12uH、标称1.1MHz时，电感纹波约0.217A峰峰值；取电感-20%为9.6uH时约0.271A。0.3A负载下峰值约0.436A。此为代数估算，不含频率公差、开关损耗或控制环路动态，不能代替仿真/实测。',
'芯片限流最高值1.4A，L2候选Isat2A；仍需考虑温度降额。输入电容、芯片VIN/GND构成最小环路；C25紧贴CB/SW；SW铜区短小，FB从C26正端安静回接。主控采样电路与开关节点分开，地平面连续。',
'建议先独立验证15/20/25V输入，负载0/50/150/300mA的直流电压、纹波、启动过冲、温升与负载阶跃，再连接主控。稳态输出按芯片完整温度范围3.25–3.35V边界复核，实际要求还需叠加导线压降与动态偏差。',
'## 修改影响','比较基准c3c66c5/R3：删除辅助板成品模块M1，新增U7、L2、C23–C27；辅助板5→11件、20→34脚，整机75→81件、277→291脚。辅助板电路和PCB需重新设计。四只板凳柱和四条板间电源线映射不变。',
'主功率板与主控板专业版图页/配置文件与R3逐字节一致。它们的器件、BOM行、封装要求、网络和参数不改；仅辅助板BOM/封装/PCB改变。更换辅源可能影响整机效率、供电纹波、启动及ADC精度，这些属于需复测的硬件影响。',
'模型/固件不改，未新增厂家开关模型仿真、环路仿真或实测。原3.3V负载预算仍需按实物液晶及背光复核；7V设定高端余量和瞬时1A限制结论不因更换辅源自动消失。',
'## 工程与核对',f'官方Schema校验{schema["records"]}条记录通过；官方查看器三张图页解析/显示通过，0坏行、0未知图元、0占位符、0诊断；浏览器实际打开三页无脚本错误。辅源真实专业版符号/导线核对11件34脚通过；主板/主控字节比对通过；板间4条电源线与10针排线映射核对通过。',
'尚未绑定封装或设计PCB；原生编辑器打开/保存、ERC/DRC、温升/效率/纹波/稳定性未验收。这是自设计原理图候选，不能直接制板或宣称稳定性已保证。',
'完整解压后打开GBUCK_System_R4/GBUCK_System_R4.eprj3，保留sch目录。Auxiliary_R4为本次新辅源；Mainboard_R3和Control_R3保留原版本以体现它们未改。',
'官方数据手册：https://www.ti.com/lit/ds/symlink/tps560430.pdf；选型来源与未核实项见references/selection_sources.json。复现：在仓库根目录运行python projects/2026-electronics-contest/g-buck/self-aux-r4/tools/build_self_aux_r4.py。']
md='\n\n'.join(notes)+'\n';(R/'reports/自设计辅助电源与修改影响.md').write_text(md);(project/'打开与辅助电源说明.md').write_text(md)
readme='''# G题R4：自设计贴片辅助电源

[下载专业版eprj3完整工程](downloads/GBUCK_System_R4_EPRJ3.zip) · [BOM Excel](schematic/System_BOM_R4.xlsx) · [设计与影响说明](reports/自设计辅助电源与修改影响.md) · [PDF](reports/Auxiliary_Design_R4.pdf) · [实际显示](schematic/previews/Aux_Power.png)

采用TPS560430X3FDBVR固定3.3V同步Buck；15–25V系统输入，芯片标称600mA，整板目标0.3A待验证。7个贴片器件＋4只通孔板凳柱，不用成品辅源。IC为扩展库，普通电容优先基础库。

对比R3：M1替换为U7、L2、C23–C27；辅助板11件34脚，整机81件291脚。主板/主控文件逐字节不变，板间接口、模型和固件不改。更换辅源的纹波、启动、效率与ADC影响需复测。

解压后打开`GBUCK_System_R4/GBUCK_System_R4.eprj3`，保留`sch/`。三张图页/三块独立板。Schema、专业版导线静态检查及官方查看器通过；封装未绑定，接线柱和部分器件机械资料待核实，原生ERC/PCB/实测未完成。
''';(R/'README.md').write_text(readme)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));c=canvas.Canvas(str(R/'reports/Auxiliary_Design_R4.pdf'),pagesize=(595.28,841.89));y=790;pg=1
for para in notes:
 size=14 if para.startswith('#') else 10;lines=[];line=''
 for ch in para.lstrip('# '):
  if line and pdfmetrics.stringWidth(line+ch,'STSong-Light',size)>499:lines.append(line);line=ch
  else:line+=ch
 if line:lines.append(line)
 for line in lines:
  if y<55:c.setFont('STSong-Light',9);c.drawString(48,28,f'R4辅助电源 / {pg}');c.showPage();pg+=1;y=790
  c.setFont('STSong-Light',size);c.drawString(48,y,line);y-=size+5
 y-=6
c.setFont('STSong-Light',9);c.drawString(48,28,f'R4辅助电源 / {pg}');c.save()
report={'baseline':'c3c66c5 / R3','boards':3,'total_components':81,'total_pins':291,'aux_components':11,'aux_pins':34,'smd_aux_components':7,'through_hole_posts_aux':4,'main_control_documents_byte_identical':True,'external_power_links_unchanged':4,'IDC_pins_unchanged':10,'native_editor_erc':False,'footprints_bound':False,'hardware_test':False,'design_load_A':.3,'chip_rating_A':.6}
(R/'results/data/assembly_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
f=Path('README.md');s=f.read_text();line='2026-11-08：[G题R4：自设计3.3V贴片辅助电源](projects/2026-electronics-contest/g-buck/self-aux-r4/README.md) · [eprj3完整工程](projects/2026-electronics-contest/g-buck/self-aux-r4/downloads/GBUCK_System_R4_EPRJ3.zip)。TPS560430X3F＋6只外围贴片元件替代成品M1，保留板凳柱；辅助板11件，主板/主控及固件/模型不改；格式/静态检查通过，PCB/实测待完成。'
if line not in s:s=s.replace('## 项目目录\n','## 项目目录\n\n'+line+'\n',1)
f.write_text(s)
with zipfile.ZipFile(R/'downloads/GBUCK_System_R4_EPRJ3.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(project.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(project.parent)))
 z.write(R/'schematic/System_BOM_R4.xlsx','BOM/System_BOM_R4.xlsx');z.write(R/'schematic/System_BOM_R4.csv','BOM/System_BOM_R4.csv');z.write(R/'reports/Auxiliary_Design_R4.pdf','Auxiliary_Design_R4.pdf')
 for f in (R/'results/data').glob('*'):
  if f.is_file():z.write(f,'checks/'+f.name)
 z.write(R/'schematic/previews/Aux_Power.png','previews/Aux_Power.png')
with zipfile.ZipFile(R/'downloads/GBUCK_System_R4_EPRJ3.zip') as z:assert z.testzip() is None
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(R.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print('R4 packaged; 81 items / 291 pins; PDF',pg,'pages')
