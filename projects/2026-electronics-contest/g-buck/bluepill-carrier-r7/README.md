# R7：适配你选购的STM32F103C8T6核心板

核心板改为用户商品截图同款Blue Pill，向下已焊排针；用户确认USB端上排首针为GND。屏幕仍为Joy-IT SBC-LCD84x48 Rev.2（PCD8544）。

[主控板.eprj3工程](downloads/GBUCK_Control_R7_EPRJ3.zip) · [三板完整.eprj3工程](downloads/GBUCK_System_R7_EPRJ3.zip) · [最新BOM Excel](schematic/Control_Modules_BOM_R7.xlsx)

[六区原理图PDF](schematic/previews/Control/Control_Blocks.pdf) · [接线、方向及修改影响](reports/选型接线与修改影响.md) · [40针映射表](results/data/Core_Socket_Map_R7.csv)

相对2fcaa7d/R6，JCORE1.1从NC改接GND，两排中心距要求由15.22mm改为15.24mm，更新核心板BOM。两条1×20排母型号保留；主控仍17件88脚、22个NC；全系统73件263脚，另单独采购两个成品模块。

方向：从模块元件面看，USB朝左，上排为JCORE1/P1，下排为JCORE2/P2；两排均从USB端编号1→20。这是本设计的安装编号，不是芯片脚号。上排前两针均GND，第三针3V3；下排第18针5V在底板不接。到货检查首针与GND导通，不能套用首针5V的其他板型。

GPIO保留R6：电压PA2/ADC_IN2、电流PA1/ADC_IN1、减少键PB10；不因换板再次改固件。PCD8544屏幕脚序及主板10针接口不变，主功率/辅助图页与R6逐字节相同，模型未修改。

静态真实导线与符号网络核对、官方格式Schema及六区PDF生成通过；本轮未运行官方查看器或原生编辑保存/ERC/DRC，未绑定封装/设计PCB/实测。新模块LDO、供电反灌、屏幕供电容差及机械实物仍需核对，不能直接投板。保留通孔件由工厂贴片＋插件焊接，具体服务按订单审核。

解压后打开同名文件夹内.eprj3，必须保留sch目录。历史R6不覆盖；references/generated内标准版JSON仅为生成输入。
