"""Extend the existing modified-IIB diagnostic to 100ms; no new model edits."""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block


def main():
    source=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_25ms_DIAG.ms14'
    raw=source.read_bytes();xml,_=unpack(raw);root=parse(xml);before=inspect(root)
    assert before['transient_settings']=={'TSTOP':'0.025','TSTART':'0','TMAX':'5e-008','IC':'auto_ic'}
    opts=analysis_options(xml)
    assert opts['reltol']=={'enabled':True,'value':'0.001'}
    assert opts['method']=={'enabled':True,'value':'trapezoidal'}
    assert opts['itl4']=={'enabled':True,'value':'300'}
    text=xml.decode('ascii');tran=block(text,'TRAN')
    assert tran.count('TSTOP:double{0.025}')==1
    revised=tran.replace('TSTOP:double{0.025}','TSTOP:double{0.1}',1)
    title='PLOT_TITLE:string{5R IIB SMOOTH 0.1mV MODEL DIAGNOSTIC 25ms}'
    assert revised.count(title)==1
    revised=revised.replace(title,title.replace('25ms','100ms'),1)
    candidate=text.replace(tran,revised,1).encode('ascii')
    assert candidate.decode('ascii').replace(revised,tran,1).encode('ascii')==xml
    newroot=parse(candidate);after=inspect(newroot)
    assert components(newroot)==components(root)
    assert model_sources(newroot)==model_sources(root)
    assert analysis_options(candidate)==opts
    assert after==dict(before,transient_settings=dict(before['transient_settings'],TSTOP='0.1'))
    data=pack(candidate);verify_independent_decoder(data,candidate)
    dest=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14';dest.write_bytes(data)
    result={'date':'2026-10-25','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(),'output':str(dest.relative_to(PROJECT)),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'only_changes':['TSTOP 0.025 -> 0.1 s','plot title 25ms -> 100ms'],
        'all_parts_values_ports_models_controller_outputs_other_solver_options_preserved':True,
        'modified_INA240_IIB_model_retained_for_U2_and_U4':True,
        'unchanged_vendor_model':False,'exact_inverse_XML_verified':True,
        'two_DCL_decoders_verified':True,'settings':after['transient_settings'],
        'native_100ms_run_performed':False,'native_100ms_convergence_verified':False,
        'hardware_BOM_PCB_change':False}
    (ROOT/'results/data/iib_100ms_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
