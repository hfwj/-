# 用户手工工程 V3 补丁

输入基准保存在 `../../../references/user-projects/2026-10-27_GBUCK_REVC_DRIVER_手工搭建基准.ms14`，输出为 `../../../downloads/GBUCK_REVC_DRIVER_30k.ms14`（路径相对于本脚本目录的 Rev C 根目录，请以脚本常量为准）。

需要 Python 3、`dclimplode`、`lxml`，以及可选的 ngspice 44.2：

```sh
python3 patch_driver_30khz.py /path/to/ngspice
```

脚本仅替换 V3 两份保存模板中的载波行及 VIN 引用行；用精确逆变换、原件哈希、静态指纹和双解码器检查保留其余数据。提供 ngspice 路径时，另外运行固定占空比的 PWM 子级检查。测试用 `.spiceinit` 只启用 ngspice 的 PSpice 兼容模式，不更改原生工程。

原理图连接、参数、布局及器件/BOM/PCB不变；仿真控制模型的实际载波和 VIN 引用发生变化。比较基准、具体差异及验证限制见 [修改记录](../../../reports/2026-10-27_手工工程_V3_30kHz补丁.md)。不能据此声称完整 Multisim 工程或硬件已验证。
