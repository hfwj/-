from pathlib import Path
import json,csv,copy,ast,shutil,subprocess,sys,hashlib,math
P=Path('projects/2026-electronics-contest/g-buck');R=P/'self-aux-r4';B=P/'aux-posts-r3';R.mkdir(parents=True,exist_ok=True)
for d in ['tools','references','results/data','schematic/native-input','schematic/pro','schematic/previews','downloads','reports']:(R/d).mkdir(parents=True,exist_ok=True)
stage=R/'references/aux-conversion'
for d in ['tools','results/data','schematic/native']:(stage/d).mkdir(parents=True,exist_ok=True)
# Reuse the archived symbol drawing helper without executing its old four-board design.
source=(P/'modular-v1-1/tools/generate_easyeda.py').read_text();tree=ast.parse(source);nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))];env={'serial':0,'BLUE':'#173d70','RED':'#8b2323','GREEN':'#14803c'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<archived-symbol-helper>','exec'),env);env.update(serial=0,BLUE='#173d70',RED='#8b2323',GREEN='#14803c')
A=env['Sheet']('Aux_Power','辅助板R4：自设计3.3V同步Buck，全贴片功率电路',2000,1120)
A.shapes[1]=A.shapes[1].replace('四块板独立制作','三块独立板 / R4自设计辅助电源')
A.chip('U7','TPS560430X3FDBVR',650,230,230,[(5,'VIN','VIN_SYS'),(4,'EN','VIN_SYS'),(2,'GND','GND')],[(1,'CB','CB_AUX'),(6,'SW','SW_AUX'),(3,'FB','+3V3')],'SOT-23-6 DBV',45)
A.passive('L2','12uH Isat>=2A',1160,295,'SW_AUX','+3V3','L',recommend='ZNR6028ST120M exact lands required')
A.wire((900,295),(1130,295))
A.passive('C23','10uF 50V X7R',380,330,'VIN_SYS','GND','C',True,'1206')
A.passive('C24','100nF 50V X7R',520,330,'VIN_SYS','GND','C',True,'0805')
A.passive('C25','100nF 50V X7R',1100,150,'CB_AUX','SW_AUX','C',False,'0805')
A.passive('C26','22uF 25V X7R',1450,370,'+3V3','GND','C',True,'1210')
A.wire((1190,295),(1450,295),(1450,340))
A.passive('C27','22uF 50V AL SMD',380,600,'VIN_SYS','GND','C',True,'EEE-FK1H220P exact mechanical drawing required');A.text(405,575,'+',16)
for ref,net,x,y in [('J1P','VIN_SYS',100,180),('J1N','GND',100,520),('J2P','+3V3',1750,180),('J2N','GND',1750,520)]:A.connector(ref,'BENCH POST 4P - TBD',x,y,[net]*4,'THT4P - dimensions TBD')
for y,text in [(800,'输入15–25V；输出固定3.3V；芯片标称600mA，整板按0.3A目标复测，不将标称能力当实测结果。'),(835,'U7必须是X3F固定3.3V版：FB(3)直接接输出，不装外部分压；EN(4)直接接VIN。'),(870,'C23/C24紧贴VIN/GND；C25紧贴CB/SW；L2/C26靠近芯片；FB从C26正端安静引回。'),(905,'C27为板间导线输入缓冲/阻尼电容；接线短并成对布置。电解1正极、2负极，不可反接。'),(940,'J1P/J1N接主板J4P/J4N；J2P/J2N接主控JPP/JPN。每只柱四脚同网。'),(975,'主板/主控参数与固件不改。未绑定封装、未做原生ERC/PCB/环路或实物验证。')]:A.text(50,y,text,13)
expected={r:v['pins'] for r,v in A.parts.items()};assert len(expected)==11 and sum(map(len,expected.values()))==34
head={'docType':'1','editorVersion':'6.5.51','newgId':True,'c_para':{'Prefix Start':'1'},'c_spiceCmd':None,'x':'0','y':'0','hasIdFlag':False};data={'head':head,'canvas':'CA~2000~1120~#FFFFFF~yes~#CCCCCC~5~2000~1120~line~5~pixel~5~0~0','shape':A.shapes,'BBox':{'x':0,'y':0,'width':2000,'height':1120},'colors':{}}
std={'editorVersion':'6.5.51','docType':'5','title':'Aux_R4','description':'Conversion input only; primary delivery is eprj3','colors':{},'schematics':[{'docType':'1','title':'Aux_Power','description':'','dataStr':data}]}
(stage/'schematic/native/Mainboard_Functional_Blocks.json').write_text(json.dumps(std,ensure_ascii=False,indent=2));(stage/'results/data/expected_mainboard_pins.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
oldrows=list(csv.DictReader((B/'schematic/System_BOM_R3.csv').open(encoding='utf-8-sig')));rows=[r for r in oldrows if r['板']=='Auxiliary' and r['位号']!='M1']
parts=[('U7','TPS560430X3FDBVR','C2071721','固定3.3V/600mA/1.1MHz同步Buck','SOT-23-6 / DBV','扩展库（官网已核实）','不得替换成可调版XF/X/Y；FB直接接输出','https://jlcpcb.com/partdetail/TexasInstruments-TPS560430X3FDBVR/C2071721'),('L2','ZNR6028ST120M','C42429312','12uH ±20% Irms2A Isat2A DCR80mΩ','SMD 6x6x2.8mm，焊盘查原厂','库别待核实','目录参数已核实；不是通用6x6焊盘','https://item.szlcsc.com/44450897.html'),('C23','CL31B106KBHNNNE','C89632','10uF 50V X7R ±10%','1206','扩展库（沿用已核实选型）','25V偏压下有效输入陶瓷容量目标≥2.2uF；需曲线/实测','https://jlcpcb.com/partdetail/CL31B106KBHNNNE/C89632'),('C24','CC0805KRX7R9BB104','C49678','100nF 50V X7R ±10%','0805','基础库（沿用已核实选型）','贴近VIN与GND','https://jlcpcb.com/partdetail/C49678'),('C25','CC0805KRX7R9BB104','C49678','100nF 50V X7R ±10%','0805','基础库（沿用已核实选型）','自举电容：CB与SW之间，不能接地','https://jlcpcb.com/partdetail/C49678'),('C26','CL32B226KAJNNNE','C309062','22uF 25V X7R ±10%','1210','库别待核实','3.3V偏压有效容量设计目标≥15uF需复核；非实测保证','https://www.lcsc.com/product-detail/C309062.html'),('C27','EEE-FK1H220P','','22uF 50V 铝电解 SMD ±20%','SMD铝电解，准确焊盘查厂家图','库别/商城料号待核实','输入缓冲与阻尼候选；需核对原厂尺寸、ESR和纹波额定；1正2负','https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEEFK1H220P')]
for ref,m,c,s,p,k,n,url in parts:rows.append({'板':'Auxiliary','功能区':'自设计辅助Buck','位号':ref,'原标称':'替代M1内部功能','推荐规格':s,'厂家型号':m,'立创料号':c,'封装':p,'SMT库别':k,'备注':n,'核对日期':'2026-11-08','来源':url})
with (stage/'schematic/BOM_ByReference_R2.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
allrows=[r for r in oldrows if r['板']!='Auxiliary']+rows
with (R/'schematic/System_BOM_R4.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=allrows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(allrows)
assert len(allrows)==81
base=P/'mainboard-r2';shutil.copy(base/'tools/verify_connections.py',stage/'tools/verify_connections.py')
s=(B/'references/generated/GBUCK_Aux_R3/tools/convert_pro_eprj3.py').read_text().replace('GBUCK_Aux_R3','GBUCK_Aux_R4').replace('Auxiliary_R3','Auxiliary_R4');s=s.replace('G题主功率+CC主板R2；封装未绑定；接线柱型号和尺寸待定','R4 self-designed auxiliary buck; footprints TBD');(stage/'tools/convert_pro_eprj3.py').write_text(s)
subprocess.run([sys.executable,str(stage/'tools/convert_pro_eprj3.py'),str(stage)],check=True)
project=R/'schematic/pro/GBUCK_System_R4';shutil.copytree(B/'schematic/pro/GBUCK_System_R3',project,dirs_exist_ok=True)
for f in project.glob('*.eprj3'):f.unlink()
for f in project.glob('*.md'):f.unlink()
shutil.copytree(stage/'schematic/pro/GBUCK_Aux_R4/sch/Auxiliary',project/'sch/Auxiliary',dirs_exist_ok=True)
idx=json.loads((B/'schematic/pro/GBUCK_System_R3/GBUCK_System_R3.eprj3').read_text());auxidx=json.loads((stage/'schematic/pro/GBUCK_Aux_R4/GBUCK_Aux_R4.eprj3').read_text())
for k in ['boards','schematics','sheets']:
 idx['profile'][k]={i:r for i,r in idx['profile'][k].items() if r.get('title','') not in ['Auxiliary_R3','Aux_Power'] and r.get('name','')!='Auxiliary'};idx['profile'][k].update(auxidx['profile'][k])
idx['name']='GBUCK_System_R4';idx['content']='R4 自设计3.3V贴片辅助电源，主功率/主控保持R3'
(project/'GBUCK_System_R4.eprj3').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
# Verify the actual Pro auxiliary symbol/geometry, not merely the intended mapping.
s=(B/'references/generated/GBUCK_Aux_R3/tools/verify_pro_eprj3.py').read_text().replace('GBUCK_Aux_R3','GBUCK_Aux_R4').replace('R3 expected pin map; retained non-interface pins audited against baseline','R4 self-designed auxiliary expected pins; other boards unchanged');(stage/'tools/verify_pro_eprj3.py').write_text(s);subprocess.run([sys.executable,str(stage/'tools/verify_pro_eprj3.py'),str(stage)],check=True)
for sch in ['Mainboard','Control']:
 for f in (B/'schematic/pro/GBUCK_System_R3/sch'/sch).iterdir():assert f.read_bytes()==(project/'sch'/sch/f.name).read_bytes()
shutil.copy(stage/'results/data/pro_connectivity_report.json',R/'results/data/Auxiliary_connectivity.json')
calc={}
for vin in [15,25]:
 for L in [12e-6,9.6e-6]:
  ripple=3.3*(1-3.3/vin)/(L*1.1e6);calc[str((vin,L))]={'ripple_A_pp':ripple,'peak_at_0_3A':.3+ripple/2,'assumption':'ideal CCM, nominal 1.1MHz; not a switching simulation'}
(R/'results/data/design_calculations.json').write_text(json.dumps({'design_load_target_A':.3,'chip_max_current_A':.6,'Vin_system_V':[15,25],'Vout_nominal_V':3.3,'L_nominal_uH':12,'Cout_nominal_uF':22,'calculations':calc,'measurements':'NOT DONE','main_control_documents_byte_identical':True},ensure_ascii=False,indent=2))
print('R4 generated: 81 items, auxiliary 11 items/34 pins, 7 SMD + 4 posts')
