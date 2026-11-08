# R5：主控板六区＋辅助降压板三区

[主控板eprj3工程](downloads/GBUCK_Control_R5_EPRJ3.zip) · [辅助板eprj3工程](downloads/GBUCK_Auxiliary_R5_EPRJ3.zip) · [两板BOM Excel](schematic/Control_Auxiliary_BOM_R5.xlsx) · [三板完整工程](downloads/GBUCK_System_R5_EPRJ3.zip)

[主控六区PDF](schematic/previews/Control/Control_Blocks.pdf) · [辅助三区PDF](schematic/previews/Auxiliary/Auxiliary_Blocks.pdf) · [修改与接线说明](reports/分区与修改影响.md)

两板仍独立制作，共36件150脚；全系统81件291脚。分区内使用实际导线，跨区同名网络相连。保留全部引脚网络及标称值、板间接口和固件/模型。BOM补全部分主控0805阻容建议选型，不代表封装已绑定。

按用户确认保留通孔接口和板凳柱，由工厂贴片＋插件焊接，是否可代焊须按实际料号审核；部分器件型号/机械图仍待核实。取消接线柱统一≥5A采购要求，L1的Isat≥5A不变。

解压各包，打开对应文件夹内.eprj3，保留sch目录。官方格式/查看器和静态网络核对通过；未做原生编辑保存/ERC/DRC、PCB或实测，不能直接制板。
