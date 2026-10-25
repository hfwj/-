"""Independent coupled A/B check. Native F1 thermal behavior is NOT simulated."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_step02 import SOURCE, DEST, aliases
from ms14_project import unpack, parse, components, elements, clean
from verify_driver import NG, ngspice_compat
from verify_coupled import read_raw, value


def extract(path, stop, step):
    root = parse(unpack(path.read_bytes())[0])
    amap = aliases(root)
    models = elements(root, 'CiModel')
    objects = {clean(c.get('LocalName')): c for c in elements(root, 'CiComponent').values()}
    lines = ['* STEP02 coupled diagnostic; F1 is a fixed 1mOhm ONLY in this cross-solver test']
    for part in components(root):
        name, params = part['display_ref'], part['parameters']
        ports = {k: amap.get(n, n) if n is not None else 'NC_' + name + '_' + k
                 for k, n in part['ports'].items()}
        model = clean(models[part['model_id']].get('LocalName')) if part['model_id'] else ''
        if name == 'V3':
            line = clean(objects[part['internal_ref']].find('.//CiaSpiceTmpltExprt').get('String'))
            line = line.replace('%t1', ports['1']).replace('%t2', ports['2'])
        elif name == 'F1':
            line = f'R_SIM_FUSE {ports["1"]} {ports["2"]} 1m'
        elif name[0] in 'RCL':
            line = f'{name} {ports["1"]} {ports["2"]} {value(params[1])}'
        elif name in ['V1', 'V2', 'V_EN', 'SIM_3V3']:
            line = f'V_{name} {ports["1"]} {ports["2"]} {value(params[1])}'
        elif name in ['Q1', 'Q2']:
            line = 'X' + name + ' ' + ' '.join(ports[k] for k in ['D', 'G', 'S']) + ' ' + model
        elif name == 'U1':
            line = 'XU1 ' + ' '.join(ports[k] for k in ['VCC', 'IN', '^SD', 'COM', 'VB', 'HO', 'VS', 'LO']) + ' ' + model
        elif name in ['U2', 'U3', 'U4']:
            pins = range(1, 7 if name == 'U3' else 9)
            line = 'X' + name + ' ' + ' '.join(ports[str(k)] for k in pins) + ' ' + model
        elif name == 'D1':
            line = f'XD1 {ports["A"]} {ports["K"]} {model}'
        elif name == 'D_BOOT':
            line = f'D_BOOT {ports["A"]} {ports["K"]} {model}'
        else:
            raise ValueError(name)
        lines.append(line)
    lines += [clean(m.find('.//CiaCString').get('String')) for m in models.values()]
    lines += ['.options reltol=.003 abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=100 rshunt=1e12 method=trap',
              '.save v(VOUT) v(VDDA) v(IOUT_RAW) v(IL_BI) i(L1) v(xctrl.ilraw) v(V_CAP) v(6) v(7)',
              f'.tran 50n {stop} 0 {step}', '.end']
    return ngspice_compat('\n'.join(lines) + '\n')


def run(case, path, stop, step):
    source = extract(path, stop, step)
    logpath = ROOT / 'results/logs' / (case + '.log')
    logpath.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='step02-') as folder:
        work = Path(folder)
        lib = NG.parent.parent / 'lib/x86_64-linux-gnu/ngspice'
        (work / 'spinit').write_text(''.join(f'codemodel {lib / n}\n' for n in
            ['analog.cm', 'digital.cm', 'spice2poly.cm', 'xtradev.cm', 'xtraevt.cm', 'table.cm']))
        net, raw = work / 'test.cir', work / 'trace.raw'
        net.write_text(source)
        with logpath.open('w') as log:
            try:
                code = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', '-r', str(raw), str(net)],
                    env=dict(os.environ, SPICE_SCRIPTS=str(work)), stdout=log, stderr=subprocess.STDOUT,
                    timeout=float(os.environ.get('STEP02_TIMEOUT_S', '240'))).returncode
            except subprocess.TimeoutExpired:
                code = None
                log.write('\nERROR: wall time limit; not a demonstrated convergence failure\n')
        data, names, _ = read_raw(raw) if raw.exists() else (np.empty((0, 1)), [], 0)
    errors = [l for l in logpath.read_text().splitlines() if any(w in l.lower() for w in ['error:', 'aborted', 'too small'])]
    complete = bool(code == 0 and len(data) and data[-1, 0] >= stop * .999 and np.isfinite(data).all() and not errors)
    result = {'case': case, 'project_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'extracted_source_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'requested_end_s': stop, 'actual_end_s': float(data[-1, 0]) if len(data) else None,
              'maxstep_s': step, 'completed': complete, 'errors': errors,
              'rows': len(data), 'elapsed_s': time.monotonic() - started,
              'native_Multisim_run': False, 'fuse_thermal_trip_simulated': False}
    if len(data):
        vectors = {n.lower(): data[:, i] for i, n in enumerate(names)}
        v = lambda n: vectors[n.lower()]
        result['metrics'] = {'VOUT_end_V': float(v('v(vout)')[-1]), 'VOUT_max_V': float(v('v(vout)').max()),
                             'IL_max_A': float(v('i(l1)').max()),
                             'controller_IL_max_A': float(v('v(xctrl.ilraw)').max()),
                             'IOUT_RAW_end_V': float(v('v(iout_raw)')[-1])}
        tail = data[:, 0] >= .025
        if complete and tail.sum() > 1:
            t = data[tail, 0]
            avg = lambda a: float(np.trapezoid(a[tail], t) / (t[-1] - t[0]))
            iout = (v('v(v_cap)') - v('v(vout)')) / .05
            result['time_weighted_25_30ms'] = {
                'VOUT_V': avg(v('v(vout)')), 'VDDA_V': avg(v('v(vdda)')),
                'IOUT_A': avg(iout), 'IOUT_RAW_V': avg(v('v(iout_raw)')),
                'IOUT_transfer_error_V': avg(v('v(iout_raw)') - iout),
                'controller_IL_error_A': avg(v('v(xctrl.ilraw)') - v('i(l1)'))}
        take = np.unique(np.r_[np.arange(0, len(data), max(1, len(data) // 5000)), len(data) - 1])
        np.savetxt(ROOT / 'results/data' / (case + '_sampled.csv'), data[take], delimiter=',',
                   header=','.join(names), comments='')
    (ROOT / 'results/data' / (case + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    if '--50ns' in sys.argv:
        run('fixed_50ns', DEST, .03, 5e-8)
    else:
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(run, 'original_200ns', SOURCE, .007, 2e-7),
                    pool.submit(run, 'fixed_200ns', DEST, .03, 2e-7)]
            for job in jobs:
                job.result()
