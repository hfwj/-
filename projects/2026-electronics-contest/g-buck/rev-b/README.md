# G题模拟充电装置 · 同步 Buck Rev B

依据用户提供的完整原理图 PDF、试题 DOCX 和物料清单 DOCX，重建开关电路模型并执行验证。

## 下载与阅读

- [嘉立创 EDA Rev B：120×90 mm 首轮布局](pcb/github-rework-120x90/README.md) · [原生工程](pcb/github-rework-120x90/native/G题同步Buck_RevB_120x90_布局草稿.eprj2) · [整包下载](downloads/嘉立创EDA_G题RevB_120x90_首轮布局_2026-10-25.zip)：从 GitHub 同步 Buck 工程新增独立 Rev B 板页；7 页原理图，96 器件/43 网络/264 连接端点与用户 PDF 一致。板框 120×90 mm、双层，器件布局草稿，未布线；客户端打开及原生 ERC/DRC 未执行。相对 GitHub 有电路/器件/PCB 改动，相对 PDF 未主动改拓扑与数值；机械封装待确认，原仿真/固件未改。

- [STEP02 U3平滑：30ms通过与100ms验证准备](reports/Multisim14_STEP02_U3平滑30ms通过与100ms验证准备_2026-10-26.md) · [100ms末10ms四路工程](downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_LOWMEM.ms14)：用户明确反馈新U3平滑30ms副本通过、F1未熔断；本条反馈未附新日志/读数，100ms仍待验证。新副本保留三个采样实例的既有平滑模型、控制与全部求解选项，仅延长30→100ms、报告90–100ms、8→4路；原理图/器件值/BOM/PCB不改。离散保护继续独立夹具测试，尚未接入主图。

- [STEP02 U3共模补查与偏置平滑](reports/Multisim14_STEP02_U3共模补查与IIB平滑诊断_2026-10-26.md) · [U3平滑30ms/8路工程](downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_30ms_8CH_DIAG.ms14)：100nA候选已生效但20.1209ms报U3 INP_PSRR_OUT，F1未熔断，本项不保留。补算此前漏列的U3共模，旧24.9514ms末点也几乎恰好5V；人工受控跨越在原U3模型10/100nA下复现同节点失败，平滑后完成，特定有序上电响应保持。新副本恢复10nA，仅新增U3偏置分界平滑，保留已有U2/U4平滑，Q1/Q2、驱动、控制及硬件不改；该报告生成时原生30ms/100ms待验证；后续用户反馈30ms通过，见上方最新记录，100ms仍待验证。

- [STEP02 Q2：新原始波形与ABSTOL对照](reports/Multisim14_STEP02_Q2原始波形重放与ABSTOL对照_2026-10-26.md) · [历史100nA容差副本](downloads/GBUCK_STEP02_5R_ABSTOL100nA_30ms_8CH_DIAG.ms14)：六卷已解压，14路各815260点，末点24.9514416ms；边沿有4.333V低栅压抬升。19项探索未精确复现本机；100nA压力夹具成功未转为原生成功，后续20.1209ms报U3，本项不保留。此前漏列U3共模，现已补算旧末点约5V并更新图/表，详见上方补查。原数据与失败记录保留，该轮无原图/BOM/PCB或模型改动。

- [STEP02 100ms日志核对与Q2 VFI2定位](reports/Multisim14_STEP02_100ms日志核对与Q2_VFI2定位_2026-10-26.md)：10月26日新日志实际为14路、TSTART=0，在24.9514ms报Q2内部VFI2支路步长过小，用户明确确认F1未熔断，100ms未完成。与此前LOWMEM的四路/.09s设置不同，不判为低内存方案已失败；本轮是收敛错误而非日志报告内存不足。后续六卷原GRA已取得并分析，详见上方新报告；该轮只记录/定位，无原图、器件/BOM/PCB、模型/控制/求解设置修改。

- [STEP02 100ms：内存不足与精简记录](reports/Multisim14_STEP02_100ms内存不足与精简记录_2026-10-25.md) · [100ms低内存工程](downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_LOWMEM.ms14)：本机明确报内存不足，未完成100ms；不能仅据弹窗推断重现旧收敛故障。新副本仅保存90–100ms的VOUT/I(RS_OUT)/IOUT_RAW/VDDA四路，仍从t=0积分至100ms，保留50ns、.001、ITL300及现有U2/U4平滑模型，无原图、器件/BOM/PCB或新模型变化。10月26日收到日志对应14路/TSTART=0并在24.9514ms失败，优先保留其GRA，不在本次开关诊断前重跑此末段方案；LOWMEM实际效果仍未验证。

- [STEP02 IIB平滑：25ms截图与100ms对照](reports/Multisim14_STEP02_IIB平滑25ms截图与100ms对照_2026-10-25.md) · [历史14路100ms工程](downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14)：已收曲线覆盖25ms的本机截图，用户明确确认该轮F1未熔断、未变色；日志与精确读数仍待核对。仅将平滑诊断工程TSTOP从25ms延至100ms并改标题，不再改U2/U4模型或其他模型/控制/求解参数，无原图、器件/BOM/PCB变化；后续100ms本机报内存不足，详见上方精简方案，不将截图或修改模型称为原始模型/硬件验收通过。

- [STEP02 U4：5V分界重放与IIB平滑诊断](reports/Multisim14_STEP02_U4_5V分界重放与IIB平滑诊断_2026-10-25.md) · [25ms模型诊断工程](downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_25ms_DIAG.ms14)：四卷已解压，原生GRA14路各519429点，末点16.440824408ms，U4共模恰好5V。保留25mΩ输入阻抗的局部原模型重放在偏置SGN分界失败，1mV/0.1mV平滑均完成；理想电压钳位原模型也通过，说明需保留输入阻抗反馈。原生副本仅把共享INA240的两条IIB分界改为0.1mV尺度连续函数，**影响U2和U4模型**；硬件/BOM/PCB、U3/MOS/驱动/控制、求解参数不改。后续截图已覆盖25ms且该轮F1未熔断，无错误日志仍待核对，不能称完整修复。

- [STEP02 5Ω：U4观察工程本机复现与传输状态](reports/Multisim14_STEP02_5R_U4观测复现与波形传输状态_2026-10-25.md)：错误日志6确认14路记录及REL001/梯形/ITL300生效，仍在16.4408ms的U4内部N504417失败，25ms未通过；本轮F1状态未另确认。当时RAR超过工具32 MiB上限，后续四卷已成功读取并分析，详见上方新报告；该轮仅日志/文档与解析复核，无原图、器件/BOM/PCB、模型、控制或求解设置变化。


- [STEP02 5Ω：REL001失败与U4边界观测](reports/Multisim14_STEP02_5R_REL001失败与U4边界观测_2026-10-25.md) · [25ms U4观察工程](downloads/GBUCK_STEP02_5R_REL001_U4_TRACE_25ms.ms14)：日志5确认RELTOL=.001、梯形、ITL300已生效，但16.4408ms仍报步长过小，位置为U4 INA240内部N504417；用户确认该轮F1未熔断，25ms未通过。停止继续叠加求解参数，仅新增L_RAW/V_CAP/IL_BI三路记录并标明图表标题，以取得U4真实边界；原理图/器件/BOM/模型/控制及全部数值参数均不改。后续观察版已由日志6确认同位置失败，数值波形待分卷传入。

- [STEP02 5Ω原始波形与Q2边界重放](reports/Multisim14_STEP02_5R_原始波形分析与RELTOL单项对照_2026-10-25.md) · [历史RELTOL=0.001候选](downloads/GBUCK_STEP02_5R_TRAP_ITL300_REL001_25ms_DIAG.ms14)：四通道各571734点，末点22.77258999ms；存在SW上升时G_L约4.07V抬升，高侧同刻VGS约5.07V，尚不定量判硬件直通。原Q2单独边界夹具中梯形/.003失败、.001/.0001完成，但REL001本机整机于16.4408ms失败，夹具结果未转化为整机通过。器件/接线/模型/控制均不改。

- [STEP02 5Ω：Gear失败与开关过程观测](reports/Multisim14_STEP02_5R_Gear失败与开关波形观测_2026-10-25.md) · [25ms观测工程](downloads/GBUCK_STEP02_5R_TRAP_ITL300_25ms_TRACE.ms14)：日志确认Gear生效，但17.8381ms报Q2内部VFI1支路步长过小，F1未熔断；未完成25ms。返回覆盖更长的梯形ITL300基线，新增栅极/SW/电感电流/PWM/母线/使能观察并显式固定原梯形法，不改器件/模型/控制或其余求解数值；观测版日志已确认11通道生效，仍在22.7726ms报Q2体二极管；末尾局部图已收到：电感约0.90～1.09A、SW约10us周期，暂未见明显失控；需导出已有波形计算高侧VGS并检查边沿，根因未定，不改器件/模型或求解参数。

- [STEP02 5Ω：ITL300失败与Gear积分对照](reports/Multisim14_STEP02_5R_ITL300失败与Gear诊断_2026-10-25.md) · [Gear/25ms候选](downloads/GBUCK_STEP02_5R_GEAR_ITL300_25ms_DIAG.ms14) · [候选ZIP](downloads/Multisim14_STEP02_5R_Gear_Diagnostic_2026-10-25.zip)：本机ITL300在22.7726ms仍报步长过小，定位低侧Q2内部体二极管D1，F1未熔断，未完成25ms。下一候选相对该短时版仅启用Gear，其他参数/模型/器件均保持；结构校验完成；后续Gear于17.8381ms失败，详见上方观测记录。

- [STEP02 5Ω：U2定位与迭代上限诊断](reports/Multisim14_STEP02_5R_U2定位与迭代上限诊断_2026-10-25.md) · [先运行25ms诊断版](downloads/GBUCK_STEP02_5R_ITL300_25ms_DIAG.ms14) · [诊断ZIP](downloads/Multisim14_STEP02_5R_ITL300_Diagnostics_2026-10-25.zip)：已读取当前工程与完整历史日志，反馈/接线/模型正确，U2输入采样INA240内部支路在21.4605ms重复报错，用户确认F1未熔断。仅ITL4 100→300；短时版另改为25ms，保留容差/模型/全部器件。结构校验完成；后续本机在22.7726ms仍失败，详见上方Gear对照记录，不称已修复。

- [STEP02 25V/5Ω本机提前终止记录](reports/Multisim14_STEP02_U3_25V5Ω_21ms步长过小_2026-10-25.md)：用户确认已结束，日志在21.4605ms报Timestep too small，内部支路v_v8:x_ti:xu2#branch，失败步长6.25e-18s；未完成100ms，不标记通过。后续已取得工程与完整日志、确认本轮F1未熔断，详见上方U2定位诊断；原失败保留，无原图/器件/模型修改。

- [STEP03逐芯片保护独立测试指引](simulation/multisim14/protection-discrete-test/README.md)：已核对本次上传PDF第5/6页，与仓库原文件逐字节相同；明确LM393开集输出汇合、74HC74锁存、74HC08使能及74HC14/BAT54上电复位。先核对本机LM393型号/模型，独立测试尚未执行，未接入当前主图；本次仅新增说明，无器件/BOM/模型或原生工程修改。

- [STEP02 25V/8Ω本机100ms恒流核对](reports/Multisim14_STEP02_U3_25V8Ω本机100ms恒流核对_2026-10-25.md)：94.9575ms处VOUT=7.9665V，RS_OUT电流999.5041mA，IOUT_RAW=997.7028mV；相对1V/A的单点采样偏差约−0.180%，用户确认本次F1未熔断。符合基本恒流与采样预期，下一静态工况为5Ω副本；本次仅记录，不改原图/器件/模型。

- [STEP02本机100ms及95ms光标核对](reports/Multisim14_STEP02_U3_本机100ms采样核对_2026-10-25.md)：95.0121ms处VOUT=9.9834V，IOUT_RAW=501.4829mV，RS_OUT电流503.7873mA；相对10V单点偏差−0.166%，采样相对1V/A单点偏差约−0.457%。后段接近10V，用户已明确确认100ms本轮F1未熔断（30ms亦未熔断）。下一工况为独立8Ω负载副本；本次仅记录，不改原图/器件/模型。

- [STEP02本机30ms采样核对](reports/Multisim14_STEP02_U3_本机30ms采样核对_2026-10-25.md)：用户确认F1本次未熔断；29.0022ms处IOUT_RAW=484.5988mV、RS_OUT电流486.8077mA，按1V/A标称关系单点偏差−2.2089mV（约−0.454%）。VOUT末段约9.7V仍缓升（目测）；初步采样功能符合预期，下一步只延长至100ms观察。无原理图/器件/BOM/模型修改，下方修正交付条目的“本机待反馈”为历史状态。

- [U3接入后F1熔断：V3反馈引用修正](reports/Multisim14_U3接入_F1熔断_反馈节点修正_2026-10-25.md) · [STEP02原生修正版](downloads/GBUCK_STEP02_U3_FEEDBACK_FIX.ms14) · [工程与记录ZIP](downloads/Multisim14_STEP02_U3_FeedbackFix_2026-10-25.zip)：本次回传U3接线正确，V3仍用旧数字节点3/2；仅修正为V_CAP/L_RAW，保留全部接线、模型、F1=2A及30ms/50ns设置。原故障F1已熔断；修正版本机运行待反馈，独立诊断不模拟F1熔断。

- [U3 INA181本机独立有序上电测试](simulation/multisim14/ina181-power-on-check/README.md)：用户Multisim截图覆盖100us，89.9806us处输出497.2455mV，符合25mV差分输入时约0.5V的预期；仅本工况独立功能验证，未接入主Buck。保留固定电源初始化失败记录，不改原主图/器件/BOM/TI模型。下方较早导入条目的“待测试”是历史状态，以本条及详细记录为准。

- [STEP01采样接入反馈别名修正](reports/Multisim14_STEP01采样接入_反馈别名修正_2026-10-25.md) · [原生修正版](downloads/GBUCK_STEP01_IL_SENSE_FEEDBACK_FIX.ms14)：仅修正V3反馈节点别名，原接线/器件/Ki20保持；独立30ms完成，用户本机30ms图约6A异常消失。采样关系符合预期，本机按50ns对照指引补图后，VOUT明显平滑，30ms末约9.6～9.7V（目测）且仍缓慢上升；保留50ns，下一步复用结果核对U4采样关系，稳态精度未验收。
- [TI采样模型向导结构修正](simulation/multisim14/ti-sense-wizard-fix/README.md) · [当前导入包](downloads/Multisim14_TI_CurrentSense_WizardFix_2026-10-24.zip)：针对本机multiple top-level .subckt报错，只移动外层.ENDS、嵌套全部依赖；TI模型字节/参数和引脚不变。INA240回归通过，INA181动态仍未完成；本机导入待重试，不改主图/BOM。
- [两款TI采样模型与当前导入步骤](simulation/multisim14/ina181a1-ti-import/README.md) · [组合包](downloads/Multisim14_TI_CurrentSense_Import_2026-10-24.zip)：U2/U4的INA240独立DC/阶跃通过；U3的INA181 DC通过、瞬态未完成，失败记录保留。先导入INA240，均未运行本机Multisim、未改主图/BOM。
- [INA240A1上传TI模型与8脚导入说明](simulation/multisim14/ina240a1-ti-import/README.md) · [导入包](downloads/Multisim14_INA240A1_TI_8PIN_2026-10-24.zip)：原TI模型字节保留，只加7端到8脚接口；独立增益/参考/阶跃对照通过，本机导入待确认，用于U2/U4，U3需另模型；未改现有主图/BOM。
- [逐芯片采样功能模型及导入说明](simulation/multisim14/single-chip-sense/README.md) · [模型包](downloads/Multisim14_Sense_Chip_Functional_2026-10-24.zip)：针对本机库无INA240，提供独立8端INA240/6端INA181功能等效；增益、参考、限幅交叉检查通过，非TI模型，本机导入待确认；未编辑现有主图/BOM。
- [保护重启积分冻结对照](reports/Multisim14_保护重启积分冻结对照_2026-10-24.md) · [20ms原生工程](downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14)：此20ms功能模型对照通过；保留原失败基线，未改实物原图/BOM或真实固件，本机待验证。


- [采样与保护首轮验证](reports/Multisim14_RevB采样与保护首轮验证_2026-10-24.md) · [12ms原生诊断](downloads/GBUCK_REVB_PROT_POS_INJECT_12ms.ms14)：19项独立功能检查符合设定行为；耦合后两路栅极关断有效，但重新ARM触发约1.838A并再次保护，稳定恢复未通过。功能模型非厂商认证，不改板/BOM。
- [Ki20七工况阶段汇总](reports/Ki20_七工况本机功能验证阶段汇总_2026-10-24.md) · [七工程与报告ZIP](downloads/Multisim14_Ki20七工况阶段汇总_2026-10-24.zip)：六静态与自动CV/CC切换均有本机截图，峰顶附近光标1.5690A，距切换约12.48ms观测到0.9999704A回落点；精确过流时长仍未测定，不判为原图整机已通过。
- [Ki20动态切换工程](simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/README.md) · [动态ZIP](downloads/Multisim14_Ki20动态切换工况_2026-10-24.zip)：六静态及180ms动态图已收齐：10V/0.5A→8V/1A→5V/1A自动切换可见，仍有约1.6A瞬态；下一步导出精确数据，原图固件/保护/效率未验证。
- [C版改善后的Ki20静态回归](simulation/multisim14/native-project-check/control-loop/kiv20-regression/README.md) · [工况ZIP](downloads/Multisim14_Ki20静态回归工况_2026-10-24.zip)：C15V空载改善；同参数15V/25V的20Ω均约10V/0.5A，8Ω约8V/1A、5Ω约5V/1A均已收100ms图，六项静态截图已收齐。精确数据与动态仍待验证，不改板上器件。
- [空载C版单参数控制对照](simulation/multisim14/native-project-check/control-loop/open-load-diagnostic/C_README.md)：B截图与A起伏接近，C仅改电压外环Ki100→20；不改原理图和器件，不预称稳定性修复。
- [下一步：空载起伏A/B诊断](simulation/multisim14/native-project-check/control-loop/open-load-diagnostic/README.md) · [独立对照ZIP](downloads/Multisim14_空载起伏_AB对照_2026-10-24.zip)：保持原器件和控制不变，比较RELTOL=0.01与0.003的100ms结果；已做文件结构核对，待本机运行，不是已修复版本。
- [本机工况反馈阶段结论与原题覆盖](reports/Multisim14_本机工况反馈阶段结论_2026-10-24.md)：早期Ki100空载起伏与后续Ki20改善/回归分别记录；不混合不同控制参数的验证结果。原图固件、保护及效率仍未验证。
- 早期Ki100的七工况本机截图覆盖静态恒压/恒流、15V空载及自动切换；空载约11V过冲和切换约1.6A峰值仍需评估。见[控制模型本机反馈记录](simulation/multisim14/native-project-check/control-loop/results/data/native_user_feedback.json)。15V空载回传已接回2A保险丝，真实保护/效率未验证。
- 用户已反馈[CV/CC副本中25V/20Ω恒压工况](simulation/multisim14/native-project-check/control-loop/results/data/native_user_feedback.json)的本机30ms波形：软启动后约10V、峰值约10.4V；其余工况反馈见上方汇总。
- [当前本机工程的软启动与CV/CC控制副本](simulation/multisim14/native-project-check/control-loop/README.md) · [专用ZIP](downloads/Multisim14_软启动与CVCC控制副本_2026-10-24.zip) · [最终测试报告](reports/Multisim14_软启动与CVCC控制仿真_2026-10-24.md)：七个开关交叉工况完成，七工况均已有本机截图，15V空载100ms持续起伏，尚不能确认充分稳定。采用理想控制和采样，保护与效率未验证。
- [保险丝对照后本机20ms结果](reports/Multisim14_保险丝对照后20ms结果_2026-10-24.md)：新图末段约9.2V，持续下降不再可见；仍有约16V启动过冲，尚未通过10V恒压/1A恒流要求。
- [本机20ms输出持续下降排查](reports/Multisim14_本机20ms输出持续下降排查_2026-10-24.md)：用户新图末段约6.7V且仍下降，与交叉结果不同；需核对当前工程、输入母线、自举供电及F1状态，尚未定位。
- [40%开环测试启动振荡排查](reports/Multisim14_40percent开环启动振荡_2026-10-24.md)：用户新图出现约15V峰值与5V谷值，尚未稳定；核对LC周期并给出20ms观察步骤。
- [用户本机5ms启动波形反馈](reports/Multisim14_本机5ms启动波形反馈_2026-10-24.md)：自定义容差启用后，截图显示开关/输出曲线到5ms；仍为10%占空比开环测试，尚未验证10V稳压及1A恒流。
- [PWM首次切换报错：瞬态容差调整说明](reports/Multisim14_PWM首次切换步长过小_2026-10-24.md) · [新的5ms原生工程](downloads/设计1_瞬态容差调整_5ms_待本机验证.ms14)：针对用户本机2.00002ms步长过小，提供仅调整求解设置的副本；交叉验证与本机结果分开记录。
- [用户原生Multisim工程排查与模型修订](simulation/multisim14/native-project-check/README.md)：定位IR2104内嵌模型的3.3V输入兼容问题；提供1ms检查及5ms修订副本，待本机打开/运行确认。
- [1ms原生工程检查副本](downloads/设计1_IR2104模型修订_1ms检查.ms14) · [较早的5ms模型修订副本](downloads/设计1_IR2104模型修订_待本机验证.ms14) · [排查报告](reports/Multisim14_用户工程空白波形排查_2026-10-24.md)。较早5ms副本的本机运行在PWM启动时失败，新求解设置副本见上一条。
- [按原始原理图逐元件绘制Multisim电路](simulation/multisim14/original-schematic/README.md)：7页绘制参考、96项元件选择、逐引脚及逐网络接线表。
- [原图逐元件绘制PDF](simulation/multisim14/original-schematic/原始原理图_Multisim逐元件绘制参考.pdf) · [专用资料ZIP](downloads/Multisim14_按原图逐元件绘制资料包.zip)：供本机手工绘制，未生成原生.ms14文件。
- [NI Multisim 14.0仿真电路搭建说明](simulation/multisim14/README.md)：4页接线图、导入模型和9个测试工况；不是原生`.ms14`工程。
- [元器件向导逐页详细操作](simulation/multisim14/元器件向导逐页操作.md)：逐页填写、17脚映射、保存与首次运行。
- [Multisim电路交付与交叉核验说明](reports/Multisim14_仿真电路交付与核验说明.md)：当前模型9个工况的结果和未验证范围。
- [Multisim 14.0接线图PDF](simulation/multisim14/diagrams/Multisim14_仿真电路接线图.pdf)
- [Multisim 14.0专用搭建包ZIP](downloads/Multisim14_仿真电路搭建包.zip)
- [原理图可行性与题意符合性审查](reports/原理图可行性与题意符合性审查.md)：逐项判断，重点说明控制、瞬时限流、效率和显示要求。
- [仿真报告 PDF](reports/G题_RevB_仿真验证报告.pdf)
- [可编辑报告 DOCX](reports/G题_RevB_仿真验证报告.docx)
- [在线阅读报告 Markdown](reports/G题_RevB_仿真验证报告.md)
- [轻量完整资料包 ZIP](downloads/G题_RevB_仿真验证资料.zip)：报告、源文件、模型、汇总数据、图表及日志，不包含体积较大的 NPZ 波形。

GitHub 文件页面使用 **Download raw file** 下载文件。所有 NPZ 压缩波形另保存在 `results/data/`，可随整个仓库下载。

## 已得到的结果及边界

- 22项瞬态仿真、2组参考/比较极性DC扫描；另核对16种理想锁存逻辑组合。
- 在明确假设的连续双环控制下，恒压约10V；25V输入、8Ω/5Ω负载约0.996A/0.997A。
- 负载阶跃中瞬时负载电流约1.59A，不能认定全过程不超过1A。
- 总效率≥85%未确认；25V/8Ω点尚未计入的辅助及开关/磁芯/温升损耗预算约0.85W。
- 最初报告使用重建模型，未获得STM32固件或原始PCB/EDA工程；后续上传的Multisim工程及其中嵌入模型另行核对、归档。上述结果不构成实际固件、真实器件时序、PCB检查或整机测试通过。

## 分类入口

| 分类 | 路径 | 内容 |
|---|---|---|
| 原始资料 | [references/](references/) | 原理图、试题、物料清单、SHA256及提取文字 |
| 报告 | [reports/](reports/) | PDF、DOCX、Markdown |
| 仿真 | [simulation/](simulation/) | Python脚本、SPICE网表、依赖、安装脚本 |
| 数据 | [results/data/](results/data/) | CSV、JSON、NPZ及DC扫描数据 |
| 图表 | [results/figures/](results/figures/) | 稳态纹波、动态波形、短路、效率预算 |
| 日志 | [results/logs/](results/logs/) | 每个已归档工况的ngspice输出 |
| 压缩包 | [downloads/](downloads/) | 便于下载的轻量资料包 |

## 重跑

详见 [simulation/README.md](simulation/README.md)。代码按当前位置生成网表和输出路径；迁移后先用Python脚本重新生成，不要直接依赖归档网表中的旧绝对路径。

此次发布保留已完成仿真的数据，只调整目录和输出路径。归档后重新验证参考网络、代表性25V/8Ω工况及报告生成，结果见 [publication_checks.json](results/data/publication_checks.json)。
