from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
im=np.asarray(Image.open(root/'results/figures/source14.png').convert('RGB'))
# Original plot coordinates measured on the 1800-pixel reference preview.
sx=im.shape[1]/1800; sy=im.shape[0]/543
fig,axs=plt.subplots(1,3,figsize=(13.8,4.8));fig.subplots_adjust(left=.06,right=.94,bottom=.29,top=.85,wspace=.63)
colors={'blue':'#1f4e79','red':'#b03a2e','green':'#2e7d32'}
records=[]
def trace(ax,box,xlim,ylim,color,log=False,exclude=None):
 x0,y0,x1,y1=[int(round(v*(sx if i%2==0 else sy))) for i,v in enumerate(box)]
 a=im[y0:y1,x0:x1].astype(float);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
 mask={'blue':(b>r*1.30)&(b>g*1.08)&(r<170),'red':(r>g*1.5)&(r>b*1.25)&(g<180),'green':(g>r*1.35)&(g>b*1.15)&(r<170)}[color]
 if exclude:
  for ex in exclude:
   ex0,ey0,ex1,ey1=ex;mask[max(0,int(ey0*sy)-y0):min(y1-y0,int(ey1*sy)-y0),max(0,int(ex0*sx)-x0):min(x1-x0,int(ex1*sx)-x0)]=False
 yy,xx=np.where(mask);x=xlim[0]+xx/(x1-x0)*(xlim[1]-xlim[0]);q=1-yy/(y1-y0)
 y=10**(np.log10(ylim[0])+q*np.log10(ylim[1]/ylim[0])) if log else ylim[0]+q*(ylim[1]-ylim[0])
 ax.scatter(x,y,s=.10,color=colors[color],rasterized=True,linewidths=0)
 records.append({'panel':len(records),'color':color,'pixels':len(x),'interpolation':False})
for ax in axs:ax.grid(alpha=.22);ax.set_xlabel('Time after separation (s)');ax.tick_params(labelsize=9)
a=axs[0];a.set(xlim=(-5,101),ylim=(-9,189),ylabel='Rotation angle (deg)',title='(a) RCS reorientation');trace(a,(101,49,547,457),(-5,101),(-9,189),'blue')
ar=a.twinx();ar.set(ylim=(-.18,3.87),ylabel='Angular rate (deg/s)');trace(ar,(101,49,547,457),(-5,101),(-.18,3.87),'red');ar.tick_params(labelsize=9)
a=axs[1];a.set(xlim=(245,379),ylim=(-48,2),ylabel='Thrust angle (deg)',title='(b) Powered-flight direction');trace(a,(717,49,1162,457),(245,379),(-48,2),'blue')
ar=a.twinx();ar.set(ylim=(-3,3),ylabel='Direction rate (deg/s)');trace(ar,(717,49,1162,457),(245,379),(-3,3),'red');ar.tick_params(labelsize=9)
a.text(.5,-.27,'Unpowered coast between burns\n(no thrust direction)',transform=a.transAxes,ha='center',fontsize=8)
a=axs[2];a.set(xlim=(-20,390),ylim=(1,1e8),ylabel='Moment (N m)',title='(c) Moment scales');a.set_yscale('log')
for c,label,ls in [('green','Aerodynamic','-'),('red',r'TVC ($5^\circ$)','--'),('blue','Grid fins',':')]:
 trace(a,(1332,49,1779,457),(-20,390),(1,1e8),c,True,exclude=[(1572,380,1763,447)])
 a.plot([],[],color=colors[c],ls=ls,label=label)
a.legend(loc='upper center',bbox_to_anchor=(.5,-.22),frameon=False,fontsize=8,ncol=1)
fig.savefig(root/'results/figures/attitude_relayout.pdf');fig.savefig(root/'results/figures/attitude_relayout.png',dpi=180)
import json
(root/'results/data/attitude_relayout_provenance.json').write_text(json.dumps({'source':'source14.png','method':'Colored source pixels mapped to the original axes; no new simulation, no bridging of gaps. Original legend footprint excluded; obscured data are not reconstructed.','traces':records},indent=2))
