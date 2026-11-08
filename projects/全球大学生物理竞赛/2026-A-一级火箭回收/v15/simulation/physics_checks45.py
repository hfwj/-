from pathlib import Path
import json,numpy as np
from scipy.integrate import solve_ivp
from physics import density
from atmosphere_1976 import atmosphere
B=Path(__file__).resolve().parent.parent
hs=np.unique(np.r_[np.linspace(0,220000,101),11000,20000,32000,47000,51000,71000,85999.95,86000,144800]);err=[]
for h in hs:
 a=float(density(h/1000));b=atmosphere(float(h))['density_kg_m3'];err.append(abs(a-b)/b)
assert max(err)<1e-8
R=6371000.;mu=3.986004418e14;v=6000/3.6/np.sqrt(2)
def fun(t,y):return np.r_[y[2:4],-mu*y[:2]/np.linalg.norm(y[:2])**3]
def apex(t,y):return np.dot(y[:2],y[2:4])/np.linalg.norm(y[:2])
apex.direction=-1
z=solve_ivp(fun,[0,280],[0,R+70000,v,v],method='DOP853',rtol=1e-12,atol=1e-10,events=apex,max_step=1)
r=np.linalg.norm(z.y[:2],axis=0);energy=np.sum(z.y[2:4]**2,axis=0)/2-mu/r;ell=z.y[1]*z.y[2]-z.y[0]*z.y[3];ya=z.y_events[0][0];out=dict(density_comparison_points=len(hs),density_max_relative_difference=max(err),vacuum_apogee_time_s=float(z.t_events[0][0]),vacuum_apogee_height_m=float(np.linalg.norm(ya[:2])-R),vacuum_specific_energy_max_drift_J_kg=float(abs(energy-energy[0]).max()),vacuum_specific_angular_momentum_max_drift_m2_s=float(abs(ell-ell[0]).max()),initial_vt_m_s=v,initial_vr_m_s=v)
(B/'results/data/physics_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
