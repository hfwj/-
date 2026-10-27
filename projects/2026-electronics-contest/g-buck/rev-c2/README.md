# G 题同步 Buck Rev C.2

按用户要求，先核对 `RevC1_review.md`，再修订。已确认原图 LCD SCK 使用 PA5，因此将 VIN 监测接口移至 **PA6/ADC12_IN6**，并同步 Multisim。

| 内容 | 文件 |
|---|---|
| 新原理图（说明＋9页预览） | [Rev C.2 PDF](schematic/previews/G题同步Buck完整原理图_RevC2.pdf) |
| 可编辑原理图 | [嘉立创 EDA .eprj2](schematic/native/G题同步Buck_RevC2_PA6修订.eprj2) |
| BOM 与逐引脚表 | [BOM](schematic/BOM_RevC2.csv) · [接线表](results/data/RevC2_逐引脚接线表.csv) |
| 核对结论与修订影响 | [完整报告](reports/RevC1评审核对与RevC2修订说明.md) · [原附件](references/RevC1_review.md) |
| Multisim 配套 | [使用入口](simulation/multisim14/README.md) · [100 ms 主工程](downloads/GBUCK_REVC2_FULL_25V_5R_100ms.ms14) · [10 ms 短检查](downloads/GBUCK_REVC2_FULL_SMOKE_10ms.ms14) · [110 ms 预充](downloads/GBUCK_REVC2_PRECHARGE_ONLY_110ms.ms14) |
| 全部资料 | [Rev C.2 下载包](downloads/GBUCK_RevC2_核对修订与Multisim_2026-10-27.zip) |

**相对 Rev C.1 的硬件影响：**不新增器件、不改阻容值或主板网络；J_MON.1 在控制板上的目标由 PA5 改接 PA6，GPIO/ADC 通道配置及控制板排线/PCB需同步。主功率级和保护门限保持。无生产用 PCB。

**仿真影响：**以旧 Rev C `.ms14` 为基准同步 100 nF 告警电容和 7 项监测器件，并将 MCU 功能模型改为独立的持续过流/低压 20 ms 判据。非 MCU 模型、输入/负载/求解设置保持，预充副本保持关闭 MCU。已核查全部主板端口，完成独立逻辑与 RC 求解；未运行完整新版 Buck 动态或 Windows Multisim，不是固件或效率验收。

附件的 88% 效率、1.244/1.586 A 峰值与 3.08/4.40 ms 超限时间未独立复现。原理图 PDF 是原生记录增强预览，客户端打开、ERC/DRC、实际固件和实物测试仍待完成。
