"""Add a 2mm spur where the real round precharge pad missed the power trunk."""
from routing_engine import Router
from route_pending import connected
from route_driver_bottom import add_line
from pcb_common import *


def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm'])
    source=next(p for p in router.pads if p['ref']=='R_PRE' and p['pin']=='2')
    target=next(p for p in router.pads if p['ref']=='J_BYP' and p['pin']=='2')
    if connected(source,target,router.pads,router.tracks,router.vias,router.fills):
        print('Precharge terminal already connected.');return
    start=Point(source['x'],source['y']);candidates=[]
    for t in router.tracks:
        if t['net']!='IN_PRE' or t['body']['width']*.0254<2-1e-7 or t['layer'] not in source['layers']:continue
        body=t['body'];line=LineString([(body['startX']*.0254,body['startY']*.0254),
                                      (body['endX']*.0254,body['endY']*.0254)])
        end=line.interpolate(line.project(start));copper=LineString([start,end]).buffer(1.)
        if all(copper.distance(g)>=.2-1e-7 for g in router.obstacles('IN_PRE',t['layer'])):
            candidates.append((start.distance(end),t['layer'],end,t['id']))
    assert candidates,'Power spur requires layout review'
    length,layer,end,tid=min(candidates,key=lambda q:q[0]);before=sha(PATH)
    add_line(d[pcb],'gbuck-precharge-round-pad-spur','IN_PRE',layer,(start.x,start.y),(end.x,end.y),2.)
    append_history(PATH,m,d,{pcb},'precharge-round-pad-spur-v1')
    rm,rd,_=read_project(PATH);_,pads,_,tracks=copper_geometry(rm,rd,pcb)
    assert connected(source,target,pads,tracks,copper_vias(rd,pcb),copper_fills(rd,pcb))
    (ROOT/'data/precharge_terminal_spur.json').write_text(json.dumps({'baseline_sha256':before,
        'delivered_sha256':sha(PATH),'from':'R_PRE.2','to_trunk_id':tid,'net':'IN_PRE','width_mm':2.,
        'layer':layer,'points_mm':[[start.x,start.y],[end.x,end.y]],'length_mm':length,
        'reason':'Native round pad missed the trunk although its former rectangular proxy touched',
        'schematic_or_component_change':False},ensure_ascii=False,indent=2))
    print('Round R_PRE.2 pad connected to the 2mm precharge trunk.')


if __name__=='__main__':main()
