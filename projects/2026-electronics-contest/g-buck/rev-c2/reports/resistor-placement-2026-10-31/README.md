# Rev C.2 电阻位置图

按当前原生PCB工程核对全部120个器件坐标和角度，标出43个电阻位号，其中R_SN默认不装，正常装配42个。元件面俯视，与仓库PCB预览同向；图由工程几何绘制，不是实物照片，不含铜线以便看清焊盘。

- [总览](Resistors_Overview.png)
- [A 功率与驱动区](Resistors_A.png)
- [B 保护与逻辑区](Resistors_B.png)
- [C ADC与采样区](Resistors_C.png)
- [四页PDF](Resistors_RevC2.pdf)
- [电阻坐标及原始参数CSV](resistor_positions.csv)

黄色为电阻本体/焊盘；引线末端圆点为器件中心。R_PRE处是外置22Ω/5W预充电阻的接线焊盘，并非将功率电阻本体直接放在该框内；RS_IN/RS_OUT=50mΩ、RS_L=25mΩ。带±0.1%标注的是精密电阻，其余精度/功率及实物额定见[采购清单](../updated-bom-2026-10-27/物料清单.md)。

比较基准：436fd43的Rev C.2资料及同版原生PCB工程。本次仅增加位置图、坐标表与绘图脚本，不改原理图连接/脚号/参数，不改器件/BOM、PCB封装/位置/铜线或库存，不改仿真/模型/固件。已核对43个位号在总览及A/B/C分区中完整覆盖，120器件坐标及角度与原生记录一致；未做实物装配、电气测量或原生ERC/DRC，图不作为制板放行依据。

复现：Python + matplotlib +项目已有native读取依赖，安装Noto CJK字体后运行本目录render_resistors.py。
