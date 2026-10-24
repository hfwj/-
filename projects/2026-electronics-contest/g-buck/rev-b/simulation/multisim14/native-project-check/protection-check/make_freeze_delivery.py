"""Publish a separate restart comparison, without replacing the failing baseline."""
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
    build = read('freeze_build_checks.json')
    result = read('coupled_freeze_verification.json')
    baseline = read('coupled_native_verification.json')
    unit = read('verification_summary.json')
    native = PROJECT / build['output']
    original = PROJECT / build['baseline']
    assert sha(native) == build['output_sha256'] == result['native_project_sha256']
    assert sha(original) == build['baseline_sha256'] == baseline['native_project_sha256']
    assert result['full_requested_transient_completed']
    assert sha(ROOT / 'REVB_SENSE_PROTECT.lib') == unit['model_sha256']
    a = np.loadtxt(ROOT / 'results/data/coupled_freeze_extract_sampled.csv', delimiter=',', skiprows=1)
    hold = a[(a[:, 0] >= .0053) & (a[:, 0] <= .0079)]
    hold_ranges = {'current_integrator': float(np.ptp(hold[:, 9])),
                   'voltage_integrator': float(np.ptp(hold[:, 10]))}
    hold_ok = all(value < 1e-5 for value in hold_ranges.values())
    passed = bool(result['passed'] and hold_ok)
    outcome = '此20ms功能模型对照通过' if passed else '对照仍有未通过项，不能认定修复'
    window = result['reARM_window']
    old = baseline['reARM_window']
    report = PROJECT / 'reports/Multisim14_保护重启积分冻结对照_2026-10-24.md'
    lines = [
        '# 保护重启：停机积分冻结对照', '',
        f'2026-10-24。**{outcome}。**原12ms失败基线保留；本轮仅改变停机期间两路积分器状态管理。未运行Windows Multisim，未修改或验证真实固件。', '',
        '## 本机操作', '',
        '打开[20ms对照工程](../downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14)，直接运行瞬态分析。原画布保留，保护仍在V_EN模板内；V3模板内有理想控制器，均不是逐芯片GUI重绘。', '',
        '预选V(17)=DRV_EN、V(g_l)=下管VGS、V(vout)。需要时添加V(g_h)-V(sw)看高管VGS。不要用栅极对地电压代替高管VGS。', '',
        '| 时刻 | 应观察的过程 |', '|---|---|',
        '| 3ms | 第一次ARM使能 |',
        '| 5～6ms | 向IL采样正输入叠加55mV，模拟+2.2A表观故障；两路栅极应关断 |',
        '| 6～8ms | 故障解除仍锁存停机，原ARM保持高不应恢复 |',
        '| 8ms | 新ARM上升沿后检查是否恢复、是否再次触发 |',
        '| 8～20ms | 观察是否持续使能；本轮仅验证这一窗口 |', '',
        '这是启动阶段的采样偏移注入，不是10V稳态故障、真实短路或故障能量测试。辅助电源与偏移源的PWL在12ms后的最后值保持不变。', '',
        '## 已运行结果', '',
        f'ngspice完成到{result["actual_end_s"] * 1000:.3f}ms，共{result["data_rows"]}点。20ms末VOUT约{a[-1, 4]:.3f}V，仍在恢复上升；本轮不判定已经恢复到10V稳态。', '',
        '| 检查 | 结果 |', '|---|---|',
    ]
    lines.extend(f'| {key} | {"通过" if value else "未通过"} |' for key, value in result['checks'].items())
    lines += [f'| 停机状态保持（降采样轨迹5.3～7.9ms，变化小于1e-5） | {"通过" if hold_ok else "未通过"} |', '',
        '| 全精度重新ARM窗口8～8.5ms | 原12ms基线 | 冻结对照 |', '|---|---:|---:|',
        f'| ARM前电流积分状态 | {old["current_integrator_before_ARM"]:.8f} | {window["current_integrator_before_ARM"]:.8f} |',
        f'| ARM前电压积分状态 | {old["voltage_integrator_before_ARM"]:.8f} | {window["voltage_integrator_before_ARM"]:.8f} |',
        f'| 电感电流最大值/A | {old["IL_max_A"]:.8f} | {window["IL_max_A"]:.8f} |', '',
        '电感窗口最大值取完整求解轨迹；状态保持检查来自降采样CSV。CSV不适合证明全部高频峰值。功能保护门限仍约±1.8A/11V，没有提高门限或旁路保护。', '',
        '90s时限尝试推进到约10.83ms，240s时限推进到约19.30ms；均未导出完整数据，按执行超时保留，不认作收敛失败。随后依据进度提高执行时限，模型和求解设置不变。', '',
        '![对照轨迹](../simulation/multisim14/native-project-check/protection-check/results/figures/coupled_freeze_gate_off.png)', '',
        '## 修改影响', '',
        '比较基线：GBUCK_REVB_PROT_POS_INJECT_12ms.ms14；其上游为Ki20的25V/20Ω工程。', '',
        '| 类别 | 改动及影响 |', '|---|---|',
        '| 实物原理图 | 连线、引脚及器件值无修改 |',
        '| 器件/BOM/PCB | 无新增、更换或改板要求 |',
        '| 仿真V3控制模板 | 增加DRV_EN反馈端口；DRV_EN低于1.65V时，两路积分驱动电流置零，保留状态；仍有原1GΩ泄漏 |',
        '| 使能期间控制 | 原Ki20电压/电流环方程与系数不变；未增加复位、重启斜坡或PWM禁止逻辑 |',
        '| 保护、功率级、驱动模型 | 与12ms基线相同；F1仍仅按导通电阻交叉求解，无熔断热模型 |',
        '| 分析设置 | 12→20ms，活动图名改变；其余原生求解选项保持 |',
        '| 真实固件 | 尚未提供，未修改；若采用此策略，固件需显式实现停机状态管理，仿真改动不会自动进入MCU |', '',
        '原19项独立保护功能检查的模型哈希保持，未更改这些测试的被测保护库。本对照只覆盖既定注入及20ms恢复，不能据此确认全部故障/负载的重启、1A输出瞬态限制、芯片最坏时序、效率或硬件。', '',
        '## 文件与复现', '',
        '依赖沿用native-project-check/requirements.txt及原ngspice环境。运行build_freeze_comparison.py，然后verify_coupled.py --freeze，最后make_freeze_delivery.py。默认本对照执行时限300s，可用REVB_COUPLED_TIMEOUT_S覆盖。', '',
        f'- 基线SHA256：`{sha(original)}`',
        f'- 对照SHA256：`{sha(native)}`',
        '- [构建检查](../simulation/multisim14/native-project-check/protection-check/results/data/freeze_build_checks.json)',
        '- [完整窗口判定](../simulation/multisim14/native-project-check/protection-check/results/data/coupled_freeze_verification.json)',
        '- [保留原失败基线报告](Multisim14_RevB采样与保护首轮验证_2026-10-24.md)', '',
    ]
    report.write_text('\n'.join(lines))
    readme = ROOT / 'README.md'
    section = '\n'.join([
        '<!-- restart-freeze-comparison -->',
        '## 后续：独立停机积分冻结对照', '',
        f'**{outcome}。**见[新报告](../../../../reports/Multisim14_保护重启积分冻结对照_2026-10-24.md)、[20ms工程](../../../../downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14)和[独立ZIP](../../../../downloads/Multisim14_保护重启积分冻结对照_2026-10-24.zip)。', '',
        '比较原12ms失败基线：仅V3理想控制器加入DRV_EN反馈、停机时冻结两积分器，时间延长到20ms；原图连接/引脚/器件值及BOM/PCB不改。保护门限、功率/驱动模型和使能期间Ki20方程不改；未修改真实固件，未运行Windows Multisim。', '',
        '本机先运行新工程，看3ms使能、5ms关断、故障解除后不自动重启及8ms新ARM后的使能保持。下文首轮失败结果仍归属原12ms基线。',
        '<!-- /restart-freeze-comparison -->', '',
    ])
    body = readme.read_text()
    if '<!-- restart-freeze-comparison -->' in body:
        start = body.index('<!-- restart-freeze-comparison -->')
        end = body.index('<!-- /restart-freeze-comparison -->', start) + len('<!-- /restart-freeze-comparison -->')
        body = body[:start] + section.rstrip() + body[end:]
    else:
        first, rest = body.split('\n', 1)
        body = first + '\n\n' + section + '\n' + rest.lstrip('\n')
    readme.write_text(body)
    project_readme = PROJECT / 'README.md'
    index = project_readme.read_text()
    entry = '- [保护重启积分冻结对照](reports/Multisim14_保护重启积分冻结对照_2026-10-24.md) · [20ms原生工程](downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14)：' + outcome + '；保留原失败基线，未改实物原图/BOM或真实固件，本机待验证。'
    index = '\n'.join(line for line in index.split('\n') if not line.startswith('- [保护重启积分冻结对照]'))
    index = index.replace('## 下载与阅读\n', '## 下载与阅读\n\n' + entry + '\n', 1)
    project_readme.write_text(index)
    checks = {'date': '2026-10-24', 'native_sha256': sha(native), 'baseline_preserved': True,
              'model_matches_original_19_checks': True, 'full_window_checks_passed': result['passed'],
              'sampled_hold_ranges': hold_ranges, 'sampled_hold_passed': hold_ok,
              'restart_comparison_passed': passed, 'native_multisim_execution_performed': False}
    check_path = ROOT / 'results/data/freeze_delivery_checks.json'
    check_path.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
    paths = [native, original, report, PROJECT / 'reports/Multisim14_RevB采样与保护首轮验证_2026-10-24.md']
    paths += [ROOT / name for name in ['README.md', 'REVB_SENSE_PROTECT.lib', 'build_native.py',
              'build_reset_comparison.py', 'build_freeze_comparison.py', 'verify_coupled.py', 'make_freeze_delivery.py']]
    paths += [ROOT.parent / name for name in ['ms14_project.py', 'stabilize_transient.py',
              'verify_power_stage.py', 'verify_driver.py', 'requirements.txt']]
    paths += [ROOT.parent / 'control-loop' / 'build_projects.py']
    paths += [ROOT / 'results/data' / name for name in ['freeze_build_checks.json', 'verification_summary.json',
              'coupled_freeze_verification.json', 'coupled_native_verification.json',
              'coupled_freeze_extract_sampled.csv', 'freeze_delivery_checks.json']]
    paths += [ROOT / 'results/figures/coupled_freeze_gate_off.png', ROOT / 'results/logs/coupled_freeze_extract.log',
              ROOT / 'results/data/attempts/freeze_90s_timeout.json', ROOT / 'results/logs/freeze_90s_timeout.log',
              ROOT / 'results/data/attempts/freeze_240s_timeout.json', ROOT / 'results/logs/freeze_240s_timeout.log']
    package = PROJECT / 'downloads/Multisim14_保护重启积分冻结对照_2026-10-24.zip'
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('请先阅读.txt', f'{outcome}。\n先打开downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14。\n本轮为20ms保护重启功能模型对照，未运行Windows Multisim，未改实物原图/BOM或真实固件。\n详细操作与影响见reports。原12ms失败基线同包保留。\n')
        for path in sorted(set(paths)):
            archive.write(path, str(path.relative_to(PROJECT)))
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
    package_checks = {'package': str(package.relative_to(PROJECT)), 'package_sha256': sha(package),
                      'zip_integrity_verified': True, **checks}
    (ROOT / 'results/data/freeze_package_checks.json').write_text(json.dumps(package_checks, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(package_checks, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
