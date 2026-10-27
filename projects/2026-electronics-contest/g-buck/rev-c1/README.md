# G 题同步 Buck Rev C.1

基于 Rev C 复核结果，修正 J_CTL.6 与 MOS 脚号显示，C_IOUT_PROT 改为 100 nF/25 V X7R，并新增预充后 VIN 采样支路及 PA5 接口。

| 交付 | 文件 |
|---|---|
| 完整新原理图 PDF（10 页，含说明） | [下载/预览 PDF](schematic/previews/G题同步Buck完整原理图_RevC1.pdf) |
| 嘉立创 EDA 专业版可编辑工程 | [下载 .eprj2](schematic/native/G题同步Buck_RevC1_原理图修订.eprj2) |
| BOM（120 项，标明与 Rev C 差异） | [BOM_RevC1.csv](schematic/BOM_RevC1.csv) |
| 修改说明、接线与使用要求 | [查看说明](reports/RevC1_修改说明与使用要求.md) |
| 全部原生引脚与验证证据 | [逐引脚 CSV](results/data/RevC1_逐引脚接线表.csv) · [验证 JSON](results/data/verification.json) |
| 整套下载 | [Rev C.1 原理图资料包](downloads/GBUCK_RevC1_原理图资料_2026-10-27.zip) |

**影响：**相对 Rev C，新增 7 项器件及 VIN 监测支路，更换 C_IOUT_PROT 电容，新增 J_MON→PA5/GND 两线连接；需要同步控制板接线与 PCB。原有主功率级、MOS 型号、保护门限和所有原有网络保持。

已通过静态原生历史/逐引脚/BOM核对：9 页、120 器件、51 网络、310 连接引脚。PDF 是从交付工程记录生成的增强预览，不是客户端导出。客户端打开、ERC/PCB DRC、实际固件、动态响应及整机效率均未验收；R_PRE 等实际封装与机械待确认项仍须完成，没有生产用 PCB。

**仿真影响：**没有更新或运行原 Rev C Multisim 文件；它仍是旧 1 nF 告警滤波和旧通道配置。新增采样能观察下游 VIN，不能单独证明手动旁路已经闭合；固件接口约束也不等于固件已经实现。

原版保留：[Rev C](../rev-c/README.md) · [附件复核报告](../rev-c/reports/RevC_按附件复核_2026-10-27.md)。
