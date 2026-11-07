from pathlib import Path
import hashlib,json,zipfile,tempfile,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent
ZIP=ROOT/'downloads/UPC_2026_A_v11_论文初版与复现资料.zip'
EXTRA=['v5/results/data/passive_cases.csv','v4/results/data/safety_criteria.csv']
def files(root):return [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'downloads' not in p.relative_to(root).parts]
def pack():
 with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
  for root in [PROJECT/'v8',PROJECT/'v9',PROJECT/'v10',ROOT]:
   for p in files(root):z.write(p,Path(PROJECT.name)/root.name/p.relative_to(root))
  for n in EXTRA:z.write(PROJECT/n,Path(PROJECT.name)/n)
if __name__=='__main__':
 for suffix in ['.aux','.out','.pdf']:
  p=ROOT/'results/logs'/('paper'+suffix)
  if p.exists():p.unlink()
 pack()
 with tempfile.TemporaryDirectory() as td:
  with zipfile.ZipFile(ZIP) as z:z.extractall(td)
  script=Path(td)/PROJECT.name/'v11/simulation/validate_paper.py'
  cp=subprocess.run([sys.executable,str(script)],capture_output=True,text=True)
  assert cp.returncode==0,cp.stdout+cp.stderr
  report=json.loads(cp.stdout)
  (ROOT/'results/logs/archive_reproduction.json').write_text(json.dumps(dict(archive_extract_and_document_validation_pass=True,pdf_pages=report['pdf_pages'],abstract_words=report['abstract_words_whitespace_count'],historical_versions_unchanged=report['historical_versions_unchanged'],submission_ready=False,note='Research reproduction bundle, not a complete AI transcript or ready-to-submit anonymous supplement'),indent=2))
 manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files(ROOT) if p.name!='sha256.json'}
 (ROOT/'results/logs/sha256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));pack()
 with zipfile.ZipFile(ZIP) as z:
  assert all(hashlib.sha256(z.read(str(Path(PROJECT.name)/'v11'/name))).hexdigest()==h for name,h in manifest.items())
 print('Archive validated; files',len(manifest)+1,'bytes',ZIP.stat().st_size)
