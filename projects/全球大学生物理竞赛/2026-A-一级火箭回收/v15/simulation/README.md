# γ0=+45°实际计算复现

Python3.12.14，CasADi3.7.2（自带IPOPT）、NumPy2.3.5、SciPy1.17.0、Matplotlib；生成Word/PDF还需python-docx、pandoc、LibreOffice和Noto CJK字体。请逐个运行优化器：本环境cgroup内存上限8 GiB，一次60区间求解约需5 GiB，并行会被OOM终止。独立回放不需要重跑昂贵优化。

在v15目录执行：

```bash
MPLCONFIGDIR=/tmp/upc_matplotlib OPENBLAS_NUM_THREADS=1 python simulation/analyze45.py results/data/optimized_controls.npz
OPENBLAS_NUM_THREADS=1 python simulation/verify.py
python simulation/build_report45.py
python simulation/export_report45.py
```

最终候选重新求解（严格按同一260 s分支）：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python simulation/solve45.py --nodes 60 --propellant 140 --ignition 260 --max-iter 1000 --warm results/data/final140_coast160.npz --output results/data/recomputed_140t.npz
```

使用新结果绘图需把analyze45.py的参数改为新NPZ路径，并重新验收，不能只看IPOPT返回。

`--free-mass`连续优化初始质量；`--opt-ignition`额外将第一次点火作为230–300 s决策量，可能走到较差局部分支。scan45.py显式保留原5°/s节点设置；最终求解器默认4.5°/s余量、验收仍5°/s。scan45.py记录90–130 t的30区间、90迭代预算搜索，均不能作为全局不可行证明。自由质量目标带1e−5控制正则，固定装载目标为0.01×耗剂吨数加同一正则；没有全局最优保证。

solve45.py是最终160节点滑行版本；solve7.py仅保存本次最初40节点滑行基准，已同样改为+45°、Isp330 s和扩展密度，禁止误认为旧水平分离求解器。其他free45*.npz仅为局部搜索记录，不是完整安全通过结果；最终使用optimized_controls.npz，来自final140_rate_margin.npz；final140_coast160.npz虽求解返回，但连续速率检查超5°/s，被拒绝，只可作暖启动。

replay.py是独立SI地心笛卡尔动力学，不调用CasADi RHS。名义积分允许计划后最多0.05 s数值接触根括定；扰动严格在原计划终止时刻停止，不延长末端控制。接触是脚端海平面零事件，再检查固定船甲板覆盖。并不包含接触后支腿运动。

Cd=0.5及其面积律、CP、惯量等均为H；没有伪造附件所述12锚点Cd(M)或原tools脚本。源附件及新旧修改对照完整保留。本次模型变更不涉及原理图、器件/BOM、PCB、固件或真实硬件验证。
