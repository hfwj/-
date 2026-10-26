"""Preserve the latest failed tolerance trial and map its U3 node."""
import hashlib
import json
from audit_log5 import parse_events
from build_diagnostics import ROOT


def main():
    path=ROOT/'results/logs/2026-10-26_native_ABSTOL100nA_U3_failure_history.log'
    events=parse_events(path.read_text(encoding='utf-8-sig'));assert len(events)==2
    latest=events[-1]
    assert latest['header']=='操作已执行   (2026年10月26日, 13:06:44)'
    assert latest['solver_options']=={'reltol':'0.001','abstol':'1e-007',
        'vntol':'0.0001','chgtol':'1e-013','itl4':'300','method':'trapezoidal'}
    assert latest['requested_end_s']==.03 and latest['maxstep_s']==5e-8
    assert latest['actual_end_s']==.0201209 and latest['failed_step_s']==6.25e-18
    assert latest['reported_location']=='$inp_psrr_out:x_ti:xu3'
    assert latest['saved_variables']==['$g_h','$g_l','$iout_raw','$sw','$vdda','$vout','@rrs_out[i]','ll1#branch']
    result={'date':'2026-10-26','original_upload':'报错2.log',
        'original_log_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'events':events,'latest_ABSTOL100nA_and_8_outputs_effective':True,
        'native_30ms_completed':False,'latest_F1_status':'user explicitly confirmed not blown',
        'latest_node_mapping':'displayed U3 INA181, positive-input PSRR output feeding 25k input resistor; not U4 INA240 or Q2',
        'tolerance_trial_disposition':'failed; restore original ABSTOL 10nA in next candidate',
        'new_20_1209ms_waveforms_received':False,
        'old_24_9514ms_native_data_reanalysis':'U3 common mode (V_CAP+VOUT)/2 is about 5V; prior analysis omitted this quantity while listing U4 common mode',
        'old_data_do_not_prove_new_run_common_mode_or_native_absolute_failure_history':True,
        'next_step':'test narrowly scoped U3 IIB smoothing supported by controlled same-node reproduction; retain existing U2/U4 smoothing and undo tolerance relaxation'}
    (ROOT/'results/data/2026-10-26_native_ABSTOL100nA_U3_feedback.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'latest':latest,'F1':result['latest_F1_status']},indent=2))


if __name__=='__main__':main()
