"""A separate stop-state freeze control comparison; preserve the failing baseline."""
from pathlib import Path
import sys,re,json,hashlib
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT.parent),str(ROOT.parent/'control-loop')]
from ms14_project import PROJECT,unpack,pack,parse,components,elements,clean,inspect,block
from stabilize_transient import analysis_options,verify_independent_decoder
from build_projects import replace_component,encoded
from build_native import DEST as BASELINE
DEST=PROJECT/'downloads/GBUCK_REVB_PROT_FREEZE_20ms.ms14'

def main():
    source=BASELINE.read_bytes();xml,_=unpack(source);base=parse(xml);text=xml.decode('ascii')
    c=next(e for e in elements(base,'CiComponent').values() if clean(e.get('LocalName'))=='V3');old=clean(c.find('.//CiaSpiceTmpltExprt').get('String'))
    new=old.replace('VOUT 3 7 2 GBUCK_CTRL_EQ','VOUT 3 7 2 17 GBUCK_CTRL_EQ').replace('.SUBCKT GBUCK_CTRL_EQ PWM COM VO CAP VIN ILP','.SUBCKT GBUCK_CTRL_EQ PWM COM VO CAP VIN ILP EN')
    replacements=[('G_IV COM IV VALUE={20*(V(REF,COM)-V(VO,COM))+1000*(V(IREF,COM)-V(UV,COM))}','G_IV COM IV VALUE={IF(V(EN,COM)<1.65,0,20*(V(REF,COM)-V(VO,COM))+1000*(V(IREF,COM)-V(UV,COM)))}'),('G_II COM II VALUE={50*(V(IREF,COM)-V(ILF,COM))+1000*(V(DUTY,COM)-V(UD,COM))}','G_II COM II VALUE={IF(V(EN,COM)<1.65,0,50*(V(IREF,COM)-V(ILF,COM))+1000*(V(DUTY,COM)-V(UD,COM)))}')]
    for a,b in replacements:assert new.count(a)==1;new=new.replace(a,b)
    def patch(body):
        a='&amp;ASC'+encoded(old);b='&amp;ASC'+encoded(new);assert body.count(a)==2;return body.replace(a,b)
    text=replace_component(text,'V3',patch)
    tran=block(text,'TRAN');modified=tran.replace('TSTOP:double{0.012}','TSTOP:double{0.02}',1);assert modified!=tran
    modified,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}','PLOT_TITLE:string{REVB_PROT_FREEZE 20ms}',modified);assert n==1
    text=text.replace(tran,modified,1);out=text.encode('ascii');root=parse(out)
    assert components(root)==components(base) and analysis_options(out)==analysis_options(xml)
    assert inspect(root)['transient_settings']=={**inspect(base)['transient_settings'],'TSTOP':'0.02'}
    assert text.replace(modified,tran,1).replace('&amp;ASC'+encoded(new),'&amp;ASC'+encoded(old)).encode('ascii')==xml
    data=pack(out);verify_independent_decoder(data,out);DEST.write_bytes(data)
    report={'date':'2026-10-24','baseline':str(BASELINE.relative_to(PROJECT)),'baseline_sha256':hashlib.sha256(source).hexdigest(),'output':str(DEST.relative_to(PROJECT)),'output_sha256':hashlib.sha256(data).hexdigest(),'baseline_preserved':BASELINE.read_bytes()==source,'exact_inverse_XML_verified':True,'components_pins_values_vendor_and_protection_models_preserved':True,'active_control_coefficients_unchanged':True,'changes':['V3 controller receivesDRV_EN node17','WhileDRV_EN<1.65V, both integrator drive currents arezero; state held apart from existing1G leakage','No state reset, no new restart-ramp, no protection-threshold or gate/PWM-logic change','Transient12->20ms and plot label updated; all other solver settings unchanged'],'physical_components_BOM_PCB_change':False,'real_firmware_modified':False,'native_multisim_execution_performed':False,'scope':'Simulation control-state-management comparison only, not1A output instantaneous limiting or verified STM32 code'}
    (ROOT/'results/data/freeze_build_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
