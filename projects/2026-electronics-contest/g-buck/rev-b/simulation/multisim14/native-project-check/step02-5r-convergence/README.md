# STEP02 5Ω收敛诊断

[最新：Gear失败与开关过程观测](../../../../reports/Multisim14_STEP02_5R_Gear失败与开关波形观测_2026-10-25.md) · [25ms观测工程](../../../../downloads/GBUCK_STEP02_5R_TRAP_ITL300_25ms_TRACE.ms14)

ITL100在21.4605ms报U2内部支路；梯形ITL300在22.7726ms报Q2体二极管；Gear ITL300在17.8381ms报Q2电容网络电流检测支路。三轮F1均由用户确认未熔断，均未完成各自目标时长。根因尚未确定。

下一步回到覆盖较长的梯形ITL300基线，新增输出观察并显式固定同一梯形方法，采集中止前的栅极、SW、电感电流、PWM、母线、使能。原理图/器件/BOM/模型和该基线其余求解设置保持。原报告及ZIP保留历史状态，旧“待本机”结论以最新报告为准。

构建顺序：build_diagnostics.py为历史ITL候选；build_gear.py为历史Gear候选；build_trace.py生成当前观测版，不需要重跑旧脚本覆盖已交付文件。所有构建均不等同于Windows Multisim运行通过。
