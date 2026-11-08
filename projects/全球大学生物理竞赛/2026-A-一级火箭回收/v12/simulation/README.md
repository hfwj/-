# Draft 02 图文增强复现

```bash
cd simulation
pip install -r requirements.txt
MPLCONFIGDIR=/tmp/upc_matplotlib OPENBLAS_NUM_THREADS=1 python prepare.py
OPENBLAS_NUM_THREADS=1 python replay_sensitivity.py
MPLCONFIGDIR=/tmp/upc_matplotlib OPENBLAS_NUM_THREADS=1 python add_figures.py
python build_paper.py --team TBA
python build_guide.py
python validate_figures.py
python validate_paper.py
python package.py
```

prepare生成原4图与证据；replay_sensitivity只读v8控制，调用未改变的v9模型，将标称与9例轨迹写入本版results/data/sensitivity，逐例与原v9末状态/事件核对。没有重优化、反馈或在事件后外推。add_figures生成5张新增主图和一张全程敏感性补图；主文敏感性图仅显示t≥180s的末段，保留CG参考高度与真实脚接触的区别。

build_paper采用原生Pandoc Word样式和9幅图，正文主图顺序为：任务/几何、工作流、被动、响应、轨迹、控制、敏感性、姿态、接触。PDF24页；Word跨软件预览可有不同分页。公式、表格和匿名页眉可编辑。可用--team实际队号重建页眉；初稿文件名仍带Draft02，真正提交前另按规则命名，并补齐完整AI记录。

需Python3.12、requirements.txt依赖、Pandoc、XeLaTeX和DejaVu/Noto Serif CJK SC字体；中文导读PDF或Word预览用LibreOffice。英文PDF用fontspec局部显示原始中文AI提问，不要求xeCJK。图PDF为Matplotlib矢量导出，正文嵌入高分辨率PNG。

validate_figures核对9例真实事件/CSV、被动终点、原节流响应及几何尺寸，validate_paper核对220词摘要、9图9表、12参考文献、Word数学对象与每页队号、无溢出/缺字、历史v8–v11哈希。这些不是实际安全或完整参赛合规证书。

资料包包括v8/v9/v10/v11的必要历史完整文件（各自downloads除外）、v5/passive_cases.csv及passive_profiles.csv和v4安全表。可独立解压核查；研究历史文件不等同匿名参赛附件。旧模型重跑请在临时副本进行；本次只读旧数据。

影响对照v11提交17c2b9：新增同模型回放导出与图文，无动力学/控制节点改变，无原理图/器件/BOM/PCB/固件或旧电子模型改动。M1仍仅有必要条件与讨论，未运行一个成功刚体/接触解。
