# v14：上传论文Draft02的文字核定与Draft03修订

比较基线是用户上传的TBA_A_Draft02.docx，保留三台虚拟发动机/无风模型的149.30 t条件性结果，没有替换成v13七发动机/假设风的140 t结果。本次不重算物理模型。

- [修订净稿 Word](reports/TBA_A_Draft03_TextRevised.docx) · [PDF](reports/TBA_A_Draft03_TextRevised.pdf)
- [黄色标注稿 Word](reports/TBA_A_Draft03_TextMarked.docx)：黄色为整段/单元格改写，不是Word修订模式。
- [中文主要修改说明](reports/文字核定与主要修改说明.docx) · [Markdown](reports/文字核定与主要修改说明.md)
- [112条原文/改文记录](results/data/text_changes.json) · [完整下载包](downloads/UPC_A_Draft03_TextReview.zip)
- [原稿存档](references/TBA_A_Draft02_original.docx) · [已有数值证据快照](references/numerical_evidence_snapshot.json) · [保留验证](results/data/editorial_validation.json)

正文由6376词减为5582词，摘要220词。重点修正积分器差异不等式、过强认证/创新措辞、重力/角动量解释、CG代理终点与真实触地混用；补清混合网格比较、姿态必要条件及几何坐标定义；压缩重复论述、纠正IPOPT题名。16个数学对象与4个图片文件逐项校验不变，9张表保留。摘要独立成页，队号TBA仍为占位，完整AI逐字记录未补齐。

复现编辑：`python simulation/revise_manuscript.py`；PDF用LibreOffice导出。需要Python3、python-docx。此版本不包含新轨迹、新控制器或M1安全通过结论。

原理图连接/管脚/器件值、器件/BOM、PCB、固件无变更；模型、控制等效和计算输入无变更，仅文稿和审阅材料修订。旧版本不覆盖。
