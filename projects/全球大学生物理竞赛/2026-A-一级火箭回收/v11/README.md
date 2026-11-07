# A题v11：最终论文初版 Draft 01

**完整英文研究初稿已写成：20页PDF、220词摘要、11节正文、4图、9表、12项参考文献、两个技术附录和文末AI使用报告。**附中文摘要/审阅说明，方便修改。

[英文PDF](reports/TBA_A_Draft01.pdf) · [可编辑Word](reports/UPC_2026_A_Paper_Draft01_EN.docx) · [英文Markdown](reports/UPC_2026_A_Paper_Draft01_EN.md) · [中文审阅说明PDF](reports/论文初版_中文审阅说明.pdf) · [中文说明Word](reports/论文初版_中文审阅说明.docx) · [整套论文与复现资料](downloads/UPC_2026_A_v11_论文初版与复现资料.zip)

论文标题：*A Conditional Propellant Estimate for Shipboard Booster Recovery: Trajectory Optimization, Attitude Feasibility, and Safety Limits*。

主结论：水平分离、恒Cd=0.5、Isp=320s和虚拟发动机等假设下，得到初始总推进剂约149t、消耗约148t的名义M0候选。独立验证支持平动数值结果；保持原轨迹需至少24.8°净推力相对箭体偏转，能力未知，9个固定开环扰动未按计划通过。论文据此提出条件性估计与完整安全验收框架，没有把候选改写成安全着陆或全局最低燃料。

正文依次说明：题目解释、假设/符号、量级/被动诊断、变质量模型、受约束搜索、名义结果、独立验证/扰动、姿态、脚端/包络/接触后安全、局限与结论。附录保留计算可追溯性和18类/19条安全矩阵。

队号当前为TBA；官网要求英文及每页队号，并要求AI写作披露精确查询与完整输出。本稿如实记录本轮提问及历史输出缺口，**完整AI记录尚未附入，不能标记为可直接提交**。完整M1、闭环和真实接触/热结构安全也未证明。见[官网规则](https://university-physics-competition.com/contest-rules)、[格式核对](references/competition_format_notes.md)、[AI记录状态](references/AI_usage_record_partial.json)。

[文稿核查记录](results/logs/manuscript_checks.json) · [Word跨软件预览](results/logs/word_preview_checks.json) · [数据证据快照](results/data/evidence.json) · [来源目录](references/reference_catalog.json) · [生成/修改命令](simulation/README.md)

本版使用已归档计算并生成新图表，未新算一个“成功M1”。历史v8/v9/v10哈希均通过；Word数学为可编辑对象，原生样式兼容性已核查。研究整包含历史信息，不作为直接匿名提交附件。

相对69d48515bd0243a1272908b73655c95d971e264f：仅新增论文/编排代码、图表和索引，不改旧优化/动力学输入；原理图连接/管脚/器件值、器件/BOM/封装、PCB、固件及旧电子模型均不变。
