"""Clone the native-observed C controller into static test conditions.
No native GUI or long-transient solver execution is implied by this build.
"""
from pathlib import Path
import sys,re,json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent),str(HERE.parents[1])]
from ms14_project import PROJECT,unpack,pack,parse,inspect,components,block,elements,clean
from stabilize_transient import analysis_options,verify_independent_decoder
from build_projects import replace_component,set_parameter
SOURCE=PROJECT/'downloads/GBUCK_OPEN_DIAG_C_KIV20_100ms.ms14'
CASES=[('CV25_20R',25,'20'),('CC25_8R',25,'8'),('CC25_5R',25,'5'),('CV15_20R',15,'20'),('CV25_OPEN',25,'1e9')]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def model_text(r):return {clean(e.get('LocalName')):clean(e.find('.//CiaCString').get('String')) for e in elements(r,'CiModel').values()}
def ctrl(r):return clean(next(e for e in elements(r,'CiComponent').values() if clean(e.get('LocalName'))=='V3').find('.//CiaSpiceTmpltExprt').get('String'))
def main():
    data=SOURCE.read_bytes();xml,_=unpack(data);base=parse(xml);original={r['display_ref']:r for r in components(base)};records=[]
    assert 'G_IV COM IV VALUE={20*' in ctrl(base)
    for name,vin,load in CASES:
        text=xml.decode('ascii')
        if vin!=15:text=replace_component(text,'V1',lambda b:set_parameter(b,1,str(vin)))
        if load!='1e9':text=replace_component(text,'R4',lambda b:set_parameter(b,1,load))
        tran=block(text,'TRAN');new,n=re.subn(r'PLOT_TITLE:string\{[^}]*\}','PLOT_TITLE:string{KIV20_'+name+' 100ms}',tran);assert n==1
        pattern=r'(NODE:list\{GROUP:long\{)768(\}\s*PLOTDEVICETYPE:long\{0\}\s*TYPE:long\{4\}\s*NAME:string\{ll1#branch\})'
        new,n=re.subn(pattern,r'\g<1>0\2',new);assert n==1
        pattern=r'(NODE:list\{GROUP:long\{)0(\}\s*PLOTDEVICETYPE:long\{0\}\s*TYPE:long\{0\}\s*NAME:string\{@rrs_out\[i\]\})'
        new,n=re.subn(pattern,r'\g<1>768\2',new);assert n==1
        text=text.replace(tran,new,1);out=text.encode('ascii');r=parse(out);info=inspect(r);actual={x['display_ref']:x for x in components(r)}
        assert model_text(r)==model_text(base) and ctrl(r)==ctrl(base)
        assert analysis_options(out)==analysis_options(xml)
        assert info['transient_settings']==inspect(base)['transient_settings']
        assert set(info['selected_outputs'])=={'$vout','@rrs_out[i]'}
        assert all(info['connectivity_checks'].values())
        assert set(actual)==set(original)
        for ref in actual:
            assert actual[ref]['ports']==original[ref]['ports']
            if ref not in ['V1','RL']:assert actual[ref]==original[ref]
            else:
                assert len(actual[ref]['parameters'])==len(original[ref]['parameters'])
                assert all(i==1 or value==original[ref]['parameters'][i] for i,value in enumerate(actual[ref]['parameters']))
        assert float(actual['V1']['parameters'][1])==vin and float(actual['RL']['parameters'][1])==float(load)
        assert actual['F1']['ports']=={'2':'5','1':'8'} and actual['R1']['ports']=={'2':None,'1':None}
        output=pack(out);verify_independent_decoder(output,out)
        path=PROJECT/'downloads'/f'GBUCK_KIV20_{name}_100ms.ms14';path.write_bytes(output)
        records.append({'case':name,'input_V':vin,'load_ohm':float(load),'file':str(path.relative_to(PROJECT)),'sha256':sha(path),'power_driver_connectivity_preserved':True,'controller_and_vendor_model_text_preserved':True,'all_other_component_parameters_preserved':True,'analysis_options_and_100ms_duration_preserved':True,'native_run_verified':False,'both_container_decoders_verified':True})
    result={'date':'2026-10-24','comparison_baseline':str(SOURCE.relative_to(PROJECT)),'baseline_sha256':sha(SOURCE),'source_unchanged':SOURCE.read_bytes()==data,'controller_voltage_Ki':20,'native_feedback_for_baseline':'100ms C15V/open screenshot received; exact values not exported','new_cases_native_runs_verified':False,'schematic_impact':'V1 stimulus value and external RL test-load value only; selected measurements and plot labels updated. All wires and power/driver parts retained.','physical_components_BOM_PCB_impact':'No board changes required; RL values are external test conditions. F1 remains connected2A.','model_impact':'Same C ideal controller and modified driver models, RELTOL0.003,100ms. Earlier Ki100 results do not verify these cases.','cases':records}
    check=HERE/'results/build_checks.json';check.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    package=PROJECT/'downloads/Multisim14_Ki20静态回归工况_2026-10-24.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(SOURCE,SOURCE.name)
        for row in records:
            p=PROJECT/row['file'];z.write(p,p.name)
        z.write(HERE/'README.md','请先阅读.md');z.write(check,'build_checks.json')
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    print(json.dumps({'cases_built':len(records),'baseline_unchanged':result['source_unchanged'],'package':str(package.relative_to(PROJECT)),'package_sha256':sha(package)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
