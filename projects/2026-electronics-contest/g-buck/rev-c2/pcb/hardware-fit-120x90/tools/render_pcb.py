"""Render actual delivered native pads, outlines and copper; not an EDA screenshot."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/gbuck-pcb-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon, Circle
from matplotlib.backends.backend_pdf import PdfPages
from pcb_common import *

def main():
    manifest=json.loads((ROOT/'data/build_manifest.json').read_text())
    meta,docs,_=read_project(PATH)
    parts,pads,bodies,tracks=copper_geometry(meta,docs,manifest['pcb'])
    vias=copper_vias(docs,manifest['pcb'])
    def draw(ax,limits=(0,120,0,90),dark=True):
        bg='#092f2b' if dark else 'white';ax.set_facecolor(bg)
        ax.add_patch(plt.Rectangle((0,0),120,90,fill=False,edgecolor='#90dbbb' if dark else '#144d39',linewidth=1.5))
        for b in bodies:
            col='#ffb457' if manifest['parts'][b['ref']]['mechanical_TBD'] else '#71bba6'
            ax.add_patch(PatchPolygon(list(b['geometry'].exterior.coords),fill=False,edgecolor=col,linewidth=.6))
        for t in tracks:
            g=t['geometry'];ax.add_patch(PatchPolygon(list(g.exterior.coords),color='#ed6d63' if t['layer']==1 else '#6da9ff',linewidth=0))
        for v in vias:
            ax.add_patch(Circle((v['x'],v['y']),v['diameter']/2,color='#6da9ff'))
            ax.add_patch(Circle((v['x'],v['y']),v['hole_diameter']/2,color='#071b19'))
        for p in pads:
            ax.add_patch(PatchPolygon(list(p['geometry'].exterior.coords),color='#e8c879',linewidth=0))
            if p['hole']:
                diameter=min(p['hole']['width'],p['hole']['height'])*.0254
                ax.add_patch(Circle((p['x'],p['y']),diameter/2,color='#071b19'))
        for ref,(cid,c,a) in parts.items():
            x,y=c['x']*.0254,c['y']*.0254
            ax.text(x,y+1.1,ref,color='#f4f6df' if dark else '#172d24',ha='center',va='bottom',fontsize=5.3)
        for x,y in manifest['mounting_holes_mm']:
            ax.add_patch(Circle((x,y),1.6,facecolor='#202a2d',edgecolor='#b3b3b3',linewidth=.5))
            ax.add_patch(Circle((x,y),3.1,fill=False,edgecolor='#9eaaa4',linestyle='--',linewidth=.4))
        ax.set(xlim=limits[:2],ylim=limits[2:],xlabel='mm',ylabel='mm',aspect='equal')
        ax.grid(alpha=.15,linewidth=.3)
    fig,ax=plt.subplots(figsize=(13,10));draw(ax)
    fig.suptitle('G BUCK Rev C.2 | 120 x 90 mm | PCB review',fontsize=17)
    ax.set_title('Native-record render | 120 components | partial local routes | NOT FOR FAB',fontsize=10)
    fig.text(.09,.035,'Orange: mechanical TBD. Red: top copper. Blue: bottom copper / vias. Power / Kelvin / ground fill incomplete.',fontsize=9)
    fig.tight_layout(rect=(0,.06,1,.94))
    fig.savefig(ROOT/'previews/PCB_RevC2_120x90.png',dpi=190)
    with PdfPages(ROOT/'previews/PCB_RevC2_review.pdf') as pdf:
        pdf.savefig(fig)
        for title,limits in [('Power and drive: geometry and routing remain provisional',(32,120,47,90)),
                             ('Control / protection / ADC: PA6 monitor interface',(14,120,4,48))]:
            f,a=plt.subplots(figsize=(13,8));draw(a,limits)
            f.suptitle(title);f.text(.1,.02,'Review draft; native desktop open / ERC / DRC not run. This is not a production drawing.',fontsize=9)
            f.tight_layout(rect=(0,.04,1,.94));pdf.savefig(f);plt.close(f)
    plt.close(fig)
    # 1:1 A4 footprint review sheet. Coordinates use true mm on a 210x297 mm page.
    with PdfPages(ROOT/'previews/Footprint_1to1_CHECK_ONLY.pdf') as pdf:
        f=plt.figure(figsize=(210/25.4,297/25.4));ax=f.add_axes([0,0,1,1]);ax.set(xlim=(0,210),ylim=(0,297),aspect='equal');ax.axis('off')
        ax.text(15,281,'FOOTPRINT CHECK ONLY - PRINT 100% / ACTUAL SIZE',fontsize=11,weight='bold')
        ax.text(15,272,'Measure the 50 mm scale below. Do not use this draft to drill or manufacture.',fontsize=8)
        ax.plot([15,65],[261,261],color='black',linewidth=.6)
        for x in [15,25,35,45,55,65]:ax.plot([x,x],[259,263],color='black',linewidth=.6)
        ax.text(15,254,'50 mm',fontsize=8)
        items=[('F1',55,222),('L1',133,222),('C1',45,170),('J1',100,170),('RS_IN',150,170),('U1',45,115),('D1',96,115),('RS_L',150,115)]
        for ref,x,y in items:
            spec=manifest['specs'][manifest['parts'][ref]['package']];w,h=spec['body_mm']
            ax.add_patch(plt.Rectangle((x-w/2,y-h/2),w,h,fill=False,color='black',linewidth=.5))
            for p in spec['pads']:
                ax.add_patch(plt.Rectangle((x+p['x']-p['w']/2,y+p['y']-p['h']/2),p['w'],p['h'],fill=False,color='black',linewidth=.5))
                if p['hole']:
                    if p.get('slot'):
                        hw=p.get('hole_w',p['slot']);hh=p.get('hole_h',p['hole'])
                        ax.add_patch(plt.Rectangle((x+p['x']-hw/2,y+p['y']-hh/2),hw,hh,fill=False,color='black',linewidth=.4))
                    else:ax.add_patch(Circle((x+p['x'],y+p['y']),p['hole']/2,fill=False,color='black',linewidth=.4))
                ax.text(x+p['x'],y+p['y']+p['h']/2+1,p['num'],ha='center',fontsize=6)
            ax.text(x,y-h/2-5,ref+' '+manifest['parts'][ref]['package'],ha='center',fontsize=7)
            if spec['tbd']:ax.text(x,y-h/2-10,('P10 FROM SELLER; ENVELOPE STILL TBD' if ref=='RS_IN' else 'P5 FROM SELLER; ENVELOPE STILL TBD' if ref=='RS_L' else 'PROVISIONAL - MEASURE ACTUAL PART'),ha='center',fontsize=6,color='#aa2222')
        ax.text(15,76,'F1: 5x20 fuse; confirmed clip P5.66. Assembly centers 15mm are a DESIGN TRIAL - FIT FIRST.',fontsize=7)
        ax.text(15,68,'Seller pitch: RS_IN/OUT 50mOhm P10, wire D0.8; RS_L 25mOhm P5, wire D0.7.',fontsize=7)
        ax.text(15,60,'L1: vertical mounting; footprint 20 x 10 mm. Horizontal mounting needs a 20 x 20 mm area.',fontsize=7)
        ax.text(15,52,'C1/C3: P5, D10 body; drawing reserves D10.5 maximum. J1/J2: P2.54, hole 1.3.',fontsize=7)
        ax.text(15,37,'NOT FOR FABRICATION - native ERC / DRC and real part fit checks remain open.',fontsize=9,weight='bold')
        pdf.savefig(f);plt.close(f)
    print('Rendered native-record overview, detail PDF and 1:1 footprint check sheet.')

if __name__=='__main__':main()
