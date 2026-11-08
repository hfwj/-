"""One-command reconstruction of the new model's tables and figures.
Usage: python simulation/reproduce.py [--latex]
Requires Python, numpy, scipy, matplotlib, and g++.
Only --latex additionally requires XeLaTeX and latexmk.
"""
from pathlib import Path
import argparse,subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
SIM=ROOT/'simulation'

def execute(name):
    logs=ROOT/'results/logs';logs.mkdir(parents=True,exist_ok=True)
    print('Running',name,flush=True)
    with (logs/(name.replace('.py','')+'.log')).open('w') as f:
        subprocess.run([sys.executable,str(SIM/name)],cwd=SIM,
                       stdout=f,stderr=subprocess.STDOUT,check=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--latex',action='store_true')
    args=parser.parse_args()
    for relative in ['results/data','results/figures','results/logs','reports/latex/code']:
        (ROOT/relative).mkdir(parents=True,exist_ok=True)
    # No input data are taken from the previous manuscript.
    for name in ['search.py','analyze.py','sensitivity.py','publish.py']:
        execute(name)
    r=json.loads((ROOT/'results/data/selected.json').read_text())
    assert r['pass']==1.0
    checks=json.loads((ROOT/'results/data/verification.json').read_text())
    assert checks['all_three_steps_pass']
    print('Selected load (t):',r['load_t'])
    print('Consumed propellant (kg):',r['used_kg'])
    if args.latex:
        directory=ROOT/'reports/latex'
        subprocess.run(['latexmk','-xelatex','-interaction=nonstopmode',
                        '-halt-on-error','-outdir=build','main.tex'],
                       cwd=directory,check=True)
        import shutil
        shutil.copy2(directory/'build/main.pdf',ROOT/'reports/856A.pdf')
        execute('validate.py')
    # Numerical identity checks do not certify flight hardware.
    print('Reconstruction complete; see JSON/CSV and execution logs.')

if __name__=='__main__':main()
