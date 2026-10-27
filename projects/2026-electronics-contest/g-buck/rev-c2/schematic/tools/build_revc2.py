"""Correct the confirmed PA5/LCD conflict in a separate Rev C.2 native file."""
import base64,copy,csv,gzip,hashlib,json,shutil,sqlite3,uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from native_common import ROOT,GBUCK,read_project,inventory,attrs,sha

TITLE='G题同步Buck Rev C.2 原理图'
STAMP=1793070000000  # 2026-10-27 11:00 Beijing; newer than the Rev C.1 document version.


def uid(label,full=False):
    s=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-revc2:'+label).hex
    return s if full else s[:16]


def main():
    src=next((GBUCK/'rev-c1/schematic/native').glob('*.eprj2'))
    dest=ROOT/'schematic/native/G题同步Buck_RevC2_PA6修订.eprj2'
    m,old,ticket=read_project(src);docs=copy.deepcopy(old);m=copy.deepcopy(m)
    scheme,pages,parts,pins=inventory(m,docs,'G题同步Buck Rev C.1 原理图')
    changed=set()
    board=docs[scheme]['META','META']['board']
    docs[scheme]['META','META']['title']=TITLE;changed.add(scheme)
    docs[board]['META','META']['title']='G题 Rev C.2 — PA6监测接口修订，未建PCB';changed.add(board)
    for page in pages:
        for (kind,id),b in docs[page].items():
            if kind=='TEXT':
                value=b.get('value','')
                new=value.replace('Rev C.1','Rev C.2').replace('PA5','PA6')
                if new!=value:b['value']=new;changed.add(page)
    mon=parts['J_MON'];sym=mon['attrs']['Symbol'];device=mon['attrs']['Device']
    for u in (mon['page'],sym):
        for (kind,id),b in docs[u].items():
            if kind=='ATTR' and (u==sym or b.get('parentId')==mon['id']):
                value=b.get('value')
                if isinstance(value,str) and 'PA5' in value:
                    b['value']=value.replace('PA5','PA6');changed.add(u)
    b=docs[device]['META','META']
    b['title']=b['title'].replace('PA5','PA6')
    b['attributes']={k:v.replace('PA5','PA6') if isinstance(v,str) else v for k,v in b['attributes'].items()}
    changed.add(device)
    notes=[
        ('lcd-pins','LCD保留SPI1：SCK=PA5，MOSI=PA7，CS=PB12，DC=PB13，RST=PB14；PA6改作ADC12_IN6，禁用MISO。',76),
        ('independent-protection','固件：PB11持续低20ms判过流；短路用启动完成且目标有效下VOUT<0.5V持续20ms独立判据，不能与PB11低做AND。',870),
    ]
    for label,value,y in notes:
        page=parts['J_CTL']['page'] if label=='lcd-pins' else mon['page']
        docs[page]['TEXT',uid(label)]={'x':20,'y':y,'rotation':0,'color':None,'fillColor':None,
            'fontFamily':None,'fontSize':9,'fontWeight':False,'italic':False,'underline':False,
            'align':'LEFT_BOTTOM','value':value,'zIndex':1};changed.add(page)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    con=sqlite3.connect(dest);project,branch=con.execute('SELECT uuid,branch_uuid FROM projects').fetchone()
    parent=con.execute('SELECT history_uuid FROM branches WHERE uuid=?',(branch,)).fetchone()[0]
    lines=[]
    for u in sorted(changed):
        m[u].update(updateTime=STAMP,version=str(STAMP));ticket+=1
        lines.append(json.dumps({'type':'DOCHEAD','ticket':ticket})+'||'+json.dumps(m[u],ensure_ascii=False)+'|')
        for (kind,id),body in docs[u].items():
            ticket+=1
            lines.append(json.dumps({'type':kind,'id':id,'ticket':ticket})+'||'+json.dumps(body,ensure_ascii=False)+'|')
    h=uid('history',True);key=hashlib.sha256(('revc2-format:'+sha(src)).encode()).digest()[:16]
    data=base64.b64encode(AESGCM(key).encrypt(bytes.fromhex(h),gzip.compress(('\n'.join(lines)+'\n').encode(),mtime=0),None)).decode()
    con.execute('INSERT INTO project_history_'+branch+' (uuid,parent,key,num,snapshot_num) VALUES (?,?,?,0,0)',(h,parent,key.hex()))
    con.execute('INSERT INTO history_data (uuid,history_uuid,dataStr) VALUES (?,?,?)',(h,h,data))
    con.execute('UPDATE branches SET history_uuid=? WHERE uuid=?',(h,branch))
    con.execute('UPDATE projects SET name=?,ticket=?,g_ticket=? WHERE uuid=?',('G题同步Buck RevC.2 PA6修订（PCB未同步）',ticket,ticket,project))
    s=json.loads(con.execute('SELECT structure FROM project_structures WHERE branch_uuid=? ORDER BY id DESC LIMIT 1',(branch,)).fetchone()[0])
    s['boards'][board]['title']=docs[board]['META','META']['title']
    s['schematics'][scheme].update(name=TITLE,version=str(STAMP),updateTime=STAMP)
    for page in pages:s['sheets'][page].update(version=str(STAMP),updateTime=STAMP)
    con.execute('INSERT INTO project_structures (ticket,project_uuid,branch_uuid,structure) VALUES (?,?,?,?)',(ticket,project,branch,json.dumps(s,ensure_ascii=False)))
    con.commit();assert con.execute('pragma integrity_check').fetchone()[0]=='ok';con.close()
    _,got,_=read_project(dest)
    assert all(got[u]==d for u,d in docs.items())
    with (GBUCK/'rev-c1/schematic/BOM_RevC1.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames+['与RevC1比较'];rows=list(reader)
    for row in rows:
        row['与RevC1比较']='保留'
        if row['位号']=='J_MON':
            row['数值/型号']=row['数值/型号'].replace('PA5','PA6')
            row['装配说明']=row['装配说明'].replace('PA5','PA6')+'；PA5保留LCD SCK，PA6配置模拟输入，不启用SPI1_MISO'
            row['与RevC1比较']='外接控制板目标由PA5改PA6/ADC12_IN6；端子/脚号/主板网络不变'
    with (ROOT/'schematic/BOM_RevC2.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
    dm,dd,_=read_project(dest);_,_,new,np=inventory(dm,dd,TITLE)
    oldnets={(p['ref'],p['pin']):p['net'] for p in pins}
    newnets={(p['ref'],p['pin']):p['net'] for p in np}
    assert oldnets==newnets
    changes={r:[p['attrs']['Value'],new[r]['attrs']['Value']] for r,p in parts.items()
             if p['attrs']['Value']!=new[r]['attrs']['Value']}
    assert changes=={'J_MON':['2P VIN_POST ADC / PA5','2P VIN_POST ADC / PA6']}
    assert next(p for p in np if p['ref']=='J_MON' and p['pin']=='1')['name']=='PA6/ADC'
    assert all(dd[u]==v for u,v in old.items() if u not in changed)
    assert all(row['数值/型号']==new[row['位号']]['attrs']['Value'] for row in rows)
    result={'status':'PASS_STATIC_NATIVE_READBACK','date_beijing':'2026-10-27',
        'source_sha256':sha(src),'native_sha256':sha(dest),'pages':len(pages),'parts':len(new),
        'nets':len({p['net'] for p in np if p['net']}),'connected_pins':sum(bool(p['net']) for p in np),
        'all_RevC1_pin_nets_unchanged':True,'all_legacy_documents_unchanged':True,
        'display_value_changes':changes,'component_values_changed':False,'parts_added':False,
        'physical_control_connection':'J_MON.1: PA5 -> PA6/ADC12_IN6; J_MON.2=GND',
        'lcd_mapping_source':'RevB original PDF page 7: SCK=PA5, MOSI=PA7, CS=PB12, DC=PB13, RST=PB14',
        'native_client_open_test':False,'ERC_DRC_run':False,'hardware_tested':False,
        'changed_document_ids':sorted(changed)}
    out=ROOT/'results/data';out.mkdir(exist_ok=True,parents=True)
    (out/'schematic_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (out/'RevC2_逐引脚接线表.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(np[0]),lineterminator='\n');w.writeheader();w.writerows(np)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
