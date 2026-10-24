# 当前本机工程的软启动与CV/CC功能控制副本

来源：用户再次上传、已在本机运行过的[保险丝对照基线](../../../../references/user-projects/2026-10-24_本机可运行_保险丝对照.ms14)。原文件逐字节保留，SHA256为`5995f248b7683502ee6412937513adcecad85427633854a410c8173c6f2a7050`。

后续本机反馈：用户已运行`CV_25V_20R`到30ms，截图显示软启动及末段约10V、峰值约10.4V，与该工况交叉结果接近。见[截图观察记录](results/data/native_user_feedback.json)。其余五个工况仍待本机反馈；以下自动验证资料继续保留其ngspice来源。

这组副本保留用户功率级和驱动，替换V3的仿真SPICE模板，加入理想软启动、电压外环、电感平均电流内环和PWM。它是控制功能测试模型，不是原图中STM32程序，也没有补齐INA采样芯片、故障锁存和实物保护的验证。

## 先在本机运行

1. 下载[专用ZIP](../../../../downloads/Multisim14_软启动与CVCC控制副本_2026-10-24.zip)，解压到例如`C:\Multisim\G_Buck_CTRL\`。在Multisim用“文件→打开”打开其中`downloads/`的`.ms14`，不经过元器件向导。
2. 首先运行[25V/20Ω恒压副本](../../../../downloads/GBUCK_CTRL_EQ_CV_25V_20R_native_check.ms14)。其瞬态时长为30ms、最大步长50ns、初始化为直流工作点；沿用当前工程已能运行的自定义分析选项。
3. 观察VOUT是否随参考缓升并在末段接近10V；保留本次完整报错或波形。这些新副本尚未在本环境启动Windows Multisim，本机仍需确认。
4. 再依次运行8Ω、5Ω副本。恒流时分别应接近8V/1A、5V/1A，不能以两个工况都输出10V作为目标。CC文件预选VOUT和RS_OUT电流；需要看清电流时，可在图示仪中暂时隐藏VOUT。
5. 最后运行自动负载变化副本。18～18.1ms在20Ω→8Ω之间变化，28～28.1ms在8Ω→5Ω之间变化，分析到45ms。两个过渡均为100us，不宣称瞬时硬切换或负载电流全过程不超过1A。

| 副本 | 输入/负载 | 时长 | 用途 |
|---|---|---|---|
| [CV_25V_20R](../../../../downloads/GBUCK_CTRL_EQ_CV_25V_20R_native_check.ms14) | 25V、20Ω | 30ms | 首次恒压/软启动检查 |
| [CC_25V_8R](../../../../downloads/GBUCK_CTRL_EQ_CC_25V_8R_native_check.ms14) | 25V、8Ω | 30ms | 约1A恒流 |
| [CC_25V_5R](../../../../downloads/GBUCK_CTRL_EQ_CC_25V_5R_native_check.ms14) | 25V、5Ω | 30ms | 约1A恒流 |
| [CV_15V_20R](../../../../downloads/GBUCK_CTRL_EQ_CV_15V_20R_native_check.ms14) | 15V、20Ω | 30ms | 输入低端恒压 |
| [CV_25V_OPEN](../../../../downloads/GBUCK_CTRL_EQ_CV_25V_OPEN_native_check.ms14) | 25V、RL=1GΩ，保留2.2kΩ泄放 | 30ms | 外部空载 |
| [AUTO_20R_8R_5R](../../../../downloads/GBUCK_CTRL_EQ_AUTO_20R_8R_5R_native_check.ms14) | 25V、20Ω→8Ω→5Ω | 45ms | 同一控制器自动转入限流 |

## 模型及画布上的变化

- V3的SPICE模板改为`GBUCK_CTRL_EQ`控制器调用，包含全部所需控制模型。原来的固定4us脉宽不再决定闭环PWM，V3原脉冲参数的缓存数值显示已隐藏。画布仍沿用原V3源符号，不把它当成新增实物芯片或完整控制电路画法。
- 反馈在该仿真模板中引用当前工程的VOUT、网络3（电容侧）、网络2（RS_L输入侧）、网络7（VIN）。没有新增物理反馈导线，亦不宣称原图的ADC和控制线路已经逐元件仿真。后续若重连电路或重新编号网络，必须重新核对这些引用。
- Q1/Q2、L/C、采样电阻、驱动、自举和四份嵌入器件模型保持当前源文件内容。电源及RL仅按各测试工况改变；自动负载文件将RL的仿真模板改为受控负载，隐藏其旧固定阻值显示。
- F1仍与基线一样两端断开，R1=1mΩ仍接通输入；这是前一轮对照状态，不能当作原2A保险丝或保护链已验证。当前副本不用于验收真实保险丝动作。
- 用户保存后的自定义选择已确认：活动TRAN中`MSM_ASYS_OPT=0`，这组副本保留该选择，不再仅保存局部容差数值。

控制模型的信号关系如下：

```mermaid
flowchart LR
  SS[2ms后参考0到10V缓升] --> VP[电压PI外环]
  VO[VOUT理想采样] --> VP
  VP --> LIM[电感电流指令限幅]
  LIM --> IP[电流PI内环]
  IL[RS_L压差理想采样与滤波] --> IP
  IP --> PWM[100kHz PWM]
  PWM --> IR[原IR2104修订模型]
  IR --> POWER[原同步Buck功率级]
  POWER --> VO
  POWER --> IL
```

## 控制参数和明确假设

| 参数 | 设置 |
|---|---|
| 参考软启动 | 0～2ms为0V，2～12ms由0升至10V |
| 电压外环 | Kp=0.4 A/V、Ki=100 A/(V·s) |
| 电流内环 | Kp=0.04 duty/A、Ki=50 duty/(A·s) |
| 积分抗饱和回算 | 两环均为1000 s⁻¹ |
| 电感电流理想测量 | `V(2,3)/0.025Ω`，10us一阶滤波 |
| 电流指令范围 | −0.15～1A |
| PWM | 100kHz、0/3.3V、占空比0～0.9；有限斜率比较器 |
| 输出电流观察 | RS_OUT压差/0.05Ω，包含其后泄放支路电流 |

轻载回调采用强制连续导通的同步控制假设，允许短时负电感电流指令至−0.15A。它不是给真实电池定义充放电策略；实际固件是否允许反向电流、如何防反灌仍需另行设计。1A限制针对电感平均电流指令，稳态对应输出约1A，不是对每个开关周期峰值或负载突变瞬间的硬限制。

电压和电流采样在控制模型中是理想值，未加入INA误差、ADC量化/采样延迟或数字控制周期。IR2104仍为此前为3.3V兼容而修改的输入模型；全部求解容差仍用于功能排查，不能据此计算真实开关损耗或精确应力。

## 验证资料和复现

[最终开关验证汇总](results/data/verification_summary.json)、[原生副本结构核验](results/data/native_build_checks.json)、[工作基线检查](results/data/working_source_inspection.json)、[六工况波形](results/figures/closed_loop_overview.png)。只有汇总中`full_transient_completed`和`steady_target_passed`均为真的工况才计为通过；交叉验证使用ngspice44.2，不冒充Multisim本机运行。

在本目录运行，依赖见上一级`requirements.txt`：

```bash
python build_projects.py
python verify_projects.py
python make_delivery.py
```

提取出的网表逐项核对实际输入和负载，且检查全部原器件模型正文仍在，防止顶层RL与MOSFET内部同名RL混淆。原生容器已用两种DCL解压实现回读。完整时间范围保留降采样CSV，峰值附近/末段/负载变化附近另存完整分辨率NPZ窗口；NPZ的`columns`字段给出列顺序。ZIP为轻量交付，不含这些NPZ窗口，它们留在GitHub目录。

本次可以检查控制功能、给定工况稳态和启动响应；尚不能认定原图整体、实际STM32固件、传感器、故障锁存、真实2A保险丝、显示、总效率或硬件安全运行通过。
