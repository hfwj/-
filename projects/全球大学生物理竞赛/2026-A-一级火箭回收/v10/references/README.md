# 依据与待补参数

- ../../v4/results/data/model_assumptions.csv 和 safety_criteria.csv：沿用H几何、发动机族与18类/19条判据。
- ../../v8/results/data/controls_N320.npz 和 replay_summary.json：原始名义候选，未修改。
- ../../v9/results/data/independent_trajectory.csv：经独立验证的轨迹，用于角度必要条件诊断；v9扰动结论仅针对固定开环。
- parameter_requirements.csv：区分H代理与U待证数据。无真实TVC/RCS/支腿/热防护能力的新证据，扫描值不能冒充额定值。
- 刚体力矩、脚端速度和接触几何为第一性推导；间隙/速度/连续根及球面线段漏检反例以可执行检查核对，不称为真实M1或接触仿真。
