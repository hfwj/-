# G题：四块独立板简化方案 Modular V1

2026-11-07。以当前对话确认的 TPS54302 四板草案为基准归档；这是一套独立的新方案，不覆盖旧 Rev B/C/C.1/C.2。

**下载：[完整资料包](downloads/G题_嘉立创EDA_四块独立板.zip) · [仅JSON与导入说明](downloads/G题_嘉立创EDA_JSON.zip)。**

| 独立板 | 嘉立创EDA标准版原理图 | 预览 |
|---|---|---|
| A 主功率与采样 | [A_Power_Sense.json](schematic/standard_json/A_Power_Sense.json) | [PNG](schematic/previews/A_Power_Sense.png) · [PDF](schematic/previews/A_Power_Sense.pdf) |
| B 恒流与数字设定 | [B_CC_DAC.json](schematic/standard_json/B_CC_DAC.json) | [PNG](schematic/previews/B_CC_DAC.png) · [PDF](schematic/previews/B_CC_DAC.pdf) |
| C 主控、液晶、按键 | [C_MCU_LCD.json](schematic/standard_json/C_MCU_LCD.json) | [PNG](schematic/previews/C_MCU_LCD.png) · [PDF](schematic/previews/C_MCU_LCD.pdf) |
| D 辅助供电 | [D_Aux_Power.json](schematic/standard_json/D_Aux_Power.json) | [PNG](schematic/previews/D_Aux_Power.png) · [PDF](schematic/previews/D_Aux_Power.pdf) |

四个文件各是 docType=5、单页的标准版原生 JSON 工程，符号与电气引脚嵌入文件。不是专业版 `.epro/.eprj2`，也不是图片改扩展名。

标准版：文件 → 打开 → 嘉立创EDA；专业版：导入嘉立创EDA（标准版），分别选择 JSON。导入后检查符号、脚号、网络和 ERC。请保持四块板各自独立工程。

- [完整导入与接线说明](reports/导入说明.txt)
- [BOM及建议封装](schematic/BOM.csv)
- [逐引脚接线表](results/data/pin_connections.csv)
- [连接检查结果](results/data/connectivity_report.json)
- [修改影响与验证范围](reports/影响与验证.md)
- [SHA256校验](SHA256SUMS.txt)

## 当前状态

71个元件、261个引脚的文件结构、脚号、导线/网络/NC静态核对通过。该检查不是嘉立创原生ERC，尚未在嘉立创编辑器实际打开验证。

未绑定实体封装、未布PCB、未做DRC，不能直接下单打板。预览由同一生成几何绘制，不是编辑器截图。C14补偿值、瞬态限流、温升、整机≥85%效率与比赛功能仍待验证；不含可直接套用的MCU固件。

## 修改影响

相对当前对话四板草案：本次仅归档、索引和工具可移植性整理，电气网络、脚号、元件值、器件/BOM不变；无PCB、固件或仿真变更。

相对旧Rev C.2：这是新拓扑、控制与采样接口组合。TPS54302替代原分立开关/驱动功率方案，MCP4728/MCP6002设定与恒流环、INA180A1/INA226采样、PCD8544显示均按新方案选用。不能复用旧板、旧引脚表或旧固件；采购与PCB须另行核对。旧版本文件未修改，其仿真结论不迁移到本方案。

## 重建原理图与静态检查

仅需Python标准库；从本目录运行：

```bash
python tools/generate_easyeda.py /tmp/gbuck-modular-v1-rebuild
python tools/validate_easyeda.py /tmp/gbuck-modular-v1-rebuild
```

重建目录包含JSON、SVG、BOM和连接表。UUID重新生成，文件字节可能不同；不代表电气网络有变化。
