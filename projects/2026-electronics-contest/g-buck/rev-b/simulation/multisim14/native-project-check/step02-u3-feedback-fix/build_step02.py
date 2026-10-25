"""Patch only two stale V3 node references in the U3-integrated upload."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT.parent), str(ROOT.parent / 'control-loop'),
               str(ROOT.parent / 'step01-sense-feedback-fix')]
from ms14_project import PROJECT, unpack, pack, parse, components, inspect
from stabilize_transient import analysis_options, verify_independent_decoder
from build_projects import replace_component
from build_fix import aliases, model_sources

SOURCE = PROJECT / 'references/user-projects/2026-10-25_STEP02_U3_F1熔断_原回传.ms14'
DEST = PROJECT / 'downloads/GBUCK_STEP02_U3_FEEDBACK_FIX.ms14'
OLD = 'XCTRL %t1 %t2 VOUT 3 7 2 GBUCK_CTRL_EQ'
NEW = 'XCTRL %t1 %t2 VOUT V_CAP 7 L_RAW GBUCK_CTRL_EQ'


def main():
    original = SOURCE.read_bytes()
    xml, _ = unpack(original)
    root = parse(xml)
    amap = aliases(root)
    assert {k: amap[k] for k in ['2', '3', '4', '21', '22']} == {
        '2': 'L_RAW', '3': 'V_CAP', '4': 'VOUT', '21': 'VDDA', '22': 'IOUT_RAW'}
    assert '7' not in amap
    by = {c['display_ref']: c for c in components(root)}
    assert by['U3']['ports'] == {'1': '22', '2': '0', '3': '3', '4': '4', '5': '0', '6': '21'}
    assert by['C_U3']['ports'] == {'1': '21', '2': '0'}
    assert by['C_U3']['parameters'][1] == '100n'
    assert by['RS_OUT']['ports'] == {'1': '3', '2': '4'}
    assert by['RS_OUT']['parameters'][1] == '0.05'
    assert by['F1']['parameters'][3] == '2'

    def patch(body):
        assert body.count(OLD) == 2
        return body.replace(OLD, NEW)

    updated = replace_component(xml.decode('ascii'), 'V3', patch).encode('ascii')
    assert updated.replace(NEW.encode(), OLD.encode()) == xml
    fixed = parse(updated)
    assert components(fixed) == components(root)
    assert model_sources(fixed) == model_sources(root)
    assert inspect(fixed) == inspect(root)
    assert analysis_options(updated) == analysis_options(xml)
    data = pack(updated)
    verify_independent_decoder(data, updated)
    DEST.write_bytes(data)
    report = {
        'date': '2026-10-25', 'source_sha256': hashlib.sha256(original).hexdigest(),
        'output_sha256': hashlib.sha256(data).hexdigest(),
        'baseline': str(SOURCE.relative_to(PROJECT)), 'output': str(DEST.relative_to(PROJECT)),
        'before': OLD, 'after': NEW, 'changed_call_copies': 2,
        'exact_inverse_xml_verified': True, 'two_DCL_decoders_verified': True,
        'all_schematic_connections_parts_values_positions_models_preserved': True,
        'U3_and_100nF_decoupling_connectivity_verified': True,
        'analysis_settings_and_selected_outputs_preserved': True,
        'settings': inspect(root)['transient_settings'], 'options': analysis_options(xml),
        'selected_outputs': inspect(root)['selected_outputs'],
        'fuse_preserved_2A_no_bypass': True, 'native_Multisim_run_performed': False,
        'user_reported_fuse_blown': True,
        'impact': 'Only V3 simulation-template node bindings change; no schematic/BOM/PCB/firmware, PI coefficient, vendor-model or solver-setting change.'}
    (ROOT / 'results/data').mkdir(parents=True, exist_ok=True)
    (ROOT / 'results/data/build_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
