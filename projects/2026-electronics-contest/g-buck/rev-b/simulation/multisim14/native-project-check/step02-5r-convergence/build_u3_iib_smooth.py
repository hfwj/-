"""Add only the U3 IIB regularization and undo the failed ABSTOL relaxation."""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, elements, clean, model_sources, analysis_options, verify_independent_decoder, block
from build_projects import component_span
from bias_smoothing import patch_bias


def main():
    source=PROJECT/'downloads/GBUCK_STEP02_5R_ABSTOL100nA_30ms_8CH_DIAG.ms14'
    reference=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14'
    raw=source.read_bytes();xml,_=unpack(raw);root=parse(xml);before=inspect(root);opts=analysis_options(xml)
    refroot=parse(unpack(reference.read_bytes())[0])
    assert opts['abstol']=={'enabled':True,'value':'1e-007'}
    assert len(before['selected_outputs'])==8 and before['transient_settings']['TSTOP']=='0.03'
    by={p['display_ref']:p for p in components(root)}
    assert by['U3']['ports']=={'1':'22','2':'0','3':'3','4':'4','5':'0','6':'21'}
    models=elements(root,'CiModel');m=models[by['U3']['model_id']]
    name=clean(m.get('LocalName'));oldmodel=clean(m.find('.//CiaCString').get('String'))
    assert 'INA181A1' in name
    assert re.search(r'^GOUT1 OUT IN VALUE = .*60u\}',oldmodel,re.M)
    newmodel=patch_bias(oldmodel,part='INA181')
    text=xml.decode('ascii');mutations=[]
    a,b,old=component_span(text,by['U3']['internal_ref']);new=patch_bias(old,part='INA181')
    text=text[:a]+new+text[b:];mutations.append((old,new))
    a=text.index('<CiModel Class="CiModel" LocalName="&amp;ASC'+name+'"')
    b=text.index('</CiModel>',a)+len('</CiModel>');old=text[a:b];new=patch_bias(old,part='INA181')
    new,n=re.subn(r'ChangedByUser="0"','ChangedByUser="1"',new,count=1);assert n==1
    text=text[:a]+new+text[b:];mutations.append((old,new))
    tran=block(text,'TRAN');opt=block(tran,'ASYS_OPT')
    revised_opt,n=re.subn(r'(\d+:list\{IsEnabled:long\{1\}\s+abstol:double\{)1e-007(\}\s*\})',
        lambda m:m[1]+'1e-008'+m[2],opt);assert n==1
    revised=tran.replace(opt,revised_opt,1)
    revised,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}',
        'PLOT_TITLE:string{5R U3 IIB SMOOTH 0.1mV ABSTOL10nA 30ms 8ch DIAGNOSTIC}',revised);assert n==1
    text=text.replace(tran,revised,1);mutations.append((tran,revised))
    inverse=text
    for old,new in reversed(mutations):
        assert inverse.count(new)==1
        inverse=inverse.replace(new,old,1)
    assert inverse.encode('ascii')==xml
    changed=text.encode('ascii');newroot=parse(changed)
    assert components(newroot)==components(root)==components(refroot)
    assert inspect(newroot)==before
    assert model_sources(newroot)==dict(model_sources(root),**{name:newmodel})
    assert model_sources(root)==model_sources(refroot)
    assert analysis_options(changed)==dict(opts,abstol={'enabled':True,'value':'1e-008'})
    assert analysis_options(changed)==analysis_options(unpack(reference.read_bytes())[0])
    data=pack(changed);verify_independent_decoder(data,changed)
    dest=PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_30ms_8CH_DIAG.ms14';dest.write_bytes(data)
    result={'date':'2026-10-26','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(),
        'nominal_10nA_reference':str(reference.relative_to(PROJECT)),
        'output':str(dest.relative_to(PROJECT)),'output_sha256':hashlib.sha256(data).hexdigest(),
        'new_behavior_change':'U3 INA181 IIBP/IIBN E1ACT 5V SGN -> TANH(delta/0.0001), two saved model copies',
        'rollback':'ABSTOL 100nA -> original 10nA; failed tolerance experiment is not retained',
        'U3_IIB_60uA_limit_and_linear_450k_and_530k_terms_preserved':True,
        'U3_other_core_equations_including_PSRR_preserved':True,
        'existing_U2_U4_modified_IIB_models_preserved':True,
        'MOS_driver_controller_and_other_active_models_preserved':True,
        'all_components_ports_values_layout_outputs_times_preserved':True,
        'settings':before['transient_settings'],'outputs':before['selected_outputs'],
        'all_options_match_nominal_10nA_reference':True,
        'exact_inverse_XML_verified':True,'two_DCL_decoders_verified':True,
        'hardware_BOM_PCB_change':False,'unchanged_vendor_model':False,
        'native_30ms_run_performed':False,'native_100ms_verified':False,
        'limitation':'Controlled model fixture reproduces the same U3 node failure class, not native 20.1209ms absolute history. 0.1mV smoothing is a diagnostic assumption; all three sense-chip instances now have explicitly modified bias models.'}
    (ROOT/'results/data/2026-10-26_u3_iib_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
