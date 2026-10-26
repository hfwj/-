"""Check effective capture mode without mistaking a partial status log for a pass."""
import hashlib
import json
import re
from build_diagnostics import ROOT, PROJECT


def main():
    source = ROOT/'results/logs/2026-10-26_native_U3_100ms_FINALPLOT_status.log'
    data = source.read_bytes()
    text = data.decode('utf-8-sig')
    assert len(re.findall('操作已执行', text)) == 1
    title = re.search(r'图表标题：([^\r\n]+)', text)[1].strip()
    assert title == '5R U3 IIB SMOOTH 0.1mV ABSTOL10nA 100ms FINALPLOT record90-100ms 4ch'
    saved = re.search(r'\bsave ([^\r\n]+)', text)[1].split()
    assert saved == ['$iout_raw', '$vdda', '$vout', '@rrs_out[i]']
    tran = re.search(r'\btran\s+-env-options ([^\r\n]+)', text)[1].split()
    assert [float(v) for v in tran[:4]] == [5e-8, .1, .09, 5e-8]
    assert tran[4:] == ['auto_ic']
    options = {k:re.search(r'\bset '+k+r' = ([^\r\n]+)', text)[1].strip().strip('"')
               for k in ['reltol','abstol','vntol','chgtol','itl4','method']}
    assert options == {'reltol':'0.001','abstol':'1e-008','vntol':'0.0001',
                       'chgtol':'1e-013','itl4':'300','method':'trapezoidal'}
    assert '已保存了分析得出的变量，供以后处理' in text
    commands = [re.sub(r'^[|\s]+', '', line) for line in text.splitlines()]
    assert not any(re.match(r'iplot(?:Ext)?\s+', line) for line in commands)
    assert 'write-and-destroy-iplot' in text
    errors = re.findall(r'\bError: ([^\r\n]+)', text)
    assert errors == []
    assert not re.search(r'Timestep too small|Simulation canceled|insufficient memory', text, re.I)
    assert text.rstrip().endswith('Dynamic Gmin stepping completed')
    result = {'date':'2026-10-26','timezone':'Asia/Shanghai',
        'source':str(source.relative_to(PROJECT)), 'source_bytes':len(data),
        'source_sha256':hashlib.sha256(data).hexdigest(),
        'operation_header':text.splitlines()[0].strip(), 'title':title,
        'save_variables':saved, 'tran_arguments':tran, 'options':options,
        'incremental_plot_disabled_effective':True,
        'log_explicitly_says_saved_for_later_processing':True,
        'iplot_and_iplotExt_commands_absent':True,
        'write_and_destroy_iplot_still_present':True,
        'writer_name_alone_is_not_evidence_incremental_plotting_is_enabled':True,
        'recorded_errors':errors, 'last_output_line':'Dynamic Gmin stepping completed',
        'numerical_last_time_s':None, 'native_100ms_pass_confirmed':False,
        'previous_unknown_name_error_absent_in_this_snapshot':True,
        'previous_unknown_name_error_fixed_confirmed':False,
        'new_run_end_state_user_confirmed':None,
        'new_run_curve_status_user_confirmed':'没图像生成',
        'new_run_no_automatic_curve_user_confirmed':True,
        'new_run_F1_user_confirmed':None,
        'F1_prior_run_status_not_carried_forward':True,
        'next_step':'Confirm whether this run ended; if ended, inspect actual saved dataset and available vectors in Postprocessor before deciding to rerun.',
        'scope':'Archive and documentation only; no project, schematic, BOM, PCB, model, controller or solver edits.'}
    (ROOT/'results/data/2026-10-26_native_U3_100ms_FINALPLOT_status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
