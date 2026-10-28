"""A* across two copper layers, with physical, clearance-checked transitions."""
import heapq,itertools
import numpy as np
from shapely import union_all,prepare,intersects_xy
from routing_engine import Router
from route_pending import connected
from route_driver_bottom import add_line
from pcb_common import *


def search(router,a,b,width,step=.5):
    start=(a['x'],a['y']);end=(b['x'],b['y'])
    obstacles={l:router.obstacles(a['net'],l) for l in (1,2)}
    forbidden={l:union_all(obstacles[l]).buffer(width/2+.205) for l in (1,2)}
    for g in forbidden.values():prepare(g)
    # Joining copper of the same net is intentional. Keep the new drill out
    # of solder pads and preserve drill web, rather than imposing foreign-net
    # copper clearance on that connection and making legal fanouts impossible.
    via_foreign=union_all(obstacles[1]+obstacles[2]).buffer(.505)
    via_pad_keepout=[p['geometry'].buffer(.255) for p in router.pads if p['net']==a['net']]
    via_drill_keepout=[Point(v['x'],v['y']).buffer(.15+v['hole_diameter']/2+.205)
                       for v in router.vias if v['net']==a['net']]
    via_forbid=union_all([via_foreign]+via_pad_keepout+via_drill_keepout)
    prepare(via_forbid)
    transitions=union_all([p['geometry'] for p in router.pads if p['net']==a['net'] and 2 in p['layers']]
                          +[v['geometry'] for v in router.vias if v['net']==a['net']])
    for margin in (10.,25.):
        xs=np.arange(max(1.,math.floor((min(start[0],end[0])-margin)/step)*step),min(119.,max(start[0],end[0])+margin),step)
        ys=np.arange(max(1.,math.floor((min(start[1],end[1])-margin)/step)*step),min(89.,max(start[1],end[1])+margin),step)
        # Pin-pitch corridors can be legal yet narrower than the regular grid.
        # Add exact clearance-edge coordinates around both endpoints instead
        # of weakening clearance or relying on a coincidental grid phase.
        cx=[start[0],end[0]];cy=[start[1],end[1]];radius=width/2+.207
        for p in router.pads:
            if min(math.dist((p['x'],p['y']),start),math.dist((p['x'],p['y']),end))>4:continue
            x0,y0,x1,y1=p['geometry'].bounds
            cx += [x0-radius,x1+radius];cy += [y0-radius,y1+radius]
            vr=.257 if p['net']==a['net'] else .507
            cx += [x0-vr,x1+vr];cy += [y0-vr,y1+vr]
        xs=np.unique(np.concatenate((xs,[x for x in cx if xs[0]<=x<=xs[-1]])))
        ys=np.unique(np.concatenate((ys,[y for y in cy if ys[0]<=y<=ys[-1]])))
        xx,yy=np.meshgrid(xs,ys,indexing='ij')
        free={l:~intersects_xy(forbidden[l],xx,yy) for l in (1,2)}
        via_free=~intersects_xy(via_forbid,xx,yy)
        existing=intersects_xy(transitions,xx,yy)
        def pt(n):return float(xs[n[0]]),float(ys[n[1]])
        def clear(p,q,l):return not forbidden[l].intersects(LineString([p,q]))
        def anchors(p,layers):
            i,j=int(np.searchsorted(xs,p[0])),int(np.searchsorted(ys,p[1]))
            return [(x,y,l) for x in range(max(0,i-2),min(len(xs),i+3)) for y in range(max(0,j-2),min(len(ys),j+3))
                    for l in layers if free[l][x,y] and clear(p,pt((x,y,l)),l)]
        targets=set(anchors(end,b['layers']));cost={};prev={};queue=[];counter=itertools.count()
        for n in anchors(start,a['layers']):
            g=math.dist(start,pt(n));cost[n]=g;prev[n]=None
            heapq.heappush(queue,(g+math.dist(pt(n),end),next(counter),g,n))
        found=None;expanded=0
        while queue:
            _,_,g,n=heapq.heappop(queue)
            if g!=cost[n]:continue
            expanded+=1
            if expanded>60000:break
            if n in targets:found=n;break
            neighbors=[]
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                x,y=n[0]+dx,n[1]+dy
                if 0<=x<len(xs) and 0<=y<len(ys) and free[n[2]][x,y]:
                    q=(x,y,n[2])
                    if clear(pt(n),pt(q),n[2]):neighbors.append((q,math.dist(pt(n),pt(q))))
            if (via_free[n[0],n[1]] or existing[n[0],n[1]]) and free[3-n[2]][n[0],n[1]]:
                neighbors.append(((n[0],n[1],3-n[2]),.05 if existing[n[0],n[1]] else 4.))
            for q,edge in neighbors:
                ng=g+edge
                if ng<cost.get(q,float('inf')):
                    cost[q]=ng;prev[q]=n
                    heapq.heappush(queue,(ng+math.dist(pt(q),end),next(counter),ng,q))
        if found is None:continue
        chain=[]
        while found is not None:chain.append(found);found=prev[found]
        chain.reverse()
        runs=[];vias=[];points=[start];layer=chain[0][2]
        for n in chain:
            if n[2]!=layer:
                p=pt(n)
                if not existing[n[0],n[1]]:vias.append(p)
                runs.append((layer,points));points=[p];layer=n[2]
            if math.dist(points[-1],pt(n))>1e-7:points.append(pt(n))
        if math.dist(points[-1],end)>1e-7:points.append(end)
        runs.append((layer,points));simple=[]
        for l,pts in runs:
            result=[pts[0]];i=0
            while i<len(pts)-1:
                j=len(pts)-1
                while j>i+1 and not clear(pts[i],pts[j],l):j-=1
                if math.dist(result[-1],pts[j])>1e-7:result.append(pts[j])
                i=j
            if len(result)>1:simple.append((l,result))
        # Different new transitions must also have independent drill clearance.
        if any(math.dist(p,q)<.805 for p,q in itertools.combinations(vias,2)):continue
        return simple,vias
    return None


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);ep={p['ref']+'.'+p['pin']:p for p in router.pads}
    from route_final_signals import PAIRS
    queue=[('J_CTL.2','J_AUX5.3',.6)]+PAIRS[1:]
    routed=[];pending=[];before=sha(PATH)
    for src,dst,width in queue:
        a,b=ep[src],ep[dst]
        if connected(a,b,router.pads,router.tracks,router.vias):continue
        result=search(router,a,b,width)
        if result is None:result=search(router,a,b,width,step=.25)
        if result is None:
            pending.append({'from':src,'to':dst});print(src+' -> '+dst+' BLOCKED',flush=True);continue
        runs,vias=result;key='gbuck-multilayer:'+src+':'+dst
        for rn,(layer,points) in enumerate(runs):
            for n,(s,t) in enumerate(zip(points,points[1:])):add_line(d[pcb],key+':run:'+str(rn)+':'+str(n),a['net'],layer,s,t,width)
        for n,(x,y) in enumerate(vias):
            vid=uuid.uuid5(uuid.NAMESPACE_URL,key+':via:'+str(n)).hex[:16]
            d[pcb]['VIA',vid]={'partitionId':'','groupId':0,'netName':a['net'],'ruleName':'',
                'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.3/.0254,'viaDiameter':.6/.0254,
                'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
                'locked':False,'unusedInnerLayers':[]}
        router.refresh();assert connected(a,b,router.pads,router.tracks,router.vias)
        routed.append({'from':src,'to':dst,'net':a['net'],'width_mm':width,'layer_runs':runs,'new_vias_mm':vias})
        print(src+' -> '+dst+' connected, '+str(len(vias))+' transitions',flush=True)
    if routed:
        label='multilayer-signals-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        previous=json.loads((ROOT/'data/multilayer_routing.json').read_text()) if (ROOT/'data/multilayer_routing.json').exists() else {}
        saved={(p['from'],p['to']):p for p in previous.get('routed_pairs',[])}
        saved.update({(p['from'],p['to']):p for p in routed})
        (ROOT/'data/multilayer_routing.json').write_text(json.dumps({'baseline_sha256':previous.get('baseline_sha256',before),'delivered_sha256':sha(PATH),
            'routed_pairs':list(saved.values()),'pending_pairs':pending,'native_DRC':'not_run'},ensure_ascii=False,indent=2))
    print(json.dumps({'added_pairs':len(routed),'pending':len(pending)}))


def write_route(router,result,key,net,width):
    runs,vias=result;o=router.docs[router.pcb]
    for rn,(layer,points) in enumerate(runs):
        for n,(s,t) in enumerate(zip(points,points[1:])):add_line(o,key+':run:'+str(rn)+':'+str(n),net,layer,s,t,width)
    for n,(x,y) in enumerate(vias):
        vid=uuid.uuid5(uuid.NAMESPACE_URL,key+':via:'+str(n)).hex[:16]
        o['VIA',vid]={'partitionId':'','groupId':0,'netName':net,'ruleName':'',
            'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.3/.0254,'viaDiameter':.6/.0254,
            'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
            'locked':False,'unusedInnerLayers':[]}
    router.refresh()


if __name__=='__main__':main()
