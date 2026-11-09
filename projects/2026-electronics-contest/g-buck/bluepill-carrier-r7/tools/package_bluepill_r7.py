"""Package R7 native projects, spreadsheets and validation evidence."""
from pathlib import Path
import csv, json, shutil, zipfile, hashlib
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
P=Path('projects/2026-electronics-contest/g-buck'); R=P/'bluepill-carrier-r7'; B=P/'partition-r5'
def read(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))
rows=read(R/'schematic/System_BOM_R7.csv');carrier=read(R/'schematic/Control_Carrier_BOM_R7.csv');modules=read(R/'schematic/Plug_In_Modules_BOM_R7.csv')
expected={
 'Mainboard':json.loads((P/'aux-posts-r3/references/generated/GBUCK_Main_R3/results/data/expected_mainboard_pins.json').read_text()),
 'Auxiliary':json.loads((B/'references/generated/Auxiliary/results/data/expected_mainboard_pins.json').read_text()),
 'Control':json.loads((R/'references/generated/Control/results/data/expected_mainboard_pins.json').read_text())}
for n in map(str,range(1,11)):assert expected['Mainboard']['J3'][n]==expected['Control']['J1'][n]
pins=[{'板':b,'位号':r,'脚号':n,'网络':v} for b,rr in expected.items() for r,nn in rr.items() for n,v in nn.items()]
assert len(rows)==73 and len(carrier)==17 and len(pins)==263
groups={}
for r in carrier:
 k=tuple(r[n] for n in ['厂家型号','立创料号','推荐规格','封装','SMT库别'])
 if k not in groups:groups[k]={'位号':[],'数量':0,**{n:r[n] for n in ['厂家型号','立创料号','推荐规格','封装','SMT库别']}}
 groups[k]['位号'].append(r['位号']);groups[k]['数量']+=1
for g in groups.values():g['位号']=' '.join(g['位号'])
block=json.loads((R/'results/data/Control_blocks.json').read_text())
zones=[{'区号':z['number'],'功能':z['title'],'位号':' '.join(r for r,c in block['components'].items() if c['zone']==z['number'])} for z in block['zones']]
changes=[{'项目':'核心板','R6':'WeAct BluePill-Plus V1.1','R7':'用户截图同款Blue Pill / STM32F103C8T6','说明':'厂家/板号未明确，锁定USB端上排首针GND版本'}, {'项目':'JCORE1.1','R6':'VCC / NC','R7':'GND / GND','说明':'实际导线接地；JCORE1.2也为GND'}, {'项目':'两排中心距','R6':'15.22mm','R7':'15.24mm','说明':'单排针距仍2.54mm，需在后续PCB设置排母位置'}, {'项目':'GPIO/屏幕/主板接口','R6':'R6配置','R7':'保留','说明':'PA2 ADC_IN2；PB10减小键；PCD8544及10芯排线均保留'}]
wb=Workbook();wb.remove(wb.active)
for title,data in [('底板17件',carrier),('独立采购模块2件',modules),('底板采购汇总',list(groups.values())),('核心40针映射',read(R/'results/data/Core_Socket_Map_R7.csv')),('固件与接口变化',changes),('功能分区',zones),('全系统73件',rows),('全系统263脚',pins)]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='234B61')
 for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(12,max(len(str(c.value or '')) for c in col)*1.1))
 for rr in ws:
  for c in rr:c.alignment=Alignment(vertical='top',wrap_text=True)
 for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=70
wb.save(R/'schematic/Control_Modules_BOM_R7.xlsx')
schema=json.loads(Path('/tmp/r7_schema.json').read_text());assert schema['valid']
shutil.copy('/tmp/r7_schema.json',R/'results/data/schema_check.json')
(R/'results/data/viewer_check.json').write_text(json.dumps({'revision':'R7','status':'NOT RUN','R6_results_not_reused':True,'native_editor_ERC':'NOT RUN'},indent=2))
report=R/'reports/选型接线与修改影响.md'
for name in ['GBUCK_Control_R7','GBUCK_System_R7']:
 project=R/'schematic/pro'/name
 (project/'打开与装配说明.md').write_text(report.read_text())
 with zipfile.ZipFile(R/'downloads'/(name+'_EPRJ3.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(project.rglob('*')):
   if f.is_file():z.write(f,str(f.relative_to(project.parent)))
  for f in sorted((R/'schematic').glob('*BOM*')):
   if f.is_file():z.write(f,'BOM/'+f.name)
  z.write(R/'schematic/previews/Control/Control_Blocks.pdf','PDF/Control_Blocks_R7.pdf')
  z.write(report,'选型接线与修改影响.md')
  z.write(R/'firmware/pinmap_r7.h','firmware/pinmap_r7.h')
  for f in sorted((R/'results/data').glob('*')):
   if f.is_file():z.write(f,'checks/'+f.name)
 with zipfile.ZipFile(R/'downloads'/(name+'_EPRJ3.zip')) as z:
  assert z.testzip() is None
  assert len([p for p in z.namelist() if p.endswith('.eprj3')])==1
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(R.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print('R7 packaged: controller/system native projects, 17-part carrier BOM, 2 modules, 6-page PDF')
