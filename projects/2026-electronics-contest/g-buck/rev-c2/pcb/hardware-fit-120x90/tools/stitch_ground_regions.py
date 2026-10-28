"""Join overlapping, physically separate GND regions across the two layers."""
from shapely import union_all
from pcb_common import *

VIA_DIAMETER=.6
DRILL_DIAMETER=.3


def groups(router):
    nodes=[]
    for p in router.pads:
        if p['net']=='GND':nodes.append((p['geometry'],set(p['layers']),p['ref']+'.'+p['pin']))
    nodes += [(t['geometry'],{t['layer']},'trace:'+t['id']) for t in router.tracks if t['net']=='GND']
    nodes += [(v['geometry'],{1,2},'via:'+v['id']) for v in router.vias if v['net']=='GND']
    nodes += [(f['geometry'],{f['layer']},'fill:'+f['id']) for f in router.fills if f['net']=='GND']
    parent=list(range(len(nodes)))
    def find(i):
        while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i in range(len(nodes)):
        for j in range(i):
            if nodes[i][1]&nodes[j][1] and nodes[i][0].distance(nodes[j][0])<1e-5:parent[find(i)]=find(j)
    out=collections.defaultdict(list)
    for i,node in enumerate(nodes):out[find(i)].append(node)
    main=next(g for g in out.values() if any(n[2]=='J1.2' for n in g))
    return main,[g for g in out.values() if g is not main]


def main():
    from routing_engine import Router
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);before=sha(PATH);added=[]
    for iteration in range(40):
        main_group,others=groups(router)
        if not others:break
        main_geo={l:union_all([g for g,ls,n in main_group if l in ls]) for l in (1,2)}
        # Same-net annular copper may join a pad. Keep the drill outside the
        # soldering pad with a 0.10mm gap; do not require an artificial 0.20mm
        # copper gap between conductors that are intended to be connected.
        foreign=union_all(router.obstacles('GND',1)+router.obstacles('GND',2)).buffer(VIA_DIAMETER/2+.205)
        pad_drill_keepout=[p['geometry'].buffer(DRILL_DIAMETER/2+.105) for p in router.pads if p['net']=='GND']
        via_drill_keepout=[Point(v['x'],v['y']).buffer(DRILL_DIAMETER/2+v['hole_diameter']/2+.205)
                           for v in router.vias if v['net']=='GND']
        forbidden=union_all([foreign]+pad_drill_keepout+via_drill_keepout)
        found=False
        for group in others:
            pads=[n for _,_,n in group if not n.startswith(('trace:','via:','fill:'))]
            for layer in (1,2):
                island=union_all([g for g,ls,n in group if layer in ls])
                # The annular ring can reach existing copper even when its
                # drill center is just outside that copper's boundary.
                reach=VIA_DIAMETER/2-.1
                safe=island.buffer(reach).intersection(main_geo[3-layer].buffer(reach)).difference(forbidden)
                polygons=[g for g in getattr(safe,'geoms',[safe]) if g.geom_type=='Polygon' and g.area>1e-5]
                if not polygons:continue
                candidate=max(polygons,key=lambda g:g.area).representative_point()
                x,y=candidate.x,candidate.y;via=Point(x,y).buffer(VIA_DIAMETER/2)
                annulus=via.difference(Point(x,y).buffer(DRILL_DIAMETER/2))
                if annulus.intersection(island).area<.005 or annulus.intersection(main_geo[3-layer]).area<.005:continue
                if not box(.5,.5,119.5,89.5).covers(via):continue
                assert all(via.distance(g)>=.2-1e-7 for l in (1,2) for g in router.obstacles('GND',l))
                assert all(candidate.distance(p['geometry'])>=DRILL_DIAMETER/2+.1-1e-7 for p in router.pads if p['net']=='GND')
                assert all(candidate.distance(Point(v['x'],v['y']))-(DRILL_DIAMETER+v['hole_diameter'])/2>=.2-1e-7
                           for v in router.vias if v['net']=='GND')
                vid=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-ground-region-stitch:'+':'.join(sorted(pads))).hex[:16]
                d[pcb]['VIA',vid]={'partitionId':'','groupId':0,'netName':'GND','ruleName':'',
                    'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':DRILL_DIAMETER/.0254,'viaDiameter':VIA_DIAMETER/.0254,
                    'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
                    'locked':False,'unusedInnerLayers':[]}
                added.append({'via_id':vid,'center_mm':[x,y],'joined_ground_pads':pads,
                              'diameter_mm':VIA_DIAMETER,'drill_mm':DRILL_DIAMETER})
                router.refresh();found=True
                print('Ground region stitched: '+', '.join(pads),flush=True)
                break
            if found:break
        if not found:break
    _,others=groups(router)
    pending=[[n for _,_,n in g if not n.startswith(('trace:','via:','fill:'))] for g in others]
    if added:
        label='ground-region-stitches-'+hashlib.sha256(json.dumps(added,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        previous=json.loads((ROOT/'data/ground_region_stitches.json').read_text()) if (ROOT/'data/ground_region_stitches.json').exists() else {}
        (ROOT/'data/ground_region_stitches.json').write_text(json.dumps({'baseline_sha256':previous.get('baseline_sha256',before),
            'delivered_sha256':sha(PATH),'added_vias':previous.get('added_vias',[])+added,'pending_ground_groups':pending,
            'same_net_pad_to_drill_gap_mm':.1,
            'native_DRC':'not_run','manufacturing_release':False},ensure_ascii=False,indent=2))
    print(json.dumps({'region_stitch_vias':len(added),'pending_ground_groups':pending}))


if __name__=='__main__':main()
