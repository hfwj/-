"""Fixed-control sensitivity, run in clean processes; restore nominal config."""
from pathlib import Path
import json,subprocess,sys,copy
ROOT=Path(__file__).resolve().parents[1];SIM=ROOT/'simulation';path=SIM/'config.json'
original=path.read_text();config=json.loads(original);selected=json.loads((ROOT/'results/data/selected.json').read_text())
child="""import json,numpy as np
from model import run,ROOT
s=json.loads((ROOT/'results/data/selected.json').read_text());r=run(s['load_t'],s['parameters'],dt=.005);print(json.dumps(r))
"""
cases=[('Cd -10%',{'CD_Y':[v*.9 for v in config['CD_Y']]}),('Cd +10%',{'CD_Y':[v*1.1 for v in config['CD_Y']]}),('Wind x1.25',{'WIND_U':[v*1.25 for v in config['WIND_U']]}),('Isp -2%',{'ISP':config['ISP']*.98}),('Ignition delay 0.7 s',{'IGN_DELAY':.7}),('Upper scale 5 km',{'HIGH_H':5000.}),('Upper scale 10 km',{'HIGH_H':10000.})]
rows=[]
try:
 for label,change in cases:
  c=copy.deepcopy(config);c.update(change);path.write_text(json.dumps(c,indent=2))
  done=subprocess.run([sys.executable,'-c',child],cwd=SIM,text=True,capture_output=True,check=True)
  r=json.loads(done.stdout);r['case']=label;r['range_shift_m']=r['range_m']-selected['range_m'];r['config_changes']=change;rows.append(r)
  print(label,r['pass'],round(r['used_kg'],1),round(r['qmax_pa'],1),round(r['vz_mps'],3),round(r['range_shift_m'],2),flush=True)
 # Independent physical identities on a vacuum central-gravity coast.
 c=copy.deepcopy(config);c['CD_Y']=[0.]*12;c['WIND_U']=[0.]*8;path.write_text(json.dumps(c,indent=2))
 vacuum="""import json,numpy as np
from model import run,CONFIG
r,h=run(130,[-1e6,900,1.2,1.5],.02,history=True)
radius=CONFIG['RE']+h[:,2];energy=.5*(h[:,3]**2+h[:,4]**2)-CONFIG['MU']/radius;angular=radius*h[:,3]
print(json.dumps({'energy_relative_drift':float(np.max(abs(energy-energy[0]))/abs(energy[0])),'angular_momentum_relative_drift':float(np.max(abs(angular-angular[0]))/abs(angular[0])),'constant_mass_error_kg':float(np.max(abs(h[:,5]-260000.))),'contact_event':r['contact_event']}))
"""
 done=subprocess.run([sys.executable,'-c',vacuum],cwd=SIM,text=True,capture_output=True,check=True)
 check=json.loads(done.stdout);assert check['energy_relative_drift']<1e-9;assert check['angular_momentum_relative_drift']<1e-9;assert check['constant_mass_error_kg']<1e-8
 (ROOT/'results/data/vacuum_checks.json').write_text(json.dumps(check,indent=2));print('Vacuum invariants',check,flush=True)
finally:path.write_text(original)
(ROOT/'results/data/sensitivity.json').write_text(json.dumps(rows,indent=2))
# Rebuild nominal library after restoring the exact config file.
subprocess.run([sys.executable,'-c','import model'],cwd=SIM,check=True)
