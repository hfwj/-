"""Preserve the failing 5-ohm upload; vary only ITL4 and diagnostic stop time.

No native solver runs here. Structural checks do not establish convergence.
"""
from pathlib import Path
import copy
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT.parent), str(ROOT.parent / 'step01-sense-feedback-fix')]
from ms14_project import PROJECT, unpack, pack, parse, inspect, components, clean, elements, block
from stabilize_transient import analysis_options, verify_independent_decoder
from build_fix import aliases, model_sources

SOURCE = PROJECT / 'references/user-projects/2026-10-25_STEP02_5R_21ms失败_原回传.ms14'
LOG = ROOT / 'results/logs/2026-10-25_native_history_original.log'
PRIOR = PROJECT / 'downloads/GBUCK_STEP02_U3_FEEDBACK_FIX.ms14'
NEW_ITL4 = 300
PATTERN = r'(\d+:list\{IsEnabled:long\{1\}\s+itl4:long\{)100(\}\s*\})'


def shape(root):
    # Reopening a project may renumber model object IDs, while actual definitions remain unchanged.
    return {p['display_ref']: {k: v for k, v in p.items() if k != 'model_id'}
            for p in components(root)}


def main():
    raw = SOURCE.read_bytes()
    xml, _ = unpack(raw)
    root = parse(xml)
    inspected = inspect(root)
    amap = aliases(root)
    by = {p['display_ref']: p for p in components(root)}
    assert by['RL']['parameters'][1] == '5'
    assert inspected['transient_settings'] == {'TSTOP': '0.1', 'TSTART': '0', 'TMAX': '5e-008', 'IC': 'auto_ic'}
    assert analysis_options(xml)['itl4'] == {'enabled': True, 'value': '100'}
    call = 'XCTRL %t1 %t2 VOUT V_CAP 7 L_RAW GBUCK_CTRL_EQ'
    assert xml.count(call.encode()) == 2
    assert by['U3']['ports'] == {'1': '22', '2': '0', '3': '3', '4': '4', '5': '0', '6': '21'}
    assert by['U2']['ports']['6'] == by['U4']['ports']['6'] == by['U3']['ports']['6'] == '21'
    assert by['F1']['parameters'][3] == '2'
    prior = parse(unpack(PRIOR.read_bytes())[0])
    changed_parts = [k for k in shape(root) if shape(root)[k] != shape(prior)[k]]
    assert changed_parts == ['RL']
    assert model_sources(root) == model_sources(prior)
    log = LOG.read_text(encoding='utf-8')
    events = []
    for section in re.split(r'(?=操作已执行)', log):
        if not section.strip():
            continue
        failures = re.findall(r'Timestep too small; time = ([\d.e+-]+), timestep = ([\d.e+-]+):trouble with node ([^\r\n]+)', section)
        events.append({'header': section.splitlines()[0], 'TSTOP': re.findall(r'停止时间（TSTOP）：([^\n]+)', section),
                       'failures': [{'time_s': float(t), 'attempted_step_s': float(h), 'branch': b} for t, h, b in failures]})
    failure_events = [e for e in events if e['failures']]
    assert len(failure_events) == 2
    assert all(e['failures'][0]['branch'] == 'v_v8:x_ti:xu2#branch' for e in failure_events)
    models = elements(root, 'CiModel')
    u2model = clean(models[by['U2']['model_id']].get('LocalName'))
    assert 'INA240A1' in u2model
    u2source = clean(models[by['U2']['model_id']].find('.//CiaCString').get('String'))
    assert re.search(r'V_V8\s+INN N409527 -7\.625uVdc', u2source)
    source_summary = {
        'date': '2026-10-25', 'source_sha256': hashlib.sha256(raw).hexdigest(),
        'original_log_sha256': hashlib.sha256(LOG.read_bytes()).hexdigest(),
        'actual_settings': inspected['transient_settings'], 'actual_options': analysis_options(xml),
        'actual_load_ohm': by['RL']['parameters'][1], 'controller_call': call,
        'parts_changed_from_initial_STEP02_20ohm': changed_parts,
        'all_embedded_models_match_initial_STEP02': True,
        'U2_model': u2model, 'U2_display_ref': 'U2', 'U2_internal_database_ref': by['U2']['internal_ref'],
        'branch_mapping': 'native xu2 is displayed input-current INA240 U2; database internal_ref U4 is not the displayed U4',
        'reported_branch_function': 'INA240 input-side ideal DC offset source, -7.625uV; location is not a proven unique root cause',
        'native_history': events,
        'last_history_entry_is_incomplete': True,
        'F1_current_5ohm_status': 'user explicitly confirmed not blown after this failure',
        'native_5ohm_100ms_pass': False}
    (ROOT / 'results/data/source_audit.json').write_text(json.dumps(source_summary, ensure_ascii=False, indent=2) + '\n')
    outputs = []
    for suffix, stop in [('ITL300_25ms_DIAG', '0.025'), ('ITL300_100ms_DIAG', '0.1')]:
        text = xml.decode('ascii')
        tran = block(text, 'TRAN')
        options_text = block(tran, 'ASYS_OPT')
        revised_options, n = re.subn(PATTERN, lambda m: m[1] + str(NEW_ITL4) + m[2], options_text)
        assert n == 1
        revised_tran = tran.replace(options_text, revised_options, 1)
        changed_time = stop != '0.1'
        if changed_time:
            assert revised_tran.count('TSTOP:double{0.1}') == 1
            revised_tran = revised_tran.replace('TSTOP:double{0.1}', 'TSTOP:double{' + stop + '}', 1)
        revised = text.replace(tran, revised_tran, 1)
        assert revised.replace(revised_tran, tran, 1).encode('ascii') == xml
        patched = revised.encode('ascii')
        result_root = parse(patched)
        assert components(result_root) == components(root)
        assert model_sources(result_root) == model_sources(root)
        a = copy.deepcopy(inspected)
        a['transient_settings']['TSTOP'] = stop
        assert inspect(result_root) == a
        options = analysis_options(xml)
        options['itl4']['value'] = str(NEW_ITL4)
        assert analysis_options(patched) == options
        data = pack(patched)
        verify_independent_decoder(data, patched)
        dest = PROJECT / 'downloads' / ('GBUCK_STEP02_5R_' + suffix + '.ms14')
        dest.write_bytes(data)
        outputs.append({'file': str(dest.relative_to(PROJECT)), 'sha256': hashlib.sha256(data).hexdigest(),
                        'ITL4_before': 100, 'ITL4_after': NEW_ITL4, 'TSTOP_before_s': .1, 'TSTOP_after_s': float(stop),
                        'exact_inverse_XML_verified': True, 'both_DCL_decoders_verified': True,
                        'all_parts_connections_values_and_models_unchanged': True,
                        'TMAX_tolerances_method_initial_conditions_outputs_preserved': True,
                        'native_open_and_run_performed': False,
                        'cross_solver_run_performed': False,
                        'crossed_native_failure_time_verified': False})
    (ROOT / 'results/data/build_checks.json').write_text(json.dumps(outputs, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'audit': source_summary, 'outputs': outputs}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
