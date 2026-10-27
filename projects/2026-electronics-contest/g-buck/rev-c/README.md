# G 题同步 Buck Rev C

后续修订：[Rev C.1 新原理图、BOM 与资料包](../rev-c1/README.md)。C.1 有新增 VIN 监测支路和电容改值；本目录保留 Rev C 原版与复核记录。

- [2026-10-27 按用户附件复核报告](reports/RevC_按附件复核_2026-10-27.md)：已从原生工程排除 QH/QL 的 D/S 接反；发现 J_CTL.6 的符号名称仍为 GND。告警/短路真实固件、预充旁路状态、IR2184 实测、整机效率和 ERC/DRC 尚待验证。
- [复核报告 PDF](reports/RevC_按附件复核_2026-10-27.pdf) · [检查标准原件](references/RevC_gpt2_review.md) · [静态证据](results/data/review-2026-10-27/native_audit.json) · [逐引脚 CSV](results/data/review-2026-10-27/native_pin_readback.csv) · [只读复核脚本](simulation/review/audit_revc.py)。
- [原理图工程](schematic/native/G题同步Buck_RevC_原理图修订.eprj2) · [PDF 预览](schematic/previews/G题同步Buck完整原理图_RevC.pdf) · [BOM](schematic/BOM_RevC.csv)。PDF 的 MOS 外观不可替代原生脚号核对；尚无可用于生产的 Rev C PCB。
- [Multisim 100 ms 主工程](downloads/GBUCK_REVC_FULL_25V_5R_100ms.ms14) · [10 ms 短检查](downloads/GBUCK_REVC_FULL_SMOKE_10ms.ms14) · [110 ms 预充检查](downloads/GBUCK_REVC_PRECHARGE_ONLY_110ms.ms14) · [搭建说明](simulation/multisim14/diagrams/Multisim14_RevC完整搭建与使用说明.pdf)。功能模型不等于真实 STM32 固件或厂家时序模型；理想辅助供电不能用于整机效率验收。

2026-10-27 复核的比较基准是上述 Rev C 工程。本次只新增审查资料、证据与脚本，未修改原理图、器件/BOM、PCB 或仿真模型；后续建议的潜在影响见报告第 8 节。
