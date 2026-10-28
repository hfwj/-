from pathlib import Path
import sys,json,itertools,math,collections
ART=Path(__file__).resolve().parents[1]
LIB=ART.parent/'hardware-fit-120x90/tools'
sys.path.insert(0,str(LIB))
from pcb_common import *
from routing_engine import Router
from shapely import STRtree,union_all
from export_isolated_review import contact_groups,remap
MF=json.loads((ART/'data/build_manifest.json').read_text())
BASE=ART.parent/'hardware-fit-120x90/native/GBUCK_RevC2_F1_slotfix_v3_20261028.eprj2'
PATH_V4=ART/'native/GBUCK_RevC2_PowerLayout_v4_20261028.eprj2'
HOLES=MF['mounting_holes_mm']
m,d,_=read_project(PATH_V4);pcb=MF['pcb'];r=Router(m,d,pcb,HOLES);errors=[]

nodes=[]
for p in r.pads:nodes.append((p['net'] or 'NC:'+p['ref']+'.'+p['pin'],p['geometry'],set(p['layers']),'pad:'+p['ref']+'.'+p['pin']))
for t in r.tracks:nodes.append((t['net'],t['geometry'],{t['layer']},'trace:'+t['id']))
for v in r.vias:nodes.append((v['net'],v['geometry'],{1,2},'via:'+v['id']))
for f in r.fills:nodes.append((f['net'],f['geometry'],{f['layer']},'fill:'+f['id']))
tree=STRtree([n[1] for n in nodes]);minimum=100
for i,(net,g,ls,name) in enumerate(nodes):
 if not box(.5,.5,119.5,89.5).covers(g):errors.append(('copper margin',name))
 for j in tree.query(g.buffer(.20001)):
  j=int(j)
  if j<=i or not ls&nodes[j][2] or net==nodes[j][0]:continue
  dist=g.distance(nodes[j][1]);minimum=min(minimum,dist)
  if dist<.2-1e-5:errors.append(('foreign clearance',name,nodes[j][3],dist))
for a,b in itertools.combinations(r.bodies,2):
 if a['geometry'].intersection(b['geometry']).area>1e-7:errors.append(('body overlap',a['ref'],b['ref']))
for p in r.pads:
 for b in r.bodies:
  if p['ref']!=b['ref'] and p['geometry'].intersection(b['geometry']).area>1e-7:errors.append(('pad/body',p['ref']+'.'+p['pin'],b['ref']))
 # Native ELLIPSE (round) pads in the delivered Gerber use their width as diameter.
 if p['body']['defaultPad']['padType']=='ELLIPSE':p['geometry']=Point(p['x'],p['y']).buffer(p['w']/2,quad_segs=64)
contacts=contact_groups(r.pads,r.tracks,r.vias,r.fills)
if contacts['unfinished_networks']:errors.append(('unfinished',list(contacts['unfinished_networks'])))
if contacts['orphan_copper_groups']:errors.append(('orphans',len(contacts['orphan_copper_groups'])))
for a,b in itertools.combinations(r.vias,2):
 gap=math.dist((a['x'],a['y']),(b['x'],b['y']))-(a['hole_diameter']+b['hole_diameter'])/2
 if gap<.2-1e-5:errors.append(('via drill web',a['id'],b['id'],gap))
for v in r.vias:
 for p in r.pads:
  if not p['hole']:continue
  # Circumscribed drill envelope, conservative for the four F1 slots.
  radius=max(p['hole']['width'],p['hole']['height'])*.0254/2
  gap=math.dist((v['x'],v['y']),(p['x'],p['y']))-v['hole_diameter']/2-radius
  if gap<.2-1e-5:errors.append(('via/PTH drill web',v['id'],p['ref'],gap))
 if (v['diameter']-v['hole_diameter'])/2<.15-1e-7:errors.append(('via annulus',v['id']))
for x,y in HOLES:
 hole=Point(x,y).buffer(1.6)
 for net,g,ls,name in nodes:
  if g.distance(hole)<.2-1e-5:errors.append(('mount hole copper',name))
bm,bd,_=read_project(BASE);bs,bpages,bparts,bpins=inventory(bm,bd,'G题同步Buck Rev C.2 原理图');ns,npages,nparts,npins=inventory(m,d,'G题同步Buck Rev C.2 原理图')
assert {(p['ref'],p['pin']):p['net'] for p in bpins}=={(p['ref'],p['pin']):p['net'] for p in npins}
assert {k:v['attrs']['Value'] for k,v in bparts.items()}=={k:v['attrs']['Value'] for k,v in nparts.items()}
audit=json.loads((ART/'data/isolated_import_audit.json').read_text())
inverse={v:k for k,v in audit['document_uuid_map'].items()}
for u in d:
 if u!=pcb:
  original=inverse.get(u,u)
  normal={key:remap(value,inverse) for key,value in d[u].items()}
  assert normal==bd[original],original
report={'errors':errors,'components':len(r.parts),'pads':len(r.pads),'tracks':len(r.tracks),'vias':len(r.vias),'fills':len(r.fills),'minimum_foreign_copper_clearance_mm':minimum,'actual_round_pad_contact_audit':contacts,'schematic_all_documents_unchanged':True,'BOM_values_and_libraries_unchanged':True,'manufacturing_release':False,'native_DRC':'not_run','saved_native_sha256':sha(PATH_V4)}
plane=union_all([f['geometry'] for f in r.fills if f['layer']==2])
report['Kelvin_trunk_bottom_GND_reference_continuous']=plane.covers(box(110,76.55,112,77.45))
if not report['Kelvin_trunk_bottom_GND_reference_continuous']:errors.append(('Kelvin reference plane interrupted',))
(ART/'data/saved_native_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='actual_round_pad_contact_audit'},indent=2));print('CONTACTS',contacts['networks'],len(contacts['unfinished_networks']),len(contacts['orphan_copper_groups']))
