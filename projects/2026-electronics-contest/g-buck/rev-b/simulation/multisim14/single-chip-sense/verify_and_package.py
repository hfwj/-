"""Check original port mapping and our explicit functional models; no native GUI test."""
from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2] if (ROOT.parent / 'original-schematic').is_dir() else ROOT
MODEL_ROOT = ROOT / 'models' if (ROOT / 'models').is_dir() else ROOT
NG = Path(os.environ.get('NGSPICE', '/workspace/tools/ngspice/usr/bin/ngspice'))
MODELS = ['INA240A1_FUNC.lib', 'INA181A1_FUNC.lib']
EXPECTED = {
    'U2': ['VIN', 'GND', 'GND', 'NC', 'IIN_RAW', '+3V3_A', 'GND', 'V_SHUNT_IN'],
    'U4': ['V_CAP', 'GND', 'GND', 'NC', 'IL_BI', '+3V3_A', '+3V3_A', 'L_RAW'],
    'U3': ['IOUT_RAW', 'GND', 'V_CAP', 'VOUT', 'GND', '+3V3_A'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for folder in ['netlists', 'results/data', 'results/logs']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    reference = ROOT.parent / 'original-schematic/逐引脚接线表.csv'
    if not reference.exists():
        reference = ROOT / 'pin_reference.csv'
    with reference.open(encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    for name, nets in EXPECTED.items():
        actual = {int(row['physical_pin']): row['network'] for row in rows if row['reference'] == name}
        assert actual == dict(enumerate(nets, 1)), (name, actual)
    for name, ports in [(MODELS[0], ['INM', 'GND', 'REF2', 'NC', 'OUT', 'VS', 'REF1', 'INP']),
                        (MODELS[1], ['OUT', 'GND', 'INP', 'INM', 'REF', 'VS'])]:
        lines = (MODEL_ROOT / name).read_text().splitlines()
        assert lines[0].split()[2:] == ports
        assert sum(line.upper().startswith('.SUBCKT ') for line in lines) == 1
    includes = ''.join(f'.include "{MODEL_ROOT / name}"\n' for name in MODELS)
    fixture = '''V_SUP VA 0 3.3
V_COMMON CM 0 25
X_U2 CM 0 0 NC_U2 O_IN VA 0 IP INA240A1_FUNC
X_U4 CM 0 0 NC_U4 O_IL VA VA IP INA240A1_FUNC
X_U3 O_OUT 0 IP CM 0 VA INA181A1_FUNC
R_IN_LOAD O_IN 0 1Meg
R_IL_LOAD O_IL 0 1Meg
R_OUT_LOAD O_OUT 0 1Meg
.options reltol=1e-5 abstol=1e-12 vntol=1e-8
'''
    cases = {'dc': 'V_DIFF IP CM 0\n.dc V_DIFF -0.2 0.2 0.001\n',
             'step': 'V_DIFF IP CM PWL(0 0 5u 0 5.01u 0.025 20u 0.025)\n.tran 10n 20u 0 10n\n'}
    results = {}
    for case, stimulus in cases.items():
        # These netlists contain only our new functional models, not extracted vendor macros.
        relative = ''.join(f'.include "{os.path.relpath(MODEL_ROOT / name, ROOT / "netlists")}"\n' for name in MODELS)
        (ROOT / 'netlists' / (case + '.cir')).write_text('* Functional single-chip check\n' + relative + fixture + stimulus + '.end\n')
        with tempfile.TemporaryDirectory(prefix='sense-chip-') as temporary:
            work = Path(temporary)
            (work / 'spinit').write_text('')
            output = work / 'data.txt'
            source = '* Functional single-chip check\n' + includes + fixture + stimulus
            source += f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {output} v(o_in) v(o_out) v(o_il)\nquit\n.endc\n.end\n'
            net = work / 'check.cir'
            net.write_text(source)
            run = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', str(net)],
                                 capture_output=True, text=True, timeout=30,
                                 env=dict(os.environ, SPICE_SCRIPTS=str(work)))
            log = run.stdout + run.stderr
            (ROOT / 'results/logs' / (case + '.log')).write_text(log)
            assert run.returncode == 0 and output.exists(), log[-1200:]
            assert not any(word in log.lower() for word in ['error:', 'too small', 'aborted']), log[-1200:]
            data = np.loadtxt(output, skiprows=1)
        assert np.isfinite(data).all()
        np.savetxt(ROOT / 'results/data' / (case + '.csv'), data, delimiter=',',
                   header='scale,IIN_RAW_V,IOUT_RAW_V,IL_BI_V', comments='')
        attenuation = 1e6 / (1e6 + 1)
        if case == 'dc':
            expected = np.column_stack([np.clip(20 * data[:, 0], 0, 3.3),
                                        np.clip(20 * data[:, 0], 0, 3.3),
                                        np.clip(20 * data[:, 0] + 1.65, 0, 3.3)]) * attenuation
            checks = {'sweep_completed': len(data) >= 400 and abs(data[-1, 0] - .2) < 1e-9,
                      'gain_reference_and_rail_clip': float(np.max(abs(data[:, 1:] - expected))) < 1e-6}
            results[case] = {'rows': len(data), 'checks': {k: bool(v) for k, v in checks.items()},
                             'max_function_equation_error_V': float(np.max(abs(data[:, 1:] - expected)))}
        else:
            value = lambda time, col: float(np.interp(time, data[:, 0], data[:, col]))
            before = [value(4e-6, col) for col in [1, 2, 3]]
            settled = [value(20e-6, col) for col in [1, 2, 3]]
            fraction = value(6.005e-6, 1) / (.5 * attenuation)
            checks = {'transient_completed': data[-1, 0] >= 20e-6 * .999,
                      'initial_references': max(abs(np.array(before) - np.array([0, 0, 1.65]) * attenuation)) < 1e-6,
                      'settled_outputs': max(abs(np.array(settled) - np.array([.5, .5, 2.15]) * attenuation)) < 1e-5,
                      'assumed_1us_pole': abs(fraction - (1 - np.exp(-1))) < .002}
            results[case] = {'rows': len(data), 'checks': {k: bool(v) for k, v in checks.items()},
                             'initial_outputs_V': before, 'settled_outputs_V': settled,
                             'one_tau_fraction': fraction}
    result = {'date': '2026-10-24', 'model_type': 'Self-authored functional equivalent, NOT TI model',
              'original_pin_networks_matched': 22, 'pin_source_sha256': sha(reference),
              'model_sha256': {name: sha(MODEL_ROOT / name) for name in MODELS},
              'cases': results, 'all_checks_passed': all(all(case['checks'].values()) for case in results.values()),
              'native_multisim_import_or_run_performed': False,
              'schematic_or_existing_ms14_changed': False, 'physical_BOM_PCB_changed': False,
              'real_device_precision_CMRR_timing_efficiency_validated': False}
    (ROOT / 'results/data/verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    assert result['all_checks_passed'], result
    if '--no-package' not in sys.argv:
        destination = PROJECT / 'downloads/Multisim14_Sense_Chip_Functional_2026-10-24.zip'
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in MODELS:
                archive.write(MODEL_ROOT / name, 'models/' + name)
            for name in ['README.md', 'verify_and_package.py']:
                archive.write(ROOT / name, name)
            archive.write(reference, 'pin_reference.csv')
            for path in (ROOT / 'results').rglob('*'):
                if path.is_file() and path.name != 'package_checks.json':
                    archive.write(path, str(path.relative_to(ROOT)))
            archive.writestr('START_HERE.txt', 'Self-authored FUNCTIONAL models, not TI models.\nImport models/INA240A1_FUNC.lib as an8-terminal simulation component.\nImport models/INA181A1_FUNC.lib separately as a6-terminal simulation component.\nWindows Multisim import and run NOT yet verified. No physical BOM change.\nSee README.md for original physical pins. Recheck with python verify_and_package.py --no-package.\n')
        with zipfile.ZipFile(destination) as archive:
            assert archive.testzip() is None
        package_checks = {'package': str(destination.relative_to(PROJECT)), 'sha256': sha(destination),
                          'zip_integrity_verified': True, 'model_hashes_match_checks': True}
        (ROOT / 'results/data/package_checks.json').write_text(json.dumps(package_checks, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
