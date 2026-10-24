"""Verify only the native file's new external-load waveform using a fixed10V bench."""
from pathlib import Path
import sys,json,hashlib,subprocess,tempfile,os
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1])]
from build_dynamic import DEST
from ms14_project import unpack,parse,elements,clean
from verify_driver import NG

def main():
    root=parse(unpack(DEST.read_bytes())[0]);comp=next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))=='R4')
    tpl=clean(comp.find('.//CiaSpiceTmpltExprt').get('String'));load=tpl.replace('%t1','out').replace('%t2','0')
    source='* Isolated time-dependent external load check, notBuck regulator\nVFIX out 0 10\n'+load+'\n.save i(VFIX) v(GLOAD_CTRL)\n.tran 5u 180m 0 20u\n'
    with tempfile.TemporaryDirectory(prefix='gbuck-kiv20-load-') as td:
        w=Path(td);init=w/'init';init.mkdir();lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(lib/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        raw=w/'trace.txt';net=w/'bench.cir';net.write_text(source+f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} i(VFIX) v(GLOAD_CTRL)\nquit\n.endc\n.end\n')
        p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],env=dict(os.environ,SPICE_SCRIPTS=str(init)),capture_output=True,text=True,timeout=20);log=p.stdout+p.stderr
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,3))
    folder=HERE/'results/logs';folder.mkdir(exist_ok=True);(folder/'load_bench.log').write_text(log)
    errors=[line for line in log.splitlines() if any(x in line.lower() for x in ['error:','too small','aborted'])]
    complete=bool(p.returncode==0 and len(a)>100 and a[-1,0]>=.18*.999 and np.isfinite(a).all() and not errors)
    stages=[]
    if complete:
        for start,end,resistance in [(.06,.075,20),(.11,.125,8),(.16,.175,5)]:
            b=a[(a[:,0]>=start)&(a[:,0]<=end)];expected=10/resistance;current=-b[:,1]
            stages.append({'window_s':[start,end],'external_resistance_ohm':resistance,'fixed_bench_voltage_V':10,'expected_bench_current_A':expected,'actual_bench_current_range_A':[float(current.min()),float(current.max())],'passed':bool(np.max(abs(current-expected))<1e-6)})
    result={'date':'2026-10-24','native_project_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'extracted_load_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'solver':'ngspice44.2/psa','isolated_load_transient_complete':complete,'failure_messages':errors,'load_stage_tests':stages,'all_load_stages_passed':complete and all(x['passed'] for x in stages),'full_buck_dynamic_transient_verified':False,'native_multisim_execution_verified':False,'scope':'Only extracted external-load template at fixed10V. Bench1.25A/2A values at8ohm/5ohm are imposed10V loads, not closed-loopBuck results.'}
    (HERE/'results/data/load_bench.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
    assert result['all_load_stages_passed']
if __name__=='__main__':main()
