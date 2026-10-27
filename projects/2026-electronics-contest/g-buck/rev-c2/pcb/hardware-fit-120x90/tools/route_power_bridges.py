"""Explicit parallel-via bridges for power SMD pads blocked on top copper."""
from route_driver_bottom import add_line
from route_pending import find_path, connected
from pcb_common import *

BRIDGES=[('C2.2','C1.2',1.,[(66.4,70.8),(67.6,70.8)]),
         ('C4.2','C3.2',1.,[(100.4,61.2),(101.6,61.2)])]


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb']
    m,d,_=read_project(PATH);_,pads,bodies,tracks=copper_geometry(m,d,pcb);vias=copper_vias(d,pcb)
    ep={p['ref']+'.'+p['pin']:p for p in pads};holes=[Point(x,y).buffer(1.6) for x,y in mf['mounting_holes_mm']]
    before=sha(PATH);routed=[]
    for src,dst,width,positions in BRIDGES:
        prefix='gbuck-power-bridge:'+src+':'+dst
        if ('VIA',uuid.uuid5(uuid.NAMESPACE_URL,prefix+':via:0').hex[:16]) in d[pcb]:continue
        a,b=ep[src],ep[dst];net=a['net'];assert net==b['net']
        center=(sum(x for x,y in positions)/len(positions),sum(y for x,y in positions)/len(positions))
        obstacles={layer:[p['geometry'] for p in pads if p['net']!=net and layer in p['layers']]
                   +[t['geometry'] for t in tracks if t['net']!=net and t['layer']==layer]
                   +[v['geometry'] for v in vias if v['net']!=net]+holes for layer in (1,2)}
        new_vias=[Point(x,y).buffer(.5) for x,y in positions]
        assert all(box(.5,.5,119.5,89.5).covers(g) for g in new_vias)
        assert all(g.distance(p['geometry'])>=.20-1e-7 for g in new_vias for p in pads)
        assert all(g.distance(v['geometry'])>=.20-1e-7 for g in new_vias for v in vias)
        assert all(g.distance(h)>=.20-1e-7 for g in new_vias for layer in (1,2) for h in obstacles[layer])
        top_path=find_path(a,{'x':center[0],'y':center[1]},obstacles[1],width=width)
        assert top_path,('No top power bridge',src,dst)
        top=[(s,t,width) for s,t in zip(top_path,top_path[1:])]+[(center,p,.8) for p in positions]
        bottom=find_path({'x':center[0],'y':center[1]},b,obstacles[2],width=width)
        assert bottom,('No bottom power bridge',src,dst)
        for s,t,w in top:
            assert all(LineString([s,t]).buffer(w/2).distance(g)>=.20-1e-7 for g in obstacles[1])
        for n,(s,t,w) in enumerate(top):add_line(d[pcb],prefix+':top:'+str(n),net,1,s,t,w)
        for n,(s,t) in enumerate(zip(bottom,bottom[1:])):add_line(d[pcb],prefix+':bottom:'+str(n),net,2,s,t,width)
        for n,(x,y) in enumerate(positions):
            vid=uuid.uuid5(uuid.NAMESPACE_URL,prefix+':via:'+str(n)).hex[:16]
            d[pcb]['VIA',vid]={'partitionId':'','groupId':0,'netName':net,'ruleName':'',
                'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.5/.0254,'viaDiameter':1./.0254,
                'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
                'locked':False,'unusedInnerLayers':[]}
        _,pads,_,tracks=copper_geometry(m,d,pcb);vias=copper_vias(d,pcb)
        assert connected(a,b,pads,tracks,vias)
        routed.append({'from':src,'to':dst,'net':net,'width_mm':width,'via_centers_mm':positions,
                       'via_diameter_mm':1.,'drill_mm':.5,'top_paths_mm':top,'bottom_path_mm':bottom})
    if routed:
        label='power-bridges-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        (ROOT/'data/power_bridges.json').write_text(json.dumps({'baseline_sha256':before,
            'delivered_sha256':sha(PATH),'routed_pairs':routed,'thermal_validation':False},ensure_ascii=False,indent=2))
    print(json.dumps({'added_power_bridges':len(routed)}))


if __name__=='__main__':main()
