# v17：只据本次Word原文重排的LaTeX论文

**本版响应用户纠正：技术内容只取本轮上传《回收仿真_七机两段点火.docx》，没有沿用之前140 t重算稿。** 两篇2023/2025论文仅作结构、字体、图表形式参考。

- [22页论文 PDF](reports/TBA_A_SourceDocument_LaTeX.pdf)
- [可独立编译的LaTeX源码包](downloads/UPC_A_SourceDocument_LaTeX.zip)
- [全部源文、转写、核查与图表复现包](downloads/UPC_A_SourceDocument_Complete.zip)
- [LaTeX主文件](reports/latex/main.tex) · [原曲线的英文标注宏](reports/latex/source_plots.tex)
- [本次原文重排说明](reports/本次原文重排说明.md)
- [原稿存档](references/回收仿真_七机两段点火_本次原稿.docx) · [源文对应核查](results/data/source_paper_validation.json)

保留原文三个阶段：基准104/120 t、Powell参数优化96/110 t、面积律/启停/分级修订102/110–112 t。保留C_D(M)、330 s比冲、7→3→1分级及最后110 t工况106.6 t消耗/2.02 m/s触地。没有替换为此前常Cd0.5、140 t或CasADi/IPOPT重算结果。

源Word的18张实质数据表全部入稿，另加符号表，共19表；6幅原曲线PNG字节保持不变，LaTeX只翻译标签区域；新增流程图和3幅纯表格派生图，共10图。原文封面描述表与单格摘要框并入摘要/问题重述。摘要232词，A4/11pt正文，三线表、编号公式及(a)(b)组合图标注。

轻量源码包选XeLaTeX编译，main.tex为主文件，包含全部图和表；已在无仓库路径依赖的独立目录编译成功。本次没有重新运行原仿真，也不把源文模型的最低测试通过量说成已证明的全局最小值。队号保留TBA。

比较基线为本轮上传Word。只做论文重排、语言/符号澄清和图表标注，原结果数值未更换；原理图连接/管脚/器件值、器件/BOM、PCB、固件无修改。排版验证不代表原物理/数值仿真被独立验证。
