# 校验与预览工具

在完整仓库中运行；工具使用相邻 `hardware-fit-120x90/tools` 的原生读取和几何工具，不是嘉立创原生 ERC/DRC。仅下载资料包并用EDA打开工程不需要运行Python。

安装相邻目录的 `requirements.txt` 依赖后，从仓库根目录执行：

```bash
python projects/2026-electronics-contest/g-buck/rev-c2/pcb/power-layout-v4-120x90/tools/verify_v4.py
python projects/2026-electronics-contest/g-buck/rev-c2/pcb/power-layout-v4-120x90/tools/render_v4.py
```

`verify_v4.py`只回读交付v4并写校验JSON，不改工程。`render_v4.py`生成原生记录的近似预览，非客户端截图。不要用历史 `build_pcb.py` 或分阶段旧布线脚本覆盖当前工程。
