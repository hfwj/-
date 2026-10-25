# 嘉立创 EDA · G题 Rev B · 120×90 mm 首轮布局

新增独立 Rev B 板页，7 页可编辑原理图与主板完整器件/网络关联，原 GitHub 两版板页保留。**PCB 尚未布线；未完成客户端打开验证或原生 ERC/DRC，不能用于制板。**

- [原生工程](native/G题同步Buck_RevB_120x90_布局草稿.eprj2)
- [整包下载](../../downloads/嘉立创EDA_G题RevB_120x90_首轮布局_2026-10-25.zip)
- [PCB 布局预览](previews/RevB_PCB布局预览.png) · [原理图预览 PDF](previews/RevB_原理图预览_7页.pdf)
- [BOM](data/RevB_BOM_96项.csv) · [引脚表](data/RevB_引脚网络表.csv) · [核对结果](data/RevB_逐引脚核对.json)
- **[使用说明、修改影响和封装待确认项](使用说明与修改影响.md)**

相对用户 PDF，96 个器件、43 个网络、264 个已连接引脚逐项一致，14 个 NC 保持悬空；本轮没有主动改变 PDF 的拓扑、数值或脚号。相对 GitHub 原设计，新增符合 Rev B 的驱动、采样、保护、锁存和接口，包含实际器件/BOM/PCB 变动；通用封装、机械尺寸和散热仍需确认。原仿真模型与固件没有修改，未执行动态仿真。详细比较基准及验证边界见上方说明。

## 静态复核

Python 3.10+ 与 `cryptography`：

```bash
python tools/verify_native.py --report work/readback.json
```

此命令只读原生工程，按符号物理引脚坐标和连线恢复连接，再与 PDF 基准比对；检查 PCB 焊盘编号、网络、重叠和板框边界。它不运行嘉立创 EDA ERC/DRC。可加 `--original /path/to/original.eprj2`，验证原 GitHub 板页设计对象未改变（来源文件固定提交和 SHA-256 见使用说明）。

预览按原生设计记录绘制，不是嘉立创 EDA 截图或客户端导出。`SHA256SUMS.txt` 针对整包内的平铺文件名。
