import math,numpy as np,casadi as ca
from physics import density,R,MU,G0,VE,A,startup
K2=(65**2+3*3.5**2)/12;ELL=32.5;CP=5.;CMQ=1.;SIDE=65*7

def wind(h,t):return (10*ca.exp(-h/2)+35*ca.exp(-((h-12)/5)**2)+60*(h/70)**2+2*ca.sin(2*math.pi*t/8)*ca.exp(-h))/1000

def pack(u,d,n):
 return ca.vertcat(n*u,(7.5 if n==7 else 5)*d,(18.75 if n==7 else 12.5)*u)
def f(x,z,t,ideal=False):
 h,vt,vr,m,th,om=ca.vertsplit(x);T,S1,S2,de=ca.vertsplit(z);va=vt-wind(h,t);V=ca.sqrt(va*va+vr*vr+1e-12)
 co=-(va*ca.sin(th)+vr*ca.cos(th))/V;si=(va*ca.cos(th)-vr*ca.sin(th))/V
 area=A if ideal else A*co**2+SIDE*si**2
 D=.5*density(h)*V**2*.5*area;q=.5*density(h)*V**2*1e6
 jt=om/VE*(ELL*T*ca.cos(th)+S1*ca.sin(th));jr=om/VE*(-ELL*T*ca.sin(th)+S1*ca.cos(th))
 ft=T*ca.sin(th+de)-D*va/V+jt;fr=T*ca.cos(th+de)-D*vr/V+jr
 mt=-ELL*T*ca.sin(de)-S1*ca.cos(de)
 ma=-CP*D*si-q/1e6*A*65**2*CMQ*om/(2*V*1000)
 mj=-(T*(ELL**2-K2)+S2)*om/VE
 mg=-1.5*MU/(R+h)**3*m*.001*(K2-.5*3.5**2)*ca.sin(2*th)
 return ca.vertcat(vr,ft/m-vr*vt/(R+h),fr/m-MU/(R+h)**2+vt*vt/(R+h),-1000*T/VE,om-vt/(R+h),1000*(mt+ma+mj+mg)/(m*K2))
def rk(x,a,b,dt,t,mid=None):
 mid=(a+b)/2 if mid is None else mid;k1=f(x,a,t);k2=f(x+dt*k1/2,mid,t+dt/2);k3=f(x+dt*k2/2,mid,t+dt/2);k4=f(x+dt*k3,b,t+dt)
 return x+dt*(k1+2*k2+2*k3+k4)/6

def solve(N=30,warm=None,prop=None,ignition=65,max_iter=None,low_tilt_deg=3.5):
 op=ca.Opti();m0=op.variable();dur1=op.variable();gap=op.variable();dur2=op.variable();tf=ignition+1.6+dur1+gap+1.6+dur2;end1=ignition+1.6+dur1;start2=end1+gap+1.6
 if prop is None:op.subject_to(op.bounded(180,m0,500))
 else:op.subject_to(m0==130+prop)
 op.subject_to(op.bounded(5,dur1,110));op.subject_to(op.bounded(5,gap,100));op.subject_to(op.bounded(5,dur2,160));op.subject_to(op.bounded(110,tf,400))
 # Ideal pre-entry orientation; translation still responds to prescribed wind.
 xc=op.variable(4,41);op.subject_to(xc[:,0]==ca.vertcat(70,6000/3.6/1000,0,m0))
 def cf(y,t):
  h,vt,vr,m=ca.vertsplit(y);va=vt-wind(h,t);V=ca.sqrt(va*va+vr*vr+1e-12);D=.5*density(h)*V*V*.5*A
  return ca.vertcat(vr,-D/m*va/V-vr*vt/(R+h),-D/m*vr/V-MU/(R+h)**2+vt*vt/(R+h),0)
 for i in range(40):
  t=i*ignition/40;dt=ignition/40;x=xc[:,i];k1=cf(x,t);k2=cf(x+dt*k1/2,t+dt/2);k3=cf(x+dt*k2/2,t+dt/2);k4=cf(x+dt*k3,t+dt);op.subject_to(xc[:,i+1]==x+dt*(k1+2*k2+2*k3+k4)/6)
 x0=ca.vertcat(xc[:,-1],ca.atan2(-(xc[1,-1]-wind(xc[0,-1],ignition)),-xc[2,-1]),0)
 X1=op.variable(6,N+1);X2=op.variable(6,N+1);U1=op.variable(3,N+1);U2=op.variable(3,N+1)
 def check(x,z):
  h,vt,vr,m,th,om=ca.vertsplit(x);va=vt-wind(h,0) # replaced in check_t
 def check_t(x,z,t):
  h,vt,vr,m,th,om=ca.vertsplit(x);va=vt-wind(h,t);V=ca.sqrt(va*va+vr*vr+1e-12);co=-(va*ca.sin(th)+vr*ca.cos(th))/V;si=(va*ca.cos(th)-vr*ca.sin(th))/V
  q=.5*density(h)*V**2*1e6;D=q/1e6*.5*(A*co**2+SIDE*si**2)
  op.subject_to(q<=47000);op.subject_to((z[0]+D)*1000/(m*G0)<=3.8)
  op.subject_to(ca.fmax(q-1000,0)*(1-co)<=9000*(1-math.cos(math.radians(5))))
  op.subject_to(op.bounded(.0325,h,70));op.subject_to(op.bounded(130,m,500));op.subject_to(op.bounded(-math.radians(10),om,math.radians(10)))
  thlim=math.radians(low_tilt_deg)+math.radians(90)*ca.fmin(ca.fmax((h-.2325)/.5,0),1);op.subject_to(op.bounded(-thlim,th,thlim))
 def start(x,t0,n,de):
  XX=op.variable(6,33);op.subject_to(XX[:,0]==x)
  for i in range(32):
   t=i*.05;z0=ca.vertcat(pack(startup(t),0,n),de);z1=ca.vertcat(pack(startup(t+.05),0,n),de);zm=ca.vertcat(pack(startup(t+.025),0,n),de)
   op.subject_to(XX[:,i+1]==rk(XX[:,i],z0,z1,.05,t0+t,zm));check_t(XX[:,i],z0,t0+t)
  return XX
 XS1=start(x0,ignition,7,0);op.subject_to(X1[:,0]==XS1[:,-1]);op.subject_to(U1[:,0]==ca.vertcat(startup(1.6),0,0))
 def phase(X,U,t0,dur,n):
  dt=dur/N;ratios=[0,1,.5,-.5,-1,-.5,.5] if n==7 else [0,1,-1]
  for k in range(N+1):
   for rr in ratios:op.subject_to(op.bounded(.3,U[0,k]+rr*U[1,k],1.1))
   op.subject_to(op.bounded(-math.radians(6),U[2,k],math.radians(6)))
  for k in range(N):
   sl=(U[:,k+1]-U[:,k])/dt
   for rr in ratios:
    rate=sl[0]+rr*sl[1];op.subject_to(op.bounded(-1,rate,1))
    for j in [k,k+1]:op.subject_to(op.bounded(.3,U[0,j]+rr*U[1,j]+.1*rate,1.1))
   op.subject_to(op.bounded(-math.radians(20),sl[2],math.radians(20)))
   xx=X[:,k]
   for j in range(4):
    aa=j/4;bb=(j+1)/4;u0=(1-aa)*U[:,k]+aa*U[:,k+1];u1=(1-bb)*U[:,k]+bb*U[:,k+1];z0=ca.vertcat(pack(u0[0],u0[1],n),u0[2]);z1=ca.vertcat(pack(u1[0],u1[1],n),u1[2]);tt=t0+(k+aa)*dt
    check_t(xx,z0,tt);op.subject_to(op.bounded(-math.radians(5),xx[5]+sl[2],math.radians(5)));xx=rk(xx,z0,z1,dt/4,tt)
   op.subject_to(X[:,k+1]==xx)
  check_t(X[:,-1],ca.vertcat(pack(U[0,-1],U[1,-1],n),U[2,-1]),t0+dur)
 phase(X1,U1,ignition+1.6,dur1,7)
 # Full shutdown tails followed by coast; all seven old engines decay.
 ratios=np.array([0,1,.5,-.5,-1,-.5,.5]);aipos=ratios*2.5
 def decay(u,d):
  sw=ca.fmax(u-.1,0);return ca.if_else(d<=sw,u-d,ca.fmin(u,.1)*ca.exp(-ca.fmax(d-sw,0)/.1))
 def gz(d):
  us=ca.vertcat(*[decay(U1[0,-1]+rr*U1[1,-1],d) for rr in ratios]);b=U1[2,-1]+(U2[2,0]-U1[2,-1])*d/gap
  return ca.vertcat(ca.sum1(us),ca.dot(aipos,us),ca.dot(aipos*aipos,us),b)
 XOFF=op.variable(6,41);op.subject_to(XOFF[:,0]==X1[:,-1])
 for i in range(40):
  d=i*.05;xx=XOFF[:,i]
  for j in range(4):
   aa=d+j*.0125;xx=rk(xx,gz(aa),gz(aa+.0125),.0125,end1+aa,gz(aa+.00625))
  op.subject_to(XOFF[:,i+1]==xx);check_t(XOFF[:,i],gz(d),end1+d)
 XCO=op.variable(6,31);op.subject_to(XCO[:,0]==XOFF[:,-1]);dtc=(gap-2)/30
 for i in range(30):
  d=2+i*dtc;op.subject_to(XCO[:,i+1]==rk(XCO[:,i],gz(d),gz(d+dtc),dtc,end1+d,gz(d+dtc/2)));check_t(XCO[:,i],gz(d),end1+d)
 XS2=start(XCO[:,-1],end1+gap,3,U2[2,0]);op.subject_to(X2[:,0]==XS2[:,-1]);op.subject_to(U2[:2,0]==ca.vertcat(startup(1.6),0));phase(X2,U2,start2,dur2,3)
 op.subject_to(X2[0,-1]==.0325);op.subject_to(X2[1,-1]==0);op.subject_to(X2[2,-1]==-.001);op.subject_to(X2[4:6,-1]==0)
 op.subject_to(3*U2[0,-1]*ca.cos(U2[2,-1])<=.95*X2[3,-1]*MU/(R+.0325)**2)
 op.subject_to(X2[3,-1]>=130+.005*(m0-130)+3.3e6/VE/1000+.05)
 op.minimize((m0 if prop is None else 1e-2*(m0-X2[3,-1]))+1e-5*(ca.sumsqr(U1[1:,:])+ca.sumsqr(U2[1:,:])))
 variables=dict(X1=X1,X2=X2,U1=U1,U2=U2,XC=xc,XS1=XS1,XS2=XS2,XOFF=XOFF,XCO=XCO)
 if warm:
  for key,var in variables.items():
   if key in warm:
    arr=warm[key];old=np.linspace(0,1,arr.shape[1]);new=np.linspace(0,1,var.shape[1]);op.set_initial(var,np.array([np.interp(new,old,row) for row in arr]))
  for var,key in [(m0,'m0'),(dur1,'dur1'),(gap,'gap'),(dur2,'dur2')]:op.set_initial(var,warm[key])
 else:
  mm=300 if prop is None else 130+prop;op.set_initial(m0,mm);op.set_initial(dur1,35);op.set_initial(gap,15);op.set_initial(dur2,65)
  def guess(times):
   t=np.asarray(times);h=np.maximum(.0325,70*(1-(t/(ignition+1.6+35+15+1.6+65))**1.3));vt=np.maximum(0,1.6667*(1-t/(ignition+80)));vr=-.65*np.sin(math.pi*t/(ignition+1.6+35+15+1.6+65));mass=np.maximum(132,mm-.65*np.maximum(t-ignition,0));theta=np.arctan2(-vt,-vr-1e-8);return np.array([h,vt,vr,mass,theta,np.zeros_like(t)])
  op.set_initial(xc,guess(np.linspace(0,ignition,41))[:4]);op.set_initial(X1,guess(np.linspace(ignition+1.6,ignition+36.6,N+1)));op.set_initial(X2,guess(np.linspace(ignition+53.2,ignition+118.2,N+1)))
  for key,times in [('XS1',np.linspace(ignition,ignition+1.6,33)),('XS2',np.linspace(ignition+51.6,ignition+53.2,33)),('XOFF',np.linspace(ignition+36.6,ignition+38.6,41)),('XCO',np.linspace(ignition+38.6,ignition+51.6,31))]:op.set_initial(variables[key],guess(times))
  op.set_initial(U1,np.array([np.full(N+1,.8),np.zeros(N+1),np.zeros(N+1)]));op.set_initial(U2,np.array([np.linspace(1.063,.42,N+1),np.zeros(N+1),np.zeros(N+1)]))
 op.solver('ipopt',{'expand':True,'print_time':False},{'max_iter':max_iter if max_iter is not None else (1800 if prop is None else 700),'tol':1e-7,'print_level':0,'acceptable_tol':1e-5})
 sol=op.solve();out={k:np.array(sol.value(v)) for k,v in variables.items()};out.update(m0=float(sol.value(m0)),dur1=float(sol.value(dur1)),gap=float(sol.value(gap)),dur2=float(sol.value(dur2)),ignition=ignition,N=N)
 return out
if __name__=='__main__':
 import argparse
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--nodes',type=int,default=60);p.add_argument('--propellant',type=float,default=140);p.add_argument('--warm',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--max-iter',type=int,default=700);a=p.parse_args()
 warm=dict(np.load(a.warm)) if a.warm else None
 r=solve(a.nodes,warm,prop=a.propellant,max_iter=a.max_iter);a.output.parent.mkdir(parents=True,exist_ok=True);np.savez(a.output,**r);print({k:r[k] for k in ['m0','dur1','gap','dur2']},flush=True)
