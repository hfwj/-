# G题主功率电路：从零理解恒压与恒流

按3c3574c/R7实际主功率板编写，提供可编辑Word及便于阅读的PDF。五张教学图讲清Buck开关过程、能量与控制通路、反馈注入、恒流纠偏及恒压恒流静态特性。

- [Word文档](reports/G_Buck_Mainboard_Explained_R7.docx)
- [PDF文档](reports/G_Buck_Mainboard_Explained_R7.pdf)
- [文档与教学图整包](downloads/G_Buck_Mainboard_Explained_R7_Package.zip)
- [在线正文](reports/主功率电路从零讲解_R7.md)

从电流流向开始，解释实际器件和关键引脚，逐步推导为什么VSET_DRV越高输出越低、1A怎样变成1V、20Ω/8Ω/5Ω负载为什么会自动切换模式，以及为什么稳态恒流不能保证任意瞬间不超流。另有设定码、效率、采样换算、调试顺序和自查问题。

文中区分当前0.95A参考默认值与理想1A示例，也保留C14偏压、7V设定高端余量、输出电容放电尖峰等尚待验证的边界。图为简化教学示意，非完整接线图或实测；算术数据不是动态仿真。

修改影响：相对3c3574c/R7只新增文档、教学图、算术核对及生成源码；原理图、引脚、器件/BOM/封装、PCB、固件、控制模型均未改。无需因本资料换件或改板，没有新增ERC/DRC或实物试验。

复现：在完整仓库根目录运行`python projects/2026-electronics-contest/g-buck/power-explainer-r7-v1/tools/build_explainer.py`。需要Python的matplotlib、python-docx、reportlab、PyMuPDF，以及Noto Sans CJK SC字体。Word和PDF均从同一Markdown正文生成；PDF是独立排版输出，不声称经过Microsoft Word或LibreOffice渲染。ZIP保留Markdown的reports/results相对路径；重建需要完整仓库中的R7源图和参考文件，文件依据及哈希见references/source_manifest.json。
