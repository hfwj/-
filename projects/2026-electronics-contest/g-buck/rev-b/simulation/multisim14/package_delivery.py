"""Check completed evidence and package the Multisim wiring/model deliverables."""
from pathlib import Path
import hashlib,json,csv,re,zipfile
import numpy as np
from build_circuits import ROOT,CASES,MODEL

def make_zip(path,base,skip_diagnostics=False):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix in ['.npz','.pyc','.dat','.zip'] or '__pycache__' in p.parts:continue
            if skip_diagnostics and 'superseded_numeric_failures' in p.parts:continue
            z.write(p,p.relative_to(base))
    with zipfile.ZipFile(path) as z:assert z.testzip() is None

def main():
    data=ROOT/'results/data';project=ROOT.parent.parent;reports=project/'reports';downloads=project/'downloads'
    rows=json.loads((data/'verification_summary.json').read_text());by={x['case']:x for x in rows}
    assert len(rows)==len(CASES)==9
    for name,cfg in CASES.items():
        p=ROOT/'circuits'/f'{name}.cir';s=p.read_text(encoding='ascii');x=by[name]
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=x['source_sha256']:
            eq=x.get('header_fix_equivalence',{})
            body_digest=hashlib.sha256(s.split('\n',1)[1].encode()).hexdigest()
            assert s.startswith('* ')
            assert eq.get('distributed_source_sha256')==digest
            assert eq.get('solver_source_sha256')==x['source_sha256']
            assert eq.get('body_before_sha256')==eq.get('body_after_sha256')==body_digest
        assert not re.search(r'^\s*\.(control|include)\b',s,re.M|re.I)
        assert x['data_rows']>1000 and x['end_time_s']>=cfg.get('stop',.08)*.999
        assert x['multisim14_execution_verified'] is False
        log=(ROOT/'results/logs'/f'{name}.log').read_text().lower()
        assert not any(w in log for w in ['aborted','error:','timestep too small'])
    for n in ['01_15V_open','02_15V_20ohm','03_25V_20ohm']:
        assert abs(by[n]['vout_mean_V']-10)<.5 and not by[n]['fault_latched_final']
    for n in ['04_25V_8ohm','05_25V_5ohm']:
        assert abs(by[n]['i_load_mean_A']-1)<.1 and not by[n]['fault_latched_final']
    off=np.load(data/'09_MCU_disable.npz')['last']
    assert np.max(np.abs(off[:,4:6]))<.1,'MCU disable must remove both VGS commands'
    assert by['09_MCU_disable']['vout_mean_V']<.5
    model=(ROOT/'models/G_BUCK_RevB_EQ.lib').read_text(encoding='ascii')
    assert model.startswith('.SUBCKT GBUCK_REVB_EQ ')
    assert model==MODEL[MODEL.index('.SUBCKT GBUCK_REVB_EQ '):]
    assert len({(ROOT/'models'/f'G_BUCK_RevB_EQ.{ext}').read_bytes() for ext in ['lib','cir','txt']})==1
    ports=model.split('.SUBCKT GBUCK_REVB_EQ ',1)[1].split('+ PARAMS:',1)[0].replace('\n+',' ').split()
    with (ROOT/'pin_mapping.csv').open(encoding='utf-8-sig') as f:pinrows=list(csv.DictReader(f))
    assert len(ports)==17 and ports==[r['port_name'] for r in pinrows]
    checks={'date':'2026-10-22','circuit_count':9,'model_port_count':17,
            'source_provenance_and_comment_only_equivalence_verified':True,'all_requested_transients_completed':True,
            'normal_cv_cc_functional_checks_passed':True,'mcu_disable_both_gates_off_checked':True,
            'multisim_14_native_import_or_execution_verified':False,
            'manufacturer_transistor_or_driver_model':False,
            'lib_cir_txt_model_copies_byte_identical':True,
            'model_begins_with_subckt_and_only_leading_comments_removed':True,
            'short_circuit_caused_overcurrent_latch_in_this_model':by['08_25V_short_test']['fault_latched_final'],
            'real_hardware_efficiency_verified':False}
    (data/'delivery_checks.json').write_text(json.dumps(checks,indent=2))
    table='| 文件 | 输出均值V | 外部电流均值A | 最终SAFE |\n|---|---|---|---|\n'
    for x in rows:table+=f"| {x['case']} | {x['vout_mean_V']:.4f} | {x['i_load_mean_A']:.4f} | {x['safe_final']:.3f} |\n"
    short=by['08_25V_short_test'];step=by['06_25V_load_steps'];p=by['04_25V_8ohm']
    header_fix=any(x.get('header_fix_equivalence') for x in rows)
    provenance=('本次修订只给9个文件首行标题加了星号注释；首行以后的电路与分析指令逐字节未改。复用原先9次完整求解的数据，保留实际求解源SHA256，并另记当前分发文件SHA256与首行后正文的一致性证明；没有冒充重新运行完整工况。修正版另外执行了导入上下文中的短时语法/启动回归，见import_header_checks.json。' if header_fix else '当前源文件SHA256与结果逐项匹配。')
    report=f'''# Multisim 14.0仿真电路交付与核验说明

日期：2026-10-22。电路来源为Rev B原理图及B3物料清单。本次提供仿真电路资料，不改变用户原始原理图或采购清单。

## 交付内容

- [4页仿真接线图PDF](../simulation/multisim14/diagrams/Multisim14_仿真电路接线图.pdf)：主功率、浮动高侧驱动与自举、采样控制保护、首个17引脚组件测试电路。
- [Multisim搭建步骤](../simulation/multisim14/README.md)：Component Wizard导入完整.lib、17端口映射、外部电源与脉冲设置及瞬态分析。
- 导入模型：[.cir副本](../simulation/multisim14/models/G_BUCK_RevB_EQ.cir)、[.txt全文复制副本](../simulation/multisim14/models/G_BUCK_RevB_EQ.txt)、[原.lib](../simulation/multisim14/models/G_BUCK_RevB_EQ.lib)。三个文件逐字节相同，用于处理不同文件筛选器；不表示进行了格式转换或已经验证Multisim导入。均为ASCII编码、PSpice风格E/G行为源与通用开关/二极管，没有ngspice专用运行控制段。
- [9个完整测试网表](../simulation/multisim14/circuits/)：各文件独立包含模型，没有外部include路径依赖。
- 元件表、引脚映射、CSV/JSON数值、原始求解日志、波形图和NPZ压缩轨迹。
- [专用ZIP](../downloads/Multisim14_仿真电路搭建包.zip)：不含较大的NPZ与已取代数值失败日志，其余搭建资料均包含。完整波形保存在仓库中。

## 第一次搭建

针对本机提示“数据模型要以.subckt或者.Model开头”，当前models目录三份模型文件已去掉声明前的5行注释，第一字节即为`.SUBCKT`；17端口、参数、全部元件与辅助子电路均未改。改扩展名本身不能解决这个报错。9个完整测试网表逐字节保持原状。模型正文一致性及短时启动核验见import_header_checks.json，不代表Multisim本机通过。

先按接线图第4页操作。从文件载入当前models目录中的.lib；也可在可编辑模型文本框中粘贴.txt全文。只有文件筛选器不显示.lib时才改选同内容.cir副本。导入顶层GBUCK_REVB_EQ，COM接全局地0；VIN_EXT接25V、VSET接10V设定源、ISET接1V设定源、VOUT接8Ω；ARM在5ms给10us的3.3V脉冲，MCU_EN在5.1ms后为3.3V。运行0～80ms瞬态，最大步长100ns，零初始电容电压和电感电流。预期进入恒流，输出约8V/1A。VSET/ISET是仿真设定端口，不是实物STM32引脚。

## 已执行的交叉核验

以下9项由ngspice 44.2的PSpice兼容模式执行，实际终止时间和非零数据行数已核对。{provenance}它们不是Multisim 14.0本机运行结果。

{table}

前3项满足10V±0.5V的标称模型要求，8Ω/5Ω约1A；负载阶跃与源阶跃都已执行到设定终止时间。MCU停机后最后100us两路VGS都低于0.1V，输出已放电至0.5V以下。正常工况未产生模型过流锁存。

负载阶跃的瞬时外部电流峰值约{step['i_load_peak_after_20ms_A']:.3f}A，不支持全过程≤1A的结论。短路工况的最终SAFE={short['safe_final']:.3f}V，电感平均电流约{short['il_mean_A']:.3f}A，{'产生' if short['fault_latched_final'] else '没有产生'}过流锁存。CC把电感电流限制在约1A时，±1.8A保护不会因为“输出电压接近零”就自动动作。此模型没有补入原资料缺失的软件短路锁存，不能承诺任意短路都会停机。

当前驱动及辅助功耗假设下25V/8Ω模型效率约{p['eta_equivalent_assumptions']*100:.2f}%；这不是实物效率。辅助模块效率、控制与显示电流均为假设，开关用44mΩ受控电阻和近似二极管表示，未覆盖真实MOS的非线性开关、米勒、磁芯、热及全部逻辑功耗，因此不能据此认定整机效率≥85%。

## 数值模型修正及证据边界

初版在载波与测试边沿重合处出现步长失败，后使用10ns有限载波复位平台并错开事件时刻；两管关闭的测试还需要加入每管250pF假设漏源寄生电容，保留SW节点的连续电压状态。上述修正后重新执行当前9个工况，没有将早退求解算成完成。旧失败/慢推进日志仅作诊断保存。

当前版本比原ngspice简化模型增加了浮动驱动阻抗、栅极与漏源寄生、自举充电、辅助功耗折算、实际参考网络压降及ADC反馈。它是另一套功能模型，不能直接沿用旧报告中短路触发锁存或功率级效率的结论。4.7nF栅源电容、250pF漏源电容、积分状态网络等都是仿真辅助，不是新增采购元件。

没有提供或伪造原生.ms14文件；当前云环境不能运行Windows版Multisim。Multisim安装中的模型导入、PSpice解析与GUI实际运行仍需在用户本机确认。如本机解析报错，应根据其完整错误调整兼容语法，不能把ngspice通过写成Multisim已通过。也没有验证真实STM32程序、LCD/按键、厂家芯片时序、ERC/DRC或实物效率。
'''
    (reports/'Multisim14_仿真电路交付与核验说明.md').write_text(report)
    make_zip(downloads/'Multisim14_仿真电路搭建包.zip',ROOT,skip_diagnostics=True)
    make_zip(downloads/'G题_RevB_仿真验证资料.zip',project)
    print(json.dumps(checks,indent=2))
    print(downloads/'Multisim14_仿真电路搭建包.zip')

if __name__=='__main__':main()
