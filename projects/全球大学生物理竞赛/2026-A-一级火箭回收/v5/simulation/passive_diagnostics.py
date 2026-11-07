"""Unpowered reference arcs and algebraic fuel examples only.

No commanded thrust, fuel state, guidance, landing controller or optimization is
implemented. This is a diagnostic supplement to the scale-analysis manuscript.
"""
from pathlib import Path
import csv
import json
import math
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, minimize_scalar
from atmosphere_1976 import atmosphere, GM_E, R_E, R_AIR, R_ATM, G0, layer_state, BASES, HB, LAPSE

ROOT=Path(__file__).resolve().parents[1]
AREA=math.pi*7**2/4
V0=6000/3.6
GSEA=GM_E/R_E**2


def density_for_rhs(h):
    if h>71000:
        raise ValueError('Numerical RK probe too far above the reference domain.')
    if 0<=h<=70000:return atmosphere(h)['density_kg_m3']
    if h>70000:
        # RK stage probes can slightly overshoot the initial maximum altitude.
        # Continue the same USSA layer smoothly for probes only; accepted output
        # samples remain within geometric 0--70 km.
        H=R_ATM*h/(R_ATM+h)
        i=max(i for i,hb in enumerate(HB[:-1]) if H>=hb)
        t,p=layer_state(*BASES[i],H-HB[i],LAPSE[i])
        return p/(R_AIR*t)
    if h < -1000:raise ValueError('Numerical root probe too far below the surface.')
    # Smooth continuation for internal RK/root probes only. No reported arc
    # continues below r=R_E. This is not a physical underground atmosphere.
    H=R_ATM*h/(R_ATM+h)
    t,p=layer_state(288.15,101325,H,-.0065)
    return p/(R_AIR*t)


def observables(y,mass,cd,air):
    radius=float(np.linalg.norm(y[:2]));er=y[:2]/radius;et=np.array([er[1],-er[0]])
    height=radius-R_E;speed=float(np.linalg.norm(y[2:4]))
    if height < -1e-4 or height>70000+1e-4:raise ValueError('Reported sample outside the physical atmosphere domain.')
    rho=atmosphere(float(np.clip(height,0,70000)))['density_kg_m3'] if air else 0.
    q=.5*rho*speed**2
    return dict(height_m=max(height,0.),arc_range_m=R_E*math.atan2(y[0],y[1]),speed_m_s=speed,
                tangential_velocity_m_s=float(y[2:4]@et),radial_velocity_m_s=float(y[2:4]@er),
                q_Pa=q,drag_N=q*cd*AREA,specific_drag_work_J_kg=float(y[4]),
                log_angular_momentum_attenuation=float(y[5]))


def passive_arc(mass,cd,air=True,max_step=.25,rtol=2e-11):
    if not math.isfinite(mass) or mass<=0 or not math.isfinite(cd) or cd<0:raise ValueError('Invalid mass or Cd.')
    y0=np.array([0.,R_E+70000.,V0,0.,0.,0.])
    def rhs(t,y):
        r=y[:2];v=y[2:4];radius=np.linalg.norm(r);speed=np.linalg.norm(v)
        rho=density_for_rhs(float(radius-R_E)) if air else 0.
        k=.5*rho*cd*AREA/mass
        return np.r_[v,-GM_E*r/radius**3-k*speed*v,k*speed**3,k*speed]
    def ground(t,y):return np.linalg.norm(y[:2])-R_E
    ground.terminal=True;ground.direction=-1
    def rising_q50(t,y):
        rho=density_for_rhs(float(np.linalg.norm(y[:2])-R_E)) if air else 0.
        return .5*rho*float(y[2:4]@y[2:4])-50000
    rising_q50.terminal=False;rising_q50.direction=1
    sol=solve_ivp(rhs,(0,500),y0,method='DOP853',events=[ground,rising_q50],
                  rtol=rtol,atol=1e-8,max_step=max_step,dense_output=True)
    if not sol.success or not len(sol.t_events[0]):raise RuntimeError('Passive diagnostic failed to reach r=R_E.')
    tf=float(sol.t_events[0][0]);end=observables(sol.y_events[0][0],mass,cd,air)
    times=np.r_[np.arange(0,tf,.1),tf]
    profiles=[dict(time_s=float(t),**observables(sol.sol(t),mass,cd,air)) for t in times]
    qvals=np.array([p['q_Pa'] for p in profiles])
    candidates=[(float(qvals[0]),0.),(float(qvals[-1]),tf)]
    for i in range(1,len(times)-1):
        if qvals[i]>qvals[i-1] and qvals[i]>=qvals[i+1]:
            def minus_q(t):return -observables(sol.sol(t),mass,cd,air)['q_Pa']
            opt=minimize_scalar(minus_q,bounds=(times[i-1],times[i+1]),method='bounded',options={'xatol':1e-8})
            candidates.append((-float(opt.fun),float(opt.x)))
    peak_q,peak_t=max(candidates)
    peak=observables(sol.sol(peak_t),mass,cd,air)
    first_q50=None
    if len(sol.t_events[1]):
        tq=float(sol.t_events[1][0]);first_q50=dict(time_s=tq,**observables(sol.sol(tq),mass,cd,air))
    radius=np.linalg.norm(sol.y[:2],axis=0)
    energies=np.sum(sol.y[2:4]**2,axis=0)/2-GM_E/radius
    energy0=V0**2/2-GM_E/(R_E+70000)
    energy_residual=energies-energy0+sol.y[4]
    ell=sol.y[1]*sol.y[2]-sol.y[0]*sol.y[3]
    ell0=(R_E+70000)*V0
    expected_ell=ell0*np.exp(-sol.y[5])
    result=dict(mass_kg=mass,Cd=cd,air_enabled=air,time_to_surface_s=tf,
                surface_arc_range_m=end['arc_range_m'],surface_speed_m_s=end['speed_m_s'],
                surface_tangential_velocity_m_s=end['tangential_velocity_m_s'],
                surface_radial_velocity_m_s=end['radial_velocity_m_s'],
                max_q_Pa=peak_q,max_q_time_s=peak_t,max_q_height_m=peak['height_m'],
                max_q_over_50kPa=peak_q/50000,
                vertical_terminal_reference_sea_m_s=math.sqrt(2*mass*GSEA/(atmosphere(0)['density_kg_m3']*cd*AREA)) if air and cd>0 else None,
                first_q50=first_q50,
                energy_drag_work_max_residual_J_kg=float(np.max(np.abs(energy_residual))),
                angular_momentum_decay_max_relative_residual=float(np.max(np.abs(ell-expected_ell))/ell0))
    return result,profiles


def one_dimensional_reference(w,thrust=2.2e6,mf=130000.):
    ve=320*G0;flow=thrust/ve
    # For constant g, no drag, vertical full thrust, fixed final mass:
    # w = ve*ln(1 + flow*tb/mf) - g*tb.
    def velocity_reduction(tb):return ve*math.log1p(flow*tb/mf)-GSEA*tb
    tstar=(thrust/GSEA-mf)/flow
    max_reduction=velocity_reduction(tstar) if tstar>0 else 0.
    result=dict(prescribed_downward_speed_m_s=w,thrust_N=thrust,final_mass_kg=mf,
                g_constant_m_s2=GSEA,maximum_reduction_in_this_reference_m_s=max_reduction,
                burn_time_at_maximum_s=tstar)
    if w>max_reduction:
        result.update(status='NO_ROOT_IN_THIS_REFERENCE',burn_time_s=None,propellant_kg=None,initial_mass_kg=None,descent_distance_m=None)
    else:
        tb=brentq(lambda t:velocity_reduction(t)-w,0,tstar,xtol=1e-11)
        mp=flow*tb;m0=mf+mp
        distance=w*tb-ve*(tb-mf/flow*math.log(m0/mf))+.5*GSEA*tb**2
        result.update(status='SHORTER_BURN_ROOT',burn_time_s=tb,propellant_kg=mp,initial_mass_kg=m0,descent_distance_m=distance)
    return result


def write_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    data=ROOT/'results/data';logs=ROOT/'results/logs'
    data.mkdir(parents=True,exist_ok=True);logs.mkdir(parents=True,exist_ok=True)
    results=[];all_profiles=[]
    for mass,cd,air in [(130000.,0.,False),(130000.,.5,True),(130000.,1.,True),(200000.,.5,True),(200000.,1.,True)]:
        result,profiles=passive_arc(mass,cd,air)
        key='vacuum_130t' if not air else f'air_{mass/1000:.0f}t_Cd{cd:g}'
        result['case']=key;results.append(result)
        all_profiles += [dict(case=key,**p) for p in profiles]
    flat=[{k:v for k,v in r.items() if k!='first_q50'} for r in results]
    write_csv(data/'passive_cases.csv',flat)
    write_csv(data/'passive_profiles.csv',all_profiles)
    firsts=[dict(case=r['case'],mass_kg=r['mass_kg'],Cd=r['Cd'],**r['first_q50']) for r in results if r['first_q50'] is not None]
    write_csv(data/'first_q50_crossings.csv',firsts)
    ve=320*G0
    fuels=[dict(prescribed_delta_v_T_m_s=dv,propellant_reference_kg=130000*math.expm1(dv/ve),final_mass_assumed_kg=130000,
                interpretation='Conditional rocket-equation conversion only; not an actual demand interval.') for dv in [700.,1100.,1400.]]
    write_csv(data/'conditional_fuel_reference.csv',fuels)
    refs=[one_dimensional_reference(w) for w in [250.,300.,350.,450.]]
    write_csv(data/'coupled_vertical_reference.csv',refs)
    a=2.2e6/131000-GSEA;tb=450/a
    inconsistent=dict(frozen_mass_assumed_kg=131000,available_propellant_if_dry_130t_kg=1000,
        frozen_mass_net_acceleration_m_s2=a,frozen_mass_time_to_reduce_450m_s_s=tb,
        actual_flow_times_that_duration_kg=2.2e6/ve*tb,
        prescribed_delta_v_from_frozen_mass_example_m_s=450+GSEA*tb,
        rocket_reference_propellant_from_that_delta_v_kg=130000*math.expm1((450+GSEA*tb)/ve))
    summary=dict(scope='Unpowered constant-mass/no-wind/nonrotating point-mass references and algebra only. Not real booster trajectories or landing fuel bounds.',
        area_ref_m2=AREA,initial=dict(height_m=70000,speed_m_s=V0,gamma_deg=0),
        atmosphere='USSA1976 0--70 km for reported arcs; smooth continuation outside the two boundaries is only for internal RK/root probes, never reported as flight.',
        cases=results,conditional_fuel_reference=fuels,coupled_vertical_reference=refs,
        frozen_mass_inconsistency=inconsistent)
    (data/'bridge_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    refinements=[]
    for base in results:
        refined,_=passive_arc(base['mass_kg'],base['Cd'],base['air_enabled'],max_step=.125,rtol=3e-12)
        diff={k:abs(base[k]-refined[k]) for k in ['time_to_surface_s','surface_arc_range_m','surface_speed_m_s','max_q_Pa']}
        assert diff['surface_arc_range_m']<.01 and diff['surface_speed_m_s']<.001 and diff['max_q_Pa']<.1
        assert base['energy_drag_work_max_residual_J_kg']<.01
        assert base['angular_momentum_decay_max_relative_residual']<1e-8
        refinements.append(dict(case=base['case'],differences=diff))
    vacuum=results[0]
    predicted_vt=V0*(R_E+70000)/R_E
    assert abs(vacuum['surface_tangential_velocity_m_s']-predicted_vt)<1e-5
    assert refs[-1]['status']=='NO_ROOT_IN_THIS_REFERENCE'
    for r in refs[:-1]:
        assert abs(r['initial_mass_kg']-r['final_mass_kg']-r['propellant_kg'])<1e-6
    checks=dict(status='PASS',refinement_cases=refinements,
        vacuum_tangential_velocity_angular_momentum_prediction_m_s=predicted_vt,
        maximum_energy_work_residual_J_kg=max(r['energy_drag_work_max_residual_J_kg'] for r in results),
        maximum_angular_momentum_decay_relative_residual=max(r['angular_momentum_decay_max_relative_residual'] for r in results),
        scope='Checks apply only to these passive arcs and scalar reference equations, not to a controlled landing or proposed fuel range.')
    (logs/'passive_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
