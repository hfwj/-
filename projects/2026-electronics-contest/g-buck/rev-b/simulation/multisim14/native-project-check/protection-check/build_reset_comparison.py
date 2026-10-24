"""Explicit control-state-reset comparison after coupled re-ARM retrip.
Preserves the failing baseline; does not silently change original Ki20 projects.
"""
from pathlib import Path
import sys,re,json,hashlib
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT.parent),str(ROOT.parent/'control-loop')]
from ms14_project import PROJECT,unpack,pack,parse,components,elements,clean,inspect
from stabilize_transient import analysis_options,verify_independent_decoder
from build_projects import replace_component,encoded
from build_native import DEST as BASELINE
DEST=ROOT/'experimental/GBUCK_REVB_PROT_POS_INJECT_RESET_12ms.ms14'

def main():
    source=BASELINE.read_bytes();xml,_=unpack(source);text=xml.decode('ascii')
    e=next(e for e in elements(parse(xml),'CiComponent').values() if clean(e.get('LocalName'))=='V3')
    old=clean(e.find('.//CiaSpiceTmpltExprt').get('String'))
    new=old.replace('VOUT 3 7 2 GBUCK_CTRL_EQ','VOUT 3 7 2 17 GBUCK_CTRL_EQ').replace('.SUBCKT GBUCK_CTRL_EQ PWM COM VO CAP VIN ILP','.SUBCKT GBUCK_CTRL_EQ PWM COM VO CAP VIN ILP EN')
    old_iv='G_IV COM IV VALUE={20*(V(REF,COM)-V(VO,COM))+1000*(V(IREF,COM)-V(UV,COM))}'
    new_iv='G_IV COM IV VALUE={IF(V(EN,COM)<1.65,-0.01*V(IV,COM),20u*(V(REF,COM)-V(VO,COM))+0.001*(V(IREF,COM)-V(UV,COM)))}'
    old_ii='G_II COM II VALUE={50*(V(IREF,COM)-V(ILF,COM))+1000*(V(DUTY,COM)-V(UD,COM))}'
    new_ii='G_II COM II VALUE={IF(V(EN,COM)<1.65,-0.01*V(II,COM),50u*(V(IREF,COM)-V(ILF,COM))+0.001*(V(DUTY,COM)-V(UD,COM)))}'
    old_pwm='IF(TIME<2m,0,LIMIT(1650*(V(DUTY,COM)-V(SAW,COM))+1.65,0,3.3))'
    new_pwm='IF(V(EN,COM)<1.65,0,IF(TIME<2m,0,LIMIT(1650*(V(DUTY,COM)-V(SAW,COM))+1.65,0,3.3)))'
    for a,b in [(old_iv,new_iv),(old_ii,new_ii),(old_pwm,new_pwm)]:assert new.count(a)==1;new=new.replace(a,b)
    new=new.replace('C_IV IV COM 1 IC=0','C_IV IV COM 1u IC=0').replace('C_II II COM 1 IC=0','C_II II COM 1u IC=0').replace('R_IV IV COM 1G','R_IV IV COM 1e15').replace('R_II II COM 1G','R_II II COM 1e15')
    def patch(body):
        a='&amp;ASC'+encoded(old);b='&amp;ASC'+encoded(new);assert body.count(a)==2
        return body.replace(a,b)
    text=replace_component(text,'V3',patch)
    before='PLOT_TITLE:string{REVB_PROT_POS_INJECT 12ms}';after='PLOT_TITLE:string{REVB_PROT_RESET_COMPARE 12ms}';assert text.count(before)==1;text=text.replace(before,after)
    out=text.encode('ascii');r=parse(out);base=parse(xml)
    assert components(r)==components(base) and inspect(r)==inspect(base)
    assert analysis_options(out)==analysis_options(xml)
    def models(root):return {clean(e.get('LocalName')):clean(e.find('.//CiaCString').get('String')) for e in elements(root,'CiModel').values()}
    assert models(r)==models(base)
    # Exact inverse protects all original topology/metadata outside this explicit V3 model/label change.
    inverse=text.replace('&amp;ASC'+encoded(new),'&amp;ASC'+encoded(old)).replace(after,before)
    assert inverse.encode('ascii')==xml
    data=pack(out);verify_independent_decoder(data,out);DEST.write_bytes(data)
    report={'date':'2026-10-24','baseline':str(BASELINE.relative_to(PROJECT)),'baseline_sha256':hashlib.sha256(source).hexdigest(),'output':str(DEST.relative_to(PROJECT)),'output_sha256':hashlib.sha256(data).hexdigest(),'baseline_preserved':BASELINE.read_bytes()==source,'exact_inverse_XML_verified':True,'hardware_ports_values_vendor_models_and_protection_model_unchanged':True,'solver_and_stimulus_unchanged':True,'control_changes':['Controller receives actualDRV_EN as extra simulation feedback port','WhenDRV_EN<1.65V, voltage/current integrator states decay tozero with illustrative100us constant; internal model integrator C/current scaling1e-6 preserves enabled-loop dynamics','PWM forcedzero while disabled; existing Ki20/Kp/current coefficients and1A average command retained'],'physical_components_BOM_PCB_change':False,'real_firmware_modified':False,'native_multisim_execution_performed':False,'scope':'Explicit simulation control-state management comparison, not original firmware verification or instantaneous output-current limiter'}
    (ROOT/'results/data/reset_comparison_build_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
