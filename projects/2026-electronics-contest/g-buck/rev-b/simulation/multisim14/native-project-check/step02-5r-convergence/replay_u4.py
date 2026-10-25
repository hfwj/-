"""Imposed-boundary and finite-input-impedance U4 diagnostic comparisons.

The finite fixture drives actual IL into original 25mOhm RS_L and clamps
V_CAP/VDDA. It retains input bias feedback through RS_L but omits the whole
Buck and its prior hidden states. Vendor text/netlists are temporary only.
"""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np
from build_diagnostics import PROJECT, ROOT, unpack, parse, components, elements, clean
from replay_q2 import NG, read_raw
from bias_smoothing import patch_bias


def main(cache):
    a=np.load(cache);mask=a['time']>=.0161
    absolute=a['time'][mask];origin=float(absolute[0]);tt=absolute-origin
    assert np.all(np.diff(tt)>0)
    source=PROJECT/'downloads/GBUCK_STEP02_5R_REL001_U4_TRACE_25ms.ms14'
    root=parse(unpack(source.read_bytes())[0]);by={p['display_ref']:p for p in components(root)}
    item=elements(root,'CiModel')[by['U4']['model_id']]
    model=clean(item.find('.//CiaCString').get('String'));name=clean(item.get('LocalName'))
    assert by['RS_L']['parameters'][1]=='0.025'
    results=[]
    for fixture in ['voltage_clamped','current_into_RS_L']:
        for key,width in [('original',None),('smooth_1mV','0.001'),('smooth_01mV','0.0001')]:
            case=fixture+'_'+key;start=time.monotonic();src=model if width is None else patch_bias(model,width)
            logpath=ROOT/'results/logs'/('u4_replay_'+case+'.log')
            with tempfile.TemporaryDirectory(prefix='u4-bias-boundary-') as folder:
                work=Path(folder);(work/'model.lib').write_text(src)
                library=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
                (work/'spinit').write_text(''.join('codemodel '+str(library/n)+'\n' for n in
                    ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm']))
                lines=['* U4 boundary diagnostic, not a full Buck or native Multisim run','.include model.lib']
                first=('VINP','inp','V(l_raw)') if fixture=='voltage_clamped' else ('I_L','inp','I(L1)')
                for vname,node,channel in [first,('VINM','inm','V(v_cap)'),('VSUP','vs','V(vdda)')]:
                    terminals=f'0 {node}' if vname=='I_L' else f'{node} 0'
                    lines += [f'{vname} {terminals} PWL(']+[
                        f'+ {x:.17e} {y:.17e}' for x,y in zip(tt,a[channel][mask])]+['+ )']
                if fixture=='current_into_RS_L':lines.append('RS_L inp inm 0.025')
                lines += [f'XU4 inm 0 0 nc out vs vs inp {name}',
                    '.options reltol=.001 abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=300 rshunt=1e12 method=trap',
                    '.save v(inp) v(inm) v(vs) v(out) i(VINM) v(xu4.x_ti.n504417) v(xu4.x_ti.vicm)',
                    f'.tran 50n {tt[-1]:.17e} 0 50n','.end']
                net='\n'.join(lines)+'\n';(work/'test.cir').write_text(net)
                with logpath.open('w') as log:
                    try:
                        code=subprocess.run([str(NG),'-D','ngbehavior=psa','-b','-r','out.raw','test.cir'],
                            cwd=work,env=dict(os.environ,SPICE_SCRIPTS=str(work)),
                            stdout=log,stderr=subprocess.STDOUT,timeout=40).returncode
                    except subprocess.TimeoutExpired:
                        code=None;log.write('\nERROR: wall-time limit, not a demonstrated convergence failure\n')
                values,names=read_raw(work/'out.raw') if (work/'out.raw').exists() else (np.empty((0,1)),[])
            errors=[l for l in logpath.read_text().splitlines() if any(w in l.lower() for w in ['error:','too small','aborted'])]
            complete=bool(code==0 and not errors and len(values) and np.isfinite(values).all() and values[-1,0]>=tt[-1]*(1-1e-12))
            result={'case':case,'width_V':None if width is None else float(width),
                'returncode':code,'completed':complete,'rows':len(values),'elapsed_s':time.monotonic()-start,
                'requested_duration_s':float(tt[-1]),'actual_end_s':float(values[-1,0]) if len(values) else None,
                'errors':errors,'model_sha256':hashlib.sha256(src.encode()).hexdigest(),
                'temporary_netlist_sha256':hashlib.sha256(net.encode()).hexdigest()}
            if len(values):
                result['last_values']=dict(zip(names,values[-1].tolist()))
                if fixture=='current_into_RS_L' and width=='0.0001' and complete:
                    pick=values[:,0]>=tt[-1]-30e-6
                    np.savetxt(ROOT/'results/data/u4_smooth_01mV_fixture_last30us.csv',values[pick],delimiter=',',
                        header=','.join(names),comments='',fmt='%.17e')
            results.append(result);print(json.dumps(result),flush=True)
    assert all(r['completed'] for r in results[:3])
    assert not results[3]['completed'] and any('n1sgn' in e for e in results[3]['errors'])
    assert results[4]['completed'] and results[5]['completed']
    summary={'date':'2026-10-25','source_project_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'native_window_start_s':origin,'boundary_points':len(tt),'duration_s':float(tt[-1]),
        'maxstep_s':5e-8,'cases':results,'native_Multisim_performed':False,'full_Buck_performed':False,
        'limitations':'Different engine, DC-initialized internal state; voltage clamp removes input bias feedback, finite fixture restores only RS_L input impedance. V_CAP and VDDA are ideal recorded boundaries. Failure mechanism is localized, but native failure time/branch and whole-circuit success are not exactly reproduced.'}
    (ROOT/'results/data/u4_replay_summary.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('cache',type=Path);args=parser.parse_args();main(args.cache)
