from pathlib import Path
import fitz,re,json,hashlib,collections
B=Path(__file__).resolve().parent.parent;L=B/'reports/latex';pdf=L/'build/main.pdf';d=fitz.open(pdf);text='\n'.join(p.get_text() for p in d);log=(L/'build/main.log').read_text(errors='replace');src=(L/'main.tex').read_text()
assert 'Overfull' not in log
assert 'Missing character:' not in log
assert 'undefined references' not in log and 'undefined on input line' not in log
assert '??' not in text
assert all('Team TBA' in p.get_text() for p in d)
assert all(abs(p.rect.width-595.276)<.1 and abs(p.rect.height-841.89)<.1 for p in d)
abstract=d[0].get_text().split('Abstract',1)[1];wc=len(abstract.split());assert wc<=300
for s in ['98.308','38.942','137.250','2.750','364.203','347.624','47.018']:assert s in text,s
assert src.count('\\begin{figure}')==8
assert src.count('\\begin{table}')==8
assert len(re.findall(r'\\bibcite\{', (L/'build/main.aux').read_text()))==13
assert all(len(fitz.open(p)[0].get_images())==0 for p in (B/'results/figures').glob('*.pdf'))
# Validate the reference result has not changed while typesetting.
for n in ['metrics.json','verification.json','physics_checks.json','optimized_controls.npz','nominal_replay.npz']:
 a=(B/'results/data'/n).read_bytes();expected=json.load(open(B/'references/provenance.json'))['frozen_data_sha256'][n];assert hashlib.sha256(a).hexdigest()==expected,n
sizes=collections.Counter()
for p in d:
 for block in p.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   for s in line['spans']:
    if len(s['text'].strip())>2:sizes[(s['font'],round(s['size'],2))]+=len(s['text'])
minwords=min(len(p.get_text().split()) for p in d);assert minwords>30
out=dict(pdf_pages=len(d),page_format='A4',abstract_words=wc,main_figures=8,main_tables=8,bibliography_entries=13,dominant_fonts=[dict(font=k[0],pdf_points=k[1],characters=v) for k,v in sizes.most_common(7)],all_pages_have_team_header=True,overfull_boxes=0,missing_glyphs=0,unresolved_references=0,figure_pdfs_have_no_raster_images=True,frozen_v15_data_unchanged=True,scope='Typesetting and data-consistency validation; no new dynamics or safety validation.')
(B/'results/data/paper_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
