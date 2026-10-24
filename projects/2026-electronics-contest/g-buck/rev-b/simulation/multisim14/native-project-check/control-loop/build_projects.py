"""Embed an explicitly ideal CV/average-current controller in the user's V3 template.

No native GUI execution. Feedback references bind to this saved schematic's
canonical nets: VOUT, 3 (capacitor side of RS_OUT), 7 (VIN), 2 (RS_L input).
Raw XML is minimally edited so embedded vendor models retain their newlines.
"""
from pathlib import Path
import sys,re,json,hashlib
from xml.sax.saxutils import escape
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ms14_project import PROJECT,unpack,pack,parse,components,elements,clean,inspect,block
from stabilize_transient import analysis_options,verify_independent_decoder
from verify_power_stage import power_stage_source

ROOT=Path(__file__).resolve().parent
SOURCE=PROJECT/'references/user-projects/2026-10-24_本机可运行_保险丝对照.ms14'
MODEL=ROOT/'GBUCK_CTRL_EQ.lib'
CASES=[
 {'id':'CV_25V_20R','vin':25,'load':'20','stop':'0.03'},
 {'id':'CC_25V_8R','vin':25,'load':'8','stop':'0.03'},
 {'id':'CC_25V_5R','vin':25,'load':'5','stop':'0.03'},
 {'id':'CV_15V_20R','vin':15,'load':'20','stop':'0.03'},
 {'id':'CV_25V_OPEN','vin':25,'load':'1e9','stop':'0.03'},
 {'id':'AUTO_20R_8R_5R','vin':25,'load':'steps','stop':'0.045'},
]
LOAD_TEMPLATE='GLOAD %t1 %t2 VALUE={V(%t1)*V(GLOAD_CTRL)}\nVLOAD_CTRL GLOAD_CTRL %t2 PWL(0 0.05 18m 0.05 18.1m 0.125 28m 0.125 28.1m 0.2 45m 0.2)'


def encoded(value):return escape(value,{'"':'&quot;'})


def component_span(text,local):
    start=text.index(f'<CiComponent Class="CiComponent" LocalName="&amp;ASC{local}"')
    end=text.index('</CiComponent>',start)+len('</CiComponent>')
    return start,end,text[start:end]


def replace_templates(body,new,kind):
    pattern=rf'((?:String|Value)=")&amp;ASC{kind}%p[^\"]*(")'
    # The active template and component database metadata each contain one copy.
    revised,n=re.subn(pattern,lambda m:m[1]+'&amp;ASC'+encoded(new)+m[2],body)
    assert n==2,(kind,n)
    return revised


def replace_component(text,local,change):
    a,b,body=component_span(text,local);new=change(body)
    return text[:a]+new+text[b:]


def set_parameter(body,index,value):
    a=body.index('<CiaParamList ');b=body.index('</CiaParamList>',a)+len('</CiaParamList>')
    before,section,after=body[:a],body[a:b],body[b:]
    for tag,prefix in [('doubles',''),('parameters','&amp;ASC')]:
        if '<'+tag+'/>' in section:continue
        start=section.index('<'+tag+'>');end=section.index('</'+tag+'>',start)
        region=section[start:end];items=list(re.finditer(r'(<Item Value=")([^\"]*)("/>)',region));m=items[index]
        region=region[:m.start(2)]+prefix+value+region[m.end(2):]
        section=section[:start]+region+section[end:]
    return before+section+after


def hide_cached_value(text,symbol_id):
    start=text.index(f'<Item ID="{symbol_id}" Class="CIITSymbolComp">')
    end=text.index('</CIITSymbolComp>',start)+len('</CIITSymbolComp>')
    body=text[start:end]
    body,n=re.subn(r'(<CIITSymTextCompValue\b[^>]*\bHidden=")0(")',r'\g<1>1\2',body)
    assert n==1
    return text[:start]+body+text[end:]


def output_path(case):return PROJECT/'downloads'/f'GBUCK_CTRL_EQ_{case["id"]}_native_check.ms14'


def extract_netlist(path):
    xml,_=unpack(path.read_bytes());root=parse(xml);by={x['display_ref']:x for x in components(root)}
    comp=next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))=='V3')
    template=clean(comp.find('.//CiaSpiceTmpltExprt').get('String'))
    lines=template.splitlines();instance=next(l for l in lines if l.startswith('XCTRL '))
    instance=instance.replace('%t1',by['V3']['ports']['1']).replace('%t2',by['V3']['ports']['2']).replace('VOUT',by['RL']['ports']['1'])
    assert instance=='XCTRL 1 0 4 3 7 2 GBUCK_CTRL_EQ'
    definition=template[template.index('.SUBCKT'):]
    assert definition==MODEL.read_text()
    source=power_stage_source(root)
    source,n=re.subn(r'(?m)^V3 .*$',instance,source);assert n==1
    load_comp=next(e for e in elements(root,'CiComponent').values() if clean(e.get('LocalName'))=='R4')
    load_tpl=clean(load_comp.find('.//CiaSpiceTmpltExprt').get('String'))
    if load_tpl.startswith('GLOAD '):
        load_text=load_tpl.replace('%t1','4').replace('%t2','0')
        source,n=re.subn(r'(?m)^RL .*$',lambda _:load_text,source,count=1);assert n==1
    stop=inspect(root)['transient_settings']['TSTOP']
    assert stop in ['0.03','0.045']
    source+=definition+'\n.options method=trap reltol=0.01 abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=100\n.tran 50n '+('30m' if stop=='0.03' else '45m')+' 0 50n\n'
    return source


def main():
    original=SOURCE.read_bytes();xml,_=unpack(original);original_root=parse(xml);original_info=inspect(original_root)
    assert all(original_info['connectivity_checks'].values())
    components_by={x['display_ref']:x for x in components(original_root)}
    assert components_by['F1']['ports']=={'2':None,'1':None}
    assert components_by['R1']['ports']=={'2':'5','1':'8'} and components_by['R1']['parameters'][1]=='0.001'
    symbols={clean(e.get('LocalName')):e.get('SymCompID') for e in elements(original_root,'CiComponent').values()}
    template='* SIMULATION-ONLY CVCC + SOFT START; not STM32 firmware\nXCTRL %t1 %t2 VOUT 3 7 2 GBUCK_CTRL_EQ\n'+MODEL.read_text()
    outputs=[]
    for case in CASES:
        text=xml.decode('ascii')
        text=replace_component(text,'V3',lambda b:replace_templates(b,template,'v'))
        text=hide_cached_value(text,symbols['V3'])
        if case['vin']!=25:text=replace_component(text,'V1',lambda b:set_parameter(b,1,str(case['vin'])))
        if case['load']=='steps':
            text=replace_component(text,'R4',lambda b:replace_templates(b,LOAD_TEMPLATE,'r'))
            text=hide_cached_value(text,symbols['R4'])
        elif case['load']!='20':text=replace_component(text,'R4',lambda b:set_parameter(b,1,case['load']))
        tran=block(text,'TRAN');new_tran=tran.replace('TSTOP:double{0.02}','TSTOP:double{'+case['stop']+'}',1)
        assert new_tran!=tran
        # Existing source already proved this UI choice: MSM_ASYS_OPT=0 is custom.
        assert 'MSM_ASYS_OPT:long{0}' in new_tran
        title=re.search(r'PLOT_TITLE:string\{[^}]*\}',new_tran)
        new_tran=new_tran[:title.start()]+'PLOT_TITLE:string{'+case['id']+' CVCC_EQ + SOFT_START}'+new_tran[title.end():]
        if case['id'].startswith(('CC','AUTO')):
            pattern=r'(NODE:list\{GROUP:long\{)0(\}\s*PLOTDEVICETYPE:long\{0\}\s*TYPE:long\{0\}\s*NAME:string\{@rrs_out\[i\]\})'
            new_tran,n=re.subn(pattern,r'\g<1>768\2',new_tran);assert n==1
        text=text.replace(tran,new_tran,1)
        candidate=text.encode('ascii');root=parse(candidate);info=inspect(root)
        actual={x['display_ref']:x for x in components(root)}
        assert float(actual['V1']['parameters'][1])==case['vin']
        if case['load']!='steps':assert float(actual['RL']['parameters'][1])==float(case['load'])
        assert info['connectivity_checks']==original_info['connectivity_checks']
        assert analysis_options(candidate)==analysis_options(xml)
        before={x['display_ref']:(x['ports'],x['parameters']) for x in components(original_root)}
        after={x['display_ref']:(x['ports'],x['parameters']) for x in components(root)}
        for ref in before:
            assert before[ref][0]==after[ref][0],ref
            if ref not in ['RL','V1']:assert before[ref]==after[ref],ref
        # Vendor submodels are preserved exactly.
        old_models={clean(e.get('LocalName')):clean(e.find('.//CiaCString').get('String')) for e in elements(original_root,'CiModel').values()}
        new_models={clean(e.get('LocalName')):clean(e.find('.//CiaCString').get('String')) for e in elements(root,'CiModel').values()}
        assert old_models==new_models
        packed=pack(candidate);verify_independent_decoder(packed,candidate)
        path=output_path(case);path.write_bytes(packed)
        source=extract_netlist(path)
        outputs.append({**case,'file':str(path.relative_to(PROJECT)),'project_sha256':hashlib.sha256(packed).hexdigest(),
                        'solver_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                        'hardware_connectivity_and_vendor_models_preserved':True,'custom_analysis_selection_preserved':True,
                        'both_DCL_decoders_verified':True,'native_multisim_execution_verified':False})
    result={'date':'2026-10-24','source_sha256':hashlib.sha256(original).hexdigest(),
            'controller_model_sha256':hashlib.sha256(MODEL.read_bytes()).hexdigest(),
            'source_preserved':SOURCE.read_bytes()==original,'cases':outputs,
            'fuse_status':'F1 remains disconnected, R1=1mOhm remains connected, as in working source; protection unverified',
            'control_scope':'Ideal sensing, CV + averaged inductor-current control and soft start; not firmware or sensor-chip validation'}
    (ROOT/'results/data/native_build_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
