"""Replay measured Q2 pin voltages with its unchanged embedded model.

This deliberately reduced fixture clamps the drain and gate voltages. It does
not contain the high-side MOS, driver, inductor, protection, or their feedback.
No standalone vendor library/netlist is published; models exist only in temp.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import numpy as np
from build_diagnostics import PROJECT, ROOT, unpack, parse, components, elements, clean

NG = Path(os.environ.get('NGSPICE', '/workspace/tools/ngspice/usr/bin/ngspice'))


def read_raw(path):
    data = path.read_bytes()
    offset = data.index(b'Binary:\n') + len(b'Binary:\n')
    header = data[:offset].decode('ascii')
    count = int(re.search(r'No\. Variables:\s*(\d+)', header)[1])
    names = [l.split()[1] for l in header.split('Variables:\n')[1].split('Binary:')[0].splitlines() if l.strip()]
    nrows = (len(data) - offset) // (8 * count)
    values = np.frombuffer(data, dtype='<f8', count=nrows * count, offset=offset).reshape(-1, count)
    return values, names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cache', type=Path)
    args = parser.parse_args()
    cached = np.load(args.cache)
    t = cached['time']
    mask = t >= .02254
    time_abs, gate, drain = t[mask], cached['GL'][mask], cached['SW'][mask]
    # Text precision collapses the final two timestamps. Keep the last value.
    keep = np.r_[np.diff(time_abs) > 0, True]
    time_abs, gate, drain = time_abs[keep], gate[keep], drain[keep]
    origin = float(time_abs[0])
    tt = time_abs - origin
    source = PROJECT / 'downloads/GBUCK_STEP02_5R_TRAP_ITL300_25ms_TRACE.ms14'
    root = parse(unpack(source.read_bytes())[0])
    by = {p['display_ref']: p for p in components(root)}
    item = elements(root, 'CiModel')[by['Q2']['model_id']]
    model, name = clean(item.find('.//CiaCString').get('String')), clean(item.get('LocalName'))
    cases = [('trap_rel003', '.003', 'trap'), ('trap_rel001', '.001', 'trap'),
             ('trap_rel0001', '.0001', 'trap'), ('gear_rel003', '.003', 'gear')]
    output = []
    for case, reltol, method in cases:
        started = time.monotonic()
        logpath = ROOT / 'results/logs' / ('replay_' + case + '.log')
        with tempfile.TemporaryDirectory(prefix='q2-boundary-replay-') as folder:
            work = Path(folder)
            (work / 'model.lib').write_text(model)
            (work / 'spinit').write_text('')
            lines = ['* Q2 imposed-pin-voltage diagnostic, not a full buck', '.include model.lib']
            for vname, node, yy in [('VD', 'd', drain), ('VG', 'g', gate)]:
                lines.append(f'{vname} {node} 0 PWL(')
                lines.extend('+ ' + f'{x:.15e} {y:.15e}' for x, y in zip(tt, yy))
                lines.append('+ )')
            lines += [f'XQ2 d g 0 {name}',
                f'.options reltol={reltol} abstol=1e-8 vntol=1e-4 chgtol=1e-13 itl4=300 rshunt=1e12 method={method}',
                '.save v(d) v(g) v(xq2.7) v(xq2.8) i(VD) i(VG) @m.xq2.m1[id] @d.xq2.d1[id]',
                f'.tran 5n {tt[-1]:.15e} 0 5n', '.end']
            net = '\n'.join(lines) + '\n'
            (work / 'test.cir').write_text(net)
            with logpath.open('w') as stream:
                try:
                    code = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', '-r', 'trace.raw', 'test.cir'],
                        cwd=work, stdout=stream, stderr=subprocess.STDOUT,
                        env=dict(os.environ, SPICE_SCRIPTS=str(work)), timeout=45).returncode
                except subprocess.TimeoutExpired:
                    code = None
                    stream.write('\nERROR: wall-time limit, not proof of convergence failure\n')
            values, names = read_raw(work / 'trace.raw')
        errors = [l for l in logpath.read_text().splitlines() if any(x in l.lower() for x in ['error:', 'too small', 'aborted'])]
        complete = bool(code == 0 and not errors and len(values) and np.isfinite(values).all() and values[-1, 0] >= tt[-1] * .999999)
        vv = {n: values[:, i] for i, n in enumerate(names)}
        current_key = 'i(@m.xq2.m1[id])'
        channel = vv[current_key]
        result = {'case': case, 'reltol': float(reltol), 'method': method,
            'requested_duration_s': float(tt[-1]), 'actual_end_s': float(values[-1, 0]),
            'completed': complete, 'returncode': code, 'errors': errors,
            'rows': len(values), 'elapsed_s': time.monotonic() - started,
            'Q2_model_sha256': hashlib.sha256(model.encode()).hexdigest(),
            'temporary_netlist_sha256': hashlib.sha256(net.encode()).hexdigest(),
            'model_internal_M1_drain_max_A': float(channel.max()),
            'warning': 'Internal M1 drain current is a reduced imposed-boundary model result; do not equate it to pure channel shoot-through, native full-circuit current, or hardware measurement.'}
        last = values[:, 0] >= .0002
        if complete and last.any():
            result['last_native_32us_internal_M1_drain_max_A'] = float(channel[last].max())
        if case == 'trap_rel001' and complete:
            selected = ['time', 'v(d)', 'v(g)', 'v(xq2.7)', 'v(xq2.8)', 'i(vd)', current_key]
            np.savetxt(ROOT / 'results/data/q2_replay_rel001_last_cycles.csv',
                np.column_stack([vv[n][last] for n in selected]), delimiter=',',
                header=','.join(selected), comments='', fmt='%.14e')
        output.append(result)
        print(json.dumps(result), flush=True)
    summary = {'date': '2026-10-25', 'source_project_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'native_window_start_s': origin, 'requested_duration_s': float(tt[-1]), 'boundary_points': len(tt),
        'fixture_maxstep_s': 5e-9, 'native_maxstep_s': 5e-8,
        'cases': output, 'native_multisim_performed': False, 'full_buck_replayed': False,
        'limitations': 'Different solver, imposed external voltages, DC-initialized hidden states, no driver or circuit coupling. Native onset time and root cause are not reproduced exactly. Final duplicate formatted timestamp removed.'}
    (ROOT / 'results/data/q2_replay_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    assert output[1]['completed'] and output[2]['completed']


if __name__ == '__main__':
    main()
