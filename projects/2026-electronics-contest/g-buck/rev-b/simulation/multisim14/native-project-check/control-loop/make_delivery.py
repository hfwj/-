"""Package only a completed, matching set of extracted delivery tests."""
from pathlib import Path
import sys,json,hashlib,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from build_projects import ROOT,PROJECT,SOURCE,CASES,output_path,extract_netlist


def main():
    summary=json.loads((ROOT/'results/data/verification_summary.json').read_text())
    assert summary['all_transients_completed'] and summary['all_steady_targets_passed']
    rows=summary['cases'];checks=[]
    for case,row in zip(CASES,rows):
        assert case['id']==row['id']
        path=output_path(case)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['project_sha256']
        assert hashlib.sha256(extract_netlist(path).encode()).hexdigest()==row['solver_source_sha256']
        checks.append({'id':case['id'],'binary_and_extracted_source_match_completed_run':True})
    lines=['# 当前工程：软启动与10V/1A功能控制仿真','',
           '日期：2026-10-24。基于用户当前已运行的保险丝对照工程，保留原件并加入理想控制模型。自动交叉数据来自ngspice，用户本机截图反馈在后文单独记录。','',
           '先下载[专用ZIP](../downloads/Multisim14_软启动与CVCC控制副本_2026-10-24.zip)，打开其中的25V/20Ω恒压文件。完整操作、模型绑定与假设见[控制副本说明](../simulation/multisim14/native-project-check/control-loop/README.md)。','',
           '| 工况 | 实际结束时间/ms | 末2ms输出/V | 末2ms输出电流/A | 输出最大值/V | 稳态目标 |','|---|---:|---:|---:|---:|---|']
    for row in rows:
        mean=row['last_2ms_time_means']
        lines.append(f'| {row["id"]} | {row["actual_end_time_s"]*1000:.1f} | {mean["VOUT_V"]:.4f} | {mean["IOUT_A"]:.4f} | {row["VOUT_max_V"]:.4f} | {"通过" if row["steady_target_passed"] else "未通过"} |')
    lines+=['','上述均为ngspice开关模型交叉求解，不是本环境运行Multisim。输出电流指RS_OUT之后的总电流；空载工况仍保留2.2kΩ泄放电阻。稳态窗口满足10V±0.5V或1A±0.1A，不代表每个启动/负载变化瞬间满足同一限制。','',
            '自动负载在18～18.1ms由20Ω变8Ω、28～28.1ms变5Ω，各窗口结果：','',
            '| 区间 | 输出/V | 输出电流/A | 模式 |','|---|---:|---:|---|']
    for seg in rows[-1]['segments']:lines.append(f'| {seg["name"]} | {seg["VOUT_mean_V"]:.4f} | {seg["IOUT_mean_A"]:.4f} | {seg["mode"]} |')
    lines+=['',f'自动负载工况全程输出电流最大值约{rows[-1]["IOUT_max_A"]:.4f}A，必须与1A稳态目标区分。','',
            '控制源V3的SPICE模板已改为理想电压/电流控制及软启动，固定脉宽参数不再决定闭环PWM。画布沿用原源符号，反馈通过当前网络VOUT、3、7、2绑定；不是逐元件重画了原图控制链。','',
            '本控制假设允许轻载短时负电感电流指令至−0.15A，不是实际电池的充放电策略。原F1仍断开、R1=1mΩ仍接通，故真实保险丝、过流锁存和保护未验证；原方案2A保险丝不能据此取消。采样理想化，实际固件、INA/ADC误差、显示和总效率尚未验证。','',
            '原上传工程保存在[用户工程目录](../references/user-projects/2026-10-24_本机可运行_保险丝对照.ms14)，SHA256：`'+summary['source_working_project_sha256']+'`。','',
            '[最终验证JSON](../simulation/multisim14/native-project-check/control-loop/results/data/verification_summary.json) · [工况波形](../simulation/multisim14/native-project-check/control-loop/results/figures/closed_loop_overview.png)。','']
    feedback_file=ROOT/'results/data/native_user_feedback.json'
    if feedback_file.exists():
        feedback=json.loads(feedback_file.read_text())
        lines+=['## 用户本机后续反馈','',
                '以下按用户截图估读，与上面的自动交叉数据分别记录，未取得精确数值导出。','',
                '| 工况 | 截图时长/ms | 末段输出约/V | 末段电流约/A | 启动峰值约/V |','|---|---:|---:|---:|---:|']
        for row in feedback['cases']:
            row={**row,**(row.get('follow_up_observations') or [{}])[-1]}
            current=f'{row["approximate_IOUT_end_A"]:.1f}' if 'approximate_IOUT_end_A' in row else '未显示'
            lines.append(f'| {row["id"]} | {row["displayed_time_range_s"][1]*1000:.0f} | {row["approximate_VOUT_end_V"]:.1f} | {current} | {row["approximate_VOUT_peak_V"]:.1f} |')
        lines.append('')
        for row in feedback['cases']:
            if row.get('observation_note'):lines += [row['id']+'：'+row['observation_note'],'']
        pending=feedback.get('other_case_native_feedback_pending',[])
        lines += [('仍待本机反馈：'+', '.join(pending)+'。') if pending else '已收到列出工况的本机截图；精确测量及未解决的瞬态问题仍需分别核查。','']
        lines+=['不能据此认定真实固件、保护、效率或原图整机通过。见[本机截图观察记录](../simulation/multisim14/native-project-check/control-loop/results/data/native_user_feedback.json)。','',
                '反馈归档只更新记录、报告与资料包，不改变原理图连线、器件/BOM/PCB或已交付原生工程的模型和参数。','']
    if feedback_file.exists():
        revisions=feedback.get('control_revision_observations',[])
        if revisions:
            lines+=['## 控制参数修订后的独立本机观察','',
                    '这些是Ki20修订控制的独立截图，不能与前面的Ki100短窗口结果合并称为同一套回归通过。','']
            for item in revisions:
                detail=item.get('summary_zh') or f'Ki={item["model_voltage_Ki"]}，100ms末段约{item["approximate_VOUT_end_V"]:.1f}V，启动峰值约{item["approximate_VOUT_peak_V"]:.1f}V；起伏可见衰减，精确限值与其他同参数工况仍待核查。'
                lines+=['- '+item['id']+'：'+detail]
            lines+=['','下一步见[Ki20静态回归](../simulation/multisim14/native-project-check/control-loop/kiv20-regression/README.md)。','']
    lines+=['## 100ms空载后续检查','',
            '早期Ki100的15V空载本机100ms图显示约9.6～10.4V、周期约20ms的持续低频起伏，不能将早期30ms末2ms窗口满足目标解释为充分稳定。精确波形数据与100ms保存工程未回传。原七工程和控制参数均未改动。','']
    long_file=ROOT/'results/data/CV_15V_OPEN_100ms_diagnostic.json'
    if long_file.exists():
        diagnostic=json.loads(long_file.read_text())
        lines+=['另做同参数100ms ngspice诊断，F1仅以固定导通电阻近似，不验证熔断动作。完整到达终点：'+str(diagnostic['full_transient_completed'])+'。','']
        if not diagnostic['full_transient_completed']:
            lines+=['本次交叉求解达到300秒执行时限，未导出完整波形；不计为验证通过，也不能据此认定收敛失败。用户本机100ms截图观察独立保留。','']
        for window in diagnostic.get('late_20ms_windows',[]):
            lines.append(f'- {window["time_s"][0]*1000:.0f}～{window["time_s"][1]*1000:.0f}ms：完整采样VOUT范围{window["VOUT_range_V"][0]:.4f}～{window["VOUT_range_V"][1]:.4f}V。')
        lines+=['','交叉诊断尝试与本机截图估读分别记录；原因尚未由此确定。见[100ms诊断记录](../simulation/multisim14/native-project-check/control-loop/results/data/CV_15V_OPEN_100ms_diagnostic.json)。','']
    report=PROJECT/'reports/Multisim14_软启动与CVCC控制仿真_2026-10-24.md';report.write_text('\n'.join(lines))
    package=PROJECT/'downloads/Multisim14_软启动与CVCC控制副本_2026-10-24.zip'
    paths=[SOURCE,report,*[output_path(c) for c in CASES]]
    conclusion=PROJECT/'reports/Multisim14_本机工况反馈阶段结论_2026-10-24.md'
    if conclusion.exists():paths.append(conclusion)
    returned=PROJECT/'references/user-projects/2026-10-24_15V空载_恢复F1_本机回传.ms14'
    if returned.exists():paths.append(returned)
    helper=ROOT.parent
    paths.extend(helper/n for n in ['ms14_project.py','verify_power_stage.py','verify_driver.py','stabilize_transient.py','requirements.txt'])
    paths.extend(p for p in ROOT.rglob('*') if p.is_file() and p.suffix in ['.py','.md','.lib','.json','.csv','.log','.png'] and '__pycache__' not in p.parts and p.name!='delivery_checks.json')
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as archive:
        archive.writestr('请先阅读.txt','先打开downloads/GBUCK_CTRL_EQ_CV_25V_20R_native_check.ms14，运行30ms瞬态。\n这是软启动和CV/CC功能等效控制模型；自动交叉数据与用户本机截图反馈分别归档。\n七工况本机截图已收到；15V空载回传原件已接回F1，单独保存在references/user-projects，原交付副本保持。\n其他工况、假设与界限见simulation/multisim14/native-project-check/control-loop/README.md。\n真实固件、传感器、保护及效率尚未验证。\n轻量包不含NPZ完整分辨率窗口，窗口文件保存在GitHub相应results/data/。\n')
        for p in sorted(set(paths)):archive.write(p,str(p.relative_to(PROJECT)))
    with zipfile.ZipFile(package) as archive:assert archive.testzip() is None
    result={'date':'2026-10-24','all_delivery_files_match_completed_runs':True,'cases':checks,'source_file_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==summary['source_working_project_sha256'],
            'native_multisim_execution_verified':False,'package_file':str(package.relative_to(PROJECT)),
            'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'package_bytes':package.stat().st_size,'zip_integrity_verified':True}
    (ROOT/'results/data/delivery_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
