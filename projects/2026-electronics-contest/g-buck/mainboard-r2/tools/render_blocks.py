from pathlib import Path
import sys
from playwright.sync_api import sync_playwright
root=Path(sys.argv[1]).resolve();pre=root/'schematic/previews'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for svg in sorted(pre.glob('*.svg')):
  page=b.new_page(viewport={'width':3100,'height':3300},device_scale_factor=1)
  page.set_content(svg.read_text());page.locator('svg').screenshot(path=str(svg.with_suffix('.png')))
  if svg.stem!='Mainboard_All':
   page.add_style_tag(content='@page { size: A3 landscape; margin: 10mm; } svg { width: 100%; height: auto; max-height: 270mm; }')
   page.pdf(path=str(svg.with_suffix('.pdf')),format='A3',landscape=True,print_background=True,prefer_css_page_size=True)
  page.close()
 b.close()
import fitz
out=fitz.open()
for path in sorted(pre.glob('[0-9][0-9]_Block.pdf')):
 with fitz.open(path) as doc:out.insert_pdf(doc)
out.save(pre/'Mainboard_Six_Blocks.pdf');out.close()
print('7 PNG previews and combined 6-page PDF generated')
