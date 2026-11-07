"""Rerun historical verification in a temporary copy; optional full IPOPT solve."""
from audit import ROOT,SOURCE
from pathlib import Path
import sys,numpy as np,json,tempfile,shutil,subprocess,argparse,time
sys.path.insert(0,str(SOURCE/'simulation'))
from replay_candidate import replay
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--optimizer',action='store_true');args=parser.parse_args();out=ROOT/'results/data'
 p=dict(np.load(SOURCE/'results/data/controls_N320.npz'));p['U1'][-1]+=2*np.pi;p['U2'][-1]+=2*np.pi
 with tempfile.TemporaryDirectory() as td:
  q=Path(td)/'invalid_beta.npz';np.savez(q,**p);z,_=replay(q,.2)
  report=dict(mutation='add 2pi to both phase beta arrays, outside declared +/-pi/2',old_checker_M0_subset_pass=z['M0_subset_pass'],beta_max_deg=float(np.degrees(max(p['U1'][-1].max(),p['U2'][-1].max()))),meaning='Input guard omission. Nominal delivered controls unchanged; periodic force direction alone cannot enforce declared control bounds.')
  (out/'old_checker_negative_test.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
 with tempfile.TemporaryDirectory() as td:
  dst=Path(td)/'v8';shutil.copytree(SOURCE,dst,ignore=shutil.ignore_patterns('downloads','__pycache__'))
  cp=subprocess.run([sys.executable,str(dst/'simulation/verify.py')],capture_output=True,text=True);print(cp.stdout,cp.stderr);assert cp.returncode==0
  shutil.copy(dst/'results/data/verification.json',out/'original_verification_rerun.json')
 if args.optimizer:
  from solve_candidate import solve
  warm=dict(np.load(SOURCE/'results/data/controls_N160.npz'));baseline=dict(np.load(SOURCE/'results/data/controls_N320.npz'));t=time.monotonic();z=solve(320,warm,40);elapsed=time.monotonic()-t
  np.savez(out/'reproduced_controls_N320.npz',**z)
  report=dict(elapsed_s=elapsed,initial_propellant_kg=(z['m0']-130)*1000,initial_propellant_difference_kg=(z['m0']-float(baseline['m0']))*1000,final_time_difference_s=z['tf']-float(baseline['tf']),shutdown_time_difference_s=z['toff']-float(baseline['toff']),max_state_control_node_absolute_difference_mixed_solver_units=float(max(np.max(abs(z[k]-baseline[k])) for k in ['U1','U2','X1','X2'])))
  assert abs(report['initial_propellant_difference_kg'])<1
  (out/'optimizer_reproduction.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
