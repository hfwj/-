"""Preserve the user-supplied TI core; adapt physical pins and cross-check the adapter."""
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
SOURCE = PROJECT / 'references/vendor-models/INA240A1/sbombe4.zip'
DEST = ROOT / 'INA240A1_TI_8PIN.lib'
NG = Path(os.environ.get('NGSPICE', '/workspace/tools/ngspice/usr/bin/ngspice'))
HEADER = b'''.SUBCKT INA240A1_TI_8PIN INM GND REF2 NC OUT VS REF1 INP
* Interface adapter only; original TI model follows byte-for-byte.
* Physical pins: 1 IN-,2 GND,3 REF2,4 NC,5 OUT,6 VS,7 REF1,8 IN+.
* NC has no modeled connection. No new device behavior is added.
X_TI OUT INP INM REF1 REF2 VS GND INA240A1
.ENDS INA240A1_TI_8PIN
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    with zipfile.ZipFile(SOURCE) as archive:
        assert archive.testzip() is None
        core = archive.read('ina240a1.lib')
        contents = [{'name': item.filename, 'bytes': item.file_size} for item in archive.infolist()]
    text = core.decode('ascii')
    assert re.search(r'(?im)^\.SUBCKT INA240A1 OUT INP INN REF1 REF2 VCC GND\s*$', text)
    assert not re.search(r'(?im)^\s*\.(?:PROTECT|UNPROTECT|ENCRYPT)', text)
    assert text.count('.SUBCKT') == 12
    DEST.write_bytes(HEADER + core)
    assert DEST.read_bytes()[len(HEADER):] == core
    fixture = '''V_SUP VA 0 3.3
X_W2 CM 0 0 NC2 W2 VA 0 IP INA240A1_TI_8PIN
X_W4 CM 0 0 NC4 W4 VA VA IP INA240A1_TI_8PIN
X_D2 D2 IP CM 0 0 VA 0 INA240A1
X_D4 D4 IP CM VA 0 VA 0 INA240A1
R_W2 W2 0 100k
R_W4 W4 0 100k
R_D2 D2 0 100k
R_D4 D4 0 100k
.options reltol=1e-4 abstol=1e-10 vntol=1e-6
'''
    cases = {'dc': 'V_CM CM 0 25\nV_DIFF IP CM 0\n.dc V_DIFF -0.06 0.06 0.002\n',
             'step': 'V_CM CM 0 25\nV_DIFF IP CM PWL(0 0 10u 0 10.01u 0.025 100u 0.025)\n.tran 50n 100u 0 50n\n'}
    results = {}
    for case, stimulus in cases.items():
        body = '* TI INA240A1 pin-adapter comparison\n' + fixture + stimulus
        (ROOT / 'netlists' / (case + '.cir')).write_text(body + '.include "../INA240A1_TI_8PIN.lib"\n.end\n')
        with tempfile.TemporaryDirectory(prefix='ina240-ti-') as temporary:
            work = Path(temporary)
            lib = NG.parent.parent / 'lib/x86_64-linux-gnu/ngspice'
            (work / 'spinit').write_text('\n'.join('codemodel ' + str(lib / name) for name in
                ['analog.cm', 'digital.cm', 'spice2poly.cm', 'xtradev.cm', 'xtraevt.cm', 'table.cm']) + '\n')
            raw = work / 'trace.txt'
            net = work / 'test.cir'
            net.write_text(body + f'.include "{DEST}"\n.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} v(w2) v(w4) v(d2) v(d4) i(v_sup)\nquit\n.endc\n.end\n')
            run = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', str(net)], capture_output=True,
                text=True, timeout=45, env=dict(os.environ, SPICE_SCRIPTS=str(work)))
            log = run.stdout + run.stderr
            (ROOT / 'results/logs' / (case + '.log')).write_text(log)
            assert run.returncode == 0 and raw.exists(), log[-1200:]
            assert not any(word in log.lower() for word in ['error:', 'too small', 'aborted']), log[-1200:]
            data = np.loadtxt(raw, skiprows=1)
        assert np.isfinite(data).all()
        np.savetxt(ROOT / 'results/data' / (case + '.csv'), data, delimiter=',',
            header='scale,wrapper_U2_V,wrapper_U4_V,direct_U2_V,direct_U4_V,four_amplifier_supply_A', comments='')
        discrepancy = float(np.max(abs(data[:, 1:3] - data[:, 3:5])))
        checks = {'adapter_matches_original_direct_ports': discrepancy < 1e-7}
        value = lambda position, column: float(np.interp(position, data[:, 0], data[:, column]))
        if case == 'dc':
            checks['sweep_completed'] = len(data) == 61 and abs(data[-1, 0] - .06) < 1e-9
            for diff in [.01, .025, .05]:
                checks[f'U2_gain_at_{diff:g}V'] = abs(value(diff, 1) - 20 * diff) < .002
            for diff in [-.025, 0, .025]:
                checks[f'U4_midpoint_at_{diff:g}V'] = abs(value(diff, 2) - (1.65 + 20 * diff)) < .002
            metrics = {'U2_zero_input_output_V': value(0, 1), 'U4_zero_input_output_V': value(0, 2),
                       'U2_25mV_output_V': value(.025, 1), 'U4_25mV_output_V': value(.025, 2),
                       'four_amplifier_supply_current_A_at_zero': -value(0, 5)}
        else:
            checks['transient_completed'] = data[-1, 0] >= 100e-6 * .999
            checks['U2_settles_near_0p5V'] = abs(value(100e-6, 1) - .5) < .002
            checks['U4_settles_near_2p15V'] = abs(value(100e-6, 2) - 2.15) < .002
            metrics = {'end_s': float(data[-1, 0]), 'end_U2_V': value(100e-6, 1), 'end_U4_V': value(100e-6, 2)}
        results[case] = {'rows': len(data), 'max_adapter_discrepancy_V': discrepancy,
                        'checks': {key: bool(value) for key, value in checks.items()}, **metrics}
    result = {'date': '2026-10-24', 'uploaded_archive': SOURCE.name, 'uploaded_archive_sha256': sha(SOURCE.read_bytes()),
        'archive_contents': contents, 'original_member': 'ina240a1.lib', 'original_core_sha256': sha(core),
        'model_header_claim': 'TI INA240A1 PSpice16.2, version2.0,03/09/17', 'core_subcircuits': 12,
        'original_port_order': ['OUT', 'INP', 'INN', 'REF1', 'REF2', 'VCC', 'GND'],
        'adapter_port_order': ['INM', 'GND', 'REF2', 'NC', 'OUT', 'VS', 'REF1', 'INP'],
        'original_model_bytes_preserved': True, 'adapter_sha256': sha(DEST.read_bytes()), 'cases': results,
        'all_checks_passed': all(all(case['checks'].values()) for case in results.values()),
        'native_multisim_import_or_execution_performed': False, 'U3_INA181_included': False,
        'existing_ms14_hardware_BOM_PCB_firmware_changed': False,
        'limits': ['Independent ngspice PSA-mode checks, not Multisim compatibility certification',
                   'Core explicitly excludes temperature behavior',
                   'Core contains VICMMIN=-40.01; not a replacement for datasheet -4V common-mode rating',
                   'No 25V main power-stage or complete sensing/protection run performed',
                   'Four-amplifier fixture supply current is not board current or efficiency']}
    assert result['all_checks_passed'], result
    (ROOT / 'results/data/verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['original_core_sha256', 'adapter_sha256', 'cases', 'all_checks_passed']}, indent=2))


if __name__ == '__main__':
    main()
