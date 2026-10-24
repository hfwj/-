# G题模拟充电装置 · 同步 Buck Rev B

依据用户提供的完整原理图 PDF、试题 DOCX 和物料清单 DOCX，重建开关电路模型并执行验证。

## 下载与阅读

- [STEP01采样接入反馈别名修正](reports/Multisim14_STEP01采样接入_反馈别名修正_2026-10-25.md) · [原生修正版](downloads/GBUCK_STEP01_IL_SENSE_FEEDBACK_FIX.ms14)：仅修正V3反馈节点别名，原接线/器件/Ki20保持；独立30ms完成，用户本机30ms图约6A异常消失。采样关系符合预期，本机按50ns对照指引补图后，VOUT明显平滑，30ms末约9.6～9.7V（目测）且仍缓慢上升；保留50ns，下一步复用结果核对U4采样关系，稳态精度未验收。
- [TI采样模型向导结构修正](simulation/multisim14/ti-sense-wizard-fix/README.md) · [当前导入包](downloads/Multisim14_TI_CurrentSense_WizardFix_2026-10-24.zip)：针对本机multiple top-level .subckt报错，只移动外层.ENDS、嵌套全部依赖；TI模型字节/参数和引脚不变。INA240回归通过，INA181动态仍未完成；本机导入待重试，不改主图/BOM。
- [两款TI采样模型与当前导入步骤](simulation/multisim14/ina181a1-ti-import/README.md) · [组合包](downloads/Multisim14_TI_CurrentSense_Import_2026-10-24.zip)：U2/U4的INA240独立DC/阶跃通过；U3的INA181 DC通过、瞬态未完成，失败记录保留。先导入INA240，均未运行本机Multisim、未改主图/BOM。
- [INA240A1上传TI模型与8脚导入说明](simulation/multisim14/ina240a1-ti-import/README.md) · [导入包](downloads/Multisim14_INA240A1_TI_8PIN_2026-10-24.zip)：原TI模型字节保留，只加7端到8脚接口；独立增益/参考/阶跃对照通过，本机导入待确认，用于U2/U4，U3需另模型；未改现有主图/BOM。
- [逐芯片采样功能模型及导入说明](simulation/multisim14/single-chip-sense/README.md) · [模型包](downloads/Multisim14_Sense_Chip_Functional_2026-10-24.zip)：针对本机库无INA240，提供独立8端INA240/6端INA181功能等效；增益、参考、限幅交叉检查通过，非TI模型，本机导入待确认；未编辑现有主图/BOM。
- [保护重启积分冻结对照](reports/Multisim14_保护重启积分冻结对照_2026-10-24.md) · [20ms原生工程](downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14)：此20ms功能模型对照通过；保留原失败基线，未改实物原图/BOM或真实固件，本机待验证。


- [采样与保护首轮验证](reports/Multisim14_RevB采样与保护首轮验证_2026-10-24.md) · [12ms原生诊断](downloads/GBUCK_REVB_PROT_POS_INJECT_12ms.ms14)：19项独立功能检查符合设定行为；耦合后两路栅极关断有效，但重新ARM触发约1.838A并再次保护，稳定恢复未通过。功能模型非厂商认证，不改板/BOM。
- [Ki20七工况阶段汇总](reports/Ki20_七工况本机功能验证阶段汇总_2026-10-24.md) · [七工程与报告ZIP](downloads/Multisim14_Ki20七工况阶段汇总_2026-10-24.zip)：六静态与自动CV/CC切换均有本机截图，峰顶附近光标1.5690A，距切换约12.48ms观测到0.9999704A回落点；精确过流时长仍未测定，不判为原图整机已通过。
- [Ki20动态切换工程](simulation/multisim14/native-project-check/control-loop/kiv20-dynamic/README.md) · [动态ZIP](downloads/Multisim14_Ki20动态切换工况_2026-10-24.zip)：六静态及180ms动态图已收齐：10V/0.5A→8V/1A→5V/1A自动切换可见，仍有约1.6A瞬态；下一步导出精确数据，原图固件/保护/效率未验证。
- [C版改善后的Ki20静态回归](simulation/multisim14/native-project-check/control-loop/kiv20-regression/README.md) · [工况ZIP](downloads/Multisim14_Ki20静态回归工况_2026-10-24.zip)：C15V空载改善；同参数15V/25V的20Ω均约10V/0.5A，8Ω约8V/1A、5Ω约5V/1A均已收100ms图，六项静态截图已收齐。精确数据与动态仍待验证，不改板上器件。
- [空载C版单参数控制对照](simulation/multisim14/native-project-check/control-loop/open-load-diagnostic/C_README.md)：B截图与A起伏接近，C仅改电压外环Ki100→20；不改原理图和器件，不预称稳定性修复。
- [下一步：空载起伏A/B诊断](simulation/multisim14/native-project-check/control-loop/open-load-diagnostic/README.md) · [独立对照ZIP](downloads/Multisim14_空载起伏_AB对照_2026-10-24.zip)：保持原器件和控制不变，比较RELTOL=0.01与0.003的100ms结果；已做文件结构核对，待本机运行，不是已修复版本。
- [本机工况反馈阶段结论与原题覆盖](reports/Multisim14_本机工况反馈阶段结论_2026-10-24.md)：早期Ki100空载起伏与后续Ki20改善/回归分别记录；不混合不同控制参数的验证结果。原图固件、保护及效率仍未验证。
- 早期Ki100的七工况本机截图覆盖静态恒压/恒流、15V空载及自动切换；空载约11V过冲和切换约1.6A峰值仍需评估。见[控制模型本机反馈记录](simulation/multisim14/native-project-check/control-loop/results/data/native_user_feedback.json)。15V空载回传已接回2A保险丝，真实保护/效率未验证。
- 用户已反馈[CV/CC副本中25V/20Ω恒压工况](simulation/multisim14/native-project-check/control-loop/results/data/native_user_feedback.json)的本机30ms波形：软启动后约10V、峰值约10.4V；其余工况反馈见上方汇总。
- [当前本机工程的软启动与CV/CC控制副本](simulation/multisim14/native-project-check/control-loop/README.md) · [专用ZIP](downloads/Multisim14_软启动与CVCC控制副本_2026-10-24.zip) · [最终测试报告](reports/Multisim14_软启动与CVCC控制仿真_2026-10-24.md)：七个开关交叉工况完成，七工况均已有本机截图，15V空载100ms持续起伏，尚不能确认充分稳定。采用理想控制和采样，保护与效率未验证。
- [保险丝对照后本机20ms结果](reports/Multisim14_保险丝对照后20ms结果_2026-10-24.md)：新图末段约9.2V，持续下降不再可见；仍有约16V启动过冲，尚未通过10V恒压/1A恒流要求。
- [本机20ms输出持续下降排查](reports/Multisim14_本机20ms输出持续下降排查_2026-10-24.md)：用户新图末段约6.7V且仍下降，与交叉结果不同；需核对当前工程、输入母线、自举供电及F1状态，尚未定位。
- [40%开环测试启动振荡排查](reports/Multisim14_40percent开环启动振荡_2026-10-24.md)：用户新图出现约15V峰值与5V谷值，尚未稳定；核对LC周期并给出20ms观察步骤。
- [用户本机5ms启动波形反馈](reports/Multisim14_本机5ms启动波形反馈_2026-10-24.md)：自定义容差启用后，截图显示开关/输出曲线到5ms；仍为10%占空比开环测试，尚未验证10V稳压及1A恒流。
- [PWM首次切换报错：瞬态容差调整说明](reports/Multisim14_PWM首次切换步长过小_2026-10-24.md) · [新的5ms原生工程](downloads/设计1_瞬态容差调整_5ms_待本机验证.ms14)：针对用户本机2.00002ms步长过小，提供仅调整求解设置的副本；交叉验证与本机结果分开记录。
- [用户原生Multisim工程排查与模型修订](simulation/multisim14/native-project-check/README.md)：定位IR2104内嵌模型的3.3V输入兼容问题；提供1ms检查及5ms修订副本，待本机打开/运行确认。
- [1ms原生工程检查副本](downloads/设计1_IR2104模型修订_1ms检查.ms14) · [较早的5ms模型修订副本](downloads/设计1_IR2104模型修订_待本机验证.ms14) · [排查报告](reports/Multisim14_用户工程空白波形排查_2026-10-24.md)。较早5ms副本的本机运行在PWM启动时失败，新求解设置副本见上一条。
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
- 最初报告使用重建模型，未获得STM32固件或原始PCB/EDA工程；后续上传的Multisim工程及其中嵌入模型另行核对、归档。上述结果不构成实际固件、真实器件时序、PCB检查或整机测试通过。

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
