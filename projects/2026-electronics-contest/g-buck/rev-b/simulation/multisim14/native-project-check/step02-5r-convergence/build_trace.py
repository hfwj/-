"""After two unsuccessful settings trials, collect switching evidence.

Based on the longer-running trapezoidal ITL300/25ms file. Add output flags
and explicitly pin the original method so it cannot inherit a prior Gear run.
No numeric solver values, schematic, vendor-model or control changes are made.
"""
from pathlib import Path
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block, elements, clean

EXTRA = ['$g_l', '$g_h', '$sw', 'll1#branch', '$16', '$7', '$17']


def main():
    source = PROJECT / 'downloads/GBUCK_STEP02_5R_ITL300_25ms_DIAG.ms14'
    logpath = ROOT / 'results/logs/native_Gear_25ms_failure_history.log'
    log = logpath.read_text()
    sections = re.split(r'(?=操作已执行)', log)
    last = [s for s in sections if '操作已执行' in s][-1]
    assert 'set method = "gear"' in last and 'set itl4 = 300' in last
    assert 'time = 0.0178381, timestep = 6.25e-018:trouble with node vfi1:xq2#branch' in last
    raw = source.read_bytes()
    xml, _ = unpack(raw)
    root = parse(xml)
    before = inspect(root)
    assert before['transient_settings'] == {'TSTOP': '0.025', 'TSTART': '0', 'TMAX': '5e-008', 'IC': 'auto_ic'}
    assert analysis_options(xml)['method'] == {'enabled': False, 'value': 'trapezoidal'}
    assert analysis_options(xml)['itl4'] == {'enabled': True, 'value': '300'}
    by = {p['display_ref']: p for p in components(root)}
    assert by['Q2']['ports'] == {'D': '15', 'G': '13', 'S': '0'}
    assert by['U1']['ports']['IN'] == '16' and by['U1']['ports']['^SD'] == '17'
    assert by['RS_IN']['ports']['2'] == '7'
    assert by['L1']['ports'] == {'1': '15', '2': '2'}
    mos = clean(elements(root, 'CiModel')[by['Q2']['model_id']].find('.//CiaCString').get('String'))
    assert re.search(r'^VFI1\s+11 6 0\s*$', mos, re.M)
    assert re.search(r'^FI1\s+7 9 VFI1 -1\s*$', mos, re.M)
    text = xml.decode('ascii')
    tran = block(text, 'TRAN')
    updated = tran
    edits = []
    for name in EXTRA:
        pattern = r'(NODE:list\{GROUP:long\{)(\d+)(\}\s*PLOTDEVICETYPE:long\{\d+\}\s*TYPE:long\{\d+\}\s*NAME:string\{' + re.escape(name) + r'\})'
        matches = list(re.finditer(pattern, updated))
        assert len(matches) == 1, name
        old = int(matches[0][2])
        assert not old & 256
        new = old | 768
        updated, n = re.subn(pattern, lambda m: m[1] + str(new) + m[3], updated)
        assert n == 1
        edits.append({'variable': name, 'old_group': old, 'new_group': new})
    opttext = block(updated, 'ASYS_OPT')
    method_pattern = r'(\d+:list\{IsEnabled:long\{)0(\}\s+method:string\{trapezoidal\}\s*\})'
    explicit_method, count = re.subn(method_pattern, lambda m: m[1] + '1' + m[2], opttext)
    assert count == 1
    updated = updated.replace(opttext, explicit_method, 1)
    changed = text.replace(tran, updated, 1).encode('ascii')
    assert changed.decode('ascii').replace(updated, tran, 1).encode('ascii') == xml
    newroot = parse(changed)
    assert components(newroot) == components(root)
    assert model_sources(newroot) == model_sources(root)
    expected_options = dict(analysis_options(xml), method={'enabled': True, 'value': 'trapezoidal'})
    assert analysis_options(changed) == expected_options
    after = inspect(newroot)
    assert set(after['selected_outputs']) == set(before['selected_outputs']) | set(EXTRA)
    expected = dict(before, selected_outputs=after['selected_outputs'])
    assert after == expected
    data = pack(changed)
    verify_independent_decoder(data, changed)
    dest = PROJECT / 'downloads/GBUCK_STEP02_5R_TRAP_ITL300_25ms_TRACE.ms14'
    dest.write_bytes(data)
    result = {
        'date': '2026-10-25', 'latest_native_log_sha256': hashlib.sha256(logpath.read_bytes()).hexdigest(),
        'Gear_was_enabled_in_native_log': True,
        'Gear_run_requested_s': .025, 'Gear_run_actual_end_s': .0178381,
        'Gear_native_completed': False, 'Gear_error_branch': 'vfi1:xq2#branch',
        'branch_role': 'zero-volt current probe within Q2 model capacitance-feedback network; not an external supply',
        'Gear_run_F1': 'user explicitly confirmed not blown',
        'chosen_trace_baseline': str(source.relative_to(PROJECT)),
        'baseline_reason': 'ITL300 trapezoidal reached 22.7726ms, longer than Gear 17.8381ms',
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'output': str(dest.relative_to(PROJECT)),
        'output_sha256': hashlib.sha256(data).hexdigest(), 'observation_flag_edits': edits,
        'selected_outputs': after['selected_outputs'], 'settings': after['transient_settings'],
        'options': analysis_options(changed),
        'only_observation_flags_and_original_method_enable_changed': True,
        'original_trapezoidal_method_explicitly_enabled_to_avoid_inherited_setting': True,
        'exact_inverse_XML_verified': True, 'two_DCL_decoders_verified': True,
        'all_connections_parts_values_models_controller_and_numeric_solver_values_preserved': True,
        'native_trace_run_performed': False, 'native_trace_convergence_verified': False,
        'root_cause': 'unresolved; neither ITL4 increase nor Gear completed 25ms; switching waveforms required'}
    (ROOT / 'results/data/Gear_failure_and_trace_build.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
