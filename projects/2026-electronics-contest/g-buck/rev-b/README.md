# G题模拟充电装置 · 同步 Buck Rev B

依据用户提供的完整原理图 PDF、试题 DOCX 和物料清单 DOCX，重建开关电路模型并执行验证。

## 下载与阅读

- [按原始原理图逐元件绘制Multisim电路](simulation/multisim14/original-schematic/README.md)：7页绘制参考、96项元件选择、逐引脚及逐网络接线表。
- [原图逐元件绘制PDF](simulation/multisim14/original-schematic/原始原理图_Multisim逐元件绘制参考.pdf) · [专用资料ZIP](downloads/Multisim14_按原图逐元件绘制资料包.zip)：供本机手工绘制，未生成原生.ms14文件。
- [NI Multisim 14.0仿真电路搭建说明](simulation/multisim14/README.md)：4页接线图、导入模型和9个测试工况；不是原生`.ms14`工程。
- [元器件向导逐页详细操作](simulation/multisim14/元器件向导逐页操作.md)：逐页填写、17脚映射、保存与首次运行。
- [Multisim电路交付与交叉核验说明](reports/Multisim14_仿真电路交付与核验说明.md)：当前模型9个工况的结果和未验证范围。
- [Multisim 14.0接线图PDF](simulation/multisim14/diagrams/Multisim14_仿真电路接线图.pdf)
- [Multisim 14.0专用搭建包ZIP](downloads/Multisim14_仿真电路搭建包.zip)
- [原理图可行性与题意符合性审查](reports/原理图可行性与题意符合性审查.md)：逐项判断，重点说明控制、瞬时限流、效率和显示要求。
- [仿真报告 PDF](reports/G题_RevB_仿真验证报告.pdf)
- [可编辑报告 DOCX](reports/G题_RevB_仿真验证报告.docx)
- [在线阅读报告 Markdown](reports/G题_RevB_仿真验证报告.md)
- [轻量完整资料包 ZIP](downloads/G题_RevB_仿真验证资料.zip)：报告、源文件、模型、汇总数据、图表及日志，不包含体积较大的 NPZ 波形。

GitHub 文件页面使用 **Download raw file** 下载文件。所有 NPZ 压缩波形另保存在 `results/data/`，可随整个仓库下载。

## 已得到的结果及边界

- 22项瞬态仿真、2组参考/比较极性DC扫描；另核对16种理想锁存逻辑组合。
- 在明确假设的连续双环控制下，恒压约10V；25V输入、8Ω/5Ω负载约0.996A/0.997A。
- 负载阶跃中瞬时负载电流约1.59A，不能认定全过程不超过1A。
- 总效率≥85%未确认；25V/8Ω点尚未计入的辅助及开关/磁芯/温升损耗预算约0.85W。
- 用户没有提供STM32固件、原生EDA工程或厂家功率器件模型。上述结果不构成实际固件、真实器件时序、PCB检查或整机测试通过。

## 分类入口

| 分类 | 路径 | 内容 |
|---|---|---|
| 原始资料 | [references/](references/) | 原理图、试题、物料清单、SHA256及提取文字 |
| 报告 | [reports/](reports/) | PDF、DOCX、Markdown |
| 仿真 | [simulation/](simulation/) | Python脚本、SPICE网表、依赖、安装脚本 |
| 数据 | [results/data/](results/data/) | CSV、JSON、NPZ及DC扫描数据 |
| 图表 | [results/figures/](results/figures/) | 稳态纹波、动态波形、短路、效率预算 |
| 日志 | [results/logs/](results/logs/) | 每个已归档工况的ngspice输出 |
| 压缩包 | [downloads/](downloads/) | 便于下载的轻量资料包 |

## 重跑

详见 [simulation/README.md](simulation/README.md)。代码按当前位置生成网表和输出路径；迁移后先用Python脚本重新生成，不要直接依赖归档网表中的旧绝对路径。

此次发布保留已完成仿真的数据，只调整目录和输出路径。归档后重新验证参考网络、代表性25V/8Ω工况及报告生成，结果见 [publication_checks.json](results/data/publication_checks.json)。
