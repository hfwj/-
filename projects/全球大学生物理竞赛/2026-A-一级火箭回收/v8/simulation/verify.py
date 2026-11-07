"""Independent SI/Cartesian replays and atmosphere/grid checks; no M1 certification."""
from pathlib import Path
import json,csv,numpy as np,casadi as ca
from physics import density
from atmosphere_1976 import atmosphere
from replay_candidate import replay
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 z=ca.MX.sym('z');rho=ca.Function('rho',[z],[density(z/1000)])
 hs=np.unique(np.r_[np.linspace(0,70000,1001),*[6356766*h/(6356766-h)+np.array([-.001,0,.001]) for h in [11000,20000,32000,47000,51000]]])
 err=max(abs(float(rho(h))/atmosphere(float(h))['density_kg_m3']-1) for h in hs)
 assert err<1e-9
 out=ROOT/'results/data';checks={'density_max_relative_error':err,'replays':[]}
 for n,step in [(160,.1),(320,.1),(320,.05)]:
  summary,rows=replay(out/f'controls_N{n}.npz',step)
  assert summary['M0_subset_pass'],summary
  checks['replays'].append({'nodes':n,'max_step_s':step,'summary':summary})
  print(n,step,summary['initial_propellant_kg'],summary['actual_end_s'],summary['final']['vr_m_s'],flush=True)
 a,b,c=[x['summary'] for x in checks['replays']]
 checks['grid_fuel_relative_difference']=abs(b['initial_propellant_kg']/a['initial_propellant_kg']-1)
 checks['grid_terminal_speed_difference_m_s']=abs(b['final']['speed_m_s']-a['final']['speed_m_s'])
 checks['replay_halving_terminal_speed_difference_m_s']=abs(c['final']['speed_m_s']-b['final']['speed_m_s'])
 assert checks['grid_fuel_relative_difference']<.005
 assert checks['grid_terminal_speed_difference_m_s']<.02
 assert checks['replay_halving_terminal_speed_difference_m_s']<.001
 (out/'verification.json').write_text(json.dumps(checks,indent=2))
 (out/'replay_summary.json').write_text(json.dumps(c,indent=2))
 with (out/'candidate_trajectory.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n");w.writeheader();w.writerows(rows)
 print('PASS: numerical checks only; full v4 NOT_VERIFIED',flush=True)
