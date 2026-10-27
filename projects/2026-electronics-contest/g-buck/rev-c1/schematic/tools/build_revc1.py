"""Build a separate Rev C.1 native schematic, preserving the Rev C source file.

Uses the source's native encrypted-history format. Desktop opening/ERC/DRC
remain separate checks. No PCB or Multisim model is generated or modified.
"""
import base64
import copy
import csv
import datetime
import gzip
import hashlib
import json
import shutil
import sqlite3
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from native_common import ROOT, GBUCK, read_project, attrs, inventory, sha

SOURCE=next((GBUCK/'rev-c/schematic/native').glob('*.eprj2'))
DEST=ROOT/'schematic/native/G题同步Buck_RevC1_原理图修订.eprj2'
TITLE='G题同步Buck Rev C.1 原理图'
STAMP=int(datetime.datetime(2026,10,27,2,tzinfo=datetime.timezone.utc).timestamp()*1000)


def uid(label, full=False):
    value=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-revc1-20261027:'+label).hex
    return value if full else value[:16]


def main():
    source_hash=sha(SOURCE)
    meta,original,ticket=read_project(SOURCE)
    docs=copy.deepcopy(original);meta=copy.deepcopy(meta)
    scheme,pages,parts,pins=inventory(meta,docs,'G题同步Buck Rev C 原理图')
    changed=set();newdocs=set()

    def put(doc,kind,id,body):
        docs[doc][kind,id]=body;changed.add(doc)

    def attribute(doc,parent,key,value):
        for (kind,id),b in docs[doc].items():
            if kind=='ATTR' and b.get('parentId')==parent and b.get('key')==key:
                b['value']=value;changed.add(doc);return
        raise KeyError((doc,parent,key))

    def new_doc(label,kind,template=None):
        u=uid(label)
        assert u not in docs
        docs[u]=copy.deepcopy(docs[template]) if template else {}
        meta[u]=copy.deepcopy(meta[template]) if template else {
            'docType':kind,'editVersion':'3.2.149.88089769','client':uid('client')}
        meta[u].update(uuid=u,docType=kind,updateTime=STAMP,version=str(STAMP))
        changed.add(u);newdocs.add(u);return u

    def text(page,label,value,x=20,y=100,size=10):
        put(page,'TEXT',uid('text:'+label),{'x':x,'y':y,'rotation':0,'color':None,
            'fontFamily':None,'fontSize':size,'fontWeight':False,'italic':False,
            'underline':False,'align':'LEFT_BOTTOM','value':value,'fillColor':None,'zIndex':1})

    # Separate file, same Rev C sheet identities; legacy Rev B/reference docs remain intact.
    docs[scheme]['META','META']['title']=TITLE;changed.add(scheme)
    board=docs[scheme]['META','META']['board']
    docs[board]['META','META']['title']='G题 Rev C.1 — 监测与标注修订，未建PCB';changed.add(board)
    for page in pages:
        for (kind,id),b in docs[page].items():
            if kind=='TEXT' and 'Rev C' in b.get('value',''):
                b['value']=b['value'].replace('Rev C','Rev C.1');changed.add(page)

    # Clone shared library symbols; do not alter Rev B or other reference designs.
    for family,refs in [('mos',['QH','QL']),('ctl',['J_CTL'])]:
        old=parts[refs[0]]['attrs']['Symbol'];new=new_doc('symbol:'+family,'SYMBOL',old)
        sa=attrs(docs[new])
        if family=='mos':
            docs[new]['META','META']['title']='IRF540N_REVC1_VISIBLE_GDS'
            for (kind,id),b in docs[new].items():
                if kind=='ATTR' and b.get('key') in ('Pin Name','Pin Number'):
                    b['valueVisible']=True
        else:
            docs[new]['META','META']['title']='CTL_2X8_REVC1_PB11'
            p6=next(id for (kind,id),b in docs[new].items()
                    if kind=='PIN' and sa[id].get('Pin Number')=='6')
            attribute(new,p6,'Pin Name','PB11/OC#')
        for ref in refs:
            p=parts[ref]
            attribute(p['page'],p['id'],'Symbol',new)
            device=p['attrs']['Device']
            docs[device]['META','META']['attributes']['Symbol']=new;changed.add(device)

    cap=parts['C_IOUT_PROT'];capvalue='100nF / 25V X7R'
    for key in ('Value','Name'):
        attribute(cap['page'],cap['id'],key,capvalue)
    capdev=docs[cap['attrs']['Device']]['META','META']
    capdev['title']='C_IOUT_PROT '+capvalue
    capdev['attributes'].update(Value=capvalue,Description='1kΩ+100nF，τ=100us；不替代软件持续判据')
    changed.add(cap['attrs']['Device'])

    text(parts['QH']['page'],'mos-map',
         'Rev C.1：QH 1G=G_H / 2D=VIN / 3S=SW；QL 1G=G_L / 2D=SW / 3S=GND；不得交换D/S。')
    text(parts['J_CTL']['page'],'ctl-map',
         'Rev C.1：J_CTL.6=PB11/IOUT_OC_N，已修正旧GND脚名；新增J_MON.1接PA5(ADC)，J_MON.2接GND。')
    text(cap['page'],'alert-rc',
         'Rev C.1：C_IOUT_PROT=100nF/25V X7R，τ=100us；U9B仍为独立告警，不接FAULT_N。')

    page=new_doc('page:vin-monitor','SCH_PAGE')
    put(page,'META','META',{'title':'09 预充后VIN监测与固件约束','source':'','schematic':scheme,'zIndex':9})
    text(page,'monitor-title','09 预充后VIN监测与固件约束',20,30,19)
    text(page,'monitor-status','Rev C.1 / 新增采样支路与控制板接线 / 未运行客户端ERC、DRC',20,53)
    text(page,'monitor-purpose','VIN为D1与RS_IN之后；原ADC_VIN继续测VIN_EXT。新增ADC_VIN_POST经J_MON接PA5。',20,76)
    specs=[
        ('R_VINP_TOP','R1','100kΩ / 0.1%',{'1':'VIN','2':'VIN_POST_DIV'},'R0805','预充后VIN分压上臂'),
        ('R_VINP_BOT','R2','10kΩ / 0.1%',{'1':'VIN_POST_DIV','2':'GND'},'R0805','预充后VIN分压下臂'),
        ('R_VINP_ADC','R3','1kΩ',{'1':'VIN_POST_DIV','2':'ADC_VIN_POST'},'R0805','ADC串联滤波/限流'),
        ('C_VINP_ADC','C7','4.7nF / C0G',{'1':'ADC_VIN_POST','2':'GND'},'C0805','含分压源阻抗的标称τ约47.4us'),
        ('D_ADC6','D_ADC5','BAT54S',{'1':'GND','2':'+3V3_A','3':'ADC_VIN_POST'},'SOT23_3','1=A1，2=K2，3=K1/A2；串联双二极管钳位'),
        ('J_MON','J1','2P VIN_POST ADC / PA5',{'1':'ADC_VIN_POST','2':'GND'},'TERM_5.08_2P','1接STM32 PA5/ADC，2接控制板GND；新增双线连接，端子机械待确认'),
        ('TP14','TP13','ADC_VIN_POST',{'1':'ADC_VIN_POST'},'TP_D1.5','新增ADC节点测试点'),
    ]
    for n,(ref,template,value,nets,package,note) in enumerate(specs):
        p=parts[template];cid=uid('component:'+ref);c=copy.deepcopy(p['body'])
        x=180+(n%4)*340;y=170+(n//4)*245
        dx=x-c['x'];dy=y-c['y'];c.update(x=x,y=y,zIndex=n+2)
        put(page,'COMPONENT',cid,c)
        dev=new_doc('device:'+ref,'DEVICE',p['attrs']['Device'])
        d=docs[dev]['META','META'];d['title']=ref+' '+value
        d['attributes'].update(Designator=ref+'?',Value=value,Description=note,
                               Name='={Value}',**{'Supplier Footprint':package,'Manufacturer Part':value})
        for (kind,id),b in docs[p['page']].items():
            if kind!='ATTR' or b.get('parentId')!=p['id']:continue
            b=copy.deepcopy(b);key=b['key'];b['parentId']=cid
            if b.get('x') is not None:b['x']+=dx
            if b.get('y') is not None:b['y']+=dy
            if key in ('Designator','Value','Name','Unique ID','Device','Description'):
                b['value']={'Designator':ref,'Value':value,'Name':value,'Unique ID':cid,
                            'Device':dev,'Description':note}[key]
            elif key=='Channel ID':b['value']='$C1_'+ref
            put(page,'ATTR',uid('attr:'+ref+':'+key),b)
        if ref=='J_MON':
            mons=new_doc('symbol:monitor-connector','SYMBOL',p['attrs']['Symbol'])
            ma=attrs(docs[mons])
            for (mk,mid),mb in docs[mons].items():
                if mk=='PIN':
                    num=ma[mid]['Pin Number']
                    attribute(mons,mid,'Pin Name','PA5/ADC' if num=='1' else 'GND')
            docs[mons]['META','META']['title']='VIN_POST_MONITOR_2P'
            attribute(page,cid,'Symbol',mons)
            d['attributes']['Symbol']=mons
        symbol=docs[p['attrs']['Symbol']];sa=attrs(symbol)
        for (kind,pid),pb in symbol.items():
            if kind!='PIN' or pb.get('partId')!=c['partId']:continue
            number=sa[pid]['Pin Number'];net=nets[number]
            sx=x+pb['x'];sy=y+pb['y'];endx=sx+(-35 if pb['x']<0 else 35)
            w=uid('wire:'+ref+':'+number)
            put(page,'WIRE',w,{'zIndex':1})
            put(page,'LINE',uid('line:'+ref+':'+number),{
                'fillColor':None,'fillStyle':None,'strokeColor':None,'strokeStyle':None,
                'strokeWidth':1,'startX':sx,'startY':sy,'endX':endx,'endY':sy,'lineGroup':w})
            put(page,'ATTR',uid('net:'+ref+':'+number),{
                'parentId':w,'key':'NET','value':net,'x':endx,'y':sy-3,'rotation':0,
                'color':None,'fontSize':9,'fontWeight':False,'italic':False,'underline':False,
                'fontFamily':None,'fillColor':None,'align':'RIGHT_BOTTOM' if pb['x']<0 else 'LEFT_BOTTOM',
                'keyVisible':False,'valueVisible':True,'locked':False,'zIndex':1})
    text(page,'monitor-scale','量程：VIN_POST=11×ADC_VIN_POST；25V对应2.273V。不得以无负载电压相近判断旁路已闭合。',20,720)
    text(page,'manual-precharge','启机：MCU_EN=0，预充≥100ms，核对下游VIN，人工闭合J_BYP，之后才ARM；J_BYP仍为手动。',20,750)
    text(page,'firmware-short','固件要求（未实现）：启动完成且目标输出有效时，对VOUT<0.5V持续约20ms等条件确认短路并关断。',20,780)
    text(page,'firmware-alert','PB11不得单边沿锁存；1.10A告警持续时间须结合负载跳变验证；不能只靠>1.1A检测1A恒流短路。',20,810)
    text(page,'firmware-rearm','故障解除后由用户重新ARM；不得自动反复重启。以上是固件接口约束，不是已烧录或已验收的功能。',20,840)

    # Append one native history node. Prior records and all reference designs survive unchanged.
    DEST.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE,DEST)
    con=sqlite3.connect(DEST)
    project,branch=con.execute('SELECT uuid,branch_uuid FROM projects').fetchone()
    parent=con.execute('SELECT history_uuid FROM branches WHERE uuid=?',(branch,)).fetchone()[0]
    chunks=[]
    for u in sorted(changed):
        meta[u].update(updateTime=STAMP,version=str(STAMP))
        ticket+=1
        chunks.append(json.dumps({'type':'DOCHEAD','ticket':ticket},ensure_ascii=False)+'||'+json.dumps(meta[u],ensure_ascii=False)+'|')
        for (kind,id),body in docs[u].items():
            ticket+=1
            chunks.append(json.dumps({'type':kind,'id':id,'ticket':ticket},ensure_ascii=False)+'||'+json.dumps(body,ensure_ascii=False)+'|')
    raw=('\n'.join(chunks)+'\n').encode()
    history=uid('history',True);key=hashlib.sha256(('native-format-key:'+source_hash).encode()).digest()[:16]
    data=base64.b64encode(AESGCM(key).encrypt(bytes.fromhex(history),gzip.compress(raw,mtime=0),None)).decode()
    con.execute('INSERT INTO project_history_'+branch+' (uuid,parent,key,num,snapshot_num) VALUES (?,?,?,0,0)',(history,parent,key.hex()))
    con.execute('INSERT INTO history_data (uuid,history_uuid,dataStr) VALUES (?,?,?)',(history,history,data))
    con.execute('UPDATE branches SET history_uuid=? WHERE uuid=?',(history,branch))
    con.execute('UPDATE projects SET name=?,ticket=?,g_ticket=?,default_sheet=? WHERE uuid=?',
                ('G题同步Buck RevC.1 原理图修订（PCB未同步）',ticket,ticket,parts['QH']['page'],project))
    # Refresh the structural cache from actual active history, retaining old structure entries.
    structure=json.loads(con.execute('SELECT structure FROM project_structures WHERE branch_uuid=? ORDER BY id DESC LIMIT 1',(branch,)).fetchone()[0])
    structure.setdefault('boards',{})[board]={'uuid':board,'title':docs[board]['META','META']['title'],'zIndex':0}
    structure.setdefault('schematics',{})[scheme]={'uuid':scheme,'name':TITLE,'board':board,'source':'','version':str(STAMP),'updateTime':STAMP}
    for u in [*pages,page]:
        m=docs[u]['META','META']
        structure.setdefault('sheets',{})[u]={'uuid':u,'title':m['title'],'schematic_uuid':scheme,
                                              'zIndex':m['zIndex'],'source':'','version':str(STAMP),'updateTime':STAMP}
    con.execute('INSERT INTO project_structures (ticket,project_uuid,branch_uuid,structure) VALUES (?,?,?,?)',
                (ticket,project,branch,json.dumps(structure,ensure_ascii=False)))
    con.commit();assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok';con.close()
    assert sha(SOURCE)==source_hash
    gotmeta,gotdocs,_=read_project(DEST)
    assert all(gotdocs[u]==docs[u] for u in changed),'History readback differs from requested records'
    assert all(gotdocs[u]==d for u,d in original.items() if u not in changed),'Unrelated source documents changed'

    # BOM preserves the old comparison and adds an explicit Rev C -> C.1 comparison.
    with (GBUCK/'rev-c/schematic/BOM_RevC.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames+['与RevC比较'];rows=list(reader)
    for row in rows:
        row['与RevC比较']='保留'
        if row['位号']=='C_IOUT_PROT':
            row['数值/型号']=capvalue;row['与RevC比较']='1nF/C0G→100nF/25V X7R，封装保持C0805'
            row['装配说明']='告警RC时间常数100us；不替代固件持续判据或输出硬限流'
        elif row['位号']=='J_CTL':
            row['与RevC比较']='pin6脚名GND→PB11/OC#，IOUT_OC_N网络不变'
        elif row['位号'] in ('QH','QL'):
            row['与RevC比较']='显示G/D/S与脚号，电气网络及封装不变'
    for ref,template,value,nets,package,note in specs:
        rows.append({'位号':ref,'数值/型号':value,'封装/待确认':package,
                     '与RevB比较':'RevC.1新增','装配说明':note,'与RevC比较':'新增'})
    with (ROOT/'schematic/BOM_RevC1.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    manifest={'source_sha256':source_hash,'output_sha256':sha(DEST),'date_beijing':'2026-10-27',
              'source_file':str(SOURCE.relative_to(GBUCK)),'output_file':str(DEST.relative_to(ROOT)),
              'changed_document_ids':sorted(changed),'added_document_ids':sorted(newdocs),
              'source_unchanged':True,'unrelated_design_documents_unchanged':True,
              'new_page_uuid':page,'new_parts':[s[0] for s in specs],
              'native_client_open_test':False,'native_erc_run':False,'pcb_drc_run':False,
              'multisim_updated':False,'firmware_implemented':False,'hardware_tested':False}
    out=ROOT/'results/data';out.mkdir(parents=True,exist_ok=True)
    (out/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ('source_unchanged','unrelated_design_documents_unchanged','new_parts','output_sha256')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
