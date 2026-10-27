"""Draft static GND copper regions from actual routing, with off-pad stitching.

Solid FILL records are intentionally used rather than claiming an EDA-client
zone refill. Client import, solder-mask tenting and thermal relief remain open.
"""
from shapely import union_all
from shapely.geometry.polygon import orient
from routing_engine import Router
from route_driver_bottom import add_line
from route_pending import connected
from pcb_common import *


def ring_path(ring):
    values=[v/.0254 for xy in ring.coords for v in xy]
    return values[:2]+['L']+values[2:]


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    if copper_fills(d,pcb):
        print('Static ground regions already exist; inspect before replacing.');return
    router=Router(m,d,pcb,mf['mounting_holes_mm']);before=sha(PATH)
    ground=[p for p in router.pads if p['net']=='GND'];stitched=[];pending=[]
    for p in ground:
        # Already connected to any bottom-accessible pad/via needs no new via.
        bottom=[q for q in router.pads if q['net']=='GND' and 2 in q['layers']]
        bottom += [dict(v,layers=[1,2]) for v in router.vias if v['net']=='GND']
        if any(connected(p,q,router.pads,router.tracks,router.vias) for q in bottom):continue
        obs={l:router.obstacles('GND',l) for l in (1,2)}
        choices=router.via_options(p,obs,.3)
        if not choices:
            pending.append(p['ref']+'.'+p['pin']);continue
        choice=min(choices,key=lambda v:math.dist((p['x'],p['y']),v['point']))
        x,y=choice['point'];key='gbuck-ground-stitch:'+p['ref']+':'+p['pin']
        for sn,(s,t) in enumerate(zip(choice['stub'],choice['stub'][1:])):
            add_line(d[pcb],key+':stub:'+str(sn),'GND',1,s,t,.3)
        vid=uuid.uuid5(uuid.NAMESPACE_URL,key+':via').hex[:16]
        d[pcb]['VIA',vid]={'partitionId':'','groupId':0,'netName':'GND','ruleName':'',
            'centerX':x/.0254,'centerY':y/.0254,'holeDiameter':.3/.0254,'viaDiameter':.6/.0254,
            'viaType':'NORMAL','topSolderExpansion':None,'bottomSolderExpansion':None,
            'locked':False,'unusedInnerLayers':[]}
        stitched.append({'endpoint':p['ref']+'.'+p['pin'],'via_center_mm':[x,y]})
        router.refresh()
    fills=[]
    switch=[t['geometry'].buffer(.5) for t in router.tracks if t['net']=='SW']
    switch += [p['geometry'].buffer(.5) for p in router.pads if p['net']=='SW']
    for layer in (1,2):
        # Wider clearance for fill than signal routing; trim narrow necks and
        # retain only areas that touch intended GND pads or through-vias.
        cut=[g.buffer(.105) for g in router.obstacles('GND',layer)]
        cut += [Point(x,y).buffer(2.1) for x,y in mf['mounting_holes_mm']]+switch
        region=box(1,1,119,89).difference(union_all(cut).buffer(.2))
        region=region.buffer(-.2).buffer(.2)
        polys=list(region.geoms) if region.geom_type=='MultiPolygon' else [region]
        anchors=[p['geometry'] for p in router.pads if p['net']=='GND' and layer in p['layers']]
        anchors += [v['geometry'] for v in router.vias if v['net']=='GND']
        anchors += [t['geometry'] for t in router.tracks if t['net']=='GND' and t['layer']==layer]
        for n,g in enumerate(polys):
            if g.area<1 or not any(g.intersects(a) for a in anchors):continue
            g=orient(g,sign=1.)
            fid=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-ground-fill:'+str(layer)+':'+str(n)).hex[:16]
            d[pcb]['FILL',fid]={'partitionId':'','groupId':0,'netName':'GND','layerId':layer,
                'width':0,'fillStyle':'SOLID','path':[ring_path(g.exterior)]+[ring_path(q) for q in g.interiors],
                'locked':False,'zIndex':-1,'isBridgingCopper':False,'networkList':[],'refs':None}
            fills.append({'id':fid,'layer':layer,'area_mm2':g.area})
    label='ground-regions-'+hashlib.sha256(json.dumps(fills,sort_keys=True).encode()).hexdigest()[:16]
    append_history(PATH,m,d,{pcb},label)
    rm,rd,_=read_project(PATH);_,rp,_,rt=copper_geometry(rm,rd,pcb);rv=copper_vias(rd,pcb);rf=copper_fills(rd,pcb)
    anchor=next(p for p in rp if p['ref']=='J1' and p['pin']=='2')
    missing=[p['ref']+'.'+p['pin'] for p in rp if p['net']=='GND' and not connected(p,anchor,rp,rt,rv,rf)]
    (ROOT/'data/ground_copper.json').write_text(json.dumps({'baseline_sha256':before,
        'delivered_sha256':sha(PATH),'stitching_vias':stitched,'static_regions':fills,
        'minimum_fill_clearance_mm':.3,'board_edge_margin_mm':1.,'switch_keepout_mm':.5,
        'unstitched_initial_pads':pending,'ground_endpoints_still_disconnected':missing,
        'native_zone_refill':False,'thermal_relief':False,'manufacturing_release':False},ensure_ascii=False,indent=2))
    print(json.dumps({'stitching_vias':len(stitched),'ground_regions':len(fills),'disconnected_ground_pads':missing}))


if __name__=='__main__':main()
