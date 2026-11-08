from pathlib import Path
import numpy as np,json,time
from solve45 import solve
B=Path(__file__).resolve().parent.parent;D=B/'results/data';warm=dict(np.load(D/'free45_optign_N30.npz'));hist=[]
for fuel in range(90,140,10):
 t=time.time()
 try:
  w=solve(30,warm,prop=fuel,max_iter=90,opt_ignition=True,direction_rate_opt_deg=5.);np.savez(D/f'fuel{fuel}_optign45_N30.npz',**w);status='NLP_RETURNED_REQUIRES_REPLAY'
 except Exception as e:status='SEARCH_BUDGET_NO_VALIDATED_SOLUTION';print(fuel,str(e)[-180:],flush=True)
 row=dict(propellant_t=fuel,nodes_per_burn=30,max_iterations=90,status=status,seconds=time.time()-t);hist.append(row);(D/'load_search_history.json').write_text(json.dumps(hist,indent=2));print(row,flush=True)
