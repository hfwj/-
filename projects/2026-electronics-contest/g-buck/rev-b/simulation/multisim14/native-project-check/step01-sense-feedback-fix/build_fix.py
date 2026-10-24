"""Repair only the controller call's aliased sense nodes in the returned native file."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT.parent), str(ROOT.parent / 'control-loop')]
from ms14_project import PROJECT, unpack, pack, parse, components, elements, clean, inspect
from stabilize_transient import analysis_options, verify_independent_decoder
from build_projects import replace_component

SOURCE = PROJECT / 'references/user-projects/2026-10-24_STEP01_IL_SENSE_异常回传.ms14'
DEST = PROJECT / 'downloads/GBUCK_STEP01_IL_SENSE_FEEDBACK_FIX.ms14'
OLD = 'XCTRL %t1 %t2 VOUT 3 7 2 GBUCK_CTRL_EQ'
NEW = 'XCTRL %t1 %t2 VOUT V_CAP 7 L_RAW GBUCK_CTRL_EQ'


def aliases(root):
    nodes = elements(root, 'CiNode')
    result = {}
    for link in root.iter('CIITLinkComp'):
        for item in link.findall('./ElectricalObject/ModifierInfo/Element'):
            if item.get('NetModifier') == '&ASCNI_EWB_NET_NAME':
                name = clean(item.find('.//Item').get('Value'))
                number = clean(nodes[link.get('Node')].get('LocalName'))
                assert number not in result or result[number] == name
                result[number] = name
    return result


def model_sources(root):
    return {clean(item.get('LocalName')): clean(item.find('.//CiaCString').get('String'))
            for item in elements(root, 'CiModel').values()}


def main():
    original = SOURCE.read_bytes()
    xml, _ = unpack(original)
    root = parse(xml)
    mapping = aliases(root)
    assert mapping['2'] == 'L_RAW' and mapping['3'] == 'V_CAP' and mapping['4'] == 'VOUT'
    assert '7' not in mapping
    by = {item['display_ref']: item for item in components(root)}
    assert by['RS_L']['ports'] == {'1': '2', '2': '3'}
    assert by['U2']['ports'] == {'1': '7', '2': '0', '3': '0', '4': None, '5': '19', '6': '21', '7': '0', '8': '6'}
    assert by['U4']['ports'] == {'1': '3', '2': '0', '3': '0', '4': None, '5': '20', '6': '21', '7': '21', '8': '2'}
    for name in ['C_A1', 'C_A2', 'C_A3', 'C_U2', 'C_U4']:
        assert by[name]['ports'] == {'1': '21', '2': '0'}
    text = xml.decode('ascii')
    def patch(body):
        assert body.count(OLD) == 2
        return body.replace(OLD, NEW)
    updated = replace_component(text, 'V3', patch).encode('ascii')
    assert updated.decode('ascii').replace(NEW, OLD).encode('ascii') == xml
    fixed = parse(updated)
    assert components(fixed) == components(root)
    assert model_sources(fixed) == model_sources(root)
    assert inspect(fixed) == inspect(root)
    assert analysis_options(updated) == analysis_options(xml)
    data = pack(updated)
    verify_independent_decoder(data, updated)
    DEST.write_bytes(data)
    report = {'date': '2026-10-24', 'uploaded_file_name': 'GBUCK_STEP01_IL_SENSE.ms14.ms14',
        'baseline': str(SOURCE.relative_to(PROJECT)), 'baseline_sha256': hashlib.sha256(original).hexdigest(),
        'output': str(DEST.relative_to(PROJECT)), 'output_sha256': hashlib.sha256(data).hexdigest(),
        'aliases': mapping, 'controller_call_before': OLD, 'controller_call_after': NEW,
        'active_and_metadata_copies_changed': 2, 'exact_inverse_xml_verified': True,
        'both_DCL_decoders_verified': True, 'source_preserved': SOURCE.read_bytes() == original,
        'all_components_values_ports_positions_and_vendor_models_preserved': True,
        'controller_equations_and_Ki20_coefficients_preserved': True,
        'analysis_settings_and_selected_outputs_preserved': True,
        'settings': inspect(root)['transient_settings'], 'selected_outputs': inspect(root)['selected_outputs'],
        'native_multisim_execution_performed': False,
        'schematic_impact': 'No symbol, wire, pin, value, alias or layout change; only internal V3 control-template call fixed',
        'physical_parts_BOM_PCB_firmware_impact': 'No change',
        'scope': 'Sampling observation added by user; comparator/latch protection still not connected; actual firmware not tested'}
    (ROOT / 'results/data/build_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
