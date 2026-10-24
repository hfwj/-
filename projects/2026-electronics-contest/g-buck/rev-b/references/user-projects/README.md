# 用户原生Multisim工程

`2026-10-24_设计1.ms14`为用户首次上传原件，保留原始字节，不覆盖。

- 上传文件名：设计1.ms14。
- 文件长度：248723字节。
- SHA256：`069ea8839f390757e58e172036e62547119e40ae0ae6efea9da698603acf85f6`。
- 原生版本信息：Multisim 14.0.593。
- 检查、修订副本和证据：[原生工程排查说明](../../simulation/multisim14/native-project-check/README.md)。

原件包含用户本机保存的模型、工程状态及未修改的PNG预览。原件的保存或归档不表示仿真已经成功。

后续上传的当前可运行工程保存在[2026-10-24_本机可运行_保险丝对照.ms14](2026-10-24_本机可运行_保险丝对照.ms14)：

- 上传文件名：设计1_瞬态容差调整_5ms_待本机验证 (1).ms14。
- 文件长度：252584字节。
- SHA256：`5995f248b7683502ee6412937513adcecad85427633854a410c8173c6f2a7050`。
- 实际设置：4us/10us PWM、20ms瞬态、自定义四项容差；F1两端断开、R1=1mΩ接通输入。
- 后续交付：[基于这份工程的软启动/CVCC功能控制副本](../../simulation/multisim14/native-project-check/control-loop/README.md)。新副本与上传原件分开保存。

本机15V空载回传原件：[2026-10-24_15V空载_恢复F1_本机回传.ms14](2026-10-24_15V空载_恢复F1_本机回传.ms14)。

- 原上传名：GBUCK_CTRL_EQ_CV_15V_OPEN_native_check.ms14；长度：252343字节；SHA256：`bd3cce52a75b840f7cb5000e76bc504cdae8a8777daa7892d9e02b978e454f07`。
- 与已交付15V空载比较：F1(2A)接回V1正端至D1阳极，临时R1两端断开；其他元件参数、模型正文、控制模板及自定义分析设置相同。
- 30ms输出截图已收到：峰值约11.1V、末端约9.8V仍缓慢变化。未收到精确数值导出，未确认熔断特性或真实上电浪涌。
- 本次仅原样归档，不更改原工程、原理图、实物器件或BOM/PCB；[结构比较记录](../../simulation/multisim14/native-project-check/control-loop/results/data/CV_15V_OPEN_returned_project_inspection.json)。
