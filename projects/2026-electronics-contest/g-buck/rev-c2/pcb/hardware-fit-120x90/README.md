# Rev C.2 PCB：按实购物料修订封装与布局

以用户最新上传的《G题同步Buck完整原理图_RevC2.pdf》及仓库同版原生工程为电气基准，建立 **120×90 mm 双层 PCB 复核副本**。原 Rev C.2 原理图文件、Rev B PCB 和 GitHub 参考板保留。

**当前是可编辑的封装/布局及局部布线复核版。主功率布线、Kelvin 取样布线、地平面和客户端 ERC/DRC 尚未完成，不能直接制板。**

| 内容 | 入口 |
|---|---|
| 整包下载 | [PCB复核资料包](../../downloads/GBUCK_RevC2_PCB_review_2026-10-27.zip) |
| 嘉立创 EDA 专业版可编辑工程 | [GBUCK_RevC2_120x90_PCB_review.eprj2](native/GBUCK_RevC2_120x90_PCB_review.eprj2) |
| 实际工程记录绘制的 PCB 总览 | [PNG](previews/PCB_RevC2_120x90.png) · [总览与局部 PDF](previews/PCB_RevC2_review.pdf) |
| 封装核对打印页，必须按 100% 打印 | [1:1 核对 PDF](previews/Footprint_1to1_CHECK_ONLY.pdf) |
| 修改、接线、依据及未完成项 | [详细说明](PCB修改说明与待确认项.md) · [PDF](PCB修改说明与待确认项.pdf) · [Word](PCB修改说明与待确认项.docx) |
| PCB BOM 和坐标 | [CSV](data/PCB_BOM_RevC2.csv) |
| 保存后原生工程回读 | [验证 JSON](data/verification.json) · [逐焊盘 CSV](data/PCB_pin_readback.csv) |
| 局部走线与未布网络 | [局部连接](data/local_routing.json) · [未布网络](data/unrouted_networks.json) |

## 本轮变动

- 同步 Rev C.2 的全部 120 项器件及 51 个网络，保留 J_MON.1→PA6、LCD SCK→PA5，以及 IR2184 驱动和原保护门限。
- J1/J2/J_BYP/J_MON 改为图片中的 2.54 mm 端子；C1/C3 按直径 10 mm、脚距 5 mm 重建；C2/C4/C6 改按实购 0805。
- L1 改为 65125 立式 20×10 mm 投影、脚距 10 mm。F1 改为 6×30 mm 管夹占位，单夹脚距 7.7 mm；两夹间距仍待实装核对。
- 分流电阻改为直插占位，撤销已购件采用 2512 贴片的假设。**P10 仍是假设；参数表的“长10”没有被认定为已测脚距。**
- 重新安排功率、驱动、采样和控制器件；采样芯片靠近分流器。补充部分栅极、去耦与 ADC 局部走线。完整布线状态由验证 JSON 如实记录。

## 修改影响

比较基准：原 Rev C.2 原生工程和 PDF；旧 Rev B PCB 仅用于板框与原生格式参考。

**原理图影响：**全部引脚网络保持；同步封装关联和物料说明。F1 标注由 `2A / 5x20` 改为 `2A / 6x30`，熔断电流仍为 2 A；C4 由 `10µF / 35V` 提高为实购 `10µF / 50V X7R`，容量保持。没有更换 U1 或改变控制/保护连接。

**器件/BOM/PCB 影响：**有封装、耐压、保险管规格及布局变化，需使用本目录 PCB BOM，不能直接使用旧 Rev B 封装采购/制板。IR2184 与参数表已购 IR2104 不可直接互换；RS_L 25 mΩ 尚未购齐。其余未确认项见详细说明。

**仿真/固件影响：**本轮没有修改、运行或重新验证 Multisim、ngspice 模型及 STM32 固件。保留源文件不等于验证了 C4 有效容量、所购电感、热设计或实际功率级。

## 打开与复现

用嘉立创 EDA **专业版**支持 `.eprj2` 的版本打开工程副本，选择 `G题 Rev C.2 — PCB封装与布局修订`，查看 `Rev C2 120x90 — 封装布局复核 / 待完成布线`。默认页指向新 PCB。工程由原生历史记录追加生成，尚未在客户端打开，不能把 SQLite/网络检查当作导入验证。

Python 3.10+，安装 [tools/requirements.txt](tools/requirements.txt)，在仓库目录执行：

```bash
python projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/tools/build_pcb.py
python projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/tools/route_local.py
python projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/tools/verify_pcb.py
python projects/2026-electronics-contest/g-buck/rev-c2/pcb/hardware-fit-120x90/tools/render_pcb.py
```

先构建再布局部线；`route_local.py` 不应直接重复运行在已有走线的工程上。所有预览来自交付工程中的实际坐标和走线，不是客户端截图。1:1 页仅供器件贴合核对；F1 与分流器标为假设，不能按该页钻孔。
