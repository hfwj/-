"""U3 reanalysis, measured-boundary replay and explicitly synthetic breakpoint test.

Do not label the controlled stimulus as native data or the local-time failure
as a reproduction of the native absolute stop time. Vendor models are temporary.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
import numpy as np
from build_diagnostics import PROJECT, ROOT, unpack, parse, components, elements, clean
from replay_q2 import NG, read_raw
from bias_smoothing import patch_bias


def main(cache):
    a=np.load(cache);t=a['time'];cap=a['V(v_cap)'];vout=a['V(vout)'];vs=a['V(vdda)'];cm=(cap+vout)/2
    source=PROJECT/'downloads/GBUCK_STEP02_5R_ABSTOL100nA_30ms_8CH_DIAG.ms14'
    root=parse(unpack(source.read_bytes())[0]);by={p['display_ref']:p for p in components(root)}
    item=elements(root,'CiModel')[by['U3']['model_id']];original=clean(item.find('.//CiaCString').get('String'))
    name=clean(item.get('LocalName'));modified=patch_bias(original,part='INA181')
    assert by['RS_OUT']['parameters'][1]=='0.05' and by['RL']['parameters'][1]=='5'
    # Static finite-input boundary: IN+ stiff, IN- loaded by 5ohm ||2.2k,
    # IIB linear 450k branch plus original 0/60uA step and 1G input leak.
    rs=.05;gload=1/5+1/2200;req=450000.;gn=float(vs[-1])/2
    den=1/rs+gload+1e-9+.5/req
    def negative_pin(vc,state):return (vc*(1/rs-.5/req)+gn*(1/req+1e-9)-state*60e-6)/den
    oldcap=float(cap[-1]);v0=negative_pin(oldcap,0);v1=negative_pin(oldcap,1)
    gain=.5*(1+(1/rs-.5/req)/den)
    center=oldcap-(((oldcap+v0)/2+(oldcap+v1)/2)/2-5)/gain
    c0=(center+negative_pin(center,0))/2;c1=(center+negative_pin(center,1))/2
    assert c0>5>c1
    mask=t>=.0247;tt=t[mask]-t[mask][0]
    cases=[('measured_clamped_original_10nA','measured',True,False,'1e-8'),
        ('measured_finite_original_10nA','measured',False,False,'1e-8'),
        ('measured_finite_original_100nA','measured',False,False,'1e-7'),
        ('measured_finite_smooth_10nA','measured',False,True,'1e-8'),
        ('controlled_original_10nA','controlled',False,False,'1e-8'),
        ('controlled_original_100nA','controlled',False,False,'1e-7'),
        ('controlled_smooth_10nA','controlled',False,True,'1e-8'),
        ('ordered_start_original','ordered',False,False,'1e-8'),
        ('ordered_start_smooth','ordered',False,True,'1e-8')]
    records=[]
    for case,kind,clamp,smooth,abstol in cases:
        model=modified if smooth else original
        logpath=ROOT/'results/logs'/('2026-10-26_u3_'+case+'.log')
        with tempfile.TemporaryDirectory(prefix='u3-breakpoint-') as folder:
            work=Path(folder);(work/'model.lib').write_text(model);lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
            (work/'spinit').write_text(''.join(f'codemodel {lib/n}\n' for n in
                ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm']))
            lines=['* U3 reduced boundary or controlled stimulus; not whole Buck','.include model.lib']
            if kind=='ordered':
                duration=100e-6
                lines += ['VSUP vs 0 PWL(0 0 1u 0 11u 3.3 100u 3.3)',
                    'VCM vout 0 PWL(0 0 15u 0 25u 10 100u 10)',
                    'VDIFF cap vout PWL(0 0 35u 0 35.01u .025 100u .025)','R_TEST out 0 100k']
            else:
                if kind=='measured':
                    duration=float(tt[-1]);tx=tt;cy=cap[mask];vy=vs[mask]
                else:
                    duration=50e-6;tx=np.array([0.,10e-6,10.05e-6,50e-6])
                    cy=np.array([center+20e-6,center+20e-6,center,center]);vy=np.full(4,vs[-1])
                sources=[('VCAP','cap',cy),('VSUP','vs',vy)]
                if clamp:sources.append(('VOUT','vout',vout[mask]))
                for vn,node,y in sources:
                    lines += [f'{vn} {node} 0 PWL(']+[f'+ {x:.17e} {v:.17e}' for x,v in zip(tx,y)]+['+ )']
                lines += ['RS_OUT cap vout .05','RLOAD vout 0 5','RBL vout 0 2200']
            lines += [f'XU3 out 0 cap vout 0 vs {name}',
                f'.options reltol=.001 abstol={abstol} vntol=1e-4 chgtol=1e-13 itl4=300 rshunt=1e12 method=trap',
                '.save v(cap) v(vout) v(out) v(vs) v(xu3.x_ti.vicm) v(xu3.x_ti.inp_psrr_out)',
                f'.tran 50n {duration:.17e} 0 50n','.end']
            net='\n'.join(lines)+'\n';(work/'test.cir').write_text(net)
            with logpath.open('w') as log:
                try:
                    code=subprocess.run([str(NG),'-D','ngbehavior=psa','-b','-r','out.raw','test.cir'],cwd=work,
                        env=dict(os.environ,SPICE_SCRIPTS=str(work)),stdout=log,stderr=subprocess.STDOUT,timeout=35).returncode
                except subprocess.TimeoutExpired:
                    code=None;log.write('\nERROR: wall-time limit, not a demonstrated convergence failure\n')
            data,names=read_raw(work/'out.raw') if (work/'out.raw').exists() else (np.empty((0,1)),[])
        errors=[l for l in logpath.read_text().splitlines() if any(w in l.lower() for w in ['error:','too small','aborted'])]
        completed=bool(code==0 and len(data) and not errors and np.isfinite(data).all() and data[-1,0]>=duration*(1-1e-12))
        result={'case':case,'stimulus_kind':kind,'synthetic_stimulus':kind!='measured','abstol_A':abstol,
            'bias_smoothed':smooth,'returncode':code,'completed':completed,'rows':len(data),
            'requested_s':duration,'actual_end_s':float(data[-1,0]) if len(data) else None,
            'errors':errors,'model_sha256':hashlib.sha256(model.encode()).hexdigest(),
            'temporary_netlist_sha256':hashlib.sha256(net.encode()).hexdigest(),
            'last_values':dict(zip(names,data[-1].tolist())) if len(data) else None}
        records.append(result);print(json.dumps(result),flush=True)
    assert all(c['completed'] for c in records[:4])
    assert not records[4]['completed'] and not records[5]['completed']
    assert all(any('inp_psrr_out' in e for e in records[i]['errors']) for i in [4,5])
    assert records[6]['completed'] and records[7]['completed'] and records[8]['completed']
    original_gain=records[7]['last_values']['v(out)'];smooth_gain=records[8]['last_values']['v(out)']
    assert .49<original_gain<.51 and abs(original_gain-smooth_gain)<1e-4
    summary={'date':'2026-10-26','native_data_source':'previous 24.9514ms GRA, not a new 20.1209ms waveform',
        'native_GRA_sha256':'0fe32054e971ead3daf71927c97674adc35a5e8321cdf009b1e702398e6fe980',
        'old_native_end_s':float(t[-1]),'old_native_U3_common_mode_V':float(cm[-1]),
        'old_native_U3_common_mode_minus_5V_V':float(cm[-1]-5),
        'reconstructed_from_VOUT_and_RS_OUT_current_max_difference_V':float(np.max(np.abs(
            (vout+.025*a['I(RS_OUT)'])-cm))),
        'controlled_cap_midpoint_V':center,'original_threshold_low_state_common_mode_V':c0,
        'original_threshold_high_state_common_mode_V':c1,
        'old_last_cap_to_controlled_midpoint_shift_V':center-oldcap,
        'derivation':'Simplified DC boundary, stiff IN+, 50mOhm RS_OUT and 5ohm||2.2k load. Original bias states imply opposite signs around 5V at the chosen midpoint, hence no self-consistent static state in that idealized discontinuous model.',
        'controlled_stimulus_is_not_measured_or_extrapolated_native_trace':True,
        'same_U3_node_failure_class_reproduced_in_controlled_fixture':True,
        'native_absolute_failure_time_reproduced':False,'native_30ms_completed':False,
        'cases':records,'limitations':'Different solver, ideal recorded V_CAP/VDDA boundaries or synthetic hold, DC-initialized hidden states. Measured window terminates at the threshold and all four variants complete; only the separately labelled controlled sweep enters and holds the inconsistent interval. No full Buck or hardware validation.'}
    (ROOT/'results/data/2026-10-26_u3_breakpoint_reanalysis.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cache',type=Path);args=p.parse_args();main(args.cache)
