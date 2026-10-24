"""Independent INA181 initialization experiment; do not edit the supplier model."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parent
MODEL = ROOT.parent / 'ti-sense-wizard-fix/INA181A1_TI_6PIN_WIZARD.lib'
NG = Path(os.environ.get('NGSPICE', '/workspace/tools/ngspice/usr/bin/ngspice'))


def main():
    for name in ['netlists', 'results/data', 'results/logs']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    original = ROOT.parents[2] / 'references/vendor-models/INA181A1/sbombb7.zip'
    with zipfile.ZipFile(original) as archive:
        core = archive.read('ina181a1.lib')
    assert core in MODEL.read_bytes()
    assert hashlib.sha256(core).hexdigest() == 'b21a12037058848645c9c0569555905686a85a77430ff612dfd87d96caee21a6'
    results = {}
    for case in ['ordered_ramp', 'constant_supply_control']:
        supplies = ('V_SUP VA 0 PWL(0 0 1u 0 11u 3.3 100u 3.3)\n'
                    'V_CM CM 0 PWL(0 0 15u 0 25u 10 100u 10)\n'
                    if case == 'ordered_ramp' else 'V_SUP VA 0 3.3\nV_CM CM 0 10\n')
        body = supplies + '''V_DIFF IP CM PWL(0 0 35u 0 35.01u 0.025 100u 0.025)
X_U3 OUT 0 IP CM 0 VA INA181A1_TI_6PIN
R_LOAD OUT 0 100k
.options method=trap reltol=1e-4 abstol=1e-10 vntol=1e-6 rshunt=1e12
.tran 10n 100u 0 10n
'''
        with tempfile.TemporaryDirectory(prefix='ina181-power-on-') as temporary:
            work = Path(temporary)
            library = NG.parent.parent / 'lib/x86_64-linux-gnu/ngspice'
            (work / 'spinit').write_text(''.join(f'codemodel {library / name}\n' for name in
                ['analog.cm', 'digital.cm', 'spice2poly.cm', 'xtradev.cm', 'xtraevt.cm', 'table.cm']))
            control = '.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata data.txt v(out) v(va) v(cm)\nquit\n.endc\n.end\n'
            (ROOT / 'netlists' / (case + '.cir')).write_text('* INA181 initialization experiment\n.include "../../ti-sense-wizard-fix/' + MODEL.name + '"\n' + body + control)
            net = work / 'test.cir'
            net.write_text(f'* INA181 initialization experiment\n.include "{MODEL}"\n' + body + control)
            done = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', str(net)], cwd=work,
                capture_output=True, text=True, timeout=45, env=dict(os.environ, SPICE_SCRIPTS=str(work)))
            log = done.stdout + done.stderr
            (ROOT / 'results/logs' / (case + '.log')).write_text(log)
            errors = [line for line in log.splitlines() if any(word in line.lower() for word in ['error:', 'too small', 'aborted'])]
            data = np.atleast_2d(np.loadtxt(work / 'data.txt', skiprows=1)) if (work / 'data.txt').exists() else np.empty((0, 4))
        np.savez_compressed(ROOT / 'results/data' / (case + '.npz'), time=data[:, 0], output=data[:, 1], supply=data[:, 2], common_mode=data[:, 3])
        completed = bool(len(data) and data[-1, 0] >= 100e-6 * .999 and not errors and np.isfinite(data).all() and done.returncode == 0)
        results[case] = {'completed_100us': completed, 'rows': len(data), 'returncode': done.returncode,
                         'errors': errors, 'last_time_s': float(data[-1, 0]) if len(data) else None}
        if completed:
            before = float(np.interp(30e-6, data[:, 0], data[:, 1]))
            after = float(data[-1, 1])
            results[case].update(output_before_step_V=before, output_final_V=after,
                output_change_from_zero_input_V=after-before,
                final_within_10mV_of_nominal=abs(after-.5) < .01)
    report = {'date': '2026-10-25', 'simulator': 'ngspice 44.2, PSpice compatibility',
        'model_sha256': hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        'original_TI_core_bytes_preserved': True, 'checks': results,
        'native_Multisim_U3_test_performed': False,
        'limitations': 'Ordered ideal supply/common-mode ramps in a separate fixture; not a Buck integration, arbitrary startup, or hardware qualification. Constant-source failures retained.',
        'impact': 'No main schematic, physical parts/BOM/PCB, firmware or vendor model changes. Separate diagnostic stimuli and solver settings only.'}
    (ROOT / 'results/data/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    assert results['ordered_ramp']['completed_100us']
    assert results['ordered_ramp']['final_within_10mV_of_nominal']


if __name__ == '__main__':
    main()
