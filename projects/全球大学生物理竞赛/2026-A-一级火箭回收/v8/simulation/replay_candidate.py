from pathlib import Path
import numpy as np,math,json,csv,sys
from scipy.integrate import solve_ivp,quad
from scipy.optimize import minimize_scalar
from atmosphere_1976 import atmosphere,GM_E,R_E,G0
ROOT=Path(__file__).resolve().parents[1]
VE=320*G0;A=math.pi*7**2/4

def startup(t):
 if t<.5:return 0.
 if t<=1.5:return t-.5
 return 1.1-.1*math.exp(-(t-1.5)/.1)
def off(u,d):
 a=max(u-.1,0)
 return max(0,u-d) if d<=a else min(u,.1)*math.exp(-(d-a)/.1)

def replay(filename,step=.1):
 p=dict(np.load(filename));N=int(p['N']);toff=float(p['toff']);tf=float(p['tf']);m0=float(p['m0'])*1000
 ignition=float(p.get("ignition_s",0));start=ignition+1.6
 t1=np.linspace(start,toff,N+1);t2=np.linspace(toff+6.6,tf,N+1);u1=p['U1'];u2=p['U2']
 def linear(t,grid,arr):
  k=min(max(np.searchsorted(grid,t,side='right')-1,0),len(grid)-2);s=(arr[:,k+1]-arr[:,k])/(grid[k+1]-grid[k]);v=arr[:,k]+s*(min(max(t,grid[0]),grid[-1])-grid[k]);return v,s
 def control(t):
  if t<start:return startup(t-ignition),startup(t-ignition),-math.pi/2,0.
  if t<=toff:
   u,s=linear(t,t1,u1);return u[0],u[1],u[2],s[2]
  if t<toff+6.6:
   d=t-toff;pair=off(u1[0,-1],d) if d<5.5 else startup(d-5)
   return pair,off(u1[1,-1],d),u1[2,-1]+(u2[1,0]-u1[2,-1])*d/6.6,(u2[1,0]-u1[2,-1])/6.6
  u,s=linear(t,t2,u2);return u[0],0.,u[1],s[1] if t<=tf else 0.
 def values(t,y):
  r=y[:2];v=y[2:4];rn=np.linalg.norm(r);er=r/rn;et=np.array([er[1],-er[0]]);h=rn-R_E
  rho=atmosphere(float(np.clip(h,0,70000)))['density_kg_m3'];speed=np.linalg.norm(v)
  pair,extra,b,bd=control(t);T=1e6*(2*pair+extra);D=.5*rho*.5*A*speed**2
  direction=math.cos(b)*er+math.sin(b)*et;drag=-D*v/max(speed,1e-12)
  return dict(height_m=float(h),speed_m_s=float(speed),vt_m_s=float(v@et),vr_m_s=float(v@er),range_m=float(R_E*math.atan2(r[0],r[1])),mass_kg=float(y[4]),usable_kg=float(y[4]-130000-.005*(m0-130000)),q_Pa=float(.5*rho*speed**2),n_sum=float((T+D)/(y[4]*G0)),n_proper=float(np.linalg.norm(T*direction+drag)/(y[4]*G0)),thrust_N=float(T),pair_actual_throttle=float(pair),third_actual_throttle=float(extra),beta_deg=math.degrees(b),global_thrust_rate_deg_s=math.degrees(bd+float(v@et)/rn)),direction,drag
 def rhs(t,y):
  z,d,drag=values(t,y);r=y[:2]
  return np.r_[y[2:4],-GM_E*r/np.linalg.norm(r)**3+(z['thrust_N']*d+drag)/y[4],-z['thrust_N']/VE]
 def contact(t,y):return np.linalg.norm(y[:2])-R_E-32.5
 contact.terminal=True;contact.direction=-1
 edges=sorted(set([0,ignition,ignition+.5,ignition+1.5,start,toff,toff+max(u1[0,-1]-.1,0),toff+max(u1[1,-1]-.1,0),toff+5,toff+5.5,toff+6.5,toff+6.6,tf,tf+2]+list(t1)+list(t2)))
 y=np.array([0.,R_E+70000,6000/3.6,0.,m0]);segs=[];event=False
 for a,b in zip(edges,edges[1:]):
  if b-a<1e-9:continue
  sol=solve_ivp(rhs,(a,b),y,rtol=2e-11,atol=1e-8,max_step=step,method='DOP853',dense_output=True,events=contact)
  if not sol.success:raise RuntimeError(sol.message)
  segs.append(sol);y=sol.y[:,-1]
  if len(sol.t_events[0]):event=True;break
 end=float(segs[-1].t[-1])
 def sample(t):
  i=min(np.searchsorted([s.t[-1] for s in segs],t,side='left'),len(segs)-1)
  return values(t,segs[i].sol(t))[0]
 times=np.unique(np.r_[np.arange(0,end,.05),[s.t[-1] for s in segs],end]);rows=[dict(time_s=float(t),**sample(t)) for t in times]
 peaks={}
 for key in ['q_Pa','n_sum','n_proper']:
  vals=np.array([r[key] for r in rows]);best=max(vals)
  for i in range(1,len(times)-1):
   if vals[i]>=vals[i-1] and vals[i]>vals[i+1]:
    res=minimize_scalar(lambda t:-sample(t)[key],bounds=(times[i-1],times[i+1]),method='bounded');best=max(best,-res.fun)
  peaks[key]=float(best)
 slopes1=np.diff(u1,axis=1)/np.diff(t1);slopes2=np.diff(u2,axis=1)/np.diff(t2)
 commands=np.r_[(u1[:2,:-1]+.1*slopes1[:2]).flatten(),(u1[:2,1:]+.1*slopes1[:2]).flatten(),u2[0,:-1]+.1*slopes2[0],u2[0,1:]+.1*slopes2[0]]
 mass_used=sum(quad(lambda t:1e6*(2*control(t)[0]+control(t)[1])/VE,a,min(b,end),epsabs=1e-7)[0] for a,b in zip(edges,edges[1:]) if a<end)
 mass_error=abs(m0-rows[-1]['mass_kg']-mass_used);slew=max(1,np.max(np.abs(slopes1[:2])),np.max(np.abs(slopes2[0])));reserve_min=min(r['usable_kg'] for r in rows)
 final=rows[-1];ratio=final['thrust_N']*math.cos(math.radians(final['beta_deg']))/(final['mass_kg']*GM_E/(R_E+final['height_m'])**2);domain=all(32.5-.01<=r['height_m']<=70000+.01 for r in rows);passed=mass_error<.001 and slew<=1+1e-6 and reserve_min>=0 and domain and ratio<=1 and event and peaks['q_Pa']<=50000 and peaks['n_sum']<=4 and abs(final['vt_m_s'])<=.5 and -2<=final['vr_m_s']<=0 and final['usable_kg']>=2.2e6/VE and commands.min()>=.3-1e-6 and commands.max()<=1.1+1e-6 and max(abs(r['global_thrust_rate_deg_s']) for r in rows)<=5+1e-6
 summary=dict(M0_subset_pass=bool(passed),full_v4_status='NOT_VERIFIED',mass_balance_error_kg=mass_error,min_usable_kg=reserve_min,pair_ignition_count=2,third_ignition_count=1,atmosphere_domain_pass=domain,terminal_vertical_thrust_over_weight=ratio,contact_event=bool(event),initial_propellant_kg=m0-130000,ignition_command_s=ignition,consumed_kg=m0-final['mass_kg'],toff_s=toff,restart_command_s=toff+5,designed_end_s=tf,actual_end_s=end,final=final,peaks=peaks,command_min=float(commands.min()),command_max=float(commands.max()),max_actual_throttle_slew_per_s=float(max(1,np.max(np.abs(slopes1[:2])),np.max(np.abs(slopes2[0])))),max_global_thrust_rate_deg_s=max(abs(r['global_thrust_rate_deg_s']) for r in rows))
 return summary,rows
if __name__=='__main__':
 name=sys.argv[1] if len(sys.argv)>1 else str(ROOT/'results/data/controls_N320.npz')
 s,rows=replay(name);print(json.dumps(s,indent=2));(ROOT/'results/data/replay_summary.json').write_text(json.dumps(s,indent=2))
 with open(ROOT/'results/data/candidate_trajectory.csv','w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],lineterminator="\n");w.writeheader();w.writerows(rows)
