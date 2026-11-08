from pathlib import Path
import numpy as np,json,csv,math,sys
from replay import Replay,R,VE,K2,wind,startup,decay
ROOT=Path(__file__).resolve().parent.parent;D=ROOT/'results/data';F=ROOT/'results/figures';D.mkdir(parents=True,exist_ok=True);F.mkdir(parents=True,exist_ok=True)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
CJK_FONT=font_manager.FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").get_name()
plt.rcParams.update({'font.family':CJK_FONT,'axes.unicode_minus':False,'font.size':10,'savefig.dpi':190})
def scalar(x):return float(x)
def writecsv(p,rows):
 with open(p,'w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def savefig(name):
 plt.tight_layout();plt.savefig(F/(name+'.png'));plt.savefig(F/(name+'.pdf'));plt.close()
def main():
 p=Path(sys.argv[1]);w=dict(np.load(p));r=Replay(w);d,event=r.run(.1);d2,event2=r.run(.05);np.savez(D/'nominal_replay.npz',**d)
 np.savez(D/'optimized_controls.npz',**w)
 interp=lambda k,t:float(np.interp(t,d['t'],d[k]));m1=interp('m',r.ig2);tend=d['t'][-1];burn1=r.m0-m1;burn2=m1-d['m'][-1]
 # Foot velocities include rotational velocity; ship is stationary on the nonrotating Earth.
 y=d['state'][-1];z=r.quantities(tend,y);psi=y[5];eb=np.array([math.sin(psi),math.cos(psi)]);ep=np.array([math.cos(psi),-math.sin(psi)]);om=y[6];footv=np.array([y[2:4]+om*(-32.5*ep-sg*5*eb) for sg in [-1,1]])
 # Fixed ship selected once at nominal contact, 20 m half-width; safe inner half-width18 m.
 ph=z['phi'];er=np.array([math.sin(ph),math.cos(ph)]);et=np.array([math.cos(ph),-math.sin(ph)]);center=R*er;fx=(z['foot']-center)@et;fv=footv@er
 # Body hull sampled every 1m along axis, including both lateral outlines, 2m above feet.
 bodyclear=[]
 for yy in d['state'][d['h']<1000]:
  ps=yy[5];bb=np.array([math.sin(ps),math.cos(ps)]);pp=np.array([math.cos(ps),-math.sin(ps)]);pts=np.array([yy[:2]+s*bb+sg*3.5*pp for s in np.r_[np.arange(-30.5,32.5,1),32.5] for sg in [-1,1]]);bodyclear.append(float(np.min((pts-center)@er)))
 high=d['q']>=10000;low=d['h']<=232.5
 checks=dict(contact=event=='contact',q=d['q'].max()<=50000,n_sum=d['n'].max()<=4,foot_vertical_speed=np.max(np.abs(fv))<=2,vt=abs(d['vt'][-1])<=.5,theta=abs(np.degrees(d['theta'][-1]))<=2,omega=abs(np.degrees(d['omega'][-1]))<=.5,alpha_highq=np.max(np.degrees(d['alpha'][high]))<=5.000001,theta_lowheight=np.max(np.abs(np.degrees(d['theta'][low])))<=5.000001,deck_edge=np.max(np.abs(fx))<=18,body_before_contact=min(bodyclear)>0,reserve=d['m'][-1]>=130000+.005*140000+3.3e6/VE)
 metrics=dict(propellant_initial_t=140.,initial_mass_t=r.m0/1000,event=event,all_selected_checks_pass=all(checks.values()),checks={k:bool(v) for k,v in checks.items()},ignition1_s=r.ig,shutdown1_command_s=r.e1,ignition2_s=r.ig2,contact_s=tend,range_km=d['range'][-1]/1000,first_burn_t=burn1/1000,second_burn_t=burn2/1000,remaining_t=(d['m'][-1]-130000)/1000,qmax_kPa=d['q'].max()/1000,n_sum_max=d['n'].max(),vt_contact_m_s=d['vt'][-1],vr_contact_m_s=d['vr'][-1],theta_contact_deg=np.degrees(d['theta'][-1]),omega_contact_deg_s=np.degrees(d['omega'][-1]),foot_vertical_velocities_m_s=fv.tolist(),foot_deck_x_m=fx.tolist(),body_min_clearance_m=min(bodyclear),alpha_highq_max_deg=np.max(np.degrees(d['alpha'][high])),max_gimbal_deg=np.max(np.abs(np.degrees(d['delta']))),max_omega_deg_s=np.max(np.abs(np.degrees(d['omega']))),refine_contact_time_difference_s=abs(d2['t'][-1]-tend),refine_range_difference_m=abs(d2['range'][-1]-d['range'][-1]),refine_vr_difference_m_s=abs(d2['vr'][-1]-d['vr'][-1]),refine_mass_difference_kg=abs(d2['m'][-1]-d['m'][-1]))
 stages=[]
 for name,a,b in [('理想翻转与滑行',0,r.ig),('再入燃烧及关机尾流',r.ig,r.ig2),('着陆燃烧',r.ig2,tend)]:
  mask=(d['t']>=a)&(d['t']<=b);stages.append(dict(stage=name,start_s=a,end_s=b,start_altitude_km=interp('h',a)/1000,end_altitude_km=interp('h',b)/1000,start_speed_m_s=interp('speed',a),end_speed_m_s=interp('speed',b),propellant_t=(interp('m',a)-interp('m',b))/1000,Tmax_MN=d['T'][mask].max()/1e6,Tmean_MN=float(np.trapezoid(d['T'][mask],d['t'][mask])/(b-a)/1e6),beta_min_deg=np.degrees(d['beta'][mask]).min(),beta_max_deg=np.degrees(d['beta'][mask]).max()))
 writecsv(D/'stage_summary.csv',stages);metrics['stages']=stages
 json.dump(metrics,open(D/'metrics.json','w'),ensure_ascii=False,indent=2)
 rows=[dict(t_s=t,h_m=d['h'][i],range_m=d['range'][i],v_ground_m_s=d['speed'][i],v_air_m_s=d['airspeed'][i],vt_m_s=d['vt'][i],vr_m_s=d['vr'][i],gamma_deg=np.degrees(d['gamma'][i]),theta_deg=np.degrees(d['theta'][i]),omega_deg_s=np.degrees(d['omega'][i]),delta_deg=np.degrees(d['delta'][i]),thrust_N=d['T'][i],mass_kg=d['m'][i],q_Pa=d['q'][i]) for i,t in enumerate(d['t'])];writecsv(D/'nominal_timeseries.csv',rows)
 # Lower-load traces are honest frozen-control forward diagnostics, not optimized candidates.
 traces={140:(d,event)};scan=[]
 for fuel in range(90,141,10):
  if fuel<140:rr=Replay(w);dd,ev=rr.run(.15,prop=fuel);traces[fuel]=(dd,ev)
  else:dd,ev=d,event
  np.savez(D/f'frozen_schedule_{fuel}t.npz',**dd)
  scan.append(dict(propellant_t=fuel,protocol='nominal_optimized' if fuel==140 else 'frozen_140t_schedule_diagnostic',end_event=ev,end_time_s=dd['t'][-1],end_height_m=dd['h'][-1],end_vr_m_s=dd['vr'][-1],qmax_kPa=dd['q'].max()/1000,remaining_t=(dd['m'][-1]-130000)/1000,accepted=bool(fuel==140 and all(checks.values()))))
 writecsv(D/'mass_scan_diagnostics.csv',scan)
 for name,xkey,ykey,xscale,yscale,xlab,ylab in [('01_trajectory','range','h',.001,.001,'地表射程 / km','质心高度 / km'),('02_speed_time','t','speed',1,1,'分离后时间 / s','地速 / (m/s)'),('03_flightpath_time','t','gamma',1,180/np.pi,'分离后时间 / s','航迹角 γ / °'),('04_altitude_time','t','h',1,.001,'分离后时间 / s','质心高度 / km')]:
  fig,ax=plt.subplots(figsize=(8.5,5))
  for fuel,(dd,ev) in traces.items():ax.plot(dd[xkey]*xscale,dd[ykey]*yscale,lw=2.4 if fuel==140 else 1,ls='-' if fuel==140 else'--',label=f'{fuel} t'+(' 标称通过' if fuel==140 else' 固定控制诊断'));ax.scatter(dd[xkey][-1]*xscale,dd[ykey][-1]*yscale,s=15)
  if xkey=='t':
   for t in [r.ig,r.e1,r.ig2]:ax.axvline(t,color='gray',lw=.7,alpha=.6)
  ax.set(xlabel=xlab,ylabel=ylab);ax.grid(alpha=.25);ax.legend(fontsize=8,ncol=2);ax.set_title('140 t 为重新优化的标称方案；较低装载量虚线仅作同控制诊断');savefig(name)
 fig,axs=plt.subplots(3,1,figsize=(9,9),sharex=True)
 for k,label in [('theta','箭体倾角 θ'),('beta','推力相对天顶方向 β'),('delta','万向节角 δ')]:axs[0].plot(d['t'],np.degrees(d[k]),label=label)
 axs[1].plot(d['t'],np.degrees(d['omega']));axs[1].set_ylabel('惯性俯仰角速度 / (°/s)');axs[0].set_ylabel('角度 / °');axs[0].legend(fontsize=8);axs[2].plot(d['t'],d['T']/1e6);axs[2].set(ylabel='发动机合推力 / MN',xlabel='时间 / s')
 for ax in axs:
  ax.axvspan(0,r.ig,color='gray',alpha=.12);ax.axvline(r.ig2,color='gray',ls=':');ax.grid(alpha=.2)
 axs[0].set_title('灰色区域姿态为理想迎流参考；点火后才联立积分刚体俯仰');savefig('05_attitude_thrust')
 fig,axs=plt.subplots(1,2,figsize=(10,4));axs[0].plot(d['t'],d['q']/1000);axs[0].axhline(50,color='r',ls='--');axs[0].set(xlabel='时间 / s',ylabel='动压 / kPa');hh=np.linspace(0,70000,500)
 for tt in [0,2,6]:axs[1].plot(wind(hh,tt),hh/1000,label=f't={tt} s')
 axs[1].set(xlabel='顺航向风 / (m/s)',ylabel='高度 / km');axs[1].legend();axs[1].set_title('假设风剖面，非实测气象');savefig('06_wind_dynamicpressure')
 # Trajectory phase diagram for accepted case only.
 fig,ax=plt.subplots(figsize=(9,5));cuts=[0,r.ig,r.e1,r.ig2,tend];names=['理想翻转后滑行','7台再入燃烧','关机尾流与滑行','3台着陆燃烧']
 for a,b,name in zip(cuts[:-1],cuts[1:],names):
  mask=(d['t']>=a)&(d['t']<=b);ax.plot(d['range'][mask]/1000,d['h'][mask]/1000,lw=3,label=name)
 for t,lab in [(r.ig,'第一次点火'),(r.ig2,'第二次点火'),(tend,'首次触地')]:
  xx=interp('range',t)/1000;yy=interp('h',t)/1000;ax.scatter(xx,yy,s=25);ax.annotate(f'{lab}\n{t:.2f}s，{yy:.2f}km',(xx,yy),xytext=(-65,22),textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'->'})
 ax.set(xlabel='地表射程 / km',ylabel='质心高度 / km',title='140 t 标称回收过程：两次点火，船预置于约190 km下游');ax.legend();ax.grid(alpha=.2);savefig('07_nominal_phases')
 print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
