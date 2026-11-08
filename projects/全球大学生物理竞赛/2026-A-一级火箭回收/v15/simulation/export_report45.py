from pathlib import Path
import subprocess
from docx import Document
from docx.shared import Pt,Cm
from docx.oxml.ns import qn
B=Path(__file__).resolve().parent.parent;R=B/'reports';stem='回收仿真_七机两段点火_γ45_CasADi修订'
subprocess.run(['pandoc',stem+'.md','-o',stem+'.docx','--resource-path=.','--standalone'],cwd=R,check=True)
p=R/(stem+'.docx');d=Document(p)
for st in d.styles:
 if st.type==1:
  st.font.name='Noto Sans CJK SC';st._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
d.styles['Normal'].font.size=Pt(10)
for sec in d.sections:sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.8);sec.left_margin=Cm(1.7);sec.right_margin=Cm(1.7)
for tab in d.tables:
 for row in tab.rows:
  for cell in row.cells:
   for para in cell.paragraphs:
    for run in para.runs:run.font.size=Pt(8)
d.save(p)
subprocess.run(['soffice','-env:UserInstallation=file:///tmp/upc_v15_export','--headless','--convert-to','pdf','--outdir',str(R),str(p)],check=True)
