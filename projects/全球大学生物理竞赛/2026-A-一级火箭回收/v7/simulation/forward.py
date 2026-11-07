"""Forward-only spherical-Earth variable-mass reference model. SI units."""
from pathlib import Path
import math,json,csv
import numpy as np
from scipy.integrate import solve_ivp
from atmosphere_1976 import atmosphere,GM_E,R_E,G0
ROOT=Path(__file__).resolve().parents[1]

def simulate(propellant_kg=70000.,burn_start_s=None,burn_duration_s=40.,max_step=.1,air=True,burn_windows=None):
    if propellant_kg<=0:raise ValueError('positive propellant required')
    windows=burn_windows if burn_windows is not None else ([] if burn_start_s is None else [(burn_start_s,burn_duration_s)])
    if any(a<0 or d<=0 for a,d in windows):raise ValueError("invalid burn window")
    dry=130000.;unusable=.005*propellant_kg;usable=.995*propellant_kg
    # State: geocentric x,z,vx,vz, usable propellant, cumulative impulse, commanded equivalent throttle.
    y0=[0,R_E+70000,6000/3.6,0,usable,0,0]
    area=math.pi*7**2/4
    def force(t,y):
        r=y[:2];v=y[2:4];rn=np.linalg.norm(r);h=rn-R_E;speed=np.linalg.norm(v)
        rho=atmosphere(float(np.clip(h,0,70000)))['density_kg_m3'] if air else 0.
        drag=-.5*rho*.5*area*speed*v
        # Three installed engines; two active in this prescribed burn.
        T=2e6*max(0,min(1.1,y[6])) if y[4]>0 else 0.
        direction=-v/speed if speed>0 else r/rn
        return drag,T,direction,.5*rho*speed**2
    def rhs(t,y):
        drag,T,direction,q=force(t,y);r=y[:2];m=dry+unusable+max(y[4],0)
        on=any(a+.5<=t<a+.5+d for a,d in windows)
        target=1.1 if on else 0.
        # First-order response with hard slew cap; shutdown also finite.
        du=float(np.clip((target-y[6])/.1,-1,1))
        return np.r_[y[2:4],-GM_E*r/np.linalg.norm(r)**3+(drag+T*direction)/m,-T/(320*G0),T,du]
    def ground(t,y):return np.linalg.norm(y[:2])-R_E-32.5
    ground.terminal=True;ground.direction=-1
    def fuel(t,y):return y[4]
    fuel.terminal=True;fuel.direction=-1
    def ceiling(t,y):return 70000.01-(np.linalg.norm(y[:2])-R_E)
    ceiling.terminal=True;ceiling.direction=-1
    # Integrate at schedule boundaries to avoid stepping over discontinuities.
    edges=[0,500]
    for a,d in windows:edges += [a+.5,a+.5+d]
    edges=sorted(set(x for x in edges if 0<=x<=500));state=np.array(y0,dtype=float);segments=[];event='time_limit'
    for a,b in zip(edges,edges[1:]):
        sol=solve_ivp(rhs,[a,b],state,method='DOP853',rtol=1e-9,atol=1e-7,max_step=max_step,dense_output=True,events=[ground,fuel,ceiling])
        if not sol.success:raise RuntimeError(sol.message)
        segments.append(sol);state=sol.y[:,-1]
        if sol.status==1:
            event=['reference_contact','fuel_exhausted','atmosphere_ceiling'][next(i for i,e in enumerate(sol.t_events) if len(e))];break
    rows=[]
    for sol in segments:
        for t in np.linspace(sol.t[0],sol.t[-1],max(2,int((sol.t[-1]-sol.t[0])*10)+1)):
            y=sol.sol(t);d,T,di,q=force(t,y);m=dry+unusable+max(y[4],0)
            rows.append(dict(time_s=float(t),height_CG_m=float(np.linalg.norm(y[:2])-R_E),range_m=float(R_E*math.atan2(y[0],y[1])),speed_m_s=float(np.linalg.norm(y[2:4])),mass_kg=float(m),usable_kg=float(y[4]),thrust_N=float(T),q_Pa=float(q),n_sum=float((T+np.linalg.norm(d))/(m*G0)),impulse_Ns=float(y[5])))
    consumed=usable-state[4]
    assert abs(consumed-state[5]/(320*G0))<.01
    return dict(event=event,final=rows[-1],max_q_Pa=max(r['q_Pa'] for r in rows),max_n_sum=max(r['n_sum'] for r in rows),consumed_kg=float(consumed),mass_impulse_error_kg=float(consumed-state[5]/(320*G0)),limitations='M0 only. Retrograde thrust direction assumes ideal steering, not validated attitude. Contact uses prescribed upright 32.5 m CG offset, not full C10 collision detection. No safe landing assertion.'),rows
