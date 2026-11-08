"""Build/load the C++ RK4 model. All environmental assumptions are explicit."""
from pathlib import Path
import ctypes as ct
import hashlib,json,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SIM=ROOT/'simulation'
CONFIG=json.loads((SIM/'config.json').read_text())
KEYS=['pass','used_kg','entry_kg','landing_kg','vx_mps','vz_mps','qmax_pa','nmax','tilt_deg','contact_s','range_m','apogee_m','residual_kg','contact_event','touch_s','exhaust_s','entry_request_s','entry_start_s','entry_cut_s','landing_request_s','landing_start_s','stage3_s','stage2_s','entry_peak_N','landing_peak_N','entry_impulse_x_Ns','entry_impulse_z_Ns','landing_impulse_x_Ns','landing_impulse_z_Ns','steps','q_override_on_s','q_override_off_s']
COLUMNS=['t','s','h','u','w','m','phi','throttle','q','n','T','phase','engines','Fx_aero','Fz_aero','area','drag_loading','Vg']
def build():
    header=[]
    for k,v in CONFIG.items():
        if isinstance(v,(int,float)):header.append(f'constexpr double {k}={repr(float(v))};')
        elif isinstance(v,list):header.append('constexpr double '+k+'[]={'+', '.join(repr(float(x)) for x in v)+'};')
    (SIM/'config.h').write_text('\n'.join(header)+'\n')
    digest=hashlib.sha256((SIM/'core.cpp').read_bytes()+(SIM/'config.h').read_bytes()).hexdigest()
    if not (SIM/'core.so').exists() or not (SIM/'build.sha256').exists() or (SIM/'build.sha256').read_text()!=digest:
        subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(SIM/'core.cpp'),'-o',str(SIM/'core.so')],check=True)
        (SIM/'build.sha256').write_text(digest)
    lib=ct.CDLL(str(SIM/'core.so'));fn=lib.simulate
    ptr=ct.POINTER(ct.c_double)
    fn.argtypes=[ct.c_double,ptr,ct.c_double,ct.c_int,ptr,ptr,ct.c_int];fn.restype=ct.c_int
    return fn
_FN=build()
def run(propellant_t,parameters=(60000.,1100.,1.2,1.5),dt=.02,mode=1,history=False):
    if dt<=0 or propellant_t<=0:raise ValueError('Positive load and step required')
    p=np.ascontiguousarray(parameters,dtype=float);out=np.zeros(32)
    h=np.empty((200000,18)) if history else np.empty((0,18))
    ptr=lambda a:a.ctypes.data_as(ct.POINTER(ct.c_double))
    n=_FN(propellant_t*1000.,ptr(p),dt,mode,ptr(out),ptr(h) if history else None,len(h))
    result={k:float(v) for k,v in zip(KEYS,out)}
    result.update(load_t=float(propellant_t),parameters=p.tolist(),dt=float(dt),mode=int(mode))
    return (result,h[:n].copy()) if history else result
if __name__=='__main__':
    frozen=ROOT/'results/data/selected.json'
    if not frozen.exists():
        raise SystemExit('First run simulation/reproduce.py')
    case=json.loads(frozen.read_text())
    print(json.dumps(run(case['load_t'],case['parameters'],dt=.005),indent=2))
