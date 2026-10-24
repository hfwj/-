"""Move only the outer ENDS; verify one wizard root and recheck affected circuits."""
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
NG = Path(os.environ.get('NGSPICE', '/workspace/tools/ngspice/usr/bin/ngspice'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def structure(data):
    stack, roots, children, models = [], [], [], 0
    for line in data.decode('ascii').splitlines():
        fields = line.split()
        if not fields or fields[0].startswith('*'):
            continue
        command = fields[0].upper()
        if command == '.SUBCKT':
            (children if stack else roots).append(fields[1])
            stack.append(fields[1])
        elif command == '.ENDS':
            assert stack
            assert len(fields) == 1 or fields[1].upper() == stack[-1].upper()
            stack.pop()
        elif command == '.MODEL':
            assert stack, 'Dependent model outside main subcircuit'
            models += 1
    assert not stack
    return {'roots': roots, 'dependent_subcircuits': children, 'dependent_models': models}


def run(case, body, libraries, vectors):
    relative = ''.join(f'.include "{os.path.relpath(path, ROOT / "netlists")}"\n' for path in libraries)
    (ROOT / 'netlists' / (case + '.cir')).write_text('* Wizard nested model check\n' + relative + body + '.end\n')
    with tempfile.TemporaryDirectory(prefix='sense-wizard-') as temporary:
        work = Path(temporary)
        lib = NG.parent.parent / 'lib/x86_64-linux-gnu/ngspice'
        (work / 'spinit').write_text('\n'.join('codemodel ' + str(lib / name) for name in
            ['analog.cm', 'digital.cm', 'spice2poly.cm', 'xtradev.cm', 'xtraevt.cm', 'table.cm']) + '\n')
        raw = work / 'trace.txt'
        includes = ''.join(f'.include "{path}"\n' for path in libraries)
        net = work / 'test.cir'
        net.write_text('* Wizard nested model check\n' + includes + body + f'.control\nset wr_singlescale\nset wr_vecnames\nrun\nwrdata {raw} {vectors}\nquit\n.endc\n.end\n')
        done = subprocess.run([str(NG), '-D', 'ngbehavior=psa', '-b', str(net)], capture_output=True, text=True,
            timeout=45, env=dict(os.environ, SPICE_SCRIPTS=str(work)))
        log = done.stdout + done.stderr
        (ROOT / 'results/logs' / (case + '.log')).write_text(log)
        errors = [line for line in log.splitlines() if any(word in line.lower() for word in ['error:', 'aborted', 'too small'])]
        data = np.atleast_2d(np.loadtxt(raw, skiprows=1)) if raw.exists() else np.empty((0, 1))
    if len(data):
        np.savetxt(ROOT / 'results/data' / (case + '.csv'), data, delimiter=',',
            header='scale,' + ','.join(vectors.split()), comments='')
    return data, {'returncode': done.returncode, 'errors': errors, 'rows': len(data),
                  'last_scale': float(data[-1, 0]) if len(data) else None,
                  'solver_completed_without_errors': bool(done.returncode == 0 and not errors and len(data) and np.isfinite(data).all())}


def main():
    reports, files = {}, {}
    for part, suffix, sourcezip in [('INA240A1', '8PIN', 'sbombe4.zip'), ('INA181A1', '6PIN', 'sbombb7.zip')]:
        previous = ROOT.parent / (part.lower() + '-ti-import')
        top = part + '_TI_' + suffix
        old = (previous / (top + '.lib')).read_bytes()
        baseline_record = json.loads((previous / 'results/data/verification.json').read_text())
        assert sha(old) == baseline_record['adapter_sha256']
        closing = ('.ENDS ' + top + '\n').encode()
        assert old.count(closing) == 1
        fixed = old.replace(closing, b'', 1) + b'\n' + closing
        with zipfile.ZipFile(PROJECT / 'references/vendor-models' / part / sourcezip) as archive:
            core = archive.read(part.lower() + '.lib')
        assert sha(core) == baseline_record['original_core_sha256']
        assert core in fixed and fixed.count(core) == 1
        assert fixed.endswith(closing)
        old_shape, new_shape = structure(old), structure(fixed)
        assert len(old_shape['roots']) > 1
        assert new_shape['roots'] == [top]
        assert fixed.splitlines()[0] == old.splitlines()[0]
        # Exact inverse protects all equations, values, comments, model names and TI bytes.
        prefix, tail = old.split(closing, 1)
        assert fixed == prefix + tail + b'\n' + closing
        destination = ROOT / (top + '_WIZARD.lib')
        destination.write_bytes(fixed)
        files[part] = destination
        reports[part] = {'baseline_sha256': sha(old), 'corrected_sha256': sha(fixed),
            'vendor_core_sha256': sha(core), 'old_structure': old_shape, 'new_structure': new_shape,
            'original_vendor_bytes_preserved': True, 'only_outer_ENDS_relocated': True,
            'model_name_and_port_order_unchanged': True, 'file': destination.name}
    def body(part, case):
        old = ROOT.parent / (part.lower() + '-ti-import/netlists') / (case + '.cir')
        source = old.read_text()
        source = re.sub(r'(?m)^\.include .*\n', '', source)
        source = re.sub(r'(?mi)^\.end\s*$', '', source)
        # Check the new library alone: no original global helper definitions can mask missing nesting.
        source = re.sub(r'(?m)^(?:X_D\S*|R_D\S*) .*\n', '', source)
        return source
    results = {}
    for part, case, vectors, final in [
        ('INA240A1', 'dc', 'v(w2) v(w4) i(v_sup)', .06),
        ('INA240A1', 'step', 'v(w2) v(w4) i(v_sup)', 100e-6),
        ('INA181A1', 'dc', 'v(ow) i(v_sup)', .06),
        ('INA181A1', 'step', 'v(ow) i(v_sup)', 100e-6)]:
        key = part.lower() + '_' + case
        data, result = run(key, body(part, case), [files[part]], vectors)
        result['full_requested_analysis_completed'] = bool(result['solver_completed_without_errors'] and data[-1, 0] >= final * .999)
        if result['full_requested_analysis_completed']:
            old = np.loadtxt(ROOT.parent / (part.lower() + '-ti-import/results/data') / (case + '.csv'), delimiter=',', skiprows=1)
            columns = [1, 2] if part == 'INA240A1' else [1]
            error = max(float(np.max(abs(data[:, col] - np.interp(data[:, 0], old[:, 0], old[:, col])))) for col in columns)
            result['max_output_difference_from_flat_baseline_V'] = error
            result['output_matches_baseline_within_1mV'] = error < .001
            assert result['output_matches_baseline_within_1mV']
        results[key] = result
    mixed = (ROOT.parent / 'ina181a1-ti-import/netlists/three_chip_dc.cir').read_text()
    mixed = re.sub(r'(?m)^\.include .*\n', '', mixed)
    mixed = re.sub(r'(?mi)^\.end\s*$', '', mixed)
    data, mixed_result = run('three_chip_dc', mixed, list(files.values()), 'v(va) v(o2) v(o3) v(o4) i(v_sup)')
    assert mixed_result['solver_completed_without_errors'] and len(data) == 1
    baseline = np.atleast_2d(np.loadtxt(ROOT.parent / 'ina181a1-ti-import/results/data/three_chip_dc.csv', delimiter=',', skiprows=1))
    mixed_result['max_difference_from_flat_fixture'] = float(np.max(abs(data[:, 1:] - baseline[:, 1:])))
    assert mixed_result['max_difference_from_flat_fixture'] < 1e-6
    results['three_chip_dc'] = mixed_result
    assert all(results['ina240a1_' + name]['full_requested_analysis_completed'] for name in ['dc', 'step'])
    assert results['ina181a1_dc']['full_requested_analysis_completed']
    result = {'date': '2026-10-24', 'models': reports, 'checks': results,
        'single_top_level_structure_checks_passed': True, 'INA240_regression_passed': True,
        'INA181_DC_regression_passed': True, 'INA181_transient_completed': results['ina181a1_step']['full_requested_analysis_completed'],
        'native_multisim_import_or_execution_performed': False,
        'existing_ms14_physical_parts_BOM_PCB_firmware_changed': False,
        'scope': 'User-reported wizard structural error addressed; independent ngspice rechecks, not native import certification'}
    (ROOT / 'results/data/verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
