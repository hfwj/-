"""Build the removable controller carrier; R5 power and auxiliary sheets are preserved."""
from pathlib import Path
import ast, csv, json, shutil, subprocess, sys

P = Path('projects/2026-electronics-contest/g-buck')
R = P/'bluepill-carrier-r7'
B = P/'partition-r5'
for d in ['schematic/pro', 'schematic/previews/Control', 'results/data', 'references/generated/Control/tools', 'downloads', 'firmware']:
    (R/d).mkdir(parents=True, exist_ok=True)
source = (P/'mainboard-r2/tools/generate_blocks.py').read_text().replace('同一块主板上的功能区', '同一块主控底板上的功能区')
source = source.replace("elif kind=='D':\n   self.poly", "elif kind=='K':\n   self.poly([(x-10,y),(x+7,y-10)],local=sh);self.poly([(x+10,y),(x+10,y-2)],local=sh)\n  elif kind=='D':\n   self.poly")
env = {'BLUE':'#173d70', 'RED':'#8b2323', 'GREEN':'#14803c'}
tree = ast.parse(source)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef))], type_ignores=[]), '<drawing-helper>', 'exec'), env)
old = json.loads((B/'references/generated/Control/results/data/expected_mainboard_pins.json').read_text())
removed = ['U6','R16','C15','R17','R18','C16','C17','C18','C19','JSWD']
expected = {r:p for r,p in old.items() if r not in removed}
# Carrier-assigned P1/P2 numbering: component top view, USB left, each row left to right.
# User's product pinout/dimension screenshots + explicit confirmation that P1.1 is GND.
# P1/P2 are our aliases for upper/lower rows, not asserted manufacturer connector IDs.
module = {
    'P1':['GND','GND','3V3','NRST','PB11','PB10','PB1','PB0','PA7','PA6','PA5','PA4','PA3','PA2','PA1','PA0','PC15','PC14','PC13','VB'],
    'P2':['PB12','PB13','PB14','PB15','PA8','PA9','PA10','PA11','PA12','PA15','PB3','PB4','PB5','PB6','PB7','PB8','PB9','5V','GND','3V3'],
    'P3':['3V3','SWDIO','SWCLK','GND'],
}
gpio = {'PA1':'ISENSE','PA2':'VOUT_ADC','PA4':'LCD_CE','PA5':'LCD_CLK','PA7':'LCD_DIN','PB0':'LCD_DC','PB1':'LCD_RST','PA8':'RUN','PA9':'KEY_SET','PA10':'KEY_UP','PB10':'KEY_DOWN','PB6':'SCL','PB7':'SDA','3V3':'+3V3','GND':'GND'}
for j,p in [('JCORE1','P1'),('JCORE2','P2')]:
    expected[j] = {str(i):gpio.get(n,'NC') for i,n in enumerate(module[p],1)}
expected['JLCD'] = dict(zip(map(str,range(1,9)), ['GND','GND','+3V3','LCD_CLK','LCD_DIN','LCD_DC','LCD_CE','LCD_RST']))
plan = [(1,'供电接线柱与底板储能',['JPP','JPN','C20']),
        (2,'可拔插用户选购Blue Pill：两条20针排母',['JCORE1','JCORE2']),
        (3,'主功率板接口与I2C上拉',['J1','R14','R15']),
        (4,'可拔插Joy-IT Rev.2屏幕',['JLCD','C21','C22']),
        (5,'三个操作按键与上拉',['R19','R20','R21','K1','K2','K3']),
        (6,'供电、SWD与装配说明',[])]
rows = list(csv.DictReader((B/'schematic/System_BOM_R5.csv').open(encoding='utf-8-sig')))
rows = [r for r in rows if not (r['板']=='Control' and r['位号'] in removed)]
example = next(r for r in rows if r['板']=='Control' and r['位号']=='JLCD')
for ref in ['JCORE1','JCORE2']:
    r = dict(example)
    r.update({'位号':ref,'原标称':'新增核心板插座','厂家型号':'M20-7822046','立创料号':'未核实','推荐规格':'Harwin 1x20排母 P2.54mm；0.64mm方针；板上高8.5mm','封装':'THT 1x20 P2.54mm；3mm焊尾；封装待绑定','SMT库别':'通孔件，非SMT基础库；代焊需订单审核','备注':'两条排母承接用户选购STM32F103C8T6 Blue Pill；排间距15.24mm；USB朝左上排首针GND（用户确认）；非2x20连接器','来源':'https://www.harwin.com/products/M20-7822046'})
    rows.append(r)
for r in rows:
    if r['板']!='Control': continue
    r['核对日期']='2026-11-09'
    r['功能区']=next(f'{n:02d} {t}' for n,t,refs in plan if r['位号'] in refs)
    if r['位号']=='JLCD':
        r.update({'厂家型号':'M20-7820846','立创料号':'未核实','原标称':'8针屏幕接口','推荐规格':'Harwin 1x8排母 P2.54mm；配Joy-IT SBC-LCD84x48 Rev.2','封装':'THT 1x8 P2.54mm；3mm焊尾；封装待绑定','SMT库别':'通孔件，非SMT基础库；代焊需订单审核','备注':'新脚序：1GND/2LIGHT接GND/3VCC/4CLK/5DIN/6DC/7CE/8RST；禁止接Rev.1；模块需带已焊排针；装配前确认针距、方向、插入长度','来源':'https://www.harwin.com/products/M20-7820846'})
    if r['位号']=='C20': r['备注']='保留4.7uF底板储能，放在核心板插座电源入口；模块内部去耦不在底板重复计数；完整料号/有效容值待核'
    if r['位号'] in ['K3','R21']: r['备注']+='；KEY_DOWN现在接核心板PB10，原PA11保留给USB'
local = [r for r in rows if r['板']=='Control']
assert set(expected)=={r['位号'] for r in local}
def csvwrite(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=data[0].keys(),lineterminator='\n');w.writeheader();w.writerows(data)
csvwrite(R/'schematic/System_BOM_R7.csv',rows)
csvwrite(R/'schematic/Control_Carrier_BOM_R7.csv',local)
modules = [
    {'位号':'MCORE','数量':1,'厂家':'卖家未明确；须按用户截图同款交付','型号':'STM32F103C8T6 Blue Pill最小系统板（USB端上排首针GND版）','装配':'现成核心板，需已焊两条1x20直排针；插入JCORE1/JCORE2','接口':'两排各20针，节距2.54mm，排间距15.24mm；模块端部四针SWD','采购约束':'锁定用户截图同款：上排USB端前两针GND，第三针3.3V；核对芯片确为ST STM32F103C8T6；BOOT0/BOOT1正常运行置0；不同板型重新适配','基础库':'成品模块，非SMT基础库；单独采购；不承诺代插装','来源':'用户提供的商品引脚图/尺寸图及首针GND确认；未提供厂家原理图'},
    {'位号':'MLCD','数量':1,'厂家':'Joy-IT','型号':'SBC-LCD84x48 Revision 2 / PCD8544','装配':'现成84x48液晶，需已焊1x8直排针；插入JLCD','接口':'8针；仅3.3V逻辑/供电；Rev.2专用脚序','采购约束':'锁定Revision 2；到货按原厂手册逐脚核对；确认针距2.54mm及针长可配排母','基础库':'成品模块，非SMT基础库；单独采购；不承诺代插装','来源':'https://joy-it.net/en/products/SBC-LCD84x48'},
]
csvwrite(R/'schematic/Plug_In_Modules_BOM_R7.csv',modules)
modulepins=[]
for j,p in [('JCORE1','P1'),('JCORE2','P2')]:
    for n,name in enumerate(module[p],1):
        modulepins.append({'插座':j,'底板脚号':n,'核心板接口':p,'本版自定脚号':n,'商品资料标注':name,'底板网络':expected[j][str(n)]})
csvwrite(R/'results/data/Core_Socket_Map_R7.csv',modulepins)
(R/'results/data/Module_Pinout_Evidence_R7.json').write_text(json.dumps({'core':module,'lcd_revision_2':['GND','LIGHT','VCC','CLK','DIN','DC','CE','RST'],'source':'用户商品截图（非厂家原理图）＋用户确认USB端上排首针GND','orientation':'元件面朝上，USB朝左，P1=上排，P2=下排，两排均从USB端编号1至20','row_pitch_mm':15.24,'pin_pitch_mm':2.54,'actual_board_verified':False},ensure_ascii=False,indent=2))
env.update(expected=expected, selection={r['位号']:r for r in local}, bom={r['位号']:{'Part_or_value':r['原标称'],'Recommended_footprint':r['封装']} for r in local})
values={'JPP':'3V3 BENCH POST 4P','JPN':'GND BENCH POST 4P','JCORE1':'BLUEPILL UPPER 1x20','JCORE2':'BLUEPILL LOWER 1x20','JLCD':'JOY-IT REV.2 SOCKET 1x8','J1':'TO MAINBOARD J3','C21':'100nF 50V'}
for ref,v in values.items():env['bom'][ref]['Part_or_value']=v
D=env['Drawing']()
D.text(35,40,'主控底板R7：现成核心板＋屏幕可拔插 / 六功能区',26)
D.text(35,70,'相对R6：换用户选购核心板，JCORE1.1改GND、排间距15.24mm；GPIO、屏幕及10针接口保留。',13)
def zone(n):
    _,title,_=plan[n-1];D.zone(n,title,20 if n%2 else 1510,100+1040*((n-1)//2))
def passive(ref,x,y,vertical=False,kind='R'):
    D.passive(ref,x,y,kind,vertical)
    for num,net in expected[ref].items():
        xx,yy=D.p(ref,num)
        end=(xx,yy-45 if int(num)==1 else yy+45) if vertical else (xx-70 if int(num)==1 else xx+70,yy)
        D.wire((xx,yy),end);D.label(*end,net,'start' if vertical or int(num)!=1 else 'end')
def connector(ref,x,y,names=None):
    names=names or list(expected[ref].values())
    # Pin names carry the actual module signal; numbered contacts remain physical pin numbers.
    pp=[(i,name,(x-20,y+35+(i-1)*30),(x,y+35+(i-1)*30)) for i,name in enumerate(names,1)]
    D.chip(ref,x,y,200 if ref.startswith('JCORE') else 120,30*len(names)+30,pp)
    for n,net in expected[ref].items():
        xx,yy=D.p(ref,n)
        if net!='NC':D.wire((xx-150,yy),(xx,yy));D.label(xx-150,yy,net,'end')
zone(1);connector('JPP',250,160);connector('JPN',250,440);passive('C20',1000,430,True,'C')
D.text(50,790,'JPP接辅助板J2P（3.3V），JPN接辅助板J2N；四脚同网。',14)
D.text(50,835,'核心板接3V3脚；JCORE1.1和.2均GND；JCORE2.18的5V脚在底板NC。',13)
D.text(50,880,'底板C20保留；MCU复位、启动、时钟与芯片去耦由现成核心板提供。',13)
zone(2);connector('JCORE1',360,150,module['P1']);connector('JCORE2',1040,150,module['P2'])
D.text(50,850,'MCORE：用户选购STM32F103C8T6 Blue Pill；BOOT0/BOOT1置0正常运行。',13)
D.text(50,890,'元件面向上、USB朝左：P1上排，P2下排；两排均从USB端编号1→20。',13)
D.text(50,930,'排间距15.24mm，节距2.54mm；上排前两针GND；末端SWD不在这两排中。',13)
zone(3);connector('J1',350,180);passive('R14',1000,320);passive('R15',1000,520)
for y,t in [(790,'J1与主功率板J3：10芯直通排线，同脚号连接。'),(835,'1 +3V3 / 2 GND / 3 SCL / 4 SDA / 5 VSET_DRV / 6 CC_OUT'),(880,'7 ISENSE / 8 VOUT_ADC / 9 RUN / 10 GND；5/6仅测试，不接GPIO。'),(925,'R14/R15各4.7k上拉；3.3V统一由辅助板供电。')]:D.text(50,y,t,13)
zone(4);connector('JLCD',370,160,['GND','LIGHT','VCC','CLK','DIN','DC','CE','RST']);passive('C21',950,390,True,'C');passive('C22',1200,390,True,'C')
for y,t in [(760,'MLCD：Joy-IT SBC-LCD84x48 Revision 2，PCD8544，84x48。'),(805,'1 GND / 2 LIGHT→GND / 3 3.3V / 4 CLK / 5 DIN / 6 DC / 7 CE / 8 RST。'),(850,'背光按原厂接法接地常亮；无需新增GPIO；禁止插Rev.1或按旧JLCD脚序接线。'),(895,'3.3V供电与逻辑；实际屏幕针距/针长、机械支撑及供电容差仍须实物核对。')]:D.text(50,y,t,13)
zone(5)
for ref,k,x,net in [('R19','K1',300,'KEY_SET'),('R20','K2',740,'KEY_UP'),('R21','K3',1180,'KEY_DOWN')]:
    passive(ref,x,260);passive(k,x,500,False,'K');D.wire((x-100,260),(x-150,260),(x-150,500),(x-100,500));D.label(x-150,380,net)
D.text(50,770,'K1选择项PA9；K2增加PA10；K3减少PB10；按下接地，软件消抖。',14)
D.text(50,815,'沿用R6：电压ADC为PA2/通道2，减小键PB10；不恢复旧R5脚位。',14)
D.text(50,860,'上电先置RUN为低，再初始化ADC、I2C与屏幕；原主板EN下拉保留。',13)
zone(6)
for y,t in [(140,'SWD直接使用核心板P3，不在底板重复加JSWD。'),(190,'核心板P3：1=3V3，2=SWDIO，3=SWCLK，4=GND。'),(240,'P3.1只给支持VTref的调试器作电平参考；不并联下载器电源。'),(330,'辅助3.3V供电时，不接USB；5V脚JCORE2.18保持悬空，不带外部负载。'),(380,'本板不沿用WeAct的SB1/U3约束；板载LDO型号/反灌与启动仍须实测。'),(470,'工厂焊底板排母、板凳柱等；成品模块需带已焊排针，再插装。'),(520,'排母不防反插；丝印标P1/P2、Pin1、USB端，断电插拔。'),(570,'模块下面禁布高件，预留USB、SWD、按键操作空间及机械支撑。'),(660,'沿用R6：底板不重复装U6最小系统及JSWD，保留C20储能。'),(710,'主功率板、辅助板及屏幕沿用R6；辅助电源仍为自设计3.3V。'),(800,'本图是连线原理图，不是PCB；未绑定封装、未做原生ERC/DRC或实测。')]:D.text(50,y,t,14)
assert set(D.parts)==set(expected)
stage=R/'references/generated/Control'
for d in ['schematic/native','results/data']:(stage/d).mkdir(parents=True,exist_ok=True)
data={'head':{'docType':'1','editorVersion':'6.5.51','newgId':True,'c_para':{'Prefix Start':'1'},'c_spiceCmd':None,'x':'0','y':'0','hasIdFlag':False},'canvas':'CA~3000~3240~#FFFFFF~yes~#CCCCCC~5~3000~3240~line~5~pixel~5~0~0','shape':D.shapes,'BBox':{'x':0,'y':0,'width':3000,'height':3240},'colors':{}}
doc={'editorVersion':'6.5.51','docType':'5','title':'Control_R7','description':'Conversion source; deliver native Pro eprj3','colors':{},'schematics':[{'docType':'1','title':'Control_Sockets_R7','description':'','dataStr':data}]}
(stage/'schematic/native/Mainboard_Functional_Blocks.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2))
(stage/'results/data/expected_mainboard_pins.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2))
(R/'results/data/Control_blocks.json').write_text(json.dumps({'components':D.parts,'zones':D.zones},ensure_ascii=False,indent=2))
pre=R/'schematic/previews/Control'
def svg(x,y,w,h):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{x} {y} {w} {h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/><g font-family="Noto Sans CJK SC,Arial,sans-serif">'+''.join(D.svg)+'</g></svg>'
(pre/'All.svg').write_text(svg(0,0,3000,3240))
for z in D.zones:(pre/f'{z["number"]:02d}_Block.svg').write_text(svg(z['x'],z['y'],z['width'],z['height']))
csvwrite(stage/'schematic/BOM_ByReference_R2.csv',local)
for filename in ['verify_connections.py','convert_pro_eprj3.py','verify_pro_eprj3.py']:
    s=(B/'references/generated/Control/tools'/filename).read_text().replace('GBUCK_Control_R5','GBUCK_Control_R7').replace('Control_R5','Control_R7').replace("title='Control_Blocks'","title='Control_Sockets_R7'").replace('R5: all component pin maps equal R4 baseline','R7 user-selected core: JCORE1.1 NC to GND; GPIO unchanged from R6')
    s=s.replace('Embedded R2 symbol.', 'Embedded R7 carrier symbol.').replace('GBUCK_R2','GBUCK_R7').replace('R4 self-designed auxiliary buck; footprints TBD','R7 removable controller carrier; footprints TBD').replace("'source':'d38634b Std R2'", "'source':'R7 carrier geometry based on R5, user product pinout and confirmed first contact'")
    (stage/'tools'/filename).write_text(s)
subprocess.run([sys.executable,str(stage/'tools/convert_pro_eprj3.py'),str(stage)],check=True)
subprocess.run([sys.executable,str(stage/'tools/verify_pro_eprj3.py'),str(stage)],check=True)
shutil.copy(stage/'results/data/pro_connectivity_report.json',R/'results/data/Control_connectivity.json')
project=R/'schematic/pro/GBUCK_System_R7';project.mkdir(parents=True,exist_ok=True)
oldproject=B/'schematic/pro/GBUCK_System_R5'
idx=json.loads((oldproject/'GBUCK_System_R5.eprj3').read_text())
for board in ['Mainboard','Auxiliary']:shutil.copytree(oldproject/'sch'/board,project/'sch'/board,dirs_exist_ok=True)
coreproject=stage/'schematic/pro/GBUCK_Control_R7'
other=json.loads((coreproject/'GBUCK_Control_R7.eprj3').read_text())
oldsch={k for k,v in idx['profile']['schematics'].items() if v['name']=='Control'}
oldboards={v['board'] for k,v in idx['profile']['schematics'].items() if k in oldsch}
for key in ['boards','schematics','sheets']:
    idx['profile'][key]={k:v for k,v in idx['profile'][key].items() if not (key=='boards' and k in oldboards or key=='schematics' and k in oldsch or key=='sheets' and v['schematic_uuid'] in oldsch)}
    idx['profile'][key].update(other['profile'][key])
shutil.copytree(coreproject/'sch',project/'sch',dirs_exist_ok=True)
idx.update(name='GBUCK_System_R7',content='R7 user-selected Blue Pill: USB-end upper contact GND, row pitch15.24mm; display unchanged; footprints unbound')
idx['default_sheet']=other['default_sheet'];idx['config']['defaultSheet']=other['default_sheet']
(project/'GBUCK_System_R7.eprj3').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
shutil.copytree(coreproject,R/'schematic/pro/GBUCK_Control_R7',dirs_exist_ok=True)
pins=[{'板':'Control','位号':r,'脚号':n,'网络':v} for r,nn in expected.items() for n,v in nn.items()]
csvwrite(R/'results/data/Carrier_All_Pins_R7.csv',pins)
audit={'baseline':'75ab883 R5 actual schematic; 78c6cb6 pending R7 requirements','carrier_components':len(expected),'carrier_pins':len(pins),'carrier_NC':sum(p['网络']=='NC' for p in pins),'system_board_mounted_components':len(rows),'plug_in_modules':2,'removed_carrier_refs':removed,'GPIO_changes':{'VOUT_ADC':['PA0/ADC_IN0','PA2/ADC_IN2'],'KEY_DOWN':['PA11','PB10']},'main_auxiliary_sheets_byte_identical_to_R5':True,'IDC_J1_equals_R5':expected['J1']==old['J1'],'native_editor_ERC':False,'footprints_bound':False,'PCB':False,'hardware_test':False}
for board in ['Mainboard','Auxiliary']:
    for f in (oldproject/'sch'/board).glob('*'):assert f.read_bytes()==(project/'sch'/board/f.name).read_bytes()
assert expected['J1']==old['J1']
(R/'results/data/revision_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print(json.dumps(audit,ensure_ascii=False,indent=2))

# Independent R6->R7 change audit: exactly one carrier pin changes net.
base=P/'socket-adaptation-r6'
prev=json.loads((base/'references/generated/Control/results/data/expected_mainboard_pins.json').read_text())
delta=[{'ref':r,'pin':n,'R6':prev[r][n],'R7':v} for r,pp in expected.items() for n,v in pp.items() if prev[r][n]!=v]
assert delta==[{'ref':'JCORE1','pin':'1','R6':'NC','R7':'GND'}],delta
for board in ['Mainboard','Auxiliary']:
 for f in (base/'schematic/pro/GBUCK_System_R6/sch'/board).glob('*'):
  assert f.read_bytes()==(project/'sch'/board/f.name).read_bytes()
audit['historical_removed_carrier_refs_from_R5']=audit['removed_carrier_refs']
audit['removed_carrier_refs']=[]
audit.update(baseline='2fcaa7d R6',carrier_pin_changes=delta,carrier_NC=22,GPIO_changes={},GPIO_unchanged_from_R6=True,core_module_replaced=True,row_spacing_mm={'R6':15.22,'R7':15.24},main_auxiliary_sheets_byte_identical_to_R6=True,screen_pin_map_equals_R6=expected['JLCD']==prev['JLCD'],removed_carrier_refs_since_R6=[],core_identity_verified_by='user screenshots and first-contact GND confirmation; no actual board test',official_viewer='NOT RUN FOR R7')
(R/'results/data/revision_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print('R6->R7 delta:',delta)
