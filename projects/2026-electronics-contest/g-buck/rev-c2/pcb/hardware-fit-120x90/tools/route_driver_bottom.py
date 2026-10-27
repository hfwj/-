"""Finish the four blocked driver-local pairs with explicit 0.6/0.3mm vias.

Uses the through-hole U1 pins to enter bottom copper, then one off-pad via
near each SMD destination. No via-in-pad, no inferred layer transitions.
"""
from route_pending import connected, find_path, CLEARANCE
from pcb_common import *


def add_line(o, key, net, layer, s, t, width):
    for (kind,_),line in o.items():
        if kind!='LINE' or line['netName']!=net or line['layerId']!=layer:continue
        a=(line['startX']*.0254,line['startY']*.0254)
        b=(line['endX']*.0254,line['endY']*.0254)
        if abs(line['width']*.0254-width)<1e-7 and (
            (math.dist(a,s)<1e-7 and math.dist(b,t)<1e-7) or
            (math.dist(a,t)<1e-7 and math.dist(b,s)<1e-7)):
            return
    lid = uuid.uuid5(uuid.NAMESPACE_URL, key).hex[:16]
    assert ('LINE', lid) not in o
    o['LINE',lid] = {'partitionId':'','groupId':0,'netName':net,'layerId':layer,
                    'startX':s[0]/.0254,'startY':s[1]/.0254,
                    'endX':t[0]/.0254,'endY':t[1]/.0254,
                    'width':width/.0254,'locked':False,'zIndex':-1}


def main():
    manifest = json.loads((ROOT/'data/build_manifest.json').read_text())
    previous = json.loads((ROOT/'data/routing_continuation.json').read_text())
    meta, docs, _ = read_project(PATH)
    pcb = manifest['pcb']
    _, pads, bodies, tracks = copper_geometry(meta, docs, pcb)
    vias = copper_vias(docs, pcb)
    ep = {p['ref']+'.'+p['pin']:p for p in pads}
    holes = [Point(x,y).buffer(1.6) for x,y in manifest['mounting_holes_mm']]
    before = sha(PATH)
    routed, pending = [], []
    for pair in previous['pending_local_pairs']:
        a,b = ep[pair['from']], ep[pair['to']]
        assert 2 in a['layers'] and a['net'] == b['net'] == pair['net']
        if connected(a,b,pads,tracks,vias):
            continue
        net = a['net']
        width = .4 if net == 'GND' else .25
        obstacles = {layer:[p['geometry'] for p in pads if p['net']!=net and layer in p['layers']]
                     + [t['geometry'] for t in tracks if t['net']!=net and t['layer']==layer]
                     + [v['geometry'] for v in vias if v['net']!=net] + holes for layer in (1,2)}
        # Candidate vias remain outside every component body and off all pads;
        # their short top stubs can enter the intended pad without other copper.
        candidates = []
        for radius in (1.25,1.5,1.75,2.):
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                x,y = b['x']+radius*dx, b['y']+radius*dy
                via = Point(x,y).buffer(.3)
                if not box(.5,.5,119.5,89.5).covers(via):continue
                if any(via.distance(g)<CLEARANCE for g in obstacles[1]+obstacles[2]):continue
                if any(via.distance(v['geometry'])<CLEARANCE for v in vias):continue
                if any(via.distance(p['geometry'])<.20 for p in pads):continue
                if any(via.intersects(body['geometry']) for body in bodies):continue
                stub = LineString([(x,y),(b['x'],b['y'])]).buffer(width/2)
                if any(stub.distance(g)<CLEARANCE for g in obstacles[1]):continue
                candidates.append((math.dist((a['x'],a['y']),(x,y)),x,y))
        found = None
        for _,x,y in sorted(candidates):
            points = find_path(a, {'x':x,'y':y}, obstacles[2], width=width)
            if points:
                found = x,y,points
                break
        if found is None:
            pending.append(pair)
            continue
        x,y,points = found
        prefix = 'gbuck-driver-bottom:'+pair['from']+':'+pair['to']
        for n,(s,t) in enumerate(zip(points,points[1:])):
            add_line(docs[pcb],prefix+':bottom:'+str(n),net,2,s,t,width)
        stub_points = [(x,y),(b['x'],b['y'])]
        add_line(docs[pcb],prefix+':top',net,1,*stub_points,width)
        vid = uuid.uuid5(uuid.NAMESPACE_URL,prefix+':via').hex[:16]
        assert ('VIA',vid) not in docs[pcb]
        docs[pcb]['VIA',vid] = {'partitionId':'','groupId':0,'netName':net,'ruleName':'',
            'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.3/.0254,'viaDiameter':.6/.0254,
            'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
            'locked':False,'unusedInnerLayers':[]}
        _,pads,_,tracks = copper_geometry(meta,docs,pcb)
        vias = copper_vias(docs,pcb)
        assert connected(a,b,pads,tracks,vias)
        routed.append({k:pair[k] for k in ('from','to','net')} | {'bottom_points_mm':points,
            'top_stub_mm':stub_points,'via_center_mm':[x,y],'via_diameter_mm':.6,
            'drill_mm':.3,'trace_width_mm':width})
    if not routed:
        print(json.dumps({'added_pairs':0,'pending_pairs':len(pending)}))
        return
    label = 'driver-bottom-' + hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
    append_history(PATH,meta,docs,{pcb},label)
    rm,rd,_ = read_project(PATH)
    _,rp,_,rt = copper_geometry(rm,rd,pcb)
    rv = copper_vias(rd,pcb)
    re = {p['ref']+'.'+p['pin']:p for p in rp}
    for pair in routed:
        assert connected(re[pair['from']],re[pair['to']],rp,rt,rv)
    result = {'baseline_sha256':before,'delivered_sha256':sha(PATH),'routed_pairs':routed,
        'pending_local_pairs':pending,'clearance_mm':CLEARANCE,'routing_complete':False,
        'native_DRC':'not_run','manufacturing_release':False}
    (ROOT/'data/driver_bottom_routing.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    manifest['remaining_pending_local_pairs'] = len(pending)
    manifest['driver_bottom_pairs'] = len(routed)
    (ROOT/'data/build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({'added_pairs':len(routed),'pending_pairs':len(pending),'readback_continuity':'PASS'}))


if __name__=='__main__':
    main()
