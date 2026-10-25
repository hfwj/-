"""Diagnostic shared INA240 bias regularization; no physical circuit changes.

Both U2 and U4 use this model. Touch only their two saved component metadata
copies and the active INA240 CiModel; INA181 U3 also contains similar formulas
and must remain byte-for-byte unchanged.
"""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, elements, clean, model_sources, analysis_options, verify_independent_decoder, block
from build_fix import replace_component
from bias_smoothing import patch_bias


def main():
    source=PROJECT/'downloads/GBUCK_STEP02_5R_REL001_U4_TRACE_25ms.ms14'
    raw=source.read_bytes();xml,_=unpack(raw);root=parse(xml)
    by={p['display_ref']:p for p in components(root)}
    assert by['U2']['model_id']==by['U4']['model_id']!=by['U3']['model_id']
    models=elements(root,'CiModel');item=models[by['U4']['model_id']]
    name=clean(item.get('LocalName'));original=clean(item.find('.//CiaCString').get('String'))
    modified=patch_bias(original)
    text=xml.decode('ascii');edits=[]
    for ref in ['U2','U4']:
        internal=by[ref]['internal_ref']
        text=replace_component(text,internal,patch_bias)
        edits.append({'scope':'component saved model metadata','display_ref':ref,'internal_ref':internal})
    start=text.index('<CiModel Class="CiModel" LocalName="&amp;ASC'+name+'"')
    end=text.index('</CiModel>',start)+len('</CiModel>')
    old=text[start:end];new=patch_bias(old)
    new,count=re.subn(r'ChangedByUser="0"','ChangedByUser="1"',new,count=1);assert count==1
    text=text[:start]+new+text[end:]
    tran=block(text,'TRAN')
    revised,count=re.subn(r'PLOT_TITLE:string\{[^}]*\}',
        'PLOT_TITLE:string{5R IIB SMOOTH 0.1mV MODEL DIAGNOSTIC 25ms}',tran);assert count==1
    text=text.replace(tran,revised,1);changed=text.encode('ascii');newroot=parse(changed)
    assert components(newroot)==components(root)
    assert inspect(newroot)==inspect(root)
    assert analysis_options(changed)==analysis_options(xml)
    before=model_sources(root);after=model_sources(newroot)
    assert after==dict(before,**{name:modified})
    # Undo every exact changed byte, including title and model user flag.
    inverse=text.replace(revised,tran,1)
    cstart=inverse.index('<CiModel Class="CiModel" LocalName="&amp;ASC'+name+'"')
    cend=inverse.index('</CiModel>',cstart)+len('</CiModel>')
    portion=inverse[cstart:cend];portion,n=re.subn(r'ChangedByUser="1"','ChangedByUser="0"',portion,count=1);assert n==1
    inverse=inverse[:cstart]+portion+inverse[cend:]
    oldcomment='Interface adapter only; original TI model follows byte-for-byte.'
    newcomment='DIAGNOSTIC MODIFIED INA240: two IIB 5V SGN breakpoints use TANH, width=0.0001 V; NOT the unchanged TI model.'
    assert inverse.count(newcomment)==3
    inverse=inverse.replace(newcomment,oldcomment)
    for pin in ['INP','INN']:
        token=f'TANH((V({pin})-VCMBRK)/0.0001)'
        assert inverse.count(token)==3
        inverse=inverse.replace(token,f'SGN(V({pin})-VCMBRK) - 1 + ABS(SGN(V({pin})-VCMBRK))')
    assert inverse.encode('ascii')==xml
    data=pack(changed);verify_independent_decoder(data,changed)
    dest=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_25ms_DIAG.ms14';dest.write_bytes(data)
    result={'date':'2026-10-25','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(),'output':str(dest.relative_to(PROJECT)),
        'output_sha256':hashlib.sha256(data).hexdigest(),'active_model':name,
        'affected_display_instances':['U2','U4'],'smoothing_scale_V':.0001,
        'only_behavioral_changes':'E1ACT common-mode 5V breakpoint in IIBP and IIBN: discontinuous SGN expression -> TANH(delta/0.0001); 65uA limiting value unchanged',
        'metadata_edits':edits,'saved_model_copies_changed':3,
        'label_changes':'model header marks modified diagnostic, ChangedByUser=1 and plot title identifies diagnostic',
        'U3_and_MOS_driver_controller_models_preserved':True,
        'all_connections_parts_values_layout_solver_options_outputs_preserved':True,
        'exact_inverse_XML_verified':True,'two_DCL_decoders_verified':True,
        'source_preserved':source.read_bytes()==raw,
        'native_run_performed':False,'native_25ms_convergence_verified':False,
        'hardware_BOM_PCB_change':False,'unchanged_vendor_model':False,
        'limitation':'Simulation regularization hypothesis, not TI-qualified device behavior, firmware or hardware validation. Full native Buck and original Q2 switching issue remain to verify.'}
    (ROOT/'results/data/iib_smooth_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
