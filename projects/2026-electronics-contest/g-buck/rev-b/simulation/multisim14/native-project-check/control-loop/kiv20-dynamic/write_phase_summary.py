"""Summarize separately sourced native screenshots; retain approximate/exact distinctions."""
from pathlib import Path
import json,csv,hashlib,zipfile
HERE=Path(__file__).resolve().parent
R=HERE.parent
PROJECT=R.parents[3]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source_c=R/'open-load-diagnostic/results/C_native_feedback.json';static=R/'kiv20-regression/results/native_user_feedback.json';dynamic=HERE/'results/data/native_user_feedback.json'
    c=json.loads(source_c.read_text());s=json.loads(static.read_text());d=json.loads(dynamic.read_text());assert len(s['cases'])==5 and not s['pending_cases']
    static_rows=[c,*s['cases']];assert d['traces_visibly_reach_180ms'] and d['model_voltage_Ki']==20
    csv_path=HERE/'results/data/Ki20_screenshot_observations.csv'
    fields=['case','mode','window_start_s','window_end_s','approx_VOUT_V','approx_IOUT_A','approx_startup_VOUT_peak_V','numeric_native_export_received','note']
    with csv_path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for row in static_rows:
            writer.writerow({'case':row['id'],'mode':'CC' if row['id'].startswith('CC') else 'CV','window_start_s':.06,'window_end_s':.1,'approx_VOUT_V':row['approximate_VOUT_end_V'],'approx_IOUT_A':row.get('approximate_IOUT_end_A',''),'approx_startup_VOUT_peak_V':row['approximate_VOUT_peak_V'],'numeric_native_export_received':False,'note':'Screenshot estimates; not measured window statistics. Open-load output current not resolved.'})
        for stage,win in zip(d['approximate_observed_stages'],[[.06,.075],[.11,.125],[.16,.175]]):
            writer.writerow({'case':'AUTO_KIV20_'+str(stage['load_ohm'])+'R','mode':'CV' if stage['load_ohm']==20 else 'CC','window_start_s':win[0],'window_end_s':win[1],'approx_VOUT_V':stage['VOUT_V'],'approx_IOUT_A':stage['IOUT_A'],'numeric_native_export_received':False,'note':'Screenshot estimates, not numerical mean/range. Transient peaks separate:~1.2-1.3A near80ms,~1.6A near130ms.'})
    report=PROJECT/'reports/Ki20_七工况本机功能验证阶段汇总_2026-10-24.md'
    text='''# Ki20七工况本机功能验证阶段汇总

日期：2026-10-24。证据为用户Windows Multisim截图；不是本环境执行Multisim，不是精确波形统计。运行版本依据活动标签及交付上下文识别，未收到本轮各工程保存文件以独立校验实际设置。

**阶段结论：当前功率级在理想Ki20等效控制下，六个静态工况及自动CV/CC切换功能已有本机截图支持。不能据此认定原完整原理图、真实固件、保护和效率全部符合G题；动态约1.6A峰值仍在。**

| 同一Ki20条件 | 截图后段估读 | 当前证据范围 |
|---|---|---|
| 15V外部空载，100ms | 约10V，启动峰值约10.4V，起伏衰减 | 空载改善可见，精确误差/纹波未量化 |
| 25V/20Ω，100ms | 约10V/0.5A | 静态恒压功能 |
| 25V/8Ω，100ms | 约8V/1A | 静态恒流功能 |
| 25V/5Ω，100ms | 约5V/1A，电压小幅起伏 | 静态恒流功能 |
| 15V/20Ω，100ms | 约10V/0.5A | 低输入端恒压功能 |
| 25V外部空载，100ms | 约10V，启动峰值约10.5V，起伏衰减 | 不能据图断言峰值严格≤10.5V；电流未精确读出 |
| 25V、20Ω→8Ω→5Ω，180ms | 约10V/0.5A→8V/1A→5V/1A | 自动模式切换可见；80ms峰值约1.2～1.3A，130ms约1.6A |

外部空载采用RL=1GΩ，2.2kΩ泄放仍保留，10V时预计约4.5mA；曲线贴近零不等于实测电流严格为零。电流图采用I(RS_OUT)时包含泄放支路；最初C空载排查图中的I(L1)并非输出负载电流。

## 切换峰值与题意

Ki20动态80/130ms两次切换均有电流冲高，后一次约1.6A。输出电容约8V时接入5Ω负载，8V/5Ω≈1.6A与图形相符；这支持电容放电的解释线索，不是对所有寄生和损耗的定量验证。限制电感平均电流指令为1A不能自动阻止电容先向负载供电。

当前图不能表述为全过程瞬时不超过1A。题目要求的稳态电流容差与“最大不超过1A”必须按规定测量分别记录；本报告没有自行放宽瞬时上限。如果要求严格的输出瞬时硬上限，当前现象未满足，后续需单独评估控制/储能/输出限流方案，再报告其硬件影响；本次未新增该改动。

## 当前模型与原图的关系

- 物理功率级和驱动沿用用户工程；F1=2A已在这些Ki20副本接入，临时R1断开。截图未显示F1状态/额定熔断特性，不能宣称保护验收通过；直流工作点初始化也不能代替真实输入上电浪涌。
- V3仍使用理想软启动、理想采样、PI和PWM模板，电压外环Ki由早期100改为20是本轮改善的主要单参数对照，未修改实际STM32程序。先前IR2104兼容模型修改、负电感电流指令至−0.15A等假设保留。
- 原INA/ADC链、锁存保护、显示/按键未在这些模型中按真实实现验证。独立理想12V辅助电源及控制模型也不能用于题目含辅助功耗的整机≥85%效率验收。
- 早期Ki100交叉求解和截图单独保留，不挪作Ki20同参数回归结果。负载台架检查仅确认动态电导模型，不代表完整Buck动态仿真由本环境运行通过。

## 下一步：固定参数，量化结果

1. 在现有动态工程导出VOUT和I(RS_OUT)数值波形（CSV/文本按本机支持），或用游标读出切换峰值与持续时间。保留原模型，不继续叠加调参。
2. 统计60～75ms、110～125ms、160～175ms三个窗口的电压/电流均值、最小/最大值，以及80/130ms附近的电流峰值和超过1A的持续时间。截图估读不能代替这些统计；独立静态工况端点数据也需保留以核查源/负载调整率。
3. 再分别处理真实控制/采样/保护、显示设置和整机效率。仅有PDF、BOM和当前仿真副本时，尚不能验证未提供的固件或代替实物测量。

## 本次修改影响与交付

比较基线为已交付Ki20静态/动态工程。本次只新增截图记录、估读表、阶段报告和资料归档；原理图连接/引脚/元件值、板上器件/BOM/PCB、所有原生工程的控制/刺激/求解参数均**不变**。没有新控制或硬件修改。

[静态反馈](../simulation/multisim14/native-project-check/control-loop/kiv20-regression/results/native_user_feedback.json) · [动态反馈](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/native_user_feedback.json) · [估读CSV](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/Ki20_screenshot_observations.csv) · [七工程及报告ZIP](../downloads/Multisim14_Ki20七工况阶段汇总_2026-10-24.zip)。工况表为截图估读，另附光标显示读数；未收到完整原生数值波形。
'''
    cursor_file=HERE/'results/data/cursor_readings_130ms.json'
    if cursor_file.exists():
        cursor=json.loads(cursor_file.read_text());p1,p2=cursor['points']
        text+=f'\n## 新增光标点读数（不同于整段波形统计）\n\n切换前：{p1["time_s"]*1000:.4f}ms、VOUT={p1["VOUT_V"]:.4f}V、I(RS_OUT)={p1["IOUT_A"]:.7f}A；峰顶附近：{p2["time_s"]*1000:.4f}ms、VOUT={p2["VOUT_V"]:.4f}V、I(RS_OUT)={p2["IOUT_A"]:.4f}A，较1A高56.9%。光标显示Δt=892.2347us，是前点到峰顶附近点的间隔，不是过流持续时间；也未搜索全局峰值。\n\n按已交付连接，7.8272/5+7.8272/2200≈1.5690A，与显示电流一致。完整数据仍未导出。下一步测上升越过1A至下降首次回到1A的同一连续区间；如有纹波多次穿越，应由完整波形分别统计。\n\n[光标读数JSON](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/cursor_readings_130ms.json) · [两点CSV](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/cursor_points_130ms.csv)。本次仍仅归档，不修改工程、器件或控制。\n'
    recovery_file=HERE/'results/data/cursor_recovery_attempt_137ms.json'
    if recovery_file.exists():
        recovery=json.loads(recovery_file.read_text())
        text+='\n## 第二组回落光标读数\n\n左光标129.9919ms、0.9989547A/7.9627V；右光标137.2823ms、1.0283A/5.1296V。右点在130ms负载变化后7.2823ms，仍高于1A约2.83%，但已在1±0.1A内。显示Δt7.2904ms仍不是确认的连续过流时长，不能由两个点排除中间已发生阈值穿越。\n\n下一步向右移动右光标到该尖峰下降首次≤1.0000A处，记录时间；从130ms到此点仅作为近似恢复时间。精确超限时长需完整波形或真正的上下穿越点。本次仅记录，原理图/器件/模型/求解设置保持。\n\n[第二组光标JSON](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/cursor_recovery_attempt_137ms.json) · [两点CSV](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/cursor_recovery_points_137ms.csv)。\n'
    returned_file=HERE/'results/data/cursor_observed_return_142ms.json'
    if returned_file.exists():
        returned=json.loads(returned_file.read_text())
        text+='\n## 第三组光标：观测回落点已取得\n\n142.4828ms时读到I(RS_OUT)=0.9999704A、VOUT=4.9885V，已达到≤1A，距130ms负载切换12.4828ms。左光标129.9919ms比切换早8.1us，故软件显示Δt=12.4909ms。可记录约12.48ms后观测到回到1A附近；不能把它当成精确首次穿越、连续超流时长或稳定时间，也不能保证此后始终≤1A。\n\n本阶段的游标操作可结束：已记录峰顶附近1.5690A与一次≤1A回落点。若需精确超限统计，再导出完整波形，避免继续反复手动定位。当前参数和器件全部保留，下一阶段分别量化指标并评估原图真实控制/保护与效率。\n\n[第三组光标JSON](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/cursor_observed_return_142ms.json) · [两点CSV](../simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/results/data/cursor_return_points_142ms.csv)。\n'
    report.write_text(text)
    c_build=json.loads((R/'open-load-diagnostic/results/C_build_checks.json').read_text());s_build=json.loads((R/'kiv20-regression/results/build_checks.json').read_text());d_build=json.loads((HERE/'results/data/build_checks.json').read_text())
    files=[(c_build['output'],c_build['output_sha256']),*[(row['file'],row['sha256']) for row in s_build['cases']],(d_build['output'],d_build['output_sha256'])]
    for path,expected in files:assert sha(PROJECT/path)==expected
    manifest={'date':'2026-10-24','native_files':[{'file':p,'sha256':h,'matches_prior_build':True} for p,h in files],'native_file_count':7,'native_files_changed_by_summary':False,'six_static_and_one_dynamic_screenshots_received':True,'numeric_native_exports_received':False,'complete_design_validated':False,'full_time_instantaneous_1A_limit_met':False,'cloud_native_execution_performed':False,'cursor_display_values_received':cursor_file.exists(),'global_peak_or_overcurrent_duration_verified':False,'observed_return_at_or_below_1A_received':returned_file.exists()}
    manifest_path=HERE/'results/data/phase_manifest.json';manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    package=PROJECT/'downloads/Multisim14_Ki20七工况阶段汇总_2026-10-24.zip'
    includes=[PROJECT/p for p,_ in files]+[report,csv_path,manifest_path,source_c,static,dynamic,HERE/'README.md',R/'kiv20-regression/README.md',R/'open-load-diagnostic/C_README.md']
    if cursor_file.exists():includes.extend([cursor_file,HERE/'results/data/cursor_points_130ms.csv'])
    if recovery_file.exists():includes.extend([recovery_file,HERE/'results/data/cursor_recovery_points_137ms.csv'])
    if returned_file.exists():includes.extend([returned_file,HERE/'results/data/cursor_return_points_142ms.csv'])
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        for p in includes:z.write(p,str(p.relative_to(PROJECT)))
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    checks={'package':str(package.relative_to(PROJECT)),'package_sha256':sha(package),'zip_integrity_verified':True,'seven_native_hashes_match_prior_builds':True,'condition_table_values_are_screenshot_estimates':True,'cursor_display_values_received':cursor_file.exists(),'full_numeric_native_export_received':False}
    (HERE/'results/data/phase_delivery_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps(checks,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
