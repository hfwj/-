"""Read and minimally patch the user's compressed Multisim 14 project.

Requires dclimplode (PKWARE DCL) and lxml. Does not launch Multisim.
The original XML spelling is retained when patching: some attributes contain
literal newlines, which a standard XML parse/serialize cycle would normalize.
"""
from pathlib import Path
import hashlib,json,re,struct
from lxml import etree as ET
import dclimplode

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
SOURCE=PROJECT/'references/user-projects/2026-10-24_设计1.ms14'
DEST=PROJECT/'downloads/设计1_IR2104模型修订_待本机验证.ms14'
PRECHARGE=PROJECT/'downloads/设计1_IR2104模型修订_1ms检查.ms14'
MAGIC=b'MSMCompressedElectronicsWorkbenchXML'


def unpack(data):
    assert data.startswith(MAGIC)
    expected=struct.unpack_from('<Q',data,len(MAGIC))[0]
    assert 0<expected<=20_000_000
    chunks=[];info=[];pos=len(MAGIC)+8
    while pos<len(data):
        n,c=struct.unpack_from('<II',data,pos)
        assert 0<n<=900000 and c>0 and pos+8+c<=len(data)
        decoder=dclimplode.decompressobj()
        out=decoder.decompress(data[pos+8:pos+8+c])
        assert decoder.eof and len(out)==n
        info.append({'offset':pos,'xml_bytes':n,'compressed_bytes':c})
        chunks.append(out);pos+=8+c
    xml=b''.join(chunks)
    assert pos==len(data) and len(xml)==expected
    return xml,info


def pack(xml):
    result=MAGIC+struct.pack('<Q',len(xml))
    for pos in range(0,len(xml),900000):
        block=xml[pos:pos+900000]
        encoder=dclimplode.compressobj(dclimplode.CMP_ASCII,4096)
        compressed=encoder.compress(block)+encoder.flush()
        result+=struct.pack('<II',len(block),len(compressed))+compressed
    assert unpack(result)[0]==xml
    return result


def parse(xml):
    text=xml.decode('ascii')
    # Preserve literal whitespace in attribute strings, including SPICE models.
    text=re.sub(r'"[^"<>]*"',lambda m:m.group().replace('\n','&#10;').replace('\r','&#13;').replace('\t','&#9;'),text)
    return ET.fromstring(text.encode('ascii'),parser=ET.XMLParser(resolve_entities=False,no_network=True))


def clean(value):
    return value.removeprefix('&ASC').removeprefix('&UNI').replace('_uc103bc','u')


def elements(root,tag):
    return {e.getparent().get('CiID'):e for e in root.iter(tag) if e.get('LocalName')}


def components(root):
    cs=elements(root,'CiComponent');ps=elements(root,'CiPort');ns=elements(root,'CiNode')
    names={}
    for item in root.iter('CIRToInfoMapItem'):
        ref=item.find('RefDesInfo')
        if ref is not None:
            number=ref.get('IRNumber');names[clean(item.get('CIRKey'))]=clean(ref.get('IRPrefix'))+('' if number=='-1' else number)
    rows=[]
    for cid,e in cs.items():
        local=clean(e.get('LocalName'))
        if local=='0':continue
        ports={clean(ps[p.get('CiID')].get('LocalName')):clean(ns[ps[p.get('CiID')].find('Nodes/Item').get('CiID')].get('LocalName')) for p in e.findall('Ports/Item')}
        params=[clean(x.get('Value')) for x in e.findall('./Attributes/Item/CiaParamList/parameters/Item')]
        rows.append({'internal_ref':local,'display_ref':names[local],'ports':ports,'parameters':params,'model_id':e.get('Model')})
    return rows


def driver_model(root):
    models=elements(root,'CiModel')
    for e in models.values():
        if clean(e.get('LocalName')).startswith('IR2104/'):
            return clean(e.find('.//CiaCString').get('String'))
    raise ValueError('No IR2104 model')


def patched_model(model):
    patches=[]
    for pin in ['IN','SD']:
        for suffix,old,new in [('R2','3.45Meg','5.62Meg'),('R3','46.55Meg','18.3Meg')]:
            pattern=rf'(R_MD1_Trig{pin}_{suffix}[^\n]*?){old}'
            model,n=re.subn(pattern,rf'\g<1>{new}',model)
            assert n==1,(pin,suffix,n)
            patches.append({'model_element':f'R_MD1_Trig{pin}_{suffix}','before':old,'after':new})
    return model,patches


def block(text,key):
    start=text.index(key+':list{');end=text.index('{',start);depth=0
    for pos in range(end,len(text)):
        if text[pos]=='{':depth+=1
        elif text[pos]=='}':
            depth-=1
            if depth==0:return text[start:pos+1]
    raise ValueError(key)


def inspect(root):
    rows=components(root);by={r['display_ref']:r for r in rows}
    # Pin connectivity is independent of node aliases used in Grapher.
    u=by['U1']['ports'];qh=by['Q1']['ports'];ql=by['Q2']['ports'];cb=by['C_BOOT']['ports']
    checks={
      'driver_12V_supply':u['VCC']==by['V2']['ports']['1'],
      'driver_common_ground':u['COM']=='0',
      'driver_enable_not_tied_to_12V':u['^SD']==by['V_EN']['ports']['1'] and u['^SD']!=u['VCC'],
      'pwm_series_and_pulldown':u['IN']==by['R_PWM']['ports']['2']==by['R_IN_PD']['ports']['1'],
      'switch_node':qh['S']==ql['D']==u['VS']==by['L1']['ports']['1'],
      'bootstrap_capacitor':set(cb.values())=={u['VB'],u['VS']},
      'bootstrap_diode':by['D_BOOT']['ports']=={'A':u['VCC'],'K':u['VB']},
      'high_gate_resistor':by['RG_H']['ports']=={'1':u['HO'],'2':qh['G']},
      'low_gate_resistor':by['RG_L']['ports']=={'1':u['LO'],'2':ql['G']},
      'high_gate_pulldown_to_source':by['R_GSH']['ports']=={'1':qh['G'],'2':u['VS']},
      'low_gate_pulldown_to_ground':by['R_GSL']['ports']=={'1':ql['G'],'2':'0'},
    }
    assert all(checks.values()),checks
    sim=next(root.iter('CIITDiagram')).get('SimState');tran=block(sim,'TRAN')
    analysis=block(tran,'ANALYSIS')
    settings={k:re.search(rf'{k}:(?:string|double)\{{([^}}]+)\}}',analysis).group(1) for k in ['TSTOP','TSTART','TMAX','IC']}
    selected=[m.group(2) for m in re.finditer(r'NODE:list\{GROUP:long\{(\d+)\}\s*PLOTDEVICETYPE:long\{\d+\}\s*TYPE:long\{\d+\}\s*NAME:string\{([^}]+)\}',tran) if int(m.group(1))&256]
    return {'component_count_excluding_grounds':len(rows),'components':rows,'connectivity_checks':checks,
            'transient_settings':settings,'selected_outputs':selected,
            'pwm_pulse_parameters':[by['V3']['parameters'][j] for j in [1,3,5,7,9,11,13]],
            'native_multisim_execution_verified':False}


def main():
    raw=SOURCE.read_bytes();xml,chunks=unpack(raw);root=parse(xml)
    result=inspect(root);result.update({'date':'2026-10-24','source_sha256':hashlib.sha256(raw).hexdigest(),'container_chunks':chunks})
    original=driver_model(root);new_model,changes=patched_model(original)
    text=xml.decode('ascii')
    # Two saved copies: component library metadata and active simulation model.
    for p in changes:
        pattern=rf'({p["model_element"]}[^\n]*?){p["before"]}'
        text,n=re.subn(pattern,rf'\g<1>{p["after"]}',text)
        assert n==2,(p,n)
    pattern=r'(<CiModel Class="CiModel" LocalName="&amp;ASCIR2104/IR__MOSFET_DRIVER__1" ChangedByUser=")0(")'
    text,n=re.subn(pattern,r'\g<1>1\2',text);assert n==1
    revised=text.encode('ascii');revised_root=parse(revised)
    assert inspect(revised_root)==inspect(root),'Hardware, sources, or settings changed unexpectedly'
    assert driver_model(revised_root)==new_model
    data=pack(revised);DEST.write_bytes(data)
    assert unpack(DEST.read_bytes())[0]==revised
    # A separate pre-PWM case localizes native opening, power and logic checks.
    needle='TSTOP:double{0.005}'
    tran=block(text,'TRAN');assert tran.count(needle)==1
    precharge=text.replace(tran,tran.replace(needle,'TSTOP:double{0.001}'),1).encode('ascii')
    precharge_data=pack(precharge);PRECHARGE.write_bytes(precharge_data)
    assert inspect(parse(precharge))['transient_settings']['TSTOP']=='0.001'
    # Recompression alone is also checked, without distributing an extra copy.
    assert unpack(pack(xml))[0]==xml
    result.update({'changes':changes,'changed_saved_model_copies':2,'corrected_sha256':hashlib.sha256(data).hexdigest(),
        'source_and_corrected_xml_roundtrip_verified':True,'hardware_and_sources_and_settings_unchanged':True,
        'model_is_user_modified_compatibility_model':True,'native_multisim_open_verified':False,
        'pre_pwm_check_sha256':hashlib.sha256(precharge_data).hexdigest(),
        'pre_pwm_check_TSTOP_s':0.001,'pre_pwm_check_does_not_apply_pwm':True,
        'note':'Approximate input hysteresis calibrated to accept this project 0/3.3V signals; not a manufacturer-certified model.'})
    out=ROOT/'results/data';out.mkdir(parents=True,exist_ok=True)
    (out/'project_inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for e in root.iter():
        if e.tag.startswith('PrjPreview'):
            preview=bytes.fromhex(e.get('Data'));assert preview.startswith(b'\x89PNG')
            target=ROOT/'results/figures';target.mkdir(parents=True,exist_ok=True)
            (target/'用户原工程内嵌预览_未修改.png').write_bytes(preview)
    print(json.dumps({k:v for k,v in result.items() if k!='components'},ensure_ascii=False,indent=2))
    print(DEST)


if __name__=='__main__':main()
