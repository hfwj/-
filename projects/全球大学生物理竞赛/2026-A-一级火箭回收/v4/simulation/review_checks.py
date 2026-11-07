"""Review arithmetic and simplified 2-D geometry, not a landing solver."""
from pathlib import Path
import csv
import json
import math

ROOT=Path(__file__).resolve().parents[1]
G0=9.80665
WEIGHT=130000*G0
AREA=math.pi*7**2/4


def thrust_budget(q_pa, n_limit, mass_kg=130000., cd=.5):
    aero=q_pa*AREA*cd
    raw=n_limit*mass_kg*G0-aero
    if raw<0:
        return dict(state='INVALID_AERO_BUDGET',aero_force_N=aero,
                    load_based_thrust_budget_N=raw,installed_limited_thrust_N=None)
    return dict(state='VALID_REFERENCE',aero_force_N=aero,
                load_based_thrust_budget_N=raw,installed_limited_thrust_N=min(3.3e6,raw))


def contour(theta_deg, x_cg, z_cg, spacing_m=1., ell_m=32.5, half_span_m=5.):
    """65 m foot-plane-to-top H envelope; cylindrical main body is s=2..65 m.

    Polygon ordering includes side segments and both end caps. Other components
    require their own contours; this is not an actual booster shape model.
    """
    theta=math.radians(theta_deg)
    eb=(math.sin(theta),math.cos(theta))
    ep=(math.cos(theta),-math.sin(theta))
    number=round((65.-2.)/spacing_m)
    if number<1 or abs(number*spacing_m-63.)>1e-9:
        raise ValueError('Spacing must divide the [2,65] m body interval exactly.')
    stations=[2.+i*spacing_m for i in range(number+1)]
    def point(s,r):
        return (x_cg+(s-ell_m)*eb[0]+r*ep[0],z_cg+(s-ell_m)*eb[1]+r*ep[1])
    polygon=[point(s,-3.5) for s in stations]+[point(s,3.5) for s in reversed(stations)]
    feet=[point(0.,r) for r in [-half_span_m,half_span_m]]
    return polygon,feet


def main():
    data=ROOT/'results/data';logs=ROOT/'results/logs'
    data.mkdir(parents=True,exist_ok=True);logs.mkdir(parents=True,exist_ok=True)
    engines=[]
    for n in [1,2,3]:
        hover=WEIGHT/(n*1e6)
        engines.append(dict(active_engines=n,minimum_thrust_N=n*.3e6,maximum_thrust_N=n*1.1e6,
            minimum_TWR_dry_standard_g=n*.3e6/WEIGHT,maximum_TWR_dry_standard_g=n*1.1e6/WEIGHT,
            required_uniform_hover_throttle_dry=hover,
            hover_within_steady_throttle_range=.3<=hover<=1.1,
            downward_thrust_headroom_from_hover_N=WEIGHT-n*.3e6,
            upward_thrust_headroom_from_hover_N=n*1.1e6-WEIGHT))
    scan=[]
    for q in [30000,50000,70000]:
        for n in [3,4,5]:
            scan.append(dict(q_limit_example_Pa=q,n_sum_limit=n,mass_reference_kg=130000,Cd_reference=.5,
                             evaluation='At q=q_limit, not an assumption that all flight points have this q.',
                             **thrust_budget(q,n)))
    for filename,rows in [('engine_count_comparison.csv',engines),('coupled_limit_grid.csv',scan)]:
        with (data/filename).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader();writer.writerows(rows)
    checks=[]
    for theta_deg in [-100,-45,0,2,30,100,170]:
        for spacing in [1.,.5]:
            polygon,feet=contour(theta_deg,0.,40.,spacing)
            theta=math.radians(theta_deg)
            endpoint=2. if math.cos(theta)>=0 else 65.
            exact=40+(endpoint-32.5)*math.cos(theta)-3.5*abs(math.sin(theta))
            error=abs(min(p[1] for p in polygon)-exact)
            assert error<1e-10
            checks.append(dict(theta_deg=theta_deg,spacing_m=spacing,body_clearance_error_m=error))
    poly,feet=contour(0,0,32.5)
    assert min(z for x,z in poly)==2. and min(z for x,z in feet)==0.
    # An overturned body can touch first while both feet remain above the plane.
    bad_body,bad_feet=contour(100,0,8)
    assert min(z for x,z in bad_body)<0 and min(z for x,z in bad_feet)>0
    theta=math.radians(2)
    zcg=32.5*math.cos(theta)+5*math.sin(theta)
    touch_body,touch_feet=contour(2,0,zcg)
    assert abs(min(z for x,z in touch_feet))<1e-12
    assert min(z for x,z in touch_body)>.01
    assert not engines[0]['hover_within_steady_throttle_range']
    assert engines[1]['hover_within_steady_throttle_range'] and engines[2]['hover_within_steady_throttle_range']
    assert thrust_budget(1e6,3)['installed_limited_thrust_N'] is None
    assert thrust_budget(50000,3)['installed_limited_thrust_N']<3.3e6
    assert thrust_budget(50000,4)['installed_limited_thrust_N']==3.3e6
    result=dict(status='PASS',dry_weight_standard_N=WEIGHT,engines=engines,joint_design_cases=len(scan),
        contour_node_count_spacing_1m=len(poly),contour_node_count_spacing_0p5m=len(contour(0,0,32.5,.5)[0]),
        analytic_geometry_cases=checks,
        body_first_example=dict(theta_deg=100,CG_height_m=8,min_body_height_m=min(z for x,z in bad_body),
                                min_foot_height_m=min(z for x,z in bad_feet)),
        scope='Static H geometry and arithmetic only. No continuous collision-time integration, trajectory, real engine optimality, or actual booster clearance was verified.')
    (logs/'review_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
