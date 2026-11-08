"""Generate every plotted curve, table and manuscript number from run files."""
from pathlib import Path
import json,csv,hashlib,platform,subprocess,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from model import ROOT,CONFIG,COLUMNS
D=ROOT/'results/data';F=ROOT/'results/figures';L=ROOT/'reports/latex';(L/'tables').mkdir(parents=True,exist_ok=True)
load=lambda name:json.loads((D/name).read_text())
r=load('selected.json');conv=load('convergence.json');search=load('load_search.json');strategies=load('strategies.json');sens=load('sensitivity.json')
h=np.load(D/'convergence_0.005.npz')['history'];idx={k:i for i,k in enumerate(COLUMNS)}
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
blue='#1f4e79';red='#b03a2e';green='#2e7d32'
def save(name,fig):
 fig.tight_layout();fig.savefig(F/(name+'.pdf'),bbox_inches='tight');fig.savefig(F/(name+'.png'),dpi=190,bbox_inches='tight');plt.close(fig)
def mark(ax):
 for t,c in [(r['entry_start_s'],red),(r['entry_cut_s'],red),(r['landing_start_s'],green),(r['contact_s'],'.4')]:ax.axvline(t,color=c,lw=.7,ls='--',alpha=.55)
 ax.grid(alpha=.18)
for name,values,ylabel in [('speed',h[:,17],'Ground speed (m/s)'),('gamma',np.degrees(np.arctan2(h[:,4],h[:,3])),'Flight-path angle (deg)'),('height',h[:,2]/1000,'CM altitude (km)')]:
 fig,ax=plt.subplots(figsize=(7,3.3));ax.plot(h[:,0],values,color=blue,lw=1.7);mark(ax);ax.set(xlabel='Time after separation (s)',ylabel=ylabel);save(name,fig)
fig,ax=plt.subplots(figsize=(7,3.8));ax.plot(h[:,1]/1000,h[:,2]/1000,color=blue,lw=1.6)
for key,label,c in [('entry_start_s','Entry ignition',red),('entry_cut_s','Entry cutoff',red),('landing_start_s','Terminal ignition',green),('contact_s','Ship',green)]:
 i=np.argmin(abs(h[:,0]-r[key]));ax.scatter(h[i,1]/1000,h[i,2]/1000,color=c,s=18);ax.annotate(label,xy=(h[i,1]/1000,h[i,2]/1000),xytext=(-8,12 if label!='Entry cutoff' else -22),textcoords='offset points',ha='right',fontsize=9)
ax.set(xlabel='Surface range (km)',ylabel='CM altitude (km)');ax.grid(alpha=.18);save('trajectory',fig)
fig,axs=plt.subplots(2,2,figsize=(8,5.8));t=h[:,0]
axs[0,0].plot(t,h[:,8]/1000,color=blue);axs[0,0].axhline(CONFIG['Q_LIMIT']/1000,color=red,ls='--',label='Acceptance');axs[0,0].set_ylabel('Dynamic pressure (kPa)');axs[0,0].legend(fontsize=8)
axs[0,1].plot(t,h[:,10]/1e6,color=blue);axs[0,1].set_ylabel('Thrust (MN)')
mask=np.isin(h[:,11],[2,5]);angle=np.where(mask,np.degrees(np.remainder(h[:,6]-np.pi/2+np.pi,2*np.pi)-np.pi),np.nan)
axs[1,0].plot(t,angle,color=blue);axs[1,0].set_ylabel('Powered thrust-axis tilt (deg)')
axs[1,1].plot(t,h[:,9],color=blue);axs[1,1].axhline(CONFIG['N_LIMIT'],color=red,ls='--');axs[1,1].set_ylabel('Specific non-gravity load (g0)')
for ax in axs.flat:ax.set_xlabel('Time (s)');ax.grid(alpha=.18)
save('controls',fig)
fig,axs=plt.subplots(1,2,figsize=(8,3.6))
for k,s in enumerate(strategies):
 x=np.load(D/(f'strategy_S{k}.npz' if k<2 else 'convergence_0.005.npz'))['history'];label='S'+str(k)+(': pass' if s['pass'] else ': fail')
 axs[0].plot(x[:,0],x[:,2]/1000,label=label);axs[1].plot(x[:,0],x[:,8]/1000,label=label)
axs[0].set(ylabel='CM altitude (km)',xlabel='Time (s)');axs[1].set(ylabel='Dynamic pressure (kPa)',xlabel='Time (s)');axs[1].axhline(50,color=red,ls='--',lw=.8)
for ax in axs:ax.grid(alpha=.18);ax.legend(fontsize=8)
save('strategies',fig)
# CSVs retain full double precision; all display rounding happens below.
for name,rows in [('convergence',conv),('load_search',search),('strategies',strategies),('sensitivity',sens)]:
 keys=[k for k in rows[0] if not isinstance(rows[0][k],(list,dict))]
 with (D/(name+'.csv')).open('w',newline='') as f:
  w=csv.DictWriter(f,keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
def table(name,caption,heads,rows,note='',spec=None,label=None):
 spec=spec or '@{}'+'l'*len(heads)+'@{}';s='\\begin{table}[htbp]\n\\centering\\small\n\\caption{'+caption+'}\n\\label{tab:'+ (label or name)+'}\n\\begin{tabularx}{\\linewidth}{'+spec+'}\n\\toprule\n'+' & '.join(heads)+r' \\'+'\n\\midrule\n'+'\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)+'\n\\bottomrule\n\\end{tabularx}\n'
 if note:s+='\\par\\smallskip{\\footnotesize '+note+'}\n'
 s+='\\end{table}\n';(L/'tables'/(name+'.tex')).write_text(s)
def fmt(x,n=3):return f'{x:.{n}f}'
def fail(row):
 reasons=[]
 if not row['contact_event']:reasons.append('No contact')
 if row['exhaust_s']>=0:reasons.append('Exhausted')
 if row['residual_kg']<CONFIG['RESERVE']:reasons.append('Reserve')
 if -row['vz_mps']>CONFIG['VZ_LIMIT'] or row['vz_mps']>0:reasons.append('Vertical speed')
 if abs(row['vx_mps'])>CONFIG['VX_LIMIT']:reasons.append('Horizontal speed')
 if row['qmax_pa']>CONFIG['Q_LIMIT']:reasons.append('Pressure')
 if row['nmax']>CONFIG['N_LIMIT']:reasons.append('Load')
 if row['tilt_deg']>CONFIG['TILT_LIMIT_DEG']:reasons.append('Tilt')
 return ', '.join(reasons) if reasons else 'Pass'
table('cd','All 12 assumed axial drag anchors (H).',['Mach',r'$C_D$'],[[fmt(m,2),fmt(c,2)] for m,c in zip(CONFIG['CD_M'],CONFIG['CD_Y'])],note='Piecewise-linear interpolation in Mach; endpoint values are held outside the tabulated domain. These are declared assumptions, not recovered or measured booster data.',spec='@{}rX@{}')
table('wind','Prescribed along-track wind profile (H).',['Altitude (km)','Wind (m/s)'],[[fmt(x/1000,0),fmt(y,0)] for x,y in zip(CONFIG['WIND_H'],CONFIG['WIND_U'])],note='Piecewise-linear interpolation; no vertical wind or cross-track motion is represented.',spec='@{}rX@{}')
table('search_domain','Search domain, normalized parameter coordinates, and selected control.',['Variable','Range','Selected'],[[r'$h_e$ (km)','35--82',fmt(r['parameters'][0]/1000,6)],[r'$v_{cut}$ (m/s)','450--1150',fmt(r['parameters'][1],6)],[r'$k$','0.95--1.60',fmt(r['parameters'][2],8)],[r'$V_{td}$ (m/s)','0.5--2.0',fmt(r['parameters'][3],8)]],note='Full-precision selected.json supplies the fixed control vector in the step study. The finite search does not certify global optimality.',spec='@{}lXX@{}')
pen=[['Downward speed','2.2 m/s',r'$[-w_f/2.2-1]_+$','2.5 m/s'],['Upward velocity','2.2 m/s',r'$[w_f/2.2]_+$',r'$w_f\le0$'],['Horizontal speed','0.8 m/s',r'$[|u_f|/0.8-1]_+$','1.0 m/s'],['Peak pressure','47.5 kPa',r'$[q_{max}/47500-1]_+$','50 kPa'],['Load factor','3.9',r'$[n_{max}/3.9-1]_+$','4.0'],['Final tilt',r'$1.8^\circ$',r'$[|\theta_f|/1.8^\circ-1]_+$',r'$2^\circ$'],['Residual propellant','1500 kg',r'$[(1500-m_{res})/1500]_+$','1000 kg']]
table('penalty','Dimensionless penalties and separate acceptance limits.',['Channel','Design scale',r'$r_i$','Acceptance'],pen,note=r'$[x]_+=\max(x,0)$. Pressure in the residual is expressed in Pa; angles use the displayed degree ratio. The mass scale is $m_*=100000$ kg, the common penalty weight is 1000, and a no-contact run receives $10^8+m_{used}/m_*$.',spec='@{}lXlX@{}')
table('scan','Sequential 10 t load search; each row has its own searched control.',['Load (t)','Used (t)','Entry (t)','Terminal (t)',r'$q_{max}$ (kPa)','Outcome'],[[fmt(x['load_t'],0),fmt(x['used_kg']/1000),fmt(x['entry_kg']/1000),fmt(x['landing_kg']/1000),fmt(x['qmax_pa']/1000,2),'Pass' if x['pass'] else 'Fail'] for x in search],note='Search uses 0.1 s and validation 0.02 s. Failed rows show consumption before contact or exhaustion, not the fuel required for a successful terminal burn. Failure details and every row\'s parameters are retained in \\texttt{load\\_search.json}.',spec='@{}rrrrrX@{}')
table('strategy','Three strategies at the selected initial load, all replayed at 0.005 s.',['Policy','Entry (t)','Terminal (t)',r'$|w_f|$ (m/s)',r'$q_{max}$ (kPa)','Screen'],[[f'S{i}',fmt(x['entry_kg']/1000),fmt(x['landing_kg']/1000),fmt(abs(x['vz_mps'])),fmt(x['qmax_pa']/1000,2),'Pass' if x['pass'] else 'Fail'] for i,x in enumerate(strategies)],note='S0: entry from 75 to 55 km, k=1.30 and target 1.50 m/s; S1: 75 km entry with a 750 m/s cutoff, k=1.40 and target 1.50 m/s; S2: searched parameters in the search-domain table. All three use the same environment, actuator model, acceptance screen, and terminal law.',spec='@{}lrrrrX@{}')
burns=[]
for label,used,t0,t1,peak,ix,iz in [('Entry',r['entry_kg'],r['entry_start_s'],r['entry_cut_s'],r['entry_peak_N'],r['entry_impulse_x_Ns'],r['entry_impulse_z_Ns']),('Terminal',r['landing_kg'],r['landing_start_s'],r['contact_s'],r['landing_peak_N'],r['landing_impulse_x_Ns'],r['landing_impulse_z_Ns'])]:
 dur=t1-t0;burns.append(dict(name=label,used_t=used/1000,methane_t=used/4400,oxygen_t=used*3.4/4400,duration_s=dur,mean_scalar_MN=used*CONFIG['ISP']*CONFIG['G0']/dur/1e6,peak_MN=peak/1e6,mean_Fx_MN=ix/dur/1e6,mean_Fz_MN=iz/dur/1e6))
(D/'burns.json').write_text(json.dumps(burns,indent=2))
table('burns','Propellant species and scalar thrust for the two powered phases.',['Burn','Total (t)',r'CH$_4$ (t)',r'O$_2$ (t)','Duration (s)','Mean/peak (MN)'],[[x['name'],fmt(x['used_t']),fmt(x['methane_t']),fmt(x['oxygen_t']),fmt(x['duration_s'],3),fmt(x['mean_scalar_MN'],3)+' / '+fmt(x['peak_MN'],3)] for x in burns],note=r'The oxygen-to-methane mass ratio is 3.4. Mean scalar thrust equals $m_{used} I_{sp}g_0/\Delta t$. Counts during terminal braking are selected by the explicit 7-to-3-to-2 guards; shutdown is idealized as instantaneous.',spec='@{}lrrrrX@{}')
table('force','Mean local thrust components, computed from integrated applied force.',['Burn',r'$\overline T_x$ (MN)',r'$\overline T_z$ (MN)','Direction'],[[x['name'],fmt(x['mean_Fx_MN']),fmt(x['mean_Fz_MN']),'Upward and against downrange motion'] for x in burns],note='Components refer to the local tangent and upward directions at each instant. They are not a single vector impulse in a fixed inertial frame. Exhaust points opposite the thrust axis.',spec='@{}lrrX@{}')
table('convergence','Actual fixed-control step-halving results; no reoptimization.',['Step (s)','Consumed (kg)',r'$|w_f|$ (m/s)',r'$q_{max}$ (Pa)','Contact time (s)'],[[fmt(x['dt'],3),fmt(x['used_kg'],6),fmt(abs(x['vz_mps']),9),fmt(x['qmax_pa'],6),fmt(x['contact_s'],9)] for x in conv],note='Digits expose numerical changes only, not physical accuracy. Every row passes the same nominal acceptance screen. The 0.005 s run supplies the final reported trajectory.',spec='@{}rrrrr@{}')
ref=conv[-1];deltas=[]
for x in conv[:-1]:
 deltas.append([fmt(x['dt'],3),fmt(x['used_kg']-ref['used_kg'],6),f"{abs(x['vz_mps'])-abs(ref['vz_mps']):.8f}",fmt(x['qmax_pa']-ref['qmax_pa'],6),f"{1000*(x['contact_s']-ref['contact_s']):.6f}"])
table('differences','Signed differences relative to the 0.005 s run.',['Step (s)',r'$\Delta m$ (kg)',r'$\Delta |w_f|$ (m/s)',r'$\Delta q$ (Pa)',r'$\Delta t_f$ (ms)'],deltas,spec='@{}rrrrr@{}')
events=[('Entry request','entry_request_s'),('Entry thrust begins','entry_start_s'),('Entry cutoff','entry_cut_s'),('Terminal request','landing_request_s'),('Terminal thrust begins','landing_start_s'),('Pressure override on','q_override_on_s'),('Pressure override off','q_override_off_s'),('7 to 3 engines','stage3_s'),('3 to 2 engines','stage2_s'),('Geometric contact','contact_s')]
table('events','Actual event-time comparison under step halving.',['Event','0.02 s step','0.01 s step','0.005 s step'],[[name]+[fmt(x[k],9) if x[k]>=0 else '---' for x in conv] for name,k in events],note='All entries are seconds after separation. Crossing guards are located by 30 bisections of a re-integrated RK4 substep; actuator saturation remains piecewise smooth.',spec='@{}Xrrr@{}')
table('sensitivity','Fixed-control perturbations at the selected load.',['Change','Used (t)',r'$|w_f|$ (m/s)',r'$q_{max}$ (kPa)',r'$\Delta s$ (m)','Screen'],[[x['case'].replace('%',r'\%'),fmt(x['used_kg']/1000),fmt(abs(x['vz_mps'])),fmt(x['qmax_pa']/1000,2),fmt(x['range_shift_m'],1),'Pass' if x['pass'] else 'Fail'] for x in sens],note='The screen tests velocity, load, tilt and fuel, not a fixed-ship position constraint. Range shifts are measured relative to the nominal ship location; passing the screen does not establish robust deck capture.',spec='@{}Xrrrrl@{}')
# All scalar manuscript values are data macros, never hand copied old results.
macros={'Load':fmt(r['load_t'],0),'Used':fmt(r['used_kg']/1000,3),'Reserve':fmt(r['residual_kg']/1000,3),'Wf':fmt(abs(r['vz_mps']),3),'Uf':fmt(abs(r['vx_mps']),4),'Qmax':fmt(r['qmax_pa']/1000,3),'Nmax':fmt(r['nmax'],4),'Tilt':fmt(r['tilt_deg'],4),'Range':fmt(r['range_m']/1000,3),'Apogee':fmt(r['apogee_m']/1000,3),'Tf':fmt(r['contact_s'],6),'EntryFuel':fmt(r['entry_kg']/1000,3),'TerminalFuel':fmt(r['landing_kg']/1000,3),'FineDm':fmt(abs(conv[1]['used_kg']-ref['used_kg']),6),'FineDv':f"{abs(conv[1]['vz_mps']-ref['vz_mps']):.8f}",'FineDq':fmt(abs(conv[1]['qmax_pa']-ref['qmax_pa']),6),'FineDt':fmt(abs(conv[1]['contact_s']-ref['contact_s'])*1000,6)}
(L/'numbers.tex').write_text('\n'.join('\\newcommand{\\R'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
# Numerical identities and replay evidence, independent of the search objective.
wind=np.interp(h[:,2],CONFIG['WIND_H'],CONFIG['WIND_U']);power=h[:,13]*(h[:,3]-wind)+h[:,14]*h[:,4]
assert np.max(power)<1e-5
assert abs(r['entry_kg']+r['landing_kg']-r['used_kg'])<1e-7
assert abs(r['used_kg']+r['residual_kg']-r['load_t']*1000)<1e-7
step=np.diff(h[:,0]);mask=(step>1e-10)&(h[1:,11]==h[:-1,11])&np.isin(h[1:,11],[2,5])&(h[1:,12]==h[:-1,12])
slew=np.max(abs(np.diff(h[:,7])[mask]/step[mask]));assert slew<=CONFIG['SLEW']+1e-6
vac=load('vacuum_checks.json')
checks=dict(drag_power_max_W=float(np.max(power)),mass_budget_error_kg=float(r['used_kg']+r['residual_kg']-r['load_t']*1000),entry_plus_terminal_error_kg=float(r['entry_kg']+r['landing_kg']-r['used_kg']),measured_throttle_slew_per_s=float(slew),vacuum=vac,all_three_steps_pass=all(x['pass'] for x in conv),step_change_fine_mass_kg=float(conv[1]['used_kg']-ref['used_kg']),step_change_fine_speed_mps=float(abs(conv[1]['vz_mps'])-abs(ref['vz_mps'])),step_change_fine_q_pa=float(conv[1]['qmax_pa']-ref['qmax_pa']),step_change_fine_contact_s=float(conv[1]['contact_s']-ref['contact_s']))
# Independent trapezoidal check of mass flow on smooth same-phase intervals.
state_loss=float(np.sum((h[:-1,5]-h[1:,5])[mask]))
flux=float(np.sum((.5*(h[:-1,10]+h[1:,10])*step/(CONFIG['ISP']*CONFIG['G0']))[mask]))
checks['independent_smooth_interval_massflow_error_kg']=state_loss-flux
assert abs(state_loss-flux)<.1
(D/'verification.json').write_text(json.dumps(checks,indent=2))
table('identities','Measured numerical identity checks.', ['Check','Measured value','Criterion'],[
 ['Vacuum energy relative drift',f"{vac['energy_relative_drift']:.3e}",r'$<10^{-9}$'],
 ['Vacuum angular-momentum drift',f"{vac['angular_momentum_relative_drift']:.3e}",r'$<10^{-9}$'],
 ['Vacuum mass change (kg)',f"{vac['constant_mass_error_kg']:.3e}",r'$<10^{-8}$'],
 ['Smooth-interval mass-flow residual (kg)',f"{state_loss-flux:.6f}",r'$<0.1$ in magnitude'],
 ['Active-engine throttle slew (1/s)',f"{slew:.9f}",r'$\le1+10^{-6}$']],
 note='The mass-flow residual compares state mass loss with an independent trapezoidal integral of recorded scalar thrust divided by $I_{sp}g_0$, excluding discontinuous phase/count boundaries.',spec='@{}Xrl@{}')

import scipy
manifest=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],platform=platform.platform(),inputs={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'simulation').iterdir() if f.suffix in ['.json','.py','.cpp']},no_original_manuscript_data_used=True)
(D/'execution_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Published figures, tables, full-precision CSVs, and verification record.')

# Synchronize printed executable-source listings with this exact run.
import shutil
(L/'code').mkdir(exist_ok=True)
for name in ['model.py','search.py','reproduce.py','config.h']:
 shutil.copy2(ROOT/'simulation'/name,L/'code'/name)
core=(ROOT/'simulation/core.cpp').read_text()
(L/'code/numerics.cpp').write_text(core[core.index('static S rhs'):core.index('// Event identifiers')])
