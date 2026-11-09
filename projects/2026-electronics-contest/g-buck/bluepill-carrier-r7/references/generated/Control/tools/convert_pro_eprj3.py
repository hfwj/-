"""Convert validated EasyEDA Std R2 geometry into native Pro folder project.
Reference: easyeda/easyeda-pro-eprj3-format and easyeda/easyeda-format-skill.
"""
from pathlib import Path
import json,csv,hashlib,sys,runpy,math,re,datetime
ROOT=Path(sys.argv[1]).resolve();DEST=ROOT/'schematic/pro/GBUCK_Control_R7';DEST.mkdir(parents=True,exist_ok=True)
sys.argv=[str(ROOT/'tools/verify_connections.py'),str(ROOT)]
ctx=runpy.run_path(str(ROOT/'tools/verify_connections.py'))
std=json.loads((ROOT/'schematic/native/Mainboard_Functional_Blocks.json').read_text())['schematics'][0]['dataStr']['shape']
expected=json.loads((ROOT/'results/data/expected_mainboard_pins.json').read_text())
bom={r['位号']:r for r in csv.DictReader((ROOT/'schematic/BOM_ByReference_R2.csv').open(encoding='utf-8-sig'))}
def uid(s):return hashlib.sha256(('GBUCK_Control_R7/'+s).encode()).hexdigest()[:16]
client=uid('client');board=uid('board');sch=uid('schematic');page=uid('page');name='GBUCK_Control_R7';title='Control_Sockets_R7';now=int(datetime.datetime.now().timestamp()*1000)
def dumps(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
class Doc:
 def __init__(self,kind,id):
  self.kind=kind;self.id=id;self.lines=[];self.n=0;self.counter=0
  self.emit('DOCHEAD',{'docType':kind,'uuid':id,'client':client,'updateTime':now,'version':str(now),'editVersion':'3.2.91'},None)
  if kind in ['SYMBOL','SCH_PAGE']:self.emit('CANVAS',{'originX':0,'originY':0,'yAxisDirection':'up'},'CANVAS')
 def emit(self,t,p,id='auto'):
  self.n+=1
  if id=='auto':self.counter+=1;id=uid(f'{self.id}/{self.counter}/{t}')
  out={'type':t,'ticket':self.n}
  if id is not None:out['id']=id
  self.lines.append(dumps(out)+'||'+dumps(p)+'|\n');return id
 def base(self):return {'groupId':'','locked':False,'zIndex':self.n+1,'yAxisDirection':'up'}
 def attr(self,parent,key,val,x=None,y=None,size=10,visible=False,align='LEFT_BOTTOM',part=None):
  p={**self.base(),'parentId':parent,'key':key,'value':str(val),'keyVisible':False,'valueVisible':visible,'x':x,'y':y,'rotation':0,'color':'#173d70','fillColor':None,'fontFamily':'Noto Sans CJK SC','fontSize':size,'strikeout':False,'underline':False,'italic':False,'fontWeight':False,'align':align}
  if part:p['partId']=part
  return self.emit('ATTR',p)
 def text(self,s,x,y,size=11,align='LEFT_BOTTOM',color='#173d70',part=None):
  p={**self.base(),'x':x,'y':y,'rotation':0,'value':s,'color':color,'fillColor':None,'fontFamily':'Noto Sans CJK SC','fontSize':size,'strikeout':False,'underline':False,'italic':False,'fontWeight':False,'align':align}
  if part:p['partId']=part
  self.emit('TEXT',p)
 def poly(self,pts,color='#8b2323',width=1,part=None):
  p={**self.base(),'points':[{'x':x,'y':y} for x,y in pts],'closed':False,'startShape':None,'endShape':None,'strokeColor':color,'strokeStyle':'SOLID','fillColor':'','strokeWidth':width,'fillStyle':'NONE'}
  if part:p['partId']=part
  self.emit('POLY',p)
pageDoc=Doc('SCH_PAGE',page);pageDoc.emit('META',{'title':title,'schematic':sch,'source':'','zIndex':1},'META')
symbols=[];devices=[];mapped={};symbol_pin_ids={}
def shape_geometry(doc,s,ox=0,oy=0,part=None):
 a=s.split('~');typ=a[0]
 def P(x,y):return float(x)-ox,-(float(y)-oy)
 if typ=='PL':
  v=list(map(float,a[1].split()));doc.poly([P(x,y) for x,y in zip(v[::2],v[1::2])],a[2],float(a[3]),part)
 elif typ=='R':
  x,y=float(a[1]),float(a[2]);w,h=float(a[5]),float(a[6]);doc.poly([P(x,y),P(x+w,y),P(x+w,y+h),P(x,y+h),P(x,y)],a[7],1,part)
 elif typ=='T':
  doc.text(a[12],*P(a[2],a[3]),float(a[7].replace('pt','')), 'RIGHT_BOTTOM' if a[14]=='end' else 'LEFT_BOTTOM',a[5],part)
for shape in std:
 a=shape.split('~')
 if a[0]!='LIB':continue
 children=shape.split('#@$')[1:];ref=next(c.split('~')[12] for c in children if c.startswith('T~P~'));ox,oy=float(a[1]),float(a[2]);symid=uid('symbol/'+ref);devid=uid('device/'+ref);part=uid('part/'+ref);comp=uid('component/'+ref)
 sym=Doc('SYMBOL',symid);sym.emit('META',{'title':ref+'_'+bom[ref]['厂家型号'],'description':'Embedded R7 carrier symbol. Footprint not assigned.','tags':['GBUCK_R7'],'source':'','docType':2},'META');sym.emit('PART',{'title':''},part)
 sym.attr(part,'Symbol',symid,part=part);sym.attr(part,'Designator',ref,part=part);sym.attr(part,'Device',devid,part=part)
 pins={}
 for child in children:
  if child.startswith(('T~P~','T~N~')):continue
  if not child.startswith('P~'):shape_geometry(sym,child,ox,oy,part);continue
  seg=child.split('^^');conf=seg[0].split('~');num=conf[3];x,y=map(float,seg[1].split('~'));end=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',seg[2].split('~')[0])));X,Y=end[-2:];pid=uid('pin/'+ref+'/'+num);rotation=round(math.degrees(math.atan2(-(Y-y),X-x)))%360
  sym.emit('PIN',{**sym.base(),'partId':part,'display':True,'x':x-ox,'y':-(y-oy),'length':math.hypot(X-x,Y-y),'rotation':rotation,'color':'#8b2323','pinShape':'NONE'},pid)
  for section,key in [(seg[3],'Pin Name'),(seg[4],'Pin Number')]:
   ss=section.split('~');sym.attr(pid,key,ss[4],float(ss[1])-ox,-(float(ss[2])-oy),float(ss[7].replace('pt','')),ss[0]=='1','RIGHT_BOTTOM' if ss[5]=='end' else 'LEFT_BOTTOM',part)
  sym.attr(pid,'Pin Type','INOUT',part=part)
  pins[num]=pid;mapped[ref,num]=(x,-y)
 symbols.append(sym);symbol_pin_ids[ref]=pins
 dev=Doc('DEVICE',devid);dev.emit('META',{'title':bom[ref]['厂家型号'],'source':'','tags':['GBUCK_R7'],'images':[],'attributes':{'Symbol':symid,'Value':bom[ref]['推荐规格'],'Supplier Part':bom[ref]['立创料号'],'Manufacturer Part':bom[ref]['厂家型号'],'Recommended footprint':bom[ref]['封装'],'Footprint':''}},'META');devices.append(dev)
 payload={**pageDoc.base(),'partId':part,'x':ox,'y':-oy,'rotation':0,'isMirror':False,'attrs':{}}
 for key,vals in [('DeviceName',{'uuid':devid,'name':bom[ref]['厂家型号'],'source':''}),('Devices',[]),('SymbolName',{'uuid':symid,'name':ref+'_'+bom[ref]['厂家型号'],'source':''}),('Symbols',[]),('FootprintName',{'uuid':'','name':'','source':''}),('Footprints',[])]:payload['attrs'][key]=dumps(vals)
 pageDoc.emit('COMPONENT',payload,comp)
 for key,val in [('Symbol',symid),('Device',devid),('Footprint',''),('Unique ID',uid('unique/'+ref)),('Add into BOM','yes'),('Convert to PCB','yes'),('Supplier Part',bom[ref]['立创料号']),('Manufacturer Part',bom[ref]['厂家型号']),('Recommended footprint',bom[ref]['封装']),('SMT library status',bom[ref]['SMT库别'])]:pageDoc.attr(comp,key,val)
 for c in children:
  if c.startswith(('T~P~','T~N~')):
   ss=c.split('~');pageDoc.attr(comp,'Designator' if c.startswith('T~P~') else 'Value',ss[12],float(ss[2]),-float(ss[3]),float(ss[7].replace('pt','')),True)
 for num,net in expected[ref].items():
  if net=='NC':pageDoc.attr(comp+'-'+pins[num],'NO_CONNECT','yes',*mapped[ref,num])
# Recover named nets from the independently validated Std geometry, not expected pin names alone.
wire_records=[]
for shape in std:
 a=shape.split('~')
 if a[0]=='W':
  vals=list(map(float,a[1].split()));pts=list(zip(vals[::2],vals[1::2]));netset=ctx['names'][ctx['find'](pts[0])];assert len(netset)==1,netset;net=next(iter(netset));wid=pageDoc.emit('WIRE',pageDoc.base())
  for A,B in zip(pts,pts[1:]):pageDoc.emit('LINE',{'lineGroup':wid,'startX':A[0],'startY':-A[1],'endX':B[0],'endY':-B[1],'strokeColor':'#14803c','strokeStyle':'SOLID','strokeWidth':1,'fillColor':'','fillStyle':'NONE','yAxisDirection':'up'})
  wire_records.append({'id':wid,'net':net,'pts':pts,'label':None})
# Position real NET attributes on their wires; overflow labels become additional descriptive text.
def onseg(P,A,B):return (A[0]==B[0]==P[0] and min(A[1],B[1])<=P[1]<=max(A[1],B[1])) or (A[1]==B[1]==P[1] and min(A[0],B[0])<=P[0]<=max(A[0],B[0]))
for shape in std:
 a=shape.split('~')
 if a[0]=='N':
  pos=(float(a[1]),float(a[2]));name_=a[5];choices=[w for w in wire_records if w['net']==name_ and w['label'] is None and any(onseg(pos,A,B) for A,B in zip(w['pts'],w['pts'][1:]))]
  if choices:choices[0]['label']=(pos,a[7])
  else:pageDoc.text(name_,pos[0],-pos[1]+5,10,'RIGHT_BOTTOM' if a[7]=='end' else 'LEFT_BOTTOM')
 elif a[0] in ['T','R','PL']:shape_geometry(pageDoc,shape)
 # Junction dots are visual aids. Connectivity is the actual WIRE/LINE geometry.
 elif a[0]=='J':
  x,y=float(a[1]),float(a[2]);rad=1.6;pageDoc.poly([(x+rad*math.cos(i*math.pi/8),-y+rad*math.sin(i*math.pi/8)) for i in range(17)],'#14803c',2)
for w in wire_records:
 pos,align=(w['label'] if w['label'] else (w['pts'][0],'start'));pageDoc.attr(w['id'],'NET',w['net'],pos[0],-pos[1]+5,10,w['label'] is not None,'RIGHT_BOTTOM' if align=='end' else 'LEFT_BOTTOM')
blob=Doc('BLOB','BLOB')
folder=DEST/'sch/Control';folder.mkdir(parents=True,exist_ok=True)
(folder/(title+'.esch2')).write_text(''.join(''.join(d.lines) for d in [*symbols,*devices,blob,pageDoc]),encoding='utf-8',newline='\n')
schDoc=Doc('SCH',sch);schDoc.emit('META',{'title':'Control','board':board,'source':'','zIndex':1},'META');(folder/'Control.ecfg').write_text(''.join(schDoc.lines),encoding='utf-8',newline='\n')
index={'name':name,'owner_uuid':'','creator_uuid':'','modifier_uuid':'','created_at':'2026-11-08 12:00:00','updated_at':'2026-11-08 12:00:00','content':'R7 removable controller carrier; footprints TBD','archive':False,'cbb_project':0,'thumb':'','ticket':1,'g_ticket':1,'boards':[],'block_symbol_attrs_groups':{},'default_sheet':page,'branch_uuid':'','pcb_count':0,'format':'folder','profile':{'boards':{board:{'uuid':board,'title':'Control_R7','zIndex':1}},'schematics':{sch:{'uuid':sch,'name':'Control','board':board,'source':'','version':str(now),'updateTime':now}},'sheets':{page:{'uuid':page,'title':title,'schematic_uuid':sch,'zIndex':1,'source':'','version':str(now),'updateTime':now}},'pcbs':{},'panels':{},'blockSymbols':{},'owner':{'uuid':''},'simSchematics':{},'simulations':{}},'config':{'defaultSheet':page,'settings':{}}}
(DEST/(name+'.eprj3')).write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
(ROOT/'results/data/pro_conversion_map.json').write_text(json.dumps({'source':'R7 carrier geometry based on R5, user product pinout and confirmed first contact','components':len(expected),'pins':sum(map(len,expected.values())),'symbols':len(symbols),'devices':len(devices),'wires':len(wire_records),'embedded_symbol_pin_ids':symbol_pin_ids,'project_uuid':{'board':board,'schematic':sch,'sheet':page}},ensure_ascii=False,indent=2))
print('Native Pro folder project generated:',DEST)
