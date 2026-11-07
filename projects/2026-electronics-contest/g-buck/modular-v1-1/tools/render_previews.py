from pathlib import Path
from playwright.sync_api import sync_playwright
import sys
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'schematic/previews'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for svg in sorted(root.glob('*.svg')):
  if svg.name.startswith(('C_','D_')):continue
  page=browser.new_page(viewport={'width':2100,'height':1900},device_scale_factor=1)
  page.set_content(svg.read_text());page.locator('svg').screenshot(path=str(svg.with_suffix('.png')))
  page.add_style_tag(content='@page { size: A3 landscape; margin: 10mm; } svg { width: 100%; height: auto; max-height: 270mm; }')
  page.pdf(path=str(svg.with_suffix('.pdf')),format='A3',landscape=True,print_background=True,prefer_css_page_size=True)
  page.close()
 browser.close()
print('Rendered modified A/B SVG files to PNG and PDF; C/D preserved')
