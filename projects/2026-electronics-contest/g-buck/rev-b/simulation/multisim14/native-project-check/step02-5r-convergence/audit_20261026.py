"""Audit the new 14-channel native failure, without assuming LOWMEM was run."""
import hashlib
import json
import re
from audit_log5 import parse_events
from build_diagnostics import ROOT, PROJECT, unpack, parse, components, elements, clean


def main():
    path=ROOT/'results/logs/2026-10-26_native_14ch_Q2_VFI2_failure.log'
    text=path.read_text(encoding='utf-8-sig');events=parse_events(text)
    assert len(events)==1
    latest=events[0]
    assert latest['header']=='操作已执行   (2026年10月26日, 10:07:16)'
    assert latest['solver_options']=={'reltol':'0.001','abstol':'1e-008',
        'vntol':'0.0001','chgtol':'1e-013','itl4':'300','method':'trapezoidal'}
    assert latest['requested_end_s']==.1 and latest['maxstep_s']==5e-8
    assert latest['actual_end_s']==.0249514 and latest['failed_step_s']==6.25e-18
    assert latest['reported_location']=='vfi2:xq2#branch' and latest['simulation_canceled']
    start=float(re.search(r'起始时间（TSTART）：([\d.e+-]+)',text)[1]);assert start==0
    expected=['$16','$17','$7','$g_h','$g_l','$il_bi','$iout_raw','$l_raw',
        '$sw','$v_cap','$vdda','$vout','@rrs_out[i]','ll1#branch']
    assert latest['saved_variables']==expected
    source=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14'
    root=parse(unpack(source.read_bytes())[0]);by={p['display_ref']:p for p in components(root)}
    assert by['Q2']['ports']=={'D':'15','G':'13','S':'0'}
    model=clean(elements(root,'CiModel')[by['Q2']['model_id']].find('.//CiaCString').get('String'))
    assert re.search(r'^VFI2\s+4 0 0\s*$',model,re.M)
    assert re.search(r'^FI2\s+7 9 VFI2 -1\s*$',model,re.M)
    assert re.search(r'^D2\s+4 5 MD1\s*$',model,re.M)
    result={'date':'2026-10-26','original_upload':'报错.log',
        'original_log_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'latest_event':latest,'TSTART_s':start,'F1_status':'user explicitly confirmed not blown for this run',
        'does_not_match_delivered_LOWMEM_90ms_4ch_settings':True,
        'LOWMEM_native_effect_still_unverified':True,
        'error_type_this_log':'transient nonconvergence / timestep too small',
        'memory_error_reported_in_this_log':False,'native_100ms_completed':False,
        'model_mapping_baseline':str(source.relative_to(PROJECT)),
        'baseline_model_file_bytes_verified_against_current_user_project':False,
        'Q2_model_sha256':hashlib.sha256(model.encode()).hexdigest(),
        'VFI2_role':'zero-volt current sensor paired with FI2 in Q2 macro capacitance feedback network; not external power supply or physical failure indication',
        'new_numeric_waveforms_received':False,
        'older_GRA_and_TXT_are_not_boundaries_for_this_new_24_9514ms_event':True,
        'next_action':'Preserve existing latest 100ms Grapher page as GRA, compress in <=25MB volumes and send all; no new simulation is needed to capture already saved GH/GL/SW/IL.',
        'changes_this_turn':'log preservation, model-node mapping and documentation only; no schematic/BOM/PCB/model/control/stimulus/solver changes'}
    (ROOT/'results/data/2026-10-26_native_Q2_VFI2_feedback.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
