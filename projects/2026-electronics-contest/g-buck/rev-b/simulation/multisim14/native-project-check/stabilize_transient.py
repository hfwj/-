"""Build a reversible analysis-options-only revision after native startup failure.

Native Multisim behavior must be checked by the user. This script does not
replace MOSFETs, modify their capacitance models, or alter the driver revision.
"""
from pathlib import Path
import hashlib,json,re,struct
import dclimplode
from ms14_project import ROOT,PROJECT,DEST,MAGIC,unpack,pack,parse,inspect,block

STABLE=PROJECT/'downloads/设计1_瞬态容差调整_5ms_待本机验证.ms14'


def analysis_options(xml):
    root=parse(xml)
    state=next(root.iter('CIITDiagram')).get('SimState')
    tran=block(state,'TRAN');options=block(tran,'ASYS_OPT')
    result={}
    for key,kind in [('reltol','double'),('abstol','double'),('vntol','double'),('chgtol','double'),('method','string'),('itl4','long')]:
        match=re.search(rf'\d+:list\{{IsEnabled:long\{{(\d+)\}}\s+{key}:{kind}\{{([^}}]+)\}}\s*\}}',options)
        assert match,key
        result[key]={'enabled':match[1]=='1','value':match[2]}
    return result


def verify_independent_decoder(data,expected):
    pos=len(MAGIC)+8;decoded=[]
    while pos<len(data):
        length,size=struct.unpack_from('<II',data,pos)
        decoder=dclimplode.decompressobj_pklib()
        value=decoder.decompress(data[pos+8:pos+8+size])
        for _ in range(10):
            if decoder.eof:break
            value+=decoder.decompress(b'')
        assert decoder.eof and len(value)==length
        decoded.append(value);pos+=8+size
    assert b''.join(decoded)==expected


def main():
    raw=DEST.read_bytes();xml,_=unpack(raw);text=xml.decode('ascii')
    tran=block(text,'TRAN');options=block(tran,'ASYS_OPT');revised_options=options
    changes=[]
    for key,kind,old,new in [('reltol','double','0.001','0.01'),('abstol','double','1e-012','1e-008'),
                             ('vntol','double','1e-006','0.0001'),('chgtol','double','1e-014','1e-013')]:
        pattern=rf'(\d+:list\{{IsEnabled:long\{{)0(\}}\s+{key}:{kind}\{{){re.escape(old)}(\}}\s*\}})'
        revised_options,n=re.subn(pattern,rf'\g<1>1\g<2>{new}\g<3>',revised_options)
        assert n==1,(key,n)
        changes.append({'key':key,'before':old,'after':new,'enabled_before':False,'enabled_after':True})
    revised_tran=tran.replace(options,revised_options,1)
    revised=text.replace(tran,revised_tran,1).encode('ascii')
    # Exact inverse proves that no other XML bytes were edited.
    assert revised.decode('ascii').replace(revised_tran,tran,1).encode('ascii')==xml
    assert inspect(parse(revised))==inspect(parse(xml))
    expected=analysis_options(revised)
    assert expected['method']=={'enabled':False,'value':'trapezoidal'}
    assert expected['reltol']=={'enabled':True,'value':'0.01'}
    assert expected['itl4']=={'enabled':True,'value':'100'}
    data=pack(revised);assert unpack(data)[0]==revised
    verify_independent_decoder(data,revised)
    STABLE.write_bytes(data)
    result={
        'date':'2026-10-24','source_project':DEST.name,'output_project':STABLE.name,
        'source_sha256':hashlib.sha256(raw).hexdigest(),
        'output_sha256':hashlib.sha256(data).hexdigest(),'changes':changes,
        'active_transient_options':expected,'hardware_models_sources_and_time_settings_unchanged':True,
        'exact_inverse_xml_verified':True,'both_independent_decompressors_verified':True,
        'native_multisim_open_and_run_verified':False,
        'scope':'Functional transient troubleshooting with relaxed relative tolerance; not precision validation',
    }
    (ROOT/'results/data/startup_revision_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
