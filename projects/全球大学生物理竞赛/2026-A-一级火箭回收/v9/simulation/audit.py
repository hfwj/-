"""Independent SI polar audit. Reads v8 controls; never imports its replay/RHS."""
from pathlib import Path
import math,json,csv
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize_scalar
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'v8'
R=6371000.;MU=3.986004418e14;G=9.80665;AREA=math.pi*49/4;RA=8314.32/28.9644

def rho(h):
 # No clipping. Formula extension to 71 geopotential km is explicit;
 # audit separately checks the v8 declared geometric 0..70 km domain.
 H=6356766*h/(6356766+h)
 if not 0<=H<=71000:raise ValueError('Outside lower-atmosphere formula domain')
 T=288.15;P=101325.
 for lo,hi,lapse in zip([0,11000,20000,32000,47000,51000],[11000,20000,32000,47000,51000,71000],[-.0065,0,.001,.0028,0,-.0028]):
  dh=min(H,hi)-lo
  if dh<0:break
  end=T+lapse*dh
  P*=math.exp(-G*dh/(RA*T)) if lapse==0 else (T/end)**(G/(RA*lapse))
  T=end
  if H<=hi:return P/(RA*T)
 raise ValueError(h)

def validate(p):
 for k in ['N','m0','tf','toff','ignition_s','U1','U2','X1','X2']:
  if k not in p or not np.all(np.isfinite(p[k])):raise ValueError('Missing/nonfinite '+k)
 n=int(p['N']);ig=float(p['ignition_s']);off=float(p['toff']);tf=float(p['tf'])
 if n!=p['N'] or n<20 or p['U1'].shape!=(3,n+1) or p['U2'].shape!=(2,n+1) or p['X1'].shape!=(4,n+1) or p['X2'].shape!=(4,n+1):raise ValueError('Invalid grid/shapes')
 if not (0<=ig<=95 and ig+21.6<=off<=300 and tf-off>=26.6 and 110<=tf<=450 and 131<=float(p['m0'])<=400):raise ValueError('Invalid timing/mass')
 for key in ['U1','U2']:
  u=p[key]
  if np.max(abs(u[-1]))>math.pi/2+1e-7:raise ValueError('Direction outside +/-90 deg')
  if u[:-1].min()<.3-1e-7 or u[:-1].max()>1.1+1e-7:raise ValueError('Steady throttle bound')
 for u,dt in [(p['U1'],(off-ig-1.6)/n),(p['U2'],(tf-off-6.6)/n)]:
  slope=np.diff(u[:-1])/dt
  if np.max(abs(slope))>1+1e-6:raise ValueError('Actual throttle slew')
  commands=np.r_[(u[:-1,:-1]+.1*slope).ravel(),(u[:-1,1:]+.1*slope).ravel()]
  if commands.min()<.3-1e-6 or commands.max()>1.1+1e-6:raise ValueError('Implied command bounds')
  if max(abs(np.diff(u[-1])/dt))>math.radians(4.9)+1e-6:raise ValueError('Direction slew')
 endpoint=1.1-.1*math.exp(-1)
 if max(abs(p['U1'][:2,0]-endpoint))>1e-6 or abs(p['U2'][0,0]-endpoint)>1e-6 or abs(p['U1'][2,0]+math.pi/2)>1e-6:raise ValueError('Start continuity')
 if abs(p['U2'][1,-1])>1e-6:raise ValueError('Designed final direction')
 if abs(p['U2'][1,0]-p['U1'][2,-1])>math.radians(4.9)*6.6+1e-6:raise ValueError('Gap direction slew')
 return True

class Schedule:
 def __init__(self,p):
  validate(p);self.p=p;self.ig=float(p['ignition_s']);self.off=float(p['toff']);self.tf=float(p['tf']);n=int(p['N'])
  self.t1=np.linspace(self.ig+1.6,self.off,n+1);self.t2=np.linspace(self.off+6.6,self.tf,n+1)
  self.edges=np.unique(np.r_[0,self.ig,self.ig+.5,self.ig+1.5,self.t1,self.t2,self.off+5,self.off+5.5,self.off+6.5,self.off+np.maximum(p['U1'][:2,-1]-.1,0)])
 @staticmethod
 def rise(d):
  if d<=.5:return 0.
  if d<=1.5:return d-.5
  return 1.1-.1*math.exp(-(d-1.5)/.1)
 @staticmethod
 def decay(u,d):
  switch=max(0.,u-.1)
  return u-d if d<=switch else min(u,.1)*math.exp(-(d-switch)/.1)
 @staticmethod
 def interp(t,g,u):
  i=min(max(int(np.searchsorted(g,t,side='right'))-1,0),len(g)-2);s=(u[:,i+1]-u[:,i])/(g[i+1]-g[i]);return u[:,i]+s*(t-g[i]),s
 def actual(self,t):
  p=self.p
  if t<self.t1[0]:
   u=self.rise(t-self.ig);return np.array([u,u,-math.pi/2,0.])
  if t<=self.off:
   u,s=self.interp(t,self.t1,p['U1']);return np.r_[u,s[-1]]
  if t<self.t2[0]:
   d=t-self.off;a=p['U1'][:,-1];end=p['U2'][1,0];rate=(end-a[2])/6.6
   pair=self.decay(a[0],d) if d<=5.5 else self.rise(d-5)
   return np.array([pair,self.decay(a[1],d),a[2]+rate*d,rate])
  u,s=self.interp(min(t,self.tf),self.t2,p['U2']);return np.array([u[0],0,u[1],s[1]])
 def command(self,t):
  if t<self.t1[0]:return np.ones(2)*float(t>=self.ig+.5)*1.1
  if t<self.off:
   u,s=self.interp(t,self.t1,self.p['U1']);return u[:2]+.1*s[:2]
  if t<self.t2[0]:return np.array([1.1 if t>=self.off+5.5 else 0.,0.])
  u,s=self.interp(min(t,self.tf),self.t2,self.p['U2']);return np.array([u[0]+.1*s[0],0.])

def trajectory(p,*,method='DOP853',step=.2,cd=.5,isp=320.,density_factor=1.,dv_t=0.,dv_r=0.,sample_step=.05):
 sch=Schedule(p);m0=float(p['m0'])*1000;unusable=.005*(m0-130000);y=np.array([70000.,6000/3.6+dv_t,dv_r,m0,0.,0.,0.]);segs=[];event='NO_CONTACT_BY_PLANNED_END'
 def quantities(t,x):
  h,vt,vr,m=x[:4];pair,third,b,bd=sch.actual(t);T=1e6*(2*pair+third);q=.5*rho(h)*density_factor*(vt*vt+vr*vr);speed=math.hypot(vt,vr);D=q*cd*AREA
  at=(T*math.sin(b)-D*vt/max(speed,1e-15))/m;ar=(T*math.cos(b)-D*vr/max(speed,1e-15))/m
  return T,q,D,at,ar,b,bd
 def rhs(t,x):
  h,vt,vr,m=x[:4];r=R+h;T,q,D,at,ar,_,_=quantities(t,x)
  return [vr,at-vr*vt/r,ar-MU/r**2+vt*vt/r,-T/(isp*G),vt/r,vt*at+vr*ar,r*at]
 def contact(t,x):return x[0]-32.5
 def empty(t,x):return x[3]-130000-unusable
 contact.terminal=True;contact.direction=-1;empty.terminal=True;empty.direction=-1
 for a,b in zip(sch.edges[:-1],sch.edges[1:]):
  sol=solve_ivp(rhs,(a,b),y,method=method,rtol=3e-11,atol=[1e-7,1e-9,1e-9,1e-7,1e-13,1e-5,1e-2],max_step=step,dense_output=True,events=[contact,empty]);assert sol.success,sol.message
  segs.append(sol);y=sol.y[:,-1]
  if len(sol.t_events[0]):event='REFERENCE_CONTACT';break
  if len(sol.t_events[1]):event='USABLE_PROPELLANT_EXHAUSTED';break
 end=segs[-1].t[-1];ends=np.array([s.t[-1] for s in segs]);times=np.unique(np.r_[np.arange(0,end,sample_step),ends,end])
 def sample(t):return segs[min(int(np.searchsorted(ends,t)),len(segs)-1)].sol(t)
 def row(t):
  x=sample(t);T,q,D,at,ar,b,bd=quantities(t,x);h,vt,vr,m,theta,w,l=x;e=.5*(vt*vt+vr*vr)-MU/(R+h);e0=.5*((6000/3.6+dv_t)**2+dv_r**2)-MU/(R+70000)
  return dict(time_s=float(t),height_m=float(h),vt_m_s=float(vt),vr_m_s=float(vr),mass_kg=float(m),range_m=float(R*theta),q_Pa=float(q),n_sum=float((T+D)/(m*G)),n_proper=float(math.hypot(at,ar)/G),beta_deg=math.degrees(b),local_direction_rate_deg_s=math.degrees(bd),global_direction_rate_deg_s=math.degrees(bd+vt/(R+h)),usable_kg=float(m-130000-unusable),energy_balance_residual_J_kg=float(e-e0-w),angular_momentum_balance_residual_m2_s=float((R+h)*vt-(R+70000)*(6000/3.6+dv_t)-l),vertical_thrust_over_weight=float(T*math.cos(b)/(m*MU/(R+h)**2)))
 rows=[row(t) for t in times];peaks={}
 for key in ['q_Pa','n_sum']:
  z=np.array([r[key] for r in rows]);best=max(z)
  for i in range(1,len(times)-1):
   if z[i]>=z[i-1] and z[i]>z[i+1]:best=max(best,-minimize_scalar(lambda t:-row(t)[key],bounds=(times[i-1],times[i+1]),method='bounded').fun)
  peaks[key]=float(best)
 f=rows[-1];domain=all(0<=r['height_m']<=70000+.001 for r in rows)
 passed=event=='REFERENCE_CONTACT' and domain and peaks['q_Pa']<=50000 and peaks['n_sum']<=4 and -2<=f['vr_m_s']<=0 and abs(f['vt_m_s'])<=.5 and f['usable_kg']>=2.2e6/(320*G) and f['vertical_thrust_over_weight']<=1 and max(abs(r['global_direction_rate_deg_s']) for r in rows)<=5+1e-6
 return dict(M0_subset_pass=bool(passed),event=event,final=f,peaks=peaks,domain_pass=domain,max_energy_balance_residual_J_kg=max(abs(r['energy_balance_residual_J_kg']) for r in rows),max_angular_momentum_balance_residual_m2_s=max(abs(r['angular_momentum_balance_residual_m2_s']) for r in rows)),rows

def actuator_check(p):
 s=Schedule(p);y=np.zeros(2);err=0.
 def rhs(t,u):return np.clip((s.command(t)-u)/.1,-1,1)
 for a,b in zip(s.edges[:-1],s.edges[1:]):
  z=solve_ivp(rhs,(a,b),y,rtol=1e-10,atol=1e-11,max_step=.02,dense_output=True);assert z.success;y=z.y[:,-1]
  for t in np.linspace(a,b,5):err=max(err,float(max(abs(z.sol(t)-s.actual(t)[:2]))))
 return err

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--quick',action='store_true');args=parser.parse_args()
 p=dict(np.load(SOURCE/'results/data/controls_N320.npz'));validate(p);out=ROOT/'results/data'
 results={};s,rows=trajectory(p);results['nominal']=s;assert s['M0_subset_pass'];print('nominal',s,flush=True)
 with (out/'independent_trajectory.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
 (out/'independent_nominal.json').write_text(json.dumps(s,indent=2))
 if not args.quick:
  results['rk45'],_=trajectory(p,method='RK45',step=.1)
  print('RK45',results['rk45'],flush=True)
  results['actuator_max_actual_error']=actuator_check(p);print('actuator error',results['actuator_max_actual_error'],flush=True)
  scenarios=[('Cd_minus10pct',dict(cd=.45)),('Cd_plus10pct',dict(cd=.55)),('Isp_minus1pct',dict(isp=316.8)),('Isp_plus1pct',dict(isp=323.2)),('rho_minus5pct',dict(density_factor=.95)),('rho_plus5pct',dict(density_factor=1.05)),('initial_vt_minus1m_s',dict(dv_t=-1)),('initial_vt_plus1m_s',dict(dv_t=1)),('initial_vr_minus1m_s',dict(dv_r=-1))]
  results['frozen_open_loop_sensitivity']=[]
  for name,kwargs in scenarios:
   z,_=trajectory(p,step=.25,**kwargs);results['frozen_open_loop_sensitivity'].append(dict(name=name,parameters=kwargs,**z));print(name,z['M0_subset_pass'],z['event'],z['final']['vr_m_s'],z['final']['vt_m_s'],flush=True)
  (out/'audit.json').write_text(json.dumps(results,indent=2))
