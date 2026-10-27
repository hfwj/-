"""Read delivered native records, recover source connectivity, inspect geometry.

This deliberately reports unfinished copper connectivity. Static checks are
separate from desktop import, native ERC/DRC and manufacturing acceptance.
"""
import csv,itertools,json,sqlite3
from pcb_common import *

def main():
    manifest=json.loads((ROOT/'data/build_manifest.json').read_text())
    source=next((REV/'schematic/native').glob('*.eprj2'))
    sm,sd,_=read_project(source);meta,docs,ticket=read_project(PATH)
    ss,sp,sparts,spins=inventory(sm,sd,'G题同步Buck Rev C.2 原理图')
    scheme,pages,parts,pins=inventory(meta,docs,'G题同步Buck Rev C.2 原理图')
    errors=[]
    def require(v,msg):
        if not v:errors.append(msg)
    expected={(p['ref'],p['pin']):p['net'] for p in spins}
    recovered={(p['ref'],p['pin']):p['net'] for p in pins}
    require(recovered==expected,'Schematic connectivity differs from Rev C.2')
    pp,pads,bodies,tracks=copper_geometry(meta,docs,manifest['pcb'])
    vias=copper_vias(docs,manifest['pcb'])
    actual={}
    for p in pads:
        key=(p['ref'],p['pin'])
        require(key not in actual or actual[key]==p['net'],'Conflicting duplicate physical pad '+str(key))
        actual[key]=p['net']
    require(actual==expected,'PCB pad-to-net graph differs from Rev C.2')
    require(set(pp)==set(sparts),'PCB reference inventory differs')
    for ref,(cid,c,a) in pp.items():
        require(c['attrs']['Unique ID']==parts[ref]['id'],'Broken schematic association '+ref)
        dev=docs[a['Device']]['META','META']['attributes']
        require(dev['Footprint']==a['Footprint']==parts[ref]['attrs']['Footprint'],'Footprint association mismatch '+ref)
        require(dev['Symbol']==parts[ref]['attrs']['Symbol'],'Symbol association mismatch '+ref)
    source_hash=sha(source)
    require(source_hash==manifest['source_sha256'],'Source file has changed')
    reference_unchanged=[]
    for u in sd:
        if sm[u]['docType'] in ['PCB','SYMBOL','FOOTPRINT','DEVICE']:
            require(docs[u]==sd[u],'Source/reference library or PCB altered '+u)
            reference_unchanged.append(u)
    # Ensure unexpected value changes cannot hide behind the unchanged pin graph.
    value_changes={}
    for ref,p in parts.items():
        before=sparts[ref]['attrs']['Value'];after=p['attrs']['Value']
        if before!=after:value_changes[ref]={'before':before,'after':after}
    require(value_changes=={'F1':{'before':'2A / 5x20','after':'2A / 5x20 FAST'},
                            'C4':{'before':'10uF / 35V','after':'10uF / 50V X7R'},
                            'D1':{'before':'SS56','after':'SR560 / 60V / 5A'},
                            'D_FREE':{'before':'SS56 / 60V / 5A','after':'SR560 / 60V / 5A'}},'Unexpected component value changes')
    require(parts['U1']['attrs']['Value']=='IR2184PbF','Wrong driver version')
    require(parts['J_MON']['attrs']['Value']=='2P VIN_POST ADC / PA6','VIN monitor not assigned to PA6')
    geometry_errors=[];clearance_errors=[];board=box(0,0,120,90)
    for p in pads:
        if not board.covers(p['geometry']):geometry_errors.append('pad beyond board '+p['ref']+'.'+p['pin'])
    for b in bodies:
        if not board.covers(b['geometry']):geometry_errors.append('body beyond board '+b['ref'])
    for a,b in itertools.combinations(bodies,2):
        if a['geometry'].intersection(b['geometry']).area>1e-7:geometry_errors.append('body overlap '+a['ref']+'/'+b['ref'])
    for p in pads:
        for b in bodies:
            if p['ref']!=b['ref'] and p['geometry'].intersection(b['geometry']).area>1e-7:
                geometry_errors.append('pad/body overlap '+p['ref']+'.'+p['pin']+'/'+b['ref'])
    for a,b in itertools.combinations(pads,2):
        if not set(a['layers'])&set(b['layers']):continue
        d=a['geometry'].distance(b['geometry'])
        if a['net']!=b['net'] and d<.2-1e-5:clearance_errors.append('pad/pad <0.20mm '+a['ref']+'.'+a['pin']+'/'+b['ref']+'.'+b['pin'])
    for t in tracks:
        if not box(.5,.5,119.5,89.5).covers(t['geometry']):geometry_errors.append('track beyond copper margin '+t['id'])
        for p in pads:
            if t['layer'] in p['layers'] and p['net']!=t['net'] and t['geometry'].distance(p['geometry'])<.2-1e-5:
                clearance_errors.append('track/pad <0.20mm '+t['id']+'/'+p['ref']+'.'+p['pin'])
    for a,b in itertools.combinations(tracks,2):
        if a['layer']==b['layer'] and a['net']!=b['net'] and a['geometry'].distance(b['geometry'])<.2-1e-5:
            clearance_errors.append('track/track <0.20mm '+a['id']+'/'+b['id'])
    holes=[Point(x,y).buffer(1.6) for x,y in manifest['mounting_holes_mm']]
    for n,h in enumerate(holes):
        for p in pads:
            if h.distance(p['geometry'])<.2-1e-5:clearance_errors.append('mount hole/copper '+str(n)+'/'+p['ref'])
        for t in tracks:
            if h.distance(t['geometry'])<.2-1e-5:clearance_errors.append('mount hole/track '+str(n)+'/'+t['id'])
        for v in vias:
            if h.distance(v['geometry'])<.2-1e-5:clearance_errors.append('mount hole/via '+str(n)+'/'+v['id'])
    for v in vias:
        if not box(.5,.5,119.5,89.5).covers(v['geometry']):geometry_errors.append('via beyond copper margin '+v['id'])
        if v['body']['viaType']!='NORMAL':geometry_errors.append('unsupported via type '+v['id'])
        if v['hole_diameter']<=0 or (v['diameter']-v['hole_diameter'])/2<.15-1e-7:
            geometry_errors.append('via drill/annular ring '+v['id'])
        for p in pads:
            if p['net']!=v['net'] and v['geometry'].distance(p['geometry'])<.2-1e-5:
                clearance_errors.append('via/pad <0.20mm '+v['id']+'/'+p['ref']+'.'+p['pin'])
        for t in tracks:
            if t['net']!=v['net'] and v['geometry'].distance(t['geometry'])<.2-1e-5:
                clearance_errors.append('via/track <0.20mm '+v['id']+'/'+t['id'])
    for a,b in itertools.combinations(vias,2):
        drill_gap=math.hypot(a['x']-b['x'],a['y']-b['y'])-(a['hole_diameter']+b['hole_diameter'])/2
        if drill_gap<.2-1e-5:geometry_errors.append('via drill web <0.20mm '+a['id']+'/'+b['id'])
        if a['net']!=b['net'] and a['geometry'].distance(b['geometry'])<.2-1e-5:
            clearance_errors.append('via/via <0.20mm '+a['id']+'/'+b['id'])
    require(not geometry_errors,'Physical geometry violations')
    require(not clearance_errors,'Conservative copper clearance violations')
    # Physical same-layer copper connected components. A net assignment alone is
    # never treated as an electrically routed connection.
    pernet=collections.defaultdict(list)
    for p in pads:
        if p['net']:pernet[p['net']].append((p['geometry'],set(p['layers']),p['ref']+'.'+p['pin']))
    for t in tracks:pernet[t['net']].append((t['geometry'],{t['layer']},'trace:'+t['id']))
    for v in vias:pernet[v['net']].append((v['geometry'],{1,2},'via:'+v['id']))
    unresolved=[]
    for net,nodes in sorted(pernet.items()):
        parent=list(range(len(nodes)))
        def find(i):
            while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for i,j in itertools.combinations(range(len(nodes)),2):
            if nodes[i][1]&nodes[j][1] and nodes[i][0].distance(nodes[j][0])<1e-5:
                parent[find(j)]=find(i)
        groups=collections.defaultdict(list)
        for i,(_,_,name) in enumerate(nodes):
            if not name.startswith(('trace:','via:')):groups[find(i)].append(name)
        if len(groups)>1:unresolved.append({'net':net,'copper_islands':len(groups),'minimum_links_remaining':len(groups)-1,'endpoints':list(groups.values())})
    status='PASS_STATIC_REVIEW_ONLY' if not errors else 'FAIL'
    report={'status':status,'errors':errors,'checks':{
        'source_sha256':source_hash,'delivered_sha256':sha(PATH),
        'source_schematic_components':len(sparts),'delivered_schematic_components':len(parts),'pcb_components':len(pp),
        'source_networks':len(set(expected.values())-{''}),
        'source_connected_logical_pins':sum(bool(v) for v in expected.values()),
        'explicit_NC_logical_pins':sum(not v for v in expected.values()),
        'physical_component_pads':len(pads),'duplicate_fuse_terminal_pads':len(pads)-len(expected),
        'source_schematic_pin_graph_preserved':recovered==expected,'pcb_pad_graph_matches_source':actual==expected,
        'value_changes':value_changes,'preserved_source_PCB_library_documents':len(reference_unchanged),
        'geometric_errors':geometry_errors,'clearance_errors':clearance_errors,
        'mounting_holes':len(holes),'copper_track_segments':len(tracks),'vias':len(vias),
        'unfinished_networks':len(unresolved),'minimum_copper_links_remaining':sum(x['minimum_links_remaining'] for x in unresolved),
        'routing_complete':not unresolved,'native_desktop_open':'not_run','native_ERC':'not_run','native_DRC':'not_run',
        'manufacturing_release':False,'sqlite_integrity':sqlite3.connect('file:'+str(PATH)+'?mode=ro',uri=True).execute('pragma integrity_check').fetchone()[0]},
        'limitations':['Rectangular pad copper conservatively encloses round/oval pads; checks are not native ERC/DRC.',
        'Seller drawings support RS_IN/OUT P10 D0.8 and RS_L P5 D0.7. User confirms single 5x20 fuse-clip pitch 5.66; assembly spacing 15 is trial-fit only. Shunt ratings and fuse fit/DC breaking capacity/thermal design remain unconfirmed.',
        'No complete power routing, Kelvin routing or ground plane. No Gerber manufacturing output.',
        'Mounting pattern is proposed, not confirmed to an enclosure. Silk/courtyard/mask/paste/3D checks remain open.']}
    (ROOT/'data/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (ROOT/'data/unrouted_networks.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2))
    with (ROOT/'data/PCB_pin_readback.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['ref','pin','net','x_mm','y_mm','pad_id'])
        for p in pads:w.writerow([p['ref'],p['pin'],p['net'],round(p['x'],5),round(p['y'],5),p['pid']])
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
