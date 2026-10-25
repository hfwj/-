"""Use the actual failed ITL300 settings, varying only integration method.

The generated native file is a pending diagnostic, not a verified repair.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block, elements, clean


def main():
    source = PROJECT / 'downloads/GBUCK_STEP02_5R_ITL300_25ms_DIAG.ms14'
    logpath = ROOT / 'results/logs/native_ITL300_25ms_failure.log'
    log = logpath.read_text()
    assert 'set itl4 = 300' in log and 'set reltol = 0.003' in log
    assert 'TSTOP）：0.025' in log and '最大时间步长5e-008' in log
    assert 'time = 0.0227726, timestep = 6.25e-018:trouble with (md:xq2) d1:xq2' in log
    raw = source.read_bytes()
    xml, _ = unpack(raw)
    original = parse(xml)
    opts = analysis_options(xml)
    assert opts['itl4'] == {'enabled': True, 'value': '300'}
    assert opts['method'] == {'enabled': False, 'value': 'trapezoidal'}
    assert inspect(original)['transient_settings']['TSTOP'] == '0.025'
    by = {p['display_ref']: p for p in components(original)}
    assert by['Q2']['ports'] == {'D': '15', 'G': '13', 'S': '0'}
    mos = clean(elements(original, 'CiModel')[by['Q2']['model_id']].find('.//CiaCString').get('String'))
    assert re.search(r'^D1\s+3 1 MD\s*$', mos, re.M)
    text = xml.decode('ascii')
    tran = block(text, 'TRAN')
    opttext = block(tran, 'ASYS_OPT')
    pattern = r'(\d+:list\{IsEnabled:long\{)0(\}\s+method:string\{)trapezoidal(\}\s*\})'
    changed, count = re.subn(pattern, lambda m: m[1] + '1' + m[2] + 'gear' + m[3], opttext)
    assert count == 1
    new_tran = tran.replace(opttext, changed, 1)
    revised = text.replace(tran, new_tran, 1)
    assert revised.replace(new_tran, tran, 1).encode('ascii') == xml
    newroot = parse(revised.encode('ascii'))
    assert components(newroot) == components(original)
    assert model_sources(newroot) == model_sources(original)
    assert inspect(newroot) == inspect(original)
    expected = dict(opts, method={'enabled': True, 'value': 'gear'})
    assert analysis_options(revised.encode('ascii')) == expected
    data = pack(revised.encode('ascii'))
    verify_independent_decoder(data, revised.encode('ascii'))
    dest = PROJECT / 'downloads/GBUCK_STEP02_5R_GEAR_ITL300_25ms_DIAG.ms14'
    dest.write_bytes(data)
    result = {
        'date': '2026-10-25', 'source_project': str(source.relative_to(PROJECT)),
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'latest_native_log_sha256': hashlib.sha256(logpath.read_bytes()).hexdigest(),
        'ITL300_native_completed_25ms': False, 'ITL300_native_end_s': .0227726,
        'native_reported_branch': '(md:xq2) d1:xq2',
        'branch_mapping': 'D1 internal to low-side Q2 model; source-to-drain body diode, A=GND, K=SW',
        'F1_in_ITL300_native_run': 'user explicitly confirmed not blown',
        'output': str(dest.relative_to(PROJECT)), 'output_sha256': hashlib.sha256(data).hexdigest(),
        'only_active_analysis_method_changed': True,
        'method_before': opts['method'], 'method_after': expected['method'],
        'unchanged_options': {k: v for k, v in opts.items() if k != 'method'},
        'settings': inspect(original)['transient_settings'],
        'all_parts_models_controller_and_connections_preserved': True,
        'exact_inverse_XML_verified': True, 'two_independent_DCL_decoders_verified': True,
        'gear_native_open_or_run_performed': False, 'gear_convergence_verified': False,
        'cross_solver_run_performed': False,
        'root_cause': 'unresolved; increasing iteration budget alone did not complete the requested run'}
    (ROOT / 'results/data/gear_build_and_native_feedback.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    report = f'''# STEP02 5Ω：ITL300仍失败，Gear积分法独立对照

2026-10-25。比较基线为已交付的ITL300/25ms诊断版，不覆盖原故障或此前20Ω/8Ω成功工况。

## 新的本机证据

用户回传报错日志2.log并明确确认F1未熔断。日志确认TSTOP=25ms、TMAX=50ns、ITL4=300，RELTOL=0.003、ABSTOL=1e-8、VNTOL=1e-4、CHGTOL=1e-13均保持。实际中止：

```text
Timestep too small; time = 0.0227726, timestep = 6.25e-018:
trouble with (md:xq2) d1:xq2
```

日志原字节保存在results/logs/native_ITL300_25ms_failure.log，SHA256 `{result['latest_native_log_sha256']}`。本次没有重传运行后的原生工程；日志设置与先前交付的诊断文件匹配，不宣称已重新核验本机文件哈希。

相较ITL4=100时的21.4605ms/U2内部V_V8支路，ITL300越过原点后在22.7726ms报低侧Q2内部D1二极管错误。当前模型D1从3脚Source至1脚Drain；Q2的S接地、D接SW，因此该支路是GND到SW的体二极管。不能把内部D1与原理图输入端的肖特基D1混淆，也不能凭报错位置认定Q2实际损坏或该模型元件是唯一根因。

结论：增加迭代预算改变了失效时刻/定位，但未完成25ms，迭代上限单项调整没有解决问题。保持失败记录，不把图中约5V/1A的短时响应记为100ms通过。最新F1未熔断，不能归因于输入保险丝再次断开。

## 下一候选：只改变积分方法

候选文件：GBUCK_STEP02_5R_GEAR_ITL300_25ms_DIAG.ms14。

- 当前基线：未启用自定义覆盖的trapezoidal积分选项。
- 候选：启用该分析的method=gear。
- 保留ITL4=300、25ms/50ns、所有误差容限和其他选项；全部器件、连线和厂商模型/控制方程逐字保持。

这是用于检查积分方法敏感性的独立对照。Gear常用于含开关及刚性动态的数值求解，同时会引入不同数值阻尼；即使完成，也需再核对电压/电流响应及必要的精度对照，不能把阻尼后的平滑波形直接当成原设计动态被认证。历史STEP01不同基线的Gear交叉求解也曾失败，本候选不是通用或已证实的修复。

本环境未运行Windows Multisim，未验证能否跨过22.7726ms或完成25ms；不以不同引擎的启动检查替代本机故障点验证。

## 本机下一步

1. 在独立窗口打开Gear/25ms候选，核对积分方法Gear、ITL4=300、TSTOP=0.025s、TMAX=50ns，保留其他设置。
2. 执行瞬态分析，观察原有四条曲线。先不运行100ms版。
3. 回传数据末时间及F1状态；若仍失败，保存本次完整日志。即使文件名/旧标签含100ms或20R，也以实际参数与数据为准。
4. 保护比较器和锁存的独立搭建可以继续，不把它接入本轮数值对照而引入新变量。

## 验证及修改影响

文件输出SHA256 `{result['output_sha256']}`。已完成：只改活动瞬态method选项的精确逆变换、全部元件/连接/参数/模型/控制文本保持、两个独立DCL解码器校验。结构验证不等于本机打开或求解通过。

比较基线为ITL300/25ms版：原理图拓扑、引脚和器件值不变，RL仍5Ω、F1仍2A；无需更换实物器件/BOM/PCB；不改MOS体二极管模型或TI模型，不加寄生元件，不改PI/电流指令/保护门限/固件。仅改变求解积分方法，效果待本机验证。相对最初5Ω回传文件，ITL4与25ms窗口仍是此前诊断变动，不能称仅method相对原件变化。

复现：在本目录运行build_gear.py，使用已有dclimplode/lxml和脚本依赖；无需执行旧build_diagnostics.py，不改写历史结果。交付ZIP为当时快照，后续反馈另行补充。
'''
    report_path = PROJECT / 'reports/Multisim14_STEP02_5R_ITL300失败与Gear诊断_2026-10-25.md'
    report_path.write_text(report)
    archive = PROJECT / 'downloads/Multisim14_STEP02_5R_Gear_Diagnostic_2026-10-25.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(dest, dest.name)
        z.write(report_path, report_path.name)
        for p in [logpath, ROOT / 'results/data/gear_build_and_native_feedback.json']:
            z.write(p, str(p.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and z.read(dest.name) == data
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
