"""Record full-stage cross-solver attempts, including early termination.

An aborted transient is deliberately recorded as incomplete. Fuse interaction
is not portable and is represented by its embedded 1mOhm conducting resistor.
"""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
import numpy as np
from ms14_project import ROOT,SOURCE,DEST,PRECHARGE,unpack,parse,components,elements,clean,inspect
from verify_driver import NG,DATA,LOGS,ngspice_compat


def power_stage_source(root):
    """Extract the user's circuit, without analysis options or control commands."""
    models=elements(root,'CiModel')
    lines=['* Extracted Multisim power-stage diagnostic, ngspice only',
           '* F1 interaction replaced by embedded conducting resistance; fuse trip NOT simulated']
    for r in components(root):
        name=r['display_ref'];p=r['ports'];values=r['parameters']
        if p and all(node is None for node in p.values()):continue
        if any(node is None for node in p.values()):raise ValueError(f'Partly unconnected component: {name}')
        model=clean(models[r['model_id']].get('LocalName')) if r['model_id'] else ''
        if name[0] in 'RCL':line=f'{name} {p["1"]} {p["2"]} {values[1]}'
        elif name.startswith('V'):
            value='PULSE('+ ' '.join(values[j] for j in [1,3,5,7,9,11,13])+')' if name=='V3' else values[1]
            line=f'{name} {p["1"]} {p["2"]} {value}'
        elif name[0]=='Q':line='X'+name+' '+' '.join(p[n] for n in ['D','G','S'])+' '+model
        elif name=='U1':line='XU1 '+' '.join(p[n] for n in ['VCC','IN','^SD','COM','VB','HO','VS','LO'])+' '+model
        elif name=='F1':line=f'R_SIM_FUSE {p["1"]} {p["2"]} 1m'
        elif name=='D1':line='XD1 '+p['A']+' '+p['K']+' '+model
        elif name=='D_BOOT':line='D_BOOT '+p['A']+' '+p['K']+' '+model
        else:raise ValueError(name)
        lines.append(line)
    for e in models.values():lines.append(clean(e.find('.//CiaCString').get('String')))
    return ngspice_compat('\n'.join(lines)+'\n')


def run_case(case,path,method):
    root=parse(unpack(path.read_bytes())[0])
    stop=float(inspect(root)['transient_settings']['TSTOP'])
    # Known node IDs are checked against extracted connectivity by ms14_project.
    source=power_stage_source(root)+f'.options reltol=0.001 method={method}\n.tran 50n {stop} 0 50n\n'
    with tempfile.TemporaryDirectory(prefix='gbuck-full-check-') as td:
        work=Path(td);raw=work/'trace.txt';init=work/'init';init.mkdir()
        library=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(library/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        ctl=f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(1) v(13) v(4) v(11,15) v(15) v(14,15) v(9) v(17)\nquit\n.endc\n.end\n'
        net=work/'test.cir';net.write_text(source+ctl,encoding='ascii')
        p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],capture_output=True,text=True,env=dict(os.environ,SPICE_SCRIPTS=str(init)))
        log=p.stdout+p.stderr;(LOGS/f'{case}.log').write_text(log)
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,9))
    failed=any(w in log.lower() for w in ['aborted','error:','timestep too small'])
    end=float(a[-1,0]) if len(a) else None
    complete=bool(p.returncode==0 and len(a)>1000 and end>=stop*.999 and not failed)
    failure_lines=[s for s in log.splitlines() if any(w in s.lower() for w in ['timestep too small','trouble with node','aborted','error:'])]
    result={'case':case,'solver':'ngspice 44.2 / ngbehavior=psa','native_multisim_execution_verified':False,
            'project_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'solver_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'method':method,'requested_end_time_s':stop,'end_time_s':end,'data_rows':len(a),
            'full_transient_completed':complete,'failure_messages':failure_lines,'fuse_trip_simulation':False}
    if len(a):
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//2500)),len(a)-1])
        np.savetxt(DATA/f'{case}_partial_sampled.csv',a[take],delimiter=',',header='time_s,PWM_V,GL_V,VOUT_V,VGS_H_V,SW_V,VBOOT_V,VCC_V,SD_V',comments='')
        before=a[a[:,0]<.0019]
        result['pre_pwm_GL_range_V']=[float(before[:,2].min()),float(before[:,2].max())]
        result['pre_pwm_VOUT_range_V']=[float(before[:,3].min()),float(before[:,3].max())]
    (DATA/f'{case}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result


def main():
    DATA.mkdir(exist_ok=True,parents=True);LOGS.mkdir(exist_ok=True,parents=True)
    rows=[run_case('original_power_stage',SOURCE,'trap'),run_case('corrected_power_stage',DEST,'gear'),
          run_case('corrected_pre_pwm_check',PRECHARGE,'gear')]
    assert rows[-1]['full_transient_completed'] and rows[-1]['pre_pwm_GL_range_V'][0]>10
    (DATA/'power_stage_attempts.json').write_text(json.dumps({'scope':'cross-solver diagnostic only','results':rows},indent=2)+'\n')


if __name__=='__main__':main()
