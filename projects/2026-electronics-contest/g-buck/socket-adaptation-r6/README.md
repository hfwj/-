# R6：STM32核心板与屏幕可拔插

已按用户最新授权选定现成模块，完成六区主控底板原理图：

- 核心板：WeAct Studio BluePill-Plus **V1.1 / ST STM32F103C8T6**，U3不装、SB1断开；两条1×20排母安装。
- 屏幕：Joy-IT **SBC-LCD84x48 Revision 2 / PCD8544**；一条1×8排母安装。不要混用Rev.1。

[主控底板.eprj3工程下载](downloads/GBUCK_Control_R6_EPRJ3.zip) · [三板完整.eprj3工程下载](downloads/GBUCK_System_R6_EPRJ3.zip)

[BOM Excel（含底板17件、两个模块及全系统）](schematic/Control_Modules_BOM_R6.xlsx) · [六区原理图PDF](schematic/previews/Control/Control_Blocks.pdf) · [选型、接线与修改影响](reports/选型接线与修改影响.md)

解压后打开相应文件夹内的.eprj3索引，必须保留sch目录；ZIP本身不是.eprj3文件。references/generated中的标准版JSON只用于生成/校验，不替代专业版工程。

相对75ab883/R5：底板移除U6及重复最小系统/JSWD，新增两条核心板排母并改屏幕插座脚序，25→17件、116→88脚。两个模块单独采购，需带已焊直排针；插座不是SMT基础库件。原有基础库阻容尽量保留，历史待定料号/封装仍如实待核。板凳柱和合适通孔件保留，工厂完成代焊须按订单审核。

电压采样PA0→PA2（ADC_IN2）、减小键PA11→PB10，固件必须同步调整；屏幕驱动类型仍PCD8544。主功率板/辅源原理图文件与R5逐字节相同，10芯排线脚序保留；模型未修改。全系统73件263脚，另两个成品模块，不重复计算模块内部元件。

核心板从3V3针供电，正常工作不接USB，VCC针悬空且不带负载，调试器不并联供电。屏幕2.7–3.3V工作上限与辅助电源正容差、模块LDO反灌及启动仍需确认；不能据本包直接投板。

静态实际导线/符号网络、官方格式及官方只读查看器加载通过；未做嘉立创原生编辑保存/ERC、封装绑定/PCB或实物测试。完整制造前待核事项见接线说明。此前等待用户型号的前置清单仅作历史记录。
