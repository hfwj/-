"""Single current-tolerance diagnostic plus shorter, smaller output capture.

This relaxes ABSTOL. It does not change MOS/TI models or establish accuracy.
"""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block

KEEP={'$vout','@rrs_out[i]','$iout_raw','$vdda','$g_h','$g_l','$sw','ll1#branch'}


def main():
    source=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14'
    raw=source.read_bytes();xml,_=unpack(raw);root=parse(xml);before=inspect(root);opts=analysis_options(xml)
    assert opts['abstol']=={'enabled':True,'value':'1e-008'}
    assert opts['reltol']=={'enabled':True,'value':'0.001'}
    assert opts['method']=={'enabled':True,'value':'trapezoidal'}
    assert before['transient_settings']=={'TSTOP':'0.1','TSTART':'0','TMAX':'5e-008','IC':'auto_ic'}
    assert len(before['selected_outputs'])==14
    text=xml.decode('ascii');tran=block(text,'TRAN');opt=block(tran,'ASYS_OPT')
    revised_opt,n=re.subn(r'(\d+:list\{IsEnabled:long\{1\}\s+abstol:double\{)1e-008(\}\s*\})',
        lambda m:m[1]+'1e-007'+m[2],opt);assert n==1
    updated=tran.replace(opt,revised_opt,1)
    assert updated.count('TSTOP:double{0.1}')==1
    updated=updated.replace('TSTOP:double{0.1}','TSTOP:double{0.03}',1)
    pattern=(r'(NODE:list\{GROUP:long\{)(\d+)'
        r'(\}\s*PLOTDEVICETYPE:long\{\d+\}\s*TYPE:long\{\d+\}\s*NAME:string\{([^}]+)\})')
    edits=[]
    def output(match):
        old=int(match[2]);name=match[4]
        if old&768 and name not in KEEP:
            new=old&~768;edits.append({'variable':name,'before':old,'after':new})
            return match[1]+str(new)+match[3]
        return match[0]
    updated=re.sub(pattern,output,updated);assert len(edits)==6
    updated,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}',
        'PLOT_TITLE:string{5R IIB MODIFIED ABSTOL 100nA 30ms 8ch DIAGNOSTIC}',updated);assert n==1
    changed=text.replace(tran,updated,1).encode('ascii');newroot=parse(changed);after=inspect(newroot)
    assert changed.decode('ascii').replace(updated,tran,1).encode('ascii')==xml
    assert components(newroot)==components(root)
    assert model_sources(newroot)==model_sources(root)
    assert analysis_options(changed)==dict(opts,abstol={'enabled':True,'value':'1e-007'})
    assert set(after['selected_outputs'])==KEEP
    assert after==dict(before,selected_outputs=after['selected_outputs'],
        transient_settings=dict(before['transient_settings'],TSTOP='0.03'))
    data=pack(changed);verify_independent_decoder(data,changed)
    dest=PROJECT/'downloads/GBUCK_STEP02_5R_ABSTOL100nA_30ms_8CH_DIAG.ms14';dest.write_bytes(data)
    result={'date':'2026-10-26','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(),'output':str(dest.relative_to(PROJECT)),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'only_solver_tolerance_change':'ABSTOL relaxed from 1e-8 A (10nA) to 1e-7 A (100nA)',
        'other_changes':['TSTOP 100 ->30ms to test crossing 24.9514ms first','14 ->8 output selections','diagnostic title'],
        'settings':after['transient_settings'],'outputs':after['selected_outputs'],'removed_output_flags':edits,
        'all_models_control_templates_components_ports_values_layout_preserved':True,
        'RELTOL_method_ITL4_TMAX_other_options_preserved':True,
        'existing_modified_INA240_IIB_model_for_U2_U4_retained':True,'unchanged_vendor_models_for_all_devices':False,
        'exact_inverse_XML_verified':True,'two_DCL_decoders_verified':True,
        'native_30ms_run_performed':False,'native_crossed_24_9514ms_verified':False,
        'native_100ms_completed':False,'hardware_BOM_PCB_change':False,
        'limitation':'A tolerance sensitivity test, not a verified fix or proof of full-circuit accuracy. Global convergence-current criterion changes, not just Q2. Original files remain.'}
    (ROOT/'results/data/2026-10-26_abs100na_30ms_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
