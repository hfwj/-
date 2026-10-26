# 电子设计与仿真资料

按项目、版本和资料类型归档，报告、仿真源代码及验证数据一起保存。

## 项目目录

| 项目 | 资料入口 | 当前结论 |
|---|---|---|
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
