# G题R3：辅助电源连接也采用板凳式焊接接线柱

[下载专业版eprj3完整工程](downloads/GBUCK_System_R3_EPRJ3.zip) · [BOM Excel](schematic/System_BOM_R3.xlsx) · [接线/修改说明](reports/辅助电源接线柱修改与接线说明.md) · [接线PDF](reports/Connection_Guide_R3.pdf)

解压后打开`GBUCK_System_R3/GBUCK_System_R3.eprj3`，保留`sch`目录。工程包含三块独立板的三张图页；不是一块三合一PCB。

| 从哪里 | 接到哪里 | 电源 |
|---|---|---|
| 主板J4P | 辅助板J1P | VIN_SYS，15–25V |
| 主板J4N | 辅助板J1N | GND |
| 辅助板J2P | 主控板JPP | +3V3 |
| 辅助板J2N | 主控板JPN | GND |

每只接线柱四脚接同一网络；10芯排线连接主板J3↔主控J1保持不变。四只双针电源接口改为八只板凳柱；主板45件、主控25件、辅助5件，共75件/277脚。除接口符号/封装需求外，保留网络、电路参数、模型及固件不变。

接线柱厂家型号、额定承流和机械尺寸待定，≥5A为采购要求，不能直接制板。三板BOM及真实专业版导线静态检查、官方格式和查看器通过；原生编辑保存/ERC/DRC及实测未验证。

[主板实际显示](schematic/previews/Mainboard_6_Blocks.png) · [主控实际显示](schematic/previews/MCU_LCD.png) · [辅助板实际显示](schematic/previews/Aux_Power.png)
