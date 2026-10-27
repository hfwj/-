"""Dedicated shunt-pad sense branches; no shared power trace outside launches."""
from routing_engine import Router
from pcb_common import *

PAIRS=[('RS_IN.1','U2.8'),('RS_IN.2','U2.1'),('RS_L.1','U4.8'),
       ('RS_L.2','U4.1'),('RS_OUT.1','U3.3'),('RS_OUT.2','U3.4')]

def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);ep={p['ref']+'.'+p['pin']:p for p in router.pads}
    before=sha(PATH);routed=[];pending=[]
    for src,dst in PAIRS:
        key='gbuck-kelvin:'+src+':'+dst
        if ('LINE',uuid.uuid5(uuid.NAMESPACE_URL,key+':main:0').hex[:16]) in d[pcb]:continue
        a,b=ep[src],ep[dst];launch=a['geometry'].buffer(.8)
        extra={layer:[t['geometry'].difference(launch) for t in router.tracks
                      if t['net']==a['net'] and t['layer']==layer]
               +[p['geometry'] for p in router.pads if p['net']==a['net'] and p['pid'] not in (a['pid'],b['pid'])
                  and p['ref'] not in (a['ref'],b['ref']) and layer in p['layers']]
               for layer in (1,2)}
        route=router.route(a,b,key,width=.25,extra=extra,force_branch=True)
        if route:routed.append({'from':src,'to':dst,**route});print(src+' -> '+dst+' dedicated',flush=True)
        else:pending.append({'from':src,'to':dst})
    if routed:
        label='kelvin-branches-'+hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
        append_history(PATH,m,d,{pcb},label)
        previous=json.loads((ROOT/'data/kelvin_routing.json').read_text()) if (ROOT/'data/kelvin_routing.json').exists() else {}
        saved={ (p['from'],p['to']):p for p in previous.get('routed_pairs',[]) }
        saved.update({(p['from'],p['to']):p for p in routed})
        (ROOT/'data/kelvin_routing.json').write_text(json.dumps({'baseline_sha256':previous.get('baseline_sha256',before),
            'delivered_sha256':sha(PATH),'routed_pairs':list(saved.values()),'pending_pairs':pending,
            'launch_zone_expansion_mm':.8,'matched_pair_or_noise_validation':False},ensure_ascii=False,indent=2))
    print(json.dumps({'added_sense_branches':len(routed),'pending':len(pending)}))


if __name__=='__main__':main()
