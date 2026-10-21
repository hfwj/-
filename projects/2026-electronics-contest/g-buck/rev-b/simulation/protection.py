"""DC SPICE verification of PDF reference dividers and comparator polarity."""
from simulate import ROOT,NG,NETLISTS,DATA,LOGS
import subprocess,json
import numpy as np

base='''* PDF reference network; ideal amplifier/comparator transfer only
Va a 0 3.3
R9 a pos 10k
R10a pos pm 33k
R10b pm 0 1k
R15a a nm 33k
R15b nm neg 1k
R16 neg 0 10k
R11 a ov 23k
R12 ov 0 10k
Vpull pull 0 3.3
R13 pull fault 10k
Bil il 0 V=1.65+0.5*V(itest)
R4 out div 10k
R5 div 0 1k
Bpos cp 0 V=V(il)-V(pos)
Bneg cn 0 V=V(neg)-V(il)
Bov co 0 V=V(div)-V(ov)
Sp fault 0 cp 0 CMP
Sn fault 0 cn 0 CMP
So fault 0 co 0 CMP
.model CMP SW(Ron=5 Roff=1e12 Vt=0 Vh=0)
'''

def main():
    result={}
    for mode,source,scan in [('current','Vi itest 0 0\nVo out 0 10','Vi -2.2 2.2 0.001'),
                              ('voltage','Vi itest 0 0\nVo out 0 0','Vo 0 12 0.001')]:
        net=NETLISTS/f'protection_{mode}.cir'
        data=DATA/f'protection_{mode}.txt'
        net.write_text(base+source+f'\n.control\nset wr_singlescale\nset wr_vecnames\ndc {scan}\nwrdata {data} v(fault) v(pos) v(neg) v(ov) v(il)\nquit\n.endc\n.end\n')
        p=subprocess.run([NG,'-b',str(net)],capture_output=True,text=True)
        (LOGS/f'protection_{mode}.log').write_text(p.stdout+p.stderr)
        assert p.returncode==0
        a=np.loadtxt(data,skiprows=1)
        ok=a[:,1]>2
        result[mode]={'healthy_min':float(a[ok,0].min()),'healthy_max':float(a[ok,0].max()),
           'ref_pos':float(a[0,2]),'ref_neg':float(a[0,3]),'ref_ov':float(a[0,4]),'points':len(a)}
    # Exhaustive ideal logic truth-table test of specified latch/enabling behavior.
    rows=[]
    for q in [0,1]:
        for fault_n in [0,1]:
            for arm_edge in [0,1]:
                for en in [0,1]:
                    qnext=0 if not fault_n else (1 if arm_edge else q)
                    drv=qnext & en
                    assert (not fault_n and drv==0) or fault_n
                    assert en or drv==0
                    rows.append([q,fault_n,arm_edge,en,qnext,drv])
    result['ideal_latch_truth_table_cases']=len(rows)
    (DATA/'latch_truth_table.csv').write_text('q,fault_n,arm_rising,mcu_en,qnext,drv_en\n'+'\n'.join(','.join(map(str,r)) for r in rows)+'\n')
    (DATA/'protection_summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
