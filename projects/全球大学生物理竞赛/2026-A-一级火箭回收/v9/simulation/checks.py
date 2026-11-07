"""Analytic limits, coordinate/unit transformations, and negative input tests."""
from pathlib import Path
import sys,math,json,tempfile,hashlib
import numpy as np,casadi as ca
from scipy.integrate import solve_ivp
from audit import ROOT,SOURCE,R,MU,G,rho,validate
sys.path.insert(0,str(SOURCE/'simulation'))
from solve_candidate import f
from atmosphere_1976 import atmosphere

def run():
 result={};x=ca.MX.sym('x',4);u=ca.MX.sym('u',2);fun=ca.Function('audit_v8_rhs',[x,u],[f(x,u)])
 rng=np.random.default_rng(20261107);errors=[]
 for _ in range(200):
  h=rng.uniform(100,69999);vt=rng.uniform(-1700,1700);vr=rng.uniform(-1200,300);m=rng.uniform(131000,300000);T=rng.uniform(0,3.3e6);b=rng.uniform(-math.pi/2,math.pi/2);theta=rng.uniform(-1,1)
  er=np.array([math.sin(theta),math.cos(theta)]);et=np.array([math.cos(theta),-math.sin(theta)]);v=vt*et+vr*er;rr=(R+h)*er;speed=np.linalg.norm(v)
  D=.5*rho(h)*speed**2*.5*math.pi*49/4;a=-MU*rr/np.linalg.norm(rr)**3+(T*(math.cos(b)*er+math.sin(b)*et)-D*v/speed)/m
  expected=np.array([vr,a@et-vr*vt/(R+h),a@er+vt*vt/(R+h),-T/(320*G)])
  got=np.array(fun([h/1000,vt/1000,vr/1000,m/1000],[T/1e6,b])).ravel()*1000
  errors.append(max(abs(got-expected)))
 result['coordinate_rhs_max_absolute_error_mixed_SI']=max(errors);assert max(errors)<1e-8
 result['density_max_relative_error']=max(abs(rho(float(h))/atmosphere(float(h))['density_kg_m3']-1) for h in np.linspace(0,70000,1001));assert result['density_max_relative_error']<1e-10
 anchors=[(0,1.225),(11000,.36392),(20000,.088035),(32000,.013225),(47000,.0014275),(51000,.00086160)]
 result['rounded_geopotential_anchor_max_relerr']=max(abs(rho(6356766*H/(6356766-H))/expected-1) for H,expected in anchors);assert result['rounded_geopotential_anchor_max_relerr']<5e-5
 # Pure gravity: conservation laws and Cartesian/polar agreement.
 duration=123.;r0=R+70000;v0=6000/3.6
 def grav(t,y):
  h,vt,vr=y;rr=R+h;return [vr,-vr*vt/rr,-MU/rr**2+vt*vt/rr]
 sol=solve_ivp(grav,(0,duration),[70000,v0,0],rtol=1e-12,atol=1e-9,max_step=.1);h,vt,vr=sol.y;energy=.5*(vt*vt+vr*vr)-MU/(R+h);L=(R+h)*vt
 result['vacuum_max_energy_relerr']=float(max(abs(energy/energy[0]-1)));result['vacuum_max_angular_momentum_relerr']=float(max(abs(L/L[0]-1)));assert result['vacuum_max_energy_relerr']<1e-11 and result['vacuum_max_angular_momentum_relerr']<1e-11
 # Ideal rocket equation in vacuum, no gravity: independent analytic anchor.
 T=2.2e6;m0=200000.;dt=20.;ve=320*G
 z=solve_ivp(lambda t,y:[T/y[1],-T/ve],(0,dt),[0,m0],rtol=1e-12,atol=1e-10,max_step=.1).y[:,-1]
 expected_v=ve*math.log(m0/(m0-T*dt/ve));result['ideal_rocket_velocity_error_m_s']=float(abs(z[0]-expected_v));assert abs(z[0]-expected_v)<1e-7
 # Quadratic drag deceleration: analytic solution checks sign and speed scaling.
 k=.001;v0=400.;dt=10.
 z=solve_ivp(lambda t,y:[-k*y[0]*abs(y[0])],(0,dt),[v0],rtol=1e-12,atol=1e-11,max_step=.02).y[0,-1];result['quadratic_drag_velocity_error_m_s']=abs(z-v0/(1+k*v0*dt));assert result['quadratic_drag_velocity_error_m_s']<1e-7
 p=dict(np.load(SOURCE/'results/data/controls_N320.npz'));assert validate(p)
 result['negative_controls']=[]
 for name in ['beta_add_2pi','nan_throttle','wrong_shape','invalid_timing']:
  bad={k:v.copy() for k,v in p.items()}
  if name=='beta_add_2pi':bad['U1'][-1]+=2*math.pi;bad['U2'][-1]+=2*math.pi
  elif name=='nan_throttle':bad['U1'][0,0]=np.nan
  elif name=='wrong_shape':bad['U1']=bad['U1'][:,:-1]
  else:bad['toff']=bad['tf']
  try:validate(bad)
  except ValueError as e:result['negative_controls'].append(dict(name=name,rejected=True,reason=str(e)))
  else:raise AssertionError(name+' was not rejected')
 # Preserve all baseline artifacts; hashes also rule out accidental mutations.
 manifest=json.loads((SOURCE/'results/logs/sha256.json').read_text());result['v8_manifest_pass']=all(hashlib.sha256((SOURCE/k).read_bytes()).hexdigest()==v for k,v in manifest.items());assert result['v8_manifest_pass']
 return result
if __name__=='__main__':
 z=run();(ROOT/'results/data/checks.json').write_text(json.dumps(z,indent=2));print(json.dumps(z,indent=2))
