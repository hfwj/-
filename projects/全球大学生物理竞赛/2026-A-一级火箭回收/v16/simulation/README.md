# 图表与排版复现

本轮冻结v15结果、重绘图表并生成LaTeX，不修改或重跑火箭优化。完整包保留数据，轻量LaTeX包只含编译所需文件。

在v16目录执行：

```bash
MPLCONFIGDIR=/tmp/upc_matplotlib OPENBLAS_NUM_THREADS=1 python simulation/build_figures.py
python simulation/build_tables.py
cd reports/latex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
cd ../..
python simulation/validate_paper.py
```

绘图需NumPy、Matplotlib、随包辅助模块和Latin Modern字体；验证需PyMuPDF。编译需TeX Live常用宏包、XeLaTeX、BibTeX，中文原问使用Noto Serif CJK SC或FandolSong-Regular。无需访问外网。

验证包括A4、摘要限字、页眉、8图8表13文献、关键数值、引用/缺字/溢出、矢量图与冻结数据SHA256，不是新的安全验证。

相对v15：原理图、器件/BOM、PCB、固件、动力学、控制等效、环境输入与数值结果均不变。
