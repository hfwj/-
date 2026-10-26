# STEP02 5Ω收敛诊断

[最新：后处理器无结果与从零记录对照](../../../../reports/Multisim14_STEP02_后处理器无结果与从零记录对照_2026-10-26.md) · [FROM0四路副本](../../../../downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_FROM0.ms14)。截图当前无仿真结果/变量，不能照旧从空列表绘图；先刷新，仍为空则回到TSTART=0、IncrPlot=1，保留100ms四路及全部模型/控制/求解/电路。build_u3_100ms_from0.py与LOWMEM、FINALPLOT及30ms基线交叉比对；无原图/器件/BOM/PCB修改，原生100ms和数据问题效果待验证。

[此前：FINALPLOT日志状态核对](../../../../reports/Multisim14_STEP02_FINALPLOT日志状态核对_2026-10-26.md)。新日志确认不再生成iplot/iplotExt命令，并明确保存供以后处理；write-and-destroy-iplot写出命令名称不等于仍增量绘图。用户回复没图像生成，结束状态/F1尚未新确认，当前快照止于Gmin completed，无实际末时间轴，100ms不判通过。audit_u3_finalplot_status.py核对日志/选项/状态边界；仅归档及说明，无新工程、模型、控制、求解、原图或器件/BOM/PCB修改。

[此前：100ms变量名错误与非增量绘图对照](../../../../reports/Multisim14_STEP02_100ms输出变量名错误与非增量绘图对照_2026-10-26.md) · [FINALPLOT副本](../../../../downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_FINALPLOT.ms14)。报错4.rar内两次16:10:31/16:21:58日志均采用新LOWMEM设置，末尾Unknown name: V(iout_raw)，无步长或内存错误记录，用户F1未熔断且两次无曲线。audit_u3_100ms_unknown_name.py保留分类界限；build_u3_100ms_finalplot.py仅改IncrPlot=0与标题，全部电路/模型/控制/求解/时间窗/四路保持。100ms及本对照效果未验证，不重传旧GRA。

[此前：U3平滑30ms用户报告通过与100ms准备](../../../../reports/Multisim14_STEP02_U3平滑30ms通过与100ms验证准备_2026-10-26.md) · [100ms末10ms四路副本](../../../../downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_LOWMEM.ms14)。用户明确回复“通过 F1未熔断”，关联刚交付的U3平滑30ms/8路文件；未附新结束日志/读数，不扩大为独立日志核验或100ms通过。build_u3_100ms_lowmem.py仅改TSTOP、报告起点、输出选择和标题，保留全部模型/求解/控制与元件；TSTART=.09是报告起点，前90ms仍积分。原图/器件值/BOM/PCB不改；全部三个采样实例仍是明确修改过的偏置模型。

[此前：U3补查与偏置平滑](../../../../reports/Multisim14_STEP02_U3共模补查与IIB平滑诊断_2026-10-26.md) · [30ms/8路U3新副本](../../../../downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_30ms_8CH_DIAG.ms14)。100nA原生候选在20.1209ms报U3 INP_PSRR_OUT，F1未熔断，恢复10nA。旧24.9514ms GRA的U3共模此前漏列，补算约5V；原记录重放四项均完成，另行人工受控跨分界才复现同节点失败，两种ABSTOL均失败，平滑后完成。有序上电原/平滑响应相同。replay_u3_event.py保留全部九项及刺激区别；audit_abs100na_failure.py核对新日志；build_u3_iib_smooth.py同步U3两份模型并恢复10nA，原图/BOM/PCB、MOS/驱动/控制、既有U2/U4平滑保持。analyze_q2_20261026.py已补U3共模，原始六卷不变、不重传。该轮生成时原生30ms/100ms待验证；后续30ms用户报告通过，见上方最新记录。

[此前：六卷原GRA与ABSTOL对照](../../../../reports/Multisim14_STEP02_Q2原始波形重放与ABSTOL对照_2026-10-26.md) · [失败100nA历史副本](../../../../downloads/GBUCK_STEP02_5R_ABSTOL100nA_30ms_8CH_DIAG.ms14)。末点24.9514416ms，原生边沿有4.333V低栅压抬升。19项探索未精确复现本机；100nA原生试验后续失败且不保留，见最新U3补查。原数据、所有探索失败/超时与构建记录保留；原图、器件/BOM/PCB未改。

[此前：10月26日14路日志与Q2 VFI2](../../../../reports/Multisim14_STEP02_100ms日志核对与Q2_VFI2定位_2026-10-26.md)：本次实际TSTART=0、save14路，24.9514ms在Q2内部VFI2报步长过小，用户确认该轮F1未熔断。与LOWMEM四路/.09s配置不同，不将本次判为精简方案已运行失败。后续六卷原GRA已收到并分析，不再等待重传。audit_20261026.py复核日志与节点映射；该轮仅记录/文档，无原图/BOM/PCB、模型、控制、求解设置变化。

[此前：100ms内存不足与精简记录](../../../../reports/Multisim14_STEP02_100ms内存不足与精简记录_2026-10-25.md) · [100ms末10ms四路工程](../../../../downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_LOWMEM.ms14)。截图明确提示内存不足，曲线约16ms，实际日志时间/F1未另确认，不等同原16.4408ms收敛故障。build_iib_low_memory.py保留积分至100ms、50ns/.001/ITL300，报告起点90ms且仅4路，原图/BOM/PCB/模型/控制不改。记录窗口是90–100ms，前90ms仍积分但无曲线；10月26日新日志仍是14路/TSTART=0，尚未验证本文件效果。先处理新Q2支路已有数据，不在本轮诊断前重跑末段方案。

[此前：平滑模型25ms截图与100ms对照](../../../../reports/Multisim14_STEP02_IIB平滑25ms截图与100ms对照_2026-10-25.md) · [历史14路100ms工程](../../../../downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14)。用户截图曲线延续至25ms，并明确确认该轮F1未熔断、未变色；无错误结束的日志及精确读数尚未收到。build_iib_100ms.py仅改TSTOP 25→100ms与图表标题，全部元件/引脚/模型/控制/其余求解设置/14路输出保持；相对25ms诊断版无新模型、原图、BOM或PCB变化。后续100ms遇内存不足，详见最新项，仍为修改过的共享U2/U4模型。

[最新：U4的5V分界重放与IIB平滑诊断](../../../../reports/Multisim14_STEP02_U4_5V分界重放与IIB平滑诊断_2026-10-25.md) · [25ms模型诊断候选](../../../../downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_25ms_DIAG.ms14)。四卷原GRA已读取，14路519429点，末点共模恰为5V。输入阻抗夹具原模型失败、平滑两条偏置分界后完成；理想电压钳位原模型也通过，不能忽略偏置反馈。候选仅改共享INA240 IIBP/IIBN为TANH、尺度0.1mV；U2/U4均受影响，其他器件/模型、原理图/BOM/PCB、控制、求解参数不改。原生25ms效果待反馈，原工程保留。解压原四卷获得GRA后，依次运行decode_gra.py、analyze_u4.py、replay_u4.py、build_iib_smooth.py；中间XML/NPZ留在工作目录，不入库。

[前次本机反馈：U4观察复现与波形传输](../../../../reports/Multisim14_STEP02_5R_U4观测复现与波形传输状态_2026-10-25.md)：日志6确认新增三路生效，共14路，仍16.4408ms在同一U4内部节点失败。当时新RAR超过文件工具32 MiB上限；后续四卷现已读取，不再等待重传。该轮仅归档/解析/文档，无原图、器件/BOM/PCB变化。audit_log6.py核对该事件；audit_log5.py保留更早检查。

[REL001本机失败与U4边界观测准备](../../../../reports/Multisim14_STEP02_5R_REL001失败与U4边界观测_2026-10-25.md) · [25ms U4观察工程](../../../../downloads/GBUCK_STEP02_5R_REL001_U4_TRACE_25ms.ms14)

错误日志5最后一段确认RELTOL=.001已生效，但16.4408ms在U4 INA240内部N504417仍失败，F1未熔断；不再称REL001待反馈或已修复。仅新增L_RAW/V_CAP/IL_BI记录与明确图表标题，供进一步检查实际共模、差分和供电；数值设置、元件、原图、BOM、TI/MOS/驱动模型及控制均保持。U2/U4共享同一模型，不能全局修改后称只改U4。audit_log5.py核对累计日志最后一段，build_u4_trace.py构建下一观察文件；结构校验不等同原生运行。

[历史：原始波形分析与RELTOL单项候选](../../../../reports/Multisim14_STEP02_5R_原始波形分析与RELTOL单项对照_2026-10-25.md) · [历史25ms REL001候选](../../../../downloads/GBUCK_STEP02_5R_TRAP_ITL300_REL001_25ms_DIAG.ms14)

已收到四通道原始数值并计算高侧VGS。电感末尾纹波正常量级，但SW上升时低栅压有约4.07V抬升；停止时低栅压又已接近0，不能直接认定直通是唯一中止根因。

单颗原Q2模型的固定端口重放可出现数值失败；收紧RELTOL的夹具对照完成，不能替代原生整机通过。此前主图候选仅RELTOL 0.003→0.001，其他设置/元件/模型/控制保持；本机反馈为16.4408ms失败，25ms未通过。

历史：ITL100在21.4605ms报U2，梯形ITL300在22.7726ms报Q2体二极管，Gear在17.8381ms报Q2内部支路，观测版重现22.7726ms。历史失败不改写为通过。旧报告/ZIP保留当时快照。

复现：解压归档RAR，analyze_export.py生成数值分析/图和工作缓存，replay_q2.py读取缓存测试单颗模型，build_rel001.py构建当前候选。旧build_diagnostics.py/build_gear.py/build_trace.py对应历史候选，需复现旧文件时再运行。所有脚本均不等同于Windows Multisim本机运行验证。
