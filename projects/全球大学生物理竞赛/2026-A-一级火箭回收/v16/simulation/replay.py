"""Independent SI Cartesian replay. No CasADi dynamics are called."""
import numpy as np, math,json
from scipy.integrate import solve_ivp
from atmosphere_1976 import atmosphere
R=6371000.;MU=3.986004418e14;VE=330*9.80665;A=math.pi*3.5**2;K2=(65**2+3*3.5**2)/12

def wind(h,t):
 h=np.maximum(h/1000,0)
 return np.where(h>20.,20*np.exp(-(h-20.)/15.),np.interp(h,[0,.1,2,11,20],[8,8,15,35,20]))

def startup(t):
 if t<=.5:return 0.
 if t<=1.5:return t-.5
 return 1.1-.1*np.exp(-(t-1.5)/.1)
def decay(u,t):
 sw=np.maximum(u-.1,0);return np.where(t<=sw,u-t,np.minimum(u,.1)*np.exp(-np.maximum(t-sw,0)/.1))
class Replay:
 def __init__(self,w,cd=.5,wind_scale=1.,isp=330.):
  self.cd=cd;self.wind_scale=wind_scale;self.ve=isp*9.80665
  self.w=w;self.ig=float(w['ignition']);self.e1=self.ig+1.6+float(w['dur1']);self.ig2=self.e1+float(w['gap']);self.tf=self.ig2+1.6+float(w['dur2']);self.m0=float(w['m0'])*1000
 def control(self,t):
  w=self.w
  if t<self.ig:return np.zeros(7),np.array([0,2.5,1.25,-1.25,-2.5,-1.25,1.25]),0.
  if t<self.ig+1.6:u=np.full(7,startup(t-self.ig));de=0.;a=np.array([0,2.5,1.25,-1.25,-2.5,-1.25,1.25])
  elif t<=self.e1:
   q=np.array([np.interp(t,np.linspace(self.ig+1.6,self.e1,w['U1'].shape[1]),row) for row in w['U1']]);a=np.array([0,2.5,1.25,-1.25,-2.5,-1.25,1.25]);u=q[0]+a/2.5*q[1];de=q[2]
  elif t<self.ig2:
   a=np.array([0,2.5,1.25,-1.25,-2.5,-1.25,1.25]);u=decay(w['U1'][0,-1]+a/2.5*w['U1'][1,-1],t-self.e1);de=w['U1'][2,-1]+(w['U2'][2,0]-w['U1'][2,-1])*(t-self.e1)/(self.ig2-self.e1)
  elif t<self.ig2+1.6:a=np.array([0,2.5,-2.5]);u=np.full(3,startup(t-self.ig2));de=w['U2'][2,0]
  else:
   a=np.array([0,2.5,-2.5]);q=np.array([np.interp(t,np.linspace(self.ig2+1.6,self.tf,w['U2'].shape[1]),row) for row in w['U2']]);u=q[0]+a/2.5*q[1];de=q[2]
  return u,a,float(de)
 def quantities(self,t,y,ideal=False):
  pos=y[:2];v=y[2:4];m=y[4];r=np.linalg.norm(pos);er=pos/r;et=np.array([er[1],-er[0]]);h=r-R;phi=math.atan2(pos[0],pos[1]);air=v-self.wind_scale*wind(h,t)*et;speed=np.linalg.norm(air)+1e-12
  psi=math.atan2(-air[0],-air[1]) if ideal else y[5];om=0 if ideal else y[6];eb=np.array([math.sin(psi),math.cos(psi)]);ep=np.array([math.cos(psi),-math.sin(psi)])
  co=-np.dot(air,eb)/speed;si=np.dot(air,ep)/speed;rho=atmosphere(np.clip(h,0,220000))['density_kg_m3'];q=.5*rho*speed**2;area=A if ideal else A*co**2+455*si**2;D=q*self.cd*area;Fa=-D*air/speed
  u,a,de=self.control(t);T=u.sum()*1e6;S1=np.dot(a,u)*1e6;S2=np.dot(a*a,u)*1e6;Ft=T*np.array([math.sin(psi+de),math.cos(psi+de)]);Fj=om/self.ve*(32.5*T*ep+S1*eb)
  mt=-32.5*T*math.sin(de)-S1*math.cos(de);ma=5*(eb[1]*Fa[0]-eb[0]*Fa[1])-q*A*65**2*om/(2*speed);mj=-(T*(32.5**2-K2)+S2)*om/self.ve;mg=-1.5*MU/r**3*m*(K2-.5*3.5**2)*math.sin(2*(psi-phi))
  foot=np.array([pos-32.5*eb+sgn*5*ep for sgn in [-1,1]]);clear=np.min(np.linalg.norm(foot,axis=1))-R
  return dict(h=h,phi=phi,theta=psi-phi,omega=om,vt=np.dot(v,et),vr=np.dot(v,er),speed=np.linalg.norm(v),airspeed=speed,q=q,T=T,D=D,n=(T+D+np.linalg.norm(Fj))/(m*9.80665),alpha=math.acos(np.clip(co,-1,1)),delta=de,beta=psi+de-phi,clear=clear,foot=foot,force=Ft+Fa+Fj,moment=mt+ma+mj+mg,mt=mt,ma=ma,mj=mj,mg=mg,u=u,wind=self.wind_scale*wind(h,t))
 def rhs(self,ideal=False):
  def fun(t,y):
   z=self.quantities(t,y,ideal);r=np.linalg.norm(y[:2]);acc=z['force']/y[4]-MU*y[:2]/r**3
   return np.r_[y[2:4],acc,-z['T']/self.ve,0 if ideal else y[6],0 if ideal else z['moment']/(y[4]*K2)]
  return fun
 def run(self,maxstep=.1,prop=None,end_at_plan=False):
  if prop is not None:self.m0=130000+prop*1000
  y=np.array([0,R+70000,6000/3.6/math.sqrt(2),6000/3.6/math.sqrt(2),self.m0,0,0.]);ts=[];ys=[];event='time_limit';residue=.005*(self.m0-130000)
  def contact(t,y):return self.quantities(t,y,t<self.ig)['clear']
  def empty(t,y):return y[4]-130000-residue
  contact.terminal=True;contact.direction=-1;empty.terminal=True;empty.direction=-1
  knots=np.unique(np.r_[np.linspace(0,self.ig,41),self.ig+np.array([.5,1.5,1.6]),np.linspace(self.ig+1.6,self.e1,self.w['U1'].shape[1]),self.e1+np.linspace(0,2,41),self.ig2,self.ig2+np.array([.5,1.5,1.6]),np.linspace(self.ig2+1.6,self.tf,self.w['U2'].shape[1]),self.tf+(0 if end_at_plan else .05)])
  for a,b in zip(knots[:-1],knots[1:]):
   if a==self.ig:
    pos=y[:2];er=pos/np.linalg.norm(pos);air=y[2:4]-self.wind_scale*wind(np.linalg.norm(pos)-R,a)*np.array([er[1],-er[0]]);y[5]=math.atan2(-air[0],-air[1]);y[6]=0.
   sol=solve_ivp(self.rhs(a<self.ig-1e-9),(a,b),y,method='DOP853',rtol=2e-11,atol=1e-10,max_step=maxstep,dense_output=True,events=[contact,empty]);end=sol.t[-1];tt=np.linspace(a,end,max(2,math.ceil((end-a)/.05)+1));yy=sol.sol(tt);ts.extend(tt[:-1]);ys.extend(yy[:,:-1].T);y=sol.y[:,-1]
   if sol.status==1:event='contact' if len(sol.t_events[0]) else 'usable_propellant_exhausted';ts.append(end);ys.append(y.copy());break
  else:ts.append(end);ys.append(y.copy())
  ts=np.array(ts);ys=np.array(ys);zz=[self.quantities(t,y,t<self.ig) for t,y in zip(ts,ys)];keys=['h','phi','theta','omega','vt','vr','speed','airspeed','q','T','D','n','alpha','delta','beta','clear','wind'];data={k:np.array([z[k] for z in zz]) for k in keys};data.update(t=ts,state=ys,m=ys[:,4],range=R*data['phi'],gamma=np.arctan2(data['vr'],data['vt']));return data,event
if __name__=='__main__':
 import sys
 w=dict(np.load(sys.argv[1]));r=Replay(w);d,event=r.run();np.savez(sys.argv[1].replace('.npz','_replay.npz'),**d);print(json.dumps(dict(event=event,tf=d['t'][-1],h=d['h'][-1],vr=d['vr'][-1],vt=d['vt'][-1],theta_deg=np.degrees(d['theta'][-1]),omega_deg=np.degrees(d['omega'][-1]),qmax=d['q'].max(),nmax=d['n'].max(),mass=d['m'][-1],range=d['range'][-1]),indent=2))
