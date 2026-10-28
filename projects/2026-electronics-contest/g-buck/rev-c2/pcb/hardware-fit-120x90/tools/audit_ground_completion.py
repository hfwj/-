"""Compare a saved checkpoint and bracket round-pad connectivity conservatively."""
import argparse,itertools
from pcb_common import *


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);args=parser.parse_args()
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb']
    bm,bd,_=read_project(args.baseline);m,d,_=read_project(PATH)
    assert m==bm and set(d)==set(bd)
    for u in bd:
        if u!=pcb:assert d[u]==bd[u],('Changed source or library document',u)
    for key,value in bd[pcb].items():
        if key[0] not in ('LINE','VIA','FILL'):assert d[pcb].get(key)==value,('Changed component or pad association',key)
    removed=[k for k in bd[pcb] if k not in d[pcb]]
    changed=[k for k in bd[pcb] if k in d[pcb] and bd[pcb][k]!=d[pcb][k]]
    added=[k for k in d[pcb] if k not in bd[pcb]]
    assert all(k[0] in ('LINE','VIA','FILL') for k in removed+changed+added)
    _,pads,_,tracks=copper_geometry(m,d,pcb);vias=copper_vias(d,pcb);fills=copper_fills(d,pcb)
    pernet=collections.defaultdict(list)
    for p in pads:
        if not p['net']:continue
        g=p['geometry']
        # Clearance uses an OUTER ellipse proxy. Contact must still be present
        # with the INNER proxy, so approximation cannot create a false join.
        if p['body']['defaultPad']['padType']=='ELLIPSE':
            factor=math.cos(math.pi/128)
            g=affinity.scale(g,factor,factor,origin=(p['x'],p['y']))
        pernet[p['net']].append((g,set(p['layers']),p['ref']+'.'+p['pin']))
    for t in tracks:pernet[t['net']].append((t['geometry'],{t['layer']},'trace:'+t['id']))
    for v in vias:pernet[v['net']].append((v['geometry'],{1,2},'via:'+v['id']))
    for f in fills:pernet[f['net']].append((f['geometry'],{f['layer']},'fill:'+f['id']))
    incomplete=[];orphans=[]
    for net,nodes in pernet.items():
        parent=list(range(len(nodes)))
        def find(i):
            while i!=parent[i]:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for i,j in itertools.combinations(range(len(nodes)),2):
            if nodes[i][1]&nodes[j][1] and nodes[i][0].distance(nodes[j][0])<1e-8:parent[find(i)]=find(j)
        sets=collections.defaultdict(list)
        for i,(_,_,name) in enumerate(nodes):sets[find(i)].append(name)
        component_sets=[v for v in sets.values() if any(not n.startswith(('trace:','via:','fill:')) for n in v)]
        if len(component_sets)>1:incomplete.append(net)
        for names in sets.values():
            if all(n.startswith(('trace:','via:','fill:')) for n in names):orphans.append({'net':net,'primitives':names})
    assert not incomplete and not orphans,(incomplete,orphans)
    verification=json.loads((ROOT/'data/verification.json').read_text())
    assert verification['status']=='PASS_STATIC_REVIEW_ONLY' and verification['checks']['routing_complete']
    assert verification['checks']['delivered_sha256']==sha(PATH)
    gates=json.loads((ROOT/'data/ground_gate_bundles.json').read_text())
    affected=sorted({line['net'] for c in gates['changes'] for line in c['removed_signal_lines']})
    report={'status':'PASS_GROUND_AND_ALL_NET_CONTACT_AUDIT','comparison_commit':'ea19975484126b024eb23974dcb06828404c4aed',
        'baseline_sha256':sha(args.baseline),'delivered_sha256':sha(PATH),
        'schematic_and_library_documents_unchanged':True,'all_component_positions_values_packages_unchanged':True,
        'pad_and_net_associations_unchanged':True,'removed_native_records':dict(collections.Counter(k[0] for k in removed)),
        'changed_native_records':dict(collections.Counter(k[0] for k in changed)),
        'added_native_records':dict(collections.Counter(k[0] for k in added)),
        'added_vias_by_net':dict(collections.Counter(d[pcb][k]['netName'] for k in added if k[0]=='VIA')),
        'locally_rerouted_signal_nets':affected,'connected_networks':len(pernet),
        'inscribed_ellipse_contact_graph_complete':True,'inner_contact_tolerance_mm':1e-8,
        'orphan_copper_groups':orphans,'unfinished_networks':incomplete,
        'native_desktop_open':'not_run','native_ERC':'not_run','native_DRC':'not_run','manufacturing_release':False}
    (ROOT/'data/ground_completion_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
