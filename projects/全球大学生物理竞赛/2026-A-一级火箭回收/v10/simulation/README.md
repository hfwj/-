# 姿态/安全诊断复现

```bash
cd simulation
pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python attitude_safety.py
python build_report.py
```

Python3.12，NumPy≥2（使用trapezoid）。运行环境见../results/logs/environment.json。Word转PDF需LibreOffice与中文字体。

attitude_safety.py执行171个倾角的脚/主筒间隙解析式核对、100组脚速度有限差分、连续脚接触根、倒置主筒先碰及球面线段内部碰撞反例，再做δ_max=3/5/10/15/20/25/30°的瞬时角度必要条件扫描、脚端速度/支腿吸能/关机尾部量级计算。25°样本相容不等于连续M1可行。

没有实现M1刚体控制、真实力矩/质量特性、闭环纠偏或接触后2s仿真；没有据此标记完整安全通过。geometry/feet_velocity可复用为后续几何模块，实际突出物/变形/船体仍需补齐。

整包包含本诊断所需的4个历史输入，保留同级v4/v8/v9路径：v4的safety_criteria.csv、v8的controls_N320.npz和replay_summary.json、v9的independent_trajectory.csv；不是这些历史版本的整包。完整版本见仓库。

相对e61fbde，只新增本版诊断/文档，不改历史模型/输入，不改原理图、器件/BOM/PCB、固件及旧电子模型。
