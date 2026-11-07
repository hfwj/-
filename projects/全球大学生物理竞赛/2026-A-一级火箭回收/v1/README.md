# 2026 UPC A：一级火箭助推器海上回收 · v1

本版完成资料核查和参数准备：68项参数/待定记录、10个一手来源及0–70 km标准大气复算。未建立轨迹求解器或计算所需推进剂。

- [Word参数文档](reports/2026_UPC_A题_资料核查与建模参数表.docx) · [PDF阅读版](reports/2026_UPC_A题_资料核查与建模参数表.pdf) · [在线阅读](reports/资料核查与建模参数表.md)
- [参数表CSV](results/data/parameters.csv) · [JSON](results/data/parameters.json)
- [大气表CSV](results/data/standard_atmosphere_0_70km.csv) · [推算值JSON](results/data/derived_parameters.json)
- [来源及适用边界](references/README.md) · [复算方法](simulation/README.md) · [检查日志](results/logs/parameter_checks.json)
- [完整资料包](downloads/UPC_2026_A_v1_参数资料包.zip)

G=题目给定；L=文献参考；D=公式推算；H=人为假设；U=未知。未知项在JSON为null，在CSV中为“待定”。虚拟发动机V0和敏感性网格均为H，不冒充题中实机、经验上下界或置信区间。

优先补充：分离航迹角、同一发动机族的推力/比冲图、气动闭合和结构/热/触地限值。Prometheus的历史1000 kN为真空推力；360 s是上面级方案。BE-4网页未提供比冲，使用LOX/LNG。

相对基线`fcc2c33`：只新增A题v1文档、参数和算术脚本；B题与电子工程保留。原理图连接/引脚/器件值、器件/BOM、PCB、固件及已有仿真模型无改动；新增内容不验证任何原硬件设计。
