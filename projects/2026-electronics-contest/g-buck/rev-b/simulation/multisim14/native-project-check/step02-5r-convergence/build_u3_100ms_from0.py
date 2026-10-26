"""Restore reporting from zero and live plotting, keeping four outputs.

Use the existing LOWMEM file as a direct single-setting baseline: only
TSTART and title change. Also verify against the user-reported passing 30ms
model/solver/circuit and the latest FINALPLOT capture mode.
"""
import hashlib
import json
import re
from build_diagnostics import ROOT, PROJECT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block


def main():
    source = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_LOWMEM.ms14'
    latest = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_FINALPLOT.ms14'
    passed = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_30ms_8CH_DIAG.ms14'
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
    assert tran.count('TSTART:double{0.09}') == 1
    revised = tran.replace('TSTART:double{0.09}','TSTART:double{0}',1)
    title = '5R U3 IIB SMOOTH 0.1mV ABSTOL10nA 100ms FROM0 LIVEPLOT 4ch'
    revised, n = re.subn(r'PLOT_TITLE:string\{[^}]*\}', 'PLOT_TITLE:string{'+title+'}', revised)
    assert n == 1
    changed = text.replace(tran,revised,1).encode('ascii')
    assert changed.decode('ascii').replace(revised,tran,1).encode('ascii') == xml
    newroot = parse(changed)
    after = inspect(newroot)
    assert after == dict(before,transient_settings=dict(before['transient_settings'],TSTART='0'))
    other_baselines = {}
    for path in [source,latest,passed]:
        otherxml, _ = unpack(path.read_bytes())
        otherroot = parse(otherxml)
        assert components(newroot) == components(otherroot)
        assert model_sources(newroot) == model_sources(otherroot)
        assert analysis_options(changed) == analysis_options(otherxml)
        other_baselines[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    # Against FINALPLOT only two capture settings plus title differ.
    latestxml, _ = unpack(latest.read_bytes())
    lt = block(latestxml.decode('ascii'),'TRAN')
    lt = lt.replace('IncrPlot:long{0}','IncrPlot:long{1}',1)
    lt = lt.replace('TSTART:double{0.09}','TSTART:double{0}',1)
    lt, n = re.subn(r'PLOT_TITLE:string\{[^}]*\}', 'PLOT_TITLE:string{'+title+'}', lt)
    assert n == 1
    assert latestxml.decode('ascii').replace(block(latestxml.decode('ascii'),'TRAN'),lt,1).encode('ascii') == changed
    assert block(unpack(passed.read_bytes())[0].decode('ascii'),'TRAN').count('IncrPlot:long{1}') == 1
    data = pack(changed)
    verify_independent_decoder(data,changed)
    dest = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_FROM0.ms14'
    dest.write_bytes(data)
    result = {'date':'2026-10-26','baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(), 'other_baselines_sha256':other_baselines,
        'output':str(dest.relative_to(PROJECT)), 'output_sha256':hashlib.sha256(data).hexdigest(),
        'changes_from_LOWMEM':['reporting TSTART .09 -> 0s','title'],
        'changes_from_FINALPLOT':['reporting TSTART .09 -> 0s','IncrPlot 0 -> 1','title'],
        'capture_mode_matches_user_reported_passing_30ms':'TSTART=0 and IncrPlot=1; 100ms/4ch remains new and unverified.',
        'same_four_outputs':after['selected_outputs'], 'settings':after['transient_settings'],
        'all_components_ports_values_layout_models_controller_preserved':True,
        'all_solver_options_maxstep_tolerances_preserved':True,
        'existing_modified_U2_U4_INA240_and_U3_INA181_bias_models_retained':True,
        'all_three_original_unmodified_vendor_models':False,
        'exact_inverse_XML_verified':True,'two_DCL_decoders_verified':True,
        'native_run_performed':False,'native_100ms_pass_confirmed':False,
        'previous_missing_results_or_unknown_name_fixed_confirmed':False,
        'hardware_BOM_PCB_change':False,
        'limitation':'The screenshot proves only that Postprocessor has no available result in that UI snapshot. Cause and elapsed integration remain unknown. This restores full-window capture; no memory or convergence success is guaranteed.'}
    (ROOT/'results/data/2026-10-26_u3_100ms_from0_build_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
