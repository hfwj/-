"""Analyze optimized +45-degree cases using independent Cartesian replay."""
from pathlib import Path
import numpy as np,json,csv,math,sys
from replay import Replay,R,MU,VE,wind
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');FONT=font_manager.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name();plt.rcParams.update({'font.family':FONT,'axes.unicode_minus':False,'font.size':10})
B=Path(__file__).resolve().parent.parent;D=B/'results/data';F=B/'results/figures'
def writecsv(p,rows):
 with open(p,'w',newline='',encoding='utf-8-sig') as f:wr=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');wr.writeheader();wr.writerows(rows)
def geometry(r,d,ship_phi=None):
 y=d['state'][-1];z=r.quantities(d['t'][-1],y);ph=z['phi'] if ship_phi is None else ship_phi;er=np.array([math.sin(ph),math.cos(ph)]);et=np.array([math.cos(ph),-math.sin(ph)]);center=R*er;psi=y[5];eb=np.array([math.sin(psi),math.cos(psi)]);ep=np.array([math.cos(psi),-math.sin(psi)]);om=y[6];fv=np.array([y[2:4]+om*(-32.5*ep-sg*5*eb) for sg in [-1,1]]);fx=(z['foot']-center)@et
 bodyclear=[]
 for yy in d['state'][d['h']<1000]:
  ps=yy[5];bb=np.array([math.sin(ps),math.cos(ps)]);pp=np.array([math.cos(ps),-math.sin(ps)]);pts=np.array([yy[:2]+s*bb+sg*3.5*pp for s in np.r_[np.arange(-30.5,32.5,1),32.5] for sg in [-1,1]]);bodyclear.append(float(np.min((pts-center)@er)))
 return dict(ship_phi=ph,foot_x=fx.tolist(),foot_vertical=(fv@er).tolist(),foot_horizontal=(fv@et).tolist(),body_min_clearance=min(bodyclear) if bodyclear else float('nan'))
def savefig(name):plt.tight_layout();plt.savefig(F/(name+'.png'),dpi=190);plt.savefig(F/(name+'.pdf'));plt.close()
def main():
 w=dict(np.load(sys.argv[1]));r=Replay(w);d,event=r.run(.1);d2,event2=r.run(.05);np.savez(D/'optimized_controls.npz',**w);np.savez(D/'nominal_replay.npz',**d);g=geometry(r,d);prop=r.m0/1000-130;interp=lambda k,t:float(np.interp(t,d['t'],d[k]));maskq=d['q']>=10000;masklo=d['h']<=232.5;active=d['t']>=r.ig
 rate_peaks=[]
 for un,start,dur in [('U1',r.ig+1.6,float(w['dur1'])),('U2',r.ig2+1.6,float(w['dur2']))]:
  uu=w[un];mm=(d['t']>=start)&(d['t']<=start+dur);ii=np.minimum(((d['t'][mm]-start)/dur*(uu.shape[1]-1)).astype(int),uu.shape[1]-2);sl=np.diff(uu[2])/(dur/(uu.shape[1]-1));rate_peaks.append(float(np.max(abs(np.degrees(d['omega'][mm]+sl[ii])))))
 checks=dict(inertial_thrust_rate=max(rate_peaks)<=5.000001,contact=event=='contact',q=d['q'].max()<=50000,n_sum=d['n'].max()<=4,foot_vertical_speed=np.max(np.abs(g['foot_vertical']))<=2,foot_horizontal_speed=np.max(np.abs(g['foot_horizontal']))<=.5,contact_tilt=abs(np.degrees(d['theta'][-1]))<=2,contact_rate=abs(np.degrees(d['omega'][-1]))<=.5,alpha_highq=np.max(np.degrees(d['alpha'][maskq]))<=5.000001,theta_lowheight=np.max(np.abs(np.degrees(d['theta'][masklo])))<=5.000001,deck_coverage=np.max(np.abs(g['foot_x']))<=18,body_clearance=g['body_min_clearance']>0,reserve=d['m'][-1]>=130000+.005*prop*1000+3.3e6/VE)
 m=dict(propellant_initial_t=prop,initial_mass_t=r.m0/1000,event=event,all_selected_checks_pass=bool(all(checks.values())),checks={k:bool(v) for k,v in checks.items()},ignition1_s=r.ig,shutdown1_command_s=r.e1,ignition2_s=r.ig2,contact_s=d['t'][-1],range_km=d['range'][-1]/1000,first_burn_t=(r.m0-interp('m',r.ig2))/1000,second_burn_t=(interp('m',r.ig2)-d['m'][-1])/1000,remaining_t=(d['m'][-1]-130000)/1000,qmax_kPa=d['q'].max()/1000,n_sum_max=d['n'].max(),vr_contact_m_s=d['vr'][-1],vt_contact_m_s=d['vt'][-1],theta_contact_deg=np.degrees(d['theta'][-1]),omega_contact_deg_s=np.degrees(d['omega'][-1]),alpha_highq_max_deg=np.max(np.degrees(d['alpha'][maskq])),low_height_max_tilt_deg=np.max(np.abs(np.degrees(d['theta'][masklo]))),max_gimbal_deg=np.max(np.abs(np.degrees(d['delta'][active]))),max_omega_deg_s=np.max(np.abs(np.degrees(d['omega'][active]))),apogee_km=float(d['h'].max()/1000),apogee_time_s=float(d['t'][d['h'].argmax()]),geometry=g,refine_contact_time_difference_s=abs(d2['t'][-1]-d['t'][-1]),refine_range_difference_m=abs(d2['range'][-1]-d['range'][-1]),refine_vr_difference_m_s=abs(d2['vr'][-1]-d['vr'][-1]),refine_mass_difference_kg=abs(d2['m'][-1]-d['m'][-1]))
 stages=[]
 for name,a,b in [('无推力上升',0,m['apogee_time_s']),('无推力下降',m['apogee_time_s'],r.ig),('七机再入燃烧',r.ig,r.e1),('关机尾流与滑行',r.e1,r.ig2),('三机着陆燃烧',r.ig2,d['t'][-1])]:
  mask=(d['t']>=a)&(d['t']<=b);powered=mask&(d['T']>1000);stages.append(dict(stage=name,start_s=a,end_s=b,start_h_km=interp('h',a)/1000,end_h_km=interp('h',b)/1000,start_speed_m_s=interp('speed',a),end_speed_m_s=interp('speed',b),propellant_t=(interp('m',a)-interp('m',b))/1000,Tmax_MN=d['T'][mask].max()/1e6,beta_min_deg=float(np.degrees(d['beta'][powered]).min()) if powered.any() else None,beta_max_deg=float(np.degrees(d['beta'][powered]).max()) if powered.any() else None))
 m['inertial_thrust_rate_max_deg_s']=max(rate_peaks);m['q_above_86km_max_Pa']=float(d['q'][d['h']>86000].max());m['stages']=stages;writecsv(D/'stage_summary.csv',stages);json.dump(m,open(D/'metrics.json','w'),ensure_ascii=False,indent=2)
 keys=['t','range','h','speed','airspeed','vt','vr','gamma','theta','omega','delta','beta','T','q','n','m','wind'];writecsv(D/'nominal_timeseries.csv',[{k:float(d[k][i]) for k in keys} for i in range(len(d['t']))])
 fig,axs=plt.subplots(2,2,figsize=(11,7.5));axs[0,0].plot(d['range']/1000,d['h']/1000);axs[0,0].set(xlabel='地表射程 / km',ylabel='质心高度 / km',title='球面地球弹道')
 for ax,k,fac,yl,title in [(axs[0,1],'speed',1,'对地速率 / (m/s)','速度—时间'),(axs[1,0],'gamma',180/np.pi,'航迹角 γ / °','航迹角—时间'),(axs[1,1],'h',.001,'质心高度 / km','高度—时间')]:
  ax.plot(d['t'],d[k]*fac);ax.set(xlabel='分离后时间 / s',ylabel=yl,title=title);ax.axvspan(r.ig,r.e1,color='orange',alpha=.15);ax.axvspan(r.ig2,d['t'][-1],color='green',alpha=.12);ax.axvline(m['apogee_time_s'],ls=':',color='gray',lw=.7)
 for ax in axs.flat:ax.grid(alpha=.2)
 fig.suptitle(f'γ0=+45°｜{prop:g} t 装载｜CasADi/IPOPT + 独立正向积分');savefig('01_four_main_curves')
 fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
 for k,label in [('theta','箭体 θ'),('beta','推力 β'),('delta','偏转 δ')]:axs[0].plot(d['t'],np.degrees(d[k]),label=label)
 axs[0].legend();axs[0].set_ylabel('角度 / °');axs[1].plot(d['t'],np.degrees(d['omega']));axs[1].set_ylabel('惯性角速度 / (°/s)');axs[2].plot(d['t'],d['T']/1e6);axs[2].set(xlabel='时间 / s',ylabel='合推力 / MN')
 for ax in axs:ax.axvspan(0,r.ig,color='gray',alpha=.12);ax.grid(alpha=.2)
 axs[0].set_title('灰区为理想姿态参考，第一次点火后才联立积分俯仰');savefig('02_attitude_thrust')
 fig,axs=plt.subplots(2,2,figsize=(10,7));axs[0,0].plot(d['t'],d['q']/1000);axs[0,0].axhline(50,color='r',ls='--');axs[0,0].set(ylabel='动压 / kPa',xlabel='时间 / s');axs[0,1].plot(d['t'],d['n']);axs[0,1].axhline(4,color='r',ls='--');axs[0,1].set(ylabel='非重力力幅值和 / mg0',xlabel='时间 / s');axs[1,0].plot(d['t'],(d['m']-130000)/1000);axs[1,0].set(ylabel='剩余总推进剂 / t',xlabel='时间 / s');hh=np.linspace(0,150000,500);axs[1,1].plot(wind(hh,0),hh/1000);axs[1,1].set(ylabel='高度 / km',xlabel='顺航向风 / (m/s)',title='沿用原稿锚点的假设风剖面');savefig('03_constraints_wind_fuel')
 fig,ax=plt.subplots(figsize=(9,4.8))
 cuts=[0,m['apogee_time_s'],r.ig,r.e1,r.ig2,d['t'][-1]]
 for a,b,name in zip(cuts[:-1],cuts[1:],[x['stage'] for x in stages]):
  mask=(d['t']>=a)&(d['t']<=b);ax.plot(d['range'][mask]/1000,d['h'][mask]/1000,lw=3,label=name)
 ax.set(xlabel='地表射程 / km',ylabel='质心高度 / km');ax.legend(fontsize=8);ax.grid(alpha=.2);savefig('04_phase_trajectory')
 # Frozen-control perturbations, not closed-loop robustness evidence.
 stress=[]
 cases=[('Cd −15%',.425,1,330),('Cd −20%',.4,1,330),('Isp −2%',.5,1,330*.98),('风 ×2',.5,2,330),('风 ×3',.5,3,330),('组合：Cd−15%/Isp−2%/风×2',.425,2,330*.98)]
 for name,cd,ws,isp in cases:
  rr=Replay(w,cd=cd,wind_scale=ws,isp=isp);dd,ev=rr.run(.15,end_at_plan=True);gg=geometry(rr,dd,ship_phi=g['ship_phi']);iscontact=ev=='contact';flag=bool(iscontact and dd['q'].max()<=50000 and dd['n'].max()<=4 and np.max(np.abs(gg['foot_vertical']))<=2 and np.max(np.abs(gg['foot_horizontal']))<=.5 and np.max(np.abs(gg['foot_x']))<=18 and abs(np.degrees(dd['theta'][-1]))<=2 and abs(np.degrees(dd['omega'][-1]))<=.5 and dd['m'][-1]>=130000+.005*prop*1000+3.3e6/(isp*9.80665))
  stress.append(dict(case=name,event=ev,time_s=dd['t'][-1],height_m=dd['h'][-1],vr_m_s=dd['vr'][-1],vt_m_s=dd['vt'][-1],qmax_kPa=dd['q'].max()/1000,remaining_t=(dd['m'][-1]-130000)/1000,downrange_error_m=dd['range'][-1]-d['range'][-1],selected_subset_pass=flag));np.savez(D/('stress_'+str(len(stress))+'.npz'),**dd)
 writecsv(D/'fixed_control_perturbations.csv',stress);print(json.dumps(m,ensure_ascii=False,indent=2));print('PERTURBATIONS',stress)
if __name__=='__main__':main()
