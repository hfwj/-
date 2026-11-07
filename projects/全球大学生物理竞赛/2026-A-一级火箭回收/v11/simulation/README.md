# 论文初版生成与核查

本版整合已有数据，不新增真实姿态/接触仿真。默认队号为TBA。

```bash
cd simulation
pip install -r requirements.txt
MPLCONFIGDIR=/tmp/upc_matplotlib OPENBLAS_NUM_THREADS=1 python prepare.py
python build_paper.py --team TBA
python build_guide.py
python validate_paper.py
```

外部工具需Pandoc、XeLaTeX、DejaVu Serif/Mono字体和Noto Serif CJK SC；中文导读PDF/Word预览可用LibreOffice。无需xeCJK：英文PDF只对精确中文提问局部切换fontspec字体。工具版本见../results/logs/environment.json。

build_paper.py读取Pandoc原生默认reference.docx，再设置匿名页眉、字体、单元格宽度与重复表头，保留原生Compact/Table等样式。不要用缺少这些样式的空白Word模板替换；已实测跨软件预览会破坏表格排版。Word有132个原生数学对象和4张嵌入图；可编辑Word与排版PDF正文相同，分页可不同。PDF为20页，Word预览为17页，不强求分页一致。

PDF由Markdown→Pandoc→XeLaTeX两遍生成；Word使用相同Markdown和Lua表宽配置。输入模板为templates/paper_en.md，生成的正文是../reports/UPC_2026_A_Paper_Draft01_EN.md。例如--team 115会更新每页队号，初稿文件名仍带Draft01；实际提交前还须按官网另命名为115A.pdf。修改队号后按实际参数运行验证；默认出版状态仍有完整AI记录和完整物理安全验证缺口，修改队号不代表这些缺口已消除。

validate_paper.py检查220词摘要、PDF每页队号、首页边界、11节/4图/9表/12参考文献、Word公式和图片、无缺字/溢出、名义质量账与历史输入哈希。它不是完整参赛合规证书或新物理验收器。匿名仅针对论文正文/元数据；研究复现整包含历史文件，不能当作可直接提交的匿名参赛附件。

资料包保留同级v8/v9/v10（不嵌套各自downloads）、v5被动诊断CSV与v4安全CSV，以便读取完整证据和核对历史哈希。历史模型的复跑说明见各自simulation目录。若需要重新计算历史数据，请在临时复制目录进行；本版prepare只读原始输入。

本轮精确提问和披露缺口在../references/AI_usage_record_partial.json。完整历史AI输出须由实际会话导出后补入论文文末，不能从本包重构后冒充逐字原文。

影响基线69d48515bd0243a1272908b73655c95d971e264f：仅论文/图表/编排和核查代码新增；旧物理模型/输入以及原理图、器件/BOM/PCB、固件和旧电子模型不改。
