"""Verify the native U4 observation run, without claiming unread waveforms."""
import hashlib
import json
from audit_log5 import parse_events
from build_diagnostics import ROOT


def main():
    path = ROOT / 'results/logs/native_U4_TRACE_25ms_failure_history.log'
    text = path.read_text(encoding='utf-8-sig')
    events = parse_events(text)
    assert len(events) == 6
    latest = events[-1]
    assert latest['header'] == '操作已执行   (2026年10月25日, 21:53:04)'
    assert latest['solver_options'] == {'reltol': '0.001', 'abstol': '1e-008',
        'vntol': '0.0001', 'chgtol': '1e-013', 'itl4': '300', 'method': 'trapezoidal'}
    assert latest['requested_end_s'] == .025 and latest['maxstep_s'] == 5e-8
    assert latest['actual_end_s'] == .0164408 and latest['failed_step_s'] == 6.25e-18
    assert latest['reported_location'] == '$n504417:x_ti:xu4'
    expected = ['$16', '$17', '$7', '$g_h', '$g_l', '$il_bi', '$iout_raw',
        '$l_raw', '$sw', '$v_cap', '$vdda', '$vout', '@rrs_out[i]', 'll1#branch']
    assert latest['saved_variables'] == expected and latest['simulation_canceled']
    lasttext = text.rsplit('操作已执行', 1)[1]
    assert '5R REL001 U4 boundary observation 25ms' in lasttext
    result = {'date': '2026-10-25', 'original_upload': '报错日志6.log',
        'original_log_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'history_event_count': len(events), 'latest_event': latest,
        'new_U4_observation_channels_effective': True,
        'failure_time_and_node_match_prior_REL001_run_at_log_precision': True,
        'latest_native_25ms_completed': False,
        'latest_F1_status': 'not separately confirmed for this run; earlier run was explicitly not blown',
        'uploaded_archive_name': 'GBUCK_STEP02_5R_ITL300_25ms_DIAG.rar',
        'waveform_transfer_status': 'download_file rejected: exceeds 32 MiB transfer limit',
        'waveforms_read': False, 'archive_sha256': None,
        'U4_boundary_metrics': None,
        'next_step': 'Split the existing RAR as a WinRAR multivolume archive with each volume <=25 MB and send all volumes; no simulation rerun is required.',
        'scope': 'Evidence and documentation only. No schematic, component, BOM, PCB, model, control, stimulus or solver setting changes.'}
    (ROOT / 'results/data/native_u4_trace_feedback.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
