"""Run extracted delivery netlists; never substitute inside vendor subcircuits."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys,hashlib,json,os,subprocess,tempfile,argparse,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from build_projects import ROOT,SOURCE,CASES,output_path,extract_netlist
from ms14_project import unpack,parse,components
from verify_power_stage import power_stage_source
from verify_driver import NG

DATA=ROOT/'results/data';LOGS=ROOT/'results/logs';FIG=ROOT/'results/figures'
COLUMNS=['time_s','VOUT_V','IL_A','VREF_V','IREF_A','DUTY','IL_FILTERED_A','PWM_V','VGS_H_V','VGS_L_V','VIN_V','VCAP_V','IOUT_A']


def mean(a,col,start,stop):
    part=a[(a[:,0]>=start)&(a[:,0]<=stop)];assert len(part)>2
    return float(np.trapezoid(part[:,col],part[:,0])/(part[-1,0]-part[0,0]))


def run_case(case,init):
    path=output_path(case);source=extract_netlist(path)
    source_project=path.read_bytes();rows={r['display_ref']:r for r in components(parse(unpack(source_project)[0]))}
    assert float(rows['V1']['parameters'][1])==case['vin']
    if case['load']!='steps':assert float(rows['RL']['parameters'][1])==float(case['load'])
    baseline=power_stage_source(parse(unpack(SOURCE.read_bytes())[0]))
    # A top-level load named RL must never overwrite the internal MOSFET RL.
    vendor_tail=baseline[baseline.index('.SUBCKT'):]
    assert vendor_tail in source,'Embedded vendor model text changed in extraction'
    assert '\nRL 5 10 1\n' in source
    source_hash=hashlib.sha256(source.encode()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='gbuck-delivery-'+case['id']+'-') as td:
        work=Path(td);raw=work/'trace.txt';net=work/'test.cir'
        ctl=f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(4) i(l1) v(xctrl.ref) v(xctrl.iref) v(xctrl.duty) v(xctrl.ilf) v(1) v(11,15) v(13) v(7) v(3)\nquit\n.endc\n.end\n'
        net.write_text(source+ctl,encoding='ascii')
        try:
            p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],env=dict(os.environ,SPICE_SCRIPTS=str(init)),capture_output=True,text=True,timeout=480)
            log=p.stdout+p.stderr;returncode=p.returncode
        except subprocess.TimeoutExpired as exc:
            log=(exc.stdout or b'').decode(errors='replace')+(exc.stderr or b'').decode(errors='replace')+'\nERROR: diagnostic timeout\n';returncode=None
        (LOGS/f'{case["id"]}.log').write_text(log)
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,12))
    errors=[line for line in log.splitlines() if any(w in line.lower() for w in ['too small','error:','aborted'])]
    stop=float(case['stop']);completed=bool(returncode==0 and len(a)>1000 and a[-1,0]>=stop*.999 and not errors)
    record={**case,'solver':'ngspice 44.2 / ngbehavior=psa','native_multisim_execution_verified':False,
            'project_sha256':hashlib.sha256(source_project).hexdigest(),'solver_source_sha256':source_hash,
            'vendor_model_text_preserved_in_extracted_source':True,
            'requested_end_time_s':stop,'actual_end_time_s':float(a[-1,0]) if len(a) else None,
            'data_rows':len(a),'full_transient_completed':completed,'failure_messages':errors,
            'scope':'Ideal control and sensing, modified IR2104 input model, user power-stage models, fuse disconnected as in working source'}
    if len(a):
        assert np.isfinite(a).all()
        a=np.c_[a,(a[:,11]-a[:,1])/.05]
        vo_peak=int(np.argmax(a[:,1]));il_peak=int(np.argmax(a[:,2]))
        record.update({'VOUT_max_V':float(a[vo_peak,1]),'IL_max_A':float(a[il_peak,2]),'IL_min_A':float(a[:,2].min()),
                       'IOUT_max_A':float(a[:,12].max()),'VIN_max_V':float(a[:,10].max()),
                       'peak_VOUT_time_s':float(a[vo_peak,0]),'peak_IL_time_s':float(a[il_peak,0])})
        selected=(a[:,0]>=stop-.002)|(abs(a[:,0]-a[vo_peak,0])<=25e-6)|(abs(a[:,0]-a[il_peak,0])<=25e-6)
        windows=[[stop-.002,stop],[float(a[vo_peak,0])-25e-6,float(a[vo_peak,0])+25e-6],[float(a[il_peak,0])-25e-6,float(a[il_peak,0])+25e-6]]
        if case['load']=='steps':
            selected|=((a[:,0]>=.0175)&(a[:,0]<=.019))|((a[:,0]>=.0275)&(a[:,0]<=.029))
            windows.extend([[.0175,.019],[.0275,.029]])
        np.savez_compressed(DATA/f'{case["id"]}_windows.npz',trace=a[selected],columns=np.array(COLUMNS))
        record['full_resolution_windows_s']=windows
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//3000)),len(a)-1])
        np.savetxt(DATA/f'{case["id"]}_sampled.csv',a[take],delimiter=',',header=','.join(COLUMNS),comments='')
    if completed:
        tail=a[a[:,0]>=stop-.002]
        record['last_2ms_ranges']={'VOUT_V':[float(tail[:,1].min()),float(tail[:,1].max())],
                                 'IOUT_A':[float(tail[:,12].min()),float(tail[:,12].max())]}
        selected_range=record['last_2ms_ranges']['VOUT_V' if case['id'].startswith('CV') else 'IOUT_A']
        low,high=(9.5,10.5) if case['id'].startswith('CV') else (.9,1.1)
        record['last_2ms_full_band_passed']=low<=selected_range[0]<=selected_range[1]<=high
        record['last_2ms_time_means']={'VOUT_V':mean(a,1,stop-.002,stop),'IOUT_A':mean(a,12,stop-.002,stop),'IL_A':mean(a,2,stop-.002,stop)}
        if case['load']=='steps':
            segments=[('CV20',.016,.0175,'CV'),('CC8',.026,.0275,'CC'),('CC5',.043,.045,'CC')]
            record['segments']=[]
            for label,start,end,mode in segments:
                voltage=mean(a,1,start,end);current=mean(a,12,start,end)
                passed=abs(voltage-10)<=.5 if mode=='CV' else abs(current-1)<=.1
                record['segments'].append({'name':label,'mode':mode,'window_s':[start,end],'VOUT_mean_V':voltage,'IOUT_mean_A':current,'within_steady_target':passed})
            record['steady_target_passed']=all(s['within_steady_target'] for s in record['segments']) and record['last_2ms_full_band_passed']
        else:
            cv=case['id'].startswith('CV');value=record['last_2ms_time_means']['VOUT_V' if cv else 'IOUT_A']
            record['steady_target_passed']=abs(value-(10 if cv else 1))<=(.5 if cv else .1) and record['last_2ms_full_band_passed']
    else:record['steady_target_passed']=False
    (DATA/f'{case["id"]}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False),flush=True)
    # Only decimated full-range data is retained in memory for the overview figure.
    return record,a[::max(1,len(a)//6000)] if len(a) else a


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-verified',action='store_true',help='Reuse only complete prior cases whose exact native binary and extracted source hashes match')
    args=parser.parse_args()
    for p in [DATA,LOGS,FIG]:p.mkdir(parents=True,exist_ok=True)
    cached={};todo=[]
    for case in CASES:
        saved=DATA/f'{case["id"]}.json';csv=DATA/f'{case["id"]}_sampled.csv'
        if args.reuse_verified and saved.exists() and csv.exists():
            row=json.loads(saved.read_text())
            if row.get('full_transient_completed') and row.get('steady_target_passed') and row.get('last_2ms_full_band_passed') and row['project_sha256']==hashlib.sha256(output_path(case).read_bytes()).hexdigest() and row['solver_source_sha256']==hashlib.sha256(extract_netlist(output_path(case)).encode()).hexdigest():
                cached[case['id']]=(row,np.loadtxt(csv,delimiter=',',skiprows=1));continue
        todo.append(case)
    with tempfile.TemporaryDirectory(prefix='gbuck-loop-init-') as td:
        init=Path(td);lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(lib/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        with ThreadPoolExecutor(max_workers=6) as pool:new=list(pool.map(lambda c:run_case(c,init),todo))
    combined={**cached,**{row['id']:(row,a) for row,a in new}}
    results=[combined[case['id']] for case in CASES]
    summary={'date':'2026-10-24','source_working_project_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'all_transients_completed':all(r['full_transient_completed'] for r,_ in results),
             'all_steady_targets_passed':all(r['steady_target_passed'] for r,_ in results),
             'native_multisim_execution_verified':False,
             'execution_this_invocation':[case['id'] for case in todo],
             'prior_completed_runs_reused_after_exact_hash_match':list(cached),
             'assumptions':['Controller and sensing are ideal equivalents, not STM32 firmware or INA model verification',
                            'Light-load correction allows transient negative inductor-current reference down to -0.15A',
                            'F1 remains disconnected and R1=1mOhm remains in the working source',
                            'No efficiency, real fuse/protection, or physical switching-stress validation'],
             'cases':[r for r,_ in results]}
    (DATA/'verification_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    count=math.ceil(len(results)/2)
    fig,axes=plt.subplots(count,2,figsize=(12,count*3.3))
    for ax,(record,a) in zip(axes.flat,results):
        if len(a):
            ax.plot(a[:,0]*1e3,a[:,1],label='VOUT / V',lw=.8)
            twin=ax.twinx();twin.plot(a[:,0]*1e3,a[:,12],color='tab:orange',label='IOUT / A',lw=.65)
            twin.set_ylabel('IOUT / A',color='tab:orange');ax.set_ylabel('VOUT / V')
        ax.set_title(record['id']);ax.set_xlabel('Time / ms');ax.grid(alpha=.25)
    for ax in list(axes.flat)[len(results):]:ax.remove()
    fig.suptitle('User power stage + ideal CV/current controller: ngspice only')
    fig.tight_layout();fig.savefig(FIG/'closed_loop_overview.png',dpi=140);plt.close(fig)
    assert summary['all_transients_completed'] and summary['all_steady_targets_passed'],'Incomplete or failed cases are not passing'


if __name__=='__main__':main()
