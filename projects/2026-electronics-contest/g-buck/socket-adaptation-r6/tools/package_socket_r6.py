"""Package R6 native projects, spreadsheets and validation evidence."""
from pathlib import Path
import csv, json, shutil, zipfile, hashlib
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
P=Path('projects/2026-electronics-contest/g-buck'); R=P/'socket-adaptation-r6'; B=P/'partition-r5'
def read(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))
rows=read(R/'schematic/System_BOM_R6.csv');carrier=read(R/'schematic/Control_Carrier_BOM_R6.csv');modules=read(R/'schematic/Plug_In_Modules_BOM_R6.csv')
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
changes=[{'项目':'电压采样','R5':'PA0 / ADC_IN0','R6':'PA2 / ADC_IN2','说明':'避开现成核心板PA0用户键；更新ADC规则组/DMA顺序'}, {'项目':'减小按键','R5':'PA11','R6':'PB10','说明':'避开核心板USB接口；更新GPIO初始化与时钟'}, {'项目':'显示接口','R5':'旧JLCD脚序，背光NC','R6':'Joy-IT Rev.2专用脚序，LIGHT接地','说明':'仍PCD8544及原五个GPIO；到货严查Revision'}, {'项目':'SWD','R5':'底板JSWD:3V3/IO/GND/CLK','R6':'模块P3:3V3/IO/CLK/GND','说明':'原底板JSWD删除，调试线需按模块P3接'}]
wb=Workbook();wb.remove(wb.active)
for title,data in [('底板17件',carrier),('独立采购模块2件',modules),('底板采购汇总',list(groups.values())),('核心40针映射',read(R/'results/data/Core_Socket_Map_R6.csv')),('固件与接口变化',changes),('功能分区',zones),('全系统73件',rows),('全系统263脚',pins)]:
 ws=wb.create_sheet(title);ws.append(list(data[0]));[ws.append(list(r.values())) for r in data];ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
 for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='234B61')
 for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(65,max(12,max(len(str(c.value or '')) for c in col)*1.1))
 for rr in ws:
  for c in rr:c.alignment=Alignment(vertical='top',wrap_text=True)
 for n in range(2,ws.max_row+1):ws.row_dimensions[n].height=70
wb.save(R/'schematic/Control_Modules_BOM_R6.xlsx')
for name in ['schema','viewer','browser']:
 source=Path('/tmp/r6_'+name+'.json');target=R/'results/data'/(name+'_check.json')
 if source.exists():shutil.copy(source,target)
for name in ['Mainboard_6_Blocks','Auxiliary_Blocks','Control_Sockets_R6']:
 source=Path('/tmp/R6_'+name+'.png')
 if source.exists():shutil.copy(source,R/'schematic/previews'/('Pro_Viewer_'+name+'.png'))
schema=json.loads((R/'results/data/schema_check.json').read_text());viewer=json.loads((R/'results/data/viewer_check.json').read_text());browser=json.loads((R/'results/data/browser_check.json').read_text())
assert schema['valid'] and not browser['errors']
for v in viewer['results']:assert not v['report']['badLines'] and not v['report']['unknownTypes'] and not v['report']['placeholders'] and not v['diagnostics']
report=R/'reports/选型接线与修改影响.md'
for name in ['GBUCK_Control_R6','GBUCK_System_R6']:
 project=R/'schematic/pro'/name
 (project/'打开与装配说明.md').write_text(report.read_text())
 with zipfile.ZipFile(R/'downloads'/(name+'_EPRJ3.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(project.rglob('*')):
   if f.is_file():z.write(f,str(f.relative_to(project.parent)))
  for f in sorted((R/'schematic').glob('*BOM*')):
   if f.is_file():z.write(f,'BOM/'+f.name)
  z.write(R/'schematic/previews/Control/Control_Blocks.pdf','PDF/Control_Blocks_R6.pdf')
  z.write(report,'选型接线与修改影响.md')
  z.write(R/'firmware/pinmap_r6.h','firmware/pinmap_r6.h')
  for f in sorted((R/'results/data').glob('*')):
   if f.is_file():z.write(f,'checks/'+f.name)
 with zipfile.ZipFile(R/'downloads'/(name+'_EPRJ3.zip')) as z:
  assert z.testzip() is None
  assert len([p for p in z.namelist() if p.endswith('.eprj3')])==1
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in sorted(R.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.txt'))
print('R6 packaged: controller/system native projects, 17-part carrier BOM, 2 modules, 6-page PDF')
