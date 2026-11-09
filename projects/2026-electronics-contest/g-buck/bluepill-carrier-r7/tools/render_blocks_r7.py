from pathlib import Path
from playwright.sync_api import sync_playwright
import fitz
import sys
root=(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1])/'schematic/previews'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for name in ['Control']:
  pre=root/name
  for svg in sorted(pre.glob('*.svg')):
   page=b.new_page(viewport={'width':3100,'height':3300});page.set_content(svg.read_text());page.locator('svg').screenshot(path=str(svg.with_suffix('.png')))
   if svg.stem!='All':
    page.add_style_tag(content='@page { size:A3 landscape; margin:10mm; } svg { width:100%; height:auto; max-height:270mm; }');page.pdf(path=str(svg.with_suffix('.pdf')),format='A3',landscape=True,print_background=True,prefer_css_page_size=True)
   page.close()
  out=fitz.open()
  for f in sorted(pre.glob('[0-9][0-9]_Block.pdf')):
   with fitz.open(f) as d:out.insert_pdf(d)
  out.save(pre/(name+'_Blocks.pdf'));out.close()
 b.close()
print('Control R7 six-page PDF generated')
