"""Finish explicit auxiliary feeds, then signal-net copper islands.

Never substitute signal-width copper for specified main power trunks.
The ground return is handled separately after signal routing.
"""
from routing_engine import Router
from route_pending import connected
from pcb_common import *

FEEDS=[('RS_IN.2','J_AUX12.1',1.),('RS_IN.2','J_AUX5.1',1.),
       ('J_AUX12.3','D_BOOT.1',.6),('J_AUX5.3','C_U5.1',.6),
       ('J_AUX5.3','C_U9.1',.6),('J_AUX5.3','J_CTL.2',.6)]


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);ep={p['ref']+'.'+p['pin']:p for p in router.pads}
    before=sha(PATH);routed=[];pending=[]
    for src,dst,width in FEEDS:
        key='gbuck-aux-feed:'+src+':'+dst
        if ('LINE',uuid.uuid5(uuid.NAMESPACE_URL,key+':main:0').hex[:16]) in d[pcb]:continue
        result=router.route(ep[src],ep[dst],key,width=width,force_branch=True)
        if result and not result.get('already_connected'):
            routed.append({'from':src,'to':dst,'class':'auxiliary_feed',**result})
            print(src+' -> '+dst+' auxiliary feed',flush=True)
        elif result is None:pending.append({'from':src,'to':dst,'class':'auxiliary_feed'})
    groups=collections.defaultdict(list)
    for p in router.pads:
        if p['net'] and p['net']!='GND':groups[p['net']].append(p)
    # Protect dedicated sense inputs from becoming branching points for loads.
    sense={('U2','1'),('U2','8'),('U4','1'),('U4','8'),('U3','3'),('U3','4')}
    kelvin=json.loads((ROOT/'data/kelvin_routing.json').read_text())
    sense_track_ids={uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-kelvin:'+p['from']+':'+p['to']+':main:'+str(n)).hex[:16]
                     for p in kelvin['routed_pairs'] for n in range(len(p['points_mm'])-1)}
    for net,nodes in sorted(groups.items(),key=lambda q:(len(q[1]),q[0])):
        pairs=[]
        for a,b in itertools.combinations(nodes,2):
            if (a['ref'],a['pin']) in sense or (b['ref'],b['pin']) in sense:continue
            pairs.append((math.dist((a['x'],a['y']),(b['x'],b['y'])),a,b))
        failures=[];added=0
        for _,a,b in sorted(pairs,key=lambda q:q[0]):
            if connected(a,b,router.pads,router.tracks,router.vias):continue
            src,dst=a['ref']+'.'+a['pin'],b['ref']+'.'+b['pin']
            key='gbuck-signal:'+src+':'+dst
            extra={l:[t['geometry'] for t in router.tracks if t['net']==net and t['layer']==l and t['id'] in sense_track_ids]
                   for l in (1,2)}
            width=.6 if net in ('+5V','+12V_DRV') else .25
            result=router.route(a,b,key,width=width,extra=extra)
            if result:
                routed.append({'from':src,'to':dst,'class':'signal',**result});added+=1
            else:failures.append({'from':src,'to':dst,'net':net})
        # Report only still-disconnected endpoint attempts, not stale attempts
        # that were resolved through another branch of the same net.
        for f in failures:
            if not connected(ep[f['from']],ep[f['to']],router.pads,router.tracks,router.vias):pending.append(f)
        print(net+': '+str(added)+' signal links added',flush=True)
    if routed:
        label='remaining-signals-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        (ROOT/'data/signal_routing.json').write_text(json.dumps({'baseline_sha256':before,
            'delivered_sha256':sha(PATH),'routed_pairs':routed,'pending_attempts':pending,
            'clearance_mm':.2,'native_DRC':'not_run','manufacturing_release':False},ensure_ascii=False,indent=2))
    print(json.dumps({'added_pairs':len(routed),'unresolved_attempts':len(pending)}))


if __name__=='__main__':
    import itertools
    main()
