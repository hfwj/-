# G题主板功能分区与BOM手绘指南

2026-11-08 / SMT基础库优先版

基准：fb6e66e 主功率＋CC六区合板，42个器件/123个引脚。供用户在嘉立创EDA手动画图，主控和辅助电源板不在此BOM内。

库别以SMT基础库为优先。官网已核实基础库14件；基础库候选4件（C17407三件、C5378一件），未将候选计为已确认。其余保留满足电气要求的型号，分列扩展库、待核实和通孔手焊。库别/库存会变化，下单时按所用嘉立创SMT平台重新筛选。JLCPCB官网标签不能替代国内下单平台当日结果。

器件搜索：优先输入C料号，再逐项核对厂家完整型号、封装和脚序。0805/1206/1210/2512均为英制；不要选成公制0805。库中符号存在不代表SMT基础库，也不代表此工程已绑定封装。

## 修改影响

原理图：不更改连接、脚序、标称阻容值或42件数量；保留原JSON和旧BOM。新增推荐选型文件供手绘。

器件/封装：推荐普通阻容0805，采样电阻2512；C2为1206，C5/C6为1210。100nF统一50V，C4原16V提升50V。U5采用带T的卷带包装，同电气型号/同封装。尚未绑定EDA封装或制作PCB；L1、连接器等需核对厂家机械图。

模型/固件：无改动，无新增动态仿真或实测。本次完成器件覆盖、数量和引脚表静态核对，不构成原生ERC/DRC、环路稳定或效率验收。

## 六个功能区

### 01 输入保护、输入采样与接口

J1 [INPUT 15-25V]：1→RAW+；2→GND

F1 [2A fuse]：1→RAW+；2→FUSED

RS1 [0.05R 1% 1W]：1→FUSED；2→VIN_SYS

J4 [TO AUX D]：1→VIN_SYS；2→GND

U3 [INA226AIDGSR]：10→FUSED；9→VIN_SYS；8→RAW+；1→GND；2→GND；6→+3V3；7→GND；5→SCL；4→SDA；3→NC

C9 [100nF]：1→+3V3；2→GND

J3 [TO BOARD C]：1→+3V3；2→GND；3→SCL；4→SDA；5→VSET_DRV；6→CC_OUT；7→ISENSE；8→VOUT_ADC；9→RUN；10→GND

### 02 同步Buck主功率与输出

U1 [TPS54302DDCR]：3→VIN_SYS；1→GND；5→EN_A；4→FB；2→SW；6→BOOT

C1 [100uF 50V]：1→VIN_SYS；2→GND

C2 [10uF 50V X7R]：1→VIN_SYS；2→GND

C3 [100nF 50V]：1→VIN_SYS；2→GND

L1 [22uH Isat>=5A]：1→SW；2→VREG

RS2 [0.05R 1% 1W]：1→VREG；2→OUT+

J2 [OUTPUT LOAD]：1→OUT+；2→GND

C5 [22uF 25V X7R]：1→VREG；2→GND

C6 [22uF 25V X7R]：1→VREG；2→GND

C4 [100nF 16V]：1→BOOT；2→SW

### 03 恒压反馈、恒流注入与使能

R1 [100k 0.1%]：1→VREG；2→FB

R2 [5.49k 0.1%]：1→FB；2→GND

R3 [56k 0.1%]：1→VSET_DRV；2→FB

D1 [BAT54 (1=A,3=K)]：1→CC_OUT；3→CC_K；2→NC

R4 [10k 1%]：1→CC_K；2→FB

R5 [1k]：1→RUN；2→EN_A

R6 [100k]：1→EN_A；2→GND

### 04 输出电流/电压采样

U2 [INA180A1IDBVR]：3→VREG；4→OUT+；2→GND；5→+3V3；1→ISENSE

C8 [100nF]：1→+3V3；2→GND

R7 [100k 0.1%]：1→OUT+；2→VOUT_ADC

R8 [10k 0.1%]：1→VOUT_ADC；2→GND

C7 [10nF]：1→VOUT_ADC；2→GND

### 05 DAC电压/电流设定与滤波

U4 [MCP4728-E/UN]：1→+3V3；10→GND；2→SCL；3→SDA；4→GND；5→RDY；6→DAC_V；7→DAC_I；8→NC；9→NC

C10 [100nF]：1→+3V3；2→GND

R9 [100k]：1→RDY；2→+3V3

R10 [1k]：1→DAC_V；2→V_FILT

C12 [100nF]：1→V_FILT；2→GND

### 06 CC恒流补偿与设定缓冲

U5 [MCP6002-I/SN]：3→I_FILT；2→I_ERR；5→V_FILT；6→VSET_DRV；4→GND；1→CC_OUT；7→VSET_DRV；8→+3V3

R11 [1k]：1→ISENSE；2→I_FILT

C13 [10nF]：1→I_FILT；2→GND

R12 [100k 1%]：1→DAC_I；2→I_ERR

R13 [1k 1%]：1→CC_OUT；2→COMP

C14 [220nF X7R]：1→COMP；2→I_ERR

D2 [BAT54 (1=A,3=K)]：1→I_ERR；3→CC_OUT；2→NC

C11 [100nF]：1→+3V3；2→GND

## 合并采购BOM

J1 J2（2件）：2位接线端子

WJ500V-5.08-2P / C8465 / THT P5.08mm / 非SMT/手焊

按原厂机械图；1正极、2GND，勿混用5.00mm

https://jlcpcb.com/partdetail/C8465

J3（1件）：带防呆10针连接器

2.54-2*5P简牛 BOOMELE / C5665 / THT 2x5 P2.54mm / 非SMT/手焊

核对1脚三角标记和外壳尺寸

https://jlcpcb.com/partdetail/C5665

J4（1件）：2针辅助供电接口

2.54mm 1x2直插排针 / 按参数搜索 / THT 1x2 P2.54mm / 非SMT/手焊

参数选型；未指定商城料号；1 VIN_SYS，2 GND



F1（1件）：2A 63V保险丝

0466002.NRHF / C3105 / 1206保险丝 / 待核实库别

非自恢复保险；不提供精确1A限流

https://jlcpcb.com/partdetail/C3105

RS1 RS2（2件）：0.05Ω ±1% 1W

RL2512FK-070R05L / C876461 / 2512 / 待核实库别

电流取样两端用Kelvin引线

https://jlcpcb.com/partdetail/C876461

U1（1件）：同步Buck 4.5–28V/3A

TPS54302DDCR / C311983 / SOT-23-THIN6 / DDC / 待核实库别

不得用通用SOT23-6直接代替DDC焊盘

https://jlcpcb.com/partdetail/C311983

U2（1件）：电流检测增益20

INA180A1IDBVR / C122228 / SOT-23-5 / DBV / 待核实库别

必须A1；B1脚序不同，A2增益不同

https://jlcpcb.com/partdetail/C122228

U3（1件）：输入电流/电压监测

INA226AIDGSR / C49851 / VSSOP-10 / DGS P0.5mm / 待核实库别

不能与MSOP外形想当然互换

https://jlcpcb.com/partdetail/C49851

U4（1件）：四通道DAC

MCP4728-E/UN / C108207 / MSOP-10 P0.5mm / 扩展库（官网）

C/D通道不用；3.3V供电

https://jlcpcb.com/partdetail/C108207

U5（1件）：双运放

MCP6002T-I/SN / C7377 / SOIC-8 3.9mm P1.27mm / 扩展库（官网）

原MCP6002-I/SN加T仅卷带包装；同一只IC两个单元

https://jlcpcb.com/partdetail/C7377

D1 D2（2件）：单肖特基二极管

BAT54,215 Nexperia / C85084 / SOT-23 / 待核实库别

1=A，3=K，2=NC；不用BAT54A/C/S

https://jlcpcb.com/partdetail/C85084

L1（1件）：22µH ±20% 额定4A Isat5A DCR80mΩ

ZD0850-220M / C46956554 / 8.8x8.2mm型号专用焊盘 / 待核实库别

焊盘尺寸需查原厂图；不能按名称选通用8x8封装

https://jlcpcb.com/partdetail/C46956554

C1（1件）：100µF 50V 铝电解

50YXF100MEFC8X11.5 / C88728 / THT D8x11.5mm P3.5mm / 非SMT/手焊

注意极性，1正极、2GND

https://jlcpcb.com/partdetail/C88728

C2（1件）：10µF 50V X7R ±10%

CL31B106KBHNNNE / C89632 / 1206 / 扩展库（官网）

输入最高25V，保留50V耐压

https://jlcpcb.com/partdetail/C89632

C5 C6（2件）：22µF 25V X7R ±10%

CL32B226KAJNNNE / C309062 / 1210 / 待核实库别

有条件候选：10V偏压下两只合计有效容量需≥22µF；需曲线或实测

https://jlcpcb.com/partdetail/C309062

C3 C4 C8 C9 C10 C11 C12（7件）：100nF 50V X7R ±10%

CC0805KRX7R9BB104 / C49678 / 0805 / 基础库（官网已核实）

统一7只；C4由16V额定提升50V，标称容值不变

https://jlcpcb.com/partdetail/C49678

C7 C13（2件）：10nF 50V X7R ±10%

CL21B103KBANNNC / C1710 / 0805 / 基础库（官网已核实）

输出分压滤波和电流滤波

https://jlcpcb.com/partdetail/C1710

C14（1件）：220nF 50V X7R ±10%

CL21B224KBFNNNE / C5378 / 0805 / 基础库候选/待官网复核

不得仅凭第三方历史Basic标记下单；核对有效容值

https://jlcpcb.com/partdetail/C5378

R1 R7（2件）：100kΩ ±0.1% 1/8W

RT0805BRD07100KL / C122537 / 0805 / 待核实库别

保留采样/反馈精度，不换1%凑基础库

https://jlcpcb.com/partdetail/C122537

R2（1件）：5.49kΩ ±0.1% 1/8W

RT0805BRD075K49L / C865577 / 0805 / 待核实库别

不改5.49k标称值

https://jlcpcb.com/partdetail/C865577

R3（1件）：56kΩ ±0.1% 1/8W

TC0550B5602T5G / C2989136 / 0805 / 待核实库别

56k，不能替换为56.2k

https://jlcpcb.com/partdetail/C2989136

R8（1件）：10kΩ ±0.1% 1/8W

RT0805BRD0710KL / C110775 / 0805 / 待核实库别

保留输出电压采样精度

https://jlcpcb.com/partdetail/C110775

R4（1件）：10kΩ ±1% 1/8W

0805W8F1002T5E / C17414 / 0805 / 基础库（官网已核实）

保持原规格

https://jlcpcb.com/partdetail/C17414

R5 R10 R11 R13（4件）：1kΩ ±1% 1/8W

0805W8F1001T5E / C17513 / 0805 / 基础库（官网已核实）

保持原标称值

https://jlcpcb.com/partdetail/C17513

R6 R9 R12（3件）：100kΩ ±1% 1/8W

0805W8F1003T5E / C17407 / 0805 / 基础库候选/待官网复核

不涉及R1/R7精密100k；R12为补偿电阻

https://jlcpcb.com/partdetail/C17407

## 手绘与布板核对

电源：输入15–25V；外部辅助板提供稳定3.3V，所有模块共地。J3的5/6脚为模拟信号，不允许主控GPIO推挽驱动。

C5/C6需核对直流偏压下有效容量；44µF标称合计不等于有效容量。C14属于3.3V控制域，不能按输出5–7V直接当作其偏压；仍需核对偏压、容差。

7V是软件设定范围选项，不是硬件最低工作电压；恒流时输出可低于7V。保留7V设定需实测DAC/运放高端余量。

当前结构不保证任意瞬间电流≤1A；缩小C14不能消除输出电容造成的负载阶跃首峰。2A保险丝不能替代精确输出限流。

布板：输入电容靠U1 VIN/GND；C4靠BOOT/SW；SW铜区短小，避开FB/I_ERR；反馈从VREG取样。两只采样电阻Kelvin取样；模拟区远离L1和SW，优先连续地平面。这里只给分区建议，不给已验证板框尺寸。

最终逐项核对123脚（含5个NC）。NC是明确不接，不是统一接到名为NC的网络。SDA/SCL上拉须核对外部主控板是否已提供，禁止无依据增加或重复上拉。

## 来源

基础库：https://jlcpcb.com/parts/basic_parts

第三方候选记录：https://lrks.github.io/jlcpcb-economic-parts/

L1：https://item.szlcsc.com/49125430.html

完整BOM：Mainboard_BOM.xlsx；连接表：Pin_Net_Table.csv。