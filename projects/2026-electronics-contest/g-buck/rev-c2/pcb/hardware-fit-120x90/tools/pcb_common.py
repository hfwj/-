from pathlib import Path
import base64, collections, copy, gzip, hashlib, json, math, sqlite3, sys, uuid
ROOT=Path(__file__).resolve().parents[1]
REV=ROOT.parents[1]
sys.path.insert(0,str(REV/'schematic/tools'))
from native_common import read_project, inventory, attrs, sha
from shapely.geometry import Polygon, box, Point, LineString
from shapely import affinity

PATH=ROOT/'native/GBUCK_RevC2_120x90_PCB_review.eprj2'

def pcb_export_references(docs, parts):
    """Resolve schematic instance overrides before device PCB-export flags."""
    included=set()
    for ref,p in parts.items():
        device=docs[p['attrs']['Device']]['META','META']['attributes']
        value=p['attrs'].get('Convert to PCB',device.get('Convert to PCB'))
        flag=str(value).strip().lower()
        if flag in ('yes','true','1'):included.add(ref)
        elif flag not in ('no','false','0'):
            raise ValueError('Unknown PCB-export flag for '+ref+': '+str(value))
    return included

def copper_vias(docs, pcb):
    return [{'id':i,'net':v['netName'],'x':v['centerX']*.0254,
             'y':v['centerY']*.0254,'diameter':v['viaDiameter']*.0254,
             'hole_diameter':v['holeDiameter']*.0254,
             'geometry':Point(v['centerX']*.0254,v['centerY']*.0254).buffer(v['viaDiameter']*.0254/2),
             'layers':{1,2},'body':v}
            for (k,i),v in docs[pcb].items() if k=='VIA']

def copper_fills(docs, pcb):
    fills=[]
    for (k,i),f in docs[pcb].items():
        if k!='FILL' or f['layerId'] not in (1,2):continue
        assert f['fillStyle']=='SOLID' and f['width']==0,('Unsupported copper fill',i)
        rings=[]
        for path in f['path']:
            assert path[2]=='L' and all(isinstance(v,(float,int)) for v in path[:2]+path[3:])
            values=path[:2]+path[3:]
            rings.append([(values[n]*.0254,values[n+1]*.0254) for n in range(0,len(values),2)])
        g=Polygon(rings[0],rings[1:]);assert g.is_valid and not g.is_empty
        fills.append({'id':i,'net':f['netName'],'layer':f['layerId'],'geometry':g,'body':f})
    return fills

def copper_geometry(meta,docs,pcb):
    o=docs[pcb];a=attrs(o);pads=[];bodies=[];parts={}
    for (k,cid),c in o.items():
        if k!='COMPONENT':continue
        ref=a[cid]['Designator'];parts[ref]=(cid,c,a[cid])
        fp=docs[a[cid]['Footprint']]
        nets={json.loads(i)[3]:b['padNet'] for (k,i),b in o.items()
              if k=='PAD_NET' and json.loads(i)[1]==cid}
        def transform(g):
            return affinity.translate(affinity.rotate(g,c['angle'],origin=(0,0)),c['x']*.0254,c['y']*.0254)
        for (pk,pid),p in fp.items():
            if pk=='PAD':
                x=p['centerX']*.0254;y=p['centerY']*.0254
                w=p['defaultPad']['width']*.0254;h=p['defaultPad']['height']*.0254
                if p['defaultPad']['padType']=='ELLIPSE':
                    # Circumscribe the native ellipse: never gain clearance
                    # from the small chord error of an inscribed circle.
                    factor=1/math.cos(math.pi/128)
                    g=affinity.scale(Point(0,0).buffer(1,quad_segs=32),w/2*factor,h/2*factor)
                    g=affinity.translate(g,x,y)
                else:
                    g=box(x-w/2,y-h/2,x+w/2,y+h/2)
                g=affinity.rotate(g,p.get('padAngle',0),origin=(x,y));g=transform(g)
                center=transform(Point(x,y))
                pads.append({'ref':ref,'pin':p['num'],'pid':pid,'net':nets[pid],
                    'geometry':g,'x':center.x,'y':center.y,'w':w,'h':h,
                    'layers':[1,2] if p['layerId']==12 else [p['layerId']],
                    'hole':p['hole'],'body':p})
            elif pk=='POLY' and p['layerId']==48:
                vals=[z for z in p['path'] if isinstance(z,(int,float))]
                g=transform(Polygon([(vals[n]*.0254,vals[n+1]*.0254) for n in range(0,len(vals),2)]))
                bodies.append({'ref':ref,'geometry':g})
    tracks=[{'id':i,'body':b,'net':b['netName'],'layer':b['layerId'],
             'geometry':LineString([(b['startX']*.0254,b['startY']*.0254),
                                   (b['endX']*.0254,b['endY']*.0254)]).buffer(b['width']*.0254/2)}
            for (k,i),b in o.items() if k=='LINE']
    return parts,pads,bodies,tracks

def append_history(path,meta,docs,changed,label,removed=None):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _,_,ticket=read_project(path)
    con=sqlite3.connect(path)
    project,branch=con.execute('select uuid,branch_uuid from projects').fetchone()
    parent=con.execute('select history_uuid from branches where uuid=?',(branch,)).fetchone()[0]
    history=uuid.uuid5(uuid.NAMESPACE_URL,'gbuck-revc2-pcb:'+label).hex
    chunks=[]
    for u in sorted(changed):
        ticket+=1;chunks.append(json.dumps({'type':'DOCHEAD','ticket':ticket})+'||'+json.dumps(meta[u],ensure_ascii=False)+'|')
        for k,i in (removed or {}).get(u,[]):
            ticket+=1;chunks.append(json.dumps({'type':k,'id':i,'ticket':ticket})+'|||')
        for (k,i),b in docs[u].items():
            ticket+=1;chunks.append(json.dumps({'type':k,'id':i,'ticket':ticket})+'||'+json.dumps(b,ensure_ascii=False)+'|')
    key=hashlib.sha256(label.encode()).digest()[:16]
    data=base64.b64encode(AESGCM(key).encrypt(bytes.fromhex(history),gzip.compress(('\n'.join(chunks)+'\n').encode(),mtime=0),None)).decode()
    con.execute('INSERT INTO project_history_'+branch+' (uuid,parent,key,num,snapshot_num) VALUES (?,?,?,0,0)',(history,parent,key.hex()))
    con.execute('INSERT INTO history_data (uuid,history_uuid,dataStr) VALUES (?,?,?)',(history,history,data))
    con.execute('UPDATE branches SET history_uuid=? WHERE uuid=?',(history,branch))
    con.execute('UPDATE projects SET ticket=?,g_ticket=? WHERE uuid=?',(ticket,ticket,project))
    con.commit();assert con.execute('pragma integrity_check').fetchone()[0]=='ok';con.close()
