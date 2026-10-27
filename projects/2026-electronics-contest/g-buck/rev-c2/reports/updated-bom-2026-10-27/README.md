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

优先处理：U1必须IR2184PbF而非直接使用IR2104；补齐RS_L的25mΩ/1%/≥1W分流电阻；100nF电容共16只，4.7nF共5只；含472的料号不能代100nF。分流器脚距、双管夹装配位置、C_A3与D1实物封装等仍待确认。

比较基准为当前PCB复核版（e4559eb）。本次仅新增采购清单及索引：**不修改原理图、PCB、器件参数、封装、仿真模型或固件。** 表中明确标注的统一采购额定/介质/精度为建议，原始工程值另列保留；不等于已更换实际物料。既有PCB仍未完成布线及原生ERC/DRC，本清单不构成制造放行。

复现：安装`openpyxl`、`reportlab`、`cryptography`，在仓库目录运行：

```bash
python projects/2026-electronics-contest/g-buck/rev-c2/schematic/tools/export_updated_bom.py
```
