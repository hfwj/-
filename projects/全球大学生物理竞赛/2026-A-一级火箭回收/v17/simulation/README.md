# 从本次原文复现排版

本目录不含火箭轨迹求解器，也不导入之前仿真数组。程序只用于原文提取、表格转写、表格派生图、排版与来源核查。

在v17执行：

```bash
python simulation/extract_source.py
python simulation/build_source_tables.py
MPLCONFIGDIR=/tmp/upc_matplotlib OPENBLAS_NUM_THREADS=1 python simulation/build_source_figures.py
cd reports/latex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
cd ../..
python simulation/validate_source_paper.py
```

Python需python-docx、NumPy、Matplotlib、Pillow和PyMuPDF；LaTeX需XeLaTeX及常规TeX Live宏包、Latin Modern字体。中文AI原问需Noto Serif CJK SC或FandolSong-Regular。源码包自带全部编译图像，不需要Python即可编译论文。

英文表格中包含针对本次原文的人工转写，不是通用机器翻译器；若更换原文，须同步审校转写内容，不能只替换输入文件。

核查项目：Word表格逐格提取一致、6幅曲线PNG字节一致、18张原数据表入稿、19个论文表格、10图、10条引用、摘要限字、字号/页眉、无缺字/引用或溢出错误、不导入历史仿真数组。此验证不是重新验证原文的仿真物理或数值正确性。

比较基线为本次上传Word。原模型结果未重算；原理图/器件/BOM/PCB/固件无修改。
