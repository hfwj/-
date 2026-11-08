"""Manuscript checks, not a new physical validation or contest-compliance certificate."""
from pathlib import Path
import re,json,zipfile,hashlib
import fitz
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 src=(ROOT/'reports/UPC_2026_A_Paper_Draft02_EN.md').read_text();team=re.search(r'^Team (.+)$',src,re.M).group(1)
 abstract=src[src.index('We develop a staged model'):src.index('\\newpage')].strip();count=len(abstract.split());assert count<=300,count
 pdf=fitz.open(ROOT/'reports'/f'{team}_A_Draft02.pdf');pages=[p.get_text() for p in pdf];whole='\n'.join(pages)
 assert all(f'Team {team}' in t and 'Problem A' in t for t in pages)
 assert '1. Problem interpretation' not in pages[0] and 'We develop a staged model' in pages[0]
 assert re.findall(r'^# (\d+)\.',src,re.M)==[str(i) for i in range(1,12)]
 assert len(re.findall(r'^\*\*Table \d+\.',src,re.M))==9
 assert len(re.findall(r'^!\[',src,re.M))==9
 assert all(f'Figure {i}:' in whole for i in range(1,10))
 refs=set(map(int,re.findall(r'^\[(\d+)\]',src,re.M)));assert refs==set(range(1,13))
 assert all(x in src for x in ['149.30','147.84','24.78','Report on the Use of AI','写出最终论文初版','incomplete'])
 assert '@@' not in src and 'hfwj' not in whole and '/workspace/' not in whole
 assert not pdf.metadata.get('author')
 assert all(20<=span['bbox'][0] and span['bbox'][2]<=page.rect.width-20 for page in pdf for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for span in line['spans'] if span['text'].strip())
 with zipfile.ZipFile(ROOT/'reports/UPC_2026_A_Paper_Draft02_EN.docx') as z:
  doc=etree.fromstring(z.read('word/document.xml'));ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};math_count=len(doc.xpath('//m:oMath',namespaces=ns));assert math_count>=30
  wordtext=' '.join(doc.xpath('//w:t/text()',namespaces=ns));assert not any(x in wordtext for x in [r'\frac',r'\begin{aligned}',r'\rm '])
  image_count=len([n for n in z.namelist() if n.startswith('word/media/')]);assert image_count==9
  assert f'Team {team}' in z.read('word/header1.xml').decode()
 log=(ROOT/'results/logs/paper.log').read_text();assert not any(k in log for k in ['Overfull','Missing character','LaTeX Error'])
 buildlog=(ROOT/'results/logs/build.log').read_text();assert 'Could not convert TeX math' not in buildlog
 evidence=json.loads((ROOT/'results/data/evidence.json').read_text());s=evidence['nominal'];assert s['M0_subset_pass'];assert abs((s['initial_propellant_kg']-s['consumed_kg'])-(s['final']['mass_kg']-130000))<1e-6
 assert abs((evidence['comparison'][0]['initial_propellant_kg']-s['initial_propellant_kg'])/1000-1.56)<.01
 historical={}
 for version in ['v8','v9','v10','v11']:
  root=ROOT.parent/version;manifest=json.loads((root/'results/logs/sha256.json').read_text());historical[version]=all(hashlib.sha256((root/k).read_bytes()).hexdigest()==v for k,v in manifest.items());assert historical[version]
 inputs=json.loads((ROOT/'references/input_hashes.json').read_text());assert all(hashlib.sha256((ROOT.parent/k).read_bytes()).hexdigest()==v for k,v in inputs.items())
 result=dict(document_build_checks_pass=True,abstract_words_whitespace_count=count,pdf_pages=len(pdf),figure_count=9,table_count=9,reference_count=12,word_math_object_count=math_count,word_embedded_image_count=image_count,anonymous_page_headers_pass=True,first_page_only_cover_items_pass=True,no_overflow_or_missing_glyphs=True,original_input_hashes_pass=True,historical_versions_unchanged=historical,team_number=team,team_placeholder_unresolved=team=='TBA',full_AI_transcript_attached=False,full_M1_contact_safety='NOT_VERIFIED',submission_ready=False)
 (ROOT/'results/logs/manuscript_checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
