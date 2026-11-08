from pathlib import Path
from docx import Document
import json,zipfile,hashlib,shutil
B=Path(__file__).resolve().parent.parent
P=B/'references/回收仿真_七机两段点火_本次原稿.docx'
d=Document(P);tables=[[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
(B/'results/data/source_tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
(B/'results/data/source_paragraphs.json').write_text(json.dumps([dict(index=i,style=p.style.name,text=p.text) for i,p in enumerate(d.paragraphs)],ensure_ascii=False,indent=2))
with zipfile.ZipFile(P) as z:
 media={}
 for n in z.namelist():
  if n.startswith('word/media/'):
   b=z.read(n);dest=B/'references'/Path(n).name;dest.write_bytes(b);media[dest.name]=hashlib.sha256(b).hexdigest()
 for i in range(9,15):shutil.copy2(B/'references'/f'image{i}.png',B/'results/figures'/f'source{i}.png')
(B/'references/source_provenance.json').write_text(json.dumps(dict(document=P.name,sha256=hashlib.sha256(P.read_bytes()).hexdigest(),paragraphs=len(d.paragraphs),tables=len(tables),media_sha256=media,content_source='Only the document uploaded in this turn',simulation_rerun=False,prior_manuscript_or_simulation_data_used=False),ensure_ascii=False,indent=2))
print('Extracted',len(tables),'tables and',len(media),'unmodified media files.')
