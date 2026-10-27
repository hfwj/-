"""Render an enhanced pin-numbered PDF directly from the delivered native records.

Native coordinates use y down; the single xy() transform below is applied to
symbol geometry AND its pin/network labels. This is a preview, not an EDA export.
"""
import json
import math
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from native_common import ROOT,read_project,inventory,attrs

pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
W,H=landscape(A3)
INK=colors.HexColor('#162c42');BLUE=colors.HexColor('#12618c');RED=colors.HexColor('#ac3825')
CHANGED={'J_MON'}


def safe(s):return str(s).replace('µ','u')


def text(c,x,y,s,size=9,color=INK,align='left'):
    c.setFillColor(color);c.setFont('STSong-Light',size)
    getattr(c,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,y,safe(s))


def para(c,x,y,s,width,size=11,leading=18):
    style=ParagraphStyle('p',fontName='STSong-Light',fontSize=size,leading=leading,textColor=INK,wordWrap='CJK')
    p=Paragraph(escape(safe(s)),style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h-10


def footer(c,page):
    c.setStrokeColor(colors.HexColor('#ced7df'));c.line(30,35,W-30,35)
    text(c,30,21,'Rev C.2 | 原生记录增强预览（非EDA客户端导出）| 同名网络跨页相连 | 未运行客户端ERC/PCB DRC',8)
    text(c,W-30,21,f'2026-10-27（北京时间）  {page}',8,align='right')


def arc_points(b):
    p=(b['startX'],b['startY']);q=(b['referX'],b['referY']);r=(b['endX'],b['endY'])
    ax,ay=p;bx,by=q;cx,cy=r
    det=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(det)<1e-9:return [p,q,r]
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/det
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/det
    angles=[math.atan2(y-uy,x-ux) for x,y in (p,q,r)]
    ccw=(angles[2]-angles[0])%(2*math.pi)
    sweep=ccw if (angles[1]-angles[0])%(2*math.pi)<=ccw else ccw-2*math.pi
    radius=math.hypot(ax-ux,ay-uy)
    return [(ux+radius*math.cos(angles[0]+sweep*i/40),uy+radius*math.sin(angles[0]+sweep*i/40)) for i in range(41)]


def draw_component(c,ref,part,symbol,pinrows,x0,top,width,height,bomrow):
    cx=x0+width/2;cy=top-height*.51
    at=part['attrs'];a=attrs(symbol)
    rects=[b for (k,_),b in symbol.items() if k=='RECT']
    isbox=any(abs(b['dotX2']-b['dotX1'])>=100 for b in rects)
    scale=.9 if isbox else 1.5
    color=RED if ref in CHANGED else INK
    def xy(x,y):return cx+x*scale,cy-y*scale
    c.setStrokeColor(colors.HexColor('#e1e7ed'));c.setLineWidth(.4)
    c.roundRect(x0+3,top-height+4,width-6,height-8,4,stroke=1,fill=0)
    text(c,x0+12,top-17,ref,11,color)
    c.setStrokeColor(color);c.setLineWidth(.65)
    for (kind,id),b in symbol.items():
        if b.get('partId') not in (None,part['body']['partId']):continue
        points=None
        if kind=='POLY':points=[(p['x'],p['y']) for p in b['points']]
        elif kind=='ARC':points=arc_points(b)
        elif kind=='RECT':
            xa,ya=xy(b['dotX1'],b['dotY1']);xb,yb=xy(b['dotX2'],b['dotY2'])
            c.rect(min(xa,xb),min(ya,yb),abs(xb-xa),abs(yb-ya),stroke=1,fill=0)
        if points:
            path=c.beginPath();path.moveTo(*xy(*points[0]))
            for point in points[1:]:path.lineTo(*xy(*point))
            if b.get('closed'):path.close()
            c.drawPath(path,stroke=1,fill=0)
    for (kind,pid),b in symbol.items():
        if kind!='PIN' or b.get('partId')!=part['body']['partId']:continue
        number=a[pid]['Pin Number'];name=a[pid].get('Pin Name','')
        row=next(p for p in pinrows if p['pin']==number)
        x,y=b['x'],b['y'];angle=math.radians(b['rotation'])
        ix=x+math.cos(angle)*b['length'];iy=y-math.sin(angle)*b['length']
        c.setStrokeColor(color);c.line(*xy(x,y),*xy(ix,iy))
        # Draw outward from the actual physical pin direction, not enumeration order.
        ox=-math.cos(angle);oy=math.sin(angle)
        ex=x+ox*25;ey=y+oy*25
        c.setStrokeColor(BLUE)
        if row['net']:c.line(*xy(x,y),*xy(ex,ey))
        else:
            px,py=xy(x,y);c.line(px-3,py-3,px+3,py+3);c.line(px-3,py+3,px+3,py-3)
        px,py=xy(x,y);nx,ny=xy(ex,ey)
        net=row['net'] or 'NC'
        if abs(ox)>.5:
            text(c,px,py+3,number,6,color,align='center')
            text(c,nx+(-3 if ox<0 else 3),ny-2,net,7,BLUE,align='right' if ox<0 else 'left')
            if isbox:
                tx,ty=xy(ix+(4 if ox<0 else -4),iy)
                text(c,tx,ty-2,name,6,color,align='left' if ox<0 else 'right')
            elif name not in (number,''):
                text(c,px+(5 if ox<0 else -5),py-8,name,6,color,align='right' if ox<0 else 'left')
        else:
            text(c,px+5,py-2,number+' '+name,6.5,color)
            text(c,nx,ny+(4 if oy<0 else -9),net,8,BLUE,align='center')
    val=at['Value'];size=9 if len(val)<33 else 7.5
    text(c,x0+12,top-height+25,val,size,color)
    text(c,x0+12,top-height+12,bomrow['封装/待确认'],7)


def main():
    import csv
    path=next((ROOT/'schematic/native').glob('*.eprj2'))
    meta,docs,_=read_project(path)
    _,pages,parts,pins=inventory(meta,docs,'G题同步Buck Rev C.2 原理图')
    with (ROOT/'schematic/BOM_RevC2.csv').open(encoding='utf-8-sig',newline='') as f:
        bom={r['位号']:r for r in csv.DictReader(f)}
    dest=ROOT/'schematic/previews/G题同步Buck完整原理图_RevC2.pdf'
    dest.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(dest),pagesize=(W,H))
    c.setTitle('G题同步Buck完整原理图 Rev C.2 — 引脚增强预览')
    text(c,40,H-55,'G题同步 Buck 完整原理图  Rev C.2',24)
    y=H-90
    notes=['修订日期：2026-10-27（北京时间）。基准：Rev C.1 原生工程及用户附件 RevC1_review.md。原 C.1 文件保留。', '本版：9页原理图、120项器件、51个网络、310个连接引脚。相对C.1不新增器件、不改任何阻容值或主板网络。', '已确认并修正PA5冲突：原始RevB图纸第7页已将LCD的SCK分配到PA5；本版J_MON.1由PA5改接PA6/ADC12_IN6，J_MON.2仍为GND。', 'LCD保留：SCK=PA5、MOSI=PA7、CS=PB12、DC=PB13、RST=PB14。PA6配置为模拟输入，不启用SPI1_MISO；检查控制板没有额外占用。', '同步范围：可编辑工程、符号脚名、J_MON值/描述、PDF、BOM、接线表及控制接口约束均改为PA6。TP14仍测ADC_VIN_POST，电气网络不改。', '保留下游VIN监测：VIN经100k/10k分压、1k串联、4.7nF对地和BAT54S钳位。VIN=11×ADC电压，25V对应2.273V；原ADC_VIN仍测VIN_EXT。', '保留C_IOUT_PROT=100nF/25V X7R，RC约100us。正常负载跳变仍可能触发U9B；PB11不得单边沿锁存。', '保护逻辑要求：持续输出告警20ms与持续低压短路20ms应分别判定。短路判据在启动完成且目标电压有效时启用，不依赖PB11告警先出现。', '电感过流/过压仍经FAULT_N硬件锁存。软件去抖不能延迟硬件保护；故障解除后由用户重新ARM。原理图不等于可烧录固件。', '预充仍需MCU_EN=0、等待至少100ms、核对下游VIN、人工闭合J_BYP，之后ARM。仅凭电压接近不能证明旁路触点已闭合。', 'QH：1G=G_H、2D=VIN、3S=SW；QL：1G=G_L、2D=SW、3S=GND。IR2184、门限、功率器件及全部C.1数值保持。', '验证边界：本版静态引脚/BOM检查已通过。没有客户端打开、ERC/PCB DRC、实际固件或实物测量；附件88%效率、3.08/4.40ms等数值未独立复现。', '配套Multisim同步情况、保护逻辑测试和模型边界见本版报告；功能等效模型不等于厂家模型或STM32固件。没有可用于生产的Rev C.2 PCB。']
    for note in notes:y=para(c,40,y,note,W-80,11,17)
    footer(c,1);c.showPage()
    rendered=[]
    ordered=sorted(pages,key=lambda u:pages[u]['META','META']['zIndex'])
    for pageno,page in enumerate(ordered,2):
        title=pages[page]['META','META']['title']
        text(c,30,H-38,title,18)
        text(c,30,H-58,'引脚增强预览 | 端点脚号/名称/网络均来自原生记录 | 红色为C.1→C.2改动',9)
        refs=[ref for ref,p in parts.items() if p['page']==page]
        refs.sort(key=lambda r:(parts[r]['body']['y'],parts[r]['body']['x']))
        rows=math.ceil(len(refs)/4);available=H-115
        if pageno==10:available=450
        cell_h=available/rows;cell_w=(W-60)/4
        for n,ref in enumerate(refs):
            part=parts[ref];pr=[p for p in pins if p['ref']==ref]
            draw_component(c,ref,part,docs[part['attrs']['Symbol']],pr,
                           30+(n%4)*cell_w,H-78-(n//4)*cell_h,cell_w,cell_h,bom[ref])
            rendered.extend({'ref':p['ref'],'pin':p['pin'],'net':p['net'],'name':p['name']} for p in pr)
        if pageno==10:
            y=H-560
            for note in notes[2:4]+notes[6:10]:y=para(c,40,y,note,W-80,11,17)
            para(c,40,y,'PA5保留LCD SCK；PA6/ADC12_IN6接收ADC_VIN_POST。不得将低压短路与PB11告警做AND判据；固件和真实板上响应仍需验证。',W-80,11,17)
        footer(c,pageno);c.showPage()
    c.save()
    assert len(rendered)==len(pins)
    (ROOT/'results/data/rendered_pin_map.json').write_text(json.dumps(rendered,ensure_ascii=False,indent=2)+'\n')
    print(dest)


if __name__=='__main__':main()
