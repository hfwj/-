from pathlib import Path
import json,csv,math,numpy as np
from audit import ROOT,SOURCE

def summarize():
 d=ROOT/'results/data';audit=json.loads((d/'audit.json').read_text());old=json.loads((SOURCE/'results/data/replay_summary.json').read_text());new=audit['nominal'];r=list(csv.DictReader((d/'independent_trajectory.csv').open()));a={k:np.array([float(x[k]) for x in r]) for k in r[0]};b=np.radians(a['beta_deg']);V=np.hypot(a['vt_m_s'],a['vr_m_s']);incoming=np.degrees(np.arccos(np.clip((-a['vt_m_s']*np.sin(b)-a['vr_m_s']*np.cos(b))/V,-1,1)));high=(a['q_Pa']>=10000)&(a['vr_m_s']<0);low=a['height_m']<=232.5
 z=dict(independent_vs_v8=dict(contact_time_difference_s=new['final']['time_s']-old['actual_end_s'],radial_velocity_difference_m_s=new['final']['vr_m_s']-old['final']['vr_m_s'],mass_difference_kg=new['final']['mass_kg']-old['final']['mass_kg'],range_difference_m=new['final']['range_m']-old['final']['range_m'],q_peak_difference_Pa=new['peaks']['q_Pa']-old['peaks']['q_Pa']),cross_solver_radial_velocity_difference_m_s=abs(audit['rk45']['final']['vr_m_s']-new['final']['vr_m_s']),conditional_attitude=dict(max_incoming_misalignment_if_body_follows_thrust_deg=float(max(incoming[high])),minimum_required_net_gimbal_for_C07_deg=float(max(0,max(incoming[high])-5)),max_thrust_tilt_below_232_5m_deg=float(max(abs(a['beta_deg'][low]))),minimum_required_net_gimbal_for_C08_deg=float(max(0,max(abs(a['beta_deg'][low]))-5))),sensitivity_pass_count=sum(x['M0_subset_pass'] for x in audit['frozen_open_loop_sensitivity']),sensitivity_case_count=len(audit['frozen_open_loop_sensitivity']))
 for name in ['time_s','height_m','vt_m_s','vr_m_s','beta_deg','local_direction_rate_deg_s']:
  z.setdefault('nearest_200m_reference_clearance_sample',{})[name]=float(a[name][np.argmin(abs(a['height_m']-232.5))])
 z['final_if_body_follows_thrust_angular_rate_deg_s']=new['final']['local_direction_rate_deg_s'];(d/'reliability_metrics.json').write_text(json.dumps(z,indent=2))
 rows=[]
 for q in audit['frozen_open_loop_sensitivity']:
  f=q['final'];rows.append(dict(name=q['name'],event=q['event'],M0_subset_pass=q['M0_subset_pass'],end_time_s=f['time_s'],end_height_m=f['height_m'],end_vt_m_s=f['vt_m_s'],end_vr_m_s=f['vr_m_s'],end_usable_kg=f['usable_kg'],peak_q_Pa=q['peaks']['q_Pa'],peak_n_sum=q['peaks']['n_sum'],reference_ship_range_error_m=f['range_m']-new['final']['range_m']))
 with (d/'sensitivity.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
 print(json.dumps(z,indent=2));return z
if __name__=='__main__':summarize()
