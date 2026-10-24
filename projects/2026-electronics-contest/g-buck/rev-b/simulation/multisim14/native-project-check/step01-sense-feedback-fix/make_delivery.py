"""Report the returned circuit audit and alias-aware A/B solver evidence."""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    read = lambda name: json.loads((ROOT / 'results/data' / name).read_text())
    build = read('build_checks.json')
    bad = read('original_alias_mismatch_verification.json')
    good = read('fixed_trap_200ns_verification.json')
    fine = read('fixed_verification.json')
    gear = read('fixed_gear_verification.json')
    timestep = read('timestep_comparison.json')
    native = PROJECT / build['output']
    baseline = PROJECT / build['baseline']
    assert sha(native) == build['output_sha256'] == good['project_sha256']
    assert sha(baseline) == build['baseline_sha256'] == bad['project_sha256']
    assert good['passed'] and bad['full_requested_transient_completed']
    assert bad['metrics']['controller_IL_tail_mean_A'] == 0
    assert bad['metrics']['IL_max_A'] > 3
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    arrays = {}
    for name in ['original_alias_mismatch', 'fixed']:
        case_file = 'fixed_trap_200ns' if name == 'fixed' else name
        path = ROOT / 'results/data' / (case_file + '_sampled.csv')
        names = path.read_text().splitlines()[0].split(',')
        data = np.loadtxt(path, delimiter=',', skiprows=1)
        arrays[name] = {key: data[:, index] for index, key in enumerate(names)}
    fig, axes = plt.subplots(3, 2, figsize=(13, 9))
    for column, (name, title) in enumerate([('original_alias_mismatch', 'Returned file: stale numeric feedback, 7ms'),
                                          ('fixed', 'Corrected aliases: 30ms')]):
        a = arrays[name]
        time = a['time'] * 1000
        for key, label in [('i(l1)', 'Physical IL'), ('v(xctrl.ilraw)', 'Controller measured IL')]:
            axes[0, column].plot(time, a[key], label=label, linewidth=.7)
        axes[0, column].set_title(title)
        axes[0, column].set_ylabel('A')
        for key, label in [('v(vdda)', 'VDDA'), ('v(il_bi)', 'IL_BI'), ('v(iin_raw)', 'IIN_RAW')]:
            axes[1, column].plot(time, a[key], label=label, linewidth=.7)
        axes[1, column].set_ylabel('V')
        axes[2, column].plot(time, a['v(vout)'], label='VOUT')
        axes[2, column].set_ylabel('V')
        axes[2, column].set_xlabel('ms')
        for row in range(3):
            axes[row, column].grid(True, alpha=.25)
            axes[row, column].legend()
    fig.suptitle('Independent ngspice check; conducting fuse only; user native screenshot received, VOUT pending')
    fig.tight_layout()
    fig.savefig(ROOT / 'results/figures/alias_feedback_comparison.png', dpi=150)
    plt.close(fig)
    metrics = good['metrics']
    tail = good['time_weighted_tail']
    report = PROJECT / 'reports/Multisim14_STEP01采样接入_反馈别名修正_2026-10-25.md'
    lines = ['# STEP01采样接入：控制反馈别名修正', '',
        '2026-10-25归档（调查始于10月24日）。依据用户实际回传GBUCK_STEP01_IL_SENSE.ms14.ms14核对并修正。原文件保存，不覆盖。', '',
        '**结论：U2/U4采样极性、供电、参考与去耦接线正确；V3内部控制模板仍用已被网络别名替代的数字节点2/3，导致原理想控制器读不到真实电感差压。修正只改两个端口引用。**', '',
        '## 本机下一步', '',
        '用户已反馈修正版本机30ms截图，原约6A异常消失，VDDA约3.26V、零电流IL_BI约1.63V，采样与电感电流变化方向一致。后段电流仍有明显起伏，VOUT未显示，尚不能判为本机恒压/稳定性通过。下一步优先从已有结果添加V(VOUT)，再核对最大时间步长，避免盲目重算或调控制器。', '',
        '暂不继续接比较器/锁存，先确认主回路电流回到受控范围且U4采样未贴近电源上限。如仍中止，保留完整报错与当前工程；本环境没有运行Windows Multisim。', '',
        '本机截图电感峰值仅可粗读约1.4A，与独立求解峰值不完全一致；两者设置/引擎有差异，不混写数值。图示器自动缩放/抽点与实际纹波也需区分。未收到本机数值导出或峰值光标测量。', '',
        '## 文件核对', '',
        '| 实际内部节点 | 用户网络别名 | 含义 |', '|---|---|---|',
        '| 2 | L_RAW | L1之后、RS_L之前 |',
        '| 3 | V_CAP | RS_L之后、输出电容正端 |',
        '| 7 | 无新别名 | RS_IN之后的输入母线 |',
        '| 4 | VOUT | RS_OUT之后 |', '',
        '内部节点标识没有重编号；问题是导出网络名已改成别名，而V3自定义模板中的文字引用不会自动随绘图别名更新。', '',
        '原调用：`XCTRL %t1 %t2 VOUT 3 7 2 GBUCK_CTRL_EQ`', '',
        '新调用：`XCTRL %t1 %t2 VOUT V_CAP 7 L_RAW GBUCK_CTRL_EQ`', '',
        '只替换活动模板及元件元数据中的两处调用。控制方程、Ki20、1A指令、10ms软启动、功率/驱动/INA模型均不改。输入母线当前仍导出为7，保持对应。', '',
        'U2：IN+接RS_IN输入端，IN−接VIN，REF1/REF2为地；U4：IN+接L_RAW，IN−接V_CAP，REF1接VDDA、REF2接地。两颗VS均接VDDA，各100nF去耦已接地，NC脚均悬空；R_VDDA与五个模拟电源电容连接核对通过。', '',
        '## 独立交叉求解', '',
        '按实际网络别名提取用户电路和嵌入模型，使用ngspice PSpice兼容模式。未将提取的第三方功率/驱动模型另行发布为独立库。', '',
        f'- 原失配副本完成7ms；物理电感峰值约{bad["metrics"]["IL_max_A"]:.4f}A，控制器内部电感电流读数为0，末点VOUT约{bad["metrics"]["VOUT_end_V"]:.4f}V。复现了反馈失效机制，但不声称与用户截图逐点一致。',
        f'- 修正副本完成30ms，共{good["points"]}点；电感峰值约{metrics["IL_max_A"]:.4f}A，末点VOUT约{metrics["VOUT_end_V"]:.4f}V。',
        f'- 25～30ms按时间积分的平均电感电流约{tail["IL_mean_A"]:.6f}A，输入分流器电流约{tail["IIN_mean_A"]:.6f}A，平均输出电压约{tail["VOUT_mean_V"]:.6f}V。',
        f'- U4平均传递关系误差（IL_BI−VDDA/2−0.5IL）约{tail["IL_BI_error_V"]:.7f}V。', '',
        '| 修正副本检查 | 结果 |', '|---|---|']
    lines.extend(f'| {key} | {"通过" if value else "未通过"} |' for key, value in good['checks'].items())
    lines += ['', '![对照波形](../simulation/multisim14/native-project-check/step01-sense-feedback-fix/results/figures/alias_feedback_comparison.png)', '',
        '### 范围', '',
        '- 完整30ms交叉求解使用梯形法、200ns最大步长；原生工程仍保留用户的自动最大步长及原初始条件/容差。不把它当成与本机相同的求解设置，也不据此认证纳秒边沿精度。',
        f'- 修正副本另以50ns梯形法推进到{fine["actual_end_s"]*1000:.3f}ms后达到480s执行时限，未完成30ms；该段电感峰值{fine["metrics"]["IL_max_A"]:.6f}A。保留限时记录，不把它认作收敛失败。',
        f'- Gear方法对照在约{gear["actual_end_s"]*1000:.3f}ms发生步长过小，未完成，记录保留；未将原生文件改成Gear。',
        f'- 50ns与200ns结果在共同区间的降采样VOUT插值最大差约{timestep["max_VOUT_difference_V"]*1000:.2f}mV，未达到附加50mV一致性目标。这里只比较平滑输出电压，不比较开关边沿或电流高频峰值；本轮不验收数值精度/稳定性。',
        '- F1在交叉求解中仅用1mΩ导通电阻，不模拟热熔断/I²t。原生F1仍保留原2A器件，未短接、替换或提高额定值。原文件异常时本机熔断/中止行为不能由这个静态等效复现。',
        '- 25～30ms正式平均值取完整轨迹时间积分；metrics中的tail_mean是按采样点平均的诊断量，不能混用。图及CSV降采样不用于认证全部高频峰值，峰值指标取完整轨迹。',
        '- 新增U2/U4目前只供观察；Ki20仍用RS_L两端的理想差压反馈，尚未改成INA→ADC→固件控制。比较器与锁存保护尚未接入，不继承此前内部功能模型的保护通过结论。',
        '- 临时SIM_3V3仍为独立测试源，不能以此结果判定整机效率、辅助电源性能或真实固件。', '',
        '## 修改影响', '',
        '比较基线为本次用户回传文件。', '',
        '| 类别 | 本次影响 |', '|---|---|',
        '| 原理图连线/引脚/器件值/布局 | 全部保留，无修改 |',
        '| 物理器件/BOM/PCB | 不新增、更换或改板 |',
        '| 仿真模型 | 仅V3调用参数3→V_CAP、2→L_RAW；原控制方程和嵌入厂商模型不变 |',
        '| 原生分析设置 | 时间30ms、自动最大步长、初始条件、容差、输出选择均保持 |',
        '| 实际固件/保护 | 未修改、未新增；本次不验证真实MCU或保护器件响应 |', '',
        '原生文件经两套DCL解码核对；精确逆变换证明除两处调用文字外其他XML字节相同。模型、元件参数/连接、分析设置另作比较。', '',
        f'- 原回传SHA256：`{build["baseline_sha256"]}`',
        f'- 修正版SHA256：`{build["output_sha256"]}`',
        '- [构建与接线核对](../simulation/multisim14/native-project-check/step01-sense-feedback-fix/results/data/build_checks.json)',
        '- [修正版完整30ms求解](../simulation/multisim14/native-project-check/step01-sense-feedback-fix/results/data/fixed_trap_200ns_verification.json)',
        '- [失配对照求解](../simulation/multisim14/native-project-check/step01-sense-feedback-fix/results/data/original_alias_mismatch_verification.json)', '',
        '同类Linux环境下运行build_fix.py，使用verify_coupled.py --trap-coarse复现200ns梯形法，再运行make_delivery.py。原对照数据已归档，默认verify_coupled.py可重跑7ms失配与50ns限时对照，--gear复现Gear失败。需要现有dclimplode/numpy/matplotlib和ngspice/XSPICE环境；最大执行时限可由STEP01_TIMEOUT_S覆盖。Windows用户直接打开原生工程，本环境未执行本机Multisim。', '']
    report.write_text('\n'.join(lines))
    package = PROJECT / 'downloads/Multisim14_STEP01_Sense_FeedbackFix_2026-10-25.zip'
    paths = [native, baseline, report]
    paths += [ROOT / name for name in ['build_fix.py', 'verify_coupled.py', 'make_delivery.py']]
    paths += [path for path in (ROOT / 'results').rglob('*') if path.is_file() and path.name != 'delivery_checks.json']
    paths += [ROOT.parent / name for name in ['ms14_project.py', 'stabilize_transient.py', 'verify_driver.py', 'verify_power_stage.py', 'requirements.txt']]
    paths += [ROOT.parent / 'control-loop/build_projects.py']
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('请先阅读.txt', '打开downloads/GBUCK_STEP01_IL_SENSE_FEEDBACK_FIX.ms14，重新运行30ms，先看原4条曲线，可另加V(VOUT)。\n只改V3内部调用的反馈节点名：数字3/2改成V_CAP/L_RAW；不改你的接线、Ki20、芯片、保险丝、原生分析设置或实物BOM。\nngspice交叉求解完整30ms通过；用户已回传本机30ms截图，VOUT和稳定性待进一步核对。F1热熔断未被交叉求解模拟。\n比较器/锁存尚未接入；新增INA仍只供观察，不是实际ADC/固件控制。\n报告包含基线、修改影响、数值证据和限制。\n')
        for path in sorted(set(paths)):
            archive.write(path, str(path.relative_to(PROJECT)))
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert archive.read(str(native.relative_to(PROJECT))) == native.read_bytes()
    checks = {'date': '2026-10-25', 'package': str(package.relative_to(PROJECT)), 'package_sha256': sha(package),
        'zip_integrity_verified': True, 'native_matches_completed_coupled_check': True,
        'returned_source_preserved': True, 'native_multisim_execution_performed_in_this_environment': False,
        'user_native_30ms_screenshot_received': True, 'user_native_voltage_regulation_verified': False}
    (ROOT / 'results/data/delivery_checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
