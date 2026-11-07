# 正向物理主模型 · v3

输入初始位置、速度、**真实自旋向量**及气动参数，输出三维轨迹和首次穿门/触地事件。本目录没有优化器、参数反演、观测同化或预测概率估计。

## 运行

已在 Python 3.12、NumPy 2.3.5、SciPy 1.17.0、Matplotlib 3.10.8 下执行。进入本目录：

```bash
python -m pip install -r requirements.txt
python verify_physics.py
python run_forward.py
```

更改 [configs/forward_examples.json](configs/forward_examples.json) 中的已知输入后运行：

```bash
python run_forward.py --config configs/forward_examples.json --output ../results
```

`base` 为共同参数，各 `case.overrides` 递归覆盖；结果中保存完整展开后的输入。示例的初速度、自旋、升力斜率、阻力、风及OU参数均是手工设定，未拟合题目数据。程序不读取两次观测来更新参数。

## 物理接口

`physics_model.py` 提供 `Ball`、`Air`、`DragLaw`、`LiftLaw`、`Aerodynamics`、`InitialState`、`Goal`、`SolverSettings`、`simulate`。

- 状态9维：球心位置3维、速度3维、真实自旋3维；不含球缝姿态，所以不称为完整姿态耦合6-DOF模型。
- 重力、可关闭的浮力；空气动力使用球相对恒定风场的速度。
- 阻力为非负常数系数或用户提供的 `Re → Cd` 表；表要求严格递增的Re和非负Cd。超出表域时夹到端点，摘要标记 `drag_table_outside_range_clamped=true`，不视为已验证外推。
- 升力采用 `Cl = spin_slope * S_perp`，或可选 `Cl = Cl_max*tanh(spin_slope*S_perp/Cl_max)`。两者都属于需要校准的经验闭合。
- `S_perp = R*|omega × u|/|u|²`；升力沿 `omega × u`。零自旋、平行自旋或零相对速度不除零。
- 线性升力律严格化简为 `a_M = rho*A*spin_slope*R/(2m) * (omega × u)`；不再额外乘速度比。
- 可选自旋衰减 `domega/dt = -spin_decay_per_s*omega`；薄球壳惯量仅用于输出等效阻尼力矩，自旋衰减率由输入规定。

## 可选 OU 侧向残差

`make_ou_path` 按指定相关时间、3×3半正定协方差和随机种子产生潜在加速度 `b(t)`；实际附加力为 `m*(I-u_hat*u_hat.T)*b`。`initial_m_s2=null` 表示从稳态分布抽初值，给三维向量表示指定初值。

协方差单位是 `(m/s²)²`，不是位置测量误差。OU节点使用精确转移，节点间线性插值，再与运动方程积分耦合；不宣称整套SDE被精确积分。已用同一组细网格随机节点检查耦合网格细化。有限相关时间下，该侧向力通过普通 `dt` 积分进入速度方程；未将其替换为直接作用在速度上的白噪声。

示例只输出一条指定种子的路径，不是后验预测或95%预测区域。

## 事件与输出

- `goal_plane`：首次向前穿过 `x=11`；计算球心是否落在题目矩形内。
- `ground_contact`：球心下降至 `z=R`，随即终止；未建模反弹或滚动，不据此直接断言最终一定未进门。
- `time_limit`：达到设置的最长时间，尚未发生上述事件。
- `Trajectory.sample_at(times)`：只允许在已积分时间范围内取样，禁止跨越终止事件外推。

`ball_clearance_margin_at_center_plane_m` 仅为球心到门框边界的平面余量减半径，不是圆柱门柱碰撞仿真，也不是“整球已越线”的裁判判定。

CSV含每个时刻的位置、速度、真实自旋、各项力和Re/Cd/Cl；JSON记录事件及完整输入。负/非有限参数、不合法气动表和协方差会被拒绝。

## 已执行验证与范围

`verify_physics.py` 的15项检查涵盖抛体解析解、浮力、零相对流、线性Magnus化简及横向正交性、饱和上界、相对风和耗散、自旋衰减、反射对称、无风水平直线、机械能、事件、参数输入、确定性步长、OU矩和相关性、OU耦合网格细化。

这证明基本方程实现与相应数学性质一致，不证明某组气动参数符合真实比赛足球。球缝朝向、变形、反弹、纵向随机阻力及高雷诺数非定常闭合尚未标定/实现。
