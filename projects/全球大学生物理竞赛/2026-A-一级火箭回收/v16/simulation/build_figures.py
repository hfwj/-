"""Publication figures regenerated from frozen v15 data; no new trajectory optimization."""
from pathlib import Path
import json,csv,numpy as np,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,patches
from replay import Replay,VE
from atmosphere_1976 import atmosphere
B=Path(__file__).resolve().parent.parent;D=B/'results/data';F=B/'results/figures';F.mkdir(exist_ok=True)
font_manager.fontManager.addfont('/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf')
plt.rcParams.update({'font.family':'Latin Modern Roman','font.size':9,'mathtext.fontset':'cm','axes.linewidth':.65,'lines.linewidth':1.4,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':7.8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':220})
BLUE='#0072B2';ORANGE='#D55E00';GREEN='#009E73';PURPLE='#CC79A7';GRAY='#666666'
w=dict(np.load(D/'optimized_controls.npz'));d=dict(np.load(D/'nominal_replay.npz'));m=json.load(open(D/'metrics.json'));r=Replay(w);t=d['t']
def save(name):
 plt.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.savefig(F/(name+'.png'),bbox_inches='tight');plt.close()
def grid(ax):ax.grid(alpha=.2,linewidth=.5);ax.spines[['top','right']].set_visible(False)
def label(ax,txt):ax.text(.01,1.025,txt,transform=ax.transAxes,ha='left',va='bottom',fontsize=10,fontweight='bold')
def shade(ax):
 ax.axvspan(r.ig,r.e1,color=ORANGE,alpha=.10,lw=0);ax.axvspan(r.ig2,t[-1],color=GREEN,alpha=.09,lw=0)
 for x in [r.ig,r.e1,r.ig2]:ax.axvline(x,color=GRAY,lw=.6,ls=':')
# Mission + local geometric definition: schematic dimensions explicitly H.
fig,(a,b)=plt.subplots(1,2,figsize=(7,4.1),gridspec_kw={'width_ratios':[1.3,1]})
a.plot(d['range']/1000,d['h']/1000,color=BLUE)
for tm,name,off in [(0,'Separation\n$\\gamma_0=45^\\circ$',(10,-24)),(m['apogee_time_s'],'Apogee',(0,12)),(r.ig,'Entry ignition',(-80,8)),(r.ig2,'Landing ignition',(-85,12)),(t[-1],'Ship',(-28,9))]:
 x=np.interp(tm,t,d['range'])/1000;y=np.interp(tm,t,d['h'])/1000;a.scatter(x,y,s=15,color=BLUE,zorder=3);a.annotate(name,(x,y),xytext=off,textcoords='offset points',fontsize=8,arrowprops={'arrowstyle':'-','lw':.5},ha='left')
a.set(xlabel='Surface range (km)',ylabel='CG altitude (km)',ylim=(-10,165));label(a,'(a) Mission geometry');grid(a)
th=np.radians(2);eb=np.array([np.sin(th),np.cos(th)]);ep=np.array([np.cos(th),-np.sin(th)]);H=32.5*np.cos(th)+5*abs(np.sin(th));cg=np.array([0,H]);foot=[cg-32.5*eb+sg*5*ep for sg in [-1,1]];poly=np.array([cg+s*eb+sg*3.5*ep for s,sg in [(-30.5,-1),(-30.5,1),(32.5,1),(32.5,-1)]])
b.add_patch(patches.Polygon(poly,facecolor='#eaf2f8',edgecolor='black',lw=.9));b.plot([-20,20],[0,0],color='black',lw=2);b.fill_between([-20,20],-.8,0,color='#bdbdbd')
for ff in foot:b.plot([cg[0]-27*eb[0],ff[0]],[cg[1]-27*eb[1],ff[1]],color='black',lw=1);b.plot(ff[0],ff[1],'ko',ms=3)
b.plot(0,H,'o',color=BLUE,ms=4);b.annotate('CG',(0,H),xytext=(11,H+6),arrowprops={'arrowstyle':'-','lw':.6},fontsize=8)
b.annotate('',xy=(-12,.2),xytext=(-12,65),arrowprops={'arrowstyle':'<->','lw':.7});b.text(-14,32,'65 m envelope',rotation=90,va='center',ha='center',fontsize=8)
b.annotate('',xy=(4,67),xytext=(-3,67),arrowprops={'arrowstyle':'<->','lw':.7});b.text(.5,69,'7 m',ha='center',fontsize=8)
b.annotate('',xy=(10,H),xytext=(10,.2),arrowprops={'arrowstyle':'<->','lw':.7});b.text(11,H/2,r'$\ell=32.5$ m',rotation=90,va='center',fontsize=8)
b.annotate('',xy=(-5,-3),xytext=(5,-3),arrowprops={'arrowstyle':'<->','lw':.7});b.text(0,-6,r'$2b=10$ m',ha='center',fontsize=8)
b.text(0,77,r'$\theta_d=2^\circ$ illustration',ha='center',fontsize=8);b.text(0,-11,'Deck width: 40 m (assumed)',ha='center',fontsize=8);b.set(xlim=(-23,24),ylim=(-14,82),aspect='equal');b.axis('off');label(b,'(b) Assumed local geometry');fig.tight_layout();save('fig01_mission_geometry')
# Workflow.
fig,ax=plt.subplots(figsize=(7,2.9));ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
boxes=[(.1,2.35,2.0,.95,'Inputs and assumptions\nG / L / H / U'),(2.65,2.35,2.05,.95,'Coupled model\ntranslation + pitch'),(5.3,2.35,2.0,.95,'Multiple shooting\nCasADi / IPOPT'),(7.8,2.35,2.0,.95,'Independent SI replay\nDOP853 + events'),(5.3,.45,2.0,1.0,'Path, actuator and\nfoot-contact checks'),(7.8,.45,2.0,1.0,'Nominal candidate\n+ evidence boundary')]
for x,y,ww,hh,s in boxes:ax.add_patch(patches.FancyBboxPatch((x,y),ww,hh,boxstyle='round,pad=.05',fc='#f5f7fa',ec=BLUE,lw=.8));ax.text(x+ww/2,y+hh/2,s,ha='center',va='center',fontsize=9)
for x1,y1,x2,y2 in [(2.12,2.82,2.6,2.82),(4.72,2.82,5.23,2.82),(7.33,2.82,7.73,2.82),(8.8,2.3,6.35,1.5),(7.35,.95,7.72,.95)]:ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops={'arrowstyle':'->','lw':.9})
ax.annotate('',xy=(6.3,2.32),xytext=(6.3,1.5),arrowprops={'arrowstyle':'->','lw':.9,'color':ORANGE});ax.text(6.45,1.85,'Reject / revise',fontsize=8,color=ORANGE);ax.text(.2,.9,'Physics assumptions, numerical verification,\nand real-vehicle validation remain distinct.',fontsize=9,color=GRAY);fig.tight_layout();save('fig02_workflow')
# Atmosphere and prescribed wind.
h=np.linspace(0,160000,801);rho=np.array([atmosphere(float(z))['density_kg_m3'] for z in h]);from replay import wind
fig,axs=plt.subplots(1,2,figsize=(7,3.3));axs[0].semilogx(rho,h/1000,color=BLUE);axs[0].axhline(86,color=ORANGE,ls='--',lw=.8);axs[0].text(1e-8,95,'H-class extrapolation',fontsize=8);axs[0].text(2e-7,70,'USSA lower atmosphere',fontsize=8);axs[0].set(xlabel=r'Density (kg m$^{-3}$)',ylabel='Altitude (km)');axs[1].plot(wind(h,0),h/1000,color=BLUE);axs[1].set(xlabel=r'Along-track wind (m s$^{-1}$)',ylabel='Altitude (km)');
for ax,s in zip(axs,['(a) Density closure','(b) Prescribed wind']):grid(ax);label(ax,s)
fig.tight_layout(w_pad=2);save('fig03_environment')
# Four requested trajectory histories.
fig,axs=plt.subplots(2,2,figsize=(7,5.35));axs[0,0].plot(d['range']/1000,d['h']/1000,color=BLUE);axs[0,0].set(xlabel='Surface range (km)',ylabel='CG altitude (km)');label(axs[0,0],'(a) Trajectory')
for ax,k,fac,yl,lab in [(axs[0,1],'speed',1,r'Ground speed (m s$^{-1}$)','(b) Ground speed'),(axs[1,0],'gamma',180/np.pi,r'Flight-path angle $\gamma$ (deg)','(c) Flight-path angle'),(axs[1,1],'h',.001,'CG altitude (km)','(d) Altitude')]:
 ax.plot(t,d[k]*fac,color=BLUE);ax.set(xlabel='Time after separation (s)',ylabel=yl);shade(ax);label(ax,lab)
for ax in axs.flat:grid(ax)
fig.tight_layout(w_pad=2,h_pad=1.8);save('fig04_trajectory')
# Actual actuator and attitude histories.
actual=np.zeros((len(t),7))
for i,tt in enumerate(t):
 us,aa,de=r.control(tt)
 if len(us)==7:actual[i]=us
 else:actual[i,[0,1,4]]=us
rate=np.full_like(t,np.nan)
for un,start,dur in [('U1',r.ig+1.6,float(w['dur1'])),('U2',r.ig2+1.6,float(w['dur2']))]:
 uu=w[un];mask=(t>=start)&(t<=start+dur);ind=np.minimum(((t[mask]-start)/dur*(uu.shape[1]-1)).astype(int),uu.shape[1]-2);sl=np.diff(uu[2])/(dur/(uu.shape[1]-1));rate[mask]=np.degrees(d['omega'][mask]+sl[ind])
fig,axs=plt.subplots(2,2,figsize=(7,5.6));a=axs[0,0]
for j,co,lab in [(0,BLUE,'Centre'),(1,ORANGE,'Ring +'),(4,GREEN,'Ring -')]:a.plot(t,actual[:,j],color=co,label=lab,lw=1)
a.fill_between(t,actual[:,[2,3,5,6]].min(axis=1),actual[:,[2,3,5,6]].max(axis=1),color=GRAY,alpha=.20,label='Other ring engines');a.axhline(.3,color=GRAY,ls=':',lw=.7);a.set(ylabel='Actual engine throttle',ylim=(-.03,1.16));a.legend(ncol=2,fontsize=6.8);label(a,'(a) Individual thrust allocation')
a=axs[0,1];
for k,co,lab in [('theta',BLUE,r'$\theta$'),('beta',ORANGE,r'$\beta$'),('delta',GREEN,r'$\delta$')]:a.plot(t,np.degrees(d[k]),color=co,label=lab,lw=1)
a.set(ylabel='Local angle (deg)',ylim=(-55,8));a.legend(ncol=3);label(a,'(b) Body and thrust direction')
a=axs[1,0];a.plot(t,np.degrees(d['omega']),color=BLUE,label=r'$\omega$');a.plot(t,rate,color=ORANGE,label='Inertial thrust slew',lw=1);a.axhline(5,color=GRAY,ls='--',lw=.7);a.axhline(-5,color=GRAY,ls='--',lw=.7);a.set(ylabel=r'Angular rate (deg s$^{-1}$)');a.legend(fontsize=7);label(a,'(c) Rates after ignition')
a=axs[1,1];a.plot(t,d['T']/1e6,color=BLUE);a.set(ylabel='Total engine thrust (MN)');label(a,'(d) Combined thrust')
for a in axs.flat:a.set(xlim=(250,366),xlabel='Time after separation (s)');shade(a);grid(a)
fig.tight_layout(w_pad=2,h_pad=1.7);save('fig05_controls')
# Selected screening limits.
fig,axs=plt.subplots(2,2,figsize=(7,5.3));axs[0,0].plot(t,d['q']/1000,color=BLUE);axs[0,0].axhline(50,color=ORANGE,ls='--',label='50 kPa screen');axs[0,0].set(ylabel='Dynamic pressure (kPa)');axs[0,0].legend();label(axs[0,0],'(a) Dynamic pressure')
axs[0,1].plot(t,d['n'],color=BLUE);axs[0,1].axhline(4,color=ORANGE,ls='--');axs[0,1].set(ylabel=r'Force budget $n_\Sigma$');label(axs[0,1],'(b) Non-gravity force budget')
alpha=np.where(d['q']>=10000,np.degrees(d['alpha']),np.nan);axs[1,0].plot(t,alpha,color=BLUE);axs[1,0].axhline(5,color=ORANGE,ls='--');axs[1,0].set(ylabel=r'Inflow angle $\alpha$ (deg)',ylim=(0,5.5));label(axs[1,0],'(c) Inflow angle where q >= 10 kPa')
lo=d['h']<=232.5;axs[1,1].plot(t[lo],np.abs(np.degrees(d['theta'][lo])),color=BLUE);axs[1,1].axhline(5,color=ORANGE,ls='--');axs[1,1].set(ylabel=r'Body tilt $|\theta|$ (deg)',ylim=(0,5.5));label(axs[1,1],'(d) Low-altitude verticalization')
for a in axs.flat:a.set_xlabel('Time after separation (s)');grid(a)
for a in [axs[0,0],axs[0,1],axs[1,0]]:a.set_xlim(250,365)
fig.tight_layout(w_pad=2,h_pad=1.7);save('fig06_screens')
# Propellant bookkeeping, one verified case only.
fig,axs=plt.subplots(1,2,figsize=(7,3.2));cum=0
for value,co,lab in [(m['first_burn_t'],BLUE,'Entry + shutdown tail'),(m['second_burn_t'],ORANGE,'Landing to first contact'),(m['remaining_t'],GREEN,'Remaining')]:
 axs[0].barh(0,value,left=cum,color=co,height=.45,label=lab);axs[0].text(cum+value/2,0,f'{value:.2f}' if value>5 else '',ha='center',va='center',color='white',fontsize=9);cum+=value
axs[0].annotate(f"{m['remaining_t']:.2f} t",(cum-m['remaining_t']/2,.23),xytext=(120,.65),arrowprops={'arrowstyle':'-','lw':.6},fontsize=8);axs[0].set(xlabel='Total propellant (t)',yticks=[],ylim=(-.65,1.0));axs[0].legend(loc='upper left',frameon=False,fontsize=7.2,ncol=1);label(axs[0],'(a) Allocation of the 140 t load')
axs[1].plot(t,(r.m0-d['m'])/1000,color=BLUE,label='Consumed');axs[1].plot(t,(d['m']-130000)/1000,color=ORANGE,label='Remaining');axs[1].axhline(140,color=GRAY,ls=':',lw=.7);axs[1].set(xlabel='Time after separation (s)',ylabel='Propellant mass (t)');axs[1].legend();grid(axs[1]);label(axs[1],'(b) Integrated mass balance');fig.tight_layout(w_pad=2);save('fig07_propellant')
# Fixed open-loop perturbations: contrast with nominal, stop at recorded event.
rows=list(csv.DictReader(open(D/'fixed_control_perturbations.csv',encoding='utf-8-sig')));names=[r'$C_D-15\%$',r'$C_D-20\%$',r'$I_{sp}-2\%$',r'Wind $\times 2$',r'Wind $\times 3$','Combined perturbation']
fig,axs=plt.subplots(3,2,figsize=(7,7.1),sharex=True)
for i,(ax,row,name) in enumerate(zip(axs.flat,rows,names)):
 z=np.load(D/f'stress_{i+1}.npz');ax.plot(t,d['vr'],color='black',lw=1,label='Nominal');ax.plot(z['t'],z['vr'],color=ORANGE,lw=1.2,label='Perturbed');ax.scatter(z['t'][-1],z['vr'][-1],color=ORANGE,s=13,zorder=5)
 outcome=('Sea-level foot event' if row['event']=='contact' else 'Usable propellant exhausted' if row['event']=='usable_propellant_exhausted' else 'No contact by planned end');annotation=f"{outcome}\n"+('$v_r$ = '+f"{float(row['vr_m_s']):.1f} m/s" if row['event']=='contact' else '$h$ = '+f"{float(row['height_m']):.1f} m")
 ax.text(.04,.93,annotation,transform=ax.transAxes,va='top',fontsize=7.3,bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':1});ax.set(xlim=(340,366),ylim=(-340,25),ylabel=r'$v_r$ (m s$^{-1}$)');label(ax,f'({chr(97+i)}) {name}');grid(ax)
axs[0,0].legend(loc='lower left',fontsize=7)
for ax in axs[-1]:ax.set_xlabel('Time after separation (s)')
fig.tight_layout(w_pad=2,h_pad=1.5);save('fig08_perturbations')
print('Generated 8 vector PDF figures and PNG previews from frozen v15 evidence.')
