"""Add a functional protection model inside V_EN of a separate native test copy.
The canvas is NOT a per-component redraw of the protection sheet.
"""
from pathlib import Path
import sys,re,json,hashlib
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT.parent),str(ROOT.parent/'control-loop')]
from ms14_project import PROJECT,unpack,pack,parse,components,inspect,block,elements,clean
from stabilize_transient import analysis_options,verify_independent_decoder
from build_projects import replace_component,replace_templates,hide_cached_value
SOURCE=PROJECT/'downloads/GBUCK_KIV20_CV25_20R_100ms.ms14'
DEST=PROJECT/'downloads/GBUCK_REVB_PROT_POS_INJECT_12ms.ms14'
MODEL=(ROOT/'REVB_SENSE_PROTECT.lib').read_text()
ARM='PWL(0 0 3m 0 3.00001m 3.3 3.1m 3.3 3.10001m 0 5.5m 0 5.50001m 3.3 7m 3.3 7.00001m 0 8m 0 8.00001m 3.3 8.1m 3.3 8.10001m 0)'
WRAPPER='''* FUNCTIONAL RevB sensor/comparator/POR/latch test, not real IC/firmware validation
V_PS_3V3 PS_3V3 %t2 PWL(0 0 10u 0 110u 3.3 12m 3.3)
V_PS_5 PS_5 %t2 5
V_PS_ARM PS_ARM %t2 '''+ARM+'''
V_PS_MCU PS_MCU %t2 3.3
* +55mV measurement offset means +2.2A apparent IL; no real short-circuit injected
V_PS_INJECT PS_INJECT %t2 PWL(0 0 5m 0 5.001m 0.055 6m 0.055 6.001m 0 12m 0)
E_PS_ILPLUS PS_ILPLUS %t2 VALUE={V(2,%t2)+V(PS_INJECT,%t2)}
XPS 8 6 7 PS_ILPLUS 3 VOUT PS_3V3 PS_5 PS_ARM PS_MCU %t2 %t1 PS_FAULT PS_SAFE PS_ILBI PS_IIN PS_IOUT PS_AVIN PS_AIIN PS_AVOUT PS_AIOUT PS_AIL PS_VP PS_VN PS_VO PS_PORRC PS_POROK REVB_SENSE_PROTECT
'''

def main():
    original=SOURCE.read_bytes();xml,_=unpack(original);base=parse(xml);text=xml.decode('ascii')
    old={x['display_ref']:x for x in components(base)};assert old['V_EN']['internal_ref']=='V4'
    assert old['U1']['ports']['^SD']==old['V_EN']['ports']['1']=='17'
    assert old['F1']['ports']=={'2':'5','1':'8'} and old['R1']['ports']=={'2':None,'1':None}
    candidate=replace_component(text,'V4',lambda b:replace_templates(b,WRAPPER+MODEL,'v'))
    v_en=next(e for e in elements(base,'CiComponent').values() if clean(e.get('LocalName'))=='V4')
    candidate=hide_cached_value(candidate,v_en.get('SymCompID'))
    tran=block(candidate,'TRAN');new=tran.replace('TSTOP:double{0.1}','TSTOP:double{0.012}',1);assert new!=tran
    new,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}','PLOT_TITLE:string{REVB_PROT_POS_INJECT 12ms}',new);assert n==1
    # Existing node17 is IR2104 /SD; g_l shows physical low-gate drive.
    for node in ['$17','$g_l']:
        pat=r'(NODE:list\{GROUP:long\{)0(\}\s*PLOTDEVICETYPE:long\{0\}\s*TYPE:long\{3\}\s*NAME:string\{'+re.escape(node)+r'\})'
        new,n=re.subn(pat,r'\g<1>768\2',new);assert n==1
    pat=r'(NODE:list\{GROUP:long\{)768(\}\s*PLOTDEVICETYPE:long\{0\}\s*TYPE:long\{0\}\s*NAME:string\{@rrs_out\[i\]\})'
    new,n=re.subn(pat,r'\g<1>0\2',new);assert n==1
    candidate=candidate.replace(tran,new,1).encode('ascii');r=parse(candidate);info=inspect(r)
    assert components(r)==components(base)
    def models(root):return {clean(e.get('LocalName')):clean(e.find('.//CiaCString').get('String')) for e in elements(root,'CiModel').values()}
    assert models(r)==models(base)
    def template(root,name):return clean(next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))==name).find('.//CiaSpiceTmpltExprt').get('String'))
    assert template(r,'V3')==template(base,'V3')
    assert template(r,'V4')==WRAPPER+MODEL
    assert analysis_options(candidate)==analysis_options(xml)
    assert info['transient_settings']=={**inspect(base)['transient_settings'],'TSTOP':'0.012'}
    assert set(info['selected_outputs'])=={'$vout','$17','$g_l'}
    data=pack(candidate);verify_independent_decoder(data,candidate);DEST.write_bytes(data)
    report={'date':'2026-10-24','baseline':str(SOURCE.relative_to(PROJECT)),'baseline_sha256':hashlib.sha256(original).hexdigest(),'output':str(DEST.relative_to(PROJECT)),'output_sha256':hashlib.sha256(data).hexdigest(),'source_unchanged':SOURCE.read_bytes()==original,'all_physical_component_parameters_and_ports_preserved':True,'vendor_models_and_Ki20_control_template_preserved':True,'new_behavior':'V_EN constant source template replaced by functional RevB chain, ideal auxiliary rails, ARM/MCU stimuli and apparent IL fault injection','fault_injection':'Measured IL input receives +55mV (=+2.2A apparent IL) at5-6ms; does not create a real power short or quantify fault energy','native_canvas_disclosure':'V_EN symbol reused and old3.3V value hidden; protection internals are SPICE model, not original-sheet components drawn in GUI','analysis_settings_preserved_except_duration':True,'duration_s':.012,'selected_outputs':info['selected_outputs'],'both_DCL_decoders_verified':True,'native_multisim_execution_performed':False,'schematic_impact':'Separate simulation copy changes V_EN simulation template and plotting only; no physical wires/pins/power-part values changed','components_BOM_PCB_impact':'No physical redesign or new board parts; added model RC/diode/switch elements are assumptions, not procurement additions','limits':'Not manufacturer timing, common-mode/offset, fuse thermal or complete original-chip/firmware validation'}
    (ROOT/'results/data/native_build_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
