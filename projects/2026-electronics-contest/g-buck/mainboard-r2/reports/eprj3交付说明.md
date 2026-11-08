# 嘉立创专业版 eprj3：主功率＋CC主板R2

2026-11-08。此为真实文件夹式工程；不是标准版JSON改后缀。工程入口为 `GBUCK_Mainboard_R2/GBUCK_Mainboard_R2.eprj3`，必须与同目录下的 `sch/` 一起保留。

## 打开

1. 完整解压 `GBUCK_Mainboard_R2_EPRJ3.zip`。
2. 在支持文件夹工程的嘉立创EDA专业版客户端中打开 `GBUCK_Mainboard_R2/GBUCK_Mainboard_R2.eprj3`。
3. 进入 Mainboard → Mainboard_6_Blocks。六区属于同一块主板，同名网络相连。

不要只下载/移动 `.eprj3` 索引而遗漏 `sch` 文件夹；索引本身不含完整原理图。

## 相对基准的影响

基准为 d38634b 的主板R2原理图，BOM为4482aa4版本。本次只转换工程格式和符号/导线表达：44件、135脚、5个NC，以及主控J3的10针脚序全部保持。电路拓扑、引脚网络、阻容标称值、采购选型、PCB封装要求、仿真及固件不变。每只四脚接线柱为一个电极，四脚同网。

器件符号、器件定义全部内嵌，不依赖在线库加载。商城料号、推荐封装作为属性保存；实际Footprint未绑定。板凳式接线柱具体型号、额定承流及机械尺寸仍未核实，须完成选型后绑定专用封装。

## 验证与限制

- 官方格式规范的验证脚本：2095条记录通过Schema校验。
- 独立读取专业版符号/元件/导线后核对：44件/135脚/5个NC/155段导线，与R2网络一致。
- 官方 easyeda/easyeda-viewer 0.7.1：识别为eprj3工程，44件，0解析坏行、0未知图元、0占位符、0诊断；Chromium实际加载并截图，页面脚本错误为0。
- 上述查看器为只读工具，不等于嘉立创原生编辑器打开/保存验证。原生客户端导入/编辑/ERC、PCB/DRC、实物测试尚未完成；不能直接制板。

官方格式说明：https://github.com/easyeda/easyeda-pro-eprj3-format
官方格式校验：https://github.com/easyeda/easyeda-format-skill
官方查看器：https://github.com/easyeda/easyeda-viewer

## 复现

在mainboard-r2目录执行 `python tools/convert_pro_eprj3.py .`，再执行 `python tools/verify_pro_eprj3.py .`。Schema校验：`node tools/validate_pro_records.cjs schematic/pro/GBUCK_Mainboard_R2 /path/to/easyeda-format-skill`，需按官方校验器要求安装ajv/ajv-formats。转换依赖存档的标准版R2源码，仅作为生成输入保留。
