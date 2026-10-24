"""Extract the delivered protection copy and check its actual power-stage gate-off path.
Test stimulus is a sensor offset, not a real power short; thermal fuse not simulated.
"""
from pathlib import Path
import sys,re,json,hashlib,subprocess,tempfile,os
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT.parent),str(ROOT.parent/'control-loop')]
from ms14_project import unpack,parse,elements,clean,inspect
from verify_power_stage import power_stage_source
from verify_driver import NG
from build_native import DEST

def main():
    global DEST
    is_reset='--reset' in sys.argv
    is_freeze='--freeze' in sys.argv
    if is_reset:
        from build_reset_comparison import DEST as RESET_DEST
        DEST=RESET_DEST
    if is_freeze:
        from build_freeze_comparison import DEST as FREEZE_DEST
        DEST=FREEZE_DEST
    budget=float(os.environ.get('REVB_COUPLED_TIMEOUT_S','300' if is_freeze else '90'))
    case='coupled_freeze' if is_freeze else ('coupled_reset' if is_reset else 'coupled_native')
    root=parse(unpack(DEST.read_bytes())[0]);base=power_stage_source(root);stop=float(inspect(root)['transient_settings']['TSTOP'])
    def tpl(name):return clean(next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))==name).find('.//CiaSpiceTmpltExprt').get('String'))
    ctl=tpl('V3');ctl_i=next(l for l in ctl.splitlines() if l.startswith('XCTRL ')).replace('%t1','1').replace('%t2','0').replace('VOUT','4');ctl_def=ctl[ctl.index('.SUBCKT'):]
    en=tpl('V4').replace('%t1','17').replace('%t2','0').replace('VOUT','4');split=en.index('.SUBCKT');wrapper,protect=en[:split],en[split:]
    source,n=re.subn(r'(?m)^V3 .*$',lambda _:ctl_i,base,count=1);assert n==1
    source,n=re.subn(r'(?m)^V_EN .*$',lambda _:wrapper,source,count=1);assert n==1
    assert base[base.index('.SUBCKT'):] in source
    source+=ctl_def+'\n'+protect+'\n.options method=trap reltol=0.003 abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=100\n.save v(17) v(13) v(11,15) v(4) v(ps_fault) v(ps_safe) v(ps_ilbi) v(ps_arm) v(xctrl.ii) v(xctrl.iv) i(l1) v(ps_vp)\n.tran 50n '+str(stop)+' 0 50n\n'
    # Embedded power/driver definitions are extracted transiently, not redistributed as standalone libraries.
    with tempfile.TemporaryDirectory(prefix='revb-protect-coupled-') as td:
        w=Path(td);init=w/'init';init.mkdir();lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
        (init/'spinit').write_text('\n'.join('codemodel '+str(lib/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
        raw=w/'trace.txt';net=w/'test.cir';net.write_text(source+f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(17) v(13) v(11,15) v(4) v(ps_fault) v(ps_safe) v(ps_ilbi) v(ps_arm) v(xctrl.ii) v(xctrl.iv) i(l1) v(ps_vp)\nquit\n.endc\n.end\n')
        try:
            p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],capture_output=True,text=True,env=dict(os.environ,SPICE_SCRIPTS=str(init)),timeout=budget);log=p.stdout+p.stderr;code=p.returncode
        except subprocess.TimeoutExpired as exc:
            log=(exc.stdout.decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or ''))+(exc.stderr.decode(errors='replace') if isinstance(exc.stderr,bytes) else (exc.stderr or ''))+f'\nERROR: Coupled diagnostic exceeded{budget:g}s wall-time budget; not a demonstrated convergence failure\n';code=None
        a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,9))
    (ROOT/'results/logs'/f'{case}_extract.log').write_text(log)
    errors=[x for x in log.splitlines() if any(s in x.lower() for s in ['error:','aborted','too small'])]
    complete=bool(code==0 and len(a)>1000 and a[-1,0]>=stop*.999 and np.isfinite(a).all() and not errors)
    checks={}
    if complete:
        val=lambda t,k:float(np.interp(t,a[:,0],a[:,k]))
        win=lambda lo,hi,k:a[(a[:,0]>=lo)&(a[:,0]<=hi),k]
        checks={'off_before_ARM':float(np.max(win(.001,.0025,1)))<.1,'enabled_after_ARM':val(.004,1)>3,'fault_lowers_DRV_EN':val(.0052,1)<.1,'safe_remains_cleared_after_fault_release_with_ARM_high':val(.0065,1)<.1 and val(.0065,6)<.1,'new_ARM_edge_initially_asserts_enable':float(np.max(win(.008,.00805,1)))>3,'sustained_enable_after_reARM':val(.0083,1)>3,'no_retrip_after_reARM':float(np.min(win(.00805,.0085,5)))>3,'both_gate_source_drives_low_while_latched':float(np.max(abs(win(.0052,.0078,2))))<.3 and float(np.max(abs(win(.0052,.0078,3))))<.3,'low_gate_switching_before_fault':float(np.max(win(.0033,.0048,2)))>8}
        if is_freeze:
            checks['no_fault_retrip_to_end']=float(np.min(win(.00805,stop,5)))>3
            checks['enable_stays_high_to_end']=float(np.min(win(.00805,stop,1)))>3
        take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//5000)),len(a)-1]);np.savetxt(ROOT/'results/data'/f'{case}_extract_sampled.csv',a[take],delimiter=',',header='time_s,DRV_EN_V,VGS_L_V,VGS_H_V,VOUT_V,FAULT_N_V,SAFE_OK_V,IL_BI_V,ARM_V,I_INTEGRATOR_STATE,V_INTEGRATOR_STATE,IL_A,VREF_POS_V',comments='')
    result={'date':'2026-10-24','wall_time_budget_s':budget,'native_project_sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'full_requested_transient_completed':complete,'requested_end_s':stop,'actual_end_s':float(a[-1,0]) if len(a) else None,'data_rows':len(a),'checks':checks,'passed':complete and all(checks.values()),'failure_messages':errors,'case':case,'reset_controller_comparison':is_reset,'freeze_controller_comparison':is_freeze,'native_multisim_execution_performed':False,'original_vendor_power_driver_models_preserved':True,'fuse_model':'Fixed1mOhm conducting resistance; thermal trip not simulated','fault_stimulus':'Apparent IL measurement offset+2.2A, not real short-circuit energy','scope':'Checks the extracted delivered model including existing power-stage/driver; does not validate manufacturer protection latency, real INA/ADC/MCU or fuse I2t'}
    if complete:
        result['reARM_window']={'current_integrator_before_ARM':val(.00799,9),'voltage_integrator_before_ARM':val(.00799,10),'IL_max_A':float(np.max(win(.008,.0085,11))),'FAULT_N_min_V':float(np.min(win(.008,.0085,5)))}
    (ROOT/'results/data'/f'{case}_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
    if complete:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axs=plt.subplots(3,1,sharex=True,figsize=(12,8))
        for ax,cols in zip(axs,[[(1,'DRV_EN'),(5,'FAULT_N'),(6,'SAFE_OK')],[(2,'VGS_L'),(3,'VGS_H')],[(4,'VOUT')]]):
            for k,label in cols:ax.plot(a[::max(1,len(a)//12000),0]*1000,a[::max(1,len(a)//12000),k],label=label)
            ax.grid(True,alpha=.25);ax.legend();ax.set_ylabel('V')
        axs[-1].set_xlabel('ms');axs[0].set_title('Functional protection injection into native power/driver copy, ngspice cross-check')
        fig.tight_layout();fig.savefig(ROOT/'results/figures'/f'{case}_gate_off.png',dpi=150);plt.close(fig)
if __name__=='__main__':main()
