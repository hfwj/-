"""Exercise title-as-netlist-content parsing, matching the reported import issue.
Uses ngspice only; does not claim a native Multisim regression test.
"""
from pathlib import Path
import os,subprocess,tempfile,json,hashlib
from build_circuits import ROOT,CASES,MODEL

NG=os.environ.get('NGSPICE','/workspace/tools/ngspice/usr/bin/ngspice')

def probe(name,src,expected_failure=False):
    with tempfile.TemporaryDirectory(prefix='gbuck-header-',dir='/tmp') as td:
        work=Path(td);data=work/'trace.txt'
        control=f'.control\nset wr_singlescale\nrun\nwrdata {data} v(VOUT)\nquit\n.endc'
        # Add a separate outer title. The delivered first line is now ordinary
        # content, as in an importer that does not reserve it as a title card.
        lines=['Header parsing regression']
        for line in src.splitlines():
            if line.startswith('.TRAN '):line='.TRAN 1n 20n 0 1n UIC'
            if line.startswith('.PROBE '):line=control
            lines.append(line)
        net=work/'probe.cir';net.write_text('\n'.join(lines)+'\n',encoding='ascii')
        p=subprocess.run([NG,'-D','ngbehavior=psa','-b',str(net)],capture_output=True,text=True)
        log=p.stdout+p.stderr
        (ROOT/'results/logs'/f'header_import_{name}.log').write_text(log)
        failed=p.returncode!=0 or not data.exists() or any(x in log.lower() for x in ['error:','aborted','timestep too small'])
        if expected_failure:
            assert failed,'Uncommented title was expected to reproduce an import-context parse failure'
            return {'expected_legacy_parse_failure_reproduced':True}
        assert not failed,log[-1800:]
        last=data.read_text().splitlines()[-1].split()
        end=float(last[0]);assert end>=20e-9*.999
        return {'case':name,'distributed_source_sha256':hashlib.sha256(src.encode()).hexdigest(),
                'title_treated_as_ordinary_netlist_line':True,'short_startup_end_s':end,
                'native_multisim_retest':False,'parser_and_short_startup_passed':True}

def main():
    sample=(ROOT/'circuits/04_25V_8ohm.cir').read_text()
    assert sample.startswith('* G problem ')
    model=(ROOT/'models/G_BUCK_RevB_EQ.lib').read_bytes()
    assert model.startswith(b'.SUBCKT GBUCK_REVB_EQ ')
    assert model==MODEL[MODEL.index('.SUBCKT GBUCK_REVB_EQ '):].encode('ascii')
    assert model.count(b'.SUBCKT ')==2 and model.count(b'.ENDS ')==2
    for ext in ['cir','txt']:
        assert (ROOT/'models'/f'G_BUCK_RevB_EQ.{ext}').read_bytes()==model
    model_check=probe('model_entry',sample.replace(MODEL,model.decode('ascii')))
    model_check.update({'model_sha256':hashlib.sha256(model).hexdigest(),
                        'first_bytes_are_subckt':True,'only_leading_comments_removed':True,
                        'all_three_model_copies_byte_identical':True})
    legacy=probe('legacy_expected_failure',sample[2:],expected_failure=True)
    results=[]
    for name in CASES:
        src=(ROOT/'circuits'/f'{name}.cir').read_text()
        assert src.startswith('* G problem ')
        results.append(probe(name,src))
    evidence={'scope':'Title parsed as ordinary netlist content + 20ns startup, ngspice PSpice mode only',
              **legacy,'corrected_file_count':len(results),'full_transient_rerun':False,
              'native_multisim_retest':False,'model_entry_check':model_check,'results':results}
    (ROOT/'results/data/import_header_checks.json').write_text(json.dumps(evidence,indent=2))
    print('Reproduced legacy import-context failure; all 9 corrected files passed 20ns parse/startup checks.')

if __name__=='__main__':main()
