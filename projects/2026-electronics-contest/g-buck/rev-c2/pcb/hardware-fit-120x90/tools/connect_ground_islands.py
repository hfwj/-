"""Tie audited GND islands to the existing main return with real copper."""
from routing_engine import Router
from route_multilayer import search,write_route
from route_pending import connected
from pcb_common import *


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);ep={p['ref']+'.'+p['pin']:p for p in router.pads}
    anchor=ep['J1.2'];before=sha(PATH)
    queue=json.loads((ROOT/'data/unrouted_networks.json').read_text())
    ground=next((q for q in queue if q['net']=='GND'),None)
    if ground is None:
        print('No GND pad islands remain in the audited queue.');return
    main_group=next(g for g in ground['endpoints'] if 'J1.2' in g)
    others=[g for g in ground['endpoints'] if g is not main_group]
    routed=[];pending=[]
    for group in others:
        if connected(ep[group[0]],anchor,router.pads,router.tracks,router.vias,router.fills):
            main_group+=group;continue
        candidates=sorted([(math.dist((ep[a]['x'],ep[a]['y']),(ep[b]['x'],ep[b]['y'])),a,b)
                           for a in group for b in main_group])
        done=False
        for _,src,dst in candidates[:8]:
            a,b=ep[src],ep[dst];width=.4 if a['ref']=='J_CTL' else .2
            result=search(router,a,b,width)
            if result is None:result=search(router,a,b,width,step=.25)
            if result is None:continue
            key='gbuck-ground-island:'+src+':'+dst
            write_route(router,result,key,'GND',width)
            assert connected(a,anchor,router.pads,router.tracks,router.vias,router.fills)
            routed.append({'from':src,'to':dst,'width_mm':width,'layer_runs':result[0],
                           'new_vias_mm':result[1],'group_endpoints':group})
            main_group+=group;done=True
            print(src+' -> '+dst+' grounded',flush=True)
            break
        if not done:pending.append(group)
    if routed:
        label='ground-island-links-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        # The saved project, rather than the in-memory plan, is the authority.
        rm,rd,_=read_project(PATH);_,rp,_,rt=copper_geometry(rm,rd,pcb)
        rv=copper_vias(rd,pcb);rf=copper_fills(rd,pcb)
        ra=next(p for p in rp if p['ref']=='J1' and p['pin']=='2')
        missing=[p['ref']+'.'+p['pin'] for p in rp if p['net']=='GND' and not connected(p,ra,rp,rt,rv,rf)]
        previous=json.loads((ROOT/'data/ground_island_connections.json').read_text()) if (ROOT/'data/ground_island_connections.json').exists() else {}
        saved={(p['from'],p['to']):p for p in previous.get('routed_pairs',[])}
        saved.update({(p['from'],p['to']):p for p in routed})
        (ROOT/'data/ground_island_connections.json').write_text(json.dumps({'baseline_sha256':previous.get('baseline_sha256',before),
            'delivered_sha256':sha(PATH),'routed_pairs':list(saved.values()),'pending_groups':pending,
            'saved_ground_endpoints_still_disconnected':missing,'native_DRC':'not_run',
            'manufacturing_release':False},ensure_ascii=False,indent=2))
    print(json.dumps({'added_island_links':len(routed),'pending_groups':len(pending)}))


if __name__=='__main__':main()
