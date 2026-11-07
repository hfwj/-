# 2026 UPC A：无推力弹道、船位与燃料参照增补 · v5

将桥段作为§3.2–§3.4放在原§4（变质量）之前；保留原后续节序并连续重排表号。

- [全文Word](reports/2026_UPC_A题_量级分析_弹道与燃料参照增补版.docx) · [全文PDF](reports/2026_UPC_A题_量级分析_弹道与燃料参照增补版.pdf) · [在线全文](reports/量级分析_弹道与燃料参照增补版.md)
- [独立插入页Word](reports/2026_UPC_A题_无推力弹道与燃料参照_插入页.docx) · [PDF](reports/2026_UPC_A题_无推力弹道与燃料参照_插入页.pdf) · [在线桥段](reports/无推力弹道与燃料参照_插入页.md)
- [核算说明](reports/增补与核算说明.md) · [草稿核对表](results/data/draft_review.csv)
- [弹道汇总JSON](results/data/bridge_summary.json) · [被动工况CSV](results/data/passive_cases.csv) · [首次50 kPa状态](results/data/first_q50_crossings.csv)
- [恒推力变质量代数参照](results/data/coupled_vertical_reference.csv) · [核对日志](results/logs/passive_checks.json) · [运行方法](simulation/README.md)
- [完整资料包](downloads/UPC_2026_A_v5_弹道桥段增补.zip)

130 t参考工况复现Cd=0.5约134.4 s/202.0 km/607.8 m/s、Cd=1约147.4 s/198.5 km/295.8 m/s。到地表仍有切向速度，且q峰值超50 kPa H目标；这些是无控碰撞诊断，不是真实落地方案。

91.1 t不是需求上界；32.5–73.1 t只是人为给定Δv_T后的条件换算。131 t固定质量约64.5 s制动的例子需约45.2 t耗剂，与初始仅1 t燃料不自洽。船位自由的节省效果需在同一约束下比较受控方案。

相对基线`5471910`新增独立v5。仅无推力常质量积分与代数参照，不恢复此前停止的受控正向模型开发；不做燃料最优解。v1–v4/B题、原理图/器件/BOM/PCB/固件与旧电子模型保持原样。
