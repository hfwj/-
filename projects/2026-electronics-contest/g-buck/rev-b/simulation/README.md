# G题 Rev B：PDF重建的电路仿真

使用NI Multisim 14.0时，见 [multisim14/README.md](multisim14/README.md)。其中的驱动、自举、辅助功耗和采样控制模型独立于本目录原始ngspice模型，结果与原报告分别归档，不能混用或视为真实芯片模型。

本模型来自用户提供的原理图PDF、G题DOCX和B3/Rev B物料清单，没有原生EDA工程、STM32程序或厂家晶体管模型。它验证功率拓扑与明确假设的控制方案，不是整机实测，也不是原有固件验证。图纸中的“已完成B.1仿真”属于附件陈述，本次未取得其源文件，因此未作为验证证据。

## 运行

在项目的simulation目录执行（例如从仓库根目录运行 `cd projects/2026-electronics-contest/g-buck/rev-b/simulation`）：

```bash
bash setup_ngspice.sh /workspace/tools/ngspice
python -m pip install -r requirements.txt
export NGSPICE=/workspace/tools/ngspice/usr/bin/ngspice
export MPLCONFIGDIR=/tmp/buck-mpl
python simulate.py
python protection.py
python supplementary.py
python make_report.py
```

ngspice也可以使用系统已安装版本，通过NGSPICE指定程序路径。下载脚本仅支持兼容Debian trixie的amd64环境。Python脚本自动生成当前目录对应的绝对输出路径；移机后应重生成网表。所有仿真资料按项目目录归档，没有修改用户提供的原理图和物料清单。

## 目录

- `../references/`：原理图、物料清单、试题与来源校验。
- `../reports/`：PDF、DOCX、Markdown报告。
- `netlists/`：PDF重建的SPICE网表。
- `../results/data/`：JSON/CSV数值和NPZ波形数据。
- `../results/figures/`：波形图片。
- `../results/logs/`：各次ngspice求解日志。
- `../downloads/`：便于下载的轻量资料包。

## 取自PDF并与BOM一致的参数

- L1=220µH，DCR取允许上限0.15Ω；Isat≥3A、Irms≥1.5A仅作结果对照，模型不含饱和。
- C1/C2=470µF/1µF；C3/C4=470µF/10µF。
- RS_IN/RS_OUT=50mΩ；RS_L=25mΩ；R_BL=2.2kΩ。
- 输入、输出电压11:1分压；INA240A1/INA181A1标称增益20。
- 正负电感过流±1.8A，输出过压11V；故障锁存，关闭上下管。

## 必须保留的模型假设

- PWM默认为100kHz，另检查50/150kHz；并非图纸或固件已指定的频率。
- MOSFET由44mΩ双向受控电阻和近似体二极管代替，**不是IRF540NPbF厂家SPICE模型**；控制电压0/1V不代表真实VGS。
- 死区520ns、控制信号RC=47ns、C3 ESR=80mΩ、保险丝/接触等效20mΩ均为假设；C4理想电容，未建模DC偏压降容。
- 近似SS56：Is=2µA、N=1.4、Rs=25mΩ；体二极管：Is=1nA、N=1.5、Rs=30mΩ。未声称对应实际厂商模型。
- 输入有D1单向隔离，反馈吸收能量只能暂存在输入电容，不允许假定输入台式电源可吸收反向电流。
- 拟议连续双环：电压PI Kp=0.5 A/V、Ki=50 A/(V·s)；内环电感电流PI Kp=0.15 duty/A、Ki=200 duty/(A·s)，含Vcap/Vin前馈；回算抗饱和500/s与1000/s。
- 外环电感电流目标限制−0.3至1A（允许有限主动放电），占空比命令0.08～0.88。空载模式若禁止负电流，应另设计跳脉冲/受控泄放及积分处理，不能直接套用本模型。
- 1ms低侧预充，10ms电压目标斜坡，预充结束至10ms加入C·dV/dt=0.48A前馈。未建模12V轨上升、驱动器UVLO、自举VB−VS、驱动能力、Qgd、Coss、寄生电感及温升。
- 电感ADC反馈用1kΩ/4.7nF滤波近似。其余ADC量、采样保持和STM32离散执行未接入控制模型。
- 硬件保护用标称门限、0.4µs电感采样RC与1.3µs比较输出RC近似，再通过积分状态锁存。**RC时间常数不是厂家保证的传播延迟**。没有MCU软件短路锁存，不能声称该功能已通过。
- DC扫描独立验证参考电阻网络与比较极性；HC74/HC08仅验证理想逻辑真值表，不是实际芯片时序验证。上电POR电源斜率、ARM竞争、UVLO及重启时序未验证。

## 测量口径

主要结果为末5ms时间加权均值和RMS。空载用1TΩ近似外部断开，板载泄放/分压仍保留。负载电流只计外部负载；内部1A电感限流包含约0.5%的泄放及分压电流。40ms主矩阵之外，关键CV工况延长至80ms检查收敛。窗口峰峰值包含残余控制包络，不应全部解读成开关纹波。

功率级Pin取外部输入源−V·I的时间均值，包含已建模二极管/导通/电阻/电容ESR损耗，不含辅助模块、显示、核心板、真实栅极充放电、开关交叠、Coss和磁芯损耗。输入电容暂态充放电可能影响短窗口输入功率，因此总效率必须另计预算并实测。动态工况的单一负载功率汇总不适用，详见专用动态分析。

报告逐项区分条件通过、未验证与模型风险。不能凭此资料宣布PCB可投板或直接连接真实电池。
