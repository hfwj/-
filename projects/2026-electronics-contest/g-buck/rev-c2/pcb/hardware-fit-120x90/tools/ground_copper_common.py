"""Recut static ground copper after a clearance-checked signal replacement."""
from shapely import union_all
from shapely.geometry.polygon import orient
from add_ground_copper import ring_path
from pcb_common import *


def recut_fills(router,new_foreign,key):
    cuts={l:[] for l in (1,2)}
    for t in router.tracks:
        if ('LINE',t['id']) in new_foreign:cuts[t['layer']].append(t['geometry'])
    for v in router.vias:
        if ('VIA',v['id']) in new_foreign:
            for l in (1,2):cuts[l].append(v['geometry'])
    # Replacement routes are checked against retained ground at 0.20mm.
    # Recut to that same rule; expanding the cut to the initial pour's 0.30mm
    # preference would erase valid narrow ground necks the router preserved.
    cuts={l:union_all(q).buffer(.205) for l,q in cuts.items()}
    for f in list(router.fills):
        if f['net']!='GND' or cuts[f['layer']].is_empty:continue
        g=f['geometry'].difference(cuts[f['layer']])
        pieces=sorted([p for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' and p.area>.05],key=lambda p:-p.area)
        del router.docs[router.pcb]['FILL',f['id']]
        for n,p in enumerate(pieces):
            p=orient(p,sign=1.);body=copy.deepcopy(f['body'])
            body['path']=[ring_path(p.exterior)]+[ring_path(r) for r in p.interiors]
            fid=f['id'] if n==0 else uuid.uuid5(uuid.NAMESPACE_URL,key+':fill:'+f['id']+':'+str(n)).hex[:16]
            router.docs[router.pcb]['FILL',fid]=body
    router.refresh()
