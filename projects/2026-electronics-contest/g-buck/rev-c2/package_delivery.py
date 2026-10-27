"""Check cross-artifact consistency and package the completed Rev C.2 revision."""
from pathlib import Path
import csv,hashlib,json,re,zipfile
import fitz

ROOT=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    static=json.loads((ROOT/'results/data/schematic_verification.json').read_text())
    sync=json.loads((ROOT/'results/data/multisim_sync.json').read_text())
    logic=json.loads((ROOT/'results/data/protection_checks.json').read_text())
    assert static['status']=='PASS_STATIC_NATIVE_READBACK'
    assert sync['status']=='PASS_NATIVE_STATIC_READBACK'
    assert logic['status']=='PASS_ISOLATED_FUNCTIONAL_BENCHES'
    assert (static['parts'],static['nets'],static['connected_pins'])==(120,51,310)
    native=next((ROOT/'schematic/native').glob('*.eprj2'));assert sha(native)==static['native_sha256']
    main=ROOT/'downloads/GBUCK_REVC2_FULL_25V_5R_100ms.ms14'
    assert sha(main)==logic['embedded_project_sha256']
    for row in sync['files']:assert sha(ROOT/row['file'])==row['sha256']
    with (ROOT/'results/data/RevC2_逐引脚接线表.csv').open(encoding='utf-8-sig',newline='') as f:pins=list(csv.DictReader(f))
    rendered=json.loads((ROOT/'results/data/rendered_pin_map.json').read_text())
    key=lambda r:(r['ref'],r['pin'],r['net'],r['name'])
    assert set(map(key,pins))==set(map(key,rendered))
    assert len(pins)==323
    doc=fitz.open(ROOT/'schematic/previews/G题同步Buck完整原理图_RevC2.pdf')
    assert len(doc)==10;text=''.join(p.get_text() for p in doc)
    assert all(ref in text for ref in {p['ref'] for p in pins})
    assert 'PA6/ADC' in text
    for i,page in enumerate(doc):
        for b in page.get_text('blocks'):
            x0,y0,x1,y1=b[:4]
            assert x0>=-1 and y0>=-1 and x1<=page.rect.width+1 and y1<=page.rect.height+1,(i,b)
    results={'status':'PASS_DELIVERY_CONSISTENCY','date_beijing':'2026-10-27',
        'PDF_pages':10,'PDF_all_120_references_present':True,'PDF_pin_map_matches_all_323_native_pins':True,
        'PDF_text_not_clipped':True,'multisim_variants':len(sync['files']),
        'independent_logic_cases_completed':len(logic['tests']),
        'source_review_archived':True,'full_converter_dynamic_validation':False,
        'Windows_Multisim_execution':False,'real_firmware_validation':False,'efficiency_validation':False}
    (ROOT/'results/data/delivery_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    target=ROOT/'downloads/GBUCK_RevC2_核对修订与Multisim_2026-10-27.zip'
    files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
           and p!=target and p.suffix not in ('.pyc','.zip') and p.name!='SHA256SUMS.txt']
    sums=ROOT/'SHA256SUMS.txt'
    sums.write_text('\n'.join(sha(p)+'  '+str(p.relative_to(ROOT)) for p in sorted(files))+'\n')
    files.append(sums)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):z.write(p,'RevC2/'+str(p.relative_to(ROOT)))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for p in files:assert z.read('RevC2/'+str(p.relative_to(ROOT)))==p.read_bytes()
    for p in (ROOT/'README.md',ROOT/'simulation/multisim14/README.md',ROOT.parent/'rev-c1/README.md',ROOT.parents[3]/'README.md'):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if not link.startswith(('http:','https:','#')):assert (p.parent/link).exists(),(p,link)
    print(json.dumps(results,ensure_ascii=False,indent=2))
    print('Archive:',target.name,'bytes:',target.stat().st_size,'files:',len(files))


if __name__=='__main__':main()
