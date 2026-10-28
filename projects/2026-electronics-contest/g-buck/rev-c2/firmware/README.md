# Rev C.2 STM32 调试固件

基准：仓库 `94c495e` 的 Rev C.2 原理图、STM32 接口分配、试题要求及评审核对说明。日期：2026-10-28（北京时间）。用户指定按 C.2 准备。

**这是已交叉编译、已做主机逻辑测试的上板调试起点，尚未烧录或实测。默认固件禁止 ARM 和功率使能，不会自动开机。** 实机闭环稳定性、空载同步整流反向电流、实际保护延迟、瞬态最大 1A、效率和题目验收均未通过硬件验证。

## 工程内容

- STM32F103C8T6，真实 64KB Flash / 20KB SRAM，不依赖假定的扩容 Flash。
- 原创寄存器级 C 工程，无需 HAL/Cube 固件包；启动文件、链接脚本、Makefile 均包含。
- 内部 HSI/PLL 64MHz，APB1 32MHz，ADC 8MHz；不依赖控制板晶振是否安装。
- PA8/TIM1_CH1 单路 PWM：约 30.005kHz；IR2184 负责互补输出与内部死区，MCU 不另造互补波形。
- 每 1ms 顺序采样六通道、执行 CV/CC 双 PI 最小值选择、积分跟踪、300ms 电压目标软启动；85% 最大占空比保留自举刷新窗口。控制器不是仿真的“平均电流内环”，不直接移植旧仿真动态结论。
- PB10 下降沿 EXTI 优先关闭 EN/MOE 并记忆；PB11 只参与持续告警，不能单沿关机。实际硬件 FAULT_N→锁存器→驱动关断链保持原有电路。
- 独立 20ms 输出低压与 20ms 持续过流判据；低压分支不依赖 PB11。低目标≤1V、软启动期间屏蔽低压分支，但不屏蔽硬件故障、过流、采样/输入异常。
- 人工启动、预充电压连续就绪 100ms、人工旁路确认、ARM 脉冲、软启动、运行、故障锁存。FAULT 清除不自动重启。
- 预设 ST7735 128×160、RGB565、SPI 只发不收；显示四项测量值、两个独立设定值、状态/故障/下游电压。具体屏幕 tab、偏移、颜色、初始化兼容性仍待实物确认。
- 可选四按键；默认不占用任何未确认按键引脚。默认通过 SWD 调试变量操作。
- DWT 检测 ISR 执行超 1ms / 相邻入口超 2ms并锁存；独立看门狗约 250ms（LSI 有误差），只由前台喂狗。看门狗在 LCD 初始化后启用，复位后再次保持输出关闭。

## C.2 接线

| MCU | 主板接口/功能 |
|---|---|
| PA0 | J_CTL.11，输入电压 VIN_EXT |
| PA1 | J_CTL.12，输入电流 |
| PA2 | J_CTL.13，输出电压 |
| PA3 | J_CTL.14，输出电流 |
| PA4 | J_CTL.15，电感电流（带 1.65V 偏置） |
| PA6 | J_MON.1，下游 VIN；J_MON.2 为 GND |
| PA8 | J_CTL.5，PWM_CTL |
| PB0 | J_CTL.7，MCU_EN |
| PB1 | J_CTL.8，ARM，低→高→低；EN 仍关闭时发脉冲 |
| PB10 | J_CTL.9，FAULT_N，低有效 |
| PB11 | J_CTL.6，IOUT_OC_N，低有效；不能沿用旧版 GND 排线 |
| PA5 / PA7 | LCD SCK / MOSI；PA6 不初始化为 MISO |
| PB12 / PB13 / PB14 | LCD CS / DC / RST |
| PA13 / PA14 | SWDIO / SWCLK，保留调试 |

以实际 C.2 控制板/排线核对电源与地；不要将 5V 信号接到 ADC。SPI 采用单线发送模式，PA6 全程保持模拟输入。

## 编译与烧录

安装 GNU Arm Embedded `arm-none-eabi-gcc`、Make；烧录使用 ST-Link + OpenOCD 或 STM32CubeProgrammer。无需安装 CubeIDE。已验证 GCC 12.2.1。

```sh
cd projects/2026-electronics-contest/g-buck/rev-c2/firmware
make                    # 默认：禁止功率输出，LCD 开，按键关
make test               # 主机 GCC + AddressSanitizer/UBSan 逻辑测试
make flash              # OpenOCD，默认仍是禁止输出版本
make LCD=0              # 未接屏幕时，另目录输出
```

默认产物：`build/p0-k0-l1/gbuck.elf`、`.bin`、`.hex`、`.map`。BIN 烧录地址 **0x08000000**；HEX 自带地址。BOOT0=0，SWD 接 3.3V 参考/GND/SWDIO/SWCLK（可接 NRST），避免不同电源反灌。STM32CubeProgrammer 可直接选择 HEX，烧录并校验。

`downloads/GBUCK_RevC2_STM32_diagnostic_2026-10-28.zip` 包含默认禁止输出的镜像和源码。没有附送允许功率输出的预编译镜像，以避免与诊断版混淆；完整代码中保留可复现的功率调试构建：

```sh
make POWER=1            # 仅在采样/使能极性/保护/接线验证完成后用于受控台架整定
make POWER=1 KEYS=1     # 必须先落实下文四个控制板按键
```

配置取值进入构建目录名，切换选项不会错误复用另一配置的 ELF。`POWER=1` 仍不会自动启动，必须执行完整人工流程。

## 操作、标定与上板顺序

见 [上板调试与操作](docs/上板调试与操作.md)。参数集中在 `include/config.h`；比例/偏置校准在 `src/measurement.c`。不要在 ISR 运行中随意改 PI、校准数组或调试状态结构；只用命令入口修改设定。

## 验证范围与影响

[验证记录](docs/验证与修改影响.md) 区分主机逻辑测试、ARM 编译与尚未执行的板上测试。

- 原理图：相对 `94c495e` 的 C.2，不改拓扑、脚位、阻容值；落实 PA6 等已有接口约束。
- 器件/BOM/PCB：主功率板不改、不新增器件；四按键只给可选控制板方案，是否需补购/飞线尚未确认，默认关闭。LCD 型号与实际主控板仍须上板核对。
- 仿真：不改 `.ms14`、模型或激励；新增的真实 C 控制器及主机测试不能替代旧仿真或硬件验收。
