"""Resolve the audited residual signal queue, allowing one intermediate via."""
from routing_engine import Router
from route_pending import connected
from pcb_common import *

PAIRS=[('J_CTL.2','C_U9.1',.6),('U7.3','U1.2',.25),
       ('U5.1','R13.2',.25),('U5.7','R13.2',.25),('D_POR.1','R13.2',.25),('J_CTL.9','R13.2',.25),
       ('U2.5','R7.1',.25),('U4.5','R_IL_ADC.1',.25),('U9.6','C_IOUT_PROT.1',.25),
       ('R_PWM.1','J_CTL.5',.25),('U1.6','QH.3',.4),
       ('R_VINP_TOP.1','RS_IN.2',.25),('R1.1','J1.1',.25),('U9.5','C_REF_IOUT.1',.25)]


def middle_route(router,a,b,key,width):
    obs={l:router.obstacles(a['net'],l) for l in (1,2)}
    dx,dy=b['x']-a['x'],b['y']-a['y'];length=math.hypot(dx,dy)
    candidates=[]
    for fraction in (.25,.5,.75):
        for offset in (-4,4,-8,8):
            x=a['x']+dx*fraction-dy/length*offset
            y=a['y']+dy*fraction+dx/length*offset
            g=Point(x,y).buffer(.3)
            if not box(.5,.5,119.5,89.5).covers(g):continue
            if any(g.distance(h)<.205 for h in obs[1]+obs[2]):continue
            if any(g.distance(q['geometry'])<.2 for q in router.pads+router.vias):continue
            candidates.append((x,y))
    for n,(x,y) in enumerate(candidates):
        old=set(router.docs[router.pcb])
        vid=uuid.uuid5(uuid.NAMESPACE_URL,key+':middle:'+str(n)).hex[:16]
        router.docs[router.pcb]['VIA',vid]={'partitionId':'','groupId':0,'netName':a['net'],'ruleName':'',
            'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.3/.0254,'viaDiameter':.6/.0254,
            'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
            'locked':False,'unusedInnerLayers':[]}
        router.refresh();mid={'x':x,'y':y,'geometry':Point(x,y).buffer(.3),'layers':[1,2],'net':a['net']}
        first=router.route(a,mid,key+':a:'+str(n),width=width)
        second=router.route(mid,b,key+':b:'+str(n),width=width) if first else None
        if first and second:return {'intermediate_via_mm':[x,y],'first':first,'second':second}
        for k in set(router.docs[router.pcb])-old:del router.docs[router.pcb][k]
        router.refresh()
    return None


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);ep={p['ref']+'.'+p['pin']:p for p in router.pads}
    before=sha(PATH);routed=[];pending=[];corner_changes=[]
    # Retain the route but move the audited corner 0.05mm away from U9.2.
    for t in router.tracks:
        if t['net']!='IL_PROT' or t['layer']!=1:continue
        for xk,yk in [('startX','startY'),('endX','endY')]:
            if abs(t['body'][xk]*.0254-70.25)<1e-7 and abs(t['body'][yk]*.0254-35)<1e-7:
                t['body'][xk]=70.30/.0254;corner_changes.append(t['id'])
    router.refresh()
    for src,dst,width in PAIRS:
        a,b=ep[src],ep[dst]
        if connected(a,b,router.pads,router.tracks,router.vias):continue
        key='gbuck-final-signal:'+src+':'+dst
        result=router.route(a,b,key,width=width)
        if result is None:result=middle_route(router,a,b,key,width)
        if result:
            assert connected(a,b,router.pads,router.tracks,router.vias)
            routed.append({'from':src,'to':dst,'width_mm':width,'route':result})
            print(src+' -> '+dst+' connected',flush=True)
        else:pending.append({'from':src,'to':dst});print(src+' -> '+dst+' BLOCKED',flush=True)
    if routed or corner_changes:
        label='final-signals-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        (ROOT/'data/final_signal_routing.json').write_text(json.dumps({'baseline_sha256':before,
            'delivered_sha256':sha(PATH),'routed_pairs':routed,'pending_pairs':pending,
            'corner_clearance_repair_line_ids':corner_changes,'corner_mm_before':[70.25,35.],
            'corner_mm_after':[70.30,35.]},ensure_ascii=False,indent=2))
    print(json.dumps({'added_pairs':len(routed),'pending_pairs':len(pending)}))


if __name__=='__main__':main()
