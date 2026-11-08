"""Generate three independent boards with bench-post auxiliary power interfaces."""
from pathlib import Path
import json,csv,copy,hashlib,sys,shutil
P=Path('projects/2026-electronics-contest/g-buck');R=P/'aux-posts-r3';R.mkdir(parents=True,exist_ok=True)
for d in ['tools','references/source','results/data','schematic/pro','schematic/previews','downloads','reports']:(R/d).mkdir(parents=True,exist_ok=True)
oldmain=P/'mainboard-r2';oldmod=P/'modular-v1-1'
oldexpected=json.loads((oldmod/'results/data/expected_pins.json').read_text())
allrows=[];audit=[]
configs=[('GBUCK_Main_R3','Mainboard','Mainboard_6_Blocks',oldmain/'schematic/native/Mainboard_Functional_Blocks.json',json.loads((oldmain/'results/data/expected_mainboard_pins.json').read_text()),{'J4':[('J4P','VIN_SYS'),('J4N','GND')]}),('GBUCK_Control_R3','Control','MCU_LCD',oldmod/'schematic/standard_json/C_MCU_LCD.json',oldexpected['C_MCU_LCD'],{'JP':[('JPP','+3V3'),('JPN','GND')]}),('GBUCK_Aux_R3','Auxiliary','Aux_Power',oldmod/'schematic/standard_json/D_Aux_Power.json',oldexpected['D_Aux_Power'],{'J1':[('J1P','VIN_SYS'),('J1N','GND')],'J2':[('J2P','+3V3'),('J2N','GND')]})]
def gid(seed):return 'ggeR3'+hashlib.sha256(seed.encode()).hexdigest()[:12]
def text(x,y,s,size=12,mark='L'):return f'T~{mark}~{x}~{y}~0~#173d70~Arial~{size}pt~~~~comment~{s}~1~start~{gid(str((x,y,s,mark)))}~0~'
def label(x,y,net):return f'N~{x}~{y}~0~#173d70~{net}~{gid(str((x,y,net)))}~start~{x}~{y-5}~Arial~10pt~0'
def wire(x,y,X,Y):return f'W~{x} {y} {X} {Y}~#14803c~1~0~none~{gid(str((x,y,X,Y)))}~0'
def bench(ref,net,x,y):
 s=[text(x,y-30,ref,13,'P'),text(x,y-12,'BENCH POST 4P - TBD',10,'N'),f'R~{x}~{y}~~~120~150~#8b2323~1~0~none~{gid(ref+"box")}~0~'];extras=[]
 for n in range(1,5):
  Y=y+25+n*25;a=x-20;b=x
  s.append(f'P~show~0~{n}~{a}~{Y}~180~{gid(ref+str(n))}~0^^{a}~{Y}^^M {a} {Y} L {b} {Y}~#8b2323^^1~{b+6}~{Y+4}~0~{n}~start~Arial~9pt~#173d70^^1~{a+7}~{Y-5}~0~{n}~start~Arial~8pt~#173d70^^0~{b}~{Y}^^0~M {b} {Y} L {b} {Y}')
  extras +=[wire(a-75,Y,a,Y),label(a-75,Y,net)]
 cp='package``name`BENCH POST 4P - TBD`spicePre`J`Status`TBD model and footprint'
 return [f'LIB~{x}~{y}~{cp}~~0~{gid(ref)}~~{hashlib.sha256(ref.encode()).hexdigest()[:32]}~0~~yes~yes#@$'+'#@$'.join(s),*extras]
for name,sch,title,inputfile,before,replacements in configs:
 stage=R/'references/generated'/name
 for d in ['schematic/native','results/data','tools']:(stage/d).mkdir(parents=True,exist_ok=True)
 original=json.loads(inputfile.read_text());doc=copy.deepcopy(original);shapes=doc['schematics'][0]['dataStr']['shape'];after=copy.deepcopy(before)
 if sch=='Mainboard':rows=list(csv.DictReader((oldmain/'schematic/BOM_ByReference_R2.csv').open(encoding='utf-8-sig')))
 else:
  rows=[]
  for r in csv.DictReader((oldmod/'schematic/BOM.csv').open(encoding='utf-8-sig')):
   if r['Board']!=('C_MCU_LCD' if sch=='Control' else 'D_Aux_Power'):continue
   rows.append({'功能区':sch,'位号':r['Reference'],'原标称':r['Part_or_value'],'推荐规格':r['Part_or_value'],'厂家型号':r['Part_or_value'],'立创料号':'','封装':r['Recommended_footprint'],'SMT库别':'沿用V1.1，库别未核实','备注':'本轮仅改电源接口，非接口器件沿用基准；未重新选型','核对日期':'2026-11-08','来源':''})
 
 if sch=='Control':
  for r in rows:
   if r['位号']=='J1':r['推荐规格']='TO MAINBOARD J3 / 2x5 keyed header'
 oldrefs=set(replacements);rows=[r for r in rows if r['位号'] not in oldrefs];out=[];endpoint_notes=[]
 for shape in shapes:
  if shape.startswith('LIB~'):
   children=shape.split('#@$')[1:];ref=next(c.split('~')[12] for c in children if c.startswith('T~P~'))
   if ref in oldrefs:
    for c in children:
     if c.startswith('P~'):
      q=c.split('^^');num=q[0].split('~')[3];x,y=map(float,q[1].split('~'));endpoint_notes.append(label(x,y,before[ref][num]))
    continue
   if sch=='Control' and ref=='J1':shape=shape.replace('TO BOARD B','TO MAINBOARD J3')
  elif shape.startswith('T~'):
   shape=shape.replace('四块板独立制作','三块板独立制作 / R3辅助电源接线柱').replace('INPUT FROM A.J4','INPUT FROM MAIN J4P/J4N').replace('OUTPUT TO C.JP','OUTPUT TO CONTROL JPP/JPN')
  out.append(shape)
 if sch!='Mainboard':
  # Remove obsolete connector-only stubs, leaving retained component wiring intact.
  removed_pin_coords={(float(q.split('~')[1]),float(q.split('~')[2])) for q in endpoint_notes}
  removed_label_coords=set(removed_pin_coords)
  cleaned=[]
  for q in out:
   a=q.split('~')
   if a[0]=='W':
    vv=list(map(float,a[1].split()));points=list(zip(vv[::2],vv[1::2]))
    if any(pt in removed_pin_coords for pt in points):removed_label_coords.update(points);continue
   cleaned.append(q)
  out=[q for q in cleaned if not(q.startswith('N~') and (float(q.split('~')[1]),float(q.split('~')[2])) in removed_label_coords)]
 else:out+=endpoint_notes
 oldwidth=doc['schematics'][0]['dataStr']['BBox']['width'];oldheight=doc['schematics'][0]['dataStr']['BBox']['height'];x=oldwidth+130;y=160
 out.append(text(oldwidth+25,60,'R3 辅助供电接线柱',18));out.append(text(oldwidth+25,90,'每只4脚同网，型号/尺寸待定',11))
 added=[]
 for oldref,pairs in replacements.items():
  del after[oldref]
  for ref,net in pairs:
   after[ref]={str(i):net for i in range(1,5)};out+=bench(ref,net,x,y);y+=230;added.append(ref)
   rows.append({'功能区':'辅助供电接口','位号':ref,'原标称':oldref,'推荐规格':'单极四脚板凳式焊接接线柱，采购要求≥5A','厂家型号':'待定：四脚同体导通、横梁供鳄鱼夹夹持','立创料号':'','封装':'THT 4P，尺寸/孔距/孔径待定','SMT库别':'非SMT/通孔手焊','备注':f'四脚全部接{net}；替代原{oldref}相应电极；需核实厂家承流与机械图','核对日期':'2026-11-08','来源':''})
  out.append(text(oldwidth+25,y-45,oldref+' → '+' / '.join(r for r,n in pairs),11))
 width=oldwidth+470;height=max(oldheight,y+60);data=doc['schematics'][0]['dataStr'];data['shape']=out;data['BBox']['width']=width;data['BBox']['height']=height;data['canvas']=f'CA~{width}~{height}~#FFFFFF~yes~#CCCCCC~5~{width}~{height}~line~5~pixel~5~0~0';doc['title']=name+' / Bench post auxiliary interfaces'
 (stage/'schematic/native/Mainboard_Functional_Blocks.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2));(stage/'results/data/expected_mainboard_pins.json').write_text(json.dumps(after,ensure_ascii=False,indent=2))
 with (stage/'schematic/BOM_ByReference_R2.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
 for r in rows:allrows.append({'板':sch,**r})
 for r,v in before.items():
  if r not in oldrefs:assert after[r]==v
 audit.append({'board':sch,'before_components':len(before),'after_components':len(after),'before_pins':sum(map(len,before.values())),'after_pins':sum(map(len,after.values())),'removed':list(oldrefs),'added':added,'retained_pin_maps_unchanged':True,'source':str(inputfile)})
 shutil.copy(oldmain/'tools/verify_connections.py',stage/'tools/verify_connections.py')
 # Adapt the proven converter to each independent board; UUID namespace includes board name.
 s=(oldmain/'tools/convert_pro_eprj3.py').read_text();s=s.replace("ROOT/'schematic/pro/GBUCK_Mainboard_R2'",f"ROOT/'schematic/pro/{name}'");s=s.replace("'GBUCK_R2_PRO/'",repr(name+'/'));s=s.replace("name='GBUCK_Mainboard_R2';title='Mainboard_6_Blocks'",f"name='{name}';title='{title}'")
 s=s.replace("'sch/Mainboard'",f"'sch/{sch}'").replace("'title':'Mainboard'",f"'title':'{sch}'").replace("'Mainboard.ecfg'",f"'{sch}.ecfg'").replace("'name':'Mainboard'",f"'name':'{sch}'").replace("'title':'Mainboard_R2'",f"'title':'{sch}_R3'")
 s=s.replace("'components':44,'pins':135,'symbols':44,'devices':44", "'components':len(expected),'pins':sum(map(len,expected.values())),'symbols':len(symbols),'devices':len(devices)")
 (stage/'tools/convert_pro_eprj3.py').write_text(s)
 shutil.copy(inputfile,R/'references/source'/f'{name}_baseline.json')
(R/'results/data/revision_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
with (R/'schematic/System_BOM_R3.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=allrows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(allrows)
assert len(allrows)==75
print('Prepared',[(a['board'],a['after_components'],a['after_pins']) for a in audit],'total',len(allrows))
# Convert and independently verify each board, then combine their separate board containers.
import subprocess
combined=None;dest=R/'schematic/pro/GBUCK_System_R3';dest.mkdir(parents=True,exist_ok=True)
for stage in sorted((R/'references/generated').iterdir()):
 subprocess.run([sys.executable,str(stage/'tools/convert_pro_eprj3.py'),str(stage)],check=True)
 project=next((stage/'schematic/pro').iterdir());index=json.loads(next(project.glob('*.eprj3')).read_text());shutil.copytree(project/'sch',dest/'sch',dirs_exist_ok=True)
 if combined is None:combined=index
 else:
  for k in ['boards','schematics','sheets']:combined['profile'][k].update(index['profile'][k])
 s=(oldmain/'tools/verify_pro_eprj3.py').read_text().replace("'schematic/pro/GBUCK_Mainboard_R2'",repr('schematic/pro/'+stage.name)).replace('component_count==44 and len(pins)==135','component_count==len(expected) and len(pins)==sum(map(len,expected.values()))').replace("'comparison':'d38634b R2 standard-format expected pin map'","'comparison':'R3 expected pin map; retained non-interface pins audited against baseline'")
 (stage/'tools/verify_pro_eprj3.py').write_text(s);subprocess.run([sys.executable,str(stage/'tools/verify_pro_eprj3.py'),str(stage)],check=True)
combined['name']='GBUCK_System_R3';combined['content']='G题三板R3：辅助供电接口均为板凳式焊接柱；封装待定'
for id,sh in combined['profile']['sheets'].items():
 if sh['title']=='Mainboard_6_Blocks':combined['default_sheet']=id;combined['config']['defaultSheet']=id
(dest/'GBUCK_System_R3.eprj3').write_text(json.dumps(combined,ensure_ascii=False,indent=2)+'\n')
print('Combined 3 boards into',dest)
