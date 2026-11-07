# 2026 UPC A：量级分析与建模取舍 · v3

基于v1参数与v2假设，比较重力、几何、气动、推进、响应及末端精度；新增独立量级诊断，不是受控着陆求解器。

- [Word](reports/2026_UPC_A题_量级分析与建模取舍.docx) · [PDF](reports/2026_UPC_A题_量级分析与建模取舍.pdf) · [在线阅读](reports/量级分析与建模取舍.md)
- [量级汇总JSON](results/data/scale_summary.json) · [取舍表CSV](results/data/model_tradeoffs.csv)
- [真空诊断表](results/data/vacuum_ballistic_diagnostics.csv) · [冻结速度大气表](results/data/frozen_speed_atmosphere.csv)
- [火箭方程参照](results/data/rocket_equation_reference.csv) · [定质量制动参照](results/data/terminal_thrust_stopping_reference.csv)
- [运行方法](simulation/README.md) · [守恒与加密检查](results/logs/numerical_checks.json) · [来源](references/README.md)
- [资料包](downloads/UPC_2026_A_v3_量级分析与建模取舍.zip)

主要结论：重力势能约为初始动能49%；70 km初始阻力仅约0.177%干态重力，但全程不可据此删除气动；变质量/有限响应必须保留。γ₀=0°真空航程约205 km，应保留地球曲率。无自转/无风仅作参考，不能直接支持5 m落点目标。脚端转动速度约0.284 m/s已占水平容差57%，姿态与接触需独立核查。

冻结速度表不是飞行轨迹；真空弧线没有大气、推力或自转；火箭方程中的Δv_T是人为参照，不是本题所需推进剂，也不是严格需求上下界。130 t只作干态极限，实际有燃料的制动质量更大。所有归一化风/力矩/惯量例子均有H输入。

相对基线`894029b`：新增v3诊断代码、数据与文档，v1/v2/B题保留；未实现着陆优化或给燃料答案。原理图、器件/BOM、PCB、固件与既有电子工程仿真模型均未修改。
