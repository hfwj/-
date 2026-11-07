"""Independent arithmetic and illustrative CC model, not a TPS54302 manufacturer model."""
import json,math,csv
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/data';FIG=ROOT/'results/figures'
DATA.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
R1,R2,R3,R4=100e3,5.49e3,56e3,10e3
VF=.596;alpha=R1/R3;K=VF*(1+R1/R2+alpha)
VA=(K-10)/alpha
ripple_i=10*(1-10/25)/(22e-6*400e3)
out={'evidence':'Independent arithmetic plus assumed averaged voltage-plant model, NOT hardware validation','K_V':K,'alpha':alpha,'DAC_A_10V_V':VA,'DAC_A_7V_V':(K-7)/alpha,'ripple_A_pp_at_25_to_10':ripple_i,'ripple_44uF_V_pp_ideal':ripple_i/(8*400e3*44e-6),'ripple_22uF_V_pp_ideal':ripple_i/(8*400e3*22e-6),'new_series_1k_error_at_10V_V':VF*(1+R1/R2+R1/57e3)-R1/57e3*VA-10,'CC_0p98A_Pout_R8_W':.98**2*8,'CC_0p95A_Pout_R8_W':.95**2*8,'loss_budget_85pct_at_0p95A_W':.95**2*8*(1/.85-1),'aux_input_W_for_3p3V_50mA_eff80pct':3.3*.05/.8,'step_I_20_to_8_initial_A':10/(8+.05),'step_I_8_to_5_initial_A_at_0p95A':.95*(8+.05)/(5+.05),'A_G2_nominal_start_code':round(VA/.001),'B_G1_nominal_start_code':round(.95/.0005)}
# op-amp A idealized, output clipped to [0,3.27V], piecewise-linear D2 antiwindup.
# q = Vinverting - Vcomp; cap is between I_ERR and COMP; R13 from COMP to output.
# Diodes use Vf=0.2V, D2 Ron=100R; sensor gain 1V/A; R11C13=10us.
# Main Buck is replaced by an ASSUMED closed-loop voltage plant with variable tau.
# It is not a switching model; no ripple, enable soft-start, IC internal compensation, or slew-rate evidence.
RI,RF,RD=100e3,1e3,100.
ISET=.95

def opamp(vs,q):
 vo=vs-q+RF/RI*(vs-ISET)
 if vs-vo>.2:
  vo=((vs-ISET)/RI+(vs-q)/RF+(vs-.2)/RD)/(1/RF+1/RD)
 vo=max(0.,min(3.27,vo))
 vi=(ISET/RI+(q+vo)/RF)/(1/RI+1/RF)
 if vi>vo+.2:vi=(ISET/RI+(q+vo)/RF+(vo+.2)/RD)/(1/RI+1/RF+1/RD)
 return vo,vi

metrics=[];traces={}
for cap in [1e-6,220e-9,100e-9]:
 for tau in [50e-6,200e-6,1e-3]:
  vs0=10/(20+.05);vo0=max(0,vs0-.2+RD/RI*(vs0-ISET));q0=vs0-vo0
  state=np.array([10.,vs0,q0]);ts=[];ys=[]
  for a,b,rl in [(0,.02,20.),(.02,.62,8.),(.62,1.22,5.)]:
   def fun(t,y):
    v,vs,q=y;vo,vi=opamp(vs,q)
    vt=max(0.,min(25.,10.-R1/R4*max(vo-VF-.2,0.)))
    return [(vt-v)/tau,(v/(rl+.05)-vs)/10e-6,(vi-q-vo)/(RF*cap)]
   tx=np.linspace(a,b,max(50,int((b-a)/1e-4)+1))
   sol=solve_ivp(fun,(a,b),state,method='LSODA',t_eval=tx,rtol=1e-7,atol=1e-9,max_step=1e-3)
   assert sol.success
   state=sol.y[:,-1];ts.extend(sol.t);ys.extend((sol.y[0]/(rl+.05)).tolist())
  t=np.array(ts);i=np.array(ys)
  for name,step,end in [('20_to_8',.02,.62),('8_to_5',.62,1.22)]:
   mask=(t>=step)&(t<end);idx=np.flatnonzero(mask);err=abs(i[idx]-ISET)
   bad=np.flatnonzero(err>.02)
   settling=(t[idx[bad[-1]+1]]-step) if len(bad) and bad[-1]+1<len(idx) else 0. if not len(bad) else None
   metrics.append({'C14_F':cap,'assumed_tau_s':tau,'step':name,'peak_A':float(i[idx].max()),'final_A':float(i[idx][-1]),'settling_within_20mA_s':None if settling is None else float(settling)})
  if tau==200e-6:traces[str(cap)]=(t,i)
out['VFB_range_only_output_error_V'] = .015*(1+R1/R2+alpha)
assert .0048 < out['ripple_44uF_V_pp_ideal'] < .0049
assert .025 < out['new_series_1k_error_at_10V_V'] < .026
assert out['step_I_20_to_8_initial_A'] > 1.2
out['illustrative_model']=metrics
(DATA/'review_calculations.json').write_text(json.dumps(out,indent=2))
with open(DATA/'cc_model_summary.csv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
# plot is generated with standard scientific plotting, not an edited/generated photo.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(10,4.5))
for k,(t,i) in traces.items():ax.plot(t*1000,i,label=f'C14 = {float(k)*1e9:g} nF')
ax.axhline(1.,color='red',ls='--',lw=1,label='1 A')
ax.axhline(.95,color='gray',ls=':',lw=1,label='0.95 A target')
ax.set(xlabel='Time (ms)',ylabel='Load current (A)',title='Illustrative CC model only: assumed Buck voltage-loop tau = 0.2 ms')
ax.grid(alpha=.3);ax.legend();fig.tight_layout();fig.savefig(FIG/'cc_model_comparison.png',dpi=160)
print(json.dumps({k:v for k,v in out.items() if k!='illustrative_model'},indent=2))
print(json.dumps([m for m in metrics if m['assumed_tau_s']==.0002],indent=2))
