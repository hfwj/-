# 验证复现

在完整仓库中运行，需保留相邻v8，不复制覆盖历史版本。Python3.12，依赖numpy/scipy/casadi/python-docx。

```bash
cd simulation
pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python checks.py
OPENBLAS_NUM_THREADS=1 python audit.py
OPENBLAS_NUM_THREADS=1 python crosscheck.py
python summarize.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduce.py --optimizer
python build_report.py
```

原优化器复跑约2分钟；去掉`--optimizer`可只复跑旧验收与负例。`audit.py --quick`仅名义独立回放，不产生完整扰动audit.json；完整报告需正常运行。所有检查在普通Python执行，不使用`python -O`，因为-O会关闭assert。

各程序作用：audit独立SI极坐标、分层大气、实际节流回放与有效指令响应ODE；checks验证随机坐标转换、真空守恒、火箭方程/二次阻力解析极限、4种负例与v8历史哈希；crosscheck另用RK45复核3个扰动；reproduce在临时复制的v8中运行原verify，不修改历史输入，再按选项求解320区间；summarize提取姿态必要条件/敏感性表。

`M0_subset_pass`只对既定拓扑和已经实现的约束有效，不包括刚体/万向节、脚端包络、甲板覆盖、热结构和接触后稳定性。9个扰动不含闭环/重优化，不是随机样本，不报告概率。扰动回放止于首次参考接触、可用燃料耗尽或原计划终时；不延长最后控制节点。大气公式显式允许至71 km位势高度，另检查v8声明的0–70 km几何域；不静默截断高度。

整包包含验证所需的v8文件，按目录层次解压即可（不重复嵌套v8下载ZIP）。若单独拷贝v9目录，则需保留仓库v8至同级目录。Word转PDF需LibreOffice。相对d60ee2d，仅新增审计代码与报告，旧v8输入/控制与硬件、BOM/PCB/固件、旧电子模型不改。
