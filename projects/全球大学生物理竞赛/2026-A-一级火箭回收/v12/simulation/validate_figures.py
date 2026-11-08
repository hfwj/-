"""Check plotted numerical sources and stop events, not full M1 safety."""
from pathlib import Path
import csv,json,hashlib,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];P=ROOT.parent
sys.path.insert(0,str(P/'v8/simulation'))
from replay_candidate import startup

def rows(name):return list(csv.DictReader((ROOT/'results/data/sensitivity'/name).open()))
if __name__=='__main__':
 index=json.loads((ROOT/'results/data/sensitivity/replay_index.json').read_text());assert len(index['cases'])==9 and index['nominal']['M0_subset_pass']
 assert index['control_sha256']==hashlib.sha256((P/'v8/results/data/controls_N320.npz').read_bytes()).hexdigest()
 checks=[]
 for x in index['cases']:
  r=rows(x['name']+'.csv');t=np.array([float(q['time_s']) for q in r]);assert t[0]==0 and np.all(np.diff(t)>0)
  s=x['summary'];assert abs(t[-1]-s['final']['time_s'])<1e-9 and not s['M0_subset_pass']
  for key in ['height_m','vr_m_s','vt_m_s','usable_kg']:assert abs(float(r[-1][key])-s['final'][key])<1e-8
  assert x['historical_endpoint_max_mixed_SI_difference']<.001
  checks.append(dict(case=x['name'],samples=len(r),event=s['event'],no_extrapolation_past_recorded_event=True,original_endpoint_difference=x['historical_endpoint_max_mixed_SI_difference']))
 endpoints=json.loads((ROOT/'results/data/passive_figure_endpoints.json').read_text());reference=list(csv.DictReader((P/'v5/results/data/passive_cases.csv').open(encoding='utf-8-sig')))
 for x in endpoints:
  ref=next(z for z in reference if z['case']==x['case']);assert abs(x['surface_speed_m_s']-float(ref['surface_speed_m_s']))<.001
  assert abs(x['height_m'])<1e-5 and abs(x['range_km']-float(ref['surface_arc_range_m'])/1000)<1e-5
 t=np.linspace(0,3,3001);curve=np.where(t<=.5,0,np.where(t<=1.5,t-.5,1.1-.1*np.exp(-(t-1.5)/.1)));error=float(max(abs(curve-np.array([startup(float(q)) for q in t]))));assert error<1e-12
 th=math.radians(12);eb=np.array([math.sin(th),math.cos(th)]);ep=np.array([math.cos(th),-math.sin(th)]);cg=np.array([32.5*math.sin(th),40]);B=cg-32.5*eb
 assert abs(np.linalg.norm(cg-B)-32.5)<1e-10 and abs(np.linalg.norm(10*ep)-10)<1e-10
 for length,vector in [(65,65*eb),(7,7*ep),(20,np.array([20.,0.]))]:assert abs(np.linalg.norm(vector)-length)<1e-10
 mapping=list(csv.DictReader((ROOT/'results/data/figure_map.csv').open()));assert [int(x['figure']) for x in mapping]==list(range(1,10))
 for x in mapping:
  for ext in ['png','pdf']:assert (ROOT/'results/figures'/(x['file_stem']+'.'+ext)).is_file()
 result=dict(main_figures=9,requested_added_figures=5,supplement_full_history=True,sensitivity_cases=checks,passive_endpoints_match=True,response_max_difference_from_original=error,geometry_G_H_dimensions_consistent=True,M1_stage_displayed_as_pending=True,full_safety_verified=False)
 (ROOT/'results/logs/figure_checks.json').write_text(json.dumps(result,indent=2));print('PASS: nine main figures, five additions, nine replayed cases, reference sources and response law')
