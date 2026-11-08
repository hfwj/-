from pathlib import Path
import casadi as ca
import numpy as np
import json,math
R=6371.;MU=398600.4418;G0=9.80665;VE=330*G0;A=math.pi*7**2/4
# Exact lower-atmosphere layer recurrence, symbolic geometric altitude.
HB=[0,11000,20000,32000,47000,51000,71000,84852];L=[-.0065,0,.001,.0028,0,-.0028,-.002]
base=[(288.15,101325.)]
for i,l in enumerate(L[:-1]):
 t,p=base[-1];dh=HB[i+1]-HB[i];tt=t+l*dh
 pp=p*math.exp(-G0*dh/(287.05307204706463*t)) if l==0 else p*(t/tt)**(G0/(287.05307204706463*l))
 base.append((tt,pp))
def density(h):
 z=h*1000;H=6356766*z/(6356766+z);rho=0
 for i in range(len(L)):
  tb,pb=base[i];l=L[i];t=tb+l*(H-HB[i]);t=ca.fmax(t,100)
  p=pb*ca.exp(-G0*(H-HB[i])/(287.05307204706463*tb)) if l==0 else pb*(tb/t)**(G0/(287.05307204706463*l))
  rho=ca.if_else(H>=HB[i],p/(287.05307204706463*t),rho)
 Htop=84852.;tb,pb=base[-1];tt=tb+L[-1]*(Htop-HB[-2]);pt=pb*(tb/tt)**(G0/(287.05307204706463*L[-1]));rhotop=pt/(287.05307204706463*tt);ztop=6356766*Htop/(6356766-Htop)
 return ca.if_else(z<=ztop,rho,rhotop*ca.exp(-(z-ztop)/7000))


def startup(t):
 if t<.5:return 0.
 if t<=1.5:return t-.5
 return 1.1-.1*math.exp(-(t-1.5)/.1)
