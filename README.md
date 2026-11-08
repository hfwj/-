# 电子设计与仿真资料

2026-11-08：[A题v20引言照片已插入](projects/全球大学生物理竞赛/2026-A-一级火箭回收/v20/README.md)。21页，正文第1页含用户附件照片和英文图注；符号表和图二/三排版保持；模型、结果、原理图、器件不变。

2026-11-08：[A题v19正式论文措辞修订](projects/全球大学生物理竞赛/2026-A-一级火箭回收/v19/README.md)。删除“原文档”相关编辑表述及重排附录，保留技术局限；21页，模型/结果/原理图/器件不变。

2026-11-08：[A题v18符号逐行与姿态图排版修订](projects/全球大学生物理竞赛/2026-A-一级火箭回收/v18/README.md)。§2.2逐符号列示；§5.3标注滑行断开、图例移出曲线；引言实拍图待可读取原图文件。仅排版，模型/原理图/器件不改。

按项目、版本和资料类型归档，报告、仿真源代码及验证数据一起保存。

设计约定：电源接口优先用鳄鱼夹可夹持的板凳式焊接接线柱，保留合适的通孔件由工厂焊接。电流、耐压、间距和机械尺寸按实际工况选型，不统一要求接线柱≥5A。详见[仓库约定](AGENTS.md)。

交付格式约定：嘉立创EDA工程采用专业版 **`.eprj3`文件夹工程**，下载包必须包含索引及`sch`图页目录；历史标准版JSON仅保留作输入或旧版归档。

装配要求更新（2026-11-08，最新确认）：保留适合的通孔件，目标由工厂完成“贴片＋插件”焊接；不再要求所有元件均为SMT。取消接线柱统一≥5A门槛，按各路负载及保护选型；工厂能否焊接须逐料号/订单审核。

## 项目目录

2026-11-08：[R6可拔插主控与屏幕：已选模块、原理图及BOM](projects/2026-electronics-contest/g-buck/socket-adaptation-r6/README.md) · [eprj3完整工程](projects/2026-electronics-contest/g-buck/socket-adaptation-r6/downloads/GBUCK_System_R6_EPRJ3.zip)。WeAct BluePill-Plus V1.1/ST STM32F103C8T6＋Joy-IT SBC-LCD84x48 Rev.2，通过排母安装；主控底板17件88脚，另采购两个模块。相对R5更改插座/JLCD脚序、电压ADC至PA2及减小键至PB10，需改固件配置；主功率/辅源图页和10针接口不变，模型未改。静态网络及官方只读查看器通过；封装/PCB、供电容差、实物和代焊订单仍待核。

2026-11-08：[R5主控六区＋辅助降压三区原理图及BOM](projects/2026-electronics-contest/g-buck/partition-r5/README.md) · [eprj3完整工程](projects/2026-electronics-contest/g-buck/partition-r5/downloads/GBUCK_System_R5_EPRJ3.zip)。两板36件150脚，重画分区及实际连线，保留R4网络/标称值；补全部分0805建议选型，固件/模型不改。用户确认保留通孔件，由工厂贴片＋插件焊接，替代此前全SMT要求；实际料号/订单审核、封装/PCB/实测仍待完成。

2026-11-08：[G题R4：自设计3.3V贴片辅助电源](projects/2026-electronics-contest/g-buck/self-aux-r4/README.md) · [eprj3完整工程](projects/2026-electronics-contest/g-buck/self-aux-r4/downloads/GBUCK_System_R4_EPRJ3.zip)。TPS560430X3F＋6只外围贴片元件替代成品M1，保留板凳柱；辅助板11件，主板/主控及固件/模型不改；格式/静态检查通过，PCB/实测待完成。

2026-11-08：[G题R3：三板辅助供电接口改板凳式焊接接线柱](projects/2026-electronics-contest/g-buck/aux-posts-r3/README.md) · [专业版eprj3整包](projects/2026-electronics-contest/g-buck/aux-posts-r3/downloads/GBUCK_System_R3_EPRJ3.zip)。主板J4、辅源输入/输出、主控JP四个接口改八只单极四脚柱；75件/277脚核对通过，主功率/控制参数、模型及固件不变；封装待定，原生ERC/实测未验证。

2026-11-08：[G题主板R2专业版eprj3完整工程](projects/2026-electronics-contest/g-buck/mainboard-r2/downloads/GBUCK_Mainboard_R2_EPRJ3.zip) · [说明](projects/2026-electronics-contest/g-buck/mainboard-r2/reports/eprj3交付说明.md)。格式转换保留44件/135脚，官方Schema及查看器显示通过；BOM/硬件/固件/模型不变，原生编辑保存/ERC尚未验证，封装未绑定。

2026-11-08：[最新G题主板R2嘉立创原理图](projects/2026-electronics-contest/g-buck/mainboard-r2/README.md) · [JSON/PDF/BOM整包](projects/2026-electronics-contest/g-buck/mainboard-r2/downloads/GBUCK_Mainboard_R2_EasyEDA_Std.zip)。44件/135脚静态通过；同步四只板凳柱和0603基础库选型，保留J3脚序；未绑定封装，未做原生ERC/PCB或实测。

2026-11-08：[主板BOM R2：板凳式接线柱、SMT基础库优先](projects/2026-electronics-contest/g-buck/mainboard-v1/reports/bom-r2-bench-posts/README.md) · [Excel](projects/2026-electronics-contest/g-buck/mainboard-v1/reports/bom-r2-bench-posts/Mainboard_BOM_R2.xlsx)。44件，17件官网已核实基础库；4只接线柱型号/封装待定。接口需重画，R6/R9/R12改0603；主电路标称值不变，模型/固件不改。

2026-11-08：[G题主板手绘分区与BOM（SMT基础库优先）](projects/2026-electronics-contest/g-buck/mainboard-v1/reports/manual-drawing-2026-11-08/README.md) · [Word/PDF/Excel资料包](projects/2026-electronics-contest/g-buck/mainboard-v1/downloads/GBUCK_Manual_BOM_BasicFirst.zip)。42件/123脚，基础库已核实14件，另4件候选；连接和标称值不变，新增推荐封装与选型，未改模型/固件。

2026-11-08：[G题主功率＋CC主板：六功能区已连线](projects/2026-electronics-contest/g-buck/mainboard-v1/README.md) · [嘉立创JSON资料包](projects/2026-electronics-contest/g-buck/mainboard-v1/downloads/GBUCK_Mainboard_Functional_Std.zip)。42件/123脚静态核对通过；减少两只板间插座，保留芯片与阻容参数；尚未绑定封装/设计PCB或实测。

2026-11-07：[G题V1.1 C14偏压与7V余量补充](projects/2026-electronics-contest/g-buck/modular-v1-1/reports/C14偏压与7V余量补充核对.md)。C14稳态偏压不等于5~7V输出；补充≥25V、优先0805选型约束，连接与标称值、71件数量不变，现有器件是否替换待核。

2026-11-07：[G题四板 V1.1 最简试改](projects/2026-electronics-contest/g-buck/modular-v1-1/README.md) · [审查核对](projects/2026-electronics-contest/g-buck/modular-v1-1/reports/审查核对与最简试改.md)。A板不加器件；B.C14改220nF，DAC参考/电流目标需按新配置校准。71件/261脚静态核对通过，环路/瞬时1A/效率与原生导入尚未验证。

2026-11-07：[G题四块独立板简化方案 Modular V1](projects/2026-electronics-contest/g-buck/modular-v1/README.md) · [嘉立创EDA完整资料包](projects/2026-electronics-contest/g-buck/modular-v1/downloads/G题_嘉立创EDA_四块独立板.zip)。四个独立标准版JSON、BOM/逐针表/预览；静态连接核对通过，未做原生导入/ERC/封装绑定/PCB或效率验证。新方案与旧Rev C.2不兼容；本次归档不改四板草案、旧硬件/固件/仿真。

2026-11-03：[G题Rev C.2 ADCFIX1 / A1诊断HEX与修正说明](projects/2026-electronics-contest/g-buck/rev-c2/firmware/docs/ADC采样修正与上板复测_2026-11-03.md) · [用户上板复测](projects/2026-electronics-contest/g-buck/rev-c2/reports/firmware-bringup-2026-11-03/README.md)。软件回归/ARM编译通过；用户照片确认A1运行、OFF/FAULT 0、VIN=14.865V，采样精度及保护/功率验收仍待完成。仍禁止功率输出；原理图/器件/BOM/PCB和仿真不改，旧诊断包仅留档。

| 项目 | 资料入口 | 当前结论 |
|---|---|---|
| 全球大学生物理竞赛（UPC） | [项目首页](projects/全球大学生物理竞赛/README.md) · [按上传原文重排LaTeX v17](projects/全球大学生物理竞赛/2026-A-一级火箭回收/v17/README.md) · [B题主模型](projects/全球大学生物理竞赛/2026-B-点球轨迹预测/v3/README.md) | 当前论文只据用户本次Word，22页、10图19表，保留原文模型和结果；不沿用旧140 t稿；原理图/器件/BOM/PCB/固件不改 |
| 2026 电子电赛 G题：辅助模块实物端口 | [XL7015_V2背面照片接线](projects/2026-electronics-contest/g-buck/rev-c2/reports/external-wiring-2026-11-01/XL7015_V2_背面照片接线.md) | 记录一块PCB丝印/四角端口，正面型号与两路分配待核；主板设计/PCB不改，外接模块差异单列 |
| 2026 电子电赛 G题：板外模块接线 | [三张接线图/PDF及外置电阻/开关、降压模块、STM32、LCD接线表](projects/2026-electronics-contest/g-buck/rev-c2/reports/external-wiring-2026-11-01/README.md) | 按当前接口整理，实物板版本与电源方向待核；仅文档，原理图/器件/PCB/仿真/固件不改 |
| 2026 电子电赛 G题：直插与功率件图 | [位置、极性、接线及PDF](projects/2026-electronics-contest/g-buck/rev-c2/reports/through-hole-power-placement-2026-11-01/README.md) | 覆盖22位号，区分外置R_PRE与板上件；仅图文，原理图/器件/PCB/仿真/固件不改 |
| 2026 电子电赛 G题：采样/比较/逻辑芯片图 | [位置、型号、1脚方向及PDF](projects/2026-electronics-contest/g-buck/rev-c2/reports/ic-placement-2026-10-31/README.md) | U2～U9共8只，80脚坐标/网络交叉核对；仅图文，原理图/器件/PCB/仿真/固件不改 |
| 2026 电子电赛 G题：二极管位置图 | [位置、方向、脚位及PDF](projects/2026-electronics-contest/g-buck/rev-c2/reports/diode-placement-2026-10-31/README.md) | 标出10只二极管，核对27焊盘；仅图文，原理图/器件/PCB/仿真/固件不改 |
| 2026 电子电赛 G题：电容位置图 | [总览、分区、PDF](projects/2026-electronics-contest/g-buck/rev-c2/reports/capacitor-placement-2026-10-31/README.md) | 标出33电容及容量/耐压/介质、电解极性；仅图文，原理图/器件/PCB/仿真/固件不改 |
| 2026 电子电赛 G题：电阻位置图 | [总览、分区、PDF](projects/2026-electronics-contest/g-buck/rev-c2/reports/resistor-placement-2026-10-31/README.md) | 按原生PCB核对120器件坐标，标出43电阻位号；仅图文，原理图/器件/PCB/仿真/固件不改 |
| 2026 电子电赛 G题：实物装配步骤 | [焊接、排线与首次调试](projects/2026-electronics-contest/g-buck/rev-c2/reports/实物装配与首次调试步骤.md) | 按Rev C.2和当前采购清单整理；原生ERC/DRC及实物验证待完成；仅文档，不改原理图/器件/PCB/仿真/固件 |
| 2026 电子电赛 G题：STM32固件起点 | [源码与操作](projects/2026-electronics-contest/g-buck/rev-c2/firmware/README.md) · [A1诊断包](projects/2026-electronics-contest/g-buck/rev-c2/downloads/GBUCK_RevC2_STM32_diagnostic_ADCFIX1_2026-11-03.zip) | 三配置ARM编译/主机逻辑测试通过；默认禁止功率输出，未上板/未整定；主板原理图/BOM与仿真不改，可选控制板按键待确认 |
| 2026 电子电赛 G题：器件逐项确认 | [记录](projects/2026-electronics-contest/g-buck/rev-c2/reports/component-confirmations-2026-10-27/README.md) | 1nF/50V/C0G/0805库存4只，单板用2只/补购0只/装一板余2只；1206/X7R款分开，原理图/PCB与仿真未改 |
| 2026 电子电赛 G题：Rev C.2 更新采购清单 | [Excel](projects/2026-electronics-contest/g-buck/rev-c2/downloads/GBUCK_RevC2_updated_BOM.xlsx) · [PDF](projects/2026-electronics-contest/g-buck/rev-c2/downloads/GBUCK_RevC2_updated_BOM.pdf) · [说明](projects/2026-electronics-contest/g-buck/rev-c2/reports/updated-bom-2026-10-27/README.md) | 120位号合并46项采购记录；商品图分别支持50mΩ P10/线径0.8、25mΩ P5/线径0.7，RS_L已从P10改P5；F1按5×20/P5.66更新，双夹15mm待试装；电气网络/2A额定保持，仿真未改 |
| 2026 电子电赛 G题：Rev C.2 PCB实物适配 | [工程/说明](projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/README.md) · [PCB预览](projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/previews/PCB_RevC2_120x90.png) | 当前768段铜线/188过孔/44地铜块，51网静态全连通；仅改PCB铜与局部走线，原理图/器件/BOM及位置保持；原生ERC/DRC和实物检查待完成，不能制板 |
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
