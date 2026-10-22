"""Cross-solver checks in ngspice PSpice compatibility mode, NOT Multisim tests.
No runtime control commands are added to the delivered Multisim .cir files.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os,json,hashlib,tempfile,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build_circuits import ROOT,CASES

DATA=ROOT/'results/data';LOGS=ROOT/'results/logs';FIG=ROOT/'results/figures'
for d in [DATA,LOGS,FIG]:d.mkdir(exist_ok=True,parents=True)
NG=os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice')
VECTORS='v(VOUT) v(ADC_IOUT) v(IL_BI) v(GH_MON) v(GL_MON) v(BOOT_MON) v(FAULT_N) i(VINPUT) v(XBUCK.VIN) v(XBUCK.V3A) v(XBUCK.SAFE) v(XBUCK.DUTY) v(XBUCK.L_RAW) v(XBUCK.V_CAP)'

def run(name):
    src=(ROOT/'circuits'/f'{name}.cir').read_text()
    digest=hashlib.sha256(src.encode()).hexdigest()
    cache=DATA/f'{name}.json'
    if cache.exists():
        result=json.loads(cache.read_text())
        if result.get('source_sha256')==digest:
            print('Reusing validated '+name,flush=True);return result
    print('Starting '+name,flush=True)
    with tempfile.TemporaryDirectory(prefix='gbuck-ms14-',dir='/tmp') as td:
        work=Path(td);raw=work/'trace.txt'
        ctl=f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} {VECTORS}\nquit\n.endc'
        modified='\n'.join(ctl if line.startswith('.PROBE ') else line for line in src.splitlines())+'\n'
        p=work/'test.cir';p.write_text(modified)
        with (LOGS/f'{name}.log').open('w') as f:
            done=subprocess.run([NG,'-D','ngbehavior=psa','-b',str(p)],stdout=f,stderr=subprocess.STDOUT)
        log=(LOGS/f'{name}.log').read_text()
        assert done.returncode==0 and raw.exists() and not any(s in log.lower() for s in ['error:','aborted','timestep too small']),log[-2000:]
        a=np.loadtxt(raw,skiprows=1)
    assert a[-1,0]>=CASES[name].get('stop',.08)*.999
    t=a[:,0];m=t>t[-1]-.005
    mean=lambda x:float(np.trapezoid(x[m],t[m])/(t[m][-1]-t[m][0]))
    il=(a[:,13]-a[:,14])/.025
    cfg=CASES[name];g=np.full(len(t),1/cfg['load'])
    event=cfg.get('event')
    if event=='load':g=np.where(t<.0800035,.05,np.where(t<.1100035,.125,.2))
    if event=='short':g=np.where(t<.0800035,.125,.125+1/.011)
    vin=np.full(len(t),cfg['vin'])
    if event=='line':vin=np.interp(t,[0,.080003,.080013],[15,15,25])
    io=a[:,1]*g;pin=-vin*a[:,8]
    active=(t>.025)&(t<(.079 if event else t[-1]))
    faults=t[(t>.005)&(a[:,7]<1)]
    final_latched=bool(a[-1,11]<1)
    result={'case':name,'source_sha256':digest,'solver':'ngspice 44.2 / ngbehavior=psa',
            'multisim14_execution_verified':False,'end_time_s':float(t[-1]),'data_rows':len(t),
            'vout_mean_V':mean(a[:,1]),'i_load_mean_A':mean(io),
            'il_mean_A':mean(il),'il_peak_after_20ms_A':float(il[t>.02].max()),
            'il_min_after_20ms_A':float(il[t>.02].min()),'i_load_peak_after_20ms_A':float(io[t>.02].max()),
            'vout_peak_after_20ms_V':float(a[t>.02,1].max()),
            'high_vgs_min_active_V':float(a[active&(a[:,4]>7),4].min()) if np.any(active&(a[:,4]>7)) else None,
            'bootstrap_min_active_V':float(a[active,6].min()),
            'v3a_mean_V':mean(a[:,10]),'fault_after_5ms_s':float(faults[0]) if len(faults) else None,
            'safe_final':float(a[-1,11]),'fault_latched_final':final_latched,
            'pin_equivalent_assumptions_W':mean(pin),'pout_W':mean(a[:,1]*io)}
    result['eta_equivalent_assumptions']=result['pout_W']/result['pin_equivalent_assumptions_W'] if cfg['load']<1e10 and event not in ['short','disable'] else None
    result['simultaneous_vgs_above_6V_samples_after_20ms']=int(np.sum((t>.02)&(a[:,4]>6.01)&(a[:,5]>6.01)))
    trace=a[::25]
    # Add computed IL to exported review samples.
    reduced=np.column_stack((trace,il[::25]))
    reduced=reduced[::max(1,len(reduced)//3000)]
    np.savetxt(DATA/f'{name}_sampled.csv',reduced,delimiter=',',header='t,vout,adc_iout,il_bi,vgs_h,vgs_l,vboot,fault_n,i_source,vin,v3a,safe,duty,l_raw,v_cap,il',comments='')
    np.savez_compressed(DATA/f'{name}.npz',trace=trace,last=a[t>t[-1]-.0001],il=il[::25])
    cache.write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)
    return result

def main():
    # Independent processes only; no Multisim GUI or Windows execution on this host.
    order=['04_25V_8ohm']+[x for x in CASES if x!='04_25V_8ohm']
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,order))
    results.sort(key=lambda r:r['case'])
    (DATA/'verification_summary.json').write_text(json.dumps(results,indent=2))
    with (DATA/'verification_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    for name in ['04_25V_8ohm','06_25V_load_steps','07_input_15_to_25V','08_25V_short_test','09_MCU_disable']:
        b=np.load(DATA/f'{name}.npz');a=b['trace'];il=b['il']
        fig,ax=plt.subplots(3,1,figsize=(10,7),layout='constrained')
        ax[0].plot(a[:,0]*1000,a[:,1]);ax[0].set_ylabel('Output (V)')
        ax[1].plot(a[:,0]*1000,il);ax[1].set_ylabel('Inductor current (A)')
        ax[2].plot(a[:,0]*1000,a[:,7],label='FAULT_N');ax[2].plot(a[:,0]*1000,a[:,11],label='SAFE');ax[2].legend()
        for x in ax:x.grid();x.set_xlabel('Time (ms)')
        fig.suptitle(name+' | ngspice cross-check; Multisim GUI unverified')
        fig.savefig(FIG/f'{name}.png',dpi=130);plt.close(fig)
    print('Completed 9 cross-solver runs (not native Multisim validation).',flush=True)

if __name__=='__main__':main()
