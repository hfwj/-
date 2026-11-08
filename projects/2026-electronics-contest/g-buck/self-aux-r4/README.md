# G题R4：自设计贴片辅助电源

[下载专业版eprj3完整工程](downloads/GBUCK_System_R4_EPRJ3.zip) · [BOM Excel](schematic/System_BOM_R4.xlsx) · [设计与影响说明](reports/自设计辅助电源与修改影响.md) · [PDF](reports/Auxiliary_Design_R4.pdf) · [实际显示](schematic/previews/Aux_Power.png)

采用TPS560430X3FDBVR固定3.3V同步Buck；15–25V系统输入，芯片标称600mA，整板目标0.3A待验证。7个贴片器件＋4只通孔板凳柱，不用成品辅源。IC为扩展库，普通电容优先基础库。

对比R3：M1替换为U7、L2、C23–C27；辅助板11件34脚，整机81件291脚。主板/主控文件逐字节不变，板间接口、模型和固件不改。更换辅源的纹波、启动、效率与ADC影响需复测。

解压后打开`GBUCK_System_R4/GBUCK_System_R4.eprj3`，保留`sch/`。三张图页/三块独立板。Schema、专业版导线静态检查及官方查看器通过；封装未绑定，接线柱和部分器件机械资料待核实，原生ERC/PCB/实测未完成。
