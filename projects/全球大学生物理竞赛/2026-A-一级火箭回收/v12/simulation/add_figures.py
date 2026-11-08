"""Five manuscript figures from declared geometry and actual archived/replayed data."""
from pathlib import Path
import csv,json,math,hashlib
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,FancyBboxPatch,FancyArrowPatch,Arc
ROOT=Path(__file__).resolve().parents[1];P=ROOT.parent
BLUE='#26587f';TEAL='#238b83';ORANGE='#d17a29';RED='#ad3140';GRAY='#687381'

def read(path):
 rows=list(csv.DictReader(Path(path).open(encoding='utf-8-sig')))
 return {k:np.array([float(r[k]) for r in rows]) for k in rows[0]}
def save(fig,name):
 fig.savefig(ROOT/f'results/figures/{name}.png',dpi=240,bbox_inches='tight');fig.savefig(ROOT/f'results/figures/{name}.pdf',bbox_inches='tight');plt.close(fig)
def dim(ax,a,b,label,offset=(0,0),rotate=0,color=GRAY):
 ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='<->',color=color,lw=1))
 mid=(np.array(a)+b)/2;ax.text(mid[0]+offset[0],mid[1]+offset[1],label,ha='center',va='center',rotation=rotate,fontsize=10,color=color,bbox=dict(fc='white',ec='none',alpha=.82,pad=.7))
def mission():
 a=read(P/'v8/results/data/candidate_trajectory.csv');s=json.loads((P/'v8/results/data/replay_summary.json').read_text())
 fig=plt.figure(figsize=(8,7.2),layout='constrained');gs=fig.add_gridspec(2,2,width_ratios=[1.4,1],height_ratios=[1,1.15]);ax=fig.add_subplot(gs[0,0]);tm=fig.add_subplot(gs[1,0]);g=fig.add_subplot(gs[:,1])
 t=a['time_s'];x=a['range_m']/1000;y=a['height_m']/1000
 for l,r,col,label in [(0,40,GRAY,'Coast'),(40,s['toff_s'],ORANGE,'Entry burn'),(s['toff_s'],s['toff_s']+6.6,GRAY,'Transition'),(s['toff_s']+6.6,t[-1],TEAL,'Final burn')]:
  m=(t>=l)&(t<=r);ax.plot(x[m],y[m],color=col,lw=2,label=label)
 for tau,label,xytext in [(0,'Separation: 70 km\n6,000 km/h',(7,61)),(40,'Entry ignition request\nt = 40 s',(92,59)),(t[-1],'CG reference endpoint\n(not verified foot contact)',(96,13))]:
  pt=(np.interp(tau,t,x),np.interp(tau,t,y));ax.plot(*pt,'o',color=BLUE,ms=4);ax.annotate(label,pt,xytext=xytext,textcoords='data',fontsize=9.5,arrowprops={'arrowstyle':'->','color':GRAY},bbox=dict(fc='white',ec='none',alpha=.85))
 ax.set(xlim=(-5,218),ylim=(-2,76),xlabel='Surface arc range (km)',ylabel='CG altitude (km)',title='(a) Nominal M0 mission path');ax.grid(alpha=.2);ax.legend(loc='lower left',ncol=2,fontsize=8.5)
 tm.set(xlim=(0,1),ylim=(0,1));tm.axis('off');tm.set_title('(b) Command sequence and response',loc='left')
 items=[('Separation: engines initially off',BLUE),('Coast 0–40 s',GRAY),('Three-engine entry burn\nIgnition request 40 s; off request 160.42 s',ORANGE),('Response transition\nTwo-engine restart request 165.42 s',GRAY),('Two-engine final burn\nCG reference end 217.75 s',TEAL)]
 for i,(txt,col) in enumerate(items):
  yy=.85-i*.19;tm.add_patch(FancyBboxPatch((.02,yy-.065),.95,.145,boxstyle='round,pad=.008',ec=col,fc='white',lw=1.3));tm.text(.495,yy+.005,txt,ha='center',va='center',fontsize=10)
  if i<4:tm.annotate('',(.495,yy-.105),(.495,yy-.07),arrowprops=dict(arrowstyle='->',color=GRAY))
 th=math.radians(12);delta=math.radians(25);eb=np.array([math.sin(th),math.cos(th)]);ep=np.array([math.cos(th),-math.sin(th)]);cg=np.array([32.5*math.sin(th),40.]);B=cg-32.5*eb
 body=np.array([cg+(q-32.5)*eb+sgn*3.5*ep for q,sgn in [(2,-1),(65,-1),(65,1),(2,1)]]);feet=np.array([B-q*5*ep for q in [-1,1]])
 g.add_patch(Polygon(body,closed=True,fc='#e4edf4',ec=BLUE,lw=1.5));g.plot([B[0],cg[0]+32.5*eb[0]],[B[1],cg[1]+32.5*eb[1]],'--',color=GRAY,lw=.8)
 for pt in feet:g.plot([B[0],pt[0]],[B[1]+2,pt[1]],color=BLUE,lw=1.3)
 g.scatter(feet[:,0],feet[:,1],c=BLUE,s=24);g.scatter(*cg,c=RED,s=24,zorder=5);g.annotate('CG',cg,xytext=(9,0),textcoords='offset points',color=RED,fontsize=10)
 g.plot([-20,20],[0,0],color=BLUE,lw=2);g.add_patch(Polygon([[-20,0],[20,0],[16,-6],[-16,-6]],fc='#e4edf4',ec=BLUE));g.axvline(0,color=GRAY,ls=':',lw=.8)
 dim(g,np.array([0.,-10]),np.array([20.,-10]),'20 m half-width (H)',offset=(0,-2.4))
 dim(g,B-9*ep,B+65*eb-9*ep,'65 m (G)',offset=(-2,0),rotate=78)
 dim(g,B-5.8*ep,cg-5.8*ep,r'$\ell=32.5$ m (H)',offset=(-.8,0),rotate=78)
 dim(g,B-3*eb,B+5*ep-3*eb,r'$b=5$ m (H)',offset=(0,-1.6),rotate=-12)
 mid=cg+23*eb;dim(g,mid-3.5*ep,mid+3.5*ep,'7 m (G)',offset=(0,2.8),rotate=-12)
 g.plot([cg[0],cg[0]],[cg[1],cg[1]+18],':',color=GRAY);g.add_patch(Arc(cg,19,19,theta1=78,theta2=90,color=RED,lw=1.3));g.text(cg[0]+1.4,cg[1]+12,r'$\theta_d$',color=RED,fontsize=13)
 engine=cg+(2-32.5)*eb;direction=np.array([math.sin(th+delta),math.cos(th+delta)]);end=engine+18*direction;g.annotate('',end,engine,arrowprops=dict(arrowstyle='->',lw=2,color=ORANGE));g.text(end[0]+1,end[1]+1,r'$T$',color=ORANGE,fontsize=13)
 g.add_patch(Arc(engine,15,15,theta1=53,theta2=78,color=ORANGE,lw=1.3));g.annotate(r'$\delta$',engine+7*np.array([math.sin(th+delta/2),math.cos(th+delta/2)]),xytext=(15,16),fontsize=13,color=ORANGE,arrowprops=dict(arrowstyle='-',color=ORANGE))
 g.text(B[0]-2,B[1]-2,'B',fontsize=10);g.set(xlim=(-24,26),ylim=(-15,79),xlabel='Deck-frame x (m)',ylabel='Deck-frame z (m)',title='(c) Geometry / angle definitions');g.set_aspect('equal');g.grid(alpha=.15)
 save(fig,'mission_geometry')

def workflow():
 fig,ax=plt.subplots(figsize=(9,4.6));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
 cols=[BLUE,TEAL,ORANGE,GRAY];labels=[('G: given','70 km, speed, dry mass, size'),('L: literature','Earth / standard atmosphere'),('H: hypotheses','Engine family, drag, limits'),('U: unresolved','Torque, mass properties, legs')]
 for i,((title,desc),col) in enumerate(zip(labels,cols)):
  x=.012+i*.247;ax.add_patch(FancyBboxPatch((x,.80),.228,.16,boxstyle='round,pad=.008',fc='white',ec=col,lw=1.4));ax.text(x+.114,.91,title,ha='center',va='center',fontsize=11,color=col,weight='bold');ax.text(x+.114,.845,desc,ha='center',va='center',fontsize=9.8)
 boxes=[(.02,BLUE,'1  M0: translation','Spherical gravity + atmosphere\nVariable mass + engine response\nExplicit reference assumptions'),(.355,ORANGE,'2  Trajectory optimization','CasADi + IPOPT: local candidate\nRestricted engine schedule\nIndependent replay + perturbations'),(.69,GRAY,'3  M1: required completion','Attitude + force/moment allocation\nTrue foot contact + support dynamics\nThermal / structural capacities')]
 for x,col,title,desc in boxes:
  ax.add_patch(FancyBboxPatch((x,.35),.29,.34,boxstyle='round,pad=.012',fc='#f8fafc',ec=col,lw=1.5,ls='--' if x>.6 else '-'));ax.text(x+.145,.62,title,ha='center',fontsize=11,weight='bold',color=col);ax.text(x+.145,.48,desc,ha='center',va='center',fontsize=10,linespacing=1.7)
 ax.annotate('',(.343,.52),(.318,.52),arrowprops=dict(arrowstyle='->',lw=1.7,color=GRAY));ax.annotate('',(.678,.52),(.653,.52),arrowprops=dict(arrowstyle='->',lw=1.7,color=GRAY))
 ax.text(.165,.28,'Implemented model',ha='center',fontsize=10,color=BLUE);ax.text(.50,.28,'Nominal M0 verified',ha='center',fontsize=10,color=TEAL);ax.text(.835,.28,'Necessary checks only;\nfull M1 NOT YET SOLVED',ha='center',fontsize=9.7,color=RED)
 ax.annotate('',(.50,.18),(.835,.18),arrowprops=dict(arrowstyle='->',ls='--',color=ORANGE,connectionstyle='arc3,rad=-.20'));ax.text(.67,.065,'Replan when safety / actuator limits conflict',ha='center',fontsize=10,color=ORANGE)
 ax.annotate('',(.16,.70),(.16,.79),arrowprops=dict(arrowstyle='->',color=GRAY));ax.annotate('',(.835,.70),(.875,.79),arrowprops=dict(arrowstyle='->',ls='--',color=GRAY))
 fig.tight_layout();save(fig,'method_workflow')

def passive():
 path=P/'v5/results/data/passive_profiles.csv';rows=list(csv.DictReader(path.open(encoding='utf-8-sig')));cases=['vacuum_130t','air_130t_Cd0.5','air_130t_Cd1'];labels=['Vacuum: 2,034 m/s',r'$C_D=0.5$: 608 m/s',r'$C_D=1.0$: 296 m/s'];colors=[GRAY,ORANGE,TEAL]
 fig,ax=plt.subplots(figsize=(8.6,5.2));inset=ax.inset_axes([.10,.13,.42,.39]);checks=[]
 for i,name in enumerate(cases):
  r=[x for x in rows if x['case']==name];x=np.array([float(q['arc_range_m'])/1000 for q in r]);y=np.array([float(q['height_m'])/1000 for q in r]);ax.plot(x,y,lw=2,color=colors[i],ls=['-.','--','-'][i],label=labels[i]);inset.plot(x,y,color=colors[i],ls=['-.','--','-'][i],lw=1.5);ax.plot(x[-1],0,'o',color=colors[i]);ax.annotate(['2,034 m/s','608 m/s','296 m/s'][i],(x[-1],0),xytext=(219,16-6*i),fontsize=10,color=colors[i],arrowprops=dict(arrowstyle='-',color=colors[i]));checks.append(dict(case=name,surface_speed_m_s=float(r[-1]['speed_m_s']),range_km=float(x[-1]),height_m=float(r[-1]['height_m'])))
 ax.set(xlabel='Surface arc range (km)',ylabel='CG altitude (km)',xlim=(0,265),ylim=(-2,73),title='Passive descent: dry 130 t body, no thrust');ax.legend(loc='upper left',fontsize=10);ax.grid(alpha=.2)
 inset.set(xlim=(180,207),ylim=(0,17),xlabel='Range (km)',ylabel='Height (km)');inset.tick_params(labelsize=8);inset.xaxis.label.set_size(9);inset.yaxis.label.set_size(9);inset.grid(alpha=.2);fig.tight_layout();save(fig,'passive_diagnostics')
 (ROOT/'results/data/passive_figure_endpoints.json').write_text(json.dumps(checks,indent=2));return path

def response():
 t=np.linspace(-.2,3.0,1601);u=np.where(t<=.5,0,np.where(t<=1.5,t-.5,1.1-.1*np.exp(-(t-1.5)/.1)));du=np.where(t<.5,0,np.where(t<=1.5,1,np.exp(-(t-1.5)/.1)))
 fig,ax=plt.subplots(2,1,figsize=(8.2,4.8),sharex=True,layout='constrained',height_ratios=[2,1])
 for a in ax:
  for l,r,c in [(0,.5,GRAY),(.5,1.5,ORANGE),(1.5,3,TEAL)]:a.axvspan(l,r,color=c,alpha=.10)
  a.grid(alpha=.2);a.set_xlim(-.2,3)
 ax[0].step(t,np.where(t>=0,1.1,0),where='post',ls='--',color=GRAY,label='Ignition-requested target');ax[0].plot(t,u,color=BLUE,lw=2,label='Actual throttle');ax[0].scatter([.5,1.5,1.6],[0,1,1.1-.1/math.e],c=BLUE,s=20);ax[0].annotate('0.5 s delay',(.25,.16),ha='center',fontsize=10);ax[0].text(.95,.80,'Rate-limited ramp\n1.0 s to u = 1.0',ha='center',fontsize=10);ax[0].text(2.27,.75,'Exponential tail\ntime constant = 0.1 s',ha='center',fontsize=10);ax[0].set(ylabel='Normalized throttle u',ylim=(-.05,1.3));ax[0].legend(loc='upper left',fontsize=9.5)
 ax[1].plot(t,du,color=ORANGE,lw=1.8);ax[1].axhline(1,color=GRAY,ls='--');ax[1].text(2.1,.78,r'$|\dot u|\leq1\ \mathrm{s}^{-1}$',fontsize=12);ax[1].set(ylabel=r'$\dot u$ (1/s)',xlabel='Time from ignition request (s)',ylim=(-.05,1.15));save(fig,'throttle_response')
 assert abs(u[np.argmin(abs(t-.5))])<.002 and max(du)<=1+1e-12

def sensitivities():
 base=ROOT/'results/data/sensitivity';idx=json.loads((base/'replay_index.json').read_text());nom=read(base/'nominal.csv')
 titles={'Cd_minus10pct':r'$C_D$: -10%','Cd_plus10pct':r'$C_D$: +10%','Isp_minus1pct':r'$I_{sp}$: -1%','Isp_plus1pct':r'$I_{sp}$: +1%','rho_minus5pct':r'$\rho$: -5%','rho_plus5pct':r'$\rho$: +5%','initial_vt_minus1m_s':r'$v_{t,0}$: -1 m/s','initial_vt_plus1m_s':r'$v_{t,0}$: +1 m/s','initial_vr_minus1m_s':r'$v_{r,0}$: -1 m/s'}
 fig,axs=plt.subplots(3,3,figsize=(8.8,8.5),sharex=True,sharey=True,layout='constrained');full,af=plt.subplots(3,3,figsize=(8.8,8.5),sharex=True,sharey=True,layout='constrained')
 for i,entry in enumerate(idx['cases']):
  name=entry['name'];s=entry['summary'];a=read(base/(name+'.csv'));f=s['final'];event=s['event']
  if event=='REFERENCE_CONTACT':txt=f"Reference speed outside limits\nvr = {f['vr_m_s']:.2f}, vt = {f['vt_m_s']:.2f} m/s";marker='o'
  elif event=='USABLE_PROPELLANT_EXHAUSTED':txt=f"Usable propellant exhausted\nhCG = {f['height_m']:.1f} m";marker='^'
  else:txt=f"No reference contact by tf\nhCG = {f['height_m']:.1f} m";marker='s'
  for ax,terminal in [(axs.flat[i],True),(af.flat[i],False)]:
   scale=1 if terminal else 1000;offset=32.5 if terminal else 0
   ax.plot(nom['time_s'],(nom['height_m']-offset)/scale,color=BLUE,ls='--',lw=1.7,label='Nominal');ax.plot(a['time_s'],(a['height_m']-offset)/scale,color=RED,lw=1.5,label='Perturbed');ax.plot(a['time_s'][-1],(a['height_m'][-1]-offset)/scale,marker,color=RED,ms=5)
   ax.axhline(0,color=GRAY,lw=.7);ax.set_title(titles[name],fontsize=12);ax.grid(alpha=.2);ax.tick_params(labelsize=9);ax.text(.025,.97,txt,transform=ax.transAxes,ha='left',va='top',fontsize=9.6,color=RED,bbox=dict(fc='white',ec='none',alpha=.90,pad=1.5))
   if terminal:ax.set(xlim=(180,220),ylim=(-80,3900))
   else:ax.set(xlim=(0,220),ylim=(-1,72))
   if i>=6:ax.set_xlabel('Time (s)',fontsize=11)
   if i%3==0:ax.set_ylabel('CG height - 32.5 m (m)' if terminal else 'CG altitude (km)',fontsize=10)
 z=read(base/'initial_vt_plus1m_s.csv');zi=axs.flat[7].inset_axes([.43,.25,.53,.30]);zi.plot(nom['time_s'],nom['height_m']-32.5,color=BLUE,ls='--',lw=1.3);zi.plot(z['time_s'],z['height_m']-32.5,color=RED,lw=1.3);zi.plot(z['time_s'][-1],z['height_m'][-1]-32.5,'s',color=RED,ms=3);zi.set(xlim=(214,218),ylim=(-2,70));zi.tick_params(labelsize=8);zi.grid(alpha=.2)
 axs.flat[7].legend(loc='upper right',bbox_to_anchor=(1,.82),fontsize=9)
 af.flat[7].legend(loc='upper right',bbox_to_anchor=(1,.82),fontsize=9)
 fig.suptitle('Nine frozen-plan perturbations: terminal trajectories and actual stop events',fontsize=13);full.suptitle('Supplement: full descent histories for the same nine perturbations',fontsize=13)
 save(fig,'sensitivity_grid');save(full,'sensitivity_full_history')

def run():
 plt.rcParams.update({'font.family':'DejaVu Serif','font.size':11,'axes.unicode_minus':False,'axes.grid':False})
 mission();workflow();path=passive();response();sensitivities()
 hashes=json.loads((ROOT/'references/input_hashes.json').read_text());hashes[str(path.relative_to(P))]=hashlib.sha256(path.read_bytes()).hexdigest();(ROOT/'references/input_hashes.json').write_text(json.dumps(hashes,indent=2))
 print('Five requested figures plus a full-history sensitivity supplement generated')
if __name__=='__main__':run()
