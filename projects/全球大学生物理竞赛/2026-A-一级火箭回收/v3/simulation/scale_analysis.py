"""Order-of-magnitude diagnostics, not a powered landing/fuel optimizer.

Run from any directory. Inputs, derived tables, plots, and conservation checks
are saved relative to this version's root. Vacuum arcs deliberately omit drag,
thrust and Earth rotation; frozen-speed atmosphere tables are not flight paths.
"""
from pathlib import Path
import csv
import json
import math
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/upc-a-v3-matplotlib')
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from atmosphere_1976 import atmosphere, GM_E, R_E, R_AIR, GAMMA, G0

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/data'
FIG=ROOT/'results/figures'
LOG=ROOT/'results/logs'


def csv_out(name, rows):
    with (DATA/name).open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def vacuum_arc(gamma_deg, rtol=1e-11, max_step=1.):
    speed=6000/3.6
    gamma=math.radians(gamma_deg)
    y0=np.array([0.,R_E+70000.,speed*math.cos(gamma),speed*math.sin(gamma)])
    def rhs(t,y):
        r=y[:2]; return np.r_[y[2:],-GM_E*r/np.linalg.norm(r)**3]
    def ground(t,y): return np.linalg.norm(y[:2])-R_E
    ground.terminal=True; ground.direction=-1
    sol=solve_ivp(rhs,(0.,800.),y0,events=ground,method='DOP853',
                  rtol=rtol,atol=1e-8,max_step=max_step,dense_output=True)
    if not sol.success or not len(sol.t_events[0]):raise RuntimeError('Vacuum diagnostic did not reach surface.')
    tf=float(sol.t_events[0][0]);end=sol.y_events[0][0]
    radii=np.linalg.norm(sol.y[:2],axis=0)
    energies=np.sum(sol.y[2:]**2,axis=0)/2-GM_E/radii
    momenta=sol.y[0]*sol.y[3]-sol.y[1]*sol.y[2]
    epsilon=float(np.dot(y0[2:],y0[2:])/2-GM_E/np.linalg.norm(y0[:2]))
    h_ang=float(y0[0]*y0[3]-y0[1]*y0[2])
    semi=-GM_E/(2*epsilon)
    eccentricity=math.sqrt(max(0.,1+2*epsilon*h_ang**2/GM_E**2))
    apogee=semi*(1+eccentricity)-R_E
    result=dict(gamma_deg=gamma_deg,time_to_surface_s=tf,
                surface_arc_range_m=R_E*math.atan2(end[0],end[1]),
                apogee_geometric_m=apogee,surface_speed_m_s=float(np.linalg.norm(end[2:])),
                energy_max_relative_drift=float(np.max(np.abs(energies-epsilon))/abs(epsilon)),
                angular_momentum_scaled_drift=float(np.max(np.abs(momenta-h_ang))/((R_E+70000)*speed)))
    times=np.linspace(0.,tf,601);ys=sol.sol(times)
    profile=[dict(gamma_deg=gamma_deg,time_s=float(t),
                  arc_range_m=float(R_E*math.atan2(y[0],y[1])),
                  height_m=float(np.linalg.norm(y[:2])-R_E)) for t,y in zip(times,ys.T)]
    return result,profile


def main():
    for path in [DATA,FIG,LOG]:path.mkdir(parents=True,exist_ok=True)
    inputs=json.loads((ROOT/'references/nominal_inputs_from_v2.json').read_text())
    n=inputs['nominal'];m_d=inputs['given']['dry_mass_kg'];h0=70000.;v0=6000/3.6
    area=math.pi*7**2/4;g_sea=GM_E/R_E**2;g70=GM_E/(R_E+h0)**2
    delta_phi=GM_E*(1/R_E-1/(R_E+h0));ke=.5*v0**2
    at70=atmosphere(70000.);at0=atmosphere(0.)
    ve=320*G0;beta=m_d/(.5*area)
    t_grav=math.sqrt(2*h0/(GM_E/(R_E+h0/2)**2))
    omega=2*math.pi/(23.9345*3600)
    atmos=[]
    for h in range(0,70001,1000):
        a=atmosphere(h);rho=a['density_kg_m3'];q=.5*rho*v0**2
        row=dict(a)
        row.update(frozen_speed_m_s=v0,frozen_q_Pa=q,
                   frozen_drag_Cd05_N=q*.5*area,
                   frozen_drag_over_dry_weight=q*.5*area/(m_d*a['gravity_m_s2']),
                   velocity_at_q50kPa_m_s=math.sqrt(1e5/rho),
                   Re_diameter_frozen=rho*v0*7/a['dynamic_viscosity_Pa_s'])
        atmos.append(row)
    csv_out('frozen_speed_atmosphere.csv',atmos)
    arcs=[];profiles=[]
    for gamma in [0,15,30,45,60,90]:
        result,profile=vacuum_arc(gamma);arcs.append(result);profiles+=profile
    csv_out('vacuum_ballistic_diagnostics.csv',arcs)
    csv_out('vacuum_profiles.csv',profiles)
    impulses=[]
    for dv in [500.,1000.,v0,2000.]:
        impulses.append(dict(prescribed_engine_delta_v_m_s=dv,Isp_s=320,
                             assumed_final_mass_kg=m_d,propellant_kg=m_d*math.expm1(dv/ve),
                             expended_fraction_of_initial_mass=1-math.exp(-dv/ve)))
    csv_out('rocket_equation_reference.csv',impulses)
    stopping=[];tau=.5+1.1
    for mass in [130000.,160000.,200000.,220000.,250000.]:
        thrust=2.2e6;a=thrust/mass-g_sea;w=100.
        pure=w**2/(2*a) if a>0 else None
        req=w*tau+.5*g_sea*tau**2+(w+g_sea*tau)**2/(2*a)+20 if a>0 else None
        stopping.append(dict(instantaneous_mass_kg=mass,two_engine_max_N=thrust,
            TWR_using_model_sea_gravity=thrust/(mass*g_sea),
            frozen_mass_net_upward_acceleration_m_s2=a,descent_speed_example_m_s=w,
            no_delay_frozen_mass_stop_distance_m=pure,wait_envelope_s=tau,
            delayed_frozen_mass_required_height_m=req))
    csv_out('terminal_thrust_stopping_reference.csv',stopping)
    lam=at70['dynamic_viscosity_Pa_s']/at70['pressure_Pa']*math.sqrt(math.pi*R_AIR*at70['temperature_K']/2)
    rho0=at0['density_kg_m3'];side_area=65*7;wind=10.
    per_side_coeff=.5*rho0*wind**2*side_area
    n_cap=(3.3e6+50000*.5*area)/(m_d*G0)
    S=dict(initial_speed_m_s=v0,area_ref_m2=area,side_area_m2=side_area,side_to_base_area_ratio=side_area/area,
           specific_initial_kinetic_energy_J_kg=ke,specific_gravity_potential_drop_J_kg=delta_phi,
           gravity_to_initial_kinetic_ratio=delta_phi/ke,
           total_initial_dry_mass_mechanical_energy_above_surface_J=m_d*(ke+delta_phi),
           equivalent_vacuum_surface_speed_m_s=math.sqrt(v0**2+2*delta_phi),
           gravity_sea_model_m_s2=g_sea,gravity_70km_m_s2=g70,
           gravity_fraction_change_sea_to_70km=1-g70/g_sea,
           constant_sea_gravity_potential_overestimate_fraction=g_sea*h0/delta_phi-1,
           h0_over_earth_radius=h0/R_E,gravity_fall_time_scale_s=t_grav,
           gravity_velocity_scale_over_fall_time_m_s=(GM_E/(R_E+h0/2)**2)*t_grav,
           initial_curvature_acceleration_m_s2=v0**2/(R_E+h0),
           curvature_over_initial_gravity=v0**2/((R_E+h0)*g70),
           vacuum_gamma0_range_m=arcs[0]['surface_arc_range_m'],vacuum_gamma0_time_s=arcs[0]['time_to_surface_s'],
           tangent_plane_surface_sag_at_vacuum_gamma0_range_m=arcs[0]['surface_arc_range_m']**2/(2*R_E),
           rotation_rate_rad_s=omega,coriolis_acceleration_bound_initial_m_s2=2*omega*v0,
           coriolis_acceleration_bound_over_initial_gravity=2*omega*v0/g70,
           frozen_coriolis_drift_scale_over_vacuum_flight_m=.5*2*omega*v0*arcs[0]['time_to_surface_s']**2,
           equatorial_centrifugal_acceleration_m_s2=omega**2*R_E,
           initial_drag_N=.5*at70['density_kg_m3']*v0**2*.5*area,
           initial_drag_over_dry_gravity_weight=(.5*at70['density_kg_m3']*v0**2*.5*area)/(m_d*g70),
           ballistic_coefficient_Cd05_dry_kg_m2=beta,
           initial_Mach=v0/at70['sound_speed_m_s'],initial_Re_diameter=atmos[-1]['Re_diameter_frozen'],
           viscosity_based_mean_free_path_70km_m=lam,initial_Kn_diameter=lam/7,
           exhaust_equivalent_velocity_m_s=ve,initial_speed_over_exhaust_velocity=v0/ve,
           three_engine_max_N=3.3e6,two_engine_max_N=2.2e6,
           two_engine_hover_mass_model_sea_kg=2.2e6/g_sea,
           three_engine_hover_mass_model_sea_kg=3.3e6/g_sea,
           single_engine_max_mass_flow_kg_s=1.1e6/ve,two_engine_max_mass_flow_kg_s=2.2e6/ve,
           reference_50t_burn_time_two_engine_max_s=50000/(2.2e6/ve),
           gravity_velocity_scale_over_reference_burn_m_s=g_sea*50000/(2.2e6/ve),
           sea_nozzle_backpressure_loss_per_m2_N=101325,
           sea_nozzle_loss_per_m2_relative_to_1MN=.101325,
           ideal_perfect_gas_stagnation_temperature_K=at70['temperature_K']+v0**2/(2*(GAMMA/(GAMMA-1)*R_AIR)),
           body_length_over_initial_height=65/h0,CG_foot_lever_over_200m=32.5/200,
           foot_rotation_speed_at_omega05_m_s=32.5*math.radians(.5),
           foot_rotation_speed_over_horizontal_tolerance=32.5*math.radians(.5)/.5,
           CG_base_horizontal_offset_at_tilt2_m=32.5*math.sin(math.radians(2)),
           foot_height_difference_at_tilt2_m=10*math.sin(math.radians(2)),
           wind_speed_ratio_initial=wind/v0,terminal_relative_wind_angle_at_descent2_deg=math.degrees(math.atan(10/2)),
           sea_crosswind_side_force_per_unit_Cside_N=per_side_coeff,
           sea_crosswind_drift_20s_per_unit_Cside_m=.5*per_side_coeff/m_d*20**2,
           illustrative_uniform_rod_inertia_dry_kg_m2=m_d*65**2/12,
           pitch_acceleration_at_q50kPa_Cm001_rad_s2=50000*area*65*.01/(m_d*65**2/12),
           geometric_closed_cylinder_displaced_volume_m3=area*65,
           sea_buoyancy_over_dry_weight_closed_cylinder_proxy=rho0*area*65/m_d,
           max_n_sum_given_q50_Cd05_T3p3_dry=n_cap,
           max_n_sum_given_q50_Cd10_T3p3_dry=(3.3e6+50000*area)/(m_d*G0))
    S['pitch_time_to_omega05_at_Cm001_s']=math.radians(.5)/S['pitch_acceleration_at_q50kPa_Cm001_rad_s2']
    metrics=[dict(metric=k,value=v) for k,v in S.items()]
    csv_out('scale_metrics.csv',metrics)
    (DATA/'scale_summary.json').write_text(json.dumps(dict(
        classification='D: calculations from given/reference/H inputs; not a recovered-booster flight solution.',
        nominal_inputs=inputs,scales=S,vacuum_diagnostics=arcs,rocket_reference=impulses,terminal_reference=stopping,
        frozen_speed_diagnostic_warning='Velocity held at 1666.667 m/s at all altitudes only to compare force scales; not an actual descent.',
        interpretation_notes=[
            '130 t is a dry-mass limiting comparison, not a feasible powered state carrying fuel.',
            'Vacuum arcs omit atmosphere, thrust and Earth rotation at every height, including above 70 km.',
            'Coriolis drift is a frozen-acceleration scale, not an actual error prediction or rigorous bound.',
            'Cside and Cm cases are coefficient normalizations and uniform-rod inertia is an H approximation.',
            'The n_sum maximum calculation assumes drag only, zero lift/side force, q<=50 kPa and m>=130 t.',
            'Nozzle correction is per square meter of an unspecified exit area, not an inferred real engine area.']
    ),ensure_ascii=False,indent=2)+'\n')
    refined,_=vacuum_arc(0,rtol=3e-13,max_step=.5)
    log=dict(status='PASS',checks=dict(
        max_vacuum_energy_relative_drift=max(r['energy_max_relative_drift'] for r in arcs),
        max_scaled_angular_momentum_drift=max(r['angular_momentum_scaled_drift'] for r in arcs),
        max_surface_speed_error_against_energy_m_s=max(abs(r['surface_speed_m_s']-S['equivalent_vacuum_surface_speed_m_s']) for r in arcs),
        refined_gamma0_time_difference_s=abs(refined['time_to_surface_s']-arcs[0]['time_to_surface_s']),
        refined_gamma0_range_difference_m=abs(refined['surface_arc_range_m']-arcs[0]['surface_arc_range_m'])),
        scope='Conservation and numerical refinement of vacuum diagnostics only; no powered descent, actual drag calibration, heat safety, or fuel result.')
    assert log['checks']['max_vacuum_energy_relative_drift']<1e-8
    assert log['checks']['max_surface_speed_error_against_energy_m_s']<1e-4
    assert log['checks']['refined_gamma0_range_difference_m']<.1
    (LOG/'numerical_checks.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
    font_path=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if not font_path.exists():
        raise RuntimeError('Install Noto CJK fonts or set font_path to an available CJK font before making Chinese plots.')
    font_manager.fontManager.addfont(str(font_path))
    font_family=font_manager.FontProperties(fname=str(font_path)).get_name()
    plt.rcParams.update({'font.family':font_family,'axes.unicode_minus':False,'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(7.1,2.7),layout='constrained')
    for gamma in [0,30,60,90]:
        part=[p for p in profiles if p['gamma_deg']==gamma]
        ax.plot([p['arc_range_m']/1000 for p in part],[p['height_m']/1000 for p in part],label=f'γ0={gamma}°')
    ax.set(xlabel='球面航程 / km',ylabel='几何高度 / km',title='真空无推力诊断：只展示初始方向与曲率影响')
    ax.axhline(70,color='grey',lw=.8,ls=':');ax.legend(ncol=4,fontsize=8);ax.grid(alpha=.2)
    for ext in ['png','pdf']:fig.savefig(FIG/f'vacuum_arcs.{ext}',dpi=190)
    plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.7),layout='constrained')
    heights=[r['h_geometric_m']/1000 for r in atmos]
    axs[0].semilogx([r['frozen_drag_over_dry_weight'] for r in atmos],heights,color='#087e8b')
    axs[0].axvline(1,color='grey',ls='--',lw=.8);axs[0].set(xlabel='阻力 / 干态重力（Cd=0.5）',ylabel='几何高度 / km',title='冻结V=1666.7 m/s；不是轨迹')
    axs[1].semilogx([r['velocity_at_q50kPa_m_s'] for r in atmos],heights,color='#b5672f')
    axs[1].axvline(v0,color='grey',ls='--',lw=.8)
    axs[1].set(xlabel='q=50 kPa允许速度 / m/s',title='由密度反推的速度边界');axs[1].set_xlim(200,40000)
    for ax in axs:ax.grid(alpha=.2)
    for ext in ['png','pdf']:fig.savefig(FIG/f'atmosphere_force_scales.{ext}',dpi=190)
    plt.close(fig)
    print(json.dumps(dict(scales=S,vacuum=arcs,terminal=stopping,checks=log),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
