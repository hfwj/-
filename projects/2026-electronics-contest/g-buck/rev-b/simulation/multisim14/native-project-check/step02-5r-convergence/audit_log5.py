"""Audit the newest event, rather than mistaking cumulative old failures for it."""
import hashlib
import json
import re
from build_diagnostics import ROOT


def parse_events(text):
    sections = [s for s in re.split(r'(?=操作已执行)', text) if '操作已执行' in s]
    events = []
    for s in sections:
        options = dict(re.findall(r'set (reltol|abstol|vntol|chgtol|itl4|method) = ([^\r\n]+)', s))
        options = {k: v.strip().strip('"') for k, v in options.items()}
        failure = re.search(r'Timestep too small; time = ([\d.e+-]+), timestep = ([\d.e+-]+):trouble with (?:node )?([^\r\n]+)', s)
        assert failure
        events.append({'header': s.splitlines()[0].strip(), 'solver_options': options,
            'requested_end_s': float(re.search(r'停止时间（TSTOP）：([\d.e+-]+)', s)[1]),
            'maxstep_s': float(re.search(r'最大时间步长([\d.e+-]+)', s)[1]),
            'actual_end_s': float(failure[1]), 'failed_step_s': float(failure[2]),
            'reported_location': failure[3].strip(),
            'saved_variables': re.search(r'\bsave ([^\r\n]+)', s)[1].split(),
            'simulation_canceled': 'tran simulation(s) canceled' in s})
    return events


def main():
    path = ROOT / 'results/logs/native_REL001_25ms_failure_history.log'
    events = parse_events(path.read_text(encoding='utf-8-sig'))
    assert len(events) == 5
    latest = events[-1]
    assert latest['solver_options'] == {'reltol': '0.001', 'abstol': '1e-008',
        'vntol': '0.0001', 'chgtol': '1e-013', 'itl4': '300', 'method': 'trapezoidal'}
    assert latest['requested_end_s'] == .025 and latest['maxstep_s'] == 5e-8
    assert latest['actual_end_s'] == .0164408 and latest['failed_step_s'] == 6.25e-18
    assert latest['reported_location'] == '$n504417:x_ti:xu4'
    assert len(latest['saved_variables']) == 11 and latest['simulation_canceled']
    result = {'date': '2026-10-25', 'original_upload': '错误日志5.log',
        'original_log_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'history_events': events, 'latest_native_25ms_completed': False,
        'latest_F1_status': 'user explicitly confirmed not blown',
        'RELTOL_001_was_effective': True,
        'reduced_Q2_fixture_success_did_not_transfer_to_native_full_circuit': True,
        'model_mapping': {'native_xu4': 'displayed inductor-current amplifier U4 INA240A1',
            'database_internal_ref': 'U5', 'reported_node': 'N504417',
            'role': 'common-mode-controlled current source into internal 400uH/1ohm response branch; sensed by ideal voltage source E_E16',
            'not_a_proven_unique_root_cause': True},
        'next_diagnostic': 'Preserve REL001 settings/models, record actual U4 IN+/IN-/OUT/supply before modifying any device model.'}
    (ROOT / 'results/data/native_rel001_feedback.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'latest': latest, 'F1': result['latest_F1_status']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
