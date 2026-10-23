"""Independent ngspice checks of the embedded IR2104 input-level problem.

No native Multisim execution. Only the isolated driver is a completed test;
full-power-stage attempts are recorded separately with their early aborts.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ms14_project import ROOT,SOURCE,DEST,unpack,parse,driver_model,patched_model

NG=Path(os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice'))
DATA=ROOT/'results/data';LOGS=ROOT/'results/logs';FIG=ROOT/'results/figures'


def ngspice_compat(model):
    # ngspice-specific parser accommodations, NOT applied to the .ms14 file.
    return (model.replace('IR2104/IR__MOSFET_DRIVER__1','IR2104_IR__MOSFET_DRIVER__1')
            .replace('.ENDS  IR2104/IR','.ENDS IR2104_IR__MOSFET_DRIVER__1')
            .replace('+PARAMS:','+ PARAMS:').replace('T1=-40','T1={-40}'))


def run_case(case,model,level,init):
    with tempfile.TemporaryDirectory(prefix='gbuck-native-driver-') as td:
        work=Path(td);raw=work/'trace.txt'
        net=f'''* Isolated IR2104 input test, ngspice only; no bootstrap or MOS power-stage validation
VCC vcc 0 12
VB vb 0 12
VIN inp 0 PULSE(0 {level} 30u 20n 20n 5u 10u)
VEN en 0 {level}
XU1 vcc inp en 0 vb ho 0 lo IR2104_IR__MOSFET_DRIVER__1
C_HO ho 0 1n
C_LO lo 0 1n
R_HO ho 0 100k
R_LO lo 0 100k
{ngspice_compat(model)}
.options method=gear reltol=0.001
.tran 20n 100u 0 20n
.control
set wr_singlescale
run
wrdata {raw} v(inp) v(en) v(ho) v(lo) v(xu1.md1_trigin_3) v(xu1.md1_trigsd_3)
quit
.endc
.end
'''
        path=work/'test.cir';path.write_text(net,encoding='ascii')
        env=dict(os.environ,SPICE_SCRIPTS=str(init))
        completed=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(path)],capture_output=True,text=True,env=env)
        log=completed.stdout+completed.stderr;(LOGS/f'{case}.log').write_text(log)
        assert completed.returncode==0 and raw.exists()
        assert not any(x in log.lower() for x in ['aborted','error:','timestep too small'])
        a=np.loadtxt(raw)
    assert a[-1,0]>=100e-6*.999
    if case=='original_3v3':assert a[:,3:5].max()<.01
    else:assert a[:,3].max()>10 and a[:,4].max()>10 and a[a[:,0]>40e-6,3].min()<.1
    assert not np.any((a[:,3]>6)&(a[:,4]>6))
    result={'case':case,'solver':'ngspice 44.2 / ngbehavior=psa','native_multisim_execution_verified':False,
            'input_high_V':level,'end_time_s':float(a[-1,0]),'data_rows':len(a),
            'HO_max_V':float(a[:,3].max()),'LO_max_V':float(a[:,4].max()),
            'IN_initial_reference_V':float(a[0,5]),'SD_initial_reference_V':float(a[0,6]),
            'source_model_sha256':hashlib.sha256(model.encode()).hexdigest(),
            'completed':True,'scope':'isolated driver; fixed 12V VB and VCC, VS=0, 1nF/100k output loads'}
    np.savez_compressed(DATA/f'{case}.npz',trace=a)
    take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//2500)),len(a)-1])
    np.savetxt(DATA/f'{case}_sampled.csv',a[take],delimiter=',',header='time_s,IN_V,SD_V,HO_V,LO_V,IN_reference_V,SD_reference_V',comments='')
    (DATA/f'{case}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result,a


def main():
    for p in [DATA,LOGS,FIG]:p.mkdir(parents=True,exist_ok=True)
    original=driver_model(parse(unpack(SOURCE.read_bytes())[0]))
    revised=driver_model(parse(unpack(DEST.read_bytes())[0]))
    assert patched_model(original)[0]==revised
    with tempfile.TemporaryDirectory(prefix='gbuck-nginit-') as td:
        init=Path(td)
        library=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        assert (library/'analog.cm').exists()
        (init/'spinit').write_text('\n'.join('codemodel '+str(library/name) for name in ['spice2poly.cm','analog.cm','digital.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        specs=[('original_3v3',original,3.3),('original_6v',original,6),('corrected_3v3',revised,3.3)]
        with ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(lambda args:run_case(*args,init),specs))
    summary={'date':'2026-10-24','all_three_isolated_tests_completed':True,
             'native_multisim_execution_verified':False,'full_power_stage_completed':False,
             'source_project_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             'corrected_project_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),
             'ngspice_parser_changes_only':['driver subcircuit renamed without slash and matched .ENDS','space before PARAMS, brace negative T1 default'],
             'results':[r for r,_ in results]}
    (DATA/'driver_verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
    for ax,(record,a) in zip(axes,results):
        ax.plot(a[:,0]*1e6,a[:,1],label='IN',lw=1)
        ax.plot(a[:,0]*1e6,a[:,3],label='HO (VS=0)',lw=1)
        ax.plot(a[:,0]*1e6,a[:,4],label='LO',lw=1)
        ax.set_title(record['case']);ax.set_ylabel('Voltage / V');ax.grid(alpha=.3);ax.legend(loc='upper right',ncol=3)
    axes[-1].set_xlabel('Time / us');fig.suptitle('Embedded IR2104 input-level check — ngspice only, isolated driver')
    fig.tight_layout();fig.savefig(FIG/'driver_input_comparison.png',dpi=160);plt.close(fig)


if __name__=='__main__':main()
