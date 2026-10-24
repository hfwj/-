"""One-factor voltage-integral-gain sensitivity copy, not a proven fix."""
from pathlib import Path
import sys,re,json,hashlib
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent),str(HERE.parents[1])]
from ms14_project import PROJECT,unpack,pack,parse,inspect,components,block,elements,clean
from stabilize_transient import analysis_options,verify_independent_decoder
SOURCE=PROJECT/'downloads/GBUCK_OPEN_DIAG_B_100ms.ms14'
DEST=PROJECT/'downloads/GBUCK_OPEN_DIAG_C_KIV20_100ms.ms14'
OLD='G_IV COM IV VALUE={100*(V(REF,COM)-V(VO,COM))+1000*(V(IREF,COM)-V(UV,COM))}'
NEW=OLD.replace('={100*','={20*')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=SOURCE.read_bytes();xml,_=unpack(source);text=xml.decode('ascii')
    assert text.count(OLD)==2
    text=text.replace(OLD,NEW)
    tran=block(text,'TRAN');newtran,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}','PLOT_TITLE:string{OPEN_C_KIV20 CVCC_EQ + SOFT_START}',tran);assert n==1
    text=text.replace(tran,newtran,1)
    assert text.replace(newtran,tran,1).replace(NEW,OLD).encode('ascii')==xml
    revised=text.encode('ascii');r=parse(revised);base=parse(xml)
    assert components(r)==components(base)
    assert analysis_options(revised)==analysis_options(xml)
    assert inspect(r)==inspect(base)
    def models(root):return {clean(e.get('LocalName')):clean(e.find('.//CiaCString').get('String')) for e in elements(root,'CiModel').values()}
    assert models(r)==models(base)
    ctrl=next(e for e in elements(r,'CiComponent').values() if clean(e.get('LocalName'))=='V3')
    tpl=clean(ctrl.find('.//CiaSpiceTmpltExprt').get('String'));model=tpl[tpl.index('.SUBCKT'):]
    (HERE/'GBUCK_CTRL_EQ_KIV20.lib').write_text(model)
    packed=pack(revised);verify_independent_decoder(packed,revised);DEST.write_bytes(packed)
    result={'date':'2026-10-24','baseline':str(SOURCE.relative_to(PROJECT)),'baseline_sha256':sha(SOURCE),'output':str(DEST.relative_to(PROJECT)),'output_sha256':sha(DEST),'baseline_unchanged':SOURCE.read_bytes()==source,'control_change':{'voltage_outer_loop_Ki_A_per_V_s':{'before':100,'after':20},'power_and_control_other_parameters':'unchanged','template_copies_updated':2},'display_change':'Active transient plot tab identifies OPEN_C_KIV20','native_multisim_run_verified':False,'schematic_ports_values_components_BOM_PCB_change':False,'F1':'2A connected; temporary R1 disconnected, inherited unchanged','analysis_settings':analysis_options(revised),'analysis_time':inspect(r)['transient_settings'],'exact_inverse_XML_verified':True,'all_components_and_vendor_model_text_unchanged':True,'both_DCL_decoders_verified':True,'scope':'Control-parameter sensitivity test only; no stability, firmware, sensor, fuse, efficiency or physical-design acceptance'}
    (HERE/'results/C_build_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
