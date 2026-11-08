from pathlib import Path
from docx import Document
import json,hashlib,zipfile,re,fitz,collections
B=Path(__file__).resolve().parent.parent;L=B/'reports/latex';raw=B/'references/回收仿真_七机两段点火_本次原稿.docx';doc=Document(raw)
a=json.load(open(B/'results/data/source_tables.json'));assert a==[[[c.text for c in r.cells] for r in t.rows] for t in doc.tables]
with zipfile.ZipFile(raw) as z:
 for i in range(9,15):assert (B/'results/figures'/f'source{i}.png').read_bytes()==z.read(f'word/media/image{i}.png')
con=json.load(open(B/'results/data/table_concordance.json'));assert sorted(x['source_table_index'] for x in con)==list(range(2,20));assert all(x['source_rows']==x['typeset_rows'] for x in con)
assert not list(B.rglob('*.npz')),'No prior simulation arrays may be imported'
tex=(L/'main.tex').read_text();log=(L/'build/main.log').read_text(errors='replace');d=fitz.open(L/'build/main.pdf');text='\n'.join(p.get_text() for p in d)
for bad in ['98.308','38.942','347.624','144.782','final140','v15/','v16/']:assert bad not in tex,bad
assert not re.search(r'C_D\s*=\s*0\.5',tex)
assert 'Overfull' not in log and 'Missing character:' not in log and 'undefined on input line' not in log
assert '??' not in text
for value in ['104','120','96','110','102','112','106.6','2.02','45.2','61.5','143','330']:assert value in text,value
assert 'Powell' in text
assert tex.count('\\begin{figure}')==10
assert len(re.findall(r'\\newlabel\{tab:[^}@]+\}',(L/'build/main.aux').read_text()))==19
assert len(re.findall(r'\\bibcite\{',(L/'build/main.aux').read_text()))==10
wc=len(d[0].get_text().split('Abstract',1)[1].split());assert wc<=300
assert all('Team TBA' in p.get_text() for p in d)
assert all(abs(p.rect.width-595.276)<.1 and abs(p.rect.height-841.89)<.1 for p in d)
pcounts={str(k):sum(c.startswith('✓') for r in a[k][1:] for c in r[1:]) for k in [5,16]};assert pcounts=={'5':15,'16':13}
fonts=collections.Counter()
for p in d:
 for b in p.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   for s in l['spans']:
    if len(s['text'].strip())>2:fonts[(s['font'],round(s['size'],2))]+=len(s['text'])
out=dict(pdf_pages=len(d),abstract_words=wc,figures=10,tables=19,source_tables_preserved=18,source_curve_images_preserved=6,references=10,source_table_extraction_exact=True,source_curve_files_byte_identical=True,prior_result_arrays_used=False,simulation_rerun=False,baseline_perturbation_pass_cells=15,parameterized_perturbation_pass_cells=13,all_team_headers=True,overfull_boxes=0,missing_glyphs=0,unresolved_references=0,font_profile=[dict(font=k[0],pdf_points=k[1],characters=v) for k,v in fonts.most_common(6)])
(B/'results/data/source_paper_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
