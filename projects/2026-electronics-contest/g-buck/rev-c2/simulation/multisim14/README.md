# Rev C.2 Multisim 配套工程

本版将 Rev C 的 Multisim 原生副本同步到 Rev C.2：活动 C_IOUT_PROT=100 nF，增加全部 7 项下游 VIN 监测器件，J_MON.1 对应 PA6/ADC12_IN6。主板 120 项器件的引脚与原理图一致。

本版以此前三份 **FULL/SMOKE/PRECHARGE 完整电路工程** 为基准。仓库另有独立的手工搭建 `GBUCK_REVC_DRIVER_30k.ms14`，其 V3 频率补丁保持原样，未对它套用本版完整电路同步，也不混用验证结果。

| 工程 | 用途 |
|---|---|
| [GBUCK_REVC2_FULL_SMOKE_10ms.ms14](../../downloads/GBUCK_REVC2_FULL_SMOKE_10ms.ms14) | 优先检查本机打开、模型载入和启动；10 ms 仍处软启动，不能按稳态 5 V 验收 |
| [GBUCK_REVC2_FULL_25V_5R_100ms.ms14](../../downloads/GBUCK_REVC2_FULL_25V_5R_100ms.ms14) | 25 V/5 Ω 主工程，假设已预充并闭合旁路；需要在 Multisim 本机验证 |
| [GBUCK_REVC2_PRECHARGE_ONLY_110ms.ms14](../../downloads/GBUCK_REVC2_PRECHARGE_ONLY_110ms.ms14) | 仅预充，MCU_EN 始终为 0；原 100 ms 模拟闭合旁路刺激保留 |

新通道 ADC_VIN_POST 已加入可选输出目录；需观察它时，应在运行前加入瞬态分析输出。原默认记录通道未增多。完整模型内嵌在文件中，`models/REVC2_PROTECT.lib` 是已核对的保护功能子电路副本，使用工程时不必另行导入它。

保护模型改为独立过流/低压约 20 ms 判据，提供故障记忆和 ARM 复位参考。与原 Rev C 立即抑制高边脉冲的策略不同；它不是 STM32 可烧录固件，也不代表真实故障关断时序。新 VIN 通道目前提供采样节点与观察接口，不是自动旁路确认或闭合控制。

已完成：双 DCL 解码、原生端口/符号连接核对、9 个外加波形的独立保护逻辑场景和 VIN RC 求解。未完成：Windows Multisim 客户端打开/运行、完整新版 Buck 动态、实际负载切换、实际短路、真实固件和效率验收。

物理影响与比较基准见[修订报告](../../reports/RevC1评审核对与RevC2修订说明.md)。
