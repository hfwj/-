# 核对 `原理图/G题同步Buck完整原理图_RevC1.pdf` — 评审与仿真

- 日期：2026-10-27
- 对象：`G题同步Buck完整原理图_RevC1.pdf`（10 页：1 页说明 + 9 页引脚增强预览）
- 基准：Rev C 工程 + 上一轮评审 + 平均电流模式仿真
- 结论：**QH/QL 的阻塞项已解除（Rev C.1 明确 2D/3S，连接正确）；仿真 88.0%，85% 有余量。但新增的下游 VIN 监测用了 PA5，和 LCD 的 SPI1_SCK 冲突，必须改到 PA6；U9B 1.10 A 告警的固件判据和 0.1 Ω 短路检测仍需落实。**

## 0. 结论摘要

1. **QH/QL 已正确**：Rev C.1 引脚表明确 QH `1G=G_H、2D=VIN、3S=SW`；QL `1G=G_L、2D=SW、3S=GND`。上一版预览的符号画法容易误读，本版加了脚号，连接正确；QH/QL 不再是阻塞项。
2. **仿真（Rev C.1 功率级与 Rev C 相同）**：
   - 25 kHz：**88.01%**
   - 30 kHz：**88.00%**
   - 20→8 Ω：Iout 峰值 1.244 A；8→5 Ω：1.586 A；IL 峰值约 1.0 A，无 OCP 误触发。
   - 预充：1.11 A 峰值、τ=10.4 ms、5τ≈52 ms、0.142 J；100 ms 足够。
   - 下游 VIN 分压：25 V → 2.273 V（11:1），与说明一致。
3. **新问题（必须改）：J_MON/ADC_VIN_POST 用 PA5，与 LCD 的 SPI1_SCK 冲突。**
   - RevB/RevC 的 LCD 接口：SCK→PA5、MOSI→PA7、CS→PB12、DC→PB13、RST→PB14。
   - Rev C.1 新增 J_MON pin1=ADC_VIN_POST→PA5/ADC；PA5 同时是 SPI1_SCK。**同一脚不能既做 LCD 时钟又做 ADC。**
   - 推荐改到 **PA6/ADC12_IN6**（SPI1_MISO，ST7735 只写不读，PA6 空闲）；或另找空闲 ADC 脚。J_MON 连接器/固件/控制板同步改。
4. **U9B 1.10 A 告警（100 nF 后仍有 3–4 ms 超限）**：
   - C_IOUT_PROT 改成 100 nF（1 k+100 nF≈100 µs）后，20→8 Ω 滤波峰值 1.198 V、>1.10 V 持续 **3.08 ms**；8→5 Ω 峰值 1.514 V、持续 **4.40 ms**。
   - 固件必须用 **10–20 ms 持续判据**，不能单边沿锁存；否则正常跳变会停。
   - **0.1 Ω / 0.01 Ω 短路**：Vout 0.1/0.01 V、Iout 1.0 A，U3 输出 1.0 V，滤波后峰值 1.019/1.021 V，**永远到不了 1.10 V**。U9B 不能检测 1 A 恒流短路；必须用 **VOUT<0.5 V 的软件判据**。Rev C.1 说明里已写“不可仅用 >1.1 A 检测 1 A 恒流短路”，实测仿真确认。
5. **IR2184 SD# 极性仍需实测**：本版未改；pin 2 SD# + 10 k 下拉，若 SD 是低电平关断则默认关断、DRV_EN 高使能，逻辑正确；若实际是高电平关断，DRV_EN 逻辑反。上电前用 DRV_EN=0/3.3 V 确认。
6. **其他改动核对通过**：C_IOUT_PROT 100 nF/C0805、J_CTL.6=IOUT_OC_N/PB11、C_IL_ADC 1 nF、R_VDDA 1 Ω、RS_L 25 mΩ、D1/D_FREE 方向、OCP ±2.2 A、IL/IOUT 独立滤波、U9B 1.10 A 参考、R_SN/C_SN DNP、TP11–14、LCD 模块内部 J1、预充 R_PRE/J_BYP，均正确。

## 1. 仿真结果

模型：`sim/g_buck_model.py` 平均电流模式；Rev C.1 功率级参数：

- IR2184：tr/tf=50/40 ns（1.4/1.8 A、4.7 Ω；47 ns 仍要实测）
- td=400 ns（IR2184 典型）
- D_FREE=SS56：Qrr≈5 nC，死区 Vf≈0.45 V
- D1=SS56：Vf=0.45 V，Rf=0.02 Ω
- aux=0.55 W；fsw=25/30 kHz
- L=220 µH/DCR 55 mΩ、RS_L 25 mΩ、RS_OUT 50 mΩ、Cout 480 µF/ESR 20 mΩ、IRF540N 热态 75 mΩ

| 场景 | 效率 | Vout | Iout |
|---|---:|---:|---:|
| 25 kHz | 88.01% | 7.970 V | 0.996 A |
| 30 kHz | **88.00%** | 7.970 V | 0.996 A |

负载跳变：

| 场景 | Iout 峰值 | IL 峰值 | Vout 变化 | 恢复 | U9B 滤波后 >1.10 V |
|---|---:|---:|---:|---:|---:|
| 20→8 Ω | 1.244 A | 1.020 A | 10→7.97 V | 11.5 ms | **3.08 ms** |
| 8→5 Ω | 1.586 A | 1.006 A | 8→4.99 V | 8.35 ms | **4.40 ms** |

- 100 nF 滤波后峰值：20→8 为 1.198 V；8→5 为 1.514 V。
- **固件 10–20 ms 持续判据可以避开这两个正常跳变；单边沿锁存会误停。**

短路：

| 负载 | Vout | Iout | U3 输出 | 100 nF 后峰值 | >1.10 V? |
|---|---:|---:|---:|---:|---|
| 0.1 Ω | 0.100 V | 1.000 A | 1.000 V | 1.019 V | **否** |
| 0.01 Ω | 0.010 V | 1.000 A | 1.000 V | 1.021 V | **否** |

**结论：U9B 1.10 A 告警对 1 A 恒流短路无效；必须用 VOUT<0.5 V 的软件判据。** Rev C.1 说明已写，仿真确认。

预充：

- I_peak=(25−0.45)/(22+0.17)=**1.11 A**
- τ=22 Ω×471 µF=**10.4 ms**；5τ≈**52 ms**；100 ms 足够
- 能量 0.5×471 µF×24.55²=**0.142 J**；R_PRE 标 0.3 J，有余量
- 下游 VIN 分压：25 V→**2.273 V**（11:1）；1 k+4.7 nF 的 fc≈**3.36 kHz**（分压戴维南 9.09 k+1 k）

## 2. 新问题：PA5 冲突（必须改）

**Rev C.1 新增：**

- VIN→R_VINP_TOP 100 k→VIN_POST_DIV→R_VINP_BOT 10 k→GND
- VIN_POST_DIV→R_VINP_ADC 1 k→ADC_VIN_POST；C_VINP_ADC 4.7 nF；D_ADC6 BAT54S 钳位到 GND/+3V3_A
- J_MON：1=ADC_VIN_POST→**PA5/ADC**，2=GND；TP14

**冲突：**

- RevB/RevC LCD 接口：**SCK→PA5**、MOSI→PA7、CS→PB12、DC→PB13、RST→PB14。
- STM32F103C8T6：PA5=SPI1_SCK/ADC12_IN5；PA6=SPI1_MISO/ADC12_IN6。
- 同一 PA5 不能既做 LCD 时钟又做 VIN_POST ADC。Rev C.1 自己也写了“PA5 必须核实未被控制板其他外设占用”；**它已经被 LCD 占用**。

**建议：**

- 改到 **PA6/ADC12_IN6**（ST7735 只写不读，SPI1_MISO 空闲）；或 PA5 改用别的 LCD 时钟方案（不推荐）。
- J_MON 连接器、控制板走线、固件 ADC 通道、TP14 标注同步改。
- 如果不改，LCD 初始化/刷新时 PA5 的 SPI 时钟会干扰 ADC_VIN_POST；VIN 监测不可用，甚至 LCD 不亮。

## 3. U9B 1.10 A 告警的固件判据

- 硬件：U3 IOUT_RAW（1 V/A）→R_IOUT_PROT 1 k→IOUT_PROT→C_IOUT_PROT 100 nF→GND；U9B pin6=IN_B−；pin5=IN_B+=VREF_IOUT（20 k/10 k，1.1 V）；pin7=IOUT_OC_N（10 k 上拉）→J_CTL.6→PB11/EXTI11。
- 100 nF 把滤波做到约 100 µs，但正常负载跳变的 1.244/1.586 A 仍持续 3–4 ms 超过 1.10 V。
- **固件必须：**
  1. 不要单边沿故障锁存；
  2. 持续 >1.10 V **10–20 ms** 才置告警/锁存；
  3. 与 VOUT<0.5 V 组合判短路；
  4. 8→5 Ω、0.1 Ω、0.01 Ω 台架验证。
- **0.1/0.01 Ω 短路 U9B 不动作**（1.019/1.021 V）；必须靠 VOUT<0.5 V 软件判据。Rev C.1 说明已写，仿真确认。
- 1 A 恒流负载（8 Ω、5 Ω）稳态 1.0 A，低于 1.10 V，不告警；告警只在跳变/过载时出现。

## 4. 已核对通过的点

- **QH/QL**：QH 1G=G_H、2D=VIN、3S=SW；QL 1G=G_L、2D=SW、3S=GND；正确。上一版预览的符号画法（像 P 沟道）不再作为连接依据；本版有脚号。
- **D1**：pin2 A=IN_PRE、pin1 K=V_SHUNT_IN；方向正确。
- **D_FREE**：pin2 A=GND、pin1 K=SW；方向正确。
- **U2/U3/U4**：U2 IN−=VIN、IN+=V_SHUNT_IN；U4 IN−=V_CAP、IN+=L_RAW；U3 IN+=V_CAP、IN−=VOUT；REF 接法正确。
- **IR2184**：1 IN、2 SD#、3 COM、4 LO、5 VCC、6 VS、7 HO、8 VB；与数据手册一致；4.7 Ω 栅极电阻、C_BOOT 1 µF、D_BOOT UF4007、R_GSH/R_GSL 10 k、R_IN_PD/R_SD_PD 10 k，合理。
- **OCP ±2.2 A**：R9=10 k、R10A=49.9 k、R10B=100 Ω；R15A=49.9 k、R15B=100 Ω、R16=10 k，分压正确。
- **IL_PROT/IOUT_PROT**：1 k+1 nF（IL）、1 k+100 nF（IOUT），与 ADC 支路独立。
- **U9B 1.10 A 参考**：20 k/10 k→1.1 V；pin5/6/7、10 k 上拉正确。
- **J_CTL.6**：IOUT_OC_N→PB11/OC#；旧 RevB GND 排线不能沿用，说明已写。
- **C_IOUT_PROT 100 nF/C0805**、C_IL_ADC 1 nF、R_VDDA 1 Ω、RS_L 25 mΩ、R_SN/C_SN DNP、TP11–14、LCD 模块内部 J1，均正确。
- **预充**：R_PRE 22 Ω/5 W/pulse≥0.3 J、J_BYP SPST≥30 VDC/3 A；1.11 A/52 ms/0.142 J，合理。
- **下游 VIN 监测**：100 k/10 k、1 k+4.7 nF、BAT54S、TP14，数值正确；仅 PA5 冲突需改。

## 5. 仍需确认/验证

1. **PA5→PA6**（必须）：J_MON、控制板、固件、TP14 同步改。
2. **IR2184 SD# 极性**：DRV_EN=0/3.3 V 实测；若反，加反相或改逻辑。
3. **U9B 1.10 A 固件判据**：10–20 ms 持续 + VOUT<0.5 V；8→5 Ω、0.1 Ω、0.01 Ω 台架。
4. **5 V/12 V 模块**：25 V 输入下实测输入功率；必须开关型；否则 88.0% 不保。
5. **IR2184 实际栅极边沿**：50/40 ns 是估计；示波器测 G_H/G_L；47 ns 不能用名义电流证明。
6. **输出电流 1.59 A**：说明已承认不是硬限流；若测试按瞬态“最大 1 A”，仍需输出串联限流；先确认测试口径。
7. **EDA ERC/DRC**：本 PDF 是原生记录增强预览；要用 `.eprj2` 跑 ERC/PCB DRC；`.eprj2` 不在当前文件夹。
8. **D1/aux 升级**：D1 理想 +1.5 点、aux 0.45 +1.0 点；88.0 已够，可不做。

## 6. 结论与下一步

- **Rev C.1 的功率级/QH/QL/D1/D_FREE/OCP/预充都正确；仿真 88.0% 过 85%。**
- **唯一新增的硬冲突是 PA5：J_MON/ADC_VIN_POST 必须改到 PA6（或其它空闲 ADC）。**
- **U9B 1.10 A 只能做告警，不能检测 1 A 恒流短路；固件必须用 VOUT<0.5 V + 持续判据。**
- **IR2184 SD# 极性必须实测；5 V 模块必须开关型并实测。**
- 下一步：改 PA5→PA6；加 VIN_POST 的 ADC 通道/标定；写 U9B/短路固件；测 aux/栅极/效率；跑 `.eprj2` ERC/DRC；然后功率核心板。**PA5 未改前不要投板。**

## 7. 文件

- 仿真脚本：`sim/check_revc1.py`
- 仿真结果：`sim/results/revc1_summary.csv`
- 上一版评审：`analysis/RevC_gpt2_review.md`
- 修改清单：`analysis/修改意见清单_RevC.docx/.pdf`
- 原始对象：`原理图/G题同步Buck完整原理图_RevC1.pdf`
