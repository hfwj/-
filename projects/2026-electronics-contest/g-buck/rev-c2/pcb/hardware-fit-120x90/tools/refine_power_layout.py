"""Place the freewheel diode beside QL and relocate the two DNP snubber parts."""
from pcb_common import *
from route_pending import find_path
from route_driver_bottom import add_line

POSITIONS={'D_FREE':(80.7,65.9,270),'R_SN':(88.,68.5,90),'C_SN':(91.,68.5,90)}

def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    parts,pads,bodies,tracks=copper_geometry(m,d,pcb)
    if all(abs(parts[r][1]['x']*.0254-p[0])<1e-6 and abs(parts[r][1]['y']*.0254-p[1])<1e-6
           and parts[r][1]['angle']==p[2] for r,p in POSITIONS.items()):
        print('Power layout refinement already applied.');return
    before=sha(PATH);changes=[]
    for ref,(x,y,angle) in POSITIONS.items():
        cid,c,attrs_=parts[ref];old=[c['x']*.0254,c['y']*.0254,c['angle']]
        dx,dy=x/.0254-c['x'],y/.0254-c['y']
        c.update(x=x/.0254,y=y/.0254,angle=angle)
        for (k,_),a in d[pcb].items():
            if k=='ATTR' and a.get('parentId')==cid:
                if a.get('x') is not None:a['x']+=dx
                if a.get('y') is not None:a['y']+=dy
        mf['parts'][ref].update(x=x,y=y,angle=angle)
        changes.append({'ref':ref,'before_mm_deg':old,'after_mm_deg':[x,y,angle]})
    removed=[key for key,b in d[pcb].items() if key[0]=='LINE' and b['netName']=='SN_MID']
    for key in removed:del d[pcb][key]
    _,pads,bodies,tracks=copper_geometry(m,d,pcb);ep={p['ref']+'.'+p['pin']:p for p in pads}
    a,b=ep['R_SN.2'],ep['C_SN.1'];net=a['net'];assert net==b['net']=='SN_MID'
    obstacles=[p['geometry'] for p in pads if p['net']!=net and 1 in p['layers']]
    obstacles += [t['geometry'] for t in tracks if t['net']!=net and t['layer']==1]
    obstacles += [v['geometry'] for v in copper_vias(d,pcb) if v['net']!=net]
    points=find_path(a,b,obstacles)
    assert points
    for n,(s,t) in enumerate(zip(points,points[1:])):add_line(d[pcb],'gbuck-relocated-snubber:'+str(n),net,1,s,t,.25)
    append_history(PATH,m,d,{pcb},'power-layout-diode-adjacent-v1',removed={pcb:removed})
    _,rd,_=read_project(PATH)
    assert all(key not in rd[pcb] for key in removed)
    (ROOT/'data/build_manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2))
    (ROOT/'data/power_layout_refinement.json').write_text(json.dumps({'baseline_sha256':before,
        'delivered_sha256':sha(PATH),'component_changes':changes,'removed_snubber_lines':len(removed),
        'replacement_snubber_points_mm':points,'schematic_or_BOM_change':False},ensure_ascii=False,indent=2))
    print(json.dumps({'moved_parts':list(POSITIONS),'deleted_old_snubber_lines':len(removed)}))


if __name__=='__main__':main()
