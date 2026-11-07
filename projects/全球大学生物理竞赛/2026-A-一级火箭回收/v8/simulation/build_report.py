from pathlib import Path
import json,csv,math
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 d=ROOT/'results/data';s=json.loads((d/'replay_summary.json').read_text());v=json.loads((d/'verification.json').read_text());f=s['final'];p=dict(np.load(d/'controls_N320.npz'))
 rows=list(csv.DictReader((d/'candidate_trajectory.csv').open()));a={k:np.array([float(r[k]) for r in rows]) for k in rows[0]}
 font=font_manager.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');font_manager.fontManager.addfont(font.get_file());plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':10})
 fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained');t=a['time_s']
 axs[0,0].plot(a['range_m']/1000,a['height_m']/1000);axs[0,0].set(xlabel='沿地表航程 / km',ylabel='质心高度 / km')
 axs[0,1].plot(t,a['vt_m_s'],label='切向速度');axs[0,1].plot(t,a['vr_m_s'],label='径向速度');axs[0,1].set(xlabel='时间 / s',ylabel='速度 / (m/s)');axs[0,1].legend()
 axs[1,0].plot(t,a['q_Pa']/1000);axs[1,0].axhline(50,color='r',linestyle='--',label='50 kPa目标');axs[1,0].set(xlabel='时间 / s',ylabel='动压 / kPa');axs[1,0].legend()
 axs[1,1].plot(t,a['pair_actual_throttle'],label='着陆发动机：每台');axs[1,1].plot(t,a['third_actual_throttle'],label='第三台');axs[1,1].set(xlabel='时间 / s',ylabel='实际节流 / 每台1 MN');axs[1,1].legend()
 for ax in axs.flat:ax.grid(alpha=.25)
 fig.suptitle('M0名义候选：独立正向回放，完整安全判据尚未验证');fig.savefig(ROOT/'results/figures/candidate.png',dpi=180);fig.savefig(ROOT/'results/figures/candidate.pdf');plt.close(fig)
 def P(x):return f'{x:.3f}'
 comp=json.loads((d/'strategy_comparison.json').read_text())
 comparison='\n'.join(f"| {r['label']} | {r['ignition_command_s']:.2f} | {r['initial_propellant_kg']/1000:.3f} | {r['consumed_kg']/1000:.3f} | {'通过' if r['M0_subset_pass'] else '未通过'} |" for r in comp)
 schedule=[]
 for label,tau in [('分离',0),('三台点火指令',s['ignition_command_s']),('关机指令',s['toff_s']),('两台再点火指令',s['restart_command_s']),('参考接触',s['actual_end_s'])]:
  schedule.append(dict(phase=label,time_s=tau,**{key:float(np.interp(tau,a['time_s'],a[key])) for key in ['height_m','vt_m_s','vr_m_s','mass_kg','beta_deg']}))
 with (d/'phase_states.csv').open('w') as ff:
  ww=csv.DictWriter(ff,fieldnames=schedule[0],lineterminator="\n");ww.writeheader();ww.writerows(schedule)
 state_table='\n'.join(f"| {r['phase']} | {r['time_s']:.3f} | {r['height_m']/1000:.3f} | {r['vt_m_s']:.2f} | {r['vr_m_s']:.2f} | {r['mass_kg']/1000:.3f} |" for r in schedule)
 text=f'''# A题v8：受约束低消耗候选方案

## 结论与适用范围

已找到通过M0名义可计算约束子集的候选：初始总推进剂{s['initial_propellant_kg']/1000:.3f} t，实际消耗{s['consumed_kg']/1000:.3f} t。这里推进剂指液氧与甲烷总量，不仅指甲烷。不是全局最优，也不是完整v4安全着陆认证。姿态、脚端/包络、热结构与接触后稳定性尚未验证，因此不能声称满足全部18类安全判据。

本次把初始推进剂质量作为目标变量，由轨迹、耗剂和末端条件共同闭合。保留船位自由，按名义落点配置船位；不会额外要求返回发射点。固定燃烧时窗比较已不足以完成这一目标。

## 模型与搜索口径

初始质心高度70 km、水平速度1666.667 m/s、径向速度0；干质量130 t，直径7 m，参考面积38.48451 m²。球形中心重力、0–70 km分层标准大气、无风无自转、恒定Cd=0.5与Isp=320 s。发动机参数、分离方向与限制均沿用论文假设H，不是实机额定。质量中包含不可用残余0.5%初始推进剂。

取局部切向/径向状态(h,v_t,v_r,m)，以SI制写为：

 dh/dt = v_r

 dv_t/dt = (T sinβ - D v_t/V)/m - v_r v_t/(R+h)

 dv_r/dt = (T cosβ - D v_r/V)/m - μ/(R+h)² + v_t²/(R+h)

 dm/dt = -T/(Isp g₀)，D = ρ V² Cd A/2。

β相对局部竖直，允许[-90°,90°]，是合推力方向，不是箭体姿态。此处允许理想合推力转向，不能据此证明发动机万向节或姿态机构可实现。

策略族为“先滑行—三台再入燃烧—关机指令间隔5 s—两台再点火/着陆燃烧”。两台实际节流相同，第三台独立节流。外层少量比较初次点火时刻；内层优化两段末时刻、初始质量、实际节流节点与β节点；5 s指令间隔固定，未遍历所有策略族。每台点火延迟0.5 s、实际节流变化率≤1/s、一阶响应常数0.1 s；稳态有效指令在[0.3,1.1]。优化线性实际节流，并以u_cmd=u+0.1 du/dt检查响应可实现性。启停过渡允许实际推力低于最小稳态节流，关机尾焰用指数尾部，不能误当作稳态违规。着陆两台各点火2次，第三台点火1次。

合推力方向在局部坐标的速率限4.9°/s，独立回放另查惯性方向速率≤5°/s。搜索动压上限47 kPa、力幅值预算3.9；验收分别为50 kPa、4。优化设计端点额外限制竖直推力≤0.95倍当地重量以留数值余量，独立回放的实际参考接触事件以≤1倍重量作附加筛查，该H条件不能替代接触后2 s稳定性。质心高度限制32.5 m–70 km，飞行时间110–450 s，初始质量131–400 t，初次点火外层测试0/20/40/50/60 s（接口范围0–95 s）。全程常Cd假设不等于全马赫范围真实气动标定。

采用CasADi/IPOPT局部非线性优化、直接多重射击，两段各320个控制区间、每区间4个RK4子步；滑行步长不大于0.5 s、启动64×0.025 s、启停过渡132×0.05 s。使用归一化km、km/s、t、MN求解，输出与独立回放使用SI。目标是最小初始携带总推进剂；不把理想火箭方程的Δv当作自由输入。单一数值初猜和有限策略比较不构成全局最优证明。

## 候选执行顺序

| 时刻/阶段 | 名义指令 |
|---|---|
| 0–{s['ignition_command_s']:.3f} s | 无推力滑行 |
| {s['ignition_command_s']:.3f} s | 三台点火指令；0.5 s延迟后建推 |
| {s['ignition_command_s']+1.6:.3f}–{s['toff_s']:.3f} s | 三台再入燃烧，按优化节流与β轨迹 |
| {s['toff_s']:.3f} s | 三台关机指令 |
| {s['restart_command_s']:.3f} s | 两台再点火指令；第三台保持关闭 |
| {s['toff_s']+6.6:.3f}–{s['actual_end_s']:.3f} s | 两台末段燃烧至参考接触 |

| 事件 | 时间/s | 质心高度/km | 切向速度/(m/s) | 径向速度/(m/s) | 总质量/t |
|---|---:|---:|---:|---:|---:|
{state_table}

不能只用上述时刻重现结果；必须同时读取controls_N320.npz的节流与方向节点。第二次燃烧包含水平制动与竖直化，尚未证明近竖直点火的C09辅助筛查适用。

## 少量策略比较

所有数值使用同一质量、气动和推力假设，独立Cartesian回放；固定延迟20/40/50 s的比较项两段各80区间，仅用于比较，最终候选用320区间。相同物理约束下优化初始携带量，已不再强行固定70 t或40 s燃烧时长。

| 方案 | 初次点火指令/s | 初始推进剂/t | 消耗/t | M0子集 |
|---|---:|---:|---:|---|
{comparison}

连续优化初次点火时刻达到迭代上限未收敛，不作为有效结果。测试过的60 s固定初次点火在当前初猜下求解失败，仅说明该次局部搜索未得解，不证明物理不可行。v7的70 t固定时窗失败也不能作为最低燃料下界。本次节省量只相对表内策略，不能表述为相对所有可行方案的最优收益。

## 独立正向回放结果

| 指标 | 结果 | 验收/口径 |
|---|---:|---|
| 初始总推进剂 | {s['initial_propellant_kg']/1000:.6f} t | 优化目标，含残余与储备 |
| 实际消耗 | {s['consumed_kg']/1000:.6f} t | 实际推力积分 |
| 参考接触剩余总推进剂 | {(f['mass_kg']-130000)/1000:.6f} t | 含不可用残余 |
| 参考接触可用储备 | {f['usable_kg']:.3f} kg | ≥701.055 kg；另加10 kg优化缓冲 |
| 飞行时间 | {s['actual_end_s']:.6f} s | 下穿CG高度32.5 m事件 |
| 名义船位地表航程 | {f['range_m']/1000:.6f} km | 由自由船位选定，无地理坐标 |
| 参考接触径向速度 | {f['vr_m_s']:.6f} m/s | -2至0；CG代理量 |
| 参考接触切向速度 | {f['vt_m_s']:.9f} m/s | 绝对值≤0.5；CG代理量 |
| 最大动压 | {s['peaks']['q_Pa']/1000:.6f} kPa | ≤50 kPa |
| 最大力幅值预算n_sum | {s['peaks']['n_sum']:.6f} | ≤4；气动力幅值与推力耦合 |
| 最大非重力合加速度/g₀ | {s['peaks']['n_proper']:.6f} | C06隐含的诊断 |
| 接触竖直推力/当地重量 | {s['terminal_vertical_thrust_over_weight']:.6f} | ≤1附加筛查 |
| 质量守恒误差 | {s['mass_balance_error_kg']:.9f} kg | ≤0.001 kg |

若仅为装载分配采用O/F=3.4假设，甲烷约{s['initial_propellant_kg']/4400:.3f} t、液氧约{s['initial_propellant_kg']*3.4/4400:.3f} t；不是混合比优化结果。

## 为什么携带量仍然较大

该候选的发动机特征速度积分为Isp g₀ ln(m₀/m_f)≈{320*9.80665*math.log((130000+s['initial_propellant_kg'])/f['mass_kg'])/1000:.3f} km/s，包含沿整个受控轨迹的速度改变与重力损失，不能用“无推力落地速率+固定干重减速时间”替代。50 kPa目标要求在进入稠密大气前较早制动；船位自由省去返回发射点机动，但不自动消除终端水平制动。重力改变速度方向，并非简单耗散掉初始水平动量。

按初始质量，两台2.2 MN最大推力对初始重量的比值约{2.2e6/((130000+s['initial_propellant_kg'])*9.80665):.3f}，不能假定末端近干重时的向上净加速度全程有效。本方案初段用三台，随耗剂下降后再使用两台。这也说明此前33–73 t的量级参照没有建立质量—轨迹—推力的自洽闭环，不能作为当前约束下的可行区间。本次约149 t同样仅是当前策略族找到的可行上界，不是严格需求下界。

## 哪些约束通过，哪些仍未核实

C01质量/流量、C02所用大气高度域、C03所实现的数量/节流/响应/速率/点火次数子集、C04动压、C06力预算、C16可用储备通过名义数值检查；C05为派生诊断。C02的真实全马赫气动有效性、C03真实姿态执行能力仍未核实。

C07迎风姿态、C08末段竖直化、C14倾角、C15角速度没有M1姿态状态，均NOT_VERIFIED。C09近竖直可制停辅助式未施加。C10脚端及1 m轮廓包络首次接触未实现；C11/C12当前只检查质心参考速度，不能冒充脚端速度通过；C13a/b当前只允许按名义落点布船，5 m实际位置误差及18 m全脚覆盖未验；C17热/结构与C18接触后稳定吸能未验。

因此后续应先将这一候选输入M1姿态/包络与接触模型，检查合推力方向能否实现，再做初速方向、Cd、风、延迟和Isp的扰动验证。若不通过，必须重优化，不只在最终燃料上加一个任意百分比。按全套v4定义，目前尚无已证明全部安全约束通过的方案。

## 验证证据与复现

优化器采用局部极坐标RK4；验收使用独立SI制Cartesian方程与SciPy DOP853，分割所有控制节点/启停事件，连续事件检测，0.05 s采样并对局部动压/载荷峰值再细化。有限数值检查不是解析全时域证明。

符号大气与独立分层表在1001个均匀点及层边界邻域核对，最大相对密度误差{v['density_max_relative_error']:.3e}。本次原型曾发现分层选择顺序错误，已修正并用上述闸门阻止重现；错误原型结果未纳入任何交付候选。

160→320区间初始推进剂相对变化{v['grid_fuel_relative_difference']*100:.6f}%，参考接触速率变化{v['grid_terminal_speed_difference_m_s']:.6f} m/s；320区间独立积分最大步长0.1→0.05 s，接触速率变化{v['replay_halving_terminal_speed_difference_m_s']:.9f} m/s。原始控制、轨迹、各次回放和比较保存在results/data；复现命令见simulation/README.md。

## 来源与变更影响

试题常数与参数来源沿用v1，假设/判据沿用v4，正向诊断参照v6/v7；本版不新增实机性能证据。初猜references/initial_guess.npz只是固定40 s点火的局部数值初猜，不是认证轨迹。

相对基线提交5e0f8190a8815079a73aa0d617ecfc3b689ae9d8：仅新增A题v8优化器、独立回放、数据、报告与索引。v1–v7与B题计算文件保留；原理图连接/管脚/数值、器件/BOM/封装、PCB、固件及旧电子工程模型均无变化。模型影响限本次新增火箭M0控制等效与求解设置，不构成对任何硬件的验证。
'''
 (ROOT/'reports/受约束低消耗候选.md').write_text(text)
 doc=Document();sec=doc.sections[0];sec.top_margin=sec.bottom_margin=Inches(.65)
 normal=doc.styles['Normal'];normal.font.name='Noto Sans CJK SC';normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');normal.font.size=Pt(10)
 table=None
 for line in text.splitlines():
  if line.startswith('|'):
   cells=[x.strip() for x in line.strip('|').split('|')]
   if all(set(x)<=set('-: ') for x in cells):continue
   if table is None:table=doc.add_table(rows=0,cols=len(cells));table.style='Table Grid'
   for c,t in zip(table.add_row().cells,cells):c.text=t
  else:
   table=None
   if line.startswith('# '):doc.add_heading(line[2:],0)
   elif line.startswith('## '):doc.add_heading(line[3:],1)
   elif line.strip():doc.add_paragraph(line.strip())
 doc.add_picture(str(ROOT/'results/figures/candidate.png'),width=Inches(6.6));doc.save(ROOT/'reports/2026_UPC_A题_受约束低消耗候选.docx')
 print('Report built')
