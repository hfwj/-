# Rev C.2 电容位置图

按当前原生PCB核对120个器件坐标和角度，标出33个电容位号；其中C_SN默认不装，正常装配32只。元件面俯视，与仓库PCB预览同向。图由工程几何绘制，不是实物照片；省略铜线以便看清焊盘。

- [电容总览](Capacitors_Overview.png)
- [A 功率与驱动区](Capacitors_A.png)
- [B 保护与逻辑区](Capacitors_B.png)
- [C ADC与采样区](Capacitors_C.png)
- [四页PDF](Capacitors_RevC2.pdf)
- [坐标、工程参数与采购规格CSV](capacitor_positions.csv)

图中容量、耐压、介质按[当前采购清单](../updated-bom-2026-10-27/物料清单.md)逐位号标注。采购建议不代表全部实物料号和额定均已验收；CSV保留工程原标注以便区分。

## 装配要点

- C1：470µF/50V；C3：470µF/35V。均为低ESR电解，105℃，D10/P5。图中1脚为正，2脚接GND为负，负极条纹朝负极焊盘；已与逐焊盘网络表核对。
- 其余贴片陶瓷电容均0805，无极性。
- C7～C10：4.7nF/50V/X7R，CL21B472JBANNNC，4只；C_VINP_ADC：4.7nF/50V/C0G（NP0），1只，不能混批。
- C_IL_ADC、C_IL_PROT：1nF/50V/C0G，共2只；不代用另购的1206/X7R。
- C4：10µF/50V；C6/C_A3：10µF/25V（建议X7R），不能把C4混装成25V。
- 100nF/50V/X7R共16只；1µF共4只，其中C2要求50V，C_BOOT/C_A1/C_DRV要求至少25V。
- C_SN：1nF/100V/C0G，默认不装，按实测振铃决定，不用1nF/50V备料替代该预留要求。

## 核对与修改影响

比较基准：84dc101的Rev C.2资料、当前原生PCB与更新采购逐位号CSV。33个电容全部在总览及A/B/C分区覆盖，120器件坐标/角度与原生记录一致；电解正负极与焊盘网络一致。

本次只新增位置图、PDF、坐标表及绘图脚本：原理图连接/脚号/参数不改；器件/BOM、封装、PCB位置/铜线、物料库存不改；仿真/模型/固件未修改或运行。未进行实物焊接、测量或原生ERC/DRC，本图不作为制板放行依据。

复现：Python + matplotlib、Noto CJK字体及项目已有native读取依赖，运行本目录render_capacitors.py。
