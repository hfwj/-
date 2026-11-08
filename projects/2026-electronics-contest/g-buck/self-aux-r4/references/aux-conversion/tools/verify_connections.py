"""Parse actual EasyEDA Std document and check geometry-derived connectivity."""
from pathlib import Path
from collections import defaultdict
import json,sys
root=Path(sys.argv[1]).resolve();d=json.loads((root/'schematic/native/Mainboard_Functional_Blocks.json').read_text())['schematics'][0]['dataStr']
expected=json.loads((root/'results/data/expected_mainboard_pins.json').read_text())
pins={};labels=[];wires=[];nc=set();components={}
for shape in d['shape']:
 a=shape.split('~')
 if a[0]=='LIB':
  items=shape.split('#@$');ref=next(q.split('~')[12] for q in items[1:] if q.startswith('T~P~'))
  assert ref not in components;components[ref]=shape
  for q in items[1:]:
   if q.startswith('P~'):
    s=q.split('^^');config=s[0].split('~');num=config[3];dot=tuple(map(float,s[1].split('~')))
    assert (ref,num) not in pins;pins[ref,num]=dot
 elif a[0]=='N':labels.append(((float(a[1]),float(a[2])),a[5]))
 elif a[0]=='W':
  z=list(map(float,a[1].split()));p=list(zip(z[::2],z[1::2]));wires.extend(zip(p,p[1:]))
 elif a[0]=='O':nc.add((float(a[1]),float(a[2])))
points=set(pins.values())|{p for p,n in labels}|{p for a,b in wires for p in (a,b)}
# Treat every wire crossing as connected; conservative detection of unintended intersections.
for a,b in wires:
 for c,e in wires:
  if a[0]==b[0] and c[1]==e[1] and min(a[1],b[1])<=c[1]<=max(a[1],b[1]) and min(c[0],e[0])<=a[0]<=max(c[0],e[0]):points.add((a[0],c[1]))
parent={p:p for p in points}
def find(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
def union(a,b):parent[find(a)]=find(b)
for a,b in wires:
 assert a[0]==b[0] or a[1]==b[1],('non-orthogonal',a,b)
 for p in points:
  if a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) or a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0]):union(a,p)
local_roots={p:find(p) for p in points}
byname={}
for p,n in labels:
 if n in byname:union(p,byname[n])
 else:byname[n]=p
names=defaultdict(set)
for p,n in labels:names[find(p)].add(n)
errors=[]
for ref,ps in expected.items():
 for n,net in ps.items():
  p=pins[ref,n];got=names.get(find(p),set())
  if net=='NC':
   if p not in nc or got:errors.append([ref,n,net,sorted(got)])
  elif got!={net}:errors.append([ref,n,net,sorted(got)])
# Require all non-NC pins to physically meet a wire, rather than relying on hidden expectations.
for ref,ps in expected.items():
 for n,net in ps.items():
  if net=='NC':continue
  p=pins[ref,n]
  touched=any((a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0])) for a,b in wires)
  if not touched:errors.append([ref,n,'NO_PHYSICAL_WIRE'])
# For each expected net, all pins must collapse to exactly one actual connected component.
for net in {n for p in expected.values() for n in p.values() if n!='NC'}:
 roots={find(pins[r,n]) for r,ps in expected.items() for n,v in ps.items() if v==net}
 if len(roots)!=1:errors.append(['OPEN_NET',net,len(roots)])
result={'status':'FAIL' if errors else 'PASS','components':len(components),'pins':len(pins),'no_connect_pins':len(nc),'orthogonal_wire_segments':len(wires),'errors':errors,'native_editor_erc':'NOT RUN','PCB':'NOT CREATED','footprints':'NOT ASSIGNED','hardware_validation':'NOT RUN'}
(root/'results/data/connectivity_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2));assert not errors
