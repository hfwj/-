# G题主板R2：最新嘉立创专业版原理图

**[下载专业版eprj3完整工程](downloads/GBUCK_Mainboard_R2_EPRJ3.zip)** · [打开说明与转换核对](reports/eprj3交付说明.md) · [官方查看器实开截图](schematic/previews/Pro_Viewer_Mainboard.png)

2026-11-08更新：优先交付专业版文件夹工程。解压后打开`GBUCK_Mainboard_R2/GBUCK_Mainboard_R2.eprj3`，必须保留同目录`sch/`。44件/135脚与R2一致；Schema及官方只读查看器解析/显示通过，原生客户端编辑/保存与ERC尚未验证。格式转换不改器件、网络、BOM、模型或固件。

以下为历史标准版输入和R2硬件说明，保留供复现。

2026-11-08。主功率＋CC同一块板，六个功能区；44件/135脚。配套4482aa4的BOM R2。

[原生嘉立创标准版JSON](schematic/native/Mainboard_Functional_Blocks.json) · [全部下载](downloads/GBUCK_Mainboard_R2_EasyEDA_Std.zip) · [六页PDF](schematic/previews/Mainboard_Six_Blocks.pdf) · [BOM Excel](schematic/Mainboard_BOM_R2.xlsx) · [逐引脚表](results/data/Pin_Net_Table.csv)

## 打开方法

嘉立创EDA标准版：文件→打开→嘉立创EDA，选择JSON。专业版：使用导入嘉立创EDA标准版功能导入JSON。此文件是docType=5的标准版项目，不是专业版eprj工程；未在原生编辑器中验证导入或执行ERC。

同名网络跨区相连，NC明确不接。四只板凳柱暂用自包含四脚符号，每只1/2/3/4脚均接同一网络；厂家实际脚号、形状及封装待核对，不代表四个独立电极。所有封装字段仍未绑定；属性中推荐封装和料号仅为选型信息。

## 修改影响

比较基准：4482aa4的BOM R2、fb6e66e的42件原理图。

- 原理图：删除双位J1/J2，改为J1P→RAW+、J1N→GND、J2P→OUT+、J2N→GND四只四脚板凳柱；44件/135脚。40只保留器件的脚号网络不变，主电路拓扑/阻容标称值不变。C4标示耐压16V→50V；U5标示MCP6002T-I/SN（卷带包装）。
- 选型/封装：属性同步BOM R2；R6/R9/R12推荐0603基础库C25803，100k/1%不变。其余推荐选型沿用R2；已核实基础库17件，不保证所有元件为基础库或当前订单有货。接线柱具体厂家/料号、≥5A额定和孔距/孔径未核实；PCB须按最终机械图建封装，不可直接制板。
- 主控接口：J3仍为2.54mm 2x5P简牛（C5665），1→1直通连接主控板原J1；1 +3V3、2 GND、3 SCL、4 SDA、5 VSET_DRV、6 CC_OUT、7 ISENSE、8 VOUT_ADC、9 RUN、10 GND。5/6仅测试，不由主控GPIO驱动。控制板/辅助板原图未修改，也未包含在本主板JSON中。
- 模型/固件：不改。未新增动态仿真或硬件测试；不保证任意瞬间电流≤1A、环路稳定或整机效率达标。

## 核对结果

脚号与实际导线几何/同名网络静态核对PASS：44件、135脚、5个NC、155段正交导线；40只保留器件及J3脚序与原版一致。该检查不是原生ERC/DRC。

[静态报告](results/data/connectivity_report.json) · [新旧核对](results/data/revision_audit.json)

## 重建

在本目录执行：

```bash
python tools/generate_blocks.py . references/baseline schematic/BOM_ByReference_R2.csv
python tools/verify_connections.py .
python tools/render_blocks.py .
```

生成/核对为Python标准库；预览另需Playwright、Chromium、PyMuPDF。封装和器件供应情况须按实际采购再核对。历史版本保留不覆盖。
