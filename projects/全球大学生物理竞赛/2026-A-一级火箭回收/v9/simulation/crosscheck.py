"""Confirm selected sensitivity outcomes with a different integrator."""
from audit import ROOT,SOURCE,trajectory
import json,numpy as np
if __name__=='__main__':
 p=dict(np.load(SOURCE/'results/data/controls_N320.npz'));old=json.loads((ROOT/'results/data/audit.json').read_text());out=[]
 for name,kw in [('Cd_minus10pct',dict(cd=.45)),('Isp_minus1pct',dict(isp=316.8)),('initial_vt_minus1m_s',dict(dv_t=-1))]:
  s,_=trajectory(p,method='RK45',step=.1,**kw);a=next(z for z in old['frozen_open_loop_sensitivity'] if z['name']==name);assert s['event']==a['event'];err=max(abs(s['final'][k]-a['final'][k]) for k in ['height_m','vt_m_s','vr_m_s']);assert err<.01
  out.append(dict(name=name,final_max_height_or_velocity_absolute_difference=err,event=s['event'],M0_subset_pass=s['M0_subset_pass']));print(out[-1],flush=True)
 (ROOT/'results/data/sensitivity_crosscheck.json').write_text(json.dumps(out,indent=2))
