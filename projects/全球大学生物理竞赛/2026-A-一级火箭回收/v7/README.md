# A题v7：少量下降策略比较

[比较报告](reports/少量下降策略比较.md) · [完整结果](results/data/comparison.json) · [代码](simulation/compare.py)

在simulation目录运行`python compare.py`，需要numpy、scipy；forward.py和atmosphere_1976.py需置于同目录。窗口形式为(指令起点秒,持续秒)，不是起止时刻。固定初始推进剂70 t，比较无推力、60 s连续40 s、85 s连续40 s、60 s/110 s分别20 s。采用同一理想逆速度推力方向，仍不是完整姿态/着陆控制模型。结果不能当作所需最小燃料或安全着陆证明。

本版增加多时窗接口，旧v6不改。相对c42a52c，原理图、器件/BOM、PCB、固件和旧电子工程模型不变。
