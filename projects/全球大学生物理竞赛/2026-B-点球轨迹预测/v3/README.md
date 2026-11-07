# 2026 UPC B题 · v3 正向物理主模型

输入已知初始状态和参数，计算三维飞行轨迹。此次实现物理正演，不进行参数反推、观测同化或预测概率估计。

## 文档与入口

- [物理方程与使用说明 · 在线阅读](reports/物理主动力模型_方程与使用说明.md)
- [Word](reports/2026_UPC_B题_物理主动力模型.docx) · [PDF](reports/2026_UPC_B题_物理主动力模型.pdf)
- [代码运行说明](simulation/README.md) · [物理核心](simulation/physics_model.py) · [输入配置](simulation/configs/forward_examples.json)
- [示例结果](results/data/forward_summary.json) · [15项验证日志](results/logs/physics_validation.json)
- [轨迹图](results/figures/forward_trajectories.png) · [受力分解图](results/figures/force_budget.png)
- [完整模型与文档资料包](downloads/UPC_2026_B_v3_正向物理模型.zip)

## 已实现

重力、可选浮力、相对风阻力、真实自旋马格努斯力、自旋衰减；非负常数/查表阻力、线性/饱和自旋升力；可选指定随机种子的OU横向残差；首次向前穿门、触地和时间上限事件。

马格努斯项采用一致的升力系数定义，线性 `Cl ∝ S_perp` 时化简成 `a_M = K*(omega × u)`，不重复乘速度。实际自旋与v1有效旋转参数明确区分。

## 当前结果的性质

7个演示工况均由手工参数生成。抛体、气动、风和OU示例用于检查模型行为，不是题目两次观测的反演解。单条OU轨迹不是预测区域；尚未得到本模型的“最可能入门点”。

15项解析/数值检查通过；真实气动参数、实测轨迹、概率校准及完整碰撞仍待后续工作。v1的已给代表解、v2的选型文档保留不变。

## 影响说明

比较基线：提交 `c30f693` 的v1示例代码和v2方案文档。此次新增独立v3正向模型、验证和使用文档。

- 原理图影响：无，未修改连接、拓扑、引脚或元件值。
- 器件/BOM/PCB/固件影响：无。
- 仿真/模型影响：仅新增足球物理正演及可选OU驱动；未修改既有电子工程模型或v1代码。
