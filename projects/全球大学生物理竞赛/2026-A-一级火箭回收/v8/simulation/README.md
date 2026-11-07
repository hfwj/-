# 复现

Python 3.12；依赖见requirements.txt。本次版本见../results/logs/environment.json。首次求解可能需数分钟。

```bash
cd simulation
pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python solve_candidate.py --ignition 40 --nodes 80 160 320
python verify.py
python build_report.py
```

只核查交付候选可跳过优化直接运行verify.py。该命令用独立SI Cartesian DOP853回放160/320区间，检查动压、力预算、参考末端速度、质量守恒、余量、节流及推力方向速率，并输出verification.json。完整v4仍NOT_VERIFIED；事件是质心高度32.5 m，不是真实脚端接触。

改变--ignition时请复制目录保存独立结果，避免覆盖最终候选。初次点火固定于每次外层比较，未求连续最优初次点火时刻；连续变量试验未收敛，不作为结果。5 s为关机指令至两台重新点火指令的间隔。所有节流方向节点保存在npz，不能仅按时刻表复现。

solve_candidate.py/physics.py使用km、km/s、t、MN；replay_candidate.py独立使用m、m/s、kg、N与旧版标准大气表。图/Word由build_report.py生成；Word转PDF需LibreOffice。

相对5e0f819，仅新增火箭优化模型与资料；原理图、物理器件/BOM/PCB、固件、旧电子仿真不改。
