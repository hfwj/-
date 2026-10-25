import sqlite3,json,base64,gzip
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def read_project(path, dump=False):
 c=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
 p=c.execute('select uuid,name,branch_uuid from projects').fetchone()
 b=c.execute('select uuid,history_uuid from branches where uuid=?',(p['branch_uuid'],)).fetchone()
 rows={r['uuid']:r for r in c.execute('select * from project_history_'+b['uuid'])}
 chain=[];h=b['history_uuid']
 while h:
  r=rows[h];chain.append(r);h=r['parent']
 docs={};meta={};chunks=[];last=None;max_ticket=0
 for h in reversed(chain):
  for i in range(h['num']+1):
   u=h['uuid']+('-'+str(i) if i else '')
   row=c.execute('select dataStr from history_data where uuid=?',(u,)).fetchone()
   if not row:continue
   raw=gzip.decompress(AESGCM(bytes.fromhex(h['key'])).decrypt(bytes.fromhex(h['uuid']),base64.b64decode(row[0]),None)).decode()
   chunks.append(raw)
   for line in raw.splitlines():
    if '||' not in line:continue
    left,right=line.split('||',1)
    hd=json.loads(left);max_ticket=max(max_ticket,hd.get('ticket',0));body=right.rstrip('|');body=json.loads(body) if body else None
    typ=hd['type']
    if typ=='DOCHEAD':
     last=body['uuid'];meta.setdefault(last,{}).update(body);docs.setdefault(last,{})
    elif typ=='DOCTYPE':pass
    elif last:
     key=(typ,hd.get('id',''));o=docs[last]
     if body is None:o.pop(key,None)
     else:o.setdefault(key,{}).update(body)
 if dump:
  out=Path('/workspace/work/github_buck/decoded');out.mkdir(exist_ok=True)
  for u,d in docs.items():(out/(u+'.json')).write_text(json.dumps({'meta':meta[u],'objects':[{'type':k[0],'id':k[1],'body':v} for k,v in d.items()]},ensure_ascii=False,indent=2))
  (out/'full_source.txt').write_text('\n'.join(chunks))
 c.close();return meta,docs,max_ticket
