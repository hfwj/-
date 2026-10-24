"""Distribute only wizard-nested imports, preserving earlier packages as evidence."""
from pathlib import Path
import hashlib
import json
import zipfile
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]


def main():
    result = json.loads((ROOT / 'results/data/verification.json').read_text())
    assert result['single_top_level_structure_checks_passed'] and result['INA240_regression_passed']
    assert not result['INA181_transient_completed']
    package = PROJECT / 'downloads/Multisim14_TI_CurrentSense_WizardFix_2026-10-24.zip'
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('请先阅读.txt', '解决元器件向导multiple top-level .subckt结构报错。\n当前第5页重新从文件加载models/INA240A1_TI_8PIN_WIZARD.lib。\n模型名称仍INA240A1_TI_8PIN，User-defined，符号8脚不变。\n此版仅将外层.ENDS移到文件最后，原TI字节/方程/参数/版权保留。\n结构和INA240独立DC/阶跃检查完成，但Windows Multisim本机导入/运行仍待确认。\nINA181候选也修正结构，动态仍未完成，放在models/candidate内，当前先导入INA240。\n未编辑现有主图或实物BOM/PCB/固件。原旧包保留作记录，不再用于向导导入。\nSource: https://github.com/hfwj/-/tree/main/projects/2026-electronics-contest/g-buck/rev-b/simulation/multisim14/ti-sense-wizard-fix\n')
        archive.write(ROOT / 'README.md', 'README.md')
        for part, model in result['models'].items():
            path = ROOT / model['file']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == model['corrected_sha256']
            assert model['new_structure']['roots'] == [part + ('_TI_8PIN' if part == 'INA240A1' else '_TI_6PIN')]
            target = 'models/' + ('candidate/' if part == 'INA181A1' else '') + path.name
            archive.write(path, target)
            name = 'sbombe4.zip' if part == 'INA240A1' else 'sbombb7.zip'
            archive.write(PROJECT / 'references/vendor-models' / part / name, 'original/' + name)
        for path in (ROOT / 'results').rglob('*'):
            if path.is_file() and path.name != 'package_checks.json':
                archive.write(path, str(path.relative_to(ROOT)))
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None
        assert archive.read('models/INA240A1_TI_8PIN_WIZARD.lib') == (ROOT / 'INA240A1_TI_8PIN_WIZARD.lib').read_bytes()
    report = {'date': '2026-10-24', 'package': str(package.relative_to(PROJECT)),
        'sha256': hashlib.sha256(package.read_bytes()).hexdigest(), 'zip_integrity_verified': True,
        'packaged_models_match_checks': True, 'one_top_level_per_model': True,
        'native_multisim_import_performed': False, 'INA181_transient_completed': False}
    (ROOT / 'results/data/package_checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
