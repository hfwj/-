"""5ms syntax/startup smoke check, explicitly not100ms stability validation."""
from pathlib import Path
import sys,json,re,hashlib,subprocess,tempfile,os
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent),str(HERE.parents[1])]
from ms14_project import PROJECT,unpack,parse,elements,clean,components
from verify_power_stage import power_stage_source
from verify_driver import NG
SOURCE=PROJECT/'downloads/GBUCK_OPEN_DIAG_C_KIV20_100ms.ms14'

def main():
    root=parse(unpack(SOURCE.read_bytes())[0]);by={x['display_ref']:x for x in components(root)}
    assert by['V1']['parameters'][1]=='15' and by['RL']['parameters'][1]=='1e9'
    assert by['F1']['ports']=={'2':'5','1':'8'} and by['R1']['ports']=={'2':None,'1':None}
    ctrl=next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))=='V3')
    tpl=clean(ctrl.find('.//CiaSpiceTmpltExprt').get('String'));definition=tpl[tpl.index('.SUBCKT'):]
    assert definition==(HERE/'GBUCK_CTRL_EQ_KIV20.lib').read_text()
    instance=next(x for x in tpl.splitlines() if x.startswith('XCTRL ')).replace('%t1','1').replace('%t2','0').replace('VOUT','4')
    assert instance=='XCTRL 1 0 4 3 7 2 GBUCK_CTRL_EQ'
    base=power_stage_source(root);source,n=re.subn(r'(?m)^V3 .*$',instance,base);assert n==1
    assert base[base.index('.SUBCKT'):] in source
    source+=definition+'\n.options method=trap reltol=0.003 abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=100\n.save v(4) i(l1) v(xctrl.iref) v(xctrl.duty) v(1)\n.tran 50n 5m 0 50n\n'
    with tempfile.TemporaryDirectory(prefix='gbuck-c-smoke-') as td:
        w=Path(td);init=w/'init';init.mkdir();lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(lib/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        raw=w/'trace.txt';net=w/'test.cir';net.write_text(source+f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(4) i(l1) v(xctrl.iref) v(xctrl.duty) v(1)\nquit\n.endc\n.end\n')
        try:
            p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],env=dict(os.environ,SPICE_SCRIPTS=str(init)),capture_output=True,text=True,timeout=90);log=p.stdout+p.stderr;code=p.returncode
        except subprocess.TimeoutExpired:
            log='ERROR:5ms diagnostic exceeded90s wall-time budget\n';code=None
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,6))
    (HERE/'results/C_5ms_smoke.log').write_text(log)
    errors=[l for l in log.splitlines() if any(x in l.lower() for x in ['error:','too small','aborted'])]
    passed=bool(code==0 and len(a)>1000 and a[-1,0]>=.005*.999 and np.isfinite(a).all() and not errors)
    r={'date':'2026-10-24','project_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'extracted_test_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'solver':'ngspice44.2/psa','requested_end_time_s':.005,'actual_end_time_s':float(a[-1,0]) if len(a) else None,'data_rows':len(a),'smoke_completed':passed,'failure_messages':errors,'vendor_model_text_preserved':True,'native_execution_verified':False,'native100ms_stability_verified':False,'scope':'Only5ms syntax and startup cross-check. F1 represented by fixed1mOhm; no trip behavior, long-time regulation, real firmware, sensor or efficiency acceptance.'}
    if len(a):
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//1500)),len(a)-1]);np.savetxt(HERE/'results/C_5ms_sampled.csv',a[take],delimiter=',',header='time_s,VOUT_V,IL_A,IREF_A,DUTY,PWM_V',comments='')
    (HERE/'results/C_5ms_smoke.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
