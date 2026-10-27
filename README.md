# 电子设计与仿真资料

按项目、版本和资料类型归档，报告、仿真源代码及验证数据一起保存。

## 项目目录

| 项目 | 资料入口 | 当前结论 |
|---|---|---|
| 2026 电子电赛 G题：Rev C.2 PCB实物适配 | [工程/说明](projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/README.md) · [PCB预览](projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/previews/PCB_RevC2_120x90.png) | 120×90 mm、120器件，修订P2.54端子/D10电容/65125电感/6×30管夹；同步310逻辑引脚并补局部布线；有封装、F1规格及C4耐压变化；完整布线、实物封装与原生DRC待完成，不能制板 |
| 2026 电子电赛 G题：Rev C.2 评审核对与配套修订 | [项目/下载入口](projects/2026-electronics-contest/g-buck/rev-c2/README.md) · [核对报告](projects/2026-electronics-contest/g-buck/rev-c2/reports/RevC1评审核对与RevC2修订说明.md) | 确认LCD占用PA5，监测接口改PA6；已同步Multisim电容/7项监测器件及独立保护计时模型；静态与独立逻辑检查通过，整机动态/固件/效率未验收 |
| 2026 电子电赛 G题：Rev C.1 新原理图 | [项目/整包入口](projects/2026-electronics-contest/g-buck/rev-c1/README.md) · [PDF](projects/2026-electronics-contest/g-buck/rev-c1/schematic/previews/G题同步Buck完整原理图_RevC1.pdf) · [可编辑工程](projects/2026-electronics-contest/g-buck/rev-c1/schematic/native/G题同步Buck_RevC1_原理图修订.eprj2) | 修正脚名/显示，告警电容100nF，新增下游VIN监测；新增7器件并需同步PCB/控制板接线；静态核查通过，ERC/DRC、固件与实测未验收 |
| 2026 电子电赛 G题：Rev C 附件复核 | [项目入口](projects/2026-electronics-contest/g-buck/rev-c/README.md) · [复核报告](projects/2026-electronics-contest/g-buck/rev-c/reports/RevC_按附件复核_2026-10-27.md) | 原生 QH/QL 接线正确；J_CTL.6 旧 GND 名称待修正；固件、效率、ERC/DRC 待验证。本次仅新增审查资料，未改原理图、器件或模型 |
| 2026 电子电赛 G题：Rev C Multisim完整搭建 | [100ms主工程](projects/2026-electronics-contest/g-buck/rev-c/downloads/GBUCK_REVC_FULL_25V_5R_100ms.ms14) · [10ms短检查](projects/2026-electronics-contest/g-buck/rev-c/downloads/GBUCK_REVC_FULL_SMOKE_10ms.ms14) · [110ms预充](projects/2026-electronics-contest/g-buck/rev-c/downloads/GBUCK_REVC_PRECHARGE_ONLY_110ms.ms14) · [搭建图纸与说明PDF](projects/2026-electronics-contest/g-buck/rev-c/simulation/multisim14/diagrams/Multisim14_RevC完整搭建与使用说明.pdf) | 113项主板器件逐引脚核对；有电路/器件配套变动；跨引擎100ms检查完成，Multisim本机打开/运行待确认 |
| 2026 电子电赛 G题：Rev C 原理图修订 | [PDF](projects/2026-electronics-contest/g-buck/rev-c/schematic/previews/G题同步Buck完整原理图_RevC.pdf) · [可编辑工程](projects/2026-electronics-contest/g-buck/rev-c/schematic/native/G题同步Buck_RevC_原理图修订.eprj2) · [BOM](projects/2026-electronics-contest/g-buck/rev-c/schematic/BOM_RevC.csv) | 有原理图、器件与排线/PCB影响；未运行ERC/DRC，未实现瞬时1A硬限流 |
| 2026 电子电赛 G题：模拟充电装置，同步 Buck Rev B | [项目首页](projects/2026-electronics-contest/g-buck/rev-b/README.md) | PDF重建模型在假设控制下稳态可行；总效率、实际固件与硬件时序尚未验证 |

[NI Multisim 14.0搭建入口](projects/2026-electronics-contest/g-buck/rev-b/simulation/multisim14/README.md)：接线图、SPICE功能模型、工况文件及本机搭建步骤；未提供原生`.ms14`文件。

## 归档约定

- `references/`：用户提供的试题、原理图、物料清单及来源校验。
- `reports/`：可读报告，提供 PDF、DOCX、Markdown。
- `simulation/`：仿真代码、网表、依赖和重跑说明。
- `results/data/`：计算结果、CSV/JSON 与压缩波形数据。
- `results/figures/`：波形及图表。
- `results/logs/`：求解过程日志。
- `downloads/`：便于整体下载的资料压缩包。

以后新增或修订的成果按上述方式归类，提交并推送到本仓库。仓库内容需区分模型假设、已执行验证和未验证项目。

## 下载

打开项目首页选择报告或资料包。在 GitHub 文件页面使用 **Download raw file** 下载；也可通过仓库 **Code → Download ZIP** 下载全部资料（包含原始压缩波形，体积较大）。私有仓库需登录有访问权限的 GitHub 账号。
