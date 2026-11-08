# 复现（Python 3.12）

模型：非旋转球形地球、USSA1976、给定二维风、变质量平动和点火后俯仰；不是六自由度飞行软件。目录中的NPZ含可直接回放的实际优化控制，不必先运行昂贵求解。

在v13目录执行，安装requirements.txt；绘图需Noto CJK字体（Debian/Ubuntu: fonts-noto-cjk）。报告导出还需pandoc与LibreOffice。优化器可能使用数GB内存，120区间重优化本次未完成。

```bash
python -m pip install -r simulation/requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/upc_matplotlib python simulation/analyze.py results/data/optimized_controls.npz
OPENBLAS_NUM_THREADS=1 python simulation/verify.py
MPLCONFIGDIR=/tmp/upc_matplotlib python simulation/extra_outputs.py
python simulation/build_report.py
```

重新求解140 t（与已保存结果可能落入不同局部极值，应重新检查）：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python simulation/solve7.py --nodes 60 --propellant 140 --max-iter 700 --warm results/data/optimized_controls.npz --output results/data/new_controls.npz
```

低质量搜索预算复现：`python simulation/scan_low.py`，每质量30区间、90次迭代，原暖启动在warm_continuous_candidate.npz；脚本显式传入low_tilt_deg=5.0以保留原始低质量搜索条件；最终140 t求解器默认3.5°余量条件。局部求解路径仍会随平台改变。固定控制诊断并非各质量优化结果。

analyze.py独立SI笛卡尔回放不调用CasADi动力学。verify.py仅为导数一致性比较而同时导入两实现；比较80组随机状态及执行器界限。关机尾推力计入耗剂。脚端事件与固定预置船几何另检查。

原理图/器件/BOM/PCB/固件不变；相对v12仅新增物理/控制等效、参数、数值求解和图文。不能据此验证真实硬件。
