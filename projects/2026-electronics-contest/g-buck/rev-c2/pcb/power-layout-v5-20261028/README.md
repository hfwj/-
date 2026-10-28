**最新Gerber实测更正：**[核定报告](gerber-review/README.md)。实际铜形对应v5，51网连通、无异网铜短路；底层一处约0.199881mm。先前按椭圆及槽孔方向的字段解释不代表实际Gerber，详见报告。

# PCB 功率布局 v5（相对上传 v4）

[核定与修改说明](reports/PCB_v5_核定与修改说明.md) · [验证数据](results/data/verification.json) · [修订工程](native/GBUCK_RevC2_PowerLayout_v5_PCB修正_20261028.eprj2)

修正地铜与椭圆焊盘短路，LO缩短至25.66mm并消除间距违规，删除两个无效过孔和IL_BI零长度线。静态51网连通，异网铜间距≥0.20mm。原理图、器件/BOM/封装/位置及仿真/固件不变。F1槽孔实物朝向待核；未运行原生ERC/DRC、未制造放行。
