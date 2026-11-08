"""R5: regroup control/auxiliary schematics while retaining R4 electrical maps."""
from pathlib import Path
import json,csv,ast,copy,shutil,subprocess,sys
P=Path('projects/2026-electronics-contest/g-buck');R=P/'partition-r5';BASE=P/'self-aux-r4';R.mkdir(parents=True,exist_ok=True)
for d in ['tools','references','results/data','schematic/pro','schematic/previews','downloads','reports']:(R/d).mkdir(parents=True,exist_ok=True)
source=(P/'mainboard-r2/tools/generate_blocks.py').read_text();source=source.replace('同一块主板上的功能区','同一块独立PCB上的功能区');source=source.replace("elif kind=='D':\n   self.poly","elif kind=='K':\n   self.poly([(x-10,y),(x+7,y-10)],local=sh);self.poly([(x+10,y),(x+10,y-2)],local=sh)\n  elif kind=='D':\n   self.poly");tree=ast.parse(source);env={'BLUE':'#173d70','RED':'#8b2323','GREEN':'#14803c'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef))],type_ignores=[]),'<drawing-helper>','exec'),env)
rows=list(csv.DictReader((BASE/'schematic/System_BOM_R4.csv').open(encoding='utf-8-sig')))
for r in rows:
 if r['位号'] in ['J1P','J1N','J2P','J2N','J4P','J4N','JPP','JPN'] and '板凳' in r['推荐规格']:
  r['推荐规格']='单极四脚板凳式焊接接线柱；按实际负载/瞬态/保护核对承流';r['备注']+='；取消统一≥5A采购要求；不影响L1的Isat≥5A要求'
 if r['板']=='Control':
  if r['位号'] in ['R16','R17','R18','R19','R20','R21']:r.update({'厂家型号':'0805W8F1002T5E','立创料号':'C17414','推荐规格':'10kΩ ±1% 1/8W','封装':'0805','SMT库别':'基础库（沿用已核实料号）','备注':'补全主控建议选型，10k标称值不变，未绑定封装','来源':'https://jlcpcb.com/partdetail/C17414'})
  if r['位号'] in ['C15','C16','C17','C18','C19','C21']:r.update({'厂家型号':'CC0805KRX7R9BB104','立创料号':'C49678','推荐规格':'100nF 50V X7R ±10%','封装':'0805','SMT库别':'基础库（沿用已核实料号）','备注':'补全建议耐压/封装，100nF标称值不变；未绑定封装','来源':'https://jlcpcb.com/partdetail/C49678'})
  if r['位号'] in ['R14','R15']:r['封装']='0805';r['推荐规格']='4.7kΩ ±1% 1/8W';r['备注']+='；料号待核实'
  if r['位号']=='C20':r['封装']='0805候选，偏压容值待核';r['推荐规格']='4.7uF ≥10V X7R/X5R';r['备注']+='；完整料号待核实'
  if r['位号']=='C22':r['封装']='0805候选，偏压容值待核';r['推荐规格']='1uF ≥10V X7R/X5R';r['备注']+='；完整料号待核实'
  if r['位号']=='J1':r['厂家型号']='2.54-2*5P简牛 BOOMELE';r['立创料号']='C5665';r['封装']='THT 2x5 P2.54mm';r['推荐规格']='10针主板接口，接主板J3';r['SMT库别']='插件焊接，具体订单审核'
control=json.loads((P/'aux-posts-r3/references/generated/GBUCK_Control_R3/results/data/expected_mainboard_pins.json').read_text());aux=json.loads((BASE/'references/aux-conversion/results/data/expected_mainboard_pins.json').read_text())
orig=json.loads((P/'modular-v1-1/schematic/standard_json/C_MCU_LCD.json').read_text())['schematics'][0]['dataStr']['shape'];pinnames={}
for s in orig:
 if s.startswith('LIB~') and any(x.startswith('T~P~') and x.split('~')[12]=='U6' for x in s.split('#@$')[1:]):
  for x in s.split('#@$')[1:]:
   if x.startswith('P~'):pinnames[int(x.split('^^')[0].split('~')[3])]=x.split('^^')[3].split('~')[4]
plans={'Control':[(1,'供电输入与去耦',['JPP','JPN','C16','C17','C18','C19','C20']),(2,'MCU最小系统、复位与启动',['U6','R16','C15','R17','R18']),(3,'主板接口与I2C上拉',['J1','R14','R15']),(4,'PCD8544液晶接口与去耦',['JLCD','C21','C22']),(5,'按键与上拉',['R19','R20','R21','K1','K2','K3']),(6,'SWD下载调试',['JSWD'])], 'Auxiliary':[(1,'输入接线柱与输入滤波',['J1P','J1N','C23','C24','C27']),(2,'同步Buck与自举',['U7','L2','C25']),(3,'3.3V输出滤波与接线柱',['J2P','J2N','C26'])]}
for b,plan in plans.items():
 for n,title,refs in plan:
  for r in rows:
   if r['板']==b and r['位号'] in refs:r['功能区']=f'{n:02d} {title}'
for r in rows:r['核对日期']='2026-11-08'
with (R/'schematic/System_BOM_R5.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
audit=[]
for board,expected in [('Control',control),('Auxiliary',aux)]:
 localrows=[r for r in rows if r['板']==board];env['selection']={r['位号']:r for r in localrows};env['expected']=expected;env['bom']={r['位号']:{'Part_or_value':('100nF 50V' if r['位号'] in ['C15','C16','C17','C18','C19','C21'] else r['原标称']),'Recommended_footprint':r['封装']} for r in localrows}
 # Source original-value column describes replaced interfaces rather than their actual value.
 for ref in expected:
  if ref.startswith(('JPP','JPN','J1P','J1N','J2P','J2N')):env['bom'][ref]['Part_or_value']='BENCH POST 4P - TBD'
 if board=='Control':env['bom']['J1']['Part_or_value']='TO MAINBOARD J3'
 if board=='Auxiliary':
  vals={'U7':'TPS560430X3FDBVR','L2':'12uH Isat>=2A','C23':'10uF 50V X7R','C24':'100nF 50V','C25':'100nF 50V','C26':'22uF 25V X7R','C27':'22uF 50V AL SMD'}
  for r,v in vals.items():env['bom'][r]['Part_or_value']=v
 D=env['Drawing']();D.text(35,40,('主控板R5：六功能区' if board=='Control' else '辅助降压板R5：三区 / 自设计3.3V'),26);D.text(35,70,'同一图页中的功能区属于同一块独立PCB；引脚网络沿用R4；本图不是PCB布局。',13)
 def zone(n):
  _,title,_=plans[board][n-1];D.zone(n,title,20 if n%2 else 1510,100+1040*((n-1)//2))
 def passive(ref,x,y,vertical=False,kind='R'):
  D.passive(ref,x,y,kind,vertical)
  for num,net in expected[ref].items():
   xx,yy=D.p(ref,num)
   if net=='NC':continue
   end=(xx,yy-30 if int(num)==1 else yy+30) if vertical else (xx-60 if int(num)==1 else xx+60,yy)
   D.wire((xx,yy),end);D.label(*end,net,'start' if vertical or int(num)!=1 else 'end')
 def connector(ref,x,y):
  D.connector(ref,x,y,[expected[ref][n] for n in expected[ref]])
  for n,net in expected[ref].items():
   xx,yy=D.p(ref,n)
   if net!='NC':D.wire((xx-100,yy),(xx,yy));D.label(xx-100,yy,net,'end')
 if board=='Control':
  zone(1);connector('JPP',220,160);connector('JPN',220,410)
  for ref,x in [('C16',500),('C17',680),('C18',860),('C19',1040),('C20',1220)]:
   D.passive(ref,x,500,'C',True);D.wire((x,350),D.p(ref,1));D.wire(D.p(ref,2),(x,700))
  D.wire((500,350),(1320,350));D.label(1320,350,'+3V3');D.wire((500,700),(1320,700));D.label(1320,700,'GND')
  D.text(50,820,'C16/C17/C18/C19分别紧贴U6.24/.36/.48/.9；C20靠近MCU。',13);D.text(50,860,'JPP接辅源J2P（3.3V）；JPN接辅源J2N；不接15–25V。',13)
  zone(2)
  pp=[]
  for n in range(1,49):
   right=n>24;i=n-25 if right else n-1;y=210+25*i;x=1250 if right else 870;b=1230 if right else 890
   pp.append((n,pinnames[n],(x,y),(b,y)))
  D.chip('U6',890,175,340,660,pp)
  for n,net in expected['U6'].items():
   if net=='NC':continue
   x,y=D.p('U6',n);end=(x+80,y) if int(n)>24 else (x-80,y);D.wire((x,y),end);D.label(*end,net,'start' if int(n)>24 else 'end')
  passive('R16',330,230);D.passive('C15',220,380,'C',True);D.wire((220,230),D.p('R16',1));D.wire((220,230),D.p('C15',1));D.wire(D.p('C15',2),(220,480));D.label(220,480,'GND')
  passive('R17',330,620);passive('R18',330,760)
  D.text(50,910,'内部8MHz HSI；未用脚NC；BOOT0/BOOT1下拉；复位上拉＋100nF。',13)
  zone(3);connector('J1',330,180);passive('R14',900,320);passive('R15',900,500)
  D.text(50,790,'J1与主功率板J3采用10芯直通排线，同脚号连接。',13);D.text(50,830,'1 +3V3 / 2 GND / 3 SCL / 4 SDA / 5 VSET_DRV / 6 CC_OUT',13);D.text(50,865,'7 ISENSE / 8 VOUT_ADC / 9 RUN / 10 GND；5/6仅测试，不能GPIO驱动。',13);D.text(50,900,'R14/R15为I2C上拉；全系统在此保留一组，不重复加上拉。',13)
  zone(4);connector('JLCD',350,180);D.passive('C21',900,390,'C',True);D.passive('C22',1150,390,'C',True)
  for ref,x in [('C21',900),('C22',1150)]:D.wire((x,250),D.p(ref,1));D.wire(D.p(ref,2),(x,600))
  D.wire((900,250),(1300,250));D.label(1300,250,'+3V3');D.wire((900,600),(1300,600));D.label(1300,600,'GND')
  D.text(50,780,'JLCD是8针接口，不包含液晶模块内部电路；实物脚序须逐一核对。',13);D.text(50,820,'RST / CE / DC / DIN / CLK / 3.3V / NC / GND，保留原脚序。',13);D.text(50,860,'C21/C22靠近液晶接口；背光脚保持NC，不能随意改接3.3V。',13)
  zone(5)
  for ref,k,x,net in [('R19','K1',300,'KEY_SET'),('R20','K2',740,'KEY_UP'),('R21','K3',1180,'KEY_DOWN')]:
   passive(ref,x,260);passive(k,x,500,False,'K');D.wire((x-90,260),(x-150,260),(x-150,500),(x-90,500));D.label(x-150,380,net)
  D.text(50,760,'按下接地；R19/R20/R21上拉；软件消抖。实际按键必须选常开触点。',13);D.text(50,800,'K1选择设定项，K2增加，K3减少；不改变现有引脚与固件接口。',13)
  zone(6);connector('JSWD',400,240)
  D.text(50,650,'1 +3V3（参考） / 2 SWDIO / 3 GND / 4 SWCLK。',13);D.text(50,690,'JSWD.1为调试器电平参考；主板供电来自辅助电源，不用下载器并联供电。',13);D.text(50,730,'PA13=SWDIO（U6.34），PA14=SWCLK（U6.37）。',13)
 else:
  zone(1);connector('J1P',220,160);connector('J1N',220,420)
  for ref,x in [('C23',650),('C24',900),('C27',1150)]:
   D.passive(ref,x,430,'C',True);D.wire((x,230),D.p(ref,1));D.wire(D.p(ref,2),(x,700))
  D.wire((650,230),(1350,230));D.label(1350,230,'VIN_SYS');D.wire((650,700),(1350,700));D.label(1350,700,'GND');D.text(1175,405,'+',15)
  D.text(50,840,'J1P/J1N接主板J4P/J4N；15–25V输入；C27为输入贴片电解，1正2负。',13)
  zone(2);D.chip('U7',460,280,240,260,[(5,'VIN',(440,320),(460,320)),(4,'EN',(440,390),(460,390)),(2,'GND',(520,560),(520,540)),(1,'CB',(720,360),(700,360)),(6,'SW',(720,320),(700,320)),(3,'FB',(720,470),(700,470))])
  D.wire((220,320),D.p('U7',5));D.label(220,320,'VIN_SYS');D.wire((300,320),(300,390),D.p('U7',4));D.dot(300,320)
  D.wire(D.p('U7',2),(520,700));D.label(520,700,'GND')
  D.passive('L2',1040,320,'L');D.wire(D.p('U7',6),D.p('L2',1));D.label(750,320,'SW_AUX');D.wire(D.p('L2',2),(1280,320));D.label(1280,320,'+3V3')
  D.wire(D.p('U7',3),(1190,470),(1190,320));D.dot(1190,320)
  D.passive('C25',850,360,'C');D.wire(D.p('U7',1),D.p('C25',1));D.label(730,360,'CB_AUX');D.wire(D.p('C25',2),(930,360),(930,320));D.dot(930,320)
  D.text(50,800,'U7固定3.3V版本：FB直接接输出，不装分压；EN接VIN，上电自启。',13);D.text(50,840,'C25位于CB与SW之间，不能接地；L2=12uH；未做环路实测。',13)
  zone(3);connector('J2P',1120,160);connector('J2N',1120,500);D.passive('C26',600,440,'C',True)
  D.wire((300,230),(800,230),(800,410),D.p('C26',1));D.label(300,230,'+3V3');D.wire(D.p('C26',2),(600,700));D.label(600,700,'GND')
  D.text(50,820,'J2P接主控JPP，J2N接主控JPN；输出固定3.3V；整板0.3A为待验证目标。',13);D.text(50,860,'C26=22uF/25V/X7R；实际偏压容量、纹波、启动和温升仍需复核。',13)
  D.ox,D.oy=1510,1140;D.rect(5,5,1450,1010,color='#6b879c');D.text(40,60,'板间拼装与制造核对',22)
  for y,t in [(160,'主板J4P/J4N → 辅源J1P/J1N（15–25V）'),(220,'辅源J2P/J2N → 主控JPP/JPN（3.3V）'),(280,'主控J1 ↔ 主板J3（10芯直通排线）'),(390,'每只板凳柱四脚同网；不是四路接口。'),(450,'保留插件件由工厂焊接，具体型号/焊接服务须订单审核。'),(510,'本图不是PCB布局，不代表已绑定封装或可制板。')]:D.text(50,y,t,16)
 assert set(D.parts)==set(expected),(board,set(D.parts)^set(expected))
 for ref,pins in expected.items():assert set(pins)=={n for r,n in D.positions if r==ref},ref
 stage=R/'references/generated'/board
 for d in ['tools','results/data','schematic/native']:(stage/d).mkdir(parents=True,exist_ok=True)
 data={'head':{'docType':'1','editorVersion':'6.5.51','newgId':True,'c_para':{'Prefix Start':'1'},'c_spiceCmd':None,'x':'0','y':'0','hasIdFlag':False},'canvas':'CA~3000~3240~#FFFFFF~yes~#CCCCCC~5~3000~3240~line~5~pixel~5~0~0','shape':D.shapes,'BBox':{'x':0,'y':0,'width':3000,'height':3240 if board=='Control' else 2200},'colors':{}}
 doc={'editorVersion':'6.5.51','docType':'5','title':board+'_R5','description':'Conversion source; primary deliverable eprj3','colors':{},'schematics':[{'docType':'1','title':board+'_Blocks','description':'','dataStr':data}]}
 (stage/'schematic/native/Mainboard_Functional_Blocks.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2));(stage/'results/data/expected_mainboard_pins.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
 (R/'results/data'/f'{board}_blocks.json').write_text(json.dumps({'components':D.parts,'zones':D.zones},ensure_ascii=False,indent=2))
 def svg(x,y,w,h):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x} {y} {w} {h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/><g font-family="Noto Sans CJK SC,Arial,sans-serif">'+''.join(D.svg)+'</g></svg>'
 pre=R/'schematic/previews'/board;pre.mkdir(parents=True,exist_ok=True)
 (pre/'All.svg').write_text(svg(0,0,3000,data['BBox']['height']))
 for z in D.zones:(pre/f'{z["number"]:02d}_Block.svg').write_text(svg(z['x'],z['y'],z['width'],z['height']))
 with (stage/'schematic/BOM_ByReference_R2.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=localrows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(localrows)
 shutil.copy(P/'mainboard-r2/tools/verify_connections.py',stage/'tools/verify_connections.py')
 name='GBUCK_'+board+'_R5';template=BASE/'references/aux-conversion/tools/convert_pro_eprj3.py';s=template.read_text().replace('GBUCK_Aux_R4',name).replace("title='Aux_Power'",f"title='{board}_Blocks'").replace("'sch/Auxiliary'",f"'sch/{board}'").replace("'title':'Auxiliary'",f"'title':'{board}'").replace("'name':'Auxiliary'",f"'name':'{board}'").replace("'Auxiliary.ecfg'",f"'{board}.ecfg'").replace('Auxiliary_R4',board+'_R5');(stage/'tools/convert_pro_eprj3.py').write_text(s)
 subprocess.run([sys.executable,str(stage/'tools/convert_pro_eprj3.py'),str(stage)],check=True)
 v=(BASE/'references/aux-conversion/tools/verify_pro_eprj3.py').read_text().replace('GBUCK_Aux_R4',name).replace('R4 self-designed auxiliary expected pins; other boards unchanged','R5: all component pin maps equal R4 baseline')
 (stage/'tools/verify_pro_eprj3.py').write_text(v);subprocess.run([sys.executable,str(stage/'tools/verify_pro_eprj3.py'),str(stage)],check=True)
 shutil.copy(stage/'results/data/pro_connectivity_report.json',R/'results/data'/f'{board}_connectivity.json')
 audit.append({'board':board,'components':len(expected),'pins':sum(map(len,expected.values())),'zones':len(plans[board]),'pin_map_equals_R4':True})
project=R/'schematic/pro/GBUCK_System_R5';project.mkdir(parents=True,exist_ok=True);idx=json.loads((BASE/'schematic/pro/GBUCK_System_R4/GBUCK_System_R4.eprj3').read_text())
# Keep main power page geometry; only remove superseded >=5A connector procurement wording.
shutil.copytree(BASE/'schematic/pro/GBUCK_System_R4/sch/Mainboard',project/'sch/Mainboard',dirs_exist_ok=True)
for file in (project/'sch/Mainboard').glob('*.esch2'):
 out=[]
 for line in file.read_text().splitlines():
  a,b=map(json.loads,line[:-1].split('||',1))
  if a['type']=='META' and '待定' in b.get('title','') and 'attributes' in b:b['attributes']['Value']=b['attributes'].get('Value','').replace('≥5A','按实际负载/保护核定承流')
  out.append(json.dumps(a,ensure_ascii=False,separators=(',',':'))+'||'+json.dumps(b,ensure_ascii=False,separators=(',',':'))+'|\n')
 file.write_text(''.join(out))
for key in ['boards','schematics','sheets']:
 keep={}
 for id,r in idx['profile'][key].items():
  if (key=='boards' and r.get('title')=='Mainboard_R3') or (key=='schematics' and r.get('name')=='Mainboard') or (key=='sheets' and r.get('title')=='Mainboard_6_Blocks'):keep[id]=r
 idx['profile'][key]=keep
for board in ['Control','Auxiliary']:
 pp=R/'references/generated'/board/'schematic/pro'/('GBUCK_'+board+'_R5');other=json.loads(next(pp.glob('*.eprj3')).read_text());shutil.copytree(pp/'sch',project/'sch',dirs_exist_ok=True)
 for key in ['boards','schematics','sheets']:idx['profile'][key].update(other['profile'][key])
idx['name']='GBUCK_System_R5';idx['content']='R5主控六区/辅源三区；81件291脚，参数与网络沿用R4；封装未绑定'
(project/'GBUCK_System_R5.eprj3').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n');(R/'results/data/revision_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print('R5 complete: control25/116/6zones + auxiliary11/34/3zones; unchanged pin maps')
