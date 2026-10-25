"""Read back the actual native history, recover connectivity geometrically, compare to PDF appendix."""
import json,math,collections,itertools,sqlite3
from pathlib import Path
from read_native import read_project
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--original', type=Path, help='Optional untouched upstream .eprj2')
parser.add_argument('--report', type=Path, help='Write report to this file')
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'native'
built=json.loads((ROOT/'data/revb_design_inventory.json').read_text());source=json.loads((ROOT/'data/RevB_PDF基准网络表.json').read_text());path=next(OUT.glob('*.eprj2'))
meta,docs,ticket=read_project(path)
oldmeta,old,_=read_project(args.original) if args.original else ({},{},0)
errors=[];checks={};warnings=[]
def require(ok,msg):
 if not ok:errors.append(msg)
def attrs(objs):
 a=collections.defaultdict(dict)
 for (typ,id),b in objs.items():
  if typ=='ATTR':a[b.get('parentId')][b['key']]=b.get('value')
 return a
schpins={};schrefs={}
for page in built['pages'].values():
 o=docs[page];a=attrs(o)
 lines=[b for (typ,id),b in o.items() if typ=='LINE']
 for (typ,id),b in o.items():
  if typ!='COMPONENT':continue
  ref=a[id]['Designator'];require(ref not in schrefs,'duplicate schematic ref '+ref);schrefs[ref]=id
  sy=docs[a[id]['Symbol']];sa=attrs(sy)
  for (pt,pid),pb in sy.items():
   if pt!='PIN' or pb.get('partId')!=b['partId']:continue
   number=sa[pid]['Pin Number'];x=b['x']+pb['x'];y=b['y']+pb['y']
   matching=[]
   for line in lines:
    x0,y0,x1,y1=line['startX'],line['startY'],line['endX'],line['endY'];dx=x1-x0;dy=y1-y0
    on=abs((x-x0)*dy-(y-y0)*dx)<1e-6 and min(x0,x1)-1e-6<=x<=max(x0,x1)+1e-6 and min(y0,y1)-1e-6<=y<=max(y0,y1)+1e-6
    if on:matching.append(a[line['lineGroup']].get('NET'))
   require(len(set(matching))<=1,'multiple nets at '+ref+'.'+number)
   if matching:schpins[ref+'.'+number]=matching[0]
expected={ep:net for net,eps in source['nets'].items() for ep in eps}
require(schpins==expected,'schematic wiring differs from PDF appendix: '+str(set(schpins.items())^set(expected.items())))
require(set(schrefs)==set(source['parts']),'schematic reference inventory differs')
o=docs[built['pcb']];a=attrs(o);pcbrefs={};physical=[];bodies=[];pcbpins={};unconnected=[]
for (typ,id),b in o.items():
 if typ!='COMPONENT':continue
 ref=a[id]['Designator'];require(ref not in pcbrefs,'duplicate PCB ref '+ref);pcbrefs[ref]=id
 fp=docs[a[id]['Footprint']];fp_pads={pb['num']:(pid,pb) for (pt,pid),pb in fp.items() if pt=='PAD'}
 device=docs[a[id]['Device']][('META','META')]['attributes']
 require(device['Footprint']==a[id]['Footprint'],'device/PCB footprint mismatch '+ref)
 require(device['Symbol']==attrs(docs[built['parts'][ref]['sch_page_uuid']])[schrefs[ref]]['Symbol'],'device/schematic symbol mismatch '+ref)
 require(b['attrs'].get('Unique ID')==schrefs[ref],'schematic/PCB association mismatch '+ref)
 for (pt,pid),pb in o.items():
  if pt!='PAD_NET':continue
  z=json.loads(pid)
  if z[1]!=id:continue
  num=z[2];require(num in fp_pads,'missing pad '+ref+'.'+num)
  if num not in fp_pads:continue
  padid,pad=fp_pads[num];require(z[3]==padid,'PAD_NET points to wrong pad '+ref+'.'+num)
  net=pb.get('padNet','');ep=ref+'.'+num
  if net:pcbpins[ep]=net
  else:unconnected.append(ep)
  ag=math.radians(b['angle']);cs=math.cos(ag);sn=math.sin(ag)
  px=(b['x']+pad['centerX']*cs-pad['centerY']*sn)*.0254;py=(b['y']+pad['centerX']*sn+pad['centerY']*cs)*.0254
  w=pad['defaultPad']['width']*.0254;h=pad['defaultPad']['height']*.0254
  verts=[(px+xx*cs-yy*sn,py+xx*sn+yy*cs) for xx,yy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
  physical.append({'ref':ref,'pin':num,'net':net,'x':px,'y':py,'polygon':verts,'w':w,'h':h,'hole':pad['hole'],'angle':b['angle']})
  require(all(-1e-4<=vx<=120.0001 and -1e-4<=vy<=90.0001 for vx,vy in verts),'pad outside board '+ep)
 sp=built['specs'][built['parts'][ref]['package']];w,h=sp['body_mm'];ag=math.radians(b['angle']);cs=math.cos(ag);sn=math.sin(ag);cx=b['x']*.0254;cy=b['y']*.0254
 poly=[(cx+xx*cs-yy*sn,cy+xx*sn+yy*cs) for xx,yy in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
 bodies.append((ref,poly));require(all(-.001<=x<=120.001 and -.001<=y<=90.001 for x,y in poly),'component body outside outline '+ref)
 require(len(fp_pads)==sum(1 for z in o if z[0]=='PAD_NET' and json.loads(z[1])[1]==id),'PAD_NET count mismatch '+ref)
require(pcbpins==expected,'PCB pad nets differ from PDF appendix: '+str(set(pcbpins.items())^set(expected.items())))
require(set(pcbrefs)==set(source['parts']),'PCB reference inventory differs')
# Convex polygon separating-axis overlap check of actual native copper-pad rectangles.
def overlap(pa,pb):
 for poly in [pa,pb]:
  for i in range(len(poly)):
   x,y=poly[i];xx,yy=poly[(i+1)%len(poly)];nx=-(yy-y);ny=xx-x
   aa=[u*nx+v*ny for u,v in pa];bb=[u*nx+v*ny for u,v in pb]
   if max(aa)<=min(bb)+1e-9 or max(bb)<=min(aa)+1e-9:return False
 return True
pad_overlaps=[];body_overlaps=[]
for pa,pb in itertools.combinations(physical,2):
 if overlap(pa['polygon'],pb['polygon']):pad_overlaps.append([pa['ref']+'.'+pa['pin'],pb['ref']+'.'+pb['pin']])
for (ra,pa),(rb,pb) in itertools.combinations(bodies,2):
 if overlap(pa,pb):body_overlaps.append([ra,rb])
require(not pad_overlaps,'copper pad overlaps '+str(pad_overlaps))
require(not body_overlaps,'component envelope overlaps '+str(body_overlaps))
require(all(docs[u]==old[u] for u in old if u!='CONFIG'),'reference documents changed')
require(docs['CONFIG'][('META','META')]['defaultSheet']==built['pages']['1'],'default page is not Rev B')
checks={'sqlite_integrity':sqlite3.connect(path).execute('pragma integrity_check').fetchone()[0], 'schematic_refs':len(schrefs),'pcb_refs':len(pcbrefs),'source_networks':len(source['nets']),'source_connected_pins':len(expected),'schematic_recovered_connected_pins':len(schpins),'pcb_recovered_connected_pins':len(pcbpins),'physical_pads':len(physical),'explicit_unconnected_pins':sorted(unconnected),'native_record_ticket':ticket,'reference_design_documents_unchanged':True if args.original else None,'copper_pad_overlap_pairs':pad_overlaps,'component_envelope_overlap_pairs':body_overlaps,'board_mm':[120,90],'copper_tracks':sum(1 for k in o if k[0]=='LINE'),'vias':sum(1 for k in o if k[0]=='VIA'),'native_application_open_test':'not_run','native_ERC':'not_run','native_DRC':'not_run','routing':'not_started','manufacturing_release':False}
report={'status':'PASS_STATIC_READBACK' if not errors else 'FAIL','checks':checks,'errors':errors,'limitations':['Static native-history and geometry checks are not EasyEDA ERC/DRC.','Native desktop open/import has not been tested.','Component envelopes and pad rectangles do not include heatsinks, connector mating/retention, tolerance stacks or courtyard clearance.','Mechanical packages marked TBD need actual part selection before routing.']}
if args.report:
 args.report.parent.mkdir(parents=True,exist_ok=True)
 args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
if errors:raise SystemExit(1)
