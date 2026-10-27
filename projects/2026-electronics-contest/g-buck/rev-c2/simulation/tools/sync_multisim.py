"""Synchronize native Multisim copies with Rev C.2 hardware and timing references.

Clones existing native components/ports/symbols/wire stubs with unique IDs.
All existing device model text except the explicitly identified MCU functional
equivalent is retained. Native Windows opening/running is a separate validation.
"""
from pathlib import Path
import collections,copy,csv,hashlib,json,math,re,sys,uuid
from lxml import etree as ET

ROOT=Path(__file__).resolve().parents[2];GBUCK=ROOT.parent
sys.path.insert(0,str(GBUCK/'rev-b/simulation/multisim14/native-project-check'))
from ms14_project import unpack,pack,parse,components,elements,clean,block
from stabilize_transient import verify_independent_decoder


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def model_text(root):
    return {clean(e.get('LocalName')):[clean(z.get('String','')) for z in e.findall('.//CiaCString')]
            for e in elements(root,'CiModel').values()}


def make(source):
    baseline=source.read_bytes();xml,_=unpack(baseline);root=parse(xml)
    before=components(root);by={r['display_ref']:r for r in before}
    cs=elements(root,'CiComponent');ps=elements(root,'CiPort');ns=elements(root,'CiNode')
    comp_by={ref:next(c for c in cs.values() if clean(c.get('LocalName'))==r['internal_ref']) for ref,r in by.items()}
    syms={e.getparent().get('ID'):e for e in root.iter('CIITSymbolComp')}
    objects=next(iter(syms.values())).getparent().getparent()
    obj_by={e.get('ID'):e for e in objects}
    diag=next(root.iter('CIITDiagram'));elems=diag.find('Elements');circuit=next(root.iter('CiCircuit'))
    circuit_id=circuit.getparent().get('CiID')
    counter=max(int(v) for e in root.iter() for k,v in e.attrib.items() if k in ('ID','CiID') and v.isdecimal())+1000
    def new_id():
        nonlocal counter
        counter+=8;return str(counter)
    def remap_tree(tree,mapping):
        for e in tree.iter():
            for k,v in list(e.attrib.items()):
                if v in mapping:e.set(k,mapping[v])
                elif k in ('InstanceID','Guid'):e.set(k,'{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'revc2:'+v+':'+str(counter))).upper()+'}')
    def translated(tree,dx,dy):
        for e in tree.iter():
            for k in ('CenterX','X','Transformer-M20'):
                if k in e.attrib:e.set(k,str(float(e.get(k))+dx))
            for k in ('CenterY','Y','Transformer-M21'):
                if k in e.attrib:e.set(k,str(float(e.get(k))+dy))
    def param(comp,value):
        pl=comp.find('.//CiaParamList')
        for group,prefix in [('parameters','&ASC'),('doubles','')]:
            items=pl.findall(group+'/Item')
            if len(items)>1:items[1].set('Value',prefix+value)
    # Bind semantic schematic nets to existing numeric Multisim nodes from all shared pins.
    with (ROOT/'results/data/RevC2_逐引脚接线表.csv').open(encoding='utf-8-sig',newline='') as f:native=list(csv.DictReader(f))
    nets={}
    for p in native:
        if p['ref'] in by and p['net']:
            num=by[p['ref']]['ports'][p['pin']]
            assert p['net'] not in nets or nets[p['net']]==num,(p,nets.get(p['net']),num)
            nets[p['net']]=num
    node_by_num={clean(n.get('LocalName')):n for n in ns.values()}
    node_text={}
    for wire in root.iter('CIITLinkComp'):
        node_text.setdefault(wire.get('Node'),wire.get('NodeText'))
    for name in ('VIN_POST_DIV','ADC_VIN_POST'):
        num=str(max(map(int,node_by_num))+1);nid=new_id();tid=new_id()
        original=next(iter(ns.values()))
        node=copy.deepcopy(original.getparent());node.set('CiID',nid)
        body=node[0];body.set('LocalName','&ASC'+num);body.find('Ports').clear()
        elems.append(node);ET.SubElement(circuit.find('Nodes'),'Item',CiID=nid)
        nt=copy.deepcopy(obj_by[next(iter(node_text.values()))]);nt.set('ID',tid)
        text=nt[0];text.set('Output','&ASC'+num);text.find('Links').clear()
        objects.append(nt);obj_by[tid]=nt;node_text[nid]=tid;node_by_num[num]=body;nets[name]=num
    # Existing cap value was 1n in active parameters even if one cached field said 100n.
    param(comp_by['C_IOUT_PROT'],'100n')
    for e in syms[comp_by['C_IOUT_PROT'].get('SymCompID')].iter('CIITSymTextCompValue'):
        e.set('Output','&ASC100nF / 25V X7R')
    new_specs=[('R_VINP_TOP','R1','100k','100k / 0.1%'),('R_VINP_BOT','R2','10k','10k / 0.1%'),
               ('R_VINP_ADC','R3','1k','1k'),('C_VINP_ADC','C7','4.7n','4.7nF / C0G'),
               ('D_ADC6','D_ADC5',None,'BAT54S'),('J_MON','J1',None,'VIN_POST ADC -> PA6'),
               ('TP14','TP13',None,'ADC_VIN_POST')]
    new_pin_spec={p['ref']:{q['pin']:q['net'] for q in native if q['ref']==p['ref']}
                  for p in native if p['ref'] not in by}
    mapping_table=root.find('.//CIRToInfoMap')
    ybase=max(float(s.get('Transformer-M21','0')) for s in syms.values())+450
    for index,(ref,template,value,label) in enumerate(new_specs):
        oldc=comp_by[template];oldcid=oldc.getparent().get('CiID')
        oldsymbol=syms[oldc.get('SymCompID')]
        graph=[copy.deepcopy(oldsymbol.getparent())]
        wire_infos=[]
        for pp in oldsymbol.iter('CIITPinSymbolComp'):
            port=ps[pp.get('PortID')];number=clean(port.get('LocalName'))
            connector=next(pp.iter('CIITPinConnectorComp'))
            near=connector.find('ConnectList/Item').get('ID')
            wires=[w for w in root.iter('CIITLinkComp') if near in (w.get('Connect1'),w.get('Connect2'))]
            assert len(wires)==1,(ref,number,len(wires))
            wire=wires[0];far=wire.get('Connect2') if wire.get('Connect1')==near else wire.get('Connect1')
            graph.extend(copy.deepcopy(obj_by[k]) for k in (near,far,wire.getparent().get('ID')))
            wire_infos.append((number,wire.getparent().get('ID'),far))
        component=copy.deepcopy(oldc.getparent())
        ports=[copy.deepcopy(ps[p.get('CiID')].getparent()) for p in oldc.findall('Ports/Item')]
        mapping={oldcid:new_id()}
        for tree in [*graph,component,*ports]:
            for e in tree.iter():
                for key in ('ID','CiID'):
                    if e.tag=='Item' and len(e) and e.get(key):mapping.setdefault(e.get(key),new_id())
        # CiPort and CiComponent definitions all get fresh IDs; refs inside symbols follow.
        for oldp,newp in zip(oldc.findall('Ports/Item'),ports):mapping.setdefault(oldp.get('CiID'),new_id())
        for tree in [*graph,component,*ports]:remap_tree(tree,mapping)
        comp=component[0];comp.set('LocalName','&ASC'+ref)
        if value:param(comp,value)
        x=220+(index%4)*520;y=ybase+(index//4)*320
        dx=x-float(oldsymbol.get('Transformer-M20'));dy=y-float(oldsymbol.get('Transformer-M21'))
        symbol=graph[0][0];symbol.set('Transformer-M20',str(x));symbol.set('Transformer-M21',str(y))
        for e in symbol.iter('CIITSymTextCompName'):e.set('Output','&ASC'+ref)
        for e in symbol.iter('CIITSymTextCompValue'):e.set('Output','&ASC'+label)
        if ref=='J_MON':
            for pin in symbol.iter('CIITPinSymbolComp'):
                pin.set('PinName','&ASCPA6/ADC' if clean(pin.get('PinNumber'))=='1' else '&ASCGND')
                for e in pin.iter('CIITPinSymTextCompName'):e.set('Output',pin.get('PinName'))
        # Translate only top-level graphics: nested symbol coordinates remain local.
        for tree in graph[1:]:translated(tree,dx,dy)
        elems.append(component);ET.SubElement(circuit.find('Components'),'Item',CiID=mapping[oldcid])
        port_by_num={clean(p[0].get('LocalName')):p for p in ports}
        for number,portitem in port_by_num.items():
            p=portitem[0];targetnum=nets[new_pin_spec[ref][number]]
            target=node_by_num[targetnum];targetid=target.getparent().get('CiID')
            p.find('Nodes').clear();ET.SubElement(p.find('Nodes'),'Item',CiID=targetid)
            ET.SubElement(target.find('Ports'),'Item',CiID=portitem.get('CiID'));elems.append(portitem)
        for number,oldwire,oldfar in wire_infos:
            wireitem=next(tree for tree in graph if tree.get('ID')==mapping[oldwire]);wire=wireitem[0]
            semantic=new_pin_spec[ref][number];target=node_by_num[nets[semantic]]
            nid=target.getparent().get('CiID');tid=node_text[nid]
            wire.set('Node',nid);wire.set('NodeText',tid)
            for e in wire.findall('.//ModifierInfo/Element/Item'):e.set('Value','&ASC'+semantic)
            ET.SubElement(obj_by[tid][0].find('Links'),'Item',ID=wireitem.get('ID'),Class='CIITLinkComp')
            far=next(tree[0] for tree in graph if tree.get('ID')==mapping[oldfar])
            lab=copy.deepcopy(next(e for e in objects if e.get('Class')=='CODTextComp'))
            lab.set('ID',new_id());tb=lab[0]
            tb.set('Output','&ASC'+semantic);tb.set('Font-Height','-10')
            tb.set('Transformer-M20',far.get('CenterX'));tb.set('Transformer-M21',str(float(far.get('CenterY'))-15))
            objects.append(lab)
        for tree in graph:objects.append(tree);obj_by[tree.get('ID')]=tree
        cir=copy.deepcopy(next(e for e in mapping_table if clean(e.get('CIRKey'))==by[template]['internal_ref']))
        cir.set('CIRKey','&ASC'+ref)
        ri=cir.find('RefDesInfo');ri.set('IRPrefix','&ASC'+ref);ri.set('IRNumber','-1')
        rd=ri.find('RefDesInfoData');rd.set('Prefix','&ASC'+ref);rd.set('Number','-1')
        oldstr=rd.get('RefDes');newstr=oldstr.replace(template,ref)
        rd.set('RefDes',newstr);rd.set('RefDesStrSize',str(int(rd.get('RefDesStrSize'))+len(newstr)-len(oldstr)))
        rd.set('RefDesBufSize',str(max(int(rd.get('RefDesBufSize')),len(newstr)+20)))
        mapping_table.append(cir)
    # Two explicitly independent 20ms functional timers; retain all other controller gains.
    lib=(ROOT/'simulation/multisim14/models/REVC2_PROTECT.lib').read_text()
    updated=0
    for e in root.iter():
        for attr in ('String','Value'):
            s=e.get(attr,'')
            if '.SUBCKT REVC_MCU_EQ PWM' not in s:continue
            old=re.search(r'(?ms)^\.SUBCKT REVC_MCU_EQ PWM.*?^\.ENDS REVC_MCU_EQ\s*',s).group()
            precharge_off='E_MCU MCU COM VALUE={0}' in old
            assert precharge_off==('PRECHARGE_ONLY' in source.name)
            new=old[:old.index('E_PWM ')]
            new+='E_PWM PWM COM VALUE={IF(TIME<4m,0,IF(V(DRVEN,COM)>2,LIMIT(1650*(V(DUTY,COM)-V(SAW,COM))+1.65,0,3.3),0))}\n'
            new+='E_READY READY COM VALUE={'+('0' if precharge_off else 'IF(TIME>50m,3.3,0)')+'}\n'
            new+='X_PROTECT OC VO REF READY FAULT ARM PERMIT COM REVC2_PROTECT\n'
            new+='E_MCU MCU COM VALUE={'+('0' if precharge_off else 'IF(TIME<3.2m,0,V(PERMIT,COM))')+'}\n'
            new+='V_ARM ARM COM PWL(0 0 3m 0 3.0001m 3.3 3.1m 3.3 3.1001m 0 100m 0)\n'
            new+='.ENDS REVC_MCU_EQ\n\n'+lib+'\n'
            e.set(attr,s.replace(old,new));updated+=1
    assert updated==2,updated
    title=source.stem.replace('REVC_','REVC2_')
    root.find('Project').set('Name','&ASC'+title)
    state=diag.get('SimState');state=state.replace('REVC_FULL','REVC2_FULL').replace('REVC_PRECHARGE','REVC2_PRECHARGE')
    # Make the new ADC variable available without adding a fifth main recording channel.
    tran=block(state,'TRAN');marker='NODES:list{'
    insert='NODE:list{GROUP:long{0}\nPLOTDEVICETYPE:long{0}\nTYPE:long{3}\nNAME:string{$adc_vin_post}\nDESCRIPTION:string{}\nINI_VALUE:double{0}\n}\n'
    assert marker in tran
    changedtran=tran.replace(marker,marker+insert,1);state=state.replace(tran,changedtran,1);diag.set('SimState',state)
    # Independent decoded readback verifies all 120 schematic references and 323 pins.
    encoded=ET.tostring(root,encoding='ascii',xml_declaration=False)
    assert parse(encoded).tag==root.tag
    data=pack(encoded);verify_independent_decoder(data,encoded)
    out=ROOT/'downloads'/f'{title}.ms14';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    read=parse(unpack(out.read_bytes())[0]);after={c['display_ref']:c for c in components(read)}
    assert len(after)==126,(len(after),len(before))
    for p in native:
        actual=after[p['ref']]['ports'][p['pin']]
        assert actual==(nets[p['net']] if p['net'] else None),(p,actual)
    for ref,old in by.items():
        assert after[ref]['ports']==old['ports'],ref
        if ref!='C_IOUT_PROT':assert after[ref]['parameters']==old['parameters'],ref
    assert after['C_IOUT_PROT']['parameters'][1]=='100n'
    oldmodels=model_text(parse(xml));newmodels=model_text(read)
    assert all(newmodels[k]==v for k,v in oldmodels.items() if k!='REVC_MCU_EQ_DEVICE')
    read_model='\n'.join(newmodels['REVC_MCU_EQ_DEVICE'])
    assert ('E_MCU MCU COM VALUE={0}' in read_model)==('PRECHARGE_ONLY' in source.name)
    assert ('E_READY READY COM VALUE={0}' in read_model)==('PRECHARGE_ONLY' in source.name)
    # Check GUI pins, circuit ports, wire/node lists and selected output preservation.
    read_cs=elements(read,'CiComponent');read_ps=elements(read,'CiPort');read_ns=elements(read,'CiNode')
    read_symbols={s.get('CiComponent'):s for s in read.iter('CIITSymbolComp')}
    refs_by_internal={r['internal_ref']:r['display_ref'] for r in after.values()}
    for cid,c in read_cs.items():
        if clean(c.get('LocalName')) not in refs_by_internal:continue
        ref=refs_by_internal[clean(c.get('LocalName'))]
        if ref not in {s[0] for s in new_specs}:continue
        portids={p.get('CiID') for p in c.findall('Ports/Item')}
        symbol=read_symbols[cid]
        assert {p.get('PortID') for p in symbol.iter('CIITPinSymbolComp')}==portids
        for pid in portids:
            p=read_ps[pid];assert p.get('Component')==cid
            nid=p.find('Nodes/Item').get('CiID')
            assert pid in {q.get('CiID') for q in read_ns[nid].findall('Ports/Item')}
    def selected(r):
        t=block(next(r.iter('CIITDiagram')).get('SimState'),'TRAN')
        return [n for group,n in re.findall(r'NODE:list\{GROUP:long\{(\d+)\}.*?NAME:string\{([^}]+)\}',t,re.S) if int(group)&256]
    assert selected(parse(xml))==selected(read)
    assert source.read_bytes()==baseline
    expected_nodes={v for v in nets.values()};assert len(expected_nodes)==51
    result={'file':str(out.relative_to(ROOT)),'sha256':digest(out),'source_sha256':digest(source),
        'hardware_refs':120,'total_parts_excluding_ground':126,'native_connected_pins':310,
        'all_schematic_pin_networks_match':True,'two_DCL_decoders_agree':True,
        'all_existing_ports_unchanged':True,'all_non_MCU_models_unchanged':True,
        'MCU_model_change':'Remove immediate OC pulse inhibit; independent OC/low-voltage 20ms timers, ARM reset reference',
        'new_ADC_target':'PA6/ADC12_IN6 (electrical node ADC_VIN_POST)',
        'main_selected_outputs_unchanged':True,'native_windows_open_or_run_test':False,
        'precharge_MCU_disabled_preserved':'PRECHARGE_ONLY' in source.name,
        'real_firmware_implemented':False}
    return result,nets


def main():
    results=[];nets=None
    # Keep the full-circuit baseline explicit; a separate hand-wired driver project
    # also lives in rev-c/downloads and must not receive this unrelated full-circuit patch.
    for name in ('GBUCK_REVC_FULL_25V_5R_100ms.ms14','GBUCK_REVC_FULL_SMOKE_10ms.ms14',
                 'GBUCK_REVC_PRECHARGE_ONLY_110ms.ms14'):
        source=GBUCK/'rev-c/downloads'/name
        result,nets=make(source);results.append(result)
    out=ROOT/'results/data';out.mkdir(exist_ok=True,parents=True)
    (out/'multisim_sync.json').write_text(json.dumps({'status':'PASS_NATIVE_STATIC_READBACK',
        'comparison_baseline':'Rev C .ms14 -> Rev C.2 schematic; Rev C.1 had no synchronized .ms14',
        'files':results,'semantic_to_numeric_nodes':nets},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
