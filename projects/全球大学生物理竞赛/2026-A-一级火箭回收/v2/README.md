# 2026 UPC A：模型假设与安全判据 · v2

在[v1参数资料](../v1/README.md)基础上确定参考方案，提供13项假设和18项判据。

- [Word文档](reports/2026_UPC_A题_模型假设与安全判据.docx) · [PDF阅读版](reports/2026_UPC_A题_模型假设与安全判据.pdf) · [在线阅读](reports/模型假设与安全判据.md)
- [模型假设CSV](results/data/model_assumptions.csv) · [安全判据CSV](results/data/safety_criteria.csv) · [完整JSON规范](results/data/assumptions_and_safety_criteria.json)
- [来源](references/README.md) · [算术复核](results/logs/design_arithmetic.json) · [资料包](downloads/UPC_2026_A_v2_假设与安全判据.zip)

名义触地目标：接触脚相对甲板下降速度≤2 m/s、水平速度≤0.5 m/s，箭体倾角≤2°、角速度≤0.5°/s。全程动压≤50 kPa，非重力合加速度与力幅值预算均≤4的对应无量纲值。上述均为本文自定H目标，不是题中实机额定限值。

参考任务γ₀=0°；采用3台虚拟V0发动机，末次着陆燃烧用2台；船位选定后固定。名义可用储备约701.05 kg，不可用残余按初始总推进剂的0.5%另列。热防护、实际姿态/执行器及接触后稳定性缺证据时记NOT_VERIFIED。首次接触通过不等于最终稳定着陆。

当前只形成文档规范，没有下降/姿态/接触后求解器，没有燃料结果。v1大气程序仍只覆盖0–70 km，超过该范围必须先补环境；本版没有改动它。

相对基线`97be239`：新增独立v2文档、CSV/JSON和算术记录；v1/B题保留。原理图连接/引脚/器件值、器件/BOM、PCB、固件及已有仿真模型均未修改。
