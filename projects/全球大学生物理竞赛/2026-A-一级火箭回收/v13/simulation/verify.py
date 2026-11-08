"""Checks compare independently implemented units/coordinates, not saved expected curves."""
import numpy as np,casadi as ca,json,math
from pathlib import Path
from solve7 import f,pack
from replay import Replay,R,MU,VE,wind,startup,decay
BASE=Path(__file__).resolve().parent.parent;w=dict(np.load(BASE/'results/data/optimized_controls.npz'));rr=Replay(w)
x=ca.MX.sym('x',6);u=ca.MX.sym('u',4);t=ca.MX.sym('t');fn=ca.Function('check',[x,u,t],[f(x,u,t)])
rng=np.random.default_rng(20261108);err=[]
for _ in range(80):
 h=rng.uniform(100,68000);vt=rng.uniform(2,1700);vr=-rng.uniform(2,800);m=rng.uniform(135000,270000);theta=rng.uniform(-1.4,.1);om=rng.uniform(-.05,.05);tt=rng.uniform(rr.ig+1.6,rr.e1);phi=rng.uniform(0,.05);er=np.array([math.sin(phi),math.cos(phi)]);et=np.array([math.cos(phi),-math.sin(phi)]);y=np.r_[(R+h)*er,vt*et+vr*er,m,theta+phi,om];us,a,de=rr.control(tt);z=np.array([us.sum(),np.dot(a,us),np.dot(a*a,us),de]);polar=np.array(fn(np.array([h/1000,vt/1000,vr/1000,m/1000,theta,om]),z,tt)).ravel()*np.array([1000,1000,1000,1000,1,1]);cart=rr.rhs(False)(tt,y);dvt=np.dot(cart[2:4],et)-vr*vt/(R+h);dvr=np.dot(cart[2:4],er)+vt*vt/(R+h);conv=np.r_[vr,dvt,dvr,cart[4],om-vt/(R+h),cart[6]];err.append(np.max(np.abs(conv-polar)))
assert max(err)<1e-4,max(err)
# Actual individual engine rates and reconstructed command in the steady enabled phases.
act=[]
for U,dur,n in [(w['U1'],float(w['dur1']),7),(w['U2'],float(w['dur2']),3)]:
 a=np.array([0,1,.5,-.5,-1,-.5,.5] if n==7 else[0,1,-1]);vals=U[0][None,:]+a[:,None]*U[1][None,:];rate=np.diff(vals)/ (dur/(U.shape[1]-1));cmd0=vals[:,:-1]+.1*rate;cmd1=vals[:,1:]+.1*rate;act.append(dict(n=n,actual_min=float(vals.min()),actual_max=float(vals.max()),rate_max=float(abs(rate).max()),command_min=float(min(cmd0.min(),cmd1.min())),command_max=float(max(cmd0.max(),cmd1.max())),gimbal_max_deg=float(abs(np.degrees(U[2])).max()),gimbal_rate_deg_s=float(abs(np.degrees(np.diff(U[2])/(dur/(U.shape[1]-1)))).max())))
 assert vals.min()>=.3-1e-6 and vals.max()<=1.1+1e-6
 assert abs(rate).max()<=1+1e-6 and min(cmd0.min(),cmd1.min())>=.3-1e-6 and max(cmd0.max(),cmd1.max())<=1.1+1e-6
 assert act[-1]['gimbal_max_deg']<=6.001 and act[-1]['gimbal_rate_deg_s']<=20.001
# Startup/shutdown quadrature convergence and nonnegative tail.
assert startup(.5)==0 and abs(startup(1.5)-1)<1e-10
for val in [.3,.7,1.1]:
 ts=np.linspace(0,5,100001);ar=decay(val,ts);assert ar.min()>=0
 expected=.5*max(val-.1,0)*(val+min(val,.1))+.1*min(val,.1)
 assert abs(np.trapezoid(ar,ts)-expected)<1e-7
out=dict(independent_rhs_random_cases=80,max_component_absolute_error=max(err),actuator_checks=act,startup_shutdown_checks='PASS',limitations='Does not validate actual aerodynamics, mass properties, wind forecast, hardware or 3D control.')
json.dump(out,open(BASE/'results/data/verification.json','w'),indent=2);print(json.dumps(out,indent=2))
