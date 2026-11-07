# 2026 UPC A：假设与安全判据审阅修订 · v4

针对发动机数量、C10碰撞包络、q/n载荷耦合与C13编号四项意见修订；[修改说明](reports/审阅修改说明.md)。

- [Word修订版](reports/2026_UPC_A题_模型假设与安全判据_修订版.docx) · [PDF](reports/2026_UPC_A题_模型假设与安全判据_修订版.pdf) · [在线全文](reports/模型假设与安全判据_修订版.md)
- [13项假设CSV](results/data/model_assumptions.csv) · [18类/19条检查CSV](results/data/safety_criteria.csv) · [完整JSON规范](results/data/assumptions_and_safety_criteria.json)
- [发动机比较](results/data/engine_count_comparison.csv) · [9格耦合预算示例](results/data/coupled_limit_grid.csv)
- [运行与验证范围](simulation/README.md) · [检查日志](results/logs/review_checks.json) · [资料包](downloads/UPC_2026_A_v4_审阅修订.zip)

C13a=5 m目标偏差，C13b=18 m有限甲板支撑覆盖；同属C13类。18个主类共有19条检查记录；C05为C06隐含的诊断输出。

两台是参考折中，三台42.5%干态悬停仍可行，不能称已被排除。C10中的2 m腿部净空与65 m总高解释为新增H，真实主体/喷管/腿轮廓未知时仍未核实。动态碰撞、轨迹优化和燃料量均未实现；代码只检查算术和简化二维静态几何。

相对基线`640b42f`仅新增v4。v1/v2/v3/B题、原理图、器件/BOM、PCB、固件与旧电子工程仿真模型不变。
