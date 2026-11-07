# 审计依据

- 输入基线：d60ee2d3bdc925b0f0624b4adbacc54861131a89，../../v8。控制results/data/controls_N320.npz、controls_N160.npz与标准大气/方程；不修改原版本。
- 安全规范：../../v4/results/data/model_assumptions.csv 与 safety_criteria.csv，保留所有H/U属性。
- 六个舍入密度锚点采用标准大气位势高度0/11/20/32/47/51 km的教材级值，只核对实现数量级和层次，不作为额外天气观测。
- v9/simulation/audit.py独立实现SI制极坐标、大气与调度；不导入v8的回放/RHS。checks.py为专门的坐标交叉核对而导入v8求解器RHS，不参与独立回放。
- 姿态偏转需求是给定推力轨迹下的几何必要条件，未知实际发动机/执行器能力，不伪装为实测限制。
