"""Freeze the selected control; generate convergence and strategy data."""
from pathlib import Path
import json
import numpy as np
from model import run,ROOT,COLUMNS,CONFIG
rows=json.loads((ROOT/'results/data/load_search.json').read_text())
selected=next(r for r in rows if r['pass'])
p=selected['parameters'];load=selected['load_t']
conv=[]
for dt in [.02,.01,.005]:
    r,h=run(load,p,dt=dt,history=True);conv.append(r)
    np.savez_compressed(ROOT/f'results/data/convergence_{dt:.3f}.npz',history=h,columns=np.array(COLUMNS))
    print('step',dt,{k:r[k] for k in ['used_kg','vz_mps','qmax_pa','contact_s','pass']},flush=True)
(ROOT/'results/data/convergence.json').write_text(json.dumps(conv,indent=2))
strategies=[]
for name,params,mode in [('S0: 75-to-55 km height cutoff',[75000.,1100.,1.3,1.5],0),('S1: early speed cutoff',[75000.,750.,1.4,1.5],1),('S2: bounded parameter search',p,1)]:
    r,h=run(load,params,dt=.005,mode=mode,history=True);r['strategy']=name;strategies.append(r)
    
    if len(strategies)<3:
        np.savez_compressed(ROOT/f'results/data/strategy_S{len(strategies)-1}.npz',history=h,columns=np.array(COLUMNS))
(ROOT/'results/data/strategies.json').write_text(json.dumps(strategies,indent=2))
nom=conv[-1]
(ROOT/'results/data/selected.json').write_text(json.dumps(nom,indent=2))
print(json.dumps(nom,indent=2))
