"""Frequency sensitivity and longer settling windows, matching this run."""
from simulate import run, ROOT, DATA
import json

def main():
    r=[]
    for f in [50000,150000]:
        r.append(run('frequency_'+str(f),vin=25,load=8,freq=f))
    r.append(run('settled_15V_open',vin=15,load=1e12,stop=.08))
    r.append(run('settled_15V_20ohm',vin=15,load=20,stop=.08))
    r.append(run('settled_25V_20ohm',vin=25,load=20,stop=.08))
    (DATA/'sensitivity_summary.json').write_text(json.dumps(r,indent=2))

if __name__=='__main__':main()
