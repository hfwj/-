"""Kinematic/authority diagnostics, not a certified rigid-body or contact simulation."""
from pathlib import Path
import numpy as np,math,json,csv
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent
ELL=32.5;B=5.;A=3.5;LENGTH=65.

def axes(theta):return np.array([math.sin(theta),math.cos(theta)]),np.array([math.cos(theta),-math.sin(theta)])
def geometry(cg,theta):
 eb,ep=axes(theta);feet=np.array([cg-ELL*eb+sgn*B*ep for sgn in [-1,1]])
 # Closed 1 m axial polygon; actual nozzle/leg protrusions remain unknown.
 left=[cg+(s-ELL)*eb-A*ep for s in np.arange(2,66)]
 right=[cg+(s-ELL)*eb+A*ep for s in np.arange(65,1,-1)]
 return feet,np.array(left+right+[left[0]])
def feet_velocity(vcg,theta,omega):
 eb,ep=axes(theta)
 return np.array([vcg-ELL*omega*ep-sgn*B*omega*eb for sgn in [-1,1]])
def minimum_clearance(cg_height,theta):return cg_height-ELL*math.cos(theta)-B*abs(math.sin(theta))
def body_min_at_foot_contact(theta):
 h=ELL*math.cos(theta)+B*abs(math.sin(theta))
 return float(min(geometry(np.array([0.,h]),theta)[1][:,1]))

def segment_sphere_clearance(p,q,radius):
 d=q-p;dd=float(d@d);lam=float(np.clip(-float(p@d)/dd,0,1)) if dd else 0.
 return float(np.linalg.norm(p+lam*d)-radius)

def run():
 rows=list(csv.DictReader((PROJECT/'v9/results/data/independent_trajectory.csv').open()));v={k:np.array([float(x[k]) for x in rows]) for k in rows[0]};t=v['time_s'];beta=v['beta_deg'];chi=np.degrees(np.arctan2(-v['vt_m_s'],-v['vr_m_s']))
 high=(v['q_Pa']>=10000)&(v['vr_m_s']<0);low=v['height_m']<=232.5
 # Unwrapped candidate angles remain in [-90,90]; interval intersection is valid.
 lo=np.full(len(t),-180.);hi=np.full(len(t),180.)
 lo[high]=np.maximum(lo[high],chi[high]-5);hi[high]=np.minimum(hi[high],chi[high]+5)
 lo[low]=np.maximum(lo[low],-5);hi[low]=np.minimum(hi[low],5)
 # Last sample is CG reference end, not a true touchdown event.
 lo[-1]=max(lo[-1],-2);hi[-1]=min(hi[-1],2)
 conflict=lo>hi
 delta=np.maximum.reduce([np.zeros(len(t)),lo-beta,beta-hi]);delta[conflict]=np.inf
 i=int(np.argmax(delta));finite_deg=float(np.max(delta))
 bounds=[]
 for limit in [3,5,10,15,20,25,30]:
  bad=(delta>limit+1e-8);duration=float(np.trapezoid(bad.astype(float),t))
  bounds.append(dict(assumed_net_deflection_limit_deg=limit,sampled_angle_necessary_condition_pass=bool(not bad.any()),approximate_incompatible_duration_s=duration))
 out=dict(full_M1_status='NOT_VERIFIED',angle_only_necessary_condition='no torque/rate/attitude trajectory guarantee',attitude_interval_conflict_sample_count=int(conflict.sum()),minimum_required_peak_relative_deflection_deg=finite_deg,binding_sample={k:float(v[k][i]) for k in ['time_s','height_m','q_Pa','beta_deg']},binding_incoming_direction_deg=float(chi[i]),deflection_scan=bounds,near_ground_required_relative_deflection_deg=float(max(np.maximum(abs(beta[low])-5,0))))
 # Conditional thrust moment at the angle-conflict witness. Engine lever is H.
 control=dict(np.load(PROJECT/'v8/results/data/controls_N320.npz'));tg=np.linspace(float(control['toff'])+6.6,float(control['tf']),int(control['N'])+1);thrust=2e6*np.interp(t[i],tg,control['U2'][0]);D=v['q_Pa'][i]*.5*math.pi*49/4
 out['binding_moment_surrogate']=dict(thrust_N=float(thrust),assumed_engine_axial_lever_m=ELL,required_relative_deflection_deg=finite_deg,thrust_moment_N_m=float(-ELL*thrust*math.sin(math.radians(finite_deg))),aero_drag_force_N=float(D),status='illustration only: real engine lever, aerodynamic moment, mass properties unknown')
 # Dry uniform solid-cylinder surrogate ONLY; not a flight mass property.
 inertia=130000*(65**2+3*3.5**2)/12;out['uniform_dry_cylinder_surrogate_inertia_kg_m2']=inertia
 out['minimum_bang_bang_coast_torque_90deg_in_5s_N_m']=4*inertia*(math.pi/2)/25
 geo=[]
 for deg in [0,2,5,20,45,85,100,120]:
  th=math.radians(deg);h=ELL*math.cos(th)+B*abs(math.sin(th));geo.append(dict(theta_deg=deg,foot_height_difference_m=2*B*abs(math.sin(th)),cg_height_at_lowest_foot_contact_m=h,reference_height_difference_m=h-ELL,body_min_clearance_at_foot_contact_m=body_min_at_foot_contact(th),body_clears_at_foot_contact=bool(body_min_at_foot_contact(th)>=.01)))
 out['geometry_examples']=geo
 vel=[]
 for rate in [.5,4.9]:
  z=feet_velocity(np.array([0.,-1.]),0,math.radians(rate));vel.append(dict(theta_deg=0,omega_deg_s=rate,foot_vx_m_s=z[:,0].tolist(),foot_vz_m_s=z[:,1].tolist(),horizontal_reference_limit_pass=bool(np.max(abs(z[:,0]))<=.5)))
 out['conditional_foot_velocity_examples']=vel
 # Conditional engine shutdown tail; no off-command delay is assumed here.
 nominal=json.loads((PROJECT/'v8/results/data/replay_summary.json').read_text());u0=nominal['final']['pair_actual_throttle'];integral_u=.5*u0*u0+.005 if u0>=.1 else .1*u0
 out['conditional_shutdown_tail']=dict(initial_per_engine_throttle=u0,total_impulse_N_s=2e6*integral_u,propellant_kg=2e6*integral_u/(320*9.80665),assumptions='same response as v8, immediate off command, two engines; no extra off delay or plume/ground effect')
 out['upright_static_tip_angle_deg']=math.degrees(math.atan2(B,ELL))
 # Energy-only bound, no thrust at contact, no flex/friction/leg model.
 mass=131457.6045045;tip=mass*9.80665*(math.hypot(ELL,B)-ELL);energy=.5*mass*(1**2+.5**2);out['energy_only_contact_screen']=dict(mass_kg=mass,vertical_kinetic_at_1m_s_J=.5*mass,horizontal_kinetic_at_point5m_s_J=.5*mass*.5**2,rigid_pivot_tip_barrier_J=tip,total_translation_energy_J=energy,energy_barrier_pass=bool(energy<tip),status='A limited energy screen only for zero thrust, zero initial angular rate, no external work, rigid pivot/no sliding and upright initial body; not C18 verification')
 # Required mean total support force during stroke, assuming no engine thrust.
 out['energy_absorption_stroke_scan']=[dict(assumed_stroke_m=s,vertical_initial_speed_m_s=w,minimum_mean_total_support_N=mass*(9.80665+w*w/(2*s)),mean_support_over_weight=1+w*w/(2*s*9.80665)) for s in [.2,.5,1.] for w in [1.,2.]]
 (ROOT/'results/data/diagnostics.json').write_text(json.dumps(out,indent=2))
 with (ROOT/'results/data/deflection_scan.csv').open('w') as f:
  ww=csv.DictWriter(f,fieldnames=bounds[0],lineterminator='\n');ww.writeheader();ww.writerows(bounds)
 return out

def verify():
 rng=np.random.default_rng(20261107);clear_error=vel_error=0.
 for theta in np.linspace(-math.radians(85),math.radians(85),171):
  feet,body=geometry(np.array([1.,100.]),theta);clear_error=max(clear_error,abs(min(feet[:,1])-minimum_clearance(100,theta)))
  expected=2*math.cos(theta)+(B-A)*abs(math.sin(theta));assert abs(body_min_at_foot_contact(theta)-expected)<1e-12
 for _ in range(100):
  th=rng.uniform(-1.4,1.4);w=rng.uniform(-.2,.2);cg=rng.normal(size=2);v=rng.normal(size=2);dt=1e-5
  fd=(geometry(cg+dt*v,th+dt*w)[0]-geometry(cg-dt*v,th-dt*w)[0])/(2*dt);vel_error=max(vel_error,float(np.max(abs(fd-feet_velocity(v,th,w)))))
 # Continuous event: a tilted model is lowered vertically; compare to analytic event.
 th=math.radians(5);height0=40;speed=2
 tf=brentq(lambda tt:minimum_clearance(height0-speed*tt,th),0,10)
 expected=(height0-ELL*math.cos(th)-B*abs(math.sin(th)))/speed
 assert abs(tf-expected)<1e-10 and clear_error<1e-12 and vel_error<1e-7
 # A spherical sea can intersect a segment while both vertices are outside.
 radius=6371000.;p=np.array([-1000.,radius-.01]);q=np.array([1000.,radius-.01]);sphere=segment_sphere_clearance(p,q,radius)
 assert np.linalg.norm(p)>radius and np.linalg.norm(q)>radius and sphere<0
 # Inverted cylinder strikes before feet: geometric failure is explicitly caught.
 assert body_min_at_foot_contact(math.radians(120))<0
 return dict(clearance_max_absolute_error_m=clear_error,foot_velocity_finite_difference_max_error_m_s=vel_error,tilted_contact_event_error_s=abs(tf-expected),inverted_body_collision_detected=True,spherical_sea_segment_interior_collision_detected=True,spherical_sea_segment_minimum_clearance_m=sphere)
if __name__=='__main__':
 checks=verify();(ROOT/'results/logs/geometry_checks.json').write_text(json.dumps(checks,indent=2));z=run();print(json.dumps(dict(checks=checks,summary=z),indent=2))
