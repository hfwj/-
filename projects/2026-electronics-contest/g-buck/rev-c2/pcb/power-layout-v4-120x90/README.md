# Rev C.2 PCB v4：功率回路与 Kelvin 采样布局改版

**新附件局部核实：**[J_BYP外部清单对照](reports/J_BYP_外部清单核对_2026-10-28.md)。用户限定仅核第二项，新增报告只核J_BYP：附件未给外接开关额定；其PCB短路结论依赖椭圆解释，已复现，但与旧v3实际圆形导出存在分歧，须以v4原生DRC及新Gerber判定。其余附件条目未复核；工程/器件/BOM/PCB和仿真/固件未改。

本版用于替代已投产的 v3 进行新一轮打样。**PCB 已改版并通过静态复核；v4 原生 ERC/DRC、客户端 Gerber 与厂家生产稿仍待复验。**旧 v3 工程和导出包保持原样。

**器件核实补充：**[剩余器件与实装检查清单](../../reports/component-verification-2026-10-28/README.md)。当前BOM中的机械标记不能替代实物匹配/额定验收；F1两夹15mm、MOS本体/散热与C2/D_FREE空间等须在重新下单前核实。本次仅新增说明与证据，工程/BOM/ZIP及仿真/固件保持a1ff59a版本。

| 资料 | 文件 |
|---|---|
| 当前可编辑工程 | [GBUCK_RevC2_PowerLayout_v4_20261028.eprj2](native/GBUCK_RevC2_PowerLayout_v4_20261028.eprj2) |
| 整包下载 | [v4 复核资料 ZIP](../../downloads/GBUCK_RevC2_PowerLayout_v4_20261028.zip) |
| 总览与放大图 | [PNG](previews/PCB_RevC2_PowerLayout_v4.png) · [4页复核PDF](previews/PCB_RevC2_PowerLayout_v4_review.pdf) |
| 封装打印核对 | [1:1 PDF，100%打印](previews/Footprint_1to1_CHECK_ONLY.pdf) |
| 修改说明、边界和下单步骤 | [详细说明](reports/功率布局改版_v4_2026-10-28.md) |
| PCB BOM 与坐标 | [BOM/坐标 CSV](data/PCB_BOM_RevC2_PowerLayout_v4.csv) · [20项位置/角度变更](data/component_placement_changes.csv) |
| 验证证据 | [保存后复核](data/saved_native_validation.json) · [变更审计](data/layout_change_audit.json) · [独立工程回读与SHA256](data/isolated_import_audit.json) |

C2 改为靠近 QH/QL 的局部旁路；两端显式支路各约3.5 mm，无过孔。U4 移至 RS_L 右侧，Kelvin 两线各约7.934 mm，局部主干中心距0.5 mm，无过孔。重布受影响的功率、驱动、供电和测量支线，并重新生成静态地铜。120个位号已重新避让，增加9个IC的1脚标记以及电解正极和主要二极管K极标记。

保存后检查：120元件、325物理焊盘、51网连通，804段走线、209过孔、17块静态地铜；无悬空铜组、无静态铜间距违规，最小外网铜距约0.20004 mm。11项回归检查通过。这些检查不能代替原生 DRC 或开关瞬态/温升实测。

**修改影响：**比较 [v3 原生工程](../hardware-fit-120x90/native/GBUCK_RevC2_F1_slotfix_v3_20261028.eprj2)（SHA256 `1584597ad237e959d9a694e01f6ffeb77966021066d4344dd931222dbdcbd1ba`），原理图9页、引脚网络、器件数值/额定、封装及BOM用量不变；改变20项器件位置/角度、相关走线/过孔、地铜和丝印。无需因本版默认新增或替换物料。仿真、模型和固件未改或运行。

**重新下单：**独立打开工程 `GBUCK RevC2 功率布局优化 v4 20261028`，选择唯一的 `Rev C2 120x90 — 功率布局优化 v4`，先运行原生 ERC/DRC，再重新导出 Gerber 并核对生产稿。**不得沿用旧 v2/v3 Gerber 下单。**F1仍为0.9×1.5 mm槽孔，孔位/封装未改；需在新版实际导出中确认。过孔按v3相同的双面盖油属性保留，仍需检查新版阻焊导出。订单基础参数保持120×90 mm、FR-4、双层、1.6 mm、1 oz、单款单片。

**QL、U1、U4等朝向发生变化，按v4装配图与坐标表焊接，不照旧图装配。** F1两夹15 mm试装间距、实物封装、公差和散热适配仍需实装核对。
