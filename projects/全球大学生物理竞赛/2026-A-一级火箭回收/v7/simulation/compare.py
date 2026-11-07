from pathlib import Path
import json,csv
from forward import simulate
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/data';OUT.mkdir(parents=True,exist_ok=True)
strategies=[('无推力',[]),('提前单次',[(60,40)]),('稍晚单次',[(85,40)]),('两段燃烧',[(60,20),(110,20)])]
records=[]
for name,windows in strategies:
    result,rows=simulate(burn_windows=windows)
    result.update(strategy=name,burn_windows=windows)
    records.append(result)
    with (OUT/f'{len(records):02d}_trajectory.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
fine,_=simulate(burn_windows=strategies[-1][1],max_step=.05)
error=abs(fine['final']['speed_m_s']-records[-1]['final']['speed_m_s']);assert error<.1
(OUT/'comparison.json').write_text(json.dumps(dict(initial_propellant_kg=70000,cases=records,two_burn_refinement_speed_error_m_s=error),ensure_ascii=False,indent=2))
lines=['# 四种下降策略的正向比较','','共同条件：初始推进剂70 t，Cd=0.5，比冲320 s；两台虚拟发动机最大合推力2.2 MN，方向始终理想逆速度；每次点火延迟0.5 s并保留节流响应。三个有推力方案的指令燃烧总时长均为40 s。','', '| 策略 | 指令时间窗/s | 实际耗剂/t | 参考接触速率/(m/s) | 峰值q/kPa | 峰值nΣ |','|---|---|---|---|---|---|']
for r in records:
    lines.append(f"| {r['strategy']} | {r['burn_windows']} | {r['consumed_kg']/1000:.3f} | {r['final']['speed_m_s']:.2f} | {r['max_q_Pa']/1000:.2f} | {r['max_n_sum']:.3f} |")
lines += ['', '时窗为指令起点与持续时长；实际响应延后且关机有尾段。实际耗剂由积分得到，不预设为相等；若触地提前终止，可能截断燃烧。峰值由约0.1 s输出采样取得，非连续峰值认证。','',f'两段工况最大步长从0.1 s减为0.05 s，末速差为{error:.3g} m/s；各工况质量—冲量恒等式均通过。','', '本比较用于选择后续研究方向，不是最优策略证明。仍为M0理想转向，未验证转向速率、姿态、完整包络、甲板相对速度、结构热或接触后稳定性；参考接触采用质心高度32.5 m。各策略必须先对照50 kPa、nΣ≤4及2 m/s触地目标，不能仅凭耗剂或末速排序就判安全。','', '相对c42a52c新增独立v7多时窗接口及比较，v6及旧版本保留。原理图、器件/BOM、PCB、固件及电子工程模型不变。']
(ROOT/'reports').mkdir(exist_ok=True);(ROOT/'reports/少量下降策略比较.md').write_text('\n'.join(lines))
print('\n'.join(lines))
