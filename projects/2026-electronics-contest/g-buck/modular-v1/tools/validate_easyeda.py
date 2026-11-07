import json,re
from pathlib import Path
from collections import defaultdict
import sys
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()/'generated_easyeda'
expected=json.loads((root/'expected_pins.json').read_text())
reports={}
for fn in sorted((root/'standard_json').glob('*.json')):
 p=json.loads(fn.read_text());assert p['docType']=='5' and len(p['schematics'])==1
 d=p['schematics'][0]['dataStr'];assert d['head']['docType']=='1'
 pins={};labels=[];wires=[];nc=set();ids=[];components={}
 def point(a,b):return (float(a),float(b))
 for s in d['shape']:
  seg=s.split('~');kind=seg[0]
  if kind=='LIB':
   header,*internal=s.split('#@$');ref=None
   for part in internal:
    t=part.split('~')
    if t[0]=='T' and t[1]=='P':ref=t[12]
   assert ref and ref not in components;components[ref]=header
   for part in internal:
    if part.startswith('P~'):
     q=part.split('^^');assert len(q)==7
     a=q[0].split('~');b=q[1].split('~');num=a[3]
     assert (ref,num) not in pins
     assert point(a[4],a[5])==point(*b)
     pins[(ref,num)]=point(*b)
  elif kind=='W':
   q=list(map(float,seg[1].split()));assert len(q)%2==0
   ps=list(zip(q[::2],q[1::2]))
   for a,b in zip(ps,ps[1:]):
    assert a[0]==b[0] or a[1]==b[1],('nonorthogonal',s)
    wires.append((a,b))
  elif kind=='N':labels.append((point(seg[1],seg[2]),seg[5]))
  elif kind=='O':nc.add(point(seg[1],seg[2]))
 # Build electrical connectivity from parsed document, including intersections.
 pts=set(pins.values())|set(x for x,n in labels)|{x for a,b in wires for x in (a,b)}
 for a,b in wires:
  for c,e in wires:
   if a[0]==b[0] and c[1]==e[1]:
    x,y=a[0],c[1]
    if min(a[1],b[1])<=y<=max(a[1],b[1]) and min(c[0],e[0])<=x<=max(c[0],e[0]):pts.add((x,y))
 parent={x:x for x in pts}
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):parent[find(a)]=find(b)
 for a,b in wires:
  inside=[q for q in pts if (a[0]==b[0]==q[0] and min(a[1],b[1])<=q[1]<=max(a[1],b[1])) or (a[1]==b[1]==q[1] and min(a[0],b[0])<=q[0]<=max(a[0],b[0]))]
  for q in inside:union(a,q)
 byname={}
 for pt,net in labels:
  if net in byname:union(pt,byname[net])
  else:byname[net]=pt
 names=defaultdict(set)
 for pt,net in labels:names[find(pt)].add(net)
 for r,ns in expected[fn.stem].items():
  for n,net in ns.items():
   assert (r,n) in pins,('missing pin',fn,r,n)
   pt=pins[r,n];got=names.get(find(pt),set())
   if net=='NC':assert pt in nc and not got,('NC connected',fn,r,n,got)
   else:assert got=={net},('wrong net / short',fn,r,n,net,got)
 assert len(pins)==sum(len(x) for x in expected[fn.stem].values())
 reports[fn.stem]={'json_parse':'PASS','project_shape':'PASS','all_component_pin_numbers':'PASS','pin_net_equality':'PASS','unintended_net_shorts':'NONE','components':len(components),'pins':len(pins),'no_connect_pins':len(nc),'bound_footprints':False,'native_editor_import_test':'NOT RUN','hardware_validation':'NOT RUN'}
(root/'checks'/'connectivity_report.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
