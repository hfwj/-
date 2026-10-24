"""Rebuild alias-aware user circuitry transiently; retain failing A/B results."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT.parent)]
from ms14_project import unpack, parse, elements, clean, components
from verify_driver import NG, ngspice_compat
from build_fix import SOURCE, DEST, aliases

MAXSTEP = float(os.environ.get('STEP01_MAXSTEP_S', '5e-8'))
SAVE = 'v(VOUT) v(VDDA) v(IIN_RAW) v(IL_BI) i(L1) v(6) v(7) v(L_RAW) v(V_CAP) v(xctrl.ilraw) v(13) v(11) v(SW) v(17)'


def value(text):
    return text.replace('_uc100b5', 'u').replace('_uc103bc', 'u')


def extract(path, stop, method="trap"):
    root = parse(unpack(path.read_bytes())[0])
    amap = aliases(root)
    models = elements(root, 'CiModel')
    component_objects = {clean(item.get('LocalName')): item for item in elements(root, 'CiComponent').values()}
    lines = ['* Alias-aware extraction of uploaded STEP01 circuit; independent ngspice check',
             '* Fuse represented by conducting1mOhm only; no thermal/I2t trip modeled']
    for part in components(root):
        name, ports, parameters = part['display_ref'], part['ports'], part['parameters']
        ports = {key: amap.get(node, node) if node is not None else 'NC_' + name + '_' + key for key, node in ports.items()}
        if name == 'V3':
            template = clean(component_objects[part['internal_ref']].find('.//CiaSpiceTmpltExprt').get('String'))
            lines.append(template.replace('%t1', ports['1']).replace('%t2', ports['2']))
            continue
        if name == 'F1':
            lines.append('R_SIM_FUSE ' + ports['1'] + ' ' + ports['2'] + ' 1m')
            continue
        model = clean(models[part['model_id']].get('LocalName')) if part['model_id'] else ''
        if name[0] in 'RCL':
            line = f'{name} {ports["1"]} {ports["2"]} {value(parameters[1])}'
        elif name in ['V1', 'V2', 'V_EN', 'SIM_3V3']:
            line = f'V_{name} {ports["1"]} {ports["2"]} {value(parameters[1])}'
        elif name in ['Q1', 'Q2']:
            line = 'X' + name + ' ' + ' '.join(ports[key] for key in ['D', 'G', 'S']) + ' ' + model
        elif name == 'U1':
            line = 'XU1 ' + ' '.join(ports[key] for key in ['VCC', 'IN', '^SD', 'COM', 'VB', 'HO', 'VS', 'LO']) + ' ' + model
        elif name in ['U2', 'U4']:
            line = 'X' + name + ' ' + ' '.join(ports[str(pin)] for pin in range(1, 9)) + ' ' + model
        elif name == 'D1':
            line = f'XD1 {ports["A"]} {ports["K"]} {model}'
        elif name == 'D_BOOT':
            line = f'D_BOOT {ports["A"]} {ports["K"]} {model}'
        else:
            raise ValueError(name)
        lines.append(line)
    lines += [clean(item.find('.//CiaCString').get('String')) for item in models.values()]
    lines += [f'.options reltol=.003 abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=100 rshunt=1e12 method={method} maxord=2',
              '.save ' + SAVE, '.tran 50n ' + str(stop) + ' 0 ' + str(MAXSTEP)]
    return ngspice_compat('\n'.join(lines) + '\n.end\n')


def read_raw(path):
    data = path.read_bytes()
    offset = data.index(b'Binary:\n') + len(b'Binary:\n')
    header = data[:offset].decode('ascii', errors='replace')
    nvars = int(re.search(r'No\. Variables:\s*(\d+)', header)[1])
    declared = int(re.search(r'No\. Points:\s*(\d+)', header)[1])
    names = [line.split()[1] for line in header.split('Variables:\n', 1)[1].split('Binary:')[0].splitlines() if line.strip()]
    count = (len(data) - offset) // (nvars * 8)
    array = np.frombuffer(data, dtype='<f8', count=count * nvars, offset=offset).reshape(count, nvars).copy()
    return array, names, declared


def run(case, path, stop, method="trap"):
    source = extract(path, stop, method)
    started = time.monotonic()
    log_path = ROOT / 'results/logs' / (case + '.log')
    with tempfile.TemporaryDirectory(prefix='step01-' + case + '-') as temporary:
        work = Path(temporary)
        lib = NG.parent.parent / 'lib/x86_64-linux-gnu/ngspice'
        (work / 'spinit').write_text('\n'.join('codemodel ' + str(lib / name) for name in
            ['analog.cm', 'digital.cm', 'spice2poly.cm', 'xtradev.cm', 'xtraevt.cm', 'table.cm']) + '\n')
        net = work / 'test.cir'
        net.write_text(source)
        raw = work / 'trace.raw'
        with log_path.open('w') as stream:
            try:
                process = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', '-r', str(raw), str(net)],
                    stdout=stream, stderr=subprocess.STDOUT, env=dict(os.environ, SPICE_SCRIPTS=str(work)),
                    timeout=float(os.environ.get('STEP01_TIMEOUT_S', '480')))
                code = process.returncode
            except subprocess.TimeoutExpired:
                code = None
                stream.write('\nERROR: wall-time budget exceeded; not a demonstrated convergence failure\n')
        data, names, declared = read_raw(raw) if raw.exists() else (np.empty((0, 1)), [], 0)
    log = log_path.read_text()
    errors = [line for line in log.splitlines() if any(word in line.lower() for word in ['error:', 'aborted', 'too small'])]
    complete = bool(code == 0 and len(data) > 1000 and data[-1, 0] >= stop * .999 and np.isfinite(data).all() and not errors)
    result = {'date': '2026-10-24', 'case': case, 'project_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'extracted_source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'requested_end_s': stop,
        'full_requested_transient_completed': complete, 'actual_end_s': float(data[-1, 0]) if len(data) else None,
        'points': len(data), 'raw_declared_points': declared, 'vectors': names, 'failure_messages': errors,
        'elapsed_wall_s': time.monotonic() - started, 'native_multisim_run_performed': False,
        'cross_solver_TMAX_s': MAXSTEP, 'cross_solver_method': method, 'fuse_thermal_trip_simulated': False}
    if len(data):
        take = np.unique(np.r_[np.arange(0, len(data), max(1, len(data) // 6000)), len(data)-1])
        np.savetxt(ROOT / 'results/data' / (case + '_sampled.csv'), data[take], delimiter=',', header=','.join(names), comments='')
        vectors = {name.lower(): data[:, index] for index, name in enumerate(names)}
        end = data[:, 0] > max(0, float(data[-1, 0]) - .003)
        result['metrics'] = {'IL_max_A': float(vectors['i(l1)'].max()),
            'IL_min_A': float(vectors['i(l1)'].min()), 'VOUT_end_V': float(vectors['v(vout)'][-1]),
            'VDDA_tail_mean_V': float(vectors['v(vdda)'][end].mean()),
            'controller_IL_tail_mean_A': float(vectors['v(xctrl.ilraw)'][end].mean()),
            'physical_IL_tail_mean_A': float(vectors['i(l1)'][end].mean()),
            'IL_BI_tail_mean_V': float(vectors['v(il_bi)'][end].mean()),
            'IIN_RAW_tail_mean_V': float(vectors['v(iin_raw)'][end].mean())}
        if case.startswith('fixed') and complete:
            # Static transfer check uses a time-weighted settled mean, not pointwise PWM comparison.
            tail = data[:, 0] >= .025
            mean = lambda vector: float(np.trapezoid(vector[tail], data[tail, 0]) / (data[-1, 0] - data[tail, 0][0]))
            il = vectors['i(l1)']
            iin = (vectors['v(6)'] - vectors['v(7)']) / .05
            il_eq_error = mean(vectors['v(il_bi)'] - vectors['v(vdda)'] / 2 - .5 * il)
            checks = {'VOUT_recovers_near_10V': 9.5 < vectors['v(vout)'][-1] < 10.5,
                'controller_sees_actual_inductor_current': abs(mean(vectors['v(xctrl.ilraw)'] - il)) < .002,
                'inductor_peak_below_2A_in_this_case': float(il.max()) < 2,
                'IL_BI_average_transfer_error_below_10mV': abs(il_eq_error) < .01,
                'IIN_average_transfer_error_below_10mV': abs(mean(vectors['v(iin_raw)'] - iin)) < .01}
            result['checks'] = {key: bool(value) for key, value in checks.items()}
            result['time_weighted_tail'] = {'interval_s': [.025, .03], 'IL_mean_A': mean(il),
                'IIN_mean_A': mean(iin), 'IL_BI_error_V': il_eq_error, 'VOUT_mean_V': mean(vectors['v(vout)'])}
    result['passed'] = bool(complete and (all(result.get('checks', {}).values()) if case.startswith('fixed') else False))
    (ROOT / 'results/data' / (case + '_verification.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    return result


def main():
    global MAXSTEP
    if '--trap-coarse' in sys.argv:
        MAXSTEP = 2e-7
        run('fixed_trap_200ns', DEST, .03, method='trap')
        return
    if '--gear' in sys.argv:
        run('fixed_gear', DEST, .03, method='gear')
        return
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, 'original_alias_mismatch', SOURCE, .007), pool.submit(run, 'fixed', DEST, .03)]
        for future in futures:
            future.result()


if __name__ == '__main__':
    main()
