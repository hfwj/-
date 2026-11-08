from pathlib import Path
import json,csv,numpy as np
from replay import Replay,R,MU,VE
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
CJK_FONT=font_manager.FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").get_name()
B=Path(__file__).resolve().parent.parent;D=B/'results/data';F=B/'results/figures';d=dict(np.load(D/'nominal_replay.npz'));w=dict(np.load(D/'optimized_controls.npz'));r=Replay(w)
plt.rcParams.update({'font.family':CJK_FONT,'axes.unicode_minus':False,'font.size':10})
fig,axs=plt.subplots(2,2,figsize=(11,7.8))
axs[0,0].plot(d['range']/1000,d['h']/1000,lw=2);axs[0,0].set(xlabel='地表射程 / km',ylabel='质心高度 / km',title='弹道轨迹')
for ax,k,scale,yl,title in [(axs[0,1],'speed',1,'地速 / (m/s)','速度—时间'),(axs[1,0],'gamma',180/np.pi,'航迹角 γ / °','航迹角—时间'),(axs[1,1],'h',.001,'质心高度 / km','高度—时间')]:
 ax.plot(d['t'],d[k]*scale,lw=2);ax.set(xlabel='时间 / s',ylabel=yl,title=title)
 ax.axvspan(0,r.ig,color='gray',alpha=.12);ax.axvspan(r.ig,r.e1,color='orange',alpha=.12);ax.axvspan(r.ig2,d['t'][-1],color='green',alpha=.1)
 for t in [r.ig,r.e1,r.ig2]:ax.axvline(t,color='gray',ls=':',lw=.8)
for ax in axs.flat:ax.grid(alpha=.2)
fig.suptitle('140 t 条件性名义候选｜65.00 s 七机点火 → 120.41 s 三机点火 → 183.14 s 首次触地',fontsize=12);fig.text(.5,.01,'灰：理想翻转后滑行；橙：再入燃烧；绿：着陆燃烧。假设二维风场，未验证三维回收与接触后停稳。',ha='center',fontsize=9);fig.tight_layout(rect=[0,.03,1,.95]);fig.savefig(F/'00_requested_four_plots.png',dpi=210);fig.savefig(F/'00_requested_four_plots.pdf');plt.close(fig)
rows=[]
for i,t in enumerate(d['t']):
 y=d['state'][i];z=r.quantities(t,y,t<r.ig);u,a,de=r.control(t);vt=z['vt']-z['wind'];vr=z['vr'];V=z['airspeed'];row=dict(t_s=t,thrust_tangential_N=z['T']*np.sin(z['beta']),thrust_radial_N=z['T']*np.cos(z['beta']),drag_tangential_N=-z['D']*vt/V,drag_radial_N=-z['D']*vr/V,gravity_radial_N=-y[4]*MU/(R+z['h'])**2,propellant_flow_kg_s=z['T']/VE,methane_flow_kg_s=z['T']/VE/4.4,lox_flow_kg_s=z['T']/VE*3.4/4.4,thrust_torque_Nm=z['mt'],aero_torque_Nm=z['ma'],jet_inertia_torque_Nm=z['mj'],gravity_gradient_torque_Nm=z['mg'],engine_set_size=len(u))
 for j in range(7):row[f'active_set_engine{j+1}_throttle']=float(u[j]) if j<len(u) else 0
 rows.append(row)
with open(D/'force_moment_engine_timeseries.csv','w',newline='',encoding='utf-8-sig') as f:wr=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");wr.writeheader();wr.writerows(rows)
m=json.load(open(D/'metrics.json'));m['low_height_max_tilt_deg']=float(np.max(abs(np.degrees(d['theta'][d['h']<=232.5]))));m['touchdown_thrust_MN']=float(d['T'][-1]/1e6);m['touchdown_thrust_beta_deg']=float(np.degrees(d['beta'][-1]));json.dump(m,open(D/'metrics.json','w'),ensure_ascii=False,indent=2)
print('Extra outputs completed; low-height max tilt:',m['low_height_max_tilt_deg'])
