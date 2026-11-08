"""Read Pro records, resolve embedded symbols and derive connectivity independently."""
import json,sys,math,re
from pathlib import Path
from collections import defaultdict
root=Path(sys.argv[1]);folder=root/'schematic/pro/GBUCK_Aux_R3';expected=json.loads((root/'results/data/expected_mainboard_pins.json').read_text());index=json.loads(next(folder.glob('*.eprj3')).read_text());docs={}
for file in folder.rglob('*.esch2'):
 for line in file.read_text().splitlines():
  assert line.endswith('|')
  a,b=map(json.loads,line[:-1].split('||',1))
  if a['type']=='DOCHEAD':cur=b['uuid'];docs[cur]={'head':b,'rows':[]}
  else:docs[cur]['rows'].append((a['type'],a['id'],b))
pageid=next(iter(index['profile']['sheets']));sheet=docs[pageid];attrs=defaultdict(dict)
for typ,id,p in sheet['rows']:
 if typ=='ATTR':attrs[p['parentId']][p['key']]=p['value']
pins={};nc=set();wires=[];wire_names={};part_ids={};component_count=0
for typ,id,p in sheet['rows']:
 if typ=='COMPONENT':
  component_count+=1;ref=attrs[id]['Designator'];sym=docs[attrs[id]['Symbol']];sa=defaultdict(dict)
  for t,i,d in sym['rows']:
   if t=='ATTR':sa[d['parentId']][d['key']]=d['value']
  assert any(t=='PART' and i==p['partId'] for t,i,d in sym['rows'])
  assert p['rotation']==0 and not p['isMirror']
  for t,i,d in sym['rows']:
   if t=='PIN':
    key=(ref,sa[i]['Pin Number']);pins[key]=(p['x']+d['x'],p['y']+d['y'])
    if attrs[id+'-'+i].get('NO_CONNECT')=='yes':nc.add(key)
 elif typ=='WIRE':wire_names[id]=attrs[id]['NET']
 elif typ=='LINE':wires.append(((p['startX'],p['startY']),(p['endX'],p['endY']),p['lineGroup']))
points=set(pins.values())|{q for a,b,w in wires for q in [a,b]}
for a,b,w in wires:
 assert a[0]==b[0] or a[1]==b[1]
 for c,d,v in wires:
  if a[0]==b[0] and c[1]==d[1] and min(a[1],b[1])<=c[1]<=max(a[1],b[1]) and min(c[0],d[0])<=a[0]<=max(c[0],d[0]):points.add((a[0],c[1]))
parent={p:p for p in points}
def find(p):
 while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
 return p
def union(a,b):parent[find(a)]=find(b)
def on(p,a,b):return (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0]))
for a,b,w in wires:
 for p in points:
  if on(p,a,b):union(a,p)
namefirst={}
for a,b,w in wires:
 n=wire_names[w]
 if n in namefirst:union(a,namefirst[n])
 else:namefirst[n]=a
names=defaultdict(set)
for a,b,w in wires:names[find(a)].add(wire_names[w])
errors=[]
for key,pos in pins.items():
 ref,num=key;net=expected[ref][num];actual=names[find(pos)]
 if net=='NC':
  if key not in nc or actual:errors.append([ref,num,net,list(actual),'NC mismatch'])
 elif actual!={net} or key in nc:errors.append([ref,num,net,list(actual)])
assert set(pins)=={(r,n) for r,v in expected.items() for n in v}
assert component_count==len(expected) and len(pins)==sum(map(len,expected.values()))
for set_ in names.values():
 if len(set_)>1:errors.append(['SHORT',list(set_)])
report={'status':'PASS' if not errors else 'FAIL','components':component_count,'pins':len(pins),'no_connect_pins':len(nc),'wire_segments':len(wires),'embedded_symbols':sum(d['head']['docType']=='SYMBOL' for d in docs.values()),'index_sheet_resolved':pageid in docs,'comparison':'R3 expected pin map; retained non-interface pins audited against baseline','errors':errors,'native_editor_erc':'NOT RUN','footprints':'NOT ASSIGNED','hardware':'NOT TESTED'}
(root/'results/data/pro_connectivity_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
