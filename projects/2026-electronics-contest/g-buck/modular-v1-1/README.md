# G题四块独立板：Modular V1.1 最简试改

2026-11-07。已先核对《A板可行性审查》，再尝试最小修改。**A板不加器件；四板仍71件。唯一实体变更：B.C14从1uF改220nF；DAC A改内参/G2，电流目标改为经校准的0.95A。**

[下载完整资料包](downloads/GBUCK_Modular_V1_1_reviewed_draft.zip) · [仅嘉立创JSON与说明](downloads/GBUCK_Modular_V1_1_JSON.zip) · [审查逐项核对](reports/审查核对与最简试改.md) · [导入/配置/调试](reports/导入与首次调试.md)

| 板 | 嘉立创EDA标准版原理图 | 预览 |
|---|---|---|
| A 主功率与采样 | [JSON](schematic/standard_json/A_Power_Sense.json) | [PNG](schematic/previews/A_Power_Sense.png) / [PDF](schematic/previews/A_Power_Sense.pdf) |
| B 恒流与数字设定 | [JSON](schematic/standard_json/B_CC_DAC.json) | [PNG](schematic/previews/B_CC_DAC.png) / [PDF](schematic/previews/B_CC_DAC.pdf) |
| C 主控、液晶、按键 | [JSON](schematic/standard_json/C_MCU_LCD.json) | [PNG](schematic/previews/C_MCU_LCD.png) / [PDF](schematic/previews/C_MCU_LCD.pdf) |
| D 辅助供电 | [JSON](schematic/standard_json/D_Aux_Power.json) | [PNG](schematic/previews/D_Aux_Power.png) / [PDF](schematic/previews/D_Aux_Power.pdf) |

[BOM](schematic/BOM.csv) · [逐针接线表](results/data/pin_connections.csv) · [新旧差分](results/data/change_audit.json) · [静态连接检查](results/data/connectivity_report.json) · [计算数据](results/data/review_calculations.json) · [说明性模型比较](results/figures/cc_model_comparison.png) · [原审查附件](references/A板可行性审查_原附件.md)

## 审查中纠正的重点

理想输出纹波约4.84mV而非48mV；FB本就在A板；再串1k会改变56k注入比例；反馈基准容差不能按±1%预算。未使用的INA226开漏ALERT输出不需为“防输入浮空”添加上拉。附件声称的专业版eprj3和实开截图未随本次上传，不能当作本轮验证证据。

## 验证状态

交付JSON静态核对通过，所有261个引脚的网络与V1一致；元件值差分只有C14。明确假设的CC等效模型支持220nF能加快恢复，但不等于真实TPS54302环路验证。最简结构仍不能保证瞬时电流永不超过1A。

**未在嘉立创编辑器实测导入，未做原生ERC、封装绑定、PCB/DRC、真实MCU固件、台架与≥85%整机效率验证，不能直接下单。**

## 修改影响

比较基准：`c687afe` 的Modular V1。A/C/D电气连接与物料不变，A仅改默认电流文字；B仅换C14为220nF，参考/目标配置需在实际固件中实现并校准。新增/删除实体元件均为0，未改旧版本PCB/固件或仿真。原理图网络不变不意味着旧Rev C.2硬件或固件兼容。

## 重建与计算

```bash
python tools/generate_easyeda.py /tmp/gbuck-modular-v1-1
python tools/validate_easyeda.py /tmp/gbuck-modular-v1-1
python tools/dac_startup_reference.py
python simulation/check_design.py
```

前两项和配置参考只用Python标准库；说明性模型用NumPy/SciPy/Matplotlib。模型限制见报告；UUID重建会变，不代表网络变。结果输出至results/data与results/figures。
