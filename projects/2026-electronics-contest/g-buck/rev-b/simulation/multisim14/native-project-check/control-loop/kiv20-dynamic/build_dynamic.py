"""Ki20/fuse-restored dynamic load copy; native execution must be checked separately."""
from pathlib import Path
import sys,re,json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent),str(HERE.parents[1]),str(HERE.parent/'kiv20-regression')]
from ms14_project import PROJECT,unpack,pack,parse,components,elements,clean,inspect,block
from stabilize_transient import analysis_options,verify_independent_decoder
from build_projects import replace_component,replace_templates,hide_cached_value
from build_regression import model_text,ctrl
SOURCE=PROJECT/'downloads/GBUCK_KIV20_CV25_20R_100ms.ms14'
DEST=PROJECT/'downloads/GBUCK_KIV20_AUTO_20R_8R_5R_180ms.ms14'
LOAD='GLOAD %t1 %t2 VALUE={V(%t1)*V(GLOAD_CTRL)}\nVLOAD_CTRL GLOAD_CTRL %t2 PWL(0 0.05 80m 0.05 80.1m 0.125 130m 0.125 130.1m 0.2 180m 0.2)'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    data=SOURCE.read_bytes();xml,_=unpack(data);base=parse(xml);text=xml.decode('ascii')
    by={x['display_ref']:x for x in components(base)}
    assert by['V1']['parameters'][1]=='25' and by['RL']['parameters'][1]=='20'
    assert by['F1']['ports']=={'2':'5','1':'8'} and by['R1']['ports']=={'2':None,'1':None}
    assert 'G_IV COM IV VALUE={20*' in ctrl(base)
    text=replace_component(text,'R4',lambda b:replace_templates(b,LOAD,'r'))
    load_comp=next(e for e in elements(base,'CiComponent').values() if clean(e.get('LocalName'))=='R4')
    text=hide_cached_value(text,load_comp.get('SymCompID'))
    tran=block(text,'TRAN');new=tran.replace('TSTOP:double{0.1}','TSTOP:double{0.18}',1);assert new!=tran
    new,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}','PLOT_TITLE:string{KIV20_AUTO_20R_8R_5R 180ms}',new);assert n==1
    text=text.replace(tran,new,1);out=text.encode('ascii');root=parse(out);info=inspect(root)
    assert components(root)==components(base)
    assert model_text(root)==model_text(base) and ctrl(root)==ctrl(base)
    assert analysis_options(out)==analysis_options(xml)
    assert info['selected_outputs']==inspect(base)['selected_outputs']
    assert info['transient_settings']=={**inspect(base)['transient_settings'],'TSTOP':'0.18'}
    assert all(info['connectivity_checks'].values())
    tpl=clean(next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))=='R4').find('.//CiaSpiceTmpltExprt').get('String'))
    assert tpl==LOAD
    output=pack(out);verify_independent_decoder(output,out);DEST.write_bytes(output)
    result={'date':'2026-10-24','baseline':str(SOURCE.relative_to(PROJECT)),'baseline_sha256':sha(SOURCE),'output':str(DEST.relative_to(PROJECT)),'output_sha256':sha(DEST),'source_unchanged':SOURCE.read_bytes()==data,'all_component_connections_values_and_vendor_models_preserved':True,'C_Ki20_controller_template_preserved':True,'solver_options_preserved':True,'selected_outputs':info['selected_outputs'],'time_settings':info['transient_settings'],'load_model':LOAD,'load_stages_ohm':[20,8,5],'load_transition_intervals_s':[[.08,.0801],[.13,.1301]],'proposed_observation_windows_s':[[.06,.075],[.11,.125],[.16,.175]],'both_DCL_decoders_verified':True,'native_multisim_execution_verified':False,'schematic_impact':'No wire/pin/power-part changes; RL simulation template becomes time-dependent conductance and its cached fixed value is hidden.','components_BOM_PCB_impact':'No board change; load sequence is an external test stimulus. F1 remains2A connected.','simulation_model_impact':'Same Ki20 controller, input25V, driver and power parts; only external load template, analysis100->180ms and plot label change. Relative to earlier Ki100 AUTO this is a separate control/fuse/time baseline, not a reused result.'}
    check=HERE/'results/data/build_checks.json';check.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))

def package_existing():
    check=HERE/'results/data/build_checks.json';j=json.loads(check.read_text());assert sha(DEST)==j['output_sha256'] and sha(SOURCE)==j['baseline_sha256']
    load_check=HERE/'results/data/load_bench.json'
    if load_check.exists():
        bench=json.loads(load_check.read_text())
        assert bench['native_project_sha256']==j['output_sha256'] and bench['all_load_stages_passed']
    package=PROJECT/'downloads/Multisim14_Ki20动态切换工况_2026-10-24.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(DEST,DEST.name);z.write(HERE/'README.md','请先阅读.md');z.write(check,'build_checks.json')
        for name in ['load_bench.json','native_user_feedback.json','cursor_readings_130ms.json','cursor_points_130ms.csv']:
            p=HERE/'results/data'/name
            if p.exists():z.write(p,name)
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    result={'date':'2026-10-24','package':str(package.relative_to(PROJECT)),'sha256':sha(package),'native_binary_matches_build':True,'zip_integrity_verified':True,'cloud_native_execution_performed':False,'user_native_screenshot_received':(HERE/'results/data/native_user_feedback.json').exists(),'exact_native_waveform_verified':False}
    (HERE/'results/data/delivery_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    if '--package-only' in sys.argv:package_existing()
    else:main()
