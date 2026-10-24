# Multisim元器件向导：单顶层TI采样模型修正

2026-10-24。用户在第5页加载模型后、进入第6页时得到：

> The model contains multiple top-level .subckt statements. Place any dependent .subckt or .model definitions within the main (top-level) .subckt.

此前接口文件把8脚/6脚适配层和原TI定义并列。ngspice接受这种库结构，但用户本机向导要求所有依赖在唯一主子电路内部。旧版独立求解通过不能作为向导结构兼容性通过。

## 当前请这样操作

1. 下载并解压[向导结构修正版ZIP](../../../downloads/Multisim14_TI_CurrentSense_WizardFix_2026-10-24.zip)。
2. 保留当前向导第5页，点击“从文件加载”，选新包里的`models/INA240A1_TI_8PIN_WIZARD.lib`，替换原模型数据。
3. 模型名称仍为`INA240A1_TI_8PIN`，**名称不加_WIZARD**；SPICE model type保持User-defined。
4. 点击“下一步”，把第6页引脚映射截图发回；本环境没有启动Windows Multisim，不预称本机已导入。

符号、8个管脚、前4页设置不需要重新创建。模型首行仍为：

`.SUBCKT INA240A1_TI_8PIN INM GND REF2 NC OUT VS REF1 INP`

唯一的外层`.ENDS INA240A1_TI_8PIN`现在位于整个文件最后。所有TI内部.ENDS保留，用于结束各自的辅助子电路；不能删掉它们。

U3的修正候选位于`models/candidate/INA181A1_TI_6PIN_WIZARD.lib`，顶层名仍为`INA181A1_TI_6PIN`。**U3动态检查依旧未完成，当前先处理U2/U4的INA240。**

## 修改内容和证据

比较基线为先前上传到向导的`INA240A1_TI_8PIN.lib`及对应INA181接口文件。

- 仅将原本位于适配层末尾的外层.ENDS搬到整个文件末尾。原TI文件仍作为完整连续字节块保留在新文件中，包括所有方程、参数、子电路、.MODEL、注释、版权及换行。
- INA240由13个并列顶层改为1个顶层，其余12个依赖嵌套在内部；INA181由18个顶层改为1个顶层，其余17个依赖嵌套。
- 脚本检查旧结构确有多顶层，新结构只剩预期顶层，所有依赖.MODEL在主模型内部，开始/结束配对正确，首行端口未变；精确逆变换验证只移动外层结束语句。
- 新文件单独求解，未额外载入原全局辅助库，以免缺失的局部依赖被外部定义掩盖。

| 检查 | 新结构结果 |
|---|---|
| INA240 DC扫描 | 完整61点，与原结果输出差异为导出精度内0V |
| INA240 100us阶跃 | 完整2046点，相对旧结果最大输出差约1e-8V |
| INA181 DC扫描 | 完整41点，与原输出一致 |
| INA181阶跃 | 约8ns时仍步长过小，未通过；不混写成结构修正已解决动态 |
| 三芯片及R_VDDA的DC测试台 | 完成，与旧结果一致；不是完整Buck或保护链 |
| Windows Multisim导入/主图运行 | 尚未完成，等待本机重试 |

见[验证JSON](results/data/verification.json)。新结构的INA181失败轨迹也保留，原先的失败记录在[INA181来源目录](../ina181a1-ti-import/README.md)。

## 影响

- 原理图/实物：现有.ms14和主功率连线均未编辑。
- 器件/BOM/PCB：不新增或更换实物器件，不改变额定值、封装或PCB。
- 模型：只改变定义的嵌套作用域；顶层名称、端口数、顺序和TI内部计算内容均保持。独立回归结果如上。
- 固件/控制：不修改真实固件、Ki20控制或保护门限。

## 复现

在仓库本目录运行`python build_and_check.py`，需要numpy、ngspice44.2及现有XSPICE库；再运行`python package.py`。模型及旧基线来自仓库中的原用户ZIP与已归档接口，既有文件不覆盖。

## 2026-10-25后续状态

用户已完成INA240导入，STEP01修正反馈节点后可运行30ms；U4关系得到截图功能核对。U3新增[独立初始化对照](../ina181-power-on-check/README.md)：模型不变，有序上电100us通过，固定电源对照仍失败。U3本机导入/动态尚待测试，不改写上表的历史结果，也不据此宣布Buck接入通过。
