"""Build a report and lightweight package from actual completed/limited checks."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]


def main():
    checks = json.loads((ROOT / 'results/data/build_checks.json').read_text())
    runs = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'results/data').glob('*.json')
            if p.name != 'build_checks.json'}
    feedback = {
        'date': '2026-10-25', 'evidence': 'User chat screenshot and explicit F1 blown report; no numeric waveform export received',
        'screenshot_coverage_s': [0, .03], 'VOUT_peak_V_approx': 19,
        'VOUT_end_V_approx': 6, 'VDDA_V_approx': 3.2,
        'IOUT_RAW_and_RS_OUT_current_curves': 'Visually nearly overlap on shared numeric axis; not a precision transfer measurement',
        'F1_blown': True, 'source_sha256': checks['source_sha256'],
        'native_fixed_project_results_received': False}
    (ROOT / 'results/data/native_failure_feedback.json').write_text(json.dumps(feedback, ensure_ascii=False, indent=2) + '\n')
    rows = []
    for name, run in runs.items():
        if name == 'native_failure_feedback':
            continue
        metrics = run.get('metrics', {})
        rows.append(f"| {name} | {run['completed']} | {run['actual_end_s']} | {metrics.get('VOUT_end_V')} | {metrics.get('IL_max_A')} | {metrics.get('controller_IL_max_A')} |")
    table = '\n'.join(rows)
    original = runs.get('original_200ns', {})
    fixed = runs.get('fixed_200ns', {})
    diagnosis = ''
    if original and fixed:
        a, b = original['metrics'], fixed['metrics']
        diagnosis = (f"原失配对照完整完成7ms：电感峰值{a['IL_max_A']:.6f}A，而控制器电流读数峰值为{a['controller_IL_max_A']:.6f}A，复现反馈失配。"
                     f"修正版在240秒执行时限内推进至{fixed['actual_end_s'] * 1000:.6f}ms，"
                     f"电感峰值{b['IL_max_A']:.6f}A、控制器读数峰值{b['controller_IL_max_A']:.6f}A，支持已覆盖区间的反馈恢复。"
                     "本轮修正版30ms未完成，尚不能验收稳压、后段稳定性或本机F1状态；原生文件仍保留30ms供本机复测。")
    report = f'''# U3接入后F1熔断：V3反馈节点修正

日期：2026-10-25。基线为本次上传的 `GBUCK_STEP01_IL_SENSE.ms14.ms14`，原件保存在 `references/user-projects/2026-10-25_STEP02_U3_F1熔断_原回传.ms14`，不覆盖。

## 结论与本机证据

U3及100nF去耦的实际网表连接正确。V3仍使用旧数字节点，未继承此前STEP01反馈别名修正：

```text
原：{checks['before']}
新：{checks['after']}
```

当前2/3节点的导出名称分别为L_RAW/V_CAP，V3模板内文字引用不会自动随绘图网络别名更新；输入母线7仍无别名。修正版仅替换V3活动模板与元件元数据中的两处调用，控制方程、Ki20、1A指令、软启动和PWM方程保持。V3属性中的4us/10us普通脉冲参数仍保留，但不能据此认定自定义控制模板已变成固定占空比信号源。

用户原故障截图覆盖0～30ms：VOUT峰值约19V，30ms末约6V，VDDA约3.2V；IOUT_RAW与RS_OUT电流曲线视觉上基本重合，用户明确报告F1熔断。数值为截图估读，非导出数据。F1切断输入支持解释后段下降，但未取得动作时间/电流，不能把该截图本身当成熔断机理或唯一原因的精确验证。新修正版尚待本机复测。

U3已完成的独立有序上电测试另见 `simulation/multisim14/ina181-power-on-check/README.md`：89.9806us处输出497.2455mV。此结果不自动构成当前Buck接入通过。

## 文件与静态验证

- 原回传SHA256：`{checks['source_sha256']}`。
- 修正版SHA256：`{checks['output_sha256']}`。
- U3实际端口：1 IOUT_RAW、2 GND、3 V_CAP、4 VOUT、5 GND、6 VDDA；C_U3=100nF跨VDDA/GND；RS_OUT=0.05Ω。
- 精确逆变换验证：将两处新调用还原后，整个解压XML与原件逐字节一致。
- 两套独立DCL解码器核对新文件；全部元件、位置、端口、器件值、厂商模型内容、分析参数和所选输出保持。
- 原生文件仍是30ms、TMAX=50ns、自动初始条件、RELTOL=0.003，其他选项见build_checks.json。
- F1原交互模板包含BEGIN_ANALYSIS/BEGIN_PLOT调用RESET；本次没有删除动作、提高额定值或替换为电阻。

## 独立交叉求解结果

本轮提取用户实际接线及全部嵌入模型（含U3），ngspice44.2/PSpice兼容、梯形法、200ns最大步长。原失配对照请求7ms；修正版请求30ms，各有240秒默认执行上限。表中的False必须读作未完成请求时长，不是测试通过。

| 工况 | 完成请求时长 | 实际末时间/s | 末点VOUT/V | 电感峰值/A | 控制器电流读数峰值/A |
|---|---|---|---|---|---|
{table}

{diagnosis}

完整状态、日志、末时间及错误分别保存在本目录results。200ns是交叉求解设置，未写入原生修正版；未进行本轮50ns/200ns精度收敛验收。若达到执行时限，只能确认实际已覆盖的区间，不能把超时当作已完成30ms或必然的数值收敛失败。

**交叉求解只以固定1mΩ表示F1导通状态，不模拟其交互熔断逻辑或热/I²t行为；因此不能据此证明本机修正后F1一定不熔断。** 这个诊断等效没有写入交付的.ms14。仿真引擎与部分选项不同，不能声称跨引擎逐点一致或达到实物精度。

## 本机下一步

1. 下载并打开 `GBUCK_STEP02_U3_FEEDBACK_FIX.ms14`，保留原故障工程。
2. 完全停止旧仿真，使用新文件重新启动瞬态分析；不继续显示旧结果。
3. 保留30ms/50ns及其余现有选项，先观察现有四条曲线：V(IOUT_RAW)、I(RS_OUT)、V(VDDA)、V(VOUT)。
4. 回传完整新波形和运行后F1状态。若报错，提供完整错误；若仍熔断，下一步增加输入分流器电流、电感电流和母线电压观察，记录动作时刻，不预先提高F1额定值。

## 修改影响

比较基线：此次U3已接入的原回传文件。

- 原理图：所有连线、引脚、元件值和布局均保持，不再次重接U3。
- 实物器件/BOM/PCB：无新增、更换、额定值/封装或改板要求；F1仍2A。
- 仿真模型：仅V3端口引用3→V_CAP、2→L_RAW，保留控制方程与TI/驱动/功率模型。独立诊断中F1固定导通等效和200ns步长单独标记，不混入原生交付。
- 控制/固件/保护：未改PI系数、指令或实际固件，未新增比较器/锁存保护；不构成真实控制器或整机保护验证。

## 复现

本环境使用dclimplode、lxml、numpy、matplotlib与已有ngspice44.2/XSPICE库。先运行build_step02.py，再运行verify_step02.py，最后运行make_delivery.py。可用STEP02_TIMEOUT_S设置独立求解执行上限；额外50ns对照须显式调用verify_step02.py --50ns，其结果不能在未执行时声称存在。本环境没有运行Windows Multisim。
'''
    target = PROJECT / 'reports/Multisim14_U3接入_F1熔断_反馈节点修正_2026-10-25.md'
    target.write_text(report)
    (ROOT / 'README.md').write_text('# STEP02 U3接入反馈修正\n\n[完整报告](../../../../reports/' + target.name + ') · [原生修正版](../../../../downloads/GBUCK_STEP02_U3_FEEDBACK_FIX.ms14)\n\n仅修正V3两处反馈节点引用，保留本次U3接线、所有器件及30ms/50ns设置。原故障F1熔断已记录；修正版本机运行尚待反馈。独立诊断的结果与局限见报告及results。\n')
    archive = PROJECT / 'downloads/Multisim14_STEP02_U3_FeedbackFix_2026-10-25.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(PROJECT / 'downloads/GBUCK_STEP02_U3_FEEDBACK_FIX.ms14', 'GBUCK_STEP02_U3_FEEDBACK_FIX.ms14')
        z.write(target, target.name)
        for path in (ROOT / 'results').rglob('*'):
            if path.is_file():
                z.write(path, str(path.relative_to(ROOT)))
    print(archive)


if __name__ == '__main__':
    main()
