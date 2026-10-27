"""Route an explicit power-path draft, keeping narrow signal routing separate.

2mm main trunks assume 35um external copper; they are not a thermal release.
No power-current path uses a single signal via. Existing records are retained.
"""
from route_driver_bottom import add_line
from route_pending import find_path, connected
from pcb_common import *

PLAN = [
    ('J1.1','F1.1',2.),('F1.1','F1.1#2',2.),('F1.2','F1.2#2',2.),
    ('F1.2#2','J_BYP.1',2.),('J_BYP.1','R_PRE.1',2.),
    ('J_BYP.2','D1.2',2.),('R_PRE.2','J_BYP.2',2.),
    ('D1.1','RS_IN.1',2.),('RS_IN.2','C1.1',2.),('C1.1','QH.2',2.),
    ('QH.3','QL.2',2.),('QH.3','L1.1',2.),('L1.2','RS_L.1',2.),
    ('RS_L.2','C3.1',2.),('C3.1','RS_OUT.1',2.),('RS_OUT.2','J2.1',2.),
    ('QL.3','C1.2',2.),('C3.2','QL.3',2.),('J2.2','C3.2',2.),('J1.2','C1.2',2.),
    ('C2.1','C1.1',1.),('C2.2','C1.2',1.),
    ('D_FREE.1','QH.3',2.),('D_FREE.2','QL.3',2.),
    ('C4.1','C3.1',1.),('C4.2','C3.2',1.)]


def main():
    manifest=json.loads((ROOT/'data/build_manifest.json').read_text())
    meta,docs,_=read_project(PATH);pcb=manifest['pcb']
    _,pads,_,tracks=copper_geometry(meta,docs,pcb);vias=copper_vias(docs,pcb)
    ep={};counts=collections.Counter()
    for p in pads:
        key=p['ref']+'.'+p['pin'];counts[key]+=1
        ep[key+('#'+str(counts[key]) if counts[key]>1 else '')]=p
    holes=[Point(x,y).buffer(1.6) for x,y in manifest['mounting_holes_mm']]
    before=sha(PATH);routed=[];pending=[]
    for e1,e2,width in PLAN:
        a,b=ep[e1],ep[e2];net=a['net'];assert net and net==b['net']
        # A narrow existing connection never substitutes for a specified trunk.
        prefix='gbuck-power:'+e1+':'+e2
        wide_tracks=[t for t in tracks if t['body']['width']*.0254>=width-1e-7]
        if connected(a,b,pads,wide_tracks):continue
        choices=[]
        for layer in sorted(set(a['layers'])&set(b['layers'])):
            obstacles=[p['geometry'] for p in pads if p['net']!=net and layer in p['layers']]
            obstacles += [t['geometry'] for t in tracks if t['net']!=net and t['layer']==layer]
            obstacles += [v['geometry'] for v in vias if v['net']!=net]+holes
            points=find_path(a,b,obstacles,width=width)
            if points:
                choices.append((LineString(points).length,layer,points))
        if not choices:
            pending.append({'from':e1,'to':e2,'net':net,'width_mm':width})
            continue
        length,layer,points=min(choices)
        for n,(s,t) in enumerate(zip(points,points[1:])):
            add_line(docs[pcb],prefix+':'+str(n),net,layer,s,t,width)
        _,pads,_,tracks=copper_geometry(meta,docs,pcb)
        assert connected(a,b,pads,tracks,vias)
        routed.append({'from':e1,'to':e2,'net':net,'width_mm':width,
                       'layer':layer,'points_mm':points,'length_mm':length})
        print(e1+' -> '+e2+' '+str(width)+'mm L'+str(layer),flush=True)
    if routed:
        label='power-trunks-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,meta,docs,{pcb},label)
        result={'baseline_sha256':before,'delivered_sha256':sha(PATH),'routed_pairs':routed,
                'pending_pairs':pending,'copper_thickness_um_assumed':35,
                'main_width_mm':2.,'capacitor_branch_width_mm':1.,
                'clearance_mm':.2,'thermal_validation':False,'manufacturing_release':False}
        (ROOT/'data/power_routing.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'added_pairs':len(routed),'pending_pairs':len(pending)}))


if __name__=='__main__':main()
