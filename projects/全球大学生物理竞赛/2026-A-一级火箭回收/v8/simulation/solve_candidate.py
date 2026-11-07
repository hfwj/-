from physics import density,R,MU,G0,VE,A,startup
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import casadi as ca,numpy as np,math

def off(u,d):
 a=ca.fmax(u-.1,0)
 return ca.if_else(d<=a,u-d,ca.fmin(u,.1)*ca.exp(-ca.fmax(d-a,0)/.1))
def f(x,u):
 h,vt,vr,m=x[0],x[1],x[2],x[3];T=u[0];b=u[1];V=ca.sqrt(vt*vt+vr*vr+1e-14);D=.5*density(h)*V**2*A*.5
 return ca.vertcat(vr,T/m*ca.sin(b)-D/m*vt/V-vr*vt/(R+h),T/m*ca.cos(b)-D/m*vr/V-MU/(R+h)**2+vt*vt/(R+h),-1000*T/VE)
def rk(x,ua,ub,dt,um=None):
 um=(ua+ub)/2 if um is None else um;k1=f(x,ua);k2=f(x+dt*k1/2,um);k3=f(x+dt*k2/2,um);k4=f(x+dt*k3,ub)
 return x+dt*(k1+2*k2+2*k3+k4)/6

def solve(N=40,warm=None,ignition_s=40):
 if not 0<=ignition_s<=95:raise ValueError("Ignition must be 0..95 seconds")
 if warm is None:warm=dict(np.load(ROOT/"references/initial_guess.npz"))
 start=ignition_s+1.6
 op=ca.Opti();X1=op.variable(4,N+1);X2=op.variable(4,N+1);U1=op.variable(3,N+1);U2=op.variable(2,N+1)
 m0=op.variable();toff=op.variable();tf=op.variable();dt1=(toff-start)/N;dt2=(tf-toff-6.6)/N
 op.subject_to(op.bounded(131,m0,400));op.subject_to(op.bounded(max(30,start+20),toff,300));op.subject_to(op.bounded(110,tf,450));op.subject_to(tf-toff>=26.6)
 x=ca.vertcat(70,6000/3.6/1000,0,m0)
 coast_steps=max(1,math.ceil(ignition_s*2))
 for i in range(coast_steps):x=rk(x,ca.vertcat(0,-math.pi/2),ca.vertcat(0,-math.pi/2),ignition_s/coast_steps)
 for i in range(64):x=rk(x,ca.vertcat(3*startup(i*.025),-math.pi/2),ca.vertcat(3*startup((i+1)*.025),-math.pi/2),.025,ca.vertcat(3*startup((i+.5)*.025),-math.pi/2))
 op.subject_to(X1[:,0]==x);op.subject_to(U1[:,0]==ca.vertcat(startup(1.6),startup(1.6),-math.pi/2))
 for X in [X1,X2]:
  op.subject_to(op.bounded(.0325,X[0,:],70));op.subject_to(op.bounded(-3,X[1:3,:],3));op.subject_to(op.bounded(130,X[3,:],400))
 op.subject_to(op.bounded(.3,U1[:2,:],1.1));op.subject_to(op.bounded(.3,U2[0,:],1.1))
 op.subject_to(op.bounded(-math.pi/2,U1[2,:],math.pi/2));op.subject_to(op.bounded(-math.pi/2,U2[1,:],math.pi/2))
 def check(x,u):
  q=.5*density(x[0])*(x[1]**2+x[2]**2)*1e6;D=q*A*.5/1e6
  op.subject_to(q<=47000);op.subject_to((u[0]+D)*1000/(x[3]*G0)<=3.9)
 def phase(X,U,dt,three):
  for k in range(N):
   for i in range(2 if three else 1):
    slope=(U[i,k+1]-U[i,k])/dt;op.subject_to(op.bounded(-1,slope,1))
    for j in [k,k+1]:op.subject_to(op.bounded(.3,U[i,j]+.1*slope,1.1))
   op.subject_to(op.bounded(-math.radians(4.9)*dt,U[-1,k+1]-U[-1,k],math.radians(4.9)*dt))
   def packed(u):return ca.vertcat(2*u[0]+(u[1] if three else 0),u[-1])
   xx=X[:,k]
   for j in range(4):
    a=j/4;b=(j+1)/4;ua=packed((1-a)*U[:,k]+a*U[:,k+1]);ub=packed((1-b)*U[:,k]+b*U[:,k+1]);check(xx,ua);xx=rk(xx,ua,ub,dt/4)
   op.subject_to(X[:,k+1]==xx)
  check(X[:,-1],packed(U[:,-1]))
 phase(X1,U1,dt1,True)
 # End the entry burn, command a 5 s shutdown interval, then restart the pair.
 # The 0.5 s ignition delay and 1.1 s response build-up are included in 6.6 s.
 x=X1[:,-1]
 def gap_u(d):
  pair=off(U1[0,-1],d) if d<=5.5 else startup(d-5)
  extra=off(U1[1,-1],d)
  b=U1[2,-1]+(U2[1,0]-U1[2,-1])*d/6.6
  return ca.vertcat(2*pair+extra,b)
 op.subject_to(op.bounded(-math.radians(4.9)*6.6,U2[1,0]-U1[2,-1],math.radians(4.9)*6.6))
 for i in range(132):
  a=i*.05;b=(i+1)*.05;ua=gap_u(a);ub=gap_u(b);check(x,ua);x=rk(x,ua,ub,.05,gap_u((a+b)/2))
  op.subject_to(op.bounded(.0325,x[0],70))
 op.subject_to(X2[:,0]==x);op.subject_to(U2[0,0]==startup(1.6))
 phase(X2,U2,dt2,False)
 op.subject_to(X2[0,-1]==.0325);op.subject_to(X2[1,-1]==0);op.subject_to(X2[2,-1]==-.001)
 op.subject_to(U2[1,-1]==0);op.subject_to(2*U2[0,-1]<=.95*X2[3,-1]*(MU/(R+.0325)**2));op.subject_to(X2[3,-1]>=130+.005*(m0-130)+2.2e6/VE/1000+.01)
 op.minimize(m0)
 if warm and 'X1' in warm:
  old=np.linspace(0,1,warm['X1'].shape[1]);q=np.linspace(0,1,N+1)
  for key,var in [('X1',X1),('X2',X2),('U1',U1),('U2',U2)]:op.set_initial(var,np.array([np.interp(q,old,row) for row in warm[key]]))
  op.set_initial(m0,warm['m0']);op.set_initial(tf,warm['tf']);op.set_initial(toff,warm['toff'])
 op.solver('ipopt',{'expand':True,'print_time':False},{'max_iter':2000,'tol':1e-8,'print_level':0})
 sol=op.solve();return {**{k:np.array(sol.value(v)) for k,v in [('X1',X1),('X2',X2),('U1',U1),('U2',U2)]},'m0':float(sol.value(m0)),'tf':float(sol.value(tf)),'toff':float(sol.value(toff)),'N':N,'ignition_s':ignition_s}
if __name__=='__main__':
 import argparse,json
 from atmosphere_1976 import atmosphere
 parser=argparse.ArgumentParser();parser.add_argument('--nodes',type=int,nargs='+',default=[80,160,320]);parser.add_argument('--ignition',type=float,default=40,help='Fixed initial ignition command seconds; compare separate runs')
 args=parser.parse_args();out=ROOT/'results/data';out.mkdir(parents=True,exist_ok=True)
 z=ca.MX.sym('h');rho=ca.Function('rho_check',[z],[density(z)])
 error=max(abs(float(rho(h/1000))/atmosphere(float(h))['density_kg_m3']-1) for h in np.linspace(0,70000,1001));assert error<1e-9
 warm=None;history=[]
 for n in args.nodes:
  if n<20:raise ValueError('Use at least 20 intervals per powered phase')
  result=solve(n,warm,args.ignition);np.savez(out/f'controls_N{n}.npz',**result);warm=result
  history.append({k:result[k] for k in ['N','m0','tf','toff','ignition_s']})
  (out/'optimization_history.json').write_text(json.dumps(dict(method='IPOPT local NLP; no global minimum guarantee',density_max_relative_error=error,history=history),indent=2))
  print(history[-1],flush=True)
