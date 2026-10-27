"""Route explicit local connections only; leave unverified mechanical endpoints open.

Conservative rectangular pad copper and 0.20 mm clearance. This does not run an
EDA router/DRC and deliberately does not claim a complete routed PCB.
"""
import json,math,uuid
from pcb_common import *

def main():
    manifest=json.loads((ROOT/'data/build_manifest.json').read_text())
    meta,docs,_=read_project(PATH);pcb=manifest['pcb'];o=docs[pcb]
    assert not any(k=='LINE' for k,i in o),'Rebuild the base PCB before rerouting'
    parts,pads,bodies,tracks=copper_geometry(meta,docs,pcb)
    ep={p['ref']+'.'+p['pin']:p for p in pads}
    # Gate drive, bootstrap/decoupling, sense decoupling and local ADC/filter nodes.
    pairs=[('U1.7','RG_H.1'),('RG_H.2','QH.1'),('U1.4','RG_L.1'),('RG_L.2','QL.1'),
           ('QH.1','R_GSH.1'),('QL.1','R_GSL.1'),('U1.8','C_BOOT.1'),('U1.6','C_BOOT.2'),
           ('U1.8','D_BOOT.2'),('U1.5','D_BOOT.1'),('U1.5','C5.1'),('U1.3','C5.2'),
           ('U1.5','C_DRV.1'),('U1.3','C_DRV.2'),('U1.5','C6.1'),('U1.3','C6.2'),
           ('U1.1','R_PWM.2'),('U1.1','R_IN_PD.1'),('U1.2','R_SD_PD.1'),
           ('U2.6','C_U2.1'),('U2.2','C_U2.2'),('U4.6','C_U4.1'),('U4.2','C_U4.2'),
           ('U3.6','C_U3.1'),('U3.2','C_U3.2'),('U5.8','C_U5.1'),('U5.4','C_U5.2'),
           ('U9.8','C_U9.1'),('U9.4','C_U9.2'),('U6.14','C_U6.1'),('U6.7','C_U6.2'),
           ('U7.14','C_U7.1'),('U7.7','C_U7.2'),('U8.14','C_U8.1'),('U8.7','C_U8.2'),
           ('R3.2','C7.1'),('C7.1','D_ADC1.3'),('R6.2','C8.1'),('C8.1','D_ADC3.3'),
           ('R7.2','C9.1'),('C9.1','D_ADC2.3'),('R8.2','C10.1'),('C10.1','D_ADC4.3'),
           ('R_IL_ADC.2','C_IL_ADC.1'),('C_IL_ADC.1','D_ADC5.3'),
           ('R_VINP_ADC.2','C_VINP_ADC.1'),('C_VINP_ADC.1','D_ADC6.3'),('D_ADC6.3','J_MON.1'),
           ('R_VINP_TOP.2','R_VINP_BOT.1'),('R_VINP_BOT.1','R_VINP_ADC.1'),
           ('R_IL_PROT.2','C_IL_PROT.1'),('R_IOUT_PROT.2','C_IOUT_PROT.1'),
           ('R_IOUT_TOP.2','R_IOUT_BOT.1'),('R_IOUT_BOT.1','C_REF_IOUT.1'),
           ('R_SN.2','C_SN.1')]
    width=.25;clearance=.20;routed=[];pending=[]
    board=box(.5,.5,119.5,89.5)
    holes=[Point(x,y).buffer(1.6) for x,y in manifest['mounting_holes_mm']]
    for e1,e2 in pairs:
        a,b=ep[e1],ep[e2];net=a['net'];assert net and net==b['net'],(e1,e2,net,b['net'])
        x,y=a['x'],a['y'];xx,yy=b['x'],b['y']
        candidates=[[(x,y),(xx,yy)],[(x,y),(xx,y),(xx,yy)],[(x,y),(x,yy),(xx,yy)]]
        for d in [.7,1.2,2,3,4]:
            for k in [-1,1]:
                candidates.extend([[(x,y),(x,y+k*d),(xx,y+k*d),(xx,yy)],
                                   [(x,y),(x+k*d,y),(x+k*d,yy),(xx,yy)]])
        candidates.sort(key=lambda points:LineString(points).length)
        found=None
        for points in candidates:
            points=[p for i,p in enumerate(points) if i==0 or p!=points[i-1]]
            if len(points)<2:continue
            copper=LineString(points).buffer(width/2)
            if not board.covers(copper):continue
            if any(copper.distance(g)<clearance-1e-7 for g in holes):continue
            if any(p['net']!=net and 1 in p['layers'] and copper.distance(p['geometry'])<clearance-1e-7 for p in pads):continue
            if any(t['net']!=net and copper.distance(t['geometry'])<clearance-1e-7 for t in tracks):continue
            found=(points,copper);break
        if not found:
            pending.append({'from':e1,'to':e2,'net':net,'reason':'No clear top-layer candidate; needs manual routing/vias'});continue
        points,copper=found
        for n,(s,t) in enumerate(zip(points,points[1:])):
            line={'partitionId':'','groupId':0,'netName':net,'layerId':1,
                  'startX':s[0]/.0254,'startY':s[1]/.0254,'endX':t[0]/.0254,'endY':t[1]/.0254,
                  'width':width/.0254,'locked':False,'zIndex':-1}
            lid=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-local-route:'+e1+':'+e2+':'+str(n)).hex[:16]
            o['LINE',lid]=line
        tracks.append({'net':net,'geometry':copper,'layer':1})
        routed.append({'from':e1,'to':e2,'net':net,'points_mm':points,'width_mm':width})
    append_history(PATH,meta,docs,{pcb},'local-routing-v1')
    result={'status':'PARTIAL_LOCAL_ROUTING','routed_pairs':routed,'pending_local_pairs':pending,
        'trace_width_mm':width,'geometric_clearance_mm':clearance,'routing_complete':False,
        'power_routing':'not_started','kelvin_routing':'not_started; shunt pitch unverified',
        'ground_pour':'not_started','native_DRC':'not_run','manufacturing_release':False}
    (ROOT/'data/local_routing.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    manifest['routing']='partial_local'
    manifest['routed_local_pairs']=len(routed)
    manifest['pending_local_pairs']=len(pending)
    (ROOT/'data/build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({'routed_local_pairs':len(routed),'pending_local_pairs':len(pending),'routing_complete':False}))

if __name__=='__main__':main()
