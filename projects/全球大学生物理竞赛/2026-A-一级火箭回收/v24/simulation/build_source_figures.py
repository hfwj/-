from pathlib import Path
import json,re,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,colors
B=Path(__file__).resolve().parent.parent;F=B/'results/figures';s=json.load(open(B/'results/data/source_tables.json'))
font_manager.fontManager.addfont('/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf');plt.rcParams.update({'font.family':'Latin Modern Roman','mathtext.fontset':'cm','font.size':10,'axes.labelsize':10,'xtick.labelsize':8,'ytick.labelsize':9,'pdf.fonttype':42,'axes.linewidth':.7})
def save(n):plt.tight_layout();plt.savefig(F/(n+'.pdf'),bbox_inches='tight');plt.savefig(F/(n+'.png'),bbox_inches='tight',dpi=220);plt.close()
# Only discrete values explicitly supplied in the Word table are plotted.
f=lambda x:float(re.search(r'-?\d+(?:\.\d+)?',x).group())
x=np.arange(5);names=['v3-I: ideal','v3-A: area','v4-R: response\n+ staging','v4-F: final',r'v4-L: $\tau=3$ s'];fig,axs=plt.subplots(1,2,figsize=(7,3.5))
for ax,col,title in [(axs[0],1,'(a) Initial propellant: 110 t'),(axs[1],2,'(b) Initial propellant: 120 t')]:
 vals=[f(r[col]) for r in s[18][1:]];ax.bar(x,vals,color=['#8da0cb','#66c2a5','#fc8d62','#3288bd','#c7a76c'],width=.64)
 for xx,yy in zip(x,vals):ax.text(xx,yy+.07,f'{yy:.1f}',ha='center',fontsize=8)
 ax.set_xticks(x,names,rotation=25,ha='right');ax.set_ylim(min(vals)-1,max(vals)+.8);ax.set_ylabel('Reported propellant consumed (t)');ax.set_title(title,loc='left',fontsize=10);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
save('source_ablation')
fig,ax=plt.subplots(figsize=(7,2.9));ys=[2,1,0];nominal=[104,96,102]
for y,v in zip(ys,nominal):ax.plot(v,y,'o',color='#0072B2',ms=6);ax.text(v-1.4,y-.21,str(v),ha='right',fontsize=9)
ax.plot(120,2,'D',color='#D55E00',ms=6);ax.text(120.8,2.05,'120 t',fontsize=9);ax.plot(110,1,'D',color='#D55E00',ms=6);ax.text(110.8,1.05,'110 t',fontsize=9);ax.plot([110,112],[0,0],color='#D55E00',lw=3);ax.plot([110,112],[0,0],'|',color='#D55E00',ms=12);ax.text(113,.05,'110--112 t',fontsize=9)
ax.set_yticks(ys,['v1-B: baseline','v3-P: parameterized','v4-F: final combined']);ax.set(xlim=(92,125),ylim=(-.55,2.55),xlabel='Initial total propellant (t)');ax.plot([],[],'o',color='#0072B2',label='Lowest reported nominal pass');ax.plot([],[],'D',color='#D55E00',label='Reported recommendation');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.27),ncol=2,fontsize=8);ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.2);save('source_load_summary')
fig,axs=plt.subplots(1,2,figsize=(7,3.4),gridspec_kw={'width_ratios':[6,5]});cmap=colors.ListedColormap(['#f5b7b1','#a9dfbf'])
for ax,idx,heads,title in [(axs[0],5,['Nominal',r'$C_D-15\%$',r'$C_D-20\%$',r'$I_{sp}-2\%$','Wind x3','Combined'],'(a) v1-B: baseline guidance'),(axs[1],16,['Nominal',r'$C_D-15\%$',r'$C_D-20\%$',r'$I_{sp}-2\%$','Combined'],'(b) v3-P: parameterized guidance')]:
 rows=s[idx][1:];a=np.array([[1 if c.startswith('✓') else 0 for c in r[1:]] for r in rows]);ax.imshow(a,cmap=cmap,vmin=0,vmax=1,aspect='auto')
 for i in range(a.shape[0]):
  for j in range(a.shape[1]):ax.text(j,i,'P' if a[i,j] else 'F',ha='center',va='center',fontsize=10)
 ax.set_xticks(range(len(heads)),heads,rotation=40,ha='right');ax.set_yticks(range(len(rows)),[r[0] for r in rows]);ax.set_ylabel('Initial load');ax.set_title(title,loc='left',fontsize=10)
save('source_perturbation_matrix');print('Generated 3 new vector charts solely from source tables/paragraphs; no time histories synthesized.')
