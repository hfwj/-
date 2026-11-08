# v16：参照两篇参考论文的LaTeX英文论文

按2025-GM-A-112的A4/约11pt Computer Modern类版式组织，参考2023-GM-A-227的物理过程与安全因素分析结构，实际编译为**23页英文论文**。正文采用Latin Modern Roman，摘要224词，8幅矢量图、8张表、13条参考文献。

- [论文PDF](reports/TBA_A_LaTeX_Draft01.pdf)
- [轻量LaTeX源码ZIP（含矢量图，可选XeLaTeX编译）](downloads/UPC_A_LaTeX_Source.zip)
- [完整绘图/数据/排版复现包](downloads/UPC_A_LaTeX_Reproduction.zip)
- [LaTeX主文件](reports/latex/main.tex) · [参考文献bib](reports/latex/references.bib) · [队号配置](reports/latex/config.tex)
- [中文：版式参照与编写说明](reports/版式参照与编写说明.md)
- [字体与页面测量](references/layout_study.json) · [排版与独立编译验证](results/data/paper_validation.json)

源包已在独立目录以XeLaTeX/BibTeX完整编译，PDF正文与主稿一致，无仓库路径依赖。没有实际登录Overleaf测试；上传后选择XeLaTeX、主文件main.tex即可按说明编译。CJK仅用于AI说明原始提问，需要Noto Serif CJK SC或FandolSong-Regular。

技术内容使用v15的+45°、七机140 t条件性名义候选；不是旧149 t三机/无风论文，也不恢复附件未复现的96/110 t结论。本文不重跑优化或改参数；核心数值与控制数组SHA256不变。完整AI逐字记录和实际队号尚待补齐，不声称为已完成提交准备的终稿。

相对v15，本次仅重写/组织论文、重绘图表和LaTeX排版。动力学、环境、控制等效与数值结果不变；原理图连接/引脚/器件值、器件/BOM、PCB、固件无变化，也不新增真实硬件验证。
