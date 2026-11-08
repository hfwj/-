from pathlib import Path
import json,csv,re,subprocess,shutil,io
from docx import Document
from docx.shared import Inches,Pt,Mm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]

def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(str(x).replace('|',r'\vert ') for x in row)+' |' for row in rows])
def build(team='TBA'):
 if not re.fullmatch(r'[A-Za-z0-9-]+',team):raise ValueError('Use a team-number placeholder or digits, without personal identifiers')
 d=json.loads((ROOT/'results/data/evidence.json').read_text());s=d['nominal'];f=s['final'];n=d['audit']['nominal'];final=n['final'];v=d['verification'];checks=d['checks'];metric=d['reliability']
 parameters=[['Separation altitude; speed','70 km; 6,000 km/h','G','Problem statement [1]'],['Dry mass; height; diameter','130 t; 65 m; 7.0 m','G','Problem statement [1]'],['Propellant species','Liquid oxygen and methane','G','Problem statement [1]'],['Earth radius; gravity parameter',r'$R=6371000$ m; $\mu=3.986004418\times10^{14}$ m$^3$/s$^2$','L','Spherical approximation [3,4]'],['Density model','USSA 1976, geometric 0--70 km','L/H','Reference atmosphere [2]; domain chosen'],['Initial flight-path angle; wind','0 degrees; zero','H','Unspecified by the problem'],['Engines; reference thrust','3; 1 MN per engine','H','Virtual engine family'],['Steady throttle; specific impulse','0.3--1.1; 320 s','H','Not a certified performance map'],['Ignition delay; response; slew','0.5 s; 0.1 s; 1/s','H','Finite engine response'],['Reference area; drag coefficient','38.4845 m$^2$; 0.5','D/H','Base area; zero-lift closure'],['Unusable fraction; usable reserve','0.005 of initial load; 701.055 kg','H','Mass bookkeeping and nominal target'],['Pressure; force-budget limits','50 kPa; 4','H','Nominal safety screens'],['Deck half-width; edge margin','20 m; 2 m','H','Static two-dimensional deck'],['CG-to-foot-plane; foot half-span','32.5 m; 5 m','H','Assumed deployed geometry'],['TVC, inertia, aerodynamic moment, legs','Not established','U','Required for complete M1 safety']]
 notation=[[r'$h,\phi$','CG geometric height; Earth-centered position angle'],[r'$v_t,v_r,V$','Local tangential and radial velocities; speed'],[r'$m,m_d,m_{p,0},m_{\rm use}$','Total mass; dry mass; initial total propellant; usable mass'],[r'$T,T_i,D,q$','Net M0 thrust; engine thrust magnitudes; drag; dynamic pressure'],[r'$\beta,\theta,\delta$','Thrust direction; body direction; relative deflection'],[r'$\psi,\omega,I$','Inertial body angle; body angular rate; transverse inertia'],[r'$\chi,\theta_d$','Opposite-relative-velocity direction; body tilt relative to deck'],[r'$\ell,b,A_{\rm ref}$','CG-to-foot distance; foot half-span; aerodynamic reference area'],[r'$n_\Sigma,n_{\rm proper}$','Force-magnitude budget; net non-gravitational acceleration / $g_0$']]
 passive=list(csv.DictReader((ROOT/'results/data/passive_cases.csv').open(encoding='utf-8-sig')))
 ps=[[r['case'].replace('vacuum_130t','Vacuum').replace('air_130t_Cd0.5','Atmosphere, $C_D=0.5$').replace('air_130t_Cd1','Atmosphere, $C_D=1.0$'),f"{float(r['time_to_surface_s']):.1f}",f"{float(r['surface_arc_range_m'])/1000:.1f}",f"{float(r['surface_speed_m_s']):.0f}",f"{float(r['max_q_Pa'])/1000:.1f}"] for r in passive[:3]]
 comparisons=[]
 for i,x in enumerate(d['comparison']):comparisons.append([f"{x['ignition_command_s']:.0f}"+(' (selected)' if i==4 else ''),320 if i in [0,4] else 80,f"{x['initial_propellant_kg']/1000:.3f}",f"{x['consumed_kg']/1000:.3f}",'Pass'])
 phases=list(csv.DictReader((ROOT/'results/data/phase_states.csv').open()));phase_names=['Separation','Three-engine ignition command','Off command','Two-engine restart command','CG reference endpoint'];pr=[[name,f"{float(r['time_s']):.2f}",f"{float(r['height_m'])/1000:.3f}",f"{float(r['vt_m_s']):.2f}",f"{float(r['vr_m_s']):.2f}"] for name,r in zip(phase_names,phases)]
 results=[['Initial total propellant',f"{s['initial_propellant_kg']/1000:.2f} t",'Optimization objective, conditional'],['Consumed propellant',f"{s['consumed_kg']/1000:.2f} t",'To the CG reference event'],['Usable propellant remaining',f"{f['usable_kg']:.1f} kg",'Nominal target: 701.055 kg'],['Flight time',f"{s['actual_end_s']:.2f} s",'CG-height event'],['Nominal ship range',f"{f['range_m']/1000:.2f} km",'Selected once; surface arc'],['Reference radial velocity',f"{f['vr_m_s']:.4f} m/s",'Proxy interval: -2 to 0 m/s'],['Reference tangential velocity',r'$<10^{-4}$ m/s (magnitude)','CG proxy, not foot velocity'],['Peak dynamic pressure',f"{s['peaks']['q_Pa']/1000:.2f} kPa",'Nominal threshold: 50 kPa'],['Maximum force budget',f"{s['peaks']['n_sum']:.3f}",'Nominal threshold: 4'],['Reference vertical thrust / weight',f"{s['terminal_vertical_thrust_over_weight']:.4f}",'Not post-contact stability']]
 ck=[['160 to 320 intervals',f"{v['grid_fuel_relative_difference']*100:.6f}% initial propellant change",'Empirical grid convergence'],['Independent SI coordinates',r'$1.54\times10^{-7}$ m/s radial endpoint difference','Cartesian versus independently written polar equations'],['DOP853 versus RK45',r'$1.05\times10^{-5}$ m/s radial endpoint difference','Different integrator families'],['Maximum-step halving',r'$3.30\times10^{-7}$ m/s reference-speed difference','0.1 to 0.05 s in original replay'],['Mass balance',r'$7.57\times10^{-10}$ kg residual','Independent thrust/mass-flow integral'],['Engine response ODE',r'$1.12\times10^{-9}$ maximum actual-throttle difference','Effective commands independently integrated'],['Analytic and coordinate limits','Rocket equation; quadratic drag; vacuum invariants; 200 random states','All implemented checks passed'],['Optimizer reproduction','Same state/control arrays and key times','From the delivered 160-interval guess']]
 names={'Cd_minus10pct':r'$C_D$: -10%','Cd_plus10pct':r'$C_D$: +10%','Isp_minus1pct':r'$I_{sp}$: -1%','Isp_plus1pct':r'$I_{sp}$: +1%','rho_minus5pct':r'$\rho$: -5%','rho_plus5pct':r'$\rho$: +5%','initial_vt_minus1m_s':r'$v_{t,0}$: -1 m/s','initial_vt_plus1m_s':r'$v_{t,0}$: +1 m/s','initial_vr_minus1m_s':r'$v_{r,0}$: -1 m/s'}
 sr=[]
 for x in d['audit']['frozen_open_loop_sensitivity']:
  y=x['final'];event=x['event']
  if event=='REFERENCE_CONTACT':response=f"Reference contact: $v_r={y['vr_m_s']:.2f}$, $v_t={y['vt_m_s']:.2f}$ m/s"
  elif event=='USABLE_PROPELLANT_EXHAUSTED':response=f"Usable propellant exhausted at CG height {y['height_m']:.1f} m"
  else:response=f"No reference contact by planned end; CG height {y['height_m']:.1f} m"
  sr.append([names[x['name']],f"{x['peaks']['q_Pa']/1000:.2f}",response,'Fail'])
 safety=[['C01','Mass and flow','Nominal M0 pass','Nonnegative usable mass; thrust-flow accounting'],['C02','Data/model domain','Partial','Height-domain checks pass; real aero applicability unverified'],['C03','Engine and actuator limits','Partial','M0 engine response checked; torque/gimbal authority unknown'],['C04','Dynamic pressure','Nominal M0 pass','Peak 47.0 kPa; limit 50 kPa (H)'],['C05','Proper acceleration','Derived diagnostic pass','Implied by C06 under the same limit'],['C06','Force budget','Nominal M0 pass','Maximum 2.528; limit 4 (H)'],['C07','High-q inflow attitude','Unverified; conditional contradiction','At most 20-degree net deflection cannot retain original trajectory'],['C08','Late verticalization','Unverified; conditional contradiction','About 15.28-degree relative authority required near ground'],['C09','Near-vertical stopping screen','Not verified / limited domain','Not mechanically applicable to a strongly horizontal restart'],['C10','Foot / envelope first contact','Geometry defined; not verified','Actual pose, deployment, and protrusions missing'],['C11','Foot vertical speed','CG proxy only','Required contact-foot interval: -2 to 0 m/s (H)'],['C12','Foot horizontal speed','CG proxy only','Contact-foot magnitude at most 0.5 m/s (H)'],['C13a','Foot-center target error','Not verified','At most 5 m (H); nominal ship selection is insufficient'],['C13b','All-foot deck coverage','Not verified','Every foot inside 18 m half-span (H)'],['C14','Contact body tilt','Not verified','At most 2 degrees relative to deck (H)'],['C15','Contact body angular rate','Not verified','At most 0.5 degrees/s relative to deck (H)'],['C16','Usable reserve','Nominal M0 pass; not robust','711 kg versus 701 kg target (H)'],['C17','Structure and heating','Not verified','No certified stress, temperature, heat-load, or TPS limits'],['C18','Stable post-contact support','Not verified','At least 2 s; leg/friction/capacity inputs unknown']]
 blocks={'TEAM':team,'PARAMETERS':table(['Quantity','Reference value','Status','Basis'],parameters),'NOTATION':table(['Symbol','Meaning'],notation),'PASSIVE':table(['Dry-body diagnostic','Time (s)','Range (km)','Surface speed (m/s)','Peak q (kPa)'],ps),'COMPARISON':table(['Initial ignition (s)','Intervals / phase','Initial load (t)','Consumed (t)','M0 screens'],comparisons),'PHASES':table(['Event','Time (s)','CG height (km)',r'$v_t$ (m/s)',r'$v_r$ (m/s)'],pr),'RESULTS':table(['Quantity','Nominal result','Interpretation'],results),'CHECKS':table(['Check','Observed agreement','Scope'],ck),'SENSITIVITY':table(['Single perturbation','Peak q (kPa)','Outcome of fixed plan','Screen'],sr),'SAFETY':table(['ID','Criterion','Evidence status','Boundary / target'],safety)}
 text=(ROOT/'simulation/templates/paper_en.md').read_text()
 captions={'PARAMETERS':'Table 1. Reference parameters and evidence status.','NOTATION':'Table 2. Main notation.','PASSIVE':'Table 3. Passive diagnostics for a dry 130 t body.','COMPARISON':'Table 4. Accepted M0 schedule comparisons.','PHASES':'Table 5. Selected nominal event states.','RESULTS':'Table 6. Nominal M0 results and interpretation.','CHECKS':'Table 7. Numerical verification evidence.','SENSITIVITY':'Table 8. Deterministic perturbations of the fixed plan.','SAFETY':'Table 9. Safety criteria and current evidence boundaries.'}
 for k,val in blocks.items():text=text.replace('@@'+k+'@@',('**'+captions[k]+'**\n\n' if k in captions else '')+val)
 text=re.sub(r'\\rm\s+([A-Za-z]+)',lambda q:r'\mathrm{'+q.group(1)+'}',text)
 text=text.replace('The symbol on the left is the actual throttle $u$, not a velocity. ','')
 def link_url(q):
  u=q.group(0);tail=''
  while u and u[-1] in '.,;':tail=u[-1]+tail;u=u[:-1]
  return '<'+u+'>'+tail
 text=re.sub(r'https?://[^\s<>]+',link_url,text)
 assert '@@' not in text
 out=ROOT/'reports/UPC_2026_A_Paper_Draft02_EN.md';out.write_text(text)
 # Word reference style and anonymous per-page team header.
 ref=Document(io.BytesIO(subprocess.check_output(["pandoc","--print-default-data-file","reference.docx"])));sec=ref.sections[0];sec.page_height=Mm(297);sec.page_width=Mm(210);sec.top_margin=sec.bottom_margin=Inches(.8);sec.left_margin=sec.right_margin=Inches(.8)
 for name,size in [('Normal',11),('Body Text',11),('Title',18),('Heading 1',14),('Heading 2',12),('Caption',9)]:
  st=next(s for s in ref.styles if s.name==name);st.font.name='Times New Roman';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0);st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Serif CJK SC')
 ref.styles['Normal'].paragraph_format.space_after=Pt(5)
 p=sec.header.paragraphs[0];p.text=f'Team {team} | Problem A'
 for run in p.runs:run.font.size=Pt(9)
 p=sec.footer.paragraphs[0];p.text='';p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run('Page ');field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');p._p.append(field)
 ref.core_properties.author='';ref.core_properties.last_modified_by='';ref.save(ROOT/'simulation/reference.docx')
 header=ROOT/'simulation/header.tex';header.write_text(r'''\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{Team '''+team+r'''}
\fancyhead[R]{Problem A}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{15pt}
\setlength{\emergencystretch}{3em}
\usepackage{float}
\floatplacement{figure}{H}
''')
 docx=ROOT/'reports/UPC_2026_A_Paper_Draft02_EN.docx'
 subprocess.run(['pandoc',str(out),'-o',str(docx),'--reference-doc='+str(ROOT/'simulation/reference.docx'),'--lua-filter='+str(ROOT/'simulation/table_widths.lua')],cwd=ROOT/'reports',check=True)
 doc=Document(docx);doc.core_properties.author='';doc.core_properties.last_modified_by='';doc.core_properties.title='Conditional Propellant Estimate for Shipboard Booster Recovery — Draft 02';doc.core_properties.subject='English research draft; safety and AI disclosure remain incomplete'
 for p in doc.paragraphs[:5]:
  if p.text.startswith(('Team ','Problem ')):p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  if p.text.startswith('A Conditional Propellant'):p.style='Title';p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 widths=[[.26,.33,.09,.32],[.3,.7],[.34,.14,.17,.19,.16],[.25,.18,.21,.21,.15],[.38,.15,.17,.15,.15],[.31,.27,.42],[.24,.38,.38],[.20,.12,.56,.12],[.07,.21,.28,.44]]
 usable=doc.sections[0].page_width-doc.sections[0].left_margin-doc.sections[0].right_margin
 for ti,t in enumerate(doc.tables):
  t.style=next(s for s in doc.styles if s.style_id=='Table');t.autofit=False
  tblw=t._tbl.tblPr.find(qn('w:tblW'));tblw.set(qn('w:type'),'dxa');tblw.set(qn('w:w'),str(round(usable/635)))
  for j,ratio in enumerate(widths[ti]):
   t.columns[j].width=int(usable*ratio)
   for row in t.rows:row.cells[j].width=int(usable*ratio)
  if t.rows:
   trpr=t.rows[0]._tr.get_or_add_trPr()
   if trpr.find(qn('w:tblHeader')) is None:trpr.append(OxmlElement('w:tblHeader'))
  for row in t.rows:
   for cell in row.cells:
    for p in cell.paragraphs:
     for run in p.runs:run.font.size=Pt(9)
 for p in doc.paragraphs:
  if p.text.startswith('Table '):p.paragraph_format.keep_with_next=True
 doc.save(docx)
 tex=ROOT/'results/logs/paper.tex';subprocess.run(['pandoc',str(out),'-s','-o',str(tex),'--include-in-header='+str(header),'--lua-filter='+str(ROOT/'simulation/table_widths.lua'),'-V','mainfont=DejaVu Serif','-V','monofont=DejaVu Sans Mono','-V','fontsize=11pt','-V','papersize=a4','-V','geometry:margin=0.85in','-V','colorlinks=true','-V','urlcolor=blue'],cwd=ROOT/'reports',check=True)
 tex.write_text(tex.read_text().replace("写出最终论文初版",r"{\fontspec{Noto Serif CJK SC}写出最终论文初版}"))
 # Compile in reports so all manuscript-relative figure links resolve.
 for _ in range(2):
  cp=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error','-output-directory='+str(ROOT/'results/logs'),str(tex)],cwd=ROOT/'reports',capture_output=True,text=True)
  (ROOT/'results/logs/typesetting_stdout.log').write_text(cp.stdout+'\n'+cp.stderr)
  if cp.returncode:raise RuntimeError(cp.stdout[-5000:])
 shutil.copy(ROOT/'results/logs/paper.pdf',ROOT/'reports'/f'{team}_A_Draft02.pdf')
 print('English manuscript, Word and PDF built',flush=True)
 return text
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--team',default='TBA');build(p.parse_args().team)
