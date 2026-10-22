"""Render the documentation and numbered symbol layout; no circuit changes."""
from pathlib import Path
import csv,re,html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Preformatted
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from draw_circuits import Sheet,W,H

ROOT=Path(__file__).resolve().parent

def main():
    with (ROOT/'pin_mapping.csv').open(encoding='utf-8-sig') as f:ports=list(csv.DictReader(f))
    names={int(x['model_pin']):x['port_name'] for x in ports}
    p=canvas.Canvas(str(ROOT/'diagrams/元器件向导_17脚编号图.pdf'),pagesize=(W,H))
    s=Sheet(p,'05_component_symbol_pinmap','元器件向导：17脚符号编号 / Component Wizard pin numbering')
    s.text(60,855,'这是建议的符号布局，不是Multisim界面截图，也不是实物芯片脚位。按名称在Pin mapping页面逐项对应。',18)
    s.box(610,170,480,640,'GBUCK_REVB_EQ','17 visible symbol pins\nSelect top-level 17-port model\nSimulation only; no PCB footprint')
    left=[(1,730),(3,650),(4,570),(5,490),(6,410),(17,240)]
    right=[(n,730-50*i) for i,n in enumerate([2,7,8,9,10,11,12,13,14,15,16])]
    assert {n for n,_ in left+right}==set(range(1,18))
    for n,y in left:
        s.line(390,y,610,y);s.dot(390,y)
        s.text(405,y+12,f'{n}   {names[n]}',17,color='#185ea2')
    for n,y in right:
        s.line(1090,y,1320,y);s.dot(1320,y)
        s.text(1105,y+12,f'{n}   {names[n]}',17,color='#22743e')
    s.ground(390,240)
    s.text(70,760,'左侧共6脚：',18)
    s.text(70,715,'1: VIN_EXT -> 25V supply',16)
    s.text(70,655,'3: VSET -> 10V setpoint signal',16)
    s.text(70,595,'4: ISET -> 1V setpoint signal',16)
    s.text(70,535,'5: ARM -> 3.3V pulse at 5ms',16)
    s.text(70,475,'6: MCU_EN -> high after 5.1ms',16)
    s.text(70,260,'17: COM -> global ground 0',16)
    s.text(1370,760,'右侧共11脚：',18)
    s.text(1370,705,'2: VOUT -> load',16)
    s.text(1370,660,'7..16: monitor outputs',16)
    s.text(1370,595,'No extra supply',16)
    s.text(1370,560,'on monitor pins',16)
    s.text(70,115,'模型端口顺序仍为 1 VIN_EXT, 2 VOUT, 3 VSET, ... , 17 COM。图上的左右位置不改变模型顺序。',18)
    s.text(70,80,'If your symbol arrangement differs, keep the correct 17 pin names and explicit model mapping.',15)
    s.finish();p.save()
    render_guide()
    print('Created numbered SVG/PDF symbol and detailed operation PDF.')

def render_guide():
    body=ParagraphStyle('GuideBody',fontName='STSong-Light',fontSize=10,leading=16,wordWrap='CJK',spaceAfter=6)
    title=ParagraphStyle('GuideTitle',parent=body,fontSize=19,leading=25,spaceAfter=12)
    heading=ParagraphStyle('GuideHeading',parent=body,fontSize=13,leading=20,spaceBefore=12,spaceAfter=7,keepWithNext=True)
    code=ParagraphStyle('GuideCode',fontName='Courier',fontSize=8,leading=11,spaceAfter=8)
    clean=lambda s:html.escape(re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s).replace('**','').replace('`',''))
    lines=(ROOT/'元器件向导逐页操作.md').read_text().splitlines();story=[];i=0
    while i<len(lines):
        s=lines[i].strip();i+=1
        if not s:continue
        if s.startswith('```'):
            block=[]
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            i+=1;story.append(Preformatted('\n'.join(block),code));continue
        if s.startswith('!['):
            story.append(Paragraph('编号图另见：diagrams/元器件向导_17脚编号图.pdf；映射表如下。',body));continue
        if s.startswith('|'):
            rows=[]
            while True:
                if not re.fullmatch(r'[| :\-]+',s):rows.append([x.strip() for x in s.strip('|').split('|')])
                if i>=len(lines) or not lines[i].strip().startswith('|'):break
                s=lines[i].strip();i+=1
            cols=len(rows[0]);widths={2:[135,370],3:[155,175,175],4:[58,100,125,222]}.get(cols,[505/cols]*cols)
            tab=Table([[Paragraph(clean(c),body) for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
            tab.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b6c6d0')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4eff6')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5)]))
            story.extend([tab,Spacer(1,8)]);continue
        if s.startswith('#'):
            style=title if s.startswith('# ') else heading
            story.append(Paragraph(clean(s.lstrip('#').strip()),style))
        else:story.append(Paragraph(clean(s),body))
    def footer(c,doc):
        c.setFont('STSong-Light',9);c.drawString(45,25,'Multisim 14.0向导操作说明 · 2026-10-22 · 界面名称以本机为准')
        c.drawRightString(550,25,str(doc.page))
    SimpleDocTemplate(str(ROOT/'元器件向导逐页操作.pdf'),pagesize=(595.28,841.89),leftMargin=45,rightMargin=45,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':main()
