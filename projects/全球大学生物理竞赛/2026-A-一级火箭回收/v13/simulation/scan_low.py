import sys,numpy as np,json,time
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'results/data'
from solve7 import solve
w=dict(np.load(OUT/'warm_continuous_candidate.npz'));history=[]
for fuel in range(90,140,10):
 t=time.time()
 try:
  z=solve(30,w,prop=fuel,max_iter=90,low_tilt_deg=5.);np.savez(OUT/f'fuel{fuel}_N30.npz',**z);status='NLP_SOLVED_REQUIRES_REPLAY'
 except Exception as e:status='SEARCH_BUDGET_NO_SOLUTION';print(fuel,str(e)[-170:],flush=True)
 history.append(dict(propellant_t=fuel,status=status,seconds=time.time()-t,N=30,max_iterations=90));open(OUT/'low_search_history.json','w').write(json.dumps(history,indent=2));print(history[-1],flush=True)
