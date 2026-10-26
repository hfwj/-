"""Reproduce the 2026-10-26 Q2 boundary/driver/coupled comparisons.

Vendor definitions/netlists exist only in temporary directories. All fixture
outputs are simulations, not native Multisim data or measured hardware.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from build_diagnostics import PROJECT, ROOT, unpack, parse, components, elements, clean
from replay_q2 import NG, read_raw
from verify_driver import ngspice_compat

PINS=[('orig_50n_rel001',50e-9,'.001',None),('orig_5n_rel001',5e-9,'.001',None),
    ('orig_50n_rel0001',50e-9,'.0001',None),('orig_5n_rel0001',5e-9,'.0001',None),
    ('RL2_5n_rel001',5e-9,'.001','RL'),('RCAP2_5n_rel001',5e-9,'.001','RCAP')]
DRIVER=[('driver_original_50n',50e-9,'.001',None,'trap','1e-8'),
    ('driver_original_5n',5e-9,'.001',None,'trap','1e-8'),
    ('driver_original_rel0001',50e-9,'.0001',None,'trap','1e-8'),
    ('driver_RL2',50e-9,'.001','RL','trap','1e-8'),
    ('driver_RCAP2',50e-9,'.001','RCAP','trap','1e-8'),
    ('driver_gear_001',50e-9,'.001',None,'gear','1e-8'),
    ('driver_gear_0001',50e-9,'.0001',None,'gear','1e-8'),
    ('driver_abs1e7_rel0001',50e-9,'.0001',None,'trap','1e-7'),
    ('driver_abs1e7_rel001',50e-9,'.001',None,'trap','1e-7')]
FULL=[('trap_001','trap','.001','1e-8'),('gear_001','gear','.001','1e-8'),
    ('trap_0001','trap','.0001','1e-8'),('trap_abs1e7','trap','.001','1e-7')]


def main(args):
    z=np.load(args.cache);mask=z['time']>=.0247;absolute=z['time'][mask];tt=absolute-absolute[0]
    source=PROJECT/'downloads/GBUCK_STEP02_5R_IIB_SMOOTH01mV_100ms_DIAG.ms14'
    root=parse(unpack(source.read_bytes())[0]);by={p['display_ref']:p for p in components(root)}
    models=elements(root,'CiModel')
    model=lambda ref:clean(models[by[ref]['model_id']].find('.//CiaCString').get('String'))
    mos,driver=model('Q2'),model('U1')
    mn=clean(models[by['Q2']['model_id']].get('LocalName'))
    dn=clean(models[by['U1']['model_id']].get('LocalName')).replace('/','_')
    if args.suite=='coupled':
        sys.path.insert(0,str(ROOT.parent/'step02-u3-feedback-fix'))
        from verify_step02 import extract
        full=extract(source,.03,50e-9)
        full=full.replace('.options reltol=.003','.options reltol=.001').replace('itl4=100','itl4=300')
        old='.save v(VOUT) v(VDDA) v(IOUT_RAW) v(IL_BI) i(L1) v(xctrl.ilraw) v(V_CAP) v(6) v(7)'
        assert old in full
        full=full.replace(old,'.save v(VOUT) v(VDDA) v(IOUT_RAW) i(L1) v(V_CAP)')
    cases={'pins':PINS,'driver':DRIVER,'coupled':FULL}[args.suite]
    if args.case:cases=[c for c in cases if c[0] in args.case]
    assert cases

    def run(case):
        start=time.monotonic();key=case[0];change=None
        if args.suite=='coupled':key,method,rel,abstol=case;step=50e-9
        else:
            key,step,rel,change=case[:4]
            method,abstol=('trap','1e-8') if args.suite=='pins' else case[4:]
        src=mos
        if change:
            src,count=re.subn(r'(?m)^('+change+r'\s+\d+ \d+ )1\s*$',lambda m:m[1]+'2',src)
            assert count==1
        logpath=ROOT/'results/logs'/('2026-10-26_replay_'+key+'.log')
        with tempfile.TemporaryDirectory(prefix='q2-20261026-') as folder:
            work=Path(folder);lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
            (work/'spinit').write_text(''.join(f'codemodel {lib/n}\n' for n in
                ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm']))
            if args.suite=='coupled':
                net=full.replace('method=trap','method='+method).replace('reltol=.001','reltol='+rel).replace('abstol=1e-8','abstol='+abstol)
                duration=.03
            else:
                (work/'models.lib').write_text(src+('\n'+ngspice_compat(driver) if args.suite=='driver' else ''))
                lines=['* Reduced Q2 diagnostic, not native or hardware validation','.include models.lib']
                sources=([('VD','d','V(sw)'),('VG','g','V(g_l)')] if args.suite=='pins' else
                    [('VSW','sw','V(sw)'),('VIN','inp','V(16)'),('VEN','en','V(17)')])
                for vn,node,ch in sources:
                    lines += [f'{vn} {node} 0 PWL(']+[f'+ {a:.17e} {b:.17e}' for a,b in zip(tt,z[ch][mask])]+['+ )']
                if args.suite=='pins':
                    lines += [f'XQ2 d g 0 {mn}',
                        '.save v(d) v(g) v(xq2.7) v(xq2.9) i(VD) i(VG) i(v.xq2.vfi1) i(v.xq2.vfi2) @m.xq2.m1[id]']
                else:
                    lines += ['VCC vcc 0 12','VBOOT vb sw 11.5',f'XU1 vcc inp en 0 vb ho sw lo {dn}',
                        'RHO ho sw 100k','RG_L lo g 10','R_GSL g 0 10k',f'XQ2 sw g 0 {mn}',
                        '.save v(g) v(lo) v(sw) i(VSW) @m.xq2.m1[id]']
                lines += [f'.options reltol={rel} abstol={abstol} vntol=1e-4 chgtol=1e-13 itl4=300 rshunt=1e12 method={method}',
                    f'.tran {step:.17e} {tt[-1]:.17e} 0 {step:.17e}','.end']
                net='\n'.join(lines)+'\n';duration=float(tt[-1])
            (work/'test.cir').write_text(net)
            with logpath.open('w') as log:
                try:
                    code=subprocess.run([str(NG),'-D','ngbehavior=psa','-b','-r','out.raw','test.cir'],
                        cwd=work,env=dict(os.environ,SPICE_SCRIPTS=str(work)),stdout=log,stderr=subprocess.STDOUT,timeout=50).returncode
                except subprocess.TimeoutExpired:
                    code=None;log.write('\nERROR: wall-time limit, not a demonstrated convergence failure\n')
            data,names=read_raw(work/'out.raw') if (work/'out.raw').exists() else (np.empty((0,1)),[])
        errors=[l for l in logpath.read_text().splitlines() if any(w in l.lower() for w in ['error:','too small','aborted'])]
        r={'case':key,'suite':args.suite,'method':method,'reltol':rel,'abstol_A':abstol,'maxstep_s':step,
            'returncode':code,'rows':len(data),'actual_end_s':float(data[-1,0]) if len(data) else None,
            'requested_duration_s':duration,'completed':bool(code==0 and len(data) and not errors and np.isfinite(data).all() and data[-1,0]>=duration*(1-1e-12)),
            'errors':errors,'elapsed_s':time.monotonic()-start,'Q2_model_sha256':hashlib.sha256(src.encode()).hexdigest(),
            'fixture_model_change':change,'temporary_netlist_sha256':hashlib.sha256(net.encode()).hexdigest(),
            'native_Multisim_run':False,'hardware_measurement':False}
        if len(data):r['last_values']=dict(zip(names,data[-1].tolist()))
        print(json.dumps(r),flush=True);return r

    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,cases))
    out={'date':'2026-10-26','suite':args.suite,'source_project_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'native_window_start_s':float(absolute[0]),'boundary_points':len(tt),'cases':results,
        'limitations':'Different engine and DC-initialized hidden state. Pin fixture clamps drain/gate; driver fixture uses actual low gate path but imposed SW and ideal 11.5V bootstrap, unloaded HO. Coupled export replaces F1 thermal model with 1mOhm and has initialization/compatibility differences. No fixture result establishes native 100ms success.'}
    target=ROOT/'results/data'/('2026-10-26_replay_'+args.suite+('_selected' if args.case else '')+'.json')
    target.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cache',type=Path)
    p.add_argument('--suite',choices=['pins','driver','coupled'],required=True)
    p.add_argument('--case',action='append');main(p.parse_args())
