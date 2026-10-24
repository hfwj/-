"""Publish both user-supplied TI sources, separating INA181 transient failures."""
from pathlib import Path
import hashlib
import json
import zipfile
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
INA240 = ROOT.parent / 'ina240a1-ti-import'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    r240 = json.loads((INA240 / 'results/data/verification.json').read_text())
    r181 = json.loads((ROOT / 'results/data/verification.json').read_text())
    assert r240['all_checks_passed']
    assert all(r181['cases']['dc']['checks'].values())
    assert all(r181['cases']['three_chip_dc']['checks'].values())
    assert not r181['all_checks_passed']
    assert not all(r181['cases']['step']['checks'].values())
    files = []
    for name, folder, result, model, target in [
        ('INA240A1', INA240, r240, 'INA240A1_TI_8PIN.lib', 'models/INA240A1_TI_8PIN.lib'),
        ('INA181A1', ROOT, r181, 'INA181A1_TI_6PIN.lib', 'models/candidate/INA181A1_TI_6PIN.lib')]:
        path = folder / model
        archive = PROJECT / 'references/vendor-models' / name / result['uploaded_archive']
        assert digest(path.read_bytes()) == result['adapter_sha256']
        assert digest(archive.read_bytes()) == result['uploaded_archive_sha256']
        with zipfile.ZipFile(archive) as source:
            assert path.read_bytes().endswith(source.read(result['original_member']))
        files.extend([(path, target), (archive, 'original/' + archive.name), (folder / 'README.md', 'notes/' + name + '.md')])
        files.extend((file, 'checks/' + name + '/' + str(file.relative_to(folder / 'results')))
                     for file in (folder / 'results').rglob('*') if file.is_file() and file.name != 'package_checks.json')
    destination = PROJECT / 'downloads/Multisim14_TI_CurrentSense_Import_2026-10-24.zip'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('请先阅读.txt', '两个用户上传的TI PSpice模型，原模型字节及版权保留，只添加物理引脚接口。\n当前先导入models/INA240A1_TI_8PIN.lib，元件名/子电路名INA240A1_TI_8PIN，8端，用于U2/U4。\nINA240独立DC与阶跃交叉检查通过，Multisim本机导入仍待确认。\nU3的models/candidate/INA181A1_TI_6PIN.lib仅为候选：DC检查通过，但ngspice瞬态未通过；直接调用原TI模型也未完成。不要把它当作已通过动态验证的工程。\n先关闭元件搜索窗口，打开工具→元器件向导，把第一页截图发回，再逐页核对。\n现有.ms14和实物器件/BOM/PCB均未修改。详细已完成/未完成项目见notes和checks。\nSource: https://github.com/hfwj/-/tree/main/projects/2026-electronics-contest/g-buck/rev-b/simulation/multisim14/ina181a1-ti-import\n')
        for source, target in files:
            archive.write(source, target)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for folder, model, target in [(INA240, 'INA240A1_TI_8PIN.lib', 'models/INA240A1_TI_8PIN.lib'),
                                     (ROOT, 'INA181A1_TI_6PIN.lib', 'models/candidate/INA181A1_TI_6PIN.lib')]:
            assert archive.read(target) == (folder / model).read_bytes()
    result = {'date': '2026-10-24', 'package': str(destination.relative_to(PROJECT)),
        'sha256': digest(destination.read_bytes()), 'zip_integrity_verified': True,
        'original_model_bytes_preserved': True, 'INA240_independent_transient_completed': True,
        'INA181_DC_checks_passed': True, 'INA181_transient_completed': False,
        'three_chip_DC_fixture_passed': True, 'native_multisim_import_or_run_performed': False}
    (ROOT / 'results/data/package_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
