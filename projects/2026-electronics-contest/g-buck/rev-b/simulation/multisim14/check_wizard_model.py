"""Check the nested wizard model through an 80ms Buck startup in ngspice.

This is not a Windows Multisim import or simulation test.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
import numpy as np
from build_circuits import ROOT,MODEL,inspect_model_structure

NG=os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice')


def main():
    model=(ROOT/'models/G_BUCK_RevB_EQ.lib').read_text(encoding='ascii')
    structure=inspect_model_structure(model)
    # Reproduce the structural defect with the previous two-root layout.
    try:
        inspect_model_structure(MODEL[MODEL.index('.SUBCKT GBUCK_REVB_EQ '):])
    except AssertionError:
        pass
    else:
        raise AssertionError('Previous multiple-top-level layout must be rejected')
    original=(ROOT/'circuits/04_25V_8ohm.cir').read_text(encoding='ascii')
    assert original.count(MODEL)==1
    circuit=original.replace(MODEL,model)
    log_path=ROOT/'results/logs/wizard_nested_25V_8ohm.log'
    with tempfile.TemporaryDirectory(prefix='gbuck-wizard-',dir='/tmp') as td:
        work=Path(td);raw=work/'trace.txt'
        ctl=f'.control\nset wr_singlescale\nrun\nwrdata {raw} v(VOUT) v(FAULT_N) v(GH_MON) v(GL_MON)\nquit\n.endc'
        net='\n'.join(ctl if line.startswith('.PROBE ') else line for line in circuit.splitlines())+'\n'
        test=work/'test.cir';test.write_text(net,encoding='ascii')
        print('Running nested model: 25V/8ohm, 0..80ms, ngspice only',flush=True)
        with log_path.open('w') as f:
            done=subprocess.run([NG,'-D','ngbehavior=psa','-b',str(test)],stdout=f,stderr=subprocess.STDOUT)
        log=log_path.read_text().lower()
        assert done.returncode==0 and raw.exists()
        assert not any(x in log for x in ['error:','aborted','timestep too small'])
        a=np.loadtxt(raw)
    t=a[:,0];assert t[-1]>=.08*.999 and len(t)>1000
    tail=t>.075
    vout=float(a[tail,1].mean());amps=vout/8
    assert abs(amps-1)<.1 and np.min(a[t>.006,2])>3
    both=(a[:,3]>6)&(a[:,4]>6)&(t>.02)
    assert not np.any(both),'High and low VGS must not be active together'
    old=np.load(ROOT/'results/data/04_25V_8ohm.npz')['trace']
    # Sample the continuous output signal; gate edge interpolation is unsuitable.
    grid=np.linspace(0.001,.0799,3000)
    diff=float(np.max(np.abs(np.interp(grid,t,a[:,1])-np.interp(grid,old[:,0],old[:,1]))))
    assert diff<.01,'Nested vs original output waveform difference exceeded 10mV'
    evidence={'solver':'ngspice 44.2 / ngbehavior=psa','native_multisim_retest':False,
              'case':'04_25V_8ohm','end_time_s':float(t[-1]),'data_rows':len(t),
              'model_sha256':hashlib.sha256(model.encode('ascii')).hexdigest(),
              'testbench_before_runtime_control_sha256':hashlib.sha256(circuit.encode('ascii')).hexdigest(),
              'original_distributed_testbench_sha256':hashlib.sha256(original.encode('ascii')).hexdigest(),
              'model_structure':structure,'previous_multiple_root_layout_rejected':True,
              'last_5ms_vout_mean_V':vout,'last_5ms_load_current_mean_A':amps,
              'simultaneous_vgs_above_6V_samples_after_20ms':int(np.count_nonzero(both)),
              'vout_max_difference_from_original_at_3000_samples_V':diff,
              'full_transient_passed':True,'other_eight_cases_rerun_with_nested_model':False}
    (ROOT/'results/data/wizard_nested_model_check.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2),flush=True)


if __name__=='__main__':main()
