# Rev C2 更新物料清单

按当前120×90mm PCB复核工程整理，每套用量。包括 **46项合并采购行、120个逐位号明细、12项外接模块/配套辅料记录**。已从交付原生工程回读核对全部位号、原始参数和封装；不把旧Rev B参数表当作最新版BOM。

| 文件 | 入口 |
|---|---|
| Excel，含库存填写与补购数量计算 | [GBUCK_RevC2_updated_BOM.xlsx](../../downloads/GBUCK_RevC2_updated_BOM.xlsx) |
| PDF阅读版 | [GBUCK_RevC2_updated_BOM.pdf](../../downloads/GBUCK_RevC2_updated_BOM.pdf) |
| 在线阅读完整清单 | [物料清单.md](物料清单.md) |
| CSV：合并采购 | [purchase_grouped.csv](../../results/data/bom-2026-10-27/purchase_grouped.csv) |
| CSV：120项逐位号 | [bom_by_reference_120.csv](../../results/data/bom-2026-10-27/bom_by_reference_120.csv) |
| CSV：外接模块与辅料 | [external_modules_and_accessories.csv](../../results/data/bom-2026-10-27/external_modules_and_accessories.csv) |
| 数量及原生回读验证 | [verification.json](../../results/data/bom-2026-10-27/verification.json) |

Excel含5张工作表：使用说明、采购汇总、逐位号120项、外接模块与辅料、重点变化与待确认。采购汇总 **G列填写现有可用库存，H列自动计算需补购数量**；库存留空表示未核实，不等于尚未购买。CSV没有自动计算功能。

120个逻辑位号中含14个裸测试焊盘和2个DNP预留，默认有料位号为104，包含外置R_PRE。管夹、模块、外置开关和线束另列，不重复计R_PRE，不把J_BYP端子当成已经包含开关。

用户确认中途补料为B3/Rev B那批，补购应扣除已有库存。RS_L的25mΩ已包含在B3清单中，旧参数表记未购，当前是否到货待核，Excel不再自动填写库存0。U1仍要求IR2184PbF；100nF共16只，4.7nF共5只，含472的料号不能代100nF。

新50mΩ商品图已支持RS_IN/OUT的P10、线径0.8mm、图示体高12mm和标称5A，清单与工程同步专用M型封装关联；既有孔位、位置与走线几何保持。精度、连续功率、平面厚度及RS_L实际尺寸仍待确认。

后续25mΩ商品图现已确认RS_L采用U型P5、图示线径0.7mm、体高7mm，专用封装与采购表已同步；原P10孔位已改为P5，两孔各向中心移动2.5mm。原25mΩ值、电气网络、器件中心及其他器件保持。实际焊脚径、平面厚度、精度/功率与库存仍待核。

采购表最初以e4559eb建立；50mΩ补充比较基准523113a，25mΩ补充比较基准9de6ebe。**电气网络与器件值保持；RS_L有P10→P5孔位/焊盘位置变化，须使用更新工程。仿真/固件未修改或运行。** 表中标注的统一采购额定/介质/精度为建议，原始值另列保留。既有PCB仍未完成布线及原生ERC/DRC，本清单不构成制造放行。

最新保险管确认（比较6135e14）：F1采用5×20mm、2A快断，商品标250V；5×20夹黄铜镀镍、脚宽1.1mm、厚0.5mm，用户确认5.66mm是两脚中心距。当前四槽改为0.9×1.5mm设计尺寸，两夹15mm中心距是试装初值，需实物核对。旧6×30/7.7采购与封装参考作废。网络、2A额定和其他器件保持，仿真/固件未改。

最新二极管确认（比较6f9da6a）：用户明确D1和D_FREE均为“SR560贴片”。采购表按两只贴片记录，完整厂家料号、SMA/SMB/SMC类别和尺寸待核；原工程SS56/SMB仅保留占位，不作为兼容性确认。已撤回尚未提交的DO-201AD轴向改版，PCB与6f9da6a逐字节一致；仿真/固件未改。同时记录电感采用立式，与现布局一致。详见[确认记录](../component-confirmations-2026-10-27/README.md)。

复现：安装`openpyxl`、`reportlab`、`cryptography`，在仓库目录运行：

```bash
python projects/2026-electronics-contest/g-buck/rev-c2/schematic/tools/export_updated_bom.py
```
