# v25：全新可复现模型与实测数值验证

- [论文856A.pdf](reports/856A.pdf)
- [完整可运行复现包](downloads/UPC_856A_v25_Reproducible.zip)
- [便携LaTeX源码包](downloads/UPC_856A_v25_LaTeX.zip)
- [新模型核查与替换说明](reports/新模型核查与替换说明.md) · [Word](reports/新模型核查与替换说明.docx)
- [三档步长CSV](results/data/convergence.csv) · [逐事件JSON](results/data/convergence.json)
- [完整代码入口](simulation/README.md) · [全部配置](simulation/config.json)

用户已授权独立重建并替换旧结果。12个Cd锚点、7 km高空密度延拓、无量纲目标函数和完整事件/动力学实现均公开；0.02/0.01/0.005 s在固定参数下真实执行，所有图表由本版脚本生成。旧106.6 t和110–112 t结论不作为本版输入或拟合目标。

有限搜索首先找到130 t名义候选，细步长消耗约128.078 t、剩余1.922 t、下降2.203 m/s、峰值动压45.942 kPa。参数扰动仍存在失败，本版不宣称全球最小值、稳健甲板捕获或真实飞行安全。模型未作实验气动标定和六自由度/支脚接触验证。

相对v24（0f14f28），模型、假设及全部仿真结果重新生成，原理图、器件/BOM、PCB与固件不变。完整历史AI对话记录仍有缺口，见独立说明。
