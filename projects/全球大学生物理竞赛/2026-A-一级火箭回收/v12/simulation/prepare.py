from pathlib import Path
import csv,json,hashlib,shutil,math
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];P=ROOT.parent

def load(v,path):return json.loads((P/v/path).read_text())
def prepare():
 inputs={
 'nominal':('v8','results/data/replay_summary.json'), 'verification':('v8','results/data/verification.json'),
 'comparison':('v8','results/data/strategy_comparison.json'),'audit':('v9','results/data/audit.json'),
 'checks':('v9','results/data/checks.json'),'reproduction':('v9','results/data/optimizer_reproduction.json'),
 'reliability':('v9','results/data/reliability_metrics.json'),'attitude':('v10','results/data/diagnostics.json')}
 data={k:load(*q) for k,q in inputs.items()};hashes={f'{v}/{path}':hashlib.sha256((P/v/path).read_bytes()).hexdigest() for v,path in inputs.values()}
 for src,name in [(P/'v5/results/data/passive_cases.csv','passive_cases.csv'),(P/'v8/results/data/phase_states.csv','phase_states.csv'),(P/'v9/results/data/sensitivity.csv','sensitivity.csv'),(P/'v10/results/data/safety_matrix.csv','safety_matrix_source.csv')]:
  shutil.copy(src,ROOT/'results/data'/name);hashes[str(src.relative_to(P))]=hashlib.sha256(src.read_bytes()).hexdigest()
 for name in ['v8/results/data/candidate_trajectory.csv','v9/results/data/independent_trajectory.csv']:
  hashes[name]=hashlib.sha256((P/name).read_bytes()).hexdigest()
 (ROOT/'results/data/evidence.json').write_text(json.dumps(data,indent=2,ensure_ascii=False));(ROOT/'references/input_hashes.json').write_text(json.dumps(hashes,indent=2))
 r=list(csv.DictReader((P/'v8/results/data/candidate_trajectory.csv').open()));a={k:np.array([float(x[k]) for x in r]) for k in r[0]};t=a['time_s'];s=data['nominal'];off=s['toff_s']
 plt.rcParams.update({'font.family':'DejaVu Serif','font.size':12,'axes.grid':True,'grid.alpha':.23,'axes.unicode_minus':False})
 fig,ax=plt.subplots(2,2,figsize=(9,5.8),layout='constrained')
 ax[0,0].plot(a['range_m']/1000,a['height_m']/1000);ax[0,0].set(xlabel='Surface arc range (km)',ylabel='CG altitude (km)')
 ax[0,1].plot(t,a['vt_m_s'],label=r'$v_t$');ax[0,1].plot(t,a['vr_m_s'],label=r'$v_r$');ax[0,1].set(xlabel='Time (s)',ylabel='Velocity (m/s)');ax[0,1].legend()
 ax[1,0].plot(t,a['q_Pa']/1000);ax[1,0].axhline(50,color='r',ls='--',label='50 kPa screening limit');ax[1,0].set(xlabel='Time (s)',ylabel='Dynamic pressure (kPa)');ax[1,0].legend(fontsize=10.5)
 ax[1,1].plot(t,a['mass_kg']/1000);ax[1,1].set(xlabel='Time (s)',ylabel='Total mass (t)')
 for axes in ax.flat:
  if axes is not ax[0,0]:axes.axvspan(0,40,color='gray',alpha=.10);axes.axvspan(off,off+6.6,color='orange',alpha=.12)
 fig.savefig(ROOT/'results/figures/trajectory.png',dpi=220);fig.savefig(ROOT/'results/figures/trajectory.pdf');plt.close(fig)
 fig,ax=plt.subplots(2,1,figsize=(8.5,4.8),layout='constrained',sharex=True)
 ax[0].plot(t,a['pair_actual_throttle'],label='Each of the landing pair');ax[0].plot(t,a['third_actual_throttle'],label='Third engine');ax[0].axhline(.3,color='gray',ls=':',label='Minimum steady throttle');ax[0].set(ylabel='Actual throttle');ax[0].legend(fontsize=10.5,ncol=2)
 ax[1].plot(t,a['beta_deg'],label=r'Thrust direction $\beta$');ax[1].set(xlabel='Time (s)',ylabel='Angle from local vertical (deg)');ax[1].legend();fig.savefig(ROOT/'results/figures/controls.png',dpi=220);fig.savefig(ROOT/'results/figures/controls.pdf');plt.close(fig)
 v=list(csv.DictReader((P/'v9/results/data/independent_trajectory.csv').open()));b={k:np.array([float(x[k]) for x in v]) for k in v[0]};tt=b['time_s'];chi=np.degrees(np.arctan2(-b['vt_m_s'],-b['vr_m_s']));mask=(b['q_Pa']>=10000)&(b['vr_m_s']<0);lo=np.full(len(tt),-180.);hi=-lo;lo[mask]=chi[mask]-5;hi[mask]=chi[mask]+5;low=b['height_m']<=232.5;lo[low]=np.maximum(lo[low],-5);hi[low]=np.minimum(hi[low],5);d=np.maximum.reduce([np.zeros(len(tt)),lo-b['beta_deg'],b['beta_deg']-hi])
 fig,ax=plt.subplots(2,1,figsize=(8.5,4.8),layout='constrained',sharex=True)
 ax[0].plot(tt,b['beta_deg'],label=r'Required thrust $\beta$');ax[0].fill_between(tt,chi-5,chi+5,where=mask,alpha=.25,label='Body angle allowed by high-q inflow screen');ax[0].set(ylabel='Angle (deg)');ax[0].legend(fontsize=10.5)
 ax[1].plot(tt,d,label='Necessary relative deflection');
 for y,col in [(5,'gray'),(20,'orange'),(25,'green')]:ax[1].axhline(y,ls='--',color=col,label=f'Assumed {y} deg limit')
 ax[1].set(xlabel='Time (s)',ylabel='Relative deflection (deg)',ylim=(-1,36));ax[1].legend(fontsize=9.5,ncol=2);fig.savefig(ROOT/'results/figures/attitude.png',dpi=220);fig.savefig(ROOT/'results/figures/attitude.pdf');plt.close(fig)
 # Assumed geometry at first contact, not a simulated vehicle or leg design.
 theta=math.radians(2);ell=32.5;bb=5;rad=3.5;h=ell*math.cos(theta)+bb*math.sin(theta);eb=np.array([math.sin(theta),math.cos(theta)]);ep=np.array([math.cos(theta),-math.sin(theta)]);cg=np.array([0,h]);feet=np.array([cg-ell*eb+q*bb*ep for q in [-1,1]]);body=np.array([cg+(q-ell)*eb+sgn*rad*ep for q,sgn in [(2,-1),(65,-1),(65,1),(2,1),(2,-1)]])
 fig,ax=plt.subplots(1,2,figsize=(8,4.5),layout='constrained')
 for z in ax:
  z.plot(body[:,0],body[:,1],color='steelblue');z.plot(feet[:,0],feet[:,1],'ko');z.plot([0,cg[0]],[0,cg[1]],':',color='gray');z.axhline(0,color='black');z.set(xlabel='Deck-frame x (m)',ylabel='Deck-frame z (m)');z.set_aspect('equal',adjustable='box')
 ax[0].plot(*cg,'ro');ax[0].annotate('CG',cg,xytext=(5,0),textcoords='offset points');ax[0].set(xlim=(-10,10),ylim=(-2,68),title='Assumed main-cylinder / foot geometry')
 ax[1].set(xlim=(-7,7),ylim=(-.5,5),title='First contact at 2 deg body tilt');ax[1].annotate('Second foot: 0.349 m above deck',feet[0],xytext=(-6,3.7),arrowprops={'arrowstyle':'->'},fontsize=10.5)
 fig.savefig(ROOT/'results/figures/contact_geometry.png',dpi=220);fig.savefig(ROOT/'results/figures/contact_geometry.pdf');plt.close(fig)
 return data
if __name__=='__main__':prepare();print('Evidence and four English figures prepared')
