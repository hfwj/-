# v15：γ0=+45°七机两次点火 CasADi/IPOPT 重算

依据用户上传《回收仿真_七机两段点火.docx》重建可审计参考模型。附件已经写+45°；本次实际重算并修正公式、模型及证据口径。

- [修订Word](reports/回收仿真_七机两段点火_γ45_CasADi修订.docx) · [PDF](reports/回收仿真_七机两段点火_γ45_CasADi修订.pdf) · [Markdown](reports/回收仿真_七机两段点火_γ45_CasADi修订.md)
- **文末第12节列16项修改对照**：[机器可读记录](results/data/document_modifications.json)
- [全部代码、数据与文档ZIP](downloads/UPC_A_gamma45_CasADi.zip) · [四类曲线](results/figures/01_four_main_curves.png)
- [复现方法](simulation/README.md) · [最终名义检查](results/data/metrics.json) · [程序验证](results/data/verification.json) · [固定控制扰动](results/data/fixed_control_perturbations.csv)
- [原稿存档](references/回收仿真_七机两段点火_原稿.docx)

最终140 t名义候选：先向上到144.782 km，再回落；260 s七机点火、315.636 s三机重启、364.203 s首次脚端触地，射程347.624 km。两次耗剂98.308 t与38.942 t，剩余2.750 t。峰值动压47.018 kPa，推力惯性方向变化率最大4.613°/s。

**边界**：Cd(M)原12锚点未提供，本次明确改为Cd0.5；点火后二维俯仰联立，点火前翻转理想化；H类风、气动矩和惯量；不含真实三维/热结构/接触后验证。原稿96/102/104 t下限与110/120 t鲁棒结论未沿用。90–130 t有限局部搜索失败不是物理不可行证明；140 t不是数学最小或鲁棒推荐。第一段与原稿的高度范围也不同，不能直接逐段比较耗剂。

最终控制为optimized_controls.npz（来自final140_rate_margin.npz）。此前coast160候选连续方向速率约5.13°/s，被拒绝，仅作暖启动/审计，禁止混作最终通过结果。所有最终图文、扰动和验证由速率余量修订后的控制生成。

比较基线为本次上传文档。模型、控制等效、环境与求解/回放改变；原理图、器件/BOM、PCB、固件无变化，不由此验证真实硬件。
