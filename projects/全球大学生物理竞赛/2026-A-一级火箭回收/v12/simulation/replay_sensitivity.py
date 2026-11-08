"""Save real frozen-plan trajectories for all nine panels; do not overwrite v9."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];P=ROOT.parent
sys.path.insert(0,str(P/'v9/simulation'))
from audit import trajectory

def save(name,rows):
 out=ROOT/'results/data/sensitivity';out.mkdir(parents=True,exist_ok=True)
 with (out/(name+'.csv')).open('w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)

def run():
 baseline=json.loads((P/'v9/results/data/audit.json').read_text());controls=P/'v8/results/data/controls_N320.npz';p=dict(np.load(controls));result={'control_sha256':hashlib.sha256(controls.read_bytes()).hexdigest(),'cases':[]}
 n,rows=trajectory(p);save('nominal',rows);result['nominal']=n
 assert n['M0_subset_pass']
 for old in baseline['frozen_open_loop_sensitivity']:
  s,rows=trajectory(p,step=.25,**old['parameters']);save(old['name'],rows)
  assert s['event']==old['event'] and not s['M0_subset_pass']
  err=max(abs(s['final'][k]-old['final'][k]) for k in ['time_s','height_m','vt_m_s','vr_m_s','mass_kg'])
  assert err<.001,(old['name'],err)
  result['cases'].append(dict(name=old['name'],parameters=old['parameters'],historical_endpoint_max_mixed_SI_difference=err,summary=s))
  print(old['name'],s['event'],len(rows),'samples',flush=True)
 (ROOT/'results/data/sensitivity/replay_index.json').write_text(json.dumps(result,indent=2))
 return result
if __name__=='__main__':run()
