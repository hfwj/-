from pathlib import Path
import json,csv
B=Path(__file__).resolve().parent.parent;L=B/'reports/latex';T=L/'tables';T.mkdir(exist_ok=True)
m=json.load(open(B/'results/data/metrics.json'));v=json.load(open(B/'results/data/verification.json'));p=json.load(open(B/'results/data/physics_checks.json'))
values={'Load':(m['propellant_initial_t'],0),'EntryFuel':(m['first_burn_t'],3),'LandingFuel':(m['second_burn_t'],3),'ConsumedFuel':(m['first_burn_t']+m['second_burn_t'],3),'RemainingFuel':(m['remaining_t'],3),'FlightTime':(m['contact_s'],3),'Range':(m['range_km'],3),'Apogee':(m['apogee_km'],3),'ApogeeTime':(m['apogee_time_s'],1),'FirstIgnition':(m['ignition1_s'],2),'EntryOff':(m['shutdown1_command_s'],3),'SecondIgnition':(m['ignition2_s'],3),'PeakQ':(m['qmax_kPa'],3),'PeakN':(m['n_sum_max'],4),'PeakAlpha':(m['alpha_highq_max_deg'],3),'PeakTilt':(m['low_height_max_tilt_deg'],3),'PeakGimbal':(m['max_gimbal_deg'],3),'PeakOmega':(m['max_omega_deg_s'],3),'PeakSlew':(m['inertial_thrust_rate_max_deg_s'],3),'FinalVr':(m['vr_contact_m_s'],4)}
(L/'numbers.tex').write_text('% Automatically generated from frozen v15 evidence.\n'+'\n'.join('\\newcommand{\\'+k+'}{'+f'{x:.{n}f}'+'}' for k,(x,n) in values.items())+'\n')
# Stage table: no interpolation of failed trajectories.
rows=[]
for s in m['stages']:
 names={'无推力上升':'Unpowered ascent','无推力下降':'Unpowered descent','七机再入燃烧':'Seven-engine entry burn','关机尾流与滑行':'Shutdown tail and coast','三机着陆燃烧':'Three-engine landing burn'}
 rows.append(f"{names[s['stage']]} & {s['start_s']:.2f}--{s['end_s']:.2f} & {s['start_h_km']:.3f}--{s['end_h_km']:.3f} & {s['start_speed_m_s']:.1f}--{s['end_speed_m_s']:.2f} & {s['propellant_t']:.3f} \\\\")
(T/'stages.tex').write_text('\\newcommand{\\StageRows}{%\n'+'\n'.join(rows)+'\n}\n')
rows=[]
for name,x in [('Initial carried propellant',m['propellant_initial_t']),('Entry burn including shutdown tail',m['first_burn_t']),('Landing burn to first foot contact',m['second_burn_t']),('Remaining at first foot contact',m['remaining_t'])]:rows.append(f'{name} & {x:.3f} & {x/4.4:.3f} & {x*3.4/4.4:.3f} \\\\')
(T/'fuel.tex').write_text('\\newcommand{\\FuelRows}{%\n'+'\n'.join(rows)+'\n}\n')
rr=list(csv.DictReader(open(B/'results/data/fixed_control_perturbations.csv',encoding='utf-8-sig')));names=[r'$C_D-15\%$',r'$C_D-20\%$',r'$I_{sp}-2\%$',r'Wind $\times2$',r'Wind $\times3$','Combined']
rows=[]
for name,z in zip(names,rr):
 ev={'contact':'Sea-level foot event','usable_propellant_exhausted':'Usable fuel exhausted','time_limit':'Planned end; no contact'}[z['event']]
 rows.append(f"{name} & {ev} & {float(z['height_m']):.1f} & {float(z['vr_m_s']):.2f} & {float(z['qmax_kPa']):.2f} & Fail \\\\")
(T/'perturbations.tex').write_text('\\newcommand{\\PerturbationRows}{%\n'+'\n'.join(rows)+'\n}\n')
for path in T.glob('*.tex'):print(path.name,len(path.read_text().splitlines()))
