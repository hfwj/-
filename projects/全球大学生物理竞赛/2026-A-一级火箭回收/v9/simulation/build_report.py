from pathlib import Path
import json,csv
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml.ns import qn
from audit import ROOT,SOURCE
if __name__=='__main__':
 d=ROOT/'results/data';a=json.loads((d/'audit.json').read_text());m=json.loads((d/'reliability_metrics.json').read_text());c=json.loads((d/'checks.json').read_text());opt=json.loads((d/'optimizer_reproduction.json').read_text());f=a['nominal']['final'];ca=m['conditional_attitude'];base=json.loads((SOURCE/'results/data/replay_summary.json').read_text());ng=json.loads((d/'old_checker_negative_test.json').read_text())
 labels={'Cd_minus10pct':'Cd降低10%','Cd_plus10pct':'Cd增加10%','Isp_minus1pct':'Isp降低1%','Isp_plus1pct':'Isp增加1%','rho_minus5pct':'密度降低5%','rho_plus5pct':'密度增加5%','initial_vt_minus1m_s':'初始切向速度−1 m/s','initial_vt_plus1m_s':'初始切向速度+1 m/s','initial_vr_minus1m_s':'初始径向速度−1 m/s'}
 lines=[]
 for x in a['frozen_open_loop_sensitivity']:
  fz=x['final'];event=x['event']
  if event=='REFERENCE_CONTACT':behavior=f"参考接触vr={fz['vr_m_s']:.2f}、vt={fz['vt_m_s']:.2f} m/s"
  elif event=='USABLE_PROPELLANT_EXHAUSTED':behavior=f"质心高度{fz['height_m']:.2f} m时可用推进剂耗尽"
  else:behavior=f"计划终点未接触，CG高度{fz['height_m']:.2f} m"
  lines.append(f"| {labels[x['name']]} | {behavior} | 未通过 |")
 sensitivity='\n'.join(lines)
 text=f'''# A题v9：程序验证与结果可靠性复核

## 核心评价

v8的名义平动数值结果可以复现，但尚不足以支持真实安全着陆或工程装载量结论。149.30 t是特定二维气动/发动机假设、限制策略族与局部优化下的初始总推进剂候选值。它不是题目给定事实、经验证的实际最低需求或全局最优。

| 评价层面 | 当前证据 | 判断 |
|---|---|---|
| 方程、单位与数值积分 | 独立SI实现、解析极限、两种坐标与积分器、原验收复跑 | 名义M0计算可信 |
| 名义约束 | 动压、力预算、CG参考速度、节流响应、储备 | 已建模子集通过 |
| 箭体/推力执行能力 | 需大角度相对偏转、未建刚体力矩与执行器 | 未证明可执行 |
| 固定开环的扰动容忍度 | 9个确定性单参数扰动均未按原计划通过 | 当前控制不稳健 |
| 真实燃料需求 | Cd/Isp/风/方向/姿态等未标定及闭环未设计 | 不能给置信区间或工程装载量 |
| 最优性 | 同一初猜链与有限策略比较、IPOPT局部求解 | 未证明全局最优 |

## 本次实际执行的验证

本次保持v8控制不变。v9独立实现SI极坐标动力学、标准大气和控制回放，仅从v8读取控制节点；名义对照为原v8 SI Cartesian DOP853回放。v8原始验收程序另复制到临时目录完整复跑，避免覆盖已归档文件；原SHA256清单核对通过。

| 验证 | 实测结果 | 能说明什么 |
|---|---|---|
| 200组随机状态/控制的极坐标↔Cartesian加速度及耗剂单位转换 | 最大绝对差{c['coordinate_rhs_max_absolute_error_mixed_SI']:.3e}（各分量对应SI单位） | 所检查范围内符号、曲率项和千倍单位换算一致 |
| 分层大气与v8表的1001点核对 | 最大相对密度误差{c['density_max_relative_error']:.3e} | 两实现一致；不是实际天气验证 |
| 6个教材级位势高度密度锚点 | 最大相对误差{c['rounded_geopotential_anchor_max_relerr']:.3e} | 与舍入参考值一致 |
| 123 s纯真空中心重力 | 能量相对漂移{c['vacuum_max_energy_relerr']:.3e}；角动量{c['vacuum_max_angular_momentum_relerr']:.3e} | 重力/曲率符号和数值积分合理 |
| 无重力真空理想火箭方程解析解 | 速度误差{c['ideal_rocket_velocity_error_m_s']:.3e} m/s | 质量流率与推力单位闭合 |
| 一维常密度二次阻力解析解 | 速度误差{c['quadratic_drag_velocity_error_m_s']:.3e} m/s | 阻力方向/速度平方量纲正确 |
| 从有效指令重新积分发动机响应ODE | 实际节流最大误差{a['actuator_max_actual_error']:.3e} | 当前节点轨迹可由所假设一阶/速率模型生成 |
| 原320区间优化从交付160区间初猜重新求解 | 初始推进剂差{opt['initial_propellant_difference_kg']:.9f} kg；终时差{opt['final_time_difference_s']:.9f} s | 当前初猜路径的求解可复现；不证明多初猜/全局最优 |
| 新输入验证的4种负例 | 角度数值越界、NaN、维数错误、无效时序均拒绝 | 改善验收入口的健壮性 |

另用RK45复核Cd降低10%、Isp降低1%、初始切向速度−1 m/s三个扰动，事件类型一致，末状态高度/速度的最大绝对差均小于0.01（各分量对应SI单位）。

极限解析检查主要验证共同使用的物理关系和实现，不等于标定了真实Cd、Isp、姿态或热/结构模型。守恒残差小也不能弥补缺失的物理机制。

## 名义结果复核

| 量 | 独立v9结果 | 相对v8差异 |
|---|---:|---:|
| 参考接触时刻 | {f['time_s']:.9f} s | {m['independent_vs_v8']['contact_time_difference_s']:.3e} s |
| 参考径向速度 | {f['vr_m_s']:.9f} m/s | {m['independent_vs_v8']['radial_velocity_difference_m_s']:.3e} m/s |
| 参考接触总质量 | {f['mass_kg']:.6f} kg | {m['independent_vs_v8']['mass_difference_kg']:.3e} kg |
| 名义航程 | {f['range_m']:.6f} m | {m['independent_vs_v8']['range_difference_m']:.3e} m |
| 峰值动压 | {a['nominal']['peaks']['q_Pa']/1000:.6f} kPa | {m['independent_vs_v8']['q_peak_difference_Pa']:.3e} Pa |

新实现改用RK45后，参考接触径向速度与DOP853相差{m['cross_solver_radial_velocity_difference_m_s']:.3e} m/s。结合v8的160→320区间携带量变化0.018947%，数值离散误差显著小于以下物理/扰动影响。但网格差是经验收敛指标，不是严格误差上界；表中很多小数用于回归对照，不代表同等实际精度。

## 验收程序发现的缺口

v8回放虽检查动压、载荷、节流指令等，却没有先完整验证输入控制的角度范围、形状、时序和边界连续性，且点火次数按既定策略族写死。本次把两段β节点同时加2π后，旧程序仍返回M0通过。正余弦周期性使受力相同，因此这不是一个新发现的危险物理方向；它明确证明旧通过标志不能覆盖所宣称的原始角度数值约束。原始候选本身在界内，名义数值结论没有因此失效。

v9新增严格输入核查，并用4种负例实测拒绝。v8作为历史版本保留；面向其他输入应先调用v9 validate，再作回放。新审计仍只支持明确的“三台—5 s指令间隔—两台”策略族，不能推广成任意发动机调度的安全验收器。

原优化在滑行和首段启动阶段没有施加逐点q/载荷约束，部分高度边界也仅在节点检查；当前候选由独立回放补充筛查通过，但不能仅凭IPOPT成功就断言换一个输入仍满足全程约束。峰值为密集取样与局部极值细化的数值筛查，并非解析全时域证书。旧回放默认在计划终点后把末控制保持最多2 s；本次扰动检验严格止于原计划终点，不把未定义的延长控制当作有效着陆程序。

## 物理可执行性的关键缺口

在CG高度约{m['nearest_200m_reference_clearance_sample']['height_m']:.2f} m（直立参考脚间隙约199.28 m）时，推力倾角β≈{m['nearest_200m_reference_clearance_sample']['beta_deg']:.2f}°。全程CG高度≤232.5 m部分，最大|β|约{ca['max_thrust_tilt_below_232_5m_deg']:.2f}°。若同时要求箭体倾角|θ|≤5°，则合推力相对箭体至少需要约{ca['minimum_required_net_gimbal_for_C08_deg']:.2f}°的偏转能力。该数值是几何必要条件，不是已知发动机能力；v4没有给出或验证这种能力。

当下降且q≥10 kPa时，推力方向与迎风方向最大夹角约{ca['max_incoming_misalignment_if_body_follows_thrust_deg']:.2f}°。若箭体必须在迎风方向±5°内，至少需要约{ca['minimum_required_net_gimbal_for_C07_deg']:.2f}°的相对合推力偏转能力。若直接把箭体姿态设为推力方向，C07/C08会不通过；末端β变化率约{m['final_if_body_follows_thrust_angular_rate_deg_s']:.2f}°/s也不能直接当作通过C15的0.5°/s箭体角速度。若让箭体与推力解耦，则必须补万向节/侧向执行器、气动力矩与刚体转动模型，当前没有这些证据。

CG高度32.5 m只是参考停止事件，不是真实脚端首次触碰甲板。尚未验证65 m箭体在倾斜下的包络间隙、脚端角速度项、全脚覆盖、热结构或接触后2 s吸能稳定性。因此“参考速度约1 m/s”不能升级为“安全着陆速度约1 m/s”。

## 固定开环扰动：9个案例均未按原计划通过

保持原149.30 t初始携带量、全部控制节点和时刻不变，单独改变一个参数。不是重新优化，不含反馈纠偏，也不假设扰动发生概率；9个案例不构成统计置信区间或失败概率。比冲扰动只改变耗剂模型、不联动最大推力，是隔离参数影响的诊断。密度与Cd分开改变，避免把二者在阻力乘积中的等效作用混为新证据；密度同时影响q，Cd不直接影响q定义。储备门槛沿用v4的固定名义701.055 kg。

| 单项扰动 | 结果（速度仅在确实参考接触时报告） | 原计划验收 |
|---|---|---|
{sensitivity}

“计划终点未接触”不等于永远无法着陆；这里只能说固定计划没有完成参考任务，延长/改动计划须重新设计验证。“可用推进剂耗尽”终止于不可用残余上界，不能继续把残余燃烧掉取得漂亮末速度。对扰动仍固定原名义船位；另记录参考航程误差，未将它冒充真实脚端位置C13。

尤其初始切向速度−1 m/s仅约0.06%的扰动，参考接触径向速度已约−11.54 m/s；Isp降低1%在CG高度约299.88 m可用推进剂耗尽。711 kg名义可用储备只比701 kg门槛高约10 kg，不能称为已验证的鲁棒余量。当前动压约6%的名义余量也不能保证参数变化后通过：Cd降低10%的案例峰值动压约52.38 kPa。

## 对149.30 t应该怎样表述

可以写：“在水平分离、无风、恒Cd=0.5、Isp=320 s等假设以及给定理想合推力权限下，得到初始推进剂约149 t的M0名义可行候选；名义数值计算已独立复核。”

不应写：“本题所需燃料149.30 t”“已找到真实安全着陆最低燃料”“±某百分比置信区间已知”。额外物理约束会缩小同一模型可行域，但当前局部候选不是全局最小值，因此149.30 t也不能用作更完整模型的严格下界；按真实全约束，它尚不能作已验证的可行上界。

## 下一步优先顺序

1. 先明确净推力相对箭体的偏转范围、力矩/角加速度及发动机布置，建立M1。将迎风、200 m竖直化、接触倾角和角速度一起纳入轨迹，避免事后硬贴姿态。
2. 用已有候选作初猜，加入位置/速度反馈或滚动重规划；固定名义船位，并预留控制与可用推进剂余量。重新做上述确定性扰动，确认纠偏能完成后再扩大场景。
3. 加入包络/脚端/接触后模型，补Mach/攻角气动与热结构证据；题目未给初速方向，应把不同分离仰角分情景计算。
4. 这些约束通过后，再比较更多策略族、多初猜与q/Isp/Cd场景，报告经验证的燃料范围及其条件；不能只给当前数字加一个任意安全系数。

## 可复现资料与影响说明

simulation/checks.py执行解析/坐标/负例/历史哈希检查；audit.py执行独立回放、RK45对照、执行器ODE与9个扰动；summarize.py输出差异和姿态必要条件；optimizer_reproduction.json与原验收复跑记录保存完整原始证据。全部路径和命令见simulation/README.md。依据为v4假设/判据与v8控制，不新增实机参数证据。

比较基线为d60ee2d3bdc925b0f0624b4adbacc54861131a89。本次仅新增v9审计程序、诊断数据、报告与索引；v8控制、模型与报告保持原样。原理图拓扑/管脚/器件值、器件/BOM/封装、PCB、固件及旧电子工程模型均不变；不构成任何硬件验收。
'''
 (ROOT/'reports/程序验证与可靠性评价.md').write_text(text)
 doc=Document();section=doc.sections[0];section.top_margin=section.bottom_margin=Inches(.65)
 style=doc.styles['Normal'];style.font.name='Noto Sans CJK SC';style._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');style.font.size=Pt(10)
 table=None
 for line in text.splitlines():
  if line.startswith('|'):
   cells=[x.strip() for x in line.strip('|').split('|')]
   if all(set(x)<=set('-: ') for x in cells):continue
   if table is None:table=doc.add_table(rows=0,cols=len(cells));table.style='Table Grid'
   for cell,value in zip(table.add_row().cells,cells):cell.text=value
  else:
   table=None
   if line.startswith('# '):doc.add_heading(line[2:],0)
   elif line.startswith('## '):doc.add_heading(line[3:],1)
   elif line.strip():doc.add_paragraph(line.strip())
 doc.save(ROOT/'reports/2026_UPC_A题_程序验证与可靠性评价.docx');print('Report built')
