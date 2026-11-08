# 2026 A · v13：七发动机、两次点火、风中回收算例

本次实际运行：90 t起按10 t递增搜索，140 t找到本策略下首个经独立正向积分检查的名义可行候选；前五组未在有限局部搜索预算内找到严格解，不是物理不可行证明，也不是最低燃料证明。

- [中文分析 PDF](reports/七发动机两次点火回收_模拟分析.pdf) · [可编辑 Word](reports/七发动机两次点火回收_模拟分析.docx) · [Markdown](reports/七发动机两次点火回收_模拟分析.md)
- [四类主曲线合图](results/figures/00_requested_four_plots.png) · [姿态与推力](results/figures/05_attitude_thrust.png) · [阶段轨迹](results/figures/07_nominal_phases.png)
- [全部图片 PNG/PDF](downloads/UPC_A_v13_figures.zip) · [代码、数据与报告完整包](downloads/UPC_A_v13_complete.zip)
- [复现说明](simulation/README.md) · [实际参数表](results/data/parameter_table.csv) · [来源及适用范围](references/source_catalog.json)
- [名义检查](results/data/metrics.json) · [独立实现验证](results/data/verification.json) · [扫描诊断](results/data/mass_scan_diagnostics.csv)

初始推进剂140 t=液氧108.182 t+甲烷31.818 t；总质量270 t。65 s启用七机，再入燃烧（含关机尾流）耗剂84.086 t；120.411 s启用三机，至首次脚端接触耗剂51.583 t。约183.142 s、下游190.298 km触地，竖直速度约-0.999 m/s，剩余4.331 t。

最大动压47.021 kPa，非重力力幅值和上界3.8003。参考单机1 MN、稳态节流0.3–1.1、比冲320 s均为H类虚拟模型，受2019年CNES历史方案启发，不代表真实发动机在各高度的性能。

**边界**：二维平动/俯仰；用户要求的分离至再入点火前翻转理想化；假设风而非实测天气；未验证三维侧风/闭环/热与结构/接触后停稳。灰色早段姿态仅为参考。低装载量图中虚线沿用140 t控制，不能当作其各自最优解。rejected_140t_controls.npz是被拒绝的初次方案，禁止混作最终结果；最终为optimized_controls.npz。

**修改影响（相对v12）**：只新增v13物理模型、发动机控制等效、求解、独立回放与图文；原理图、器件/BOM、PCB、固件均无修改，不验证真实硬件。旧版文件保留。
