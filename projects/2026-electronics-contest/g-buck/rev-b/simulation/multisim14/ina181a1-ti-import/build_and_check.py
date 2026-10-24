"""Preserve uploaded INA181 TI core and check physical pin adapter plus three-chip DC fixture."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
SOURCE = PROJECT / 'references/vendor-models/INA181A1/sbombb7.zip'
DEST = ROOT / 'INA181A1_TI_6PIN.lib'
INA240 = ROOT.parent / 'ina240a1-ti-import/INA240A1_TI_8PIN.lib'
NG = Path(os.environ.get('NGSPICE', '/workspace/tools/ngspice/usr/bin/ngspice'))
HEADER = b'''.SUBCKT INA181A1_TI_6PIN OUT GND INP INM REF VS
* Interface adapter only; original TI model follows byte-for-byte.
* Physical pins: 1 OUT,2 GND,3 IN+,4 IN-,5 REF,6 VS.
X_TI INP INM VS GND REF OUT INA181A1
.ENDS INA181A1_TI_6PIN
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    with zipfile.ZipFile(SOURCE) as archive:
        assert archive.testzip() is None
        core = archive.read('ina181a1.lib')
        contents = [{'name': item.filename, 'bytes': item.file_size} for item in archive.infolist()]
    text = core.decode('ascii')
    assert re.search(r'(?im)^\.SUBCKT INA181A1 INP INN VCC GND REF OUT\s*$', text)
    assert not re.search(r'(?im)^\s*\.(?:PROTECT|UNPROTECT|ENCRYPT)', text)
    assert len(re.findall(r'(?im)^\.subckt\s', text)) == 17
    DEST.write_bytes(HEADER + core)
    assert DEST.read_bytes()[len(HEADER):] == core
    fixture = '''V_SUP VA 0 3.3
V_CM CM 0 10
X_W OW 0 IP CM 0 VA INA181A1_TI_6PIN
X_D IP CM VA 0 0 OD INA181A1
R_W OW 0 100k
R_D OD 0 100k
.options method=gear maxord=2 reltol=1e-4 abstol=1e-10 vntol=1e-6
'''
    mixed = '''V_SUP VD 0 3.3
R_VDDA VD VA 10
C_A1 VA 0 1u
C_A2 VA 0 100n
C_A3 VA 0 10u
C_U2 VA 0 100n
C_U3 VA 0 100n
C_U4 VA 0 100n
V_CM2 CM2 0 25
V_CM3 CM3 0 10
V_CM4 CM4 0 10
V_DIFF2 IP2 CM2 0.01
V_DIFF3 IP3 CM3 0.025
V_DIFF4 IP4 CM4 0.025
X_U2 CM2 0 0 NC2 O2 VA 0 IP2 INA240A1_TI_8PIN
X_U3 O3 0 IP3 CM3 0 VA INA181A1_TI_6PIN
X_U4 CM4 0 0 NC4 O4 VA VA IP4 INA240A1_TI_8PIN
R_L2 O2 0 100k
R_L3 O3 0 100k
R_L4 O4 0 100k
.options method=gear maxord=2 reltol=1e-4 abstol=1e-10 vntol=1e-6
.op
'''
    cases = {
        'dc': (fixture + 'V_DIFF IP CM 0\n.dc V_DIFF -0.02 0.06 0.002\n', [DEST], 'v(ow) v(od) i(v_sup)'),
        'step': (fixture + 'V_DIFF IP CM PWL(0 0.01 10u 0.01 10.01u 0.025 100u 0.025)\n.tran 50n 100u 0 50n\n', [DEST], 'v(ow) v(od) i(v_sup)'),
        'direct_only_step': ('''V_SUP VA 0 3.3
V_CM CM 0 10
V_DIFF IP CM PWL(0 0.01 10u 0.01 10.01u 0.025 100u 0.025)
X_D IP CM VA 0 0 OD INA181A1
R_D OD 0 100k
.options method=gear maxord=2 reltol=1e-4 abstol=1e-10 vntol=1e-6
.tran 50n 100u 0 50n
''', [DEST], 'v(od)'),
        'three_chip_dc': (mixed, [DEST, INA240], 'v(va) v(o2) v(o3) v(o4) i(v_sup)'),
    }
    results = {}
    for case, (body, libraries, vectors) in cases.items():
        prefix = '* Original TI sensing model interface check\n'
        includes = ''.join(f'.include "{path}"\n' for path in libraries)
        relative = ''.join(f'.include "{os.path.relpath(path, ROOT / "netlists")}"\n' for path in libraries)
        (ROOT / 'netlists' / (case + '.cir')).write_text(prefix + relative + body + '.end\n')
        with tempfile.TemporaryDirectory(prefix='ina181-ti-') as temporary:
            work = Path(temporary)
            lib = NG.parent.parent / 'lib/x86_64-linux-gnu/ngspice'
            (work / 'spinit').write_text('\n'.join('codemodel ' + str(lib / name) for name in
                ['analog.cm', 'digital.cm', 'spice2poly.cm', 'xtradev.cm', 'xtraevt.cm', 'table.cm']) + '\n')
            raw = work / 'trace.txt'
            net = work / 'test.cir'
            net.write_text(prefix + includes + body + f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} {vectors}\nquit\n.endc\n.end\n')
            run = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', str(net)], capture_output=True,
                text=True, timeout=45, env=dict(os.environ, SPICE_SCRIPTS=str(work)))
            log = run.stdout + run.stderr
            (ROOT / 'results/logs' / (case + '.log')).write_text(log)
            errors = [line for line in log.splitlines() if any(word in line.lower() for word in ['error:', 'too small', 'aborted'])]
            data = np.atleast_2d(np.loadtxt(raw, skiprows=1)) if raw.exists() else np.empty((0, 4))
        if run.returncode != 0 or errors or not len(data):
            results[case] = {'rows': len(data), 'checks': {'completed_without_solver_error': False},
                'actual_end_scale': float(data[-1, 0]) if len(data) else None, 'failure_messages': errors}
            continue
        assert np.isfinite(data).all()
        if case == 'direct_only_step':
            np.savetxt(ROOT / 'results/data/direct_only_step.csv', data, delimiter=',', header='time_s,direct_output_V', comments='')
            results[case] = {'rows': len(data), 'checks': {'transient_completed': bool(data[-1, 0] >= 100e-6 * .999)}, 'end_s': float(data[-1, 0])}
            continue
        header = 'scale,wrapper_output_V,direct_output_V,two_amplifier_supply_A' if case != 'three_chip_dc' else 'scale,VA_V,U2_V,U3_V,U4_V,supply_A'
        np.savetxt(ROOT / 'results/data' / (case + '.csv'), data, delimiter=',', header=header, comments='')
        value = lambda position, column: float(np.interp(position, data[:, 0], data[:, column]))
        if case == 'three_chip_dc':
            _, va, u2, u3, u4, current = data[-1]
            checks = {'operating_point_completed': len(data) == 1, 'analog_rail_has_expected_load_drop': 3.2 < va < 3.3,
                'U2_near_0p2V': abs(u2 - .2) < .005, 'U3_near_0p5V': abs(u3 - .5) < .005,
                'U4_tracks_loaded_rail_midpoint': abs(u4 - (va / 2 + .5)) < .005,
                'rail_drop_matches_source_current': abs((3.3 - va) - (-current * 10)) < 1e-6}
            metrics = {'analog_rail_V': float(va), 'U2_V': float(u2), 'U3_V': float(u3), 'U4_V': float(u4),
                'fixture_supply_A': float(-current), 'scope': 'Three chips, R_VDDA and decoupling only; no protection refs, ADC filters, Buck or MCU'}
        else:
            discrepancy = float(np.max(abs(data[:, 1] - data[:, 2])))
            checks = {'adapter_matches_direct_original': discrepancy < 1e-7}
            if case == 'dc':
                gain = (value(.05, 1) - value(.01, 1)) / .04
                checks.update({'sweep_completed': len(data) == 41 and abs(data[-1, 0] - .06) < 1e-9,
                    'incremental_gain_near_20': abs(gain - 20) < .02,
                    '25mV_output_near_0p5V': abs(value(.025, 1) - .5) < .005})
                metrics = {'incremental_gain_V_per_V': gain, 'zero_input_output_V': value(0, 1), '25mV_output_V': value(.025, 1)}
            else:
                checks.update({'transient_completed': data[-1, 0] >= 100e-6 * .999,
                    'settles_near_0p5V': abs(value(100e-6, 1) - .5) < .005})
                metrics = {'end_s': float(data[-1, 0]), 'end_output_V': value(100e-6, 1)}
            metrics['max_adapter_discrepancy_V'] = discrepancy
        results[case] = {'rows': len(data), 'checks': {key: bool(value) for key, value in checks.items()}, **metrics}
    result = {'date': '2026-10-24', 'uploaded_archive': SOURCE.name, 'uploaded_archive_sha256': sha(SOURCE.read_bytes()),
        'archive_contents': contents, 'original_member': 'ina181a1.lib', 'original_core_sha256': sha(core),
        'model_header_claim': 'TI INA181A1 PSpice16.2,version2.0,08/16/19', 'core_subcircuits': 17,
        'original_port_order': ['INP', 'INN', 'VCC', 'GND', 'REF', 'OUT'],
        'adapter_port_order': ['OUT', 'GND', 'INP', 'INM', 'REF', 'VS'],
        'original_model_bytes_preserved': True, 'adapter_sha256': sha(DEST.read_bytes()),
        'INA240_adapter_used_sha256': sha(INA240.read_bytes()), 'cases': results,
        'all_checks_passed': all(all(case['checks'].values()) for case in results.values()),
        'native_multisim_import_or_run_performed': False, 'existing_ms14_hardware_BOM_PCB_firmware_changed': False,
        'limits': ['Independent ngspice PSA-mode checks, not native Multisim certification',
            'Three-chip rail test excludes protection divider/ADC/MCU loads and input supply converter',
            'Model parameter ranges are not replacements for device datasheet ratings',
            'Previous FUNC protection and restart results do not establish this TI-model chain has passed']}
    assert all(result['cases']['dc']['checks'].values()), result
    (ROOT / 'results/data/verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['original_core_sha256', 'adapter_sha256', 'cases', 'all_checks_passed']}, indent=2))


if __name__ == '__main__':
    main()
