"""Reduce stored output after native memory error; preserve circuit and solver.

TSTART is reporting start, not a new cold start of circuit state. The simulator
must still integrate startup to 100ms. Native execution remains unverified.
"""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block

KEEP = {'$vout', '@rrs_out[i]', '$iout_raw', '$vdda'}


def main():
    source=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14'
    raw=source.read_bytes();xml,_=unpack(raw);root=parse(xml);before=inspect(root)
    assert before['transient_settings']=={'TSTOP':'0.1','TSTART':'0','TMAX':'5e-008','IC':'auto_ic'}
    assert len(before['selected_outputs'])==14
    assert KEEP.issubset(before['selected_outputs'])
    text=xml.decode('ascii');tran=block(text,'TRAN');updated=tran;edits=[]
    pattern=(r'(NODE:list\{GROUP:long\{)(\d+)'
        r'(\}\s*PLOTDEVICETYPE:long\{\d+\}\s*TYPE:long\{\d+\}\s*NAME:string\{([^}]+)\})')
    def change(match):
        old=int(match[2]);name=match[4]
        if name not in KEEP and old & 768:
            new=old & ~768
            edits.append({'variable':name,'before_group':old,'after_group':new})
            return match[1]+str(new)+match[3]
        return match[0]
    updated=re.sub(pattern,change,updated)
    assert len(edits)==10
    assert updated.count('TSTART:double{0}')==1
    updated=updated.replace('TSTART:double{0}','TSTART:double{0.09}',1)
    title='PLOT_TITLE:string{5R IIB SMOOTH 0.1mV MODEL DIAGNOSTIC 100ms}'
    assert updated.count(title)==1
    updated=updated.replace(title,'PLOT_TITLE:string{5R IIB SMOOTH 100ms LOW MEMORY record 90-100ms 4ch}',1)
    changed=text.replace(tran,updated,1).encode('ascii');newroot=parse(changed);after=inspect(newroot)
    assert changed.decode('ascii').replace(updated,tran,1).encode('ascii')==xml
    assert components(newroot)==components(root)
    assert model_sources(newroot)==model_sources(root)
    assert analysis_options(changed)==analysis_options(xml)
    assert set(after['selected_outputs'])==KEEP
    assert after==dict(before,selected_outputs=after['selected_outputs'],
        transient_settings=dict(before['transient_settings'],TSTART='0.09'))
    data=pack(changed);verify_independent_decoder(data,changed)
    dest=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_LOWMEM.ms14';dest.write_bytes(data)
    result={'date':'2026-10-25','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(),'output':str(dest.relative_to(PROJECT)),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'only_changes':['reporting TSTART 0 -> 90ms','remove 10 saved/plotted output selections','diagnostic plot title'],
        'outputs':after['selected_outputs'],'removed_output_flags':edits,
        'settings':after['transient_settings'],'options':analysis_options(changed),
        'models_controller_components_connections_values_layout_preserved':True,
        'integration_maxstep_and_tolerances_preserved':True,
        'modified_INA240_model_for_U2_U4_retained':True,'unchanged_vendor_model':False,
        'expected_reporting_window_s':[.09,.1],'analysis_stop_s':.1,
        'reporting_is_not_restart_or_shortened_integration':True,
        'output_channel_times_duration_fraction_if_point_density_equal':(4*.01)/(14*.1),
        'memory_fraction_is_not_a_measured_or_guaranteed_process_memory_reduction':True,
        'exact_inverse_XML_verified':True,'two_DCL_decoders_verified':True,
        'native_run_performed':False,'native_100ms_completed':False,'memory_error_resolved':False,
        'hardware_BOM_PCB_change':False}
    (ROOT/'results/data/iib_lowmem_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
