"""Cross-check the startup solver revision; native Multisim is not launched."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,subprocess,tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ms14_project import ROOT,DEST,unpack,parse,inspect
from stabilize_transient import STABLE,analysis_options
from verify_driver import NG,DATA,LOGS,FIG
from verify_power_stage import power_stage_source


def run_case(case,path,tmax,init):
    xml,_=unpack(path.read_bytes());root=parse(xml);inspect(root)
    options=analysis_options(xml)
    method=options['method']['value'] if options['method']['enabled'] else 'trap'
    if method=='trapezoidal':method='trap'
    reltol=options['reltol']['value'] if options['reltol']['enabled'] else '0.001'
    itl4=options['itl4']['value'] if options['itl4']['enabled'] else '10'
    absolute={k:options[k]['value'] for k in ['abstol','vntol','chgtol']}
    source=power_stage_source(root)+f'.options method={method} reltol={reltol} abstol={absolute["abstol"]} vntol={absolute["vntol"]} chgtol={absolute["chgtol"]} itl4={itl4}\n.tran {tmax} 0.005 0 {tmax}\n'
    with tempfile.TemporaryDirectory(prefix='gbuck-startup-') as td:
        work=Path(td);raw=work/'trace.txt';net=work/'test.cir'
        ctl=f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(1) v(13) v(4) v(11,15) v(15) v(14,15) i(l1)\nquit\n.endc\n.end\n'
        net.write_text(source+ctl,encoding='ascii')
        try:
            p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],capture_output=True,text=True,
                             env=dict(os.environ,SPICE_SCRIPTS=str(init)),timeout=120)
            log=p.stdout+p.stderr
        except subprocess.TimeoutExpired as exc:
            log=(exc.stdout or b'').decode(errors='replace')+(exc.stderr or b'').decode(errors='replace')+'\nERROR: diagnostic timeout\n'
            p=None
        (LOGS/f'{case}.log').write_text(log)
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,8))
    errors=[s for s in log.splitlines() if any(w in s.lower() for w in ['aborted','error:','timestep too small'])]
    completed=bool(p is not None and p.returncode==0 and len(a)>1000 and a[-1,0]>=.005*.999 and not errors)
    result={'case':case,'solver':'ngspice 44.2 / ngbehavior=psa',
            'native_multisim_execution_verified':False,'fuse_trip_simulation':False,
            'project_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'solver_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'method':method,'reltol':float(reltol),'absolute_tolerances':{k:float(v) for k,v in absolute.items()},'itl4':int(itl4),'TMAX_s':float(tmax),
            'requested_end_time_s':.005,'actual_end_time_s':float(a[-1,0]) if len(a) else None,
            'data_rows':len(a),'full_transient_completed':completed,'failure_messages':errors}
    if len(a):
        assert np.all(np.isfinite(a))
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//2000)),len(a)-1])
        np.savetxt(DATA/f'{case}_sampled.csv',a[take],delimiter=',',comments='',
                   header='time_s,PWM_V,GL_V,VOUT_V,VGS_H_V,SW_V,VBOOT_V,IL_A')
        if completed:
            tail=a[a[:,0]>=.0045]
            result['last_half_ms_VOUT_time_mean_V']=float(np.trapezoid(tail[:,3],tail[:,0])/(tail[-1,0]-tail[0,0]))
            result['last_half_ms_VOUT_range_V']=[float(tail[:,3].min()),float(tail[:,3].max())]
            result['VOUT_at_5ms_V']=float(a[-1,3])
            result['GL_range_V']=[float(a[:,2].min()),float(a[:,2].max())]
            result['VGS_H_range_V']=[float(a[:,4].min()),float(a[:,4].max())]
            result['SW_range_V']=[float(a[:,5].min()),float(a[:,5].max())]
            np.savez_compressed(DATA/f'{case}.npz',trace=a)
    (DATA/f'{case}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result,a


def main():
    for directory in [DATA,LOGS,FIG]:directory.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gbuck-startup-init-') as td:
        init=Path(td);library=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(library/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        specs=[('startup_before_options',DEST,'5e-8'),('startup_full_tolerance',STABLE,'5e-8'),
               ('startup_full_tolerance_half_step',STABLE,'2.5e-8')]
        with ThreadPoolExecutor(max_workers=3) as pool:
            rows=list(pool.map(lambda spec:run_case(*spec,init),specs))
    assert not rows[0][0]['full_transient_completed']
    assert all(r['full_transient_completed'] for r,_ in rows[1:]),'Do not label an incomplete run as passing'
    # Validate the averaged output against a finer integration step, not point density.
    coarse,fine=[r['last_half_ms_VOUT_time_mean_V'] for r,_ in rows[1:]]
    relative=abs(coarse-fine)/abs(fine);assert relative<.02,relative
    summary={'date':'2026-10-24','scope':'Open-loop functional transient only; relaxed numerical tolerance',
             'native_multisim_execution_verified':False,'results':[r for r,_ in rows],
             'halving_TMAX_last_half_ms_VOUT_time_mean_relative_change':relative,
             'hardware_models_sources_unchanged_between_native_revisions':True,
             'user_reported_native_failure':{'evidence':'Screenshot in conversation, not an exported solver log',
                 'time_s':.00200002,'timestep_s':6.25e-18,'reported_branch':'vfi1:xq2#branch',
                 'completed':False},
             'limitations':['F1 replaced by 1mOhm conducting resistance in ngspice only',
                            'No native Multisim execution in this environment',
                            'Not validation of efficiency, switching loss, stress peaks, or G题 closed-loop requirements']}
    (DATA/'startup_solver_verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    a=rows[1][1]
    fig,axes=plt.subplots(3,1,figsize=(10,8))
    axes[0].plot(a[:,0]*1e3,a[:,3],lw=1);axes[0].set(xlabel='Time / ms',ylabel='VOUT / V',title='Open-loop output; PWM begins at 2 ms')
    tail=a[(a[:,0]>=.00495)&(a[:,0]<=.005)]
    axes[1].plot(tail[:,0]*1e3,tail[:,2],label='Low-side VGS',lw=1)
    axes[1].plot(tail[:,0]*1e3,tail[:,4],label='High-side VGS',lw=1)
    axes[1].set(xlabel='Time / ms',ylabel='Gate-source / V');axes[1].legend()
    axes[2].plot(tail[:,0]*1e3,tail[:,5],lw=1);axes[2].set(xlabel='Time / ms',ylabel='SW / V')
    for ax in axes:ax.grid(alpha=.3)
    fig.suptitle('ngspice cross-check: four relaxed tolerances (not a Multisim screenshot)')
    fig.tight_layout();fig.savefig(FIG/'startup_full_tolerance_crosscheck.png',dpi=150);plt.close(fig)
    print('Half-step mean-output relative change:',relative)


if __name__=='__main__':main()
