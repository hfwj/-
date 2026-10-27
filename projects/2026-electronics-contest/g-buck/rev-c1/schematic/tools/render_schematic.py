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
CHANGED={'QH','QL','J_CTL','C_IOUT_PROT','R_VINP_TOP','R_VINP_BOT','R_VINP_ADC',
         'C_VINP_ADC','D_ADC6','J_MON','TP14'}


def safe(s):return str(s).replace('µ','u')


def text(c,x,y,s,size=9,color=INK,align='left'):
    c.setFillColor(color);c.setFont('STSong-Light',size)
    getattr(c,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,y,safe(s))


def para(c,x,y,s,width,size=11,leading=18):
    style=ParagraphStyle('p',fontName='STSong-Light',fontSize=size,leading=leading,textColor=INK,wordWrap='CJK')
    p=Paragraph(escape(safe(s)),style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h-10


def footer(c,page):
    c.setStrokeColor(colors.HexColor('#ced7df'));c.line(30,35,W-30,35)
    text(c,30,21,'Rev C.1 | 原生记录增强预览（非EDA客户端导出）| 同名网络跨页相连 | 未运行客户端ERC/PCB DRC',8)
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
    _,pages,parts,pins=inventory(meta,docs,'G题同步Buck Rev C.1 原理图')
    with (ROOT/'schematic/BOM_RevC1.csv').open(encoding='utf-8-sig',newline='') as f:
        bom={r['位号']:r for r in csv.DictReader(f)}
    dest=ROOT/'schematic/previews/G题同步Buck完整原理图_RevC1.pdf'
    dest.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(dest),pagesize=(W,H))
    c.setTitle('G题同步Buck完整原理图 Rev C.1 — 引脚增强预览')
    text(c,40,H-55,'G题同步 Buck 完整原理图  Rev C.1',24)
    y=H-90
    notes=[
        '修订日期：2026-10-27（北京时间）。基准：Rev C 可编辑工程及 2026-10-27 附件复核报告。原 Rev C 文件保留。',
        '本版包含 9 页可编辑原理图、120 项主板器件、51 个网络、310 个连接引脚；后附图逐引脚来自交付 .eprj2 活动记录。',
        'QH/QL：保留 IRF540N 及原有正确连接；QH：1G=G_H、2D=VIN、3S=SW；QL：1G=G_L、2D=SW、3S=GND。符号显示 G/D/S 与脚号。',
        'J_CTL.6：脚名由 GND 修正为 PB11/OC#，网络仍为 IOUT_OC_N。现有 Rev C 电气网络不变；Rev B 的旧 GND 排线不得直接沿用。',
        'C_IOUT_PROT：1 nF/C0G 改为 100 nF/25 V X7R，封装 C0805；与 1 kΩ 组成约 100 us RC。U9B 仍只告警，不接 FAULT_N；不能替代软件判据。',
        '新增下游 VIN 监测：VIN → 100 kΩ → VIN_POST_DIV → 10 kΩ → GND；经 1 kΩ 到 ADC_VIN_POST，4.7 nF 对地，BAT54S 钳位到 GND/+3V3_A。',
        '新增 J_MON：1=ADC_VIN_POST 接 STM32 PA5/ADC，2=GND；新增 TP14。VIN=11×该 ADC 电压，25 V 时约 2.273 V；原 ADC_VIN 继续测 VIN_EXT。',
        '预充仍为人工流程：MCU_EN=0，预充至少 100 ms，核对下游 VIN，人工闭合 J_BYP 后才 ARM。VIN 电压相近不能单独证明旁路触点已闭合。',
        '固件接口要求（尚未实现）：PB11 不允许单边沿故障锁存；启动完成且目标有效时独立判断持续低压短路；故障解除后人工重新 ARM。不可仅用 >1.1 A 检测 1 A 恒流短路。',
        '影响：新增 7 项器件、替换 1 项电容，并新增控制板两线连接；需要同步原理图/PCB。现有 Multisim Rev C 工程未更新，不能当作 Rev C.1 动态验证。',
        '验证：已做原生历史重放、全部引脚和新增支路核对、BOM 一致性、器件/符号/封装关联核对。未做客户端打开、EDA ERC、PCB DRC、固件或硬件实测；整机 85% 效率未验收。',
        '封装与投板：R_PRE 仍须选定实际功率/脉冲电阻及封装；端子、电感、电解电容等机械 TBD 项仍须核实。没有本版可用于生产的 PCB。',
        '读图：蓝色为网络名称，红色为本轮改动或新增器件。所有网络标签均按实际脚号和几何端点生成，不凭符号上下位置推测连接。',
    ]
    for note in notes:y=para(c,40,y,note,W-80,11,17)
    footer(c,1);c.showPage()
    rendered=[]
    ordered=sorted(pages,key=lambda u:pages[u]['META','META']['zIndex'])
    for pageno,page in enumerate(ordered,2):
        title=pages[page]['META','META']['title']
        text(c,30,H-38,title,18)
        text(c,30,H-58,'引脚增强预览 | 端点脚号/名称/网络均来自原生记录 | 红色为Rev C→C.1改动',9)
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
            for note in notes[5:9]:y=para(c,40,y,note,W-80,11,17)
            para(c,40,y,'此页分压监测的是 VIN（D1/RS_IN 后），并不新增自动旁路执行器。PA5 必须核实未被控制板其他外设占用，ADC采样与标定须由固件实现。',W-80,11,17)
        footer(c,pageno);c.showPage()
    c.save()
    assert len(rendered)==len(pins)
    (ROOT/'results/data/rendered_pin_map.json').write_text(json.dumps(rendered,ensure_ascii=False,indent=2)+'\n')
    print(dest)


if __name__=='__main__':main()
