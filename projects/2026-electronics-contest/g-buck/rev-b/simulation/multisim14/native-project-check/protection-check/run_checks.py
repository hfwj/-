"""Actual ngspice executions for the functional RevB sensing/protection study.
No manufacturer-device or native-Multisim certification is implied.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,subprocess,tempfile,os,csv
import numpy as np
ROOT=Path(__file__).resolve().parent
NG=Path(os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice'))
MODEL=(ROOT/'REVB_SENSE_PROTECT.lib').read_text()
PORTS='vinext shuntin vin lraw vcap vout vd v5 arm en 0 drv fault safe ilbi iin iout avin aiin avout aiout ail vp vn vo porc porok'
COLS=['drv','fault','safe','ilbi','iin','iout','avin','aiin','avout','aiout','ail','vp','vn','vo','porc','porok','arm','en','xchain.va','vout']

def fixture(il='1',vo='10',arm='0',en='3.3',vin='25',iin='.5',iout='.5',va_load='0',vd='3.3',model=MODEL):
    text=f'''* RevB independent sensing/protection functional bench; noBuck plant or thermal fuse
V_DIG vd 0 {vd}
V_5 v5 0 5
V_EXT vinext 0 {vin}
V_CM vin 0 24.5
V_OUT vout 0 {vo}
RS_IN shuntin vin .05
I_IN_LOOP vin shuntin {iin}
RS_OUT vcap vout .05
I_OUT_LOOP vout vcap {iout}
RS_L lraw vcap .025
I_IL_LOOP vcap lraw {il}
'''
    if arm is not None:text+=f'V_ARM arm 0 {arm}\n'
    if en is not None:text+=f'V_MCU en 0 {en}\n'
    text+=f'Xchain {PORTS} REVB_SENSE_PROTECT\nI_VA_TEST xchain.va 0 {va_load}\n'+model
    return text

def execute(name,source,analysis,columns=COLS):
    prefix=source+'\n.options reltol=0.001 abstol=1e-10 vntol=1e-6 method=gear\n.save '+' '.join(f'v({n})' for n in columns)+'\n'+analysis+'\n'
    with tempfile.TemporaryDirectory(prefix='revb-protect-'+name+'-') as td:
        w=Path(td);init=w/'init';init.mkdir();lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(lib/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        raw=w/'data.txt';net=w/'test.cir'
        net.write_text(prefix+f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} '+' '.join(f'v({n})' for n in columns)+'\nquit\n.endc\n.end\n')
        try:
            p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],capture_output=True,text=True,env=dict(os.environ,SPICE_SCRIPTS=str(init)),timeout=45);log=p.stdout+p.stderr;code=p.returncode
        except subprocess.TimeoutExpired:
            log='ERROR: execution exceeded45s wall-time budget\n';code=None
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,len(columns)+1))
    (ROOT/'results/logs'/f'{name}.log').write_text(log)
    (ROOT/'netlists'/f'{name}.cir').write_text(prefix+'\n.end\n')
    errors=[x for x in log.splitlines() if any(s in x.lower() for s in ['error:','aborted','too small'])]
    ok=bool(code==0 and len(a)>5 and np.isfinite(a).all() and not errors)
    check={'case':name,'solver':'ngspice44.2/psa','source_sha256':hashlib.sha256(prefix.encode()).hexdigest(),'completed':ok,'rows':len(a),'last_scale_value':float(a[-1,0]) if len(a) else None,'failure_messages':errors,'functional_model_only':True,'native_multisim_execution_performed':False}
    if len(a):
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//3000)),len(a)-1]);np.savetxt(ROOT/'results/data'/f'{name}_sampled.csv',a[take],delimiter=',',header='scale,'+','.join(columns),comments='')
    return check,a

def at(a,t,col):return float(np.interp(t,a[:,0],a[:,1+COLS.index(col)]))
def fault_time(a,start,end):
    part=a[(a[:,0]>=start)&(a[:,0]<=end)];hit=part[part[:,1+COLS.index('fault')]<.5]
    return float(hit[0,0]) if len(hit) else None
ARM='PWL(0 0 3m 0 3.00001m 3.3 3.1m 3.3 3.10001m 0 5.5m 0 5.50001m 3.3 7m 3.3 7.00001m 0 8m 0 8.00001m 3.3 8.1m 3.3 8.10001m 0)'

def transient_case(kind):
    model=MODEL;il='1';vo='10';en='3.3';arm=ARM
    if kind in ['positive','positive_adc10x']:
        il='PWL(0 1 5m 1 5.001m 2.2 6m 2.2 6.001m 1 10m 1)'
        if kind.endswith('10x'):model=model.replace('C_IL_ADC ADC_IL COM 4.7n','C_IL_ADC ADC_IL COM 47n')
    elif kind=='negative':il='PWL(0 1 5m 1 5.001m -2.2 6m -2.2 6.001m 1 10m 1)'
    elif kind=='overvoltage':vo='PWL(0 10 5m 10 5.001m 12 6m 12 6.001m 10 10m 10)'
    elif kind=='overvoltage_small':vo='PWL(0 10 5m 10 5.001m 11.2 6m 11.2 6.001m 10 10m 10)'
    elif kind=='default_inputs_open':arm=None;en=None
    elif kind=='mcu_disable':en='PWL(0 3.3 4m 3.3 4.00001m 0 4.5m 0 4.50001m 3.3 10m 3.3)'
    elif kind=='startup_Q_initial_high':model=model.replace('C_M_Q Q_MEM COM 10p IC=0','C_M_Q Q_MEM COM 10p IC=3.3')
    elif kind=='short_oc_pulse':il='PWL(0 1 5m 1 5.00001m 2.2 5.00011m 2.2 5.00012m 1 10m 1)'
    rec,a=execute(kind,fixture(il=il,vo=vo,arm=arm,en=en,model=model),'.tran 100n 10m 0 200n uic')
    checks={}
    if rec['completed']:
        checks['requested_end_reached']=a[-1,0]>=.01*.999
        checks['not_enabled_before_ARM']=at(a,.0025,'drv')<.1
        if kind=='default_inputs_open':checks['open_MCU_inputs_default_off']=np.max(a[a[:,0]>.001,1+COLS.index('drv')])<.1
        else:checks['ARM_rising_edge_enables']=at(a,.004,'drv')>3
        if kind in ['positive','positive_adc10x','negative','overvoltage','overvoltage_small']:
            checks.update({'fault_detected':at(a,.0052,'fault')<.1,'async_clear_disables':at(a,.0052,'safe')<.1 and at(a,.0052,'drv')<.1,'fault_released':at(a,.0063,'fault')>3,'ARM_held_high_does_not_restart':at(a,.0068,'safe')<.1 and at(a,.0068,'drv')<.1,'no_new_edge_remains_off':at(a,.0075,'drv')<.1,'new_ARM_edge_reenables':at(a,.0083,'drv')>3})
            trip=fault_time(a,.005,.0052);rec['model_FAULT_low_time_s']=trip;rec['illustrative_delay_after_test_edge_s']=trip-.005 if trip else None
        if kind=='mcu_disable':checks.update({'MCU_low_disables':at(a,.0042,'drv')<.1,'MCU_low_does_not_clear_SAFE':at(a,.0042,'safe')>3,'MCU_high_resumes_when_SAFE_was_not_cleared':at(a,.0047,'drv')>3})
        if kind=='startup_Q_initial_high':checks['POR_and_fault_clear_high_initial_state']=at(a,.0001,'safe')<.1
        if kind=='short_oc_pulse':
            checks['short_pulse_not_claimed_cycle_by_cycle_protection']=at(a,.0052,'drv')>3
            rec['limitation_observed']='100ns input pulse is filtered by assumed1us amplifier response and does not trip; not a physical minimum pulse-width guarantee.'
    checks={k:bool(v) for k,v in checks.items()}
    rec['checks']=checks;rec['passed']=rec['completed'] and all(checks.values())
    (ROOT/'results/data'/f'{kind}.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n')
    return rec,a

def dc_case(name,source,analysis,checks_kind):
    rec,a=execute(name,source,analysis)
    checks={}
    if rec['completed']:
        vals=lambda n:a[:,1+COLS.index(n)]
        if checks_kind in ['iin','iout','ilbi','avin','avout']:
            va=vals('xchain.va');expected={'iin':a[:,0],'iout':a[:,0],'ilbi':.5*va+.5*a[:,0],'avin':a[:,0]/11,'avout':a[:,0]/11}[checks_kind]
            err=float(np.max(abs(vals(checks_kind)-expected)));checks['transfer_error_below_0p2mV']=err<.0002;rec['max_transfer_error_V']=err
        elif checks_kind=='il_threshold':
            high=vals('fault')>3;va=float(np.mean(vals('xchain.va')));pos_expected=(34/44-.5)*va/.5;neg_expected=(10/44-.5)*va/.5
            pos_low=a[(a[:,0]>0)&~high,0];neg_high=a[(a[:,0]<0)&high,0]
            pos=float(pos_low.min());neg=float(neg_high.min());checks['positive_threshold_within_2p1mA']=abs(pos-pos_expected)<.0021;checks['negative_release_within_2p1mA']=abs(neg-neg_expected)<.0021
            rec.update({'analog_supply_V':va,'positive_trip_grid_A':pos,'negative_release_grid_A':neg,'expected_positive_A':pos_expected,'expected_negative_A':neg_expected,'grid_resolution_A':float(a[1,0]-a[0,0])})
        elif checks_kind=='ov_threshold':
            low=a[vals('fault')<.5,0];trip=float(low.min());va=float(np.mean(vals('xchain.va')));expected=va*10/33*11;checks['OV_threshold_within_1p1mV']=abs(trip-expected)<.0011;rec.update({'analog_supply_V':va,'OV_trip_grid_V':trip,'expected_OV_V':expected,'grid_resolution_V':.001})
        elif checks_kind=='clamp':
            x=vals('avin');checks['ADC_clamped_between_minus0p4_and3p7V']=float(x.min())>-.4 and float(x.max())<3.7;rec['ADC_range_V']=[float(x.min()),float(x.max())]
    checks={k:bool(v) for k,v in checks.items()}
    rec['checks']=checks;rec['passed']=rec['completed'] and all(checks.values())
    (ROOT/'results/data'/f'{name}.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n');return rec,a

def main():
    for p in ['results/data','results/logs','results/figures','netlists']:(ROOT/p).mkdir(parents=True,exist_ok=True)
    tasks=[lambda:dc_case('dc_iin',fixture(),'.dc I_IN_LOOP 0 3 .01','iin'),lambda:dc_case('dc_iout',fixture(),'.dc I_OUT_LOOP 0 3 .01','iout'),lambda:dc_case('dc_il',fixture(),'.dc I_IL_LOOP -2.4 2.4 .001','ilbi'),lambda:dc_case('dc_vin',fixture(),'.dc V_EXT 0 30 .1','avin'),lambda:dc_case('dc_vout',fixture(),'.dc V_OUT 0 12 .01','avout'),lambda:dc_case('dc_il_threshold',fixture(),'.dc I_IL_LOOP -2.4 2.4 .001','il_threshold'),lambda:dc_case('dc_ov_threshold',fixture(),'.dc V_OUT 9 12 .001','ov_threshold'),lambda:dc_case('dc_adc_clamp',fixture(),'.dc V_EXT -20 60 .1','clamp')]
    for load in ['.005','.01']:
        tasks.append(lambda load=load:dc_case('dc_il_iq_'+load[1:],fixture(va_load=load),'.dc I_IL_LOOP -2.4 2.4 .001','il_threshold'))
    transient_names=['positive','negative','overvoltage','overvoltage_small','positive_adc10x','default_inputs_open','mcu_disable','startup_Q_initial_high','short_oc_pulse']
    tasks.extend(lambda n=n:transient_case(n) for n in transient_names)
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda f:f(),tasks))
    by={r['case']:(r,a) for r,a in results}
    cross_checks={'raw_IL_protection_not_routed_through_ADC_filter':abs(by['positive'][0]['model_FAULT_low_time_s']-by['positive_adc10x'][0]['model_FAULT_low_time_s'])<1e-6}
    summary={'date':'2026-10-24','model_sha256':hashlib.sha256(MODEL.encode()).hexdigest(),'solver':'ngspice44.2/psa','all_cases_completed':all(r['completed'] for r,_ in results),'all_functional_checks_passed':all(r['passed'] for r,_ in results) and all(cross_checks.values()),'cross_checks':cross_checks,'case_count':len(results),'cases':[r for r,_ in results],'native_multisim_execution_performed':False,'manufacturer_active_models_used':False,'physical_latency_fuse_thermal_accuracy_or_real_fault_energy_verified':False,'model_assumptions':['INA nominal gain20/zerooffset, rail clipping,1us pole and1ohm output model','LM393 open-collector functional polarity with0.3us pole and1uV numerical hysteresis','HC14 assumed0.3/0.6 relative thresholds; HC74 edge/memory model; output resistances illustrative','Original passive reference/ADC/POR values and connectivity; analog active quiescent currents omitted, separate5mA/10mA diagnostic loads','No INA common-mode/PWM rejection or real IC timing qualification; short-circuit energy and fuse I2t not modeled']}
    (ROOT/'results/data/verification_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(4,1,figsize=(12,10),sharex=True)
        _,a=by['positive']
        for ax,cols in zip(axes,[['ilbi','vp','vn'],['fault','porok'],['arm','safe'],['drv','en']]):
            for col in cols:ax.plot(a[:,0]*1000,a[:,1+COLS.index(col)],label=col)
            ax.grid(True,alpha=.25);ax.legend(loc='right');ax.set_ylabel('V')
        axes[-1].set_xlabel('Time / ms');axes[0].set_title('Functional RevB chain: positive fault, held ARM, re-ARM (assumed active dynamics)')
        fig.tight_layout();fig.savefig(ROOT/'results/figures/positive_fault_latch.png',dpi=150);plt.close(fig)
    except ImportError:pass
    print(json.dumps({'case_count':summary['case_count'],'completed':summary['all_cases_completed'],'passed':summary['all_functional_checks_passed'],'failed':[r['case'] for r,_ in results if not r['passed']],'cross_checks':cross_checks},ensure_ascii=False,indent=2))
    assert summary['all_cases_completed'] and summary['all_functional_checks_passed']
if __name__=='__main__':main()
