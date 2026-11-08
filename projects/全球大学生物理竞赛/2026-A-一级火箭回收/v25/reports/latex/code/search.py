"""Reproducible bounded, multi-start Powell and grid search."""
import json,time
from itertools import product
import numpy as np
from scipy.optimize import minimize
from model import run,CONFIG,ROOT
LOW=np.array(CONFIG['SEARCH_LO']);HIGH=np.array(CONFIG['SEARCH_HI'])
def decode(z):return LOW+np.clip(z,0,1)*(HIGH-LOW)
def score(r):
    if not r['contact_event']:return CONFIG['NONCONTACT_COST']+r['used_kg']/CONFIG['COST_MASS']
    violation=[max(-r['vz_mps']/CONFIG['DESIGN_VZ']-1,0),max(r['vz_mps'],0)/CONFIG['DESIGN_VZ'],
        max(abs(r['vx_mps'])/CONFIG['DESIGN_VX']-1,0),max(r['qmax_pa']/CONFIG['DESIGN_Q']-1,0),
        max(r['nmax']/CONFIG['DESIGN_N']-1,0),max(r['tilt_deg']/CONFIG['DESIGN_TILT']-1,0),
        max((CONFIG['DESIGN_RESERVE']-r['residual_kg'])/CONFIG['DESIGN_RESERVE'],0)]
    return r['used_kg']/CONFIG['COST_MASS']+CONFIG['COST_WEIGHT']*sum(x*x for x in violation)
def optimize(load,starts=3,previous=None):
    candidates=[];calls=0;fits=[]
    def fun(z):
        nonlocal calls
        calls+=1;r=run(load,decode(z),dt=.1);v=score(r);return v
    for h,v,k in product([45000.,60000.,75000.],[650.,900.,1125.],[1.05,1.55]):
        z=(np.array([h,v,k,1.2])-LOW)/(HIGH-LOW);candidates.append((fun(z),z))
    if previous is not None:
        z=(np.array(previous)-LOW)/(HIGH-LOW);candidates.append((fun(z),z))
    seeds=sorted(candidates,key=lambda row:row[0])[:starts]
    for _,z in seeds:
        fit=minimize(fun,z,method='Powell',bounds=[(0,1)]*4,
            options={'maxiter':35,'maxfev':800,'xtol':1e-3,'ftol':1e-5})
        candidates.append((float(fit.fun),fit.x));fits.append(dict(success=bool(fit.success),message=str(fit.message),nfev=int(fit.nfev),fun=float(fit.fun)))
    value,z=min(candidates,key=lambda row:row[0]);p=decode(z)
    # Ordered 27-neighbor refinement; update the current best deterministically.
    for dh,dv,dk in product([-1000.,0.,1000.],[-20.,0.,20.],[-.02,0,.02]):
        trial=np.clip(p+np.array([dh,dv,dk,0.]),LOW,HIGH);zz=(trial-LOW)/(HIGH-LOW)
        val=fun(zz)
        if val<value:value,p=val,trial
    result=run(load,p,dt=.02);result['search_calls']=calls;result['coarse_score']=value;result['powell_runs']=fits
    return result
if __name__=='__main__':
    allrows=[];previous=None;start=time.time()
    for load in range(90,301,10):
        r=optimize(load,previous=previous);allrows.append(r);previous=r['parameters']
        (ROOT/'results/data/load_search.json').write_text(json.dumps(allrows,indent=2))
        print(json.dumps({k:r[k] for k in ['load_t','pass','used_kg','entry_kg','landing_kg','vz_mps','vx_mps','qmax_pa','nmax','tilt_deg','residual_kg','parameters','search_calls']}),flush=True)
        if r['pass']:
            print('First feasible tested load, elapsed',time.time()-start,flush=True);break
    else:print('No feasible load found within the explored range',flush=True)
