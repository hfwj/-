"""Isolate the incremental plotting path; do not modify solver or circuit."""
import hashlib
import json
import re
from build_diagnostics import ROOT, PROJECT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block


def main():
    source = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_LOWMEM.ms14'
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'cac9980ff779de62587da60faa3630f5cea8755100bcb3a6d51d12a9723ea58f'
    xml, _ = unpack(raw)
    root = parse(xml)
    before = inspect(root)
    assert before['transient_settings'] == {'TSTOP':'0.1','TSTART':'0.09','TMAX':'5e-008','IC':'auto_ic'}
    assert set(before['selected_outputs']) == {'$iout_raw','$vdda','$vout','@rrs_out[i]'}
    text = xml.decode('ascii')
    tran = block(text,'TRAN')
    assert tran.count('IncrPlot:long{1}') == 1
    revised = tran.replace('IncrPlot:long{1}','IncrPlot:long{0}',1)
    title = '5R U3 IIB SMOOTH 0.1mV ABSTOL10nA 100ms FINALPLOT record90-100ms 4ch'
    revised, n = re.subn(r'PLOT_TITLE:string\{[^}]*\}', 'PLOT_TITLE:string{'+title+'}', revised)
    assert n == 1
    changed = text.replace(tran,revised,1).encode('ascii')
    assert changed.decode('ascii').replace(revised,tran,1).encode('ascii') == xml
    newroot = parse(changed)
    assert inspect(newroot) == before
    assert components(newroot) == components(root)
    assert model_sources(newroot) == model_sources(root)
    assert analysis_options(changed) == analysis_options(xml)
    data = pack(changed)
    verify_independent_decoder(data,changed)
    dest = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_FINALPLOT.ms14'
    dest.write_bytes(data)
    result = {'date':'2026-10-26','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(), 'output':str(dest.relative_to(PROJECT)),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'only_changes':['TRAN IncrPlot 1 -> 0','plot title LOWMEM -> FINALPLOT'],
        'same_names_and_selected_outputs':before['selected_outputs'], 'same_settings':before['transient_settings'],
        'all_components_ports_values_layout_models_and_controller_preserved':True,
        'all_solver_options_and_maxstep_tolerances_preserved':True,
        'existing_U2_U4_INA240_and_U3_INA181_modified_bias_models_retained':True,
        'exact_inverse_XML_verified':True, 'two_DCL_decoders_verified':True,
        'native_run_performed':False, 'unknown_name_error_fixed_verified':False,
        'native_100ms_pass_confirmed':False, 'hardware_BOM_PCB_change':False,
        'limitation':'A one-setting output-path isolation, not a proven fix. Reporting remains 90-100ms; integration must still run from zero.'}
    (ROOT/'results/data/2026-10-26_u3_100ms_finalplot_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
