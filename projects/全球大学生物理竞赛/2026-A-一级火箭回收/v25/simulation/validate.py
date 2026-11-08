"""Validate the executed records and the compiled manuscript."""
from pathlib import Path
import json,re,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'results/data'
read=lambda n:json.loads((D/n).read_text())
c=json.loads((ROOT/'simulation/config.json').read_text());r=read('selected.json');conv=read('convergence.json')
assert len(c['CD_M'])==len(c['CD_Y'])==12 and c['HIGH_H']==7000.
assert [x['dt'] for x in conv]==[.02,.01,.005]
assert all(x['parameters']==r['parameters'] and x['load_t']==r['load_t'] for x in conv)
for row in conv:
    independently_passed=(row['contact_event']==1 and row['exhaust_s']<0
        and -c['VZ_LIMIT']<=row['vz_mps']<=0 and abs(row['vx_mps'])<=c['VX_LIMIT']
        and row['tilt_deg']<=c['TILT_LIMIT_DEG'] and row['qmax_pa']<=c['Q_LIMIT']
        and row['nmax']<=c['N_LIMIT'] and row['residual_kg']>=c['RESERVE'])
    assert independently_passed and row['pass']==1
assert abs(r['entry_kg']+r['landing_kg']-r['used_kg'])<1e-7
assert abs(r['used_kg']+r['residual_kg']-1000*r['load_t'])<1e-7
checks=read('verification.json');assert abs(checks['independent_smooth_interval_massflow_error_kg'])<.1
aux=(ROOT/'reports/latex/build/main.aux').read_text()
assert re.search(r'\\newlabel\{eq:dragtrigger\}\{\{8\}',aux)
assert re.search(r'\\newlabel\{eq:objective\}\{\{11\}',aux)
log=(ROOT/'reports/latex/build/main.log').read_text(errors='replace')
assert not any(x in log for x in ['Overfull \\hbox','Missing character','There were undefined references'])
import fitz
pdf=fitz.open(ROOT/'reports/latex/build/main.pdf');texts=[p.get_text() for p in pdf]
assert all('Team 856' in t for t in texts)
starts=[i+1 for i,t in enumerate(texts) if 'Listing A.' in t]
assert len(starts)==5 and starts==list(range(starts[0],starts[0]+5)) and starts[-1]==len(pdf)
assert all(x not in '\n'.join(texts) for x in ['51--121','70--121','106.6 t','110--112 t'])
report=dict(pages=len(pdf),team=856,code_pages=starts,drag_trigger_equation=8,dimensionless_objective_equation=11,
 twelve_drag_anchors=True,upper_scale_height_m=c['HIGH_H'],three_fixed_control_steps=True,
 all_three_nominal_screens_pass=True,physical_calibration_claimed=False,old_manuscript_results_used=False,
 independent_massflow_check_kg=checks['independent_smooth_interval_massflow_error_kg'],latex_issues=[])
(D/'release_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
