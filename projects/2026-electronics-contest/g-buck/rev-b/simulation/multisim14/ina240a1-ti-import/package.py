"""Bundle the original uploaded archive, byte-preserving adapter and checks."""
from pathlib import Path
import hashlib
import json
import zipfile
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]


def main():
    result = json.loads((ROOT / 'results/data/verification.json').read_text())
    library = ROOT / 'INA240A1_TI_8PIN.lib'
    original = PROJECT / 'references/vendor-models/INA240A1/sbombe4.zip'
    assert result['all_checks_passed']
    assert hashlib.sha256(library.read_bytes()).hexdigest() == result['adapter_sha256']
    assert hashlib.sha256(original.read_bytes()).hexdigest() == result['uploaded_archive_sha256']
    with zipfile.ZipFile(original) as archive:
        assert library.read_bytes().endswith(archive.read('ina240a1.lib'))
    destination = PROJECT / 'downloads/Multisim14_INA240A1_TI_8PIN_2026-10-24.zip'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(library, 'models/INA240A1_TI_8PIN.lib')
        archive.write(original, 'original/sbombe4.zip')
        archive.write(ROOT / 'README.md', 'README.md')
        archive.writestr('START_HERE.txt', 'INA240A1 TI PSpice model from user-uploaded sbombe4.zip.\nOriginal model bytes and copyright preserved; added8-pin interface only.\nImport models/INA240A1_TI_8PIN.lib; select INA240A1_TI_8PIN.\nUsed for U2/U4; NOT for INA181 U3.\nIndependent ngspice checks completed; Windows Multisim import/run pending.\nNo existing schematic or physical BOM changed.\nSource/scripts: https://github.com/hfwj/-/tree/main/projects/2026-electronics-contest/g-buck/rev-b/simulation/multisim14/ina240a1-ti-import\n')
        for path in (ROOT / 'results').rglob('*'):
            if path.is_file() and path.name != 'package_checks.json':
                archive.write(path, str(path.relative_to(ROOT)))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert archive.read('models/INA240A1_TI_8PIN.lib') == library.read_bytes()
    report = {'date': '2026-10-24', 'package': str(destination.relative_to(PROJECT)),
              'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
              'zip_integrity_verified': True, 'packaged_model_matches_checked_adapter': True,
              'original_TI_model_bytes_preserved': True, 'native_multisim_import_or_run_performed': False}
    (ROOT / 'results/data/package_checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
