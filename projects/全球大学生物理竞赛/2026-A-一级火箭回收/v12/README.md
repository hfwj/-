# A题v12：五张科学图补全 · Draft 02

**已补齐建议的5张图，主文由4图增至9图；英文PDF为24页，摘要220词、9表、12项参考文献。**正文引用、图号/图注和中文导读同步更新，v11原稿保留。

[仅下载新增5图PNG/PDF](downloads/UPC_2026_A_v12_5_added_figures.zip) · [新版英文PDF](reports/TBA_A_Draft02.pdf) · [可编辑Word](reports/UPC_2026_A_Paper_Draft02_EN.docx) · [英文Markdown](reports/UPC_2026_A_Paper_Draft02_EN.md) · [中文审阅说明](reports/论文初版_中文审阅说明.pdf) · [论文/全部图/回放CSV与复现包](downloads/UPC_2026_A_v12_论文初版与复现资料.zip)

| 新增图 | 放置章节 | 说明 |
|---|---|---|
| Figure 1 任务时序/几何 | §1 | 分离→滑行→再入燃烧→末段；65m×7m、ℓ=32.5m、b=5m、甲板半宽20m与θ_d/δ，G/H区分；姿态角示意放大 |
| Figure 2 方法工作流 | §2.1 | G/L/H/U分类，M0→CasADi/IPOPT→M1，明确M1尚未完成 |
| Figure 3 干机被动诊断 | §3.1 | 同一130t干机的真空/Cd=0.5/Cd=1.0高度–射程，末段放大与2034/608/296m/s标注 |
| Figure 4 节流响应 | §4.3 | 0.5s延迟、1s爬升至u=1、指数逼近1.1，附实际节流导数限幅 |
| Figure 7 九扰动3×3 | §7.2 | 同模型真实回放，与标称比较；参考接触超速/耗剂耗尽/计划终点未接触分别标记 |

原4张图改为Figure 5/6/8/9；表格编号保持，九扰动表为Table 8。另附[九扰动全程图PDF](results/figures/sensitivity_full_history.pdf)和[10条完整回放CSV](results/data/sensitivity)，主文仅放大180s后的末段，未延长或拟合停机后的轨迹。

五张新增图均提供独立PNG与矢量PDF：[任务几何](results/figures/mission_geometry.pdf)、[工作流](results/figures/method_workflow.pdf)、[被动诊断](results/figures/passive_diagnostics.pdf)、[响应](results/figures/throttle_response.pdf)、[九扰动](results/figures/sensitivity_grid.pdf)。

验证：九例末状态与原v9记录在各自SI分量上差小于0.001，终止事件一致；被动诊断终点、节流曲线和G/H几何核对通过；Word嵌入9图，PDF每页队号、摘要与引用检查通过。见[图形数据检查](results/logs/figure_checks.json)、[文稿检查](results/logs/manuscript_checks.json)、[图号映射](results/data/figure_map.csv)。

本次仅增强已有研究的呈现并导出同模型轨迹，未改变149t候选的条件性结论：完整M1/闭环/实际接触安全仍未验证；队号TBA与完整AI记录缺口继续明确保留。

对照v11（17c2b9）：本次新增图、同模型回放导出、图文编排与核查，不改历史动力学方程、控制节点和原始结果；原理图连接/管脚/器件值、器件/BOM/封装、PCB、固件及旧电子模型无变化。
