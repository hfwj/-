# STEP02 5Ω收敛诊断

[最新：原始波形分析与RELTOL单项候选](../../../../reports/Multisim14_STEP02_5R_原始波形分析与RELTOL单项对照_2026-10-25.md) · [25ms REL001候选](../../../../downloads/GBUCK_STEP02_5R_TRAP_ITL300_REL001_25ms_DIAG.ms14)

已收到四通道原始数值并计算高侧VGS。电感末尾纹波正常量级，但SW上升时低栅压有约4.07V抬升；停止时低栅压又已接近0，不能直接认定直通是唯一中止根因。

单颗原Q2模型的固定端口重放可出现数值失败；收紧RELTOL的夹具对照完成，不能替代原生整机通过。下一主图候选仅RELTOL 0.003→0.001，其他设置/元件/模型/控制保持；等待本机25ms反馈。

历史：ITL100在21.4605ms报U2，梯形ITL300在22.7726ms报Q2体二极管，Gear在17.8381ms报Q2内部支路，观测版重现22.7726ms。历史失败不改写为通过。旧报告/ZIP保留当时快照。

复现：解压归档RAR，analyze_export.py生成数值分析/图和工作缓存，replay_q2.py读取缓存测试单颗模型，build_rel001.py构建当前候选。旧build_diagnostics.py/build_gear.py/build_trace.py对应历史候选，需复现旧文件时再运行。所有脚本均不等同于Windows Multisim本机运行验证。
