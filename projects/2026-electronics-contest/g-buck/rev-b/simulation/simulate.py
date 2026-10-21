"""PDF-derived switching model; all non-PDF assumptions are recorded in README.
Run: python simulate.py (requires ngspice, numpy, matplotlib).
"""
from pathlib import Path
import subprocess, os, json, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
NETLISTS=ROOT/"simulation"/"netlists"
DATA=ROOT/"results"/"data"
LOGS=ROOT/"results"/"logs"
FIGURES=ROOT/"results"/"figures"
REPORTS=ROOT/"reports"
DOWNLOADS=ROOT/"downloads"
NG=os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice')
for directory in [NETLISTS, DATA, LOGS, FIGURES, REPORTS, DOWNLOADS]:
    directory.mkdir(parents=True,exist_ok=True)

def deck(name, vin=25, load=8, scenario='steady', freq=100000, stop=.04, step='100n', event=.08):
    vinexpr = f'pwl(0 15 {event} 15 {event+1e-5} 25)' if scenario=='line' else str(vin)
    gexpr = {'load':f'(time<{event} ? 0.05 : (time<{event+.03} ? 0.125 : 0.2))',
             'release':f'(time<{event} ? 0.125 : 1e-12)',
             'short':f'(time<{event} ? 0.125 : 100)'}.get(scenario,str(1/load))
    return f'''* RevB PDF-derived synchronous Buck; NOT vendor MOSFET/MCU model
.param F={freq} T={{1/F}} DT=520n
Vsource ext 0 {vinexpr}
Rfuse ext fused 0.02
Dinput fused shunt SS56_ASSUMED
Rin shunt vin 0.05
C1 vin 0 470u
C2 vin 0 1u
Shigh vin sw gh 0 SWMOS
Slow sw 0 gl 0 SWMOS
Dhigh sw vin BODY_ASSUMED
Dlow 0 sw BODY_ASSUMED
L1 sw lr 220u
Rdcr lr lraw 0.15
Ril lraw vcap 0.025
C3 vcap ce 470u
Resr ce 0 0.08
C4 vcap 0 10u
Rout vcap out 0.05
Rbleed out 0 2200
Rdivider out 0 11000
Bload out 0 I=V(out)*{gexpr}
* Cascaded continuous PI proxy: outer voltage sets bounded inductor current.
* Back-calculation antiwindup. These parameters are proposed, NOT supplied firmware.
Bvset vset 0 V=10*min(1,time/10m)
Bev ev 0 V=V(vset)-V(out)
Bff ff 0 V=(time>1m && time<10m) ? 0.48 : 0
Biref ir 0 V=max(-0.3,min(1,0.5*V(ev)+V(xv)+V(ff)))
Cxv xv 0 1 ic=0
Bxv 0 xv I=50*V(ev)+500*(V(ir)-(0.5*V(ev)+V(xv)+V(ff)))
Bils ils 0 V=I(L1)
* Functional hardware protection proxy; delay is an assumption, not a vendor timing model.
Rprotect ils ilp 1k
Cprotect ilp 0 400p
Btrip tripraw 0 V=(time>1m && (abs(V(ilp))>1.8 || V(out)>11)) ? 1 : 0
Rtrip tripraw trip 1k
Ctrip trip 0 1.3n
Clatch latch 0 1 ic=0
Blatch 0 latch I=(V(trip)>0.5 && V(latch)<1) ? 1e6 : 0
Rfilter ils ilf 1k
Cfilter ilf 0 4.7n
Bei ei 0 V=V(ir)-V(ilf)
Braw raw 0 V=V(vcap)/max(V(vin),1)+0.15*V(ei)+V(xi)
Bduty duty 0 V=max(0.08,min(0.88,V(raw)))
Cxi xi 0 1 ic=0
Bxi 0 xi I=200*V(ei)+1000*(V(duty)-V(raw))
Bsaw saw 0 V=(time/T-floor(time/T))
* 1ms auxiliary/boot precharge; then PWM. Gate outputs have 47ns RC assumptions.
Bgh ghraw 0 V=(V(latch)<0.5 && time>1m && V(saw)>DT/T && V(saw)<V(duty)) ? 1 : 0
Bgl glraw 0 V=(V(latch)<0.5 && (time<1m || V(saw)>V(duty)+DT/T)) ? 1 : 0
Rgh ghraw gh 1k
Cgh gh 0 47p
Rgl glraw gl 1k
Cgl gl 0 47p
.model SWMOS SW(Ron=0.044 Roff=1e9 Vt=0.5 Vh=0)
.model BODY_ASSUMED D(Is=1n N=1.5 Rs=0.03)
.model SS56_ASSUMED D(Is=2u N=1.4 Rs=0.025)
.options reltol=0.001 abstol=1n method=gear
.control
set noaskquit
set wr_singlescale
set wr_vecnames
tran {step} {stop} 0 {step} uic
wrdata {DATA/f'{name}.dat'} v(out) i(L1) v(vin) v(duty) v(ir) v(ext) i(Vsource) v(sw) v(vcap) v(latch)
quit
.endc
.end
'''

def run(name, **kwargs):
    net=NETLISTS/f'{name}.cir'; net.write_text(deck(name,**kwargs))
    log=LOGS/f'{name}.log'
    with log.open('w') as f:
        p=subprocess.run([NG,'-b',str(net)],stdout=f,stderr=subprocess.STDOUT)
    if p.returncode or 'Error:' in log.read_text(): raise RuntimeError(log.read_text()[-2000:])
    a=np.loadtxt(DATA/f'{name}.dat',skiprows=1)
    assert a[-1,0]>=kwargs.get('stop',.04)*.999
    t=a[:,0]; mask=t>t[-1]-.005
    avg=lambda x:float(np.trapezoid(x[mask],t[mask])/(t[mask][-1]-t[mask][0]))
    vl=a[:,1]; il=a[:,2]
    g=1/kwargs.get('load',8)
    sc=kwargs.get('scenario','steady'); event=kwargs.get('event',.08)
    ga=np.full(len(t),g)
    if sc=='load': ga=np.where(t<event,.05,np.where(t<event+.03,.125,.2))
    if sc=='release': ga=np.where(t<event,.125,1e-12)
    if sc=='short': ga=np.where(t<event,.125,100)
    io=vl*ga
    summary={'case':name,'vin':kwargs.get('vin',25),'load':kwargs.get('load',8),
      'vout_mean':avg(vl),'vout_rms':float(np.sqrt(avg(vl*vl))),
      'i_load_mean':avg(vl)*g,'il_mean':avg(il),
      'il_min':float(il[mask].min()),'il_max':float(il[mask].max()),
      'vout_pp':float(np.ptp(vl[mask])),'vout_peak_startup':float(vl[t<.02].max()),
      'fault_latched':bool(a[-1,10]>.5),'il_abs_peak_all':float(np.abs(il).max()),
      'pout':avg(vl*io),'pin_model':avg(-a[:,6]*a[:,7]),
      'i_load_peak_all':float(io.max()),'i_load_mean_actual':avg(io),
      'fault_time':float(t[a[:,10]>.5][0]) if np.any(a[:,10]>.5) else None}
    summary['eta_power_stage_model']=summary['pout']/summary['pin_model'] if kwargs.get('load',8)<1e10 else None
    if kwargs.get('scenario','steady')!='steady': summary['i_load_mean']=None
    # Downsample full trajectory, retaining a high-resolution final 100us.
    np.savez_compressed(DATA/f'{name}.npz',trace=a[::20],last=a[t>t[-1]-.0001],event=a[np.abs(t-event)<.0001])
    (DATA/f'{name}.dat').unlink()
    print(json.dumps(summary),flush=True)
    return summary

def main():
    results=[]
    for v in [15,20,25]:
        for r in [1e12,20,8,5]:
            results.append(run(f'vin{v}_r{r:g}',vin=v,load=r))
    for name,kw in [('load_steps',dict(scenario='load',stop=.14,load=20)),
                    ('line_step',dict(scenario='line',stop=.12,load=20)),
                    ('load_release',dict(scenario='release',stop=.12,load=8)),
                    ('short_no_software',dict(scenario='short',stop=.10,load=8))]:
        results.append(run(name,**kw))
    results.append(run('convergence_50ns',vin=25,load=8,step='50n'))
    (DATA/'summary.json').write_text(json.dumps(results,indent=2))
    with (DATA/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)
    fig,ax=plt.subplots(3,1,figsize=(10,9),layout='constrained')
    for name,label in [('load_steps','Load 20 -> 8 -> 5 ohm'),('line_step','Input 15 -> 25 V'),('load_release','Load 8 ohm -> open')]:
        a=np.load(DATA/f'{name}.npz')['trace']
        ax[0].plot(a[:,0]*1e3,a[:,1],label=label)
        ax[1].plot(a[:,0]*1e3,a[:,2],label=label)
        ax[2].plot(a[:,0]*1e3,a[:,4],label=label)
    for x,y in zip(ax,['Output (V)','Inductor current (A)','Duty command']):
        x.set(xlabel='Time (ms)',ylabel=y);x.grid();x.legend(fontsize=8)
    fig.savefig(FIGURES/'transients.png',dpi=160);plt.close(fig)

if __name__=='__main__':main()
