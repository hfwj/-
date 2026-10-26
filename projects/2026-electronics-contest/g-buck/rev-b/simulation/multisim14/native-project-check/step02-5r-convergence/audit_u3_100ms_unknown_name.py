"""Audit the two native 100ms attempts without declaring numerical completion."""
import hashlib
import json
import re
from build_diagnostics import ROOT, PROJECT


def main():
    source = ROOT/'results/logs/2026-10-26_native_U3_100ms_UnknownName_history.log'
    data = source.read_bytes()
    text = data.decode('utf-8-sig')
    sections = [s for s in re.split(r'(?=操作已执行)', text) if s.strip()]
    assert len(sections) == 2
    runs = []
    for s in sections:
        title = re.search(r'图表标题：([^\r\n]+)', s)[1].strip()
        assert title == '5R U3 IIB SMOOTH 0.1mV ABSTOL10nA 100ms LOWMEM record90-100ms 4ch'
        save = re.search(r'\bsave ([^\r\n]+)', s)[1].split()
        assert save == ['$iout_raw', '$vdda', '$vout', '@rrs_out[i]']
        tran = re.search(r'\btran\s+-env-options ([^\r\n]+)', s)[1].split()
        assert [float(x) for x in tran[:4]] == [5e-8, .1, .09, 5e-8]
        assert tran[4:] == ['auto_ic']
        options = {k:re.search(r'\bset '+k+r' = ([^\r\n]+)', s)[1].strip().strip('"')
                   for k in ['reltol','abstol','vntol','chgtol','itl4','method']}
        assert options == {'reltol':'0.001','abstol':'1e-008','vntol':'0.0001',
                           'chgtol':'1e-013','itl4':'300','method':'trapezoidal'}
        errors = re.findall(r'\bError: ([^\r\n]+)', s)
        assert errors == ['Unknown name: V(iout_raw)']
        assert not re.search(r'Timestep too small|Simulation canceled|insufficient memory', s, re.I)
        assert s.rfind('Error:') > s.rfind('v_switch models')
        assert '以增量方式绘制经保存的变量' in s
        runs.append({'header':s.splitlines()[0].strip(), 'title':title,
            'save_variables':save, 'tran_arguments':tran, 'options':options, 'errors':errors,
            'incremental_plot_enabled_in_log':True,
            'result_file_reported_saved':'结果已保存至文件' in s,
            'show_all_device_and_model_tables_present':'showmod all' in s and 'Mos1:' in s,
            'no_logged_timestep_cancellation_or_memory_error':True,
            'exact_last_time_s':None, 'native_100ms_pass_confirmed':False})
    result = {'date':'2026-10-26','timezone':'Asia/Shanghai',
        'source':str(source.relative_to(PROJECT)), 'source_bytes':len(data),
        'source_sha256':hashlib.sha256(data).hexdigest(), 'runs':runs,
        'F1_latest_user_report':'未熔断', 'fresh_numeric_waveform_received':False,
        'user_followup_verbatim':'没有曲线',
        'user_confirmed_no_90_to_100ms_curve_after_both_runs':True,
        'classification':'Output name/result-processing error; no numerical convergence failure recorded in these runs.',
        'causality_not_proven':'Log does not establish whether delayed reporting plus incremental plotting, alias mapping, or missing result data causes the unresolved name.',
        'next_isolation':'Keep models, solver, names, time window and four outputs; disable incremental plotting only, plus diagnostic title.',
        'native_100ms_pass_confirmed':False, 'hardware_BOM_PCB_change':False}
    (ROOT/'results/data/2026-10-26_native_U3_100ms_UnknownName_feedback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
