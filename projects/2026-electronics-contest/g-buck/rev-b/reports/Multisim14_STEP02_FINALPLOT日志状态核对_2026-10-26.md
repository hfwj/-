# FINALPLOT：非增量记录已生效，100ms结束状态待确认

2026-10-26（Asia/Shanghai）。用户上传“报错5.log”，随后明确回复**“没图像生成”**，未另确认本次运行是否结束及新F1状态。该日志并未记录错误；核查确认非增量记录已生效，但内容停在Gmin完成信息，不能据此认定100ms已完成或前次Unknown name已彻底解决。本轮先保留现有FINALPLOT工程，不再叠加模型或求解改值，也不立即要求重跑。

## 本次实际配置与日志边界

[原始日志逐字节归档](../simulation/multisim14/native-project-check/step02-5r-convergence/results/logs/2026-10-26_native_U3_100ms_FINALPLOT_status.log)，2668字节。操作头为2026年10月26日17:00:14，标题包含`U3 IIB SMOOTH`、`ABSTOL10nA`、`100ms FINALPLOT record90-100ms 4ch`。

| 检查 | 日志证据 |
|---|---|
| 结束时间/报告起点 | TSTOP=.1、TSTART=.09s |
| TSTEP/TMAX | 都为50ns |
| 保存变量 | `$iout_raw $vdda $vout @rrs_out[i]` |
| 求解选项 | ABSTOL10nA、RELTOL=.001、ITL4=300、梯形，与基线相同 |
| 非增量模式 | 明确写“已保存了分析得出的变量，供以后处理” |
| 原生绘图命令 | `iplot`和`iplotExt`命令已消失 |
| 结果写出命令 | `write-and-destroy-iplot`仍存在；其名称本身不表示增量绘图仍启用 |
| 来自分析的输出 | 两条源的no DC value提示、Starting dynamic Gmin stepping、Dynamic Gmin stepping completed |
| 错误 | 此快照未出现Unknown name、Timestep too small、Simulation canceled或insufficient memory |

`v_saw:xctrl`和`v_ss:xctrl`的no DC value提示说明DC工作点使用其t=0值；这两行不等于瞬态失败。Gmin完成只表明初始化步骤结束，**不等于瞬态已经积分至100ms**。“结果已保存至文件”的日志提示也不是已核验的时间轴。本次没有原始波形或实际末点，不能借助配置中的TSTOP反推实际完成时刻。

本日志比前次短，也没有前次器件/模型表；不据此断言仍在运行、已结束或取消。用户本次已确认没图像生成，但尚未明确是否已结束。上次两次“无曲线、F1未熔断”只对应上次LOWMEM运行，不自动挪用其F1状态到本次。

## 曲线显示及下一步

上一轮将关闭增量绘图描述为“结束后检查曲线”不够明确；本次原生日志明确该模式是**保存变量供以后处理**，不会保证自动创建所需图页。因此无自动曲线本身不能判失败，也不能仅因空图继续改容差或芯片模型。

先查看本次运行是否已结束。若仍在运行，等结束再读取状态，不重复启动分析；若已结束，先打开后处理器（Postprocessor），选择这次FINALPLOT分析的保存结果，查看实际可用变量及时间范围，再从列表选择IOUT_RAW、VDDA、VOUT、I(RS_OUT)绘图。使用数据集中的实际变量名，不凭旧图页手工套入名称；本次F1状态留待新的明确反馈，不重复挪用旧确认。

若保存结果可用且时间轴覆盖90–100ms，再核对末段四路数值并记录完成；若无数据集、无变量或再次报Unknown name，先保留当前日志/结果状态再定位。此时不把缺少自动图页等同于零输出，不要求重新打包旧GRA。若只有本次快照，也不预判哪项假设已修复。

当前沿用[现有FINALPLOT工程](../downloads/GBUCK_STEP02_5R_U3_IIB_SMOOTH_100ms_4CH_FINALPLOT.ms14)，SHA256 `bb5e5a09aa25b448573ae665544edaeed4dc9c56ceef1f22e0d85819b4256a6f`，没有发放更多变体。前次[变量名错误与绘图对照](Multisim14_STEP02_100ms输出变量名错误与非增量绘图对照_2026-10-26.md)保留两次失败记录；此前30ms通过仍为用户报告的通过，100ms尚未确认。

## 修改影响与复核

比较基线为现有FINALPLOT副本。本轮只归档日志、生成状态审计、更新说明：**原理图拓扑/接线/引脚/元件值/布局、实物器件/BOM/额定值/封装/PCB均不改**。仿真工程、已有U2/U4/U3偏置平滑、MOS/驱动/控制模板、刺激、求解选项、时间窗口和输出选择也没有修改；未接入离散比较器/锁存，未改固件。

`audit_u3_finalplot_status.py`核对保存列表、TRAN命令、选项、绘图命令变化及日志边界，[审计结果](../simulation/multisim14/native-project-check/step02-5r-convergence/results/data/2026-10-26_native_U3_100ms_FINALPLOT_status.json)保留未确认字段。脚本对日志快照的检查不等同本机瞬态完成验证。
