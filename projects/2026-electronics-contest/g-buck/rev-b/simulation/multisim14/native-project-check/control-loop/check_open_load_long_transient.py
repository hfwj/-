"""Cross-solver100ms diagnostic only; does not model rated-fuse behavior or edit native projects."""
from pathlib import Path
import sys,hashlib,json,os,subprocess,tempfile
import numpy as np
H=Path(__file__).resolve().parent.parent;C=H/'control-loop';sys.path[:0]=[str(H),str(C)]
from build_projects import extract_netlist,PROJECT
from verify_driver import NG
src=PROJECT/'references/user-projects/2026-10-24_15V空载_恢复F1_本机回传.ms14'
s=extract_netlist(src);assert s.count('.tran 50n 30m 0 50n')==1;s=s.replace('.tran 50n 30m 0 50n','.tran 50n 100m 0 50n')
with tempfile.TemporaryDirectory(prefix='gbuck-long-') as td:
 w=Path(td);init=w/'init';init.mkdir();lib=NG.parent.parent/'lib/x86_64-linux-gnu/ngspice'
 (init/'spinit').write_text('\n'.join('codemodel '+str(lib/n) for n in ['analog.cm','digital.cm','spice2poly.cm','xtradev.cm','xtraevt.cm','table.cm'])+'\n')
 raw=w/'trace.txt';net=w/'test.cir';net.write_text(s+f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(4) i(l1) v(xctrl.iref) v(xctrl.ilf) v(xctrl.duty) v(3)\nquit\n.endc\n.end\n')
 try:
  p=subprocess.run([str(NG),'-D','ngbehavior=psa','-b',str(net)],env=dict(os.environ,SPICE_SCRIPTS=str(init)),capture_output=True,text=True,timeout=300)
 except subprocess.TimeoutExpired as exc:
  from types import SimpleNamespace
  def decoded(value): return value.decode(errors='replace') if isinstance(value,bytes) else (value or '')
  p=SimpleNamespace(returncode=None,stdout=decoded(exc.stdout),stderr=decoded(exc.stderr)+'\nERROR: diagnostic exceeded300s wall-time budget; not a demonstrated convergence failure\n')
 log=p.stdout+p.stderr;(C/'results/logs/CV_15V_OPEN_100ms_diagnostic.log').write_text(log)
 a=np.loadtxt(raw,skiprows=1) if raw.exists() else np.empty((0,7))
err=[l for l in log.splitlines() if any(x in l.lower() for x in ['error:','too small','aborted'])]
r={'date':'2026-10-24','source_project':str(src.relative_to(PROJECT)),'source_project_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'solver_source_sha256':hashlib.sha256(s.encode()).hexdigest(),'solver':'ngspice44.2/psa','analysis_change':'TSTOP 30ms to 100ms only; native file unchanged','fuse_model':'Fixed 1mOhm conducting resistor; rated fuse behavior not simulated','full_transient_completed':bool(p.returncode==0 and len(a)>1000 and a[-1,0]>=.1*.999 and not err),'actual_end_time_s':float(a[-1,0]) if len(a) else None,'failure_messages':err,'data_rows':len(a),'native_multisim_execution_performed':False,'numeric_native_export_received':False}
if len(a):
 assert np.isfinite(a).all();take=np.unique(np.r_[np.arange(0,len(a),max(1,len(a)//6000)),len(a)-1]);np.savetxt(C/'results/data/CV_15V_OPEN_100ms_diagnostic_sampled.csv',a[take],delimiter=',',header='time_s,VOUT_V,IL_A,IREF_A,IL_FILTERED_A,DUTY,VCAP_V',comments='')
 r['late_20ms_windows']=[]
 for start in [.04,.06,.08]:
  b=a[(a[:,0]>=start)&(a[:,0]<=start+.02)];r['late_20ms_windows'].append({'time_s':[start,start+.02],'VOUT_range_V':[float(b[:,1].min()),float(b[:,1].max())],'VOUT_mean_V':float(np.trapezoid(b[:,1],b[:,0])/(b[-1,0]-b[0,0])),'IREF_range_A':[float(b[:,3].min()),float(b[:,3].max())]})
(C/'results/data/CV_15V_OPEN_100ms_diagnostic.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
