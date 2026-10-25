# STEP02 5Ω收敛诊断

[最新本机反馈：U4观察复现与波形传输](../../../../reports/Multisim14_STEP02_5R_U4观测复现与波形传输状态_2026-10-25.md)：日志6确认新增三路生效，共14路，仍16.4408ms在同一U4内部节点失败。新RAR超过文件工具32 MiB上限，内容尚未读取，等待现有文件25MB分卷；不重跑、不改求解设置或模型。本轮仅归档/解析/文档，无原图、器件/BOM/PCB变化。audit_log6.py核对最新事件；audit_log5.py保留前次检查。

[REL001本机失败与U4边界观测准备](../../../../reports/Multisim14_STEP02_5R_REL001失败与U4边界观测_2026-10-25.md) · [25ms U4观察工程](../../../../downloads/GBUCK_STEP02_5R_REL001_U4_TRACE_25ms.ms14)

错误日志5最后一段确认RELTOL=.001已生效，但16.4408ms在U4 INA240内部N504417仍失败，F1未熔断；不再称REL001待反馈或已修复。仅新增L_RAW/V_CAP/IL_BI记录与明确图表标题，供进一步检查实际共模、差分和供电；数值设置、元件、原图、BOM、TI/MOS/驱动模型及控制均保持。U2/U4共享同一模型，不能全局修改后称只改U4。audit_log5.py核对累计日志最后一段，build_u4_trace.py构建下一观察文件；结构校验不等同原生运行。

[历史：原始波形分析与RELTOL单项候选](../../../../reports/Multisim14_STEP02_5R_原始波形分析与RELTOL单项对照_2026-10-25.md) · [历史25ms REL001候选](../../../../downloads/GBUCK_STEP02_5R_TRAP_ITL300_REL001_25ms_DIAG.ms14)

已收到四通道原始数值并计算高侧VGS。电感末尾纹波正常量级，但SW上升时低栅压有约4.07V抬升；停止时低栅压又已接近0，不能直接认定直通是唯一中止根因。

单颗原Q2模型的固定端口重放可出现数值失败；收紧RELTOL的夹具对照完成，不能替代原生整机通过。此前主图候选仅RELTOL 0.003→0.001，其他设置/元件/模型/控制保持；本机反馈为16.4408ms失败，25ms未通过。

历史：ITL100在21.4605ms报U2，梯形ITL300在22.7726ms报Q2体二极管，Gear在17.8381ms报Q2内部支路，观测版重现22.7726ms。历史失败不改写为通过。旧报告/ZIP保留当时快照。

复现：解压归档RAR，analyze_export.py生成数值分析/图和工作缓存，replay_q2.py读取缓存测试单颗模型，build_rel001.py构建当前候选。旧build_diagnostics.py/build_gear.py/build_trace.py对应历史候选，需复现旧文件时再运行。所有脚本均不等同于Windows Multisim本机运行验证。
