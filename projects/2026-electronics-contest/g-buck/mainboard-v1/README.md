# G题主板：主功率＋CC合板 / 六功能区已连线

2026-11-08。按用户要求将V1.1的A/B合成同一块主板，主控显示、辅助供电仍独立。

**[下载嘉立创原理图资料包](downloads/GBUCK_Mainboard_Functional_Std.zip) · [直接下载JSON](schematic/native/Mainboard_Functional_Blocks.json) · [六页PDF](schematic/previews/Mainboard_Six_Blocks.pdf) · [整图预览](schematic/previews/Mainboard_All.png)**

| 功能区 | 查看连线 |
|---|---|
| 01 输入保护、输入采样与接口 | [PNG](schematic/previews/01_Block.png) |
| 02 同步Buck主功率与输出 | [PNG](schematic/previews/02_Block.png) |
| 03 恒压反馈、恒流注入与使能 | [PNG](schematic/previews/03_Block.png) |
| 04 输出电流/电压采样 | [PNG](schematic/previews/04_Block.png) |
| 05 DAC电压/电流设定与滤波 | [PNG](schematic/previews/05_Block.png) |
| 06 CC恒流补偿与设定缓冲 | [PNG](schematic/previews/06_Block.png) |

## 嘉立创打开方法

原生文件是嘉立创EDA标准版JSON、docType=5、一个原理图页，不是专业版eprj工程。

- 标准版：文件 → 打开 → 嘉立创EDA，选择JSON。
- 专业版：导入嘉立创EDA（标准版），选择JSON；导入后复核脚号与网络。
- 六个框属于同一块板，U5A/U5B是一只MCP6002的两个部分。同名网络是电气连接，NC不接。

[BOM](schematic/BOM_mainboard.csv) · [逐引脚接线表](results/data/Pin_Net_Table.csv) · [静态连线检查](results/data/connectivity_report.json) · [新旧对比](results/data/merge_audit.json) · [修改影响与接口](reports/合板与连线影响.md)

## 本次影响

比较基准为abc0556的V1.1：芯片、阻容值和保留引脚网络不变，删除A↔B两只连接器；B.J2重命名为主板J3，沿用10针脚序。主板42件/123脚。没有更改外部主控/辅源电路、固件或仿真。

**这是原理图连线稿：未完成商城选型、封装绑定、PCB、原生ERC/DRC或台架验证，不能直接下单。**此前C14偏压/7V余量和瞬时1A限制仍适用。

## 重建及核对

```bash
python tools/generate_blocks.py /tmp/gbuck-mainboard references/baseline
python tools/verify_connections.py /tmp/gbuck-mainboard
python tools/render_blocks.py /tmp/gbuck-mainboard
```

生成与核对使用Python标准库；渲染另需Playwright/Chromium和PyMuPDF。图纸框不是PCB元件布局。旧四板版本保留，不覆盖历史资料。
