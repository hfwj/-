"""Extend the user-reported passing U3 diagnostic; limit saved output only.

Preserve all circuit, model and solver options. TSTART controls reporting;
startup is still integrated from zero. No native Multisim run occurs here.
"""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block

KEEP = {'$vout', '@rrs_out[i]', '$iout_raw', '$vdda'}


def main():
    source = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_30ms_8CH_DIAG.ms14'
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'b559650ead189f4579c1f4fb468fc4451546fd86465192ff93706b909f49a71e'
    xml, _ = unpack(raw)
    root = parse(xml)
    before = inspect(root)
    opts = analysis_options(xml)
    assert before['transient_settings'] == {'TSTOP':'0.03','TSTART':'0','TMAX':'5e-008','IC':'auto_ic'}
    assert len(before['selected_outputs']) == 8 and KEEP.issubset(before['selected_outputs'])
    for key, value in [('abstol','1e-008'), ('reltol','0.001'), ('itl4','300'), ('method','trapezoidal')]:
        assert opts[key] == {'enabled':True, 'value':value}
    text = xml.decode('ascii')
    tran = block(text, 'TRAN')
    revised = tran
    for old, new in [('TSTOP:double{0.03}', 'TSTOP:double{0.1}'),
                     ('TSTART:double{0}', 'TSTART:double{0.09}')]:
        assert revised.count(old) == 1
        revised = revised.replace(old, new, 1)
    edits = []
    pattern = (r'(NODE:list\{GROUP:long\{)(\d+)'
               r'(\}\s*PLOTDEVICETYPE:long\{\d+\}\s*TYPE:long\{\d+\}\s*NAME:string\{([^}]+)\})')
    def deselect(match):
        group = int(match[2])
        if group & 768 and match[4] not in KEEP:
            new = group & ~768
            edits.append({'variable':match[4], 'before':group, 'after':new})
            return match[1]+str(new)+match[3]
        return match[0]
    revised = re.sub(pattern, deselect, revised)
    assert len(edits) == 4
    revised, n = re.subn(r'PLOT_TITLE:string\{[^}]*\}',
        'PLOT_TITLE:string{5R U3 IIB SMOOTH 0.1mV ABSTOL10nA 100ms LOWMEM record90-100ms 4ch}', revised)
    assert n == 1
    changed = text.replace(tran, revised, 1).encode('ascii')
    assert changed.decode('ascii').replace(revised, tran, 1).encode('ascii') == xml
    newroot = parse(changed)
    after = inspect(newroot)
    assert components(newroot) == components(root)
    assert model_sources(newroot) == model_sources(root)
    assert analysis_options(changed) == opts
    assert set(after['selected_outputs']) == KEEP
    assert after == dict(before, selected_outputs=after['selected_outputs'],
        transient_settings=dict(before['transient_settings'], TSTOP='0.1', TSTART='0.09'))
    data = pack(changed)
    verify_independent_decoder(data, changed)
    dest = PROJECT/'downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_LOWMEM.ms14'
    dest.write_bytes(data)
    result = {
        'date':'2026-10-26',
        'baseline':str(source.relative_to(PROJECT)),
        'baseline_sha256':hashlib.sha256(raw).hexdigest(),
        'baseline_status':'User explicitly reported pass and F1 not blown; no new log or numerical waveform supplied in that message.',
        'output':str(dest.relative_to(PROJECT)),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'only_changes':['TSTOP 30 -> 100ms','reporting TSTART 0 -> 90ms','8 -> 4 output selections','plot title'],
        'settings':after['transient_settings'], 'outputs':after['selected_outputs'],
        'removed_output_flags':edits, 'options':opts,
        'all_components_ports_values_layout_models_controller_preserved':True,
        'all_solver_options_maxstep_and_tolerances_preserved':True,
        'existing_modified_U2_U4_INA240_and_U3_INA181_IIB_models_retained':True,
        'unchanged_vendor_models_for_all_devices':False,
        'reporting_is_not_restart_or_shortened_integration':True,
        'memory_error_resolution_is_not_verified_or_guaranteed':True,
        'exact_inverse_XML_verified':True, 'two_DCL_decoders_verified':True,
        'native_100ms_run_performed':False, 'native_100ms_completed':False,
        'hardware_BOM_PCB_change':False}
    (ROOT/'results/data/2026-10-26_u3_100ms_lowmem_build_checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
