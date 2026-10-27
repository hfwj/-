"""Re-route the existing VIN-divider branch around the relocated pull-up."""
from routing_engine import Router
from route_pending import find_path
from route_driver_bottom import add_line
from pcb_common import *

def main():
    mf=json.loads((ROOT/'data/build_manifest.json').read_text());pcb=mf['pcb'];m,d,_=read_project(PATH)
    router=Router(m,d,pcb,mf['mounting_holes_mm']);lid='64de865500575c8c'
    line=d[pcb]['LINE',lid];assert line['netName']=='VIN' and line['layerId']==1
    a={'x':line['startX']*.0254,'y':line['startY']*.0254}
    b={'x':line['endX']*.0254,'y':line['endY']*.0254}
    g=LineString([(a['x'],a['y']),(b['x'],b['y'])]).buffer(.125)
    if all(g.distance(h)>=.2-1e-7 for h in router.obstacles('VIN',1)):
        print('VIN-divider branch clearance already valid.');return
    old=[a,b];points=find_path(a,b,router.obstacles('VIN',1),width=.25)
    assert points
    before=sha(PATH);line.update(endX=points[1][0]/.0254,endY=points[1][1]/.0254)
    for n,(s,t) in enumerate(zip(points[1:],points[2:])):add_line(d[pcb],'gbuck-vin-divider-pullup-clearance:'+str(n),'VIN',1,s,t,.25)
    append_history(PATH,m,d,{pcb},'vin-divider-clearance-repair-v1')
    (ROOT/'data/vin_branch_clearance_repair.json').write_text(json.dumps({'baseline_sha256':before,
        'delivered_sha256':sha(PATH),'original_segment_mm':old,'replacement_points_mm':points},ensure_ascii=False,indent=2))
    print('VIN-divider branch re-routed around R_IOUT_PU.')


if __name__=='__main__':main()
