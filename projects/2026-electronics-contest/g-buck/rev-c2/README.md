# G 题同步 Buck Rev C.2

按用户要求，先核对 `RevC1_review.md`，再修订。已确认原图 LCD SCK 使用 PA5，因此将 VIN 监测接口移至 **PA6/ADC12_IN6**，并同步 Multisim。

| 内容 | 文件 |
|---|---|
| 新原理图（说明＋9页预览） | [Rev C.2 PDF](schematic/previews/G题同步Buck完整原理图_RevC2.pdf) |
| 可编辑原理图 | [嘉立创 EDA .eprj2](schematic/native/G题同步Buck_RevC2_PA6修订.eprj2) |
| BOM 与逐引脚表 | [BOM](schematic/BOM_RevC2.csv) · [接线表](results/data/RevC2_逐引脚接线表.csv) |
| 按当前PCB更新的采购清单 | [Excel](downloads/GBUCK_RevC2_updated_BOM.xlsx) · [PDF](downloads/GBUCK_RevC2_updated_BOM.pdf) · [明细/说明](reports/updated-bom-2026-10-27/README.md)；120位号、45项合并采购行，外接辅料另列，含库存/补购计算与待确认项 |
| 50mΩ分流电阻商品图确认 | [证据与修改影响](pcb/hardware-fit-120x90/reports/50mΩ商品图确认.md)；RS_IN/OUT脚距10mm、线径0.8mm，已同步专用封装关联与BOM；铜几何保持，RS_L尺寸不从本图推定 |
| 25mΩ分流电阻商品图确认 | [证据与修改影响](pcb/hardware-fit-120x90/reports/25mΩ商品图确认.md)；RS_L按U型P5、图示线径0.7mm、体高7mm建库，原P10孔位已改P5；网络/阻值保持，精度/功率等待核 |
| 5×20mm保险管夹确认 | [证据与试装要求](pcb/hardware-fit-120x90/reports/F1_5x20夹P5p66确认.md)；F1为2A快断，用户确认单夹P5.66，四槽更新；两夹15mm中心距仅试装初值，旧6×30/7.7参考作废 |
| 电感、二极管及C_A3确认 | [确认记录](reports/component-confirmations-2026-10-27/README.md)；C_A3已按用户0805改焊盘（10μF/25V保持）；L1立式；D1/D_FREE均按用户SR560/SMB同步物料标注，铜焊盘/位置/走线保持，厂家数据最终复核待归档；仿真未改 |
| 核对结论与修订影响 | [完整报告](reports/RevC1评审核对与RevC2修订说明.md) · [原附件](references/RevC1_review.md) |
| Multisim 配套 | [使用入口](simulation/multisim14/README.md) · [100 ms 主工程](downloads/GBUCK_REVC2_FULL_25V_5R_100ms.ms14) · [10 ms 短检查](downloads/GBUCK_REVC2_FULL_SMOKE_10ms.ms14) · [110 ms 预充](downloads/GBUCK_REVC2_PRECHARGE_ONLY_110ms.ms14) |
| 全部资料 | [Rev C.2 下载包](downloads/GBUCK_RevC2_核对修订与Multisim_2026-10-27.zip) |
| 按实购物料修订的120×90 PCB | [可编辑工程与说明](pcb/hardware-fit-120x90/README.md) · [PCB预览](pcb/hardware-fit-120x90/previews/PCB_RevC2_120x90.png) · [PCB资料包](downloads/GBUCK_RevC2_PCB_review_2026-10-27.zip)；120器件/310逻辑引脚一致，局部布线，完整布线与原生DRC未完成 |

**相对 Rev C.1 的硬件影响：**不新增器件、不改阻容值或主板网络；J_MON.1 在控制板上的目标由 PA5 改接 PA6，GPIO/ADC 通道配置及控制板排线/PCB需同步。主功率级和保护门限保持。无生产用 PCB。

**仿真影响：**以旧 Rev C `.ms14` 为基准同步 100 nF 告警电容和 7 项监测器件，并将 MCU 功能模型改为独立的持续过流/低压 20 ms 判据。非 MCU 模型、输入/负载/求解设置保持，预充副本保持关闭 MCU。已核查全部主板端口，完成独立逻辑与 RC 求解；未运行完整新版 Buck 动态或 Windows Multisim，不是固件或效率验收。

附件的 88% 效率、1.244/1.586 A 峰值与 3.08/4.40 ms 超限时间未独立复现。原理图 PDF 是原生记录增强预览，客户端打开、ERC/DRC、实际固件和实物测试仍待完成。
