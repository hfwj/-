"""Cross-check a 4us pulse at 10us period over 20ms, without editing native files."""
from pathlib import Path
import hashlib,json,os,re,subprocess,tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ms14_project import ROOT,unpack,parse,inspect
from stabilize_transient import STABLE,analysis_options
from verify_driver import NG,DATA,LOGS,FIG
from verify_power_stage import power_stage_source


def time_mean(a,column,start,stop):
    segment=a[(a[:,0]>=start)&(a[:,0]<=stop)]
    assert len(segment)>2
    return float(np.trapezoid(segment[:,column],segment[:,0])/(segment[-1,0]-segment[0,0]))


def main():
    xml,_=unpack(STABLE.read_bytes());root=parse(xml);inspect(root)
    options=analysis_options(xml)
    source=power_stage_source(root)
    pattern=r'(?m)^V3 ([^\n]*?)PULSE\(([^)]+)\)$'
    match=re.search(pattern,source);assert match
    pulse=match[2].split();assert len(pulse)==7 and pulse[5]=='1u' and pulse[6]=='10u'
    pulse[5]='4u'
    source=source[:match.start()]+f'V3 {match[1]}PULSE('+ ' '.join(pulse)+')'+source[match.end():]
    values={key:options[key]['value'] for key in ['reltol','abstol','vntol','chgtol']}
    assert all(options[key]['enabled'] for key in values)
    source+='\n.options method=trap itl4=100 '+' '.join(f'{key}={value}' for key,value in values.items())+'\n.tran 50n 20m 0 50n\n'
    case='startup_40pct_20ms'
    for directory in [DATA,LOGS,FIG]:directory.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gbuck-40pct-') as td:
        work=Path(td);init=work/'init';init.mkdir();library=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(library/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        raw=work/'trace.txt';net=work/'test.cir'
        control=f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(1) v(13) v(4) v(11,15) v(15) v(7) v(14,15) i(l1)\nquit\n.endc\n.end\n'
        net.write_text(source+control,encoding='ascii')
        try:
            run=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],env=dict(os.environ,SPICE_SCRIPTS=str(init)),
                               capture_output=True,text=True,timeout=180)
            log=run.stdout+run.stderr;returncode=run.returncode
        except subprocess.TimeoutExpired as exc:
            log=(exc.stdout or b'').decode(errors='replace')+(exc.stderr or b'').decode(errors='replace')+'\nERROR: diagnostic timeout\n';returncode=None
        (LOGS/f'{case}.log').write_text(log)
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,9))
    errors=[line for line in log.splitlines() if any(word in line.lower() for word in ['aborted','error:','timestep too small'])]
    completed=bool(returncode==0 and len(a)>1000 and a[-1,0]>=.02*.999 and not errors)
    result={'date':'2026-10-24','case':case,'solver':'ngspice 44.2 / ngbehavior=psa',
            'native_multisim_execution_verified':False,'fuse_trip_simulation':False,
            'source_project_sha256':hashlib.sha256(STABLE.read_bytes()).hexdigest(),
            'solver_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'source_changes_only_for_cross_solver':['V3 PW 1us -> 4us','Transient end time 5ms -> 20ms'],
            'native_project_modified':False,'open_loop':True,'duty_ratio':.4,
            'requested_end_time_s':.02,'actual_end_time_s':float(a[-1,0]) if len(a) else None,
            'data_rows':len(a),'full_transient_completed':completed,'failure_messages':errors,
            'ideal_LC_period_s':float(2*np.pi*np.sqrt(220e-6*480e-6)),
            'limitations':['Relaxed tolerances for functional troubleshooting','Modified IR2104 compatibility model',
                           'No closed-loop CV/CC or native 40-percent project verification','No physical switching-loss or stress validation']}
    if len(a):
        assert np.isfinite(a).all()
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//4000)),len(a)-1])
        np.savetxt(DATA/f'{case}_sampled.csv',a[take],delimiter=',',comments='',
                   header='time_s,PWM_V,GL_V,VOUT_V,VGS_H_V,SW_V,VIN_at_Q1D_V,VBOOT_V,IL_A')
        # Retain every sample around the first 5ms and the final 50us for timing review.
        selected=a[(a[:,0]<=.005)|(a[:,0]>=.01995)]
        np.savez_compressed(DATA/f'{case}_startup_and_tail.npz',trace=selected)
        result['retained_full_resolution_windows_s']=[[0,.005],[.01995,.02]]
        result['VOUT_max_V']=float(a[:,3].max());result['IL_max_A']=float(a[:,8].max())
        initial=a[(a[:,0]>=.002)&(a[:,0]<=.005)]
        imax=int(np.argmax(initial[:,3]));result['first_5ms_VOUT_peak']={'time_s':float(initial[imax,0]),'V':float(initial[imax,3])}
        result['VOUT_near_5ms_V']=float(a[np.argmin(abs(a[:,0]-.005)),3])
    if completed:
        result['last_2ms_time_means']={label:time_mean(a,col,.018,.02) for col,label in [(3,'VOUT_V'),(6,'VIN_at_Q1D_V'),(8,'IL_A')]}
        result['last_ms_VOUT_time_means_V']=[time_mean(a,3,.018,.019),time_mean(a,3,.019,.02)]
        fig,axes=plt.subplots(3,1,figsize=(10,8))
        axes[0].plot(a[:,0]*1e3,a[:,3],lw=1);axes[0].axhline(10,ls='--',color='gray',lw=.7)
        axes[0].set(xlabel='Time / ms',ylabel='VOUT / V',title='40% open-loop startup; dashed line is 10 V reference only')
        short=a[(a[:,0]>=.002)&(a[:,0]<=.005)]
        axes[1].plot(short[:,0]*1e3,short[:,3],lw=1);axes[1].set(xlabel='Time / ms',ylabel='VOUT / V',title='First 3 ms after PWM begins')
        axes[2].plot(a[:,0]*1e3,a[:,8],lw=.7);axes[2].set(xlabel='Time / ms',ylabel='Inductor current / A')
        for ax in axes:ax.grid(alpha=.3)
        fig.suptitle('ngspice cross-check only; native screenshot is separate evidence')
        fig.tight_layout();fig.savefig(FIG/f'{case}.png',dpi=150);plt.close(fig)
    (DATA/f'{case}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if not completed:raise SystemExit('Incomplete run retained as incomplete, not passed')


if __name__=='__main__':main()
