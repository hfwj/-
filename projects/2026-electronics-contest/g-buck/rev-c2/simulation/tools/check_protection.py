"""Test the actual embedded protection subcircuit and VIN RC in isolated ngspice benches.

These are imposed waveforms, not Buck load-step reproduction or STM32 tests.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
NG=Path(os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice'))
DATA=ROOT/'results/data/protection';LOGS=ROOT/'results/logs/protection'
NETS=ROOT/'simulation/benches'


def run(name,src,vectors,stop=.08):
    out=DATA/(name+'.txt');net=NETS/(name+'.cir')
    net.write_text('* Rev C.2 isolated timing/RC reference; no whole-converter validation\n'+src+
        f'\n.options method=gear reltol=1e-5 abstol=1e-10\n.tran 2u {stop} 0 2u uic\n.control\nset wr_singlescale\nrun\nwrdata {out} '+vectors+'\nquit\n.endc\n.end\n')
    p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],capture_output=True,text=True,timeout=45)
    log=p.stdout+p.stderr;(LOGS/(name+'.log')).write_text(log)
    assert p.returncode==0 and out.exists(),(name,log[-2500:])
    assert not any(s in log.lower() for s in ('timestep too small','simulation(s) aborted','error:')),(name,log[-1500:])
    a=np.loadtxt(out);assert a[-1,0]>=stop*.999,(name,a[-1,0])
    np.savetxt(DATA/(name+'.csv'),a[::max(1,len(a)//2000)],delimiter=',',header='time_s,'+vectors.replace(' ',','),comments='')
    out.unlink();return a


def main():
    for p in (DATA,LOGS,NETS):p.mkdir(exist_ok=True,parents=True)
    # Read the actual library from the delivered .ms14, not a separate ideal implementation.
    sys.path.insert(0,str(ROOT.parent/'rev-b/simulation/multisim14/native-project-check'))
    from ms14_project import unpack,parse,clean
    ms=ROOT/'downloads/GBUCK_REVC2_FULL_25V_5R_100ms.ms14'
    root=parse(unpack(ms.read_bytes())[0])
    import re
    definitions=[clean(e.get('String','')) for e in root.iter('CiaCString') if '.SUBCKT REVC2_PROTECT ' in e.get('String','')]
    assert len(definitions)==1
    lib=re.search(r'(?ms)^\.SUBCKT REVC2_PROTECT .*?^\.ENDS REVC2_PROTECT',definitions[0]).group()+'\n'
    expected=(ROOT/'simulation/multisim14/models/REVC2_PROTECT.lib').read_text()
    assert lib.strip()==expected[expected.index('.SUBCKT REVC2_PROTECT '):].strip()
    baseline={'oc':'3.3','vo':'5','target':'10','ready':'3.3','fault':'3.3','arm':'0'}
    cases=[
      ('brief_OC_pulses_4p4ms_3p08ms',{'oc':'PWL(0 3.3 10m 3.3 10.001m 0 14.4m 0 14.401m 3.3 30m 3.3 30.001m 0 33.08m 0 33.081m 3.3)'},False),
      ('oc_sustained',{'oc':'PWL(0 3.3 10m 3.3 10.001m 0)'},True),
      ('imposed_0p1V_OC_healthy',{'vo':'PWL(0 5 10m 5 10.001m 0.1)'},True),
      ('imposed_0p01V_OC_healthy',{'vo':'PWL(0 5 10m 5 10.001m 0.01)'},True),
      ('startup_low_voltage_masked',{'vo':'PWL(0 0 40m 0 40.001m 5)','ready':'PWL(0 0 50m 0 50.001m 3.3)'},False),
      ('low_target_voltage_exempt',{'vo':'0.1','target':'0.2'},False),
      ('fault_release_requires_ARM',{'vo':'PWL(0 5 10m 5 10.001m 0.1 40m 0.1 40.001m 5)'},True),
      ('manual_ARM_after_release',{'vo':'PWL(0 5 10m 5 10.001m 0.1 40m 0.1 40.001m 5)',
                                   'arm':'PWL(0 0 50m 0 50.001m 3.3 51m 3.3 51.001m 0)'},True),
      ('hardware_fault_1ms_latches',{'fault':'PWL(0 3.3 10m 3.3 10.001m 0 11m 0 11.001m 3.3)'},True),
    ]
    result=[]
    for name,changes,trip in cases:
        sig={**baseline,**changes}
        src='\n'.join('V_'+k+' '+k+' 0 '+v for k,v in sig.items())+'\nX_PROTECT oc vo target ready fault arm en 0 REVC2_PROTECT\n'+lib
        a=run(name,src,'v(en) v(oc) v(vo) v(x_protect.toc) v(x_protect.tsc)')
        fallen=a[(a[:,0]>.002)&(a[:,1]<.5),0]
        assert bool(len(fallen))==trip,(name,len(fallen))
        if name.startswith(('imposed_','oc_sustained')):
            assert .0298<=fallen[0]<=.0303,(name,fallen[0])
        if name=='manual_ARM_after_release':assert a[-1,1]>3
        elif trip:assert a[-1,1]<.1
        if name.startswith('imposed_'):assert np.min(a[:,2])>3,'Short timer unexpectedly relies on OC assertion'
        if name=='hardware_fault_1ms_latches':assert fallen[0]<.0101
        result.append({'case':name,'completed':True,'first_disable_s':float(fallen[0]) if len(fallen) else None,
                       'final_enable_V':float(a[-1,1]),'final_time_s':float(a[-1,0])})
    src='V_IN vin 0 PWL(0 0 1m 0 1.001m 25)\nR_TOP vin div 100k\nR_BOT div 0 10k\nR_ADC div adc 1k\nC_ADC adc 0 4.7n\n'
    a=run('VIN_monitor_RC',src,'v(vin) v(adc)',.003)
    assert abs(a[-1,2]-25/11)<1e-4
    level=(25/11)*(1-np.exp(-1));idx=np.flatnonzero(a[:,2]>=level)[0]
    crossing=float(a[idx,0]-.0010005)
    assert 43e-6<crossing<53e-6
    summary={'status':'PASS_ISOLATED_FUNCTIONAL_BENCHES','solver':'ngspice 44.2',
        'tests':result,'monitor_DC_V_at_25V':float(a[-1,2]),'monitor_63percent_delay_s':crossing,
        'embedded_library_used':True,'actual_load_steps_simulated':False,
        'embedded_project_sha256':hashlib.sha256(ms.read_bytes()).hexdigest(),
        'embedded_library_sha256':hashlib.sha256(lib.encode()).hexdigest(),
        'whole_Buck_transient_run':False,'native_Multisim_run':False,'STM32_firmware_test':False,
        'efficiency_verified':False,'scope':'Imposed OC/voltage/ARM signals; not reproduction of attachment peaks or durations'}
    (ROOT/'results/data/protection_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
