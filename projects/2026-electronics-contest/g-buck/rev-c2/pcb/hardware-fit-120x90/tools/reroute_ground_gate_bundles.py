"""Re-route the complete local signal fence when one-segment gates fail."""
from shapely import union_all
from stitch_ground_regions import groups
from route_multilayer import search,write_route
from route_pending import connected
from routing_engine import Router
from ground_copper_common import recut_fills
from pcb_common import *


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);before=sha(PATH);original=set(d[pcb]);changes=[]
    for iteration in range(10):
        main_group,others=groups(router)
        if not others:break
        success=False
        for group in others:
            names=[n for _,_,n in group if not n.startswith(('trace:','via:','fill:'))]
            if not names:continue
            saved=copy.deepcopy(d[pcb])
            island={l:union_all([g for g,ls,n in group if l in ls]) for l in (1,2)}
            fence=[t for t in router.tracks if t['net']!='GND' and t['body']['width']*.0254<=.3+1e-7
                   and t['geometry'].distance(island[t['layer']])<1.5]
            if not fence:continue
            for t in fence:del d[pcb]['LINE',t['id']]
            router.refresh()
            terminals=collections.defaultdict(list)
            for t in fence:
                old=t['body'];net=t['net'];layer=t['layer']
                for xk,yk in [('startX','startY'),('endX','endY')]:
                    x,y=old[xk]*.0254,old[yk]*.0254;point=Point(x,y)
                    touches=any(p['net']==net and layer in p['layers'] and point.distance(p['geometry'])<1e-6 for p in router.pads)
                    touches=touches or any(v['net']==net and point.distance(v['geometry'])<1e-6 for v in router.vias)
                    touches=touches or any(q['net']==net and q['layer']==layer and point.distance(q['geometry'])<1e-6 for q in router.tracks)
                    if touches and not any(math.dist((x,y),(p['x'],p['y']))<1e-6 and p['layers']==[layer] for p in terminals[net]):
                        terminals[net].append({'x':x,'y':y,'geometry':point.buffer(.001),'net':net,'layers':[layer]})
            planned=None
            # Anchor the new return to an existing wide power-ground path,
            # not a nearby pour neck that a subsequent recut could isolate.
            source=next(p for p in router.pads if p['ref']+'.'+p['pin']==names[0])
            anchor=next(p for p in router.pads if p['ref']=='J2' and p['pin']=='2')
            for gw in (.2,.15):
                planned=search(router,source,anchor,gw,step=.25)
                if planned:break
            if planned is None:
                print('No ground escape after fence removal: '+', '.join(names),flush=True)
                d[pcb]=saved;router.refresh();continue
            prefix='gbuck-ground-fence:'+':'.join(sorted(names))
            write_route(router,planned,prefix+':ground','GND',gw)
            new_foreign=set();foreign_routes=[];failed=False
            protected={n[5:] for _,_,n in group if n.startswith('fill:')}
            for net,points in sorted(terminals.items(),key=lambda q:len(q[1])):
                pairs=sorted([(math.dist((a['x'],a['y']),(b['x'],b['y'])),i,j) for i,a in enumerate(points)
                              for j,b in enumerate(points) if i<j])
                for _,i,j in pairs:
                    a,b=points[i],points[j]
                    if connected(a,b,router.pads,router.tracks,router.vias,router.fills):continue
                    original_fills=router.fills
                    router.fills=[dict(f,geometry=f['geometry'].buffer(.01)) for f in original_fills if f['id'] in protected]
                    result=search(router,a,b,.2,step=.25);router.fills=original_fills
                    if result is None:continue
                    oldkeys=set(d[pcb]);write_route(router,result,prefix+':'+net+':'+str(i)+':'+str(j),net,.2)
                    new_foreign.update(set(d[pcb])-oldkeys)
                    foreign_routes.append({'net':net,'width_mm':.2,'layer_runs':result[0],'new_vias_mm':result[1]})
                if points and any(not connected(points[0],p,router.pads,router.tracks,router.vias,router.fills) for p in points[1:]):
                    print('Replacement signal blocked: '+net+' near '+', '.join(names),flush=True)
                    failed=True;break
            if failed:
                d[pcb]=saved;router.refresh();continue
            recut_fills(router,new_foreign,prefix)
            new_main,new_others=groups(router)
            for detached in new_others:
                if all(n.startswith('fill:') for _,_,n in detached):
                    for _,_,n in detached:del d[pcb]['FILL',n[5:]]
            router.refresh();new_main,new_others=groups(router)
            if not set(names)<={n for _,_,n in new_main}:
                print('Ground endpoint not retained after recut: '+', '.join(names),flush=True)
                d[pcb]=saved;router.refresh();continue
            changes.append({'joined_ground_pads':names,'removed_signal_lines':[{'id':t['id'],'net':t['net'],'body':t['body']} for t in fence],
                            'ground_width_mm':gw,'ground_layer_runs':planned[0],'ground_vias_mm':planned[1],
                            'replacement_signals':foreign_routes})
            print('Ground fence opened and signals restored: '+', '.join(names),flush=True)
            success=True;break
        if not success:break
    _,others=groups(router);pending=[[n for _,_,n in g if not n.startswith(('trace:','via:','fill:'))] for g in others]
    if changes:
        label='ground-fence-bundles-'+hashlib.sha256(json.dumps(changes,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label,removed={pcb:sorted(original-set(d[pcb]))})
        previous=json.loads((ROOT/'data/ground_gate_bundles.json').read_text()) if (ROOT/'data/ground_gate_bundles.json').exists() else {}
        (ROOT/'data/ground_gate_bundles.json').write_text(json.dumps({'baseline_sha256':previous.get('baseline_sha256',before),'delivered_sha256':sha(PATH),
            'changes':previous.get('changes',[])+changes,'pending_ground_groups':pending,
            'replacement_copper_clearance_mm':.2,'native_DRC':'not_run','manufacturing_release':False},ensure_ascii=False,indent=2))
    print(json.dumps({'opened_fence_bundles':len(changes),'pending_ground_groups':pending}))


if __name__=='__main__':main()
