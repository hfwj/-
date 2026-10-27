"""Rip up the new IOUT_OC_N branches to release the adjacent U9.6 fanout."""
from route_multilayer import search,write_route
from routing_engine import Router
from route_pending import connected
from pcb_common import *

def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);ep={p['ref']+'.'+p['pin']:p for p in router.pads}
    if connected(ep['U9.6'],ep['C_IOUT_PROT.1'],router.pads,router.tracks,router.vias):
        print('Output protection fanout already complete.');return
    before=sha(PATH)
    kept=set()
    for route in json.loads((ROOT/'data/multilayer_routing.json').read_text())['routed_pairs']:
        if route['from']=='J_CTL.2' and route['to']=='J_AUX5.3':
            prefix='gbuck-multilayer:J_CTL.2:J_AUX5.3'
            for rn,(_,points) in enumerate(route['layer_runs']):
                for n in range(len(points)-1):kept.add(('LINE',uuid.uuid5(uuid.NAMESPACE_URL,prefix+':run:'+str(rn)+':'+str(n)).hex[:16]))
            for n in range(len(route['new_vias_mm'])):kept.add(('VIA',uuid.uuid5(uuid.NAMESPACE_URL,prefix+':via:'+str(n)).hex[:16]))
    removed=[k for k,b in d[pcb].items() if
             (k[0] in ('LINE','VIA') and b['netName'] in ('IOUT_OC_N','+5V') and k not in kept) or
             (k[0]=='LINE' and b['netName']=='GND' and b['layerId']==1 and b['width']*.0254<=.3)]
    for k in removed:del d[pcb][k]
    # The pull-up was boxed in by reference/ADC copper. Move it into the free
    # control area and extend its existing +3V3 junction without changing value.
    old_supply=copy.deepcopy(ep['R_IOUT_PU.1'])
    cid,c,_=router.parts['R_IOUT_PU'];old_position=[c['x']*.0254,c['y']*.0254,c['angle']]
    dx,dy=82.5/.0254-c['x'],23./.0254-c['y']
    c.update(x=82.5/.0254,y=23./.0254,angle=0)
    for (kind,_),attr in d[pcb].items():
        if kind=='ATTR' and attr.get('parentId')==cid:
            if attr.get('x') is not None:attr['x']+=dx
            if attr.get('y') is not None:attr['y']+=dy
    mf['parts']['R_IOUT_PU'].update(x=82.5,y=23.,angle=0)
    router.refresh();ep={p['ref']+'.'+p['pin']:p for p in router.pads};ep['old_pullup_supply_junction']=old_supply
    routed=[]
    pairs=[('U9.6','C_IOUT_PROT.1',.25),('U9.7','J_CTL.6',.25),('J_CTL.6','R_IOUT_PU.2',.25),
           ('U9.8','C_U9.1',.6),('U5.8','C_U5.1',.6),('J_AUX5.3','U9.8',.6),
           ('J_AUX5.3','U5.8',.6),('J_AUX5.3','J_CTL.2',.6),
           ('R_IOUT_PU.1','old_pullup_supply_junction',.25)]
    for src,dst,width in pairs:
        a,b=ep[src],ep[dst]
        if connected(a,b,router.pads,router.tracks,router.vias):continue
        result=search(router,a,b,width,step=.25)
        assert result,('Fanout requires further layout review',src,dst)
        write_route(router,result,'gbuck-output-protection-repair:'+src+':'+dst,a['net'],width)
        assert connected(a,b,router.pads,router.tracks,router.vias)
        routed.append({'from':src,'to':dst,'net':a['net'],'width_mm':width,'layer_runs':result[0],'new_vias_mm':result[1]})
        print(src+' -> '+dst+' connected',flush=True)
    append_history(PATH,m,d,{pcb},'output-protection-ripup-v1',removed={pcb:removed})
    (ROOT/'data/build_manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2))
    (ROOT/'data/output_protection_reroute.json').write_text(json.dumps({'baseline_sha256':before,
        'delivered_sha256':sha(PATH),'removed_IOUT_OC_N_5V_and_thin_top_GND_records':len(removed),
        'routed_pairs':routed,'moved_pullup':{'ref':'R_IOUT_PU','before_mm_deg':old_position,'after_mm_deg':[82.5,23.,0]},
        'schematic_or_component_value_change':False},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
