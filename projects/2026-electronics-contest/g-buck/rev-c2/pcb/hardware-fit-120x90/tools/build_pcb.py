"""Append a Rev C.2 PCB review board to a copy of the native schematic.

Mechanical assumptions are explicit; this is not a manufacturing release.
All coordinates in configuration are mm; native EasyEDA PCB coordinates are mil.
"""
from pathlib import Path
import base64, collections, copy, csv, datetime, gzip, hashlib, json, math
import shutil, sqlite3, sys, uuid

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT.parents[1]
GBUCK = REV.parent
sys.path.insert(0, str(REV/'schematic/tools'))
from native_common import read_project, attrs, inventory, sha

SOURCE = next((REV/'schematic/native').glob('*.eprj2'))
DEST = ROOT/'native/GBUCK_RevC2_120x90_PCB_review.eprj2'
TITLE = 'G题同步Buck Rev C.2 原理图'
STAMP = int(datetime.datetime(2026,10,27,8,tzinfo=datetime.timezone.utc).timestamp()*1000)

def uid(label, full=False):
    s=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-revc2-pcb-hardware-fit:'+label).hex
    return s if full else s[:16]

def mil(v): return round(v/.0254,5)

def rectpoly(x,y,w,h):
    return [mil(x-w/2),mil(y-h/2),'L',mil(x-w/2),mil(y+h/2),
            mil(x+w/2),mil(y+h/2),mil(x+w/2),mil(y-h/2),mil(x-w/2),mil(y-h/2)]

def main():
    source_hash=sha(SOURCE)
    meta,original,ticket=read_project(SOURCE)
    docs=copy.deepcopy(original);meta=copy.deepcopy(meta)
    scheme,pages,parts,pins=inventory(meta,docs,TITLE)
    legacy=json.loads((GBUCK/'rev-b/pcb/github-rework-120x90/data/revb_design_inventory.json').read_text())
    specs=copy.deepcopy(legacy['specs'])
    changes=set();newdocs=set()
    def newdoc(label,kind,template=None):
        u=uid(label);assert u not in docs
        docs[u]=copy.deepcopy(docs[template]) if template else {}
        meta[u]=copy.deepcopy(meta[template]) if template else {'editVersion':'3.2.149.88089769','client':uid('client')}
        meta[u].update(uuid=u,docType=kind,updateTime=STAMP,version=str(STAMP))
        changes.add(u);newdocs.add(u);return u
    def attr(doc,parent,key,value):
        for (kind,i),b in docs[doc].items():
            if kind=='ATTR' and b.get('parentId')==parent and b.get('key')==key:
                b['value']=value;changes.add(doc);return
        # Some Rev C additions have no Channel ID/Supplier Footprint attributes.
        docs[doc]['ATTR',uid(doc+parent+key)]={'parentId':parent,'key':key,'value':value,
            'x':None,'y':None,'keyVisible':False,'valueVisible':False,'rotation':0,'zIndex':1}
        changes.add(doc)
    def twopad(p,w,h,hole,body,tbd=True):
        return {'pads':[{'num':str(i+1),'x':x,'y':0,'w':w,'h':h,'hole':hole}
                        for i,x in enumerate([-p/2,p/2])],'body_mm':body,'tbd':tbd}
    specs['TERM_2.54_2P']=twopad(2.54,1.9,2.4,1.3,[5.48,6.3],False)
    specs['CP_D10_P5']=twopad(5,2.2,2.2,.9,[10.5,10.5],False)
    specs['L65125_VERTICAL_P10']=twopad(10,2.4,2.4,1.1,[20,10],False)
    specs['SHUNT_TH_P10_TBD']=twopad(10,2.6,2.6,1.1,[12,4],True)
    specs['RPRE_EXTERNAL_P5.08_TBD']=twopad(5.08,2.5,2.5,1.3,[9,5],True)
    # A measured clip is NOT a measured assembled fuse holder. 30 mm clip spacing
    # and axis of the 7.7 mm leg pitch are provisional, never fabrication evidence.
    specs['FUSE_6X30_4SLOT_TBD']={'pads':[
        {'num':str(end+1),'x':x,'y':y,'w':3.0,'h':2.4,'hole':1.0,'slot':1.8}
        for end,x in enumerate([-15,15]) for y in [-3.85,3.85]],
        'body_mm':[42,14],'tbd':True}
    packages={}
    with (REV/'schematic/BOM_RevC2.csv').open(encoding='utf-8-sig') as f:
        bom={r['位号']:r for r in csv.DictReader(f)}
    for ref in parts: packages[ref]=bom[ref]['封装/待确认']
    for ref in ['J1','J2','J_BYP','J_MON']:packages[ref]='TERM_2.54_2P'
    for ref in ['C1','C3']:packages[ref]='CP_D10_P5'
    for ref in ['C2','C4','C6']:packages[ref]='C0805'
    for ref in ['RS_IN','RS_OUT','RS_L']:packages[ref]='SHUNT_TH_P10_TBD'
    packages.update(L1='L65125_VERTICAL_P10',F1='FUSE_6X30_4SLOT_TBD',R_PRE='RPRE_EXTERNAL_P5.08_TBD')
    # 0.25 W snubber resistor should not use an unqualified generic 0805.
    packages['R_SN']='R1206'
    package_ids={}
    fpbase=parts['C1']['attrs']['Footprint']
    padbase=next(copy.deepcopy(b) for (k,i),b in docs[fpbase].items() if k=='PAD')
    polybase=next(copy.deepcopy(b) for (k,i),b in docs[fpbase].items() if k=='POLY')
    for name in sorted(set(packages.values())):
        if name not in specs:raise KeyError(name)
        spec=specs[name]
        fp=newdoc('footprint:'+name,'FOOTPRINT',fpbase);package_ids[name]=fp
        docs[fp]={k:v for k,v in docs[fp].items() if k[0] not in ['PAD','POLY','STRING']}
        docs[fp]['META','META']={'title':name,'source':''}
        for n,p in enumerate(spec['pads']):
            b=copy.deepcopy(padbase);b.update(num=p['num'],centerX=mil(p['x']),centerY=mil(p['y']),
                layerId=12 if p['hole'] else 1,topPasteExpansion=0 if not p['hole'] else None,
                bottomPasteExpansion=0 if not p['hole'] else None)
            b['defaultPad']={'padType':'RECT' if p['num']=='1' or not p['hole'] else 'ELLIPSE',
                             'width':mil(p['w']),'height':mil(p['h'])}
            b['hole']=({'holeType':'SLOT' if p.get('slot') else 'ROUND',
                        'width':mil(p.get('slot',p['hole'])),'height':mil(p['hole'])} if p['hole'] else None)
            docs[fp]['PAD','p'+str(n+1)]=b
        w,h=spec['body_mm']
        for layer,extra in [(3,0),(48,0),(47,.5)]:
            b=copy.deepcopy(polybase);b.update(layerId=layer,path=rectpoly(0,0,w+extra,h+extra),width=mil(.12 if layer==3 else .05))
            docs[fp]['POLY','body'+str(layer)]=b
    notes={
        'J1':'2.54mm 2P；5.48×6.3×8.8mm；孔径1.3mm来自图；供应商标称6A/150V',
        'J2':'2.54mm 2P；进线朝板外；1=VOUT，2=GND',
        'J_BYP':'2.54mm 2P；外接常开旁路开关；开关额定≥30VDC/3A另核',
        'J_MON':'2.54mm 2P；1=ADC_VIN_POST→PA6，2=GND；PA5保留LCD SCK',
        'F1':'改用6×30mm管夹；仍需2A保险管；双夹中心距与7.7mm脚距轴向待量；当前4槽为占位，禁止制板',
        'L1':'65125 220μH±10%；DCR≤55mΩ；卖家6A Max≠Isat；立式20×10投影、P10、线径0.75；孔1.1为设计值',
        'C1':'470μF/50V；实物D10×H18、P5、脚径0.6；按Dmax10.5留空间；ESR/纹波及完整型号待核',
        'C3':'470μF/35V；实物D10×H13、P5、脚径0.6；按Dmax10.5留空间；耐压及完整型号待核',
        'C2':'1μF/50V X7R，0805；有效容量按实际料号的直流偏压曲线核对',
        'C4':'10μF/50V X7R，0805；由35V提高至实购50V；直流偏压后有效容量待核',
        'C6':'10μF/25V，按实购2×1.25贴片改0805；完整料号/偏压待核',
        'C_A3':'资料未填写，暂保留C1206；不能从C6推定本件也为0805',
        'R_PRE':'外置22Ω/5W脉冲≥0.3J电阻，板上仅两引出焊盘；不得将电阻实体塞进引出焊盘投影',
        'U1':'Rev C.2指定IR2184PbF/DIP8；已购表IR2104不可直接代装；1IN 2SD# 3COM 4LO 5VCC 6VS 7HO 8VB',
        'R_SN':'DNP；10Ω≥0.25W，改1206以匹配功率要求；实购功率仍需核对',
    }
    for ref in ['RS_IN','RS_OUT','RS_L']:
        notes[ref]='已购类型改直插占位；P10仅假设，图片尚未确认本件脚距；高度12、线径0.8来自参数表；功率≥1W；Kelvin取样；RS_L25mΩ尚未购齐'
    for ref in ['QH','QL']:notes[ref]='直立TO220，1G2D3S；金属背板=D；按无散热片实购，热设计待验证'
    for ref,p in parts.items():
        olddev=p['attrs']['Device'];dev=newdoc('device:'+ref,'DEVICE',olddev)
        dm=docs[dev]['META','META'];dm['attributes'].update(Footprint=package_ids[packages[ref]],**{'Supplier Footprint':packages[ref]})
        if ref in notes:dm['attributes']['Description']=notes[ref]
        for k,v in [('Device',dev),('Footprint',package_ids[packages[ref]])]:attr(p['page'],p['id'],k,v)
        if ref in notes:attr(p['page'],p['id'],'Description',notes[ref])
        if ref in ['F1','C4']:
            value={'F1':'2A / 6x30','C4':'10uF / 50V X7R'}[ref]
            for key in ['Value','Name']:attr(p['page'],p['id'],key,value)
            dm['attributes']['Value']=value;dm['title']=ref+' '+value
        p['attrs']['Device']=dev;p['attrs']['Footprint']=package_ids[packages[ref]]
    pcb=newdoc('pcb','PCB',legacy['pcb'])
    keep=['META','PRIMITIVE','CANVAS','LAYER','LAYER_PHYS','ACTIVE_LAYER','RULE_TEMPLATE','RULE','SILK_OPTS','PREFERENCE','PANELIZE']
    docs[pcb]={k:v for k,v in docs[pcb].items() if k[0] in keep}
    o=docs[pcb];board=docs[scheme]['META','META']['board']
    o['META','META']={'title':'Rev C2 120x90 — 封装布局复核 / 待完成布线','source':'','board':board,'parent':'','zIndex':0}
    docs[board]['META','META']['title']='G题 Rev C.2 — PCB封装与布局修订';changes.add(board)
    poly=copy.deepcopy(polybase);poly.update(partitionId='',layerId=11,path=rectpoly(60,45,120,90),width=mil(.1),locked=True,polyType='BOARD_OUTLINE')
    o['POLY',uid('outline')]=poly
    for net in sorted({p['net'] for p in pins}):
        o['NET',json.dumps(['NET',net],ensure_ascii=False,separators=(',',':'))]={
            'netType':None,'specialColor':None,'retLine':True,'differentialName':None,'isPositiveNet':False,'equalLengthGroupName':None}
    # Fixed high-energy parts and I/O. Coordinates are deliberately sparse near
    # the measured inductor, fuse clips, wiring entrances and the gate driver.
    positions={
      'J1':(5,66,90),'F1':(29,80,0),'J_BYP':(7,56,90),'R_PRE':(19,58,0),
      'D1':(40,63,180),'RS_IN':(47.5,70,0),'C1':(60,76,0),'C2':(66,69,0),
      'QH':(73,73,0),'QL':(73,64,0),'L1':(90,77,0),'D_FREE':(81,60,90),
      'RS_L':(108,77,270),'C3':(108,64.7,0),'C4':(100,63,0),'RS_OUT':(108,52,270),
      'J2':(115.8,51,90),'R_BL':(112,43,90),'U1':(61,62,0),
      'U2':(47.5,64.8,0),'U4':(103,86.5,0),'U3':(102,54,0),
      'J_AUX12':(7,43,90),'J_AUX5':(7,28,90),'J_CTL':(113,21,0),'J_MON':(101,9,0),
      'U5':(53,35,0),'U9':(72,35,0),'U6':(30,20,0),'U7':(45,20,0),'U8':(60,20,0),
    }
    targets={
      'RG_H':(69,70),'RG_L':(69,64),'R_GSH':(73,69),'R_GSL':(73,60),
      'C_BOOT':(66,64),'D_BOOT':(61,53),'C5':(65,57),'C_DRV':(64,55),'C6':(69,54),
      'R_PWM':(54,61),'R_IN_PD':(53,65),'R_SD_PD':(53,62),
      'C_U2':(52,64.8),'C_U4':(109,86.5),'C_U3':(102,57),
      'C_U5':(57,35),'C_U9':(76,35),'C_U6':(34,23),'C_U7':(49,23),'C_U8':(64,23),
      'R_SN':(81,64),'C_SN':(84,64),'R_IL_PROT':(92,46),'C_IL_PROT':(88,44),
      'R_IOUT_PROT':(91,39),'C_IOUT_PROT':(87,37),'R_IOUT_TOP':(77,41),'R_IOUT_BOT':(80,39),
      'C_REF_IOUT':(80,35),'R_IOUT_PU':(79,32),'R_VINP_TOP':(87,18),'R_VINP_BOT':(91,18),
      'R_VINP_ADC':(94,14),'C_VINP_ADC':(97,11),'D_ADC6':(95,8),
      'R_VDDA':(101,25),'C_A1':(98,25),'C_A2':(95,25),'C_A3':(92,25),
      'R1':(87,29),'R2':(90,29),'R3':(94,28),'C7':(98,28),'D_ADC1':(103,29),
      'R4':(87,23),'R5':(90,23),'R6':(94,23),'C8':(98,22),'D_ADC3':(103,23),
      'R7':(94,34),'C9':(98,34),'D_ADC2':(103,35),
      'R8':(94,39),'C10':(98,39),'D_ADC4':(103,40),
      'R_IL_ADC':(88,32),'C_IL_ADC':(91,32),'D_ADC5':(91,35),
      'R9':(47,41),'R10A':(49,42),'R10B':(51,42),'R16':(58,42),'R15A':(60,42),
      'R15B':(62,42),'R11':(67,41),'R12':(69,41),'R13':(34,32),
      'C_REF_POS':(50,39),'C_REF_NEG':(60,39),'C_REF_OV':(67,38),
      'R14':(61,29),'C11':(65,27),'D_POR':(58,28),'R_EN_PD':(41,29),'R_ARM_PD':(27,28),
    }
    for ref,(x,y) in {'TP1':(10,68),'TP2':(57,83),'TP3':(83,71),'TP4':(115,42),'TP5':(109,37),
      'TP6':(77,70),'TP7':(77,66),'TP8':(88,49),'TP9':(36,28),'TP10':(103,19),
      'TP11':(109,39),'TP12':(85,43),'TP13':(80,31),'TP14':(101,13)}.items():targets[ref]=(x,y)
    # Mechanical keepouts around four proposed 3.2 mm mounting holes.
    mounting=[(3.5,3.5),(116.5,3.5),(3.5,86.5),(116.5,86.5)]
    occupied=[]
    def envelope(ref,x,y,angle):
        s=specs[packages[ref]];w,h=s['body_mm']
        xs=[-w/2,w/2]+[p['x']+k*p['w']/2 for p in s['pads'] for k in [-1,1]]
        ys=[-h/2,h/2]+[p['y']+k*p['h']/2 for p in s['pads'] for k in [-1,1]]
        w=max(xs)-min(xs);h=max(ys)-min(ys)
        if angle%180:w,h=h,w
        return (x-w/2-.3,y-h/2-.3,x+w/2+.3,y+h/2+.3)
    def fits(b):
        if b[0]<.6 or b[1]<.6 or b[2]>119.4 or b[3]>89.4:return False
        if any(not (b[2]<=c[0] or c[2]<=b[0] or b[3]<=c[1] or c[3]<=b[1]) for _,c in occupied):return False
        for x,y in mounting:
            nx=max(b[0],min(x,b[2]));ny=max(b[1],min(y,b[3]))
            if (nx-x)**2+(ny-y)**2<3.1**2:return False
        return True
    for ref,pos in list(positions.items()):
        b=envelope(ref,*pos)
        if not fits(b):raise ValueError(('fixed component collision',ref,pos,[r for r,c in occupied if not (b[2]<=c[0] or c[2]<=b[0] or b[3]<=c[1] or c[3]<=b[1])]))
        occupied.append((ref,b))
    # Closest legal placement to explicit functional targets, allowing quarter-turns.
    for ref in sorted(set(parts)-set(positions),key=lambda r:(r.startswith('TP'),r not in targets,r)):
        tx,ty=targets.get(ref,(39,42))
        candidates=[]
        for dx in range(-24,25):
            for dy in range(-24,25):
                x=tx+dx*.5;y=ty+dy*.5
                for angle in [0,90,180,270]:
                    candidates.append((dx*dx+dy*dy+(angle%180)*.001,x,y,angle))
        candidates.sort()
        for _,x,y,angle in candidates:
            b=envelope(ref,x,y,angle)
            if fits(b):break
        else:raise ValueError(('no legal placement',ref))
        positions[ref]=(x,y,angle);occupied.append((ref,b))
    sample_comp=next(copy.deepcopy(b) for (k,i),b in original[legacy['pcb']].items() if k=='COMPONENT')
    sample_attr=next(copy.deepcopy(b) for (k,i),b in original[legacy['pcb']].items() if k=='ATTR')
    manifest={}
    for ref,p in parts.items():
        cid=uid('pcbpart:'+ref);x,y,angle=positions[ref];fp=package_ids[packages[ref]]
        actual=attrs(docs[p['page']])[p['id']]
        c=copy.deepcopy(sample_comp);c.update(x=mil(x),y=mil(y),angle=angle,
            attrs={'Value':actual['Value'],'Unique ID':p['id'],'Channel ID':actual.get('Channel ID',''),'Reuse Block':'','Group ID':''})
        o['COMPONENT',cid]=c
        for key,value in [('Footprint',fp),('Device',p['attrs']['Device']),('Designator',ref)]:
            a=copy.deepcopy(sample_attr);a.update(parentId=cid,key=key,value=value,valueVisible=key=='Designator',
                x=mil(x) if key=='Designator' else None,y=mil(y+1.3) if key=='Designator' else None,fontSize=mil(.9),strokeWidth=mil(.12))
            o['ATTR',uid('pcbattr:'+ref+key)]=a
        nets={z['pin']:z['net'] for z in pins if z['ref']==ref}
        for (k,pid),pad in docs[fp].items():
            if k!='PAD':continue
            key=json.dumps(['PAD_NET',cid,pad['num'],pid],ensure_ascii=False,separators=(',',':'))
            o['PAD_NET',key]={'partitionId':'','padNet':nets[pad['num']],'padLen':None,'attrsMap':{}}
        manifest[ref]={'id':cid,'schematic_id':p['id'],'x':x,'y':y,'angle':angle,'package':packages[ref],
                       'value':actual['Value'],'notes':notes.get(ref,bom[ref].get('装配说明','')),'mechanical_TBD':specs[packages[ref]]['tbd']}
    # Individual NPTH holes: never net-connected; 6.2 mm mechanical clearance.
    for n,(x,y) in enumerate(mounting):
        p=copy.deepcopy(padbase);p.update(partitionId='',num='H'+str(n+1),centerX=mil(x),centerY=mil(y),layerId=12,plated=False)
        p['hole']={'holeType':'ROUND','width':mil(3.2),'height':mil(3.2)}
        p['defaultPad']={'padType':'ELLIPSE','width':mil(3.2),'height':mil(3.2)}
        p.update(topPasteExpansion=None,bottomPasteExpansion=None)
        o['PAD',uid('mount:'+str(n))]=p
    stringbase=next(copy.deepcopy(b) for (k,i),b in original[legacy['pcb']].items() if k=='STRING')
    for n,(text,x,y,size,layer) in enumerate([
      ('G BUCK REV C2 | 120x90 | PCB REVIEW - NOT FOR FAB',21,5,1,3),
      ('U1 = IR2184 ONLY',48,49,.9,3),('J_MON.1 -> PA6 / ADC6',83,5,.85,3),
      ('F1 6x30 / 2A - CLIP SPACING TBD',9,70,.8,13),
      ('M1 12V / M2 5V: EXTERNAL LM2596HV; IN+ GND OUT+ GND',11,12,.8,13),
      ('SHUNT PITCH TBD | NO FAB RELEASE | NO COPPER FILL',12,8,.8,13)]):
        b=copy.deepcopy(stringbase);b.update(text=text,x=mil(x),y=mil(y),fontSize=mil(size),strokeWidth=mil(.12),layerId=layer)
        o['STRING',uid('label:'+str(n))]=b
    # Board association in both project/config metadata and the structural cache.
    docs['CONFIG']['META','META']['defaultSheet']=pcb;changes.add('CONFIG')
    DEST.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE,DEST)
    con=sqlite3.connect(DEST)
    project,branch=con.execute('SELECT uuid,branch_uuid FROM projects').fetchone()
    parent=con.execute('SELECT history_uuid FROM branches WHERE uuid=?',(branch,)).fetchone()[0]
    chunks=[]
    for u in sorted(changes):
        meta[u].update(updateTime=STAMP,version=str(STAMP));ticket+=1
        chunks.append(json.dumps({'type':'DOCHEAD','ticket':ticket})+'||'+json.dumps(meta[u],ensure_ascii=False)+'|')
        for (kind,i),body in docs[u].items():
            ticket+=1;chunks.append(json.dumps({'type':kind,'id':i,'ticket':ticket})+'||'+json.dumps(body,ensure_ascii=False)+'|')
    history=uid('history',True);key=hashlib.sha256(('native-format-key:'+source_hash).encode()).digest()[:16]
    data=base64.b64encode(AESGCM(key).encrypt(bytes.fromhex(history),gzip.compress(('\n'.join(chunks)+'\n').encode(),mtime=0),None)).decode()
    con.execute('INSERT INTO project_history_'+branch+' (uuid,parent,key,num,snapshot_num) VALUES (?,?,?,0,0)',(history,parent,key.hex()))
    con.execute('INSERT INTO history_data (uuid,history_uuid,dataStr) VALUES (?,?,?)',(history,history,data))
    con.execute('UPDATE branches SET history_uuid=? WHERE uuid=?',(history,branch))
    con.execute('UPDATE projects SET name=?,ticket=?,g_ticket=?,default_sheet=? WHERE uuid=?',('G题 RevC2 PCB封装布局复核 / 未制板',ticket,ticket,pcb,project))
    structure=json.loads(con.execute('SELECT structure FROM project_structures WHERE branch_uuid=? ORDER BY id DESC LIMIT 1',(branch,)).fetchone()[0])
    structure['boards'][board].update(title=docs[board]['META','META']['title'])
    structure.setdefault('pcbs',{})[pcb]={'uuid':pcb,'title':o['META','META']['title'],'board':board,'parent_uuid':'','source':'','version':str(STAMP),'updateTime':STAMP,'zIndex':0}
    con.execute('INSERT INTO project_structures (ticket,project_uuid,branch_uuid,structure) VALUES (?,?,?,?)',(ticket,project,branch,json.dumps(structure,ensure_ascii=False)))
    con.commit();assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok';con.close()
    assert sha(SOURCE)==source_hash
    m2,d2,_=read_project(DEST)
    assert all(d2[u]==docs[u] for u in changes)
    assert all(d2[u]==d for u,d in original.items() if u not in changes)
    report={'source':str(SOURCE.relative_to(GBUCK.parent.parent.parent)), 'source_sha256':source_hash,
            'pcb':pcb,'scheme':scheme,'board':board,'parts':manifest,'specs':specs,
            'changed_source_documents':sorted(changes-newdocs),'new_documents':sorted(newdocs),
            'mounting_holes_mm':mounting,'board_mm':[120,90],'native_path':DEST.name,
            'manufacturing_release':False,'routing':'not_started'}
    (ROOT/'data/build_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    with (ROOT/'data/PCB_BOM_RevC2.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['位号','数值/型号','PCB封装','X_mm','Y_mm','旋转_deg','机械待确认','装配与核查说明'])
        for ref,p in manifest.items():w.writerow([ref,p['value'],p['package'],p['x'],p['y'],p['angle'],p['mechanical_TBD'],p['notes']])
    print(json.dumps({'native':str(DEST),'parts':len(parts),'pins':len(pins),'pcb':pcb,'routing':'not_started'},ensure_ascii=False))

if __name__=='__main__':
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    main()
