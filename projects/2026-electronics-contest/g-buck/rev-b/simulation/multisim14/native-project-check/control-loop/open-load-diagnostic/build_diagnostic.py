"""Build an analysis-only A/B diagnostic; no native solver execution."""
from pathlib import Path
import sys,re,json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from ms14_project import PROJECT,unpack,pack,parse,inspect,components,block
from stabilize_transient import analysis_options,verify_independent_decoder
SOURCE=PROJECT/'references/user-projects/2026-10-24_15V空载_恢复F1_本机回传.ms14'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    data=SOURCE.read_bytes();xml,_=unpack(data);text=xml.decode('ascii');tran=block(text,'TRAN')
    assert 'MSM_ASYS_OPT:long{0}' in tran
    a=tran.replace('TSTOP:double{0.03}','TSTOP:double{0.1}',1);assert a!=tran
    pat=r'(NODE:list\{GROUP:long\{)0(\}\s*PLOTDEVICETYPE:long\{0\}\s*TYPE:long\{4\}\s*NAME:string\{ll1#branch\})'
    a,n=re.subn(pat,r'\g<1>768\2',a);assert n==1
    pat=r'(\d+:list\{IsEnabled:long\{1\}\s+reltol:double\{)0\.01(\}\s*\})'
    b,n=re.subn(pat,r'\g<1>0.003\2',a);assert n==1
    assert re.sub(r'(reltol:double\{)0\.003(\})',r'\g<1>0.01\2',b)==a
    rows=[]
    for label,new in [('A',a),('B',b)]:
        candidate=text.replace(tran,new,1).encode('ascii')
        # Exact inverse proves all XML outside the active transient block is untouched.
        assert candidate.decode('ascii').replace(new,tran,1).encode('ascii')==xml
        root=parse(candidate);info=inspect(root);opts=analysis_options(candidate)
        assert components(root)==components(parse(xml))
        assert all(info['connectivity_checks'].values())
        assert info['transient_settings']=={'TSTOP':'0.1','TSTART':'0','TMAX':'5e-008','IC':'dcop'}
        assert set(info['selected_outputs'])=={'$vout','ll1#branch'}
        expected=analysis_options(xml);expected['reltol']['value']='0.01' if label=='A' else '0.003'
        assert opts==expected
        path=PROJECT/'downloads'/f'GBUCK_OPEN_DIAG_{label}_100ms.ms14'
        output=pack(candidate);verify_independent_decoder(output,candidate);path.write_bytes(output)
        rows.append({'id':label,'file':str(path.relative_to(PROJECT)),'sha256':digest(path),'native_open_and_run_verified':False,'analysis_options':opts,'time_settings':info['transient_settings'],'selected_outputs':info['selected_outputs'],'exact_inverse_outside_TRAN_verified':True,'components_and_models_and_control_unchanged':True,'both_container_decoders_verified':True})
    result={'date':'2026-10-24','baseline_file':str(SOURCE.relative_to(PROJECT)),'baseline_sha256':digest(SOURCE),'baseline_retained':SOURCE.read_bytes()==data,'A_to_B_only_change':'Active transient RELTOL0.01->0.003','purpose':'Numerical sensitivity diagnostic only; neither a stability fix nor a validation of firmware/protection','schematic_components_BOM_PCB_impact':'None relative to returned source; F1=2A connected, temporaryR1 disconnected in both copies','cases':rows}
    check=HERE/'results/build_checks.json';check.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    package=PROJECT/'downloads/Multisim14_空载起伏_AB对照_2026-10-24.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        for row in rows:
            path=PROJECT/row['file'];z.write(path,path.name)
        z.write(HERE/'README.md','请先阅读.md');z.write(check,'build_checks.json')
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    print(json.dumps({'checks':result,'package':str(package.relative_to(PROJECT)),'package_sha256':digest(package)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
