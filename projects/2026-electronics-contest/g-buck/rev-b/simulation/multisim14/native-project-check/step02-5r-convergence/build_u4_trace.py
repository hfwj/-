"""Record the actual U4 input/output boundary after the REL001 native failure.

Only three output-selection flags and the plot title change. No vendor model
is modified and no convergence improvement is claimed.
"""
import hashlib
import json
import re
from build_diagnostics import (PROJECT, ROOT, unpack, pack, parse, inspect,
    components, model_sources, analysis_options, verify_independent_decoder,
    block, aliases, elements, clean)

EXTRA = ['$l_raw', '$v_cap', '$il_bi']


def main():
    source = PROJECT / 'downloads/GBUCK_STEP02_5R_TRAP_ITL300_REL001_25ms_DIAG.ms14'
    raw = source.read_bytes()
    xml, _ = unpack(raw)
    root = parse(xml)
    before = inspect(root)
    opts = analysis_options(xml)
    assert opts['reltol'] == {'enabled': True, 'value': '0.001'}
    assert opts['method'] == {'enabled': True, 'value': 'trapezoidal'}
    assert opts['itl4'] == {'enabled': True, 'value': '300'}
    by = {p['display_ref']: p for p in components(root)}
    assert by['U4']['ports'] == {'1': '3', '2': '0', '3': '0', '4': None,
        '5': '20', '6': '21', '7': '21', '8': '2'}
    amap = aliases(root)
    assert {n: amap[n] for n in ['2', '3', '20', '21']} == {
        '2': 'L_RAW', '3': 'V_CAP', '20': 'IL_BI', '21': 'VDDA'}
    assert by['U2']['model_id'] == by['U4']['model_id']
    model = clean(elements(root, 'CiModel')[by['U4']['model_id']].find('.//CiaCString').get('String'))
    assert re.search(r'^G_G1\s+GNDF N504417 VICM GNDF 0\.25u\s*$', model, re.M)
    assert re.search(r'^L_L1\s+N504417 N506257\s+400uH\s*$', model, re.M)
    assert re.search(r'^R_R20\s+N506257 GNDF\s+1 TC=0,0\s*$', model, re.M)
    text = xml.decode('ascii')
    tran = block(text, 'TRAN')
    revised = tran
    edits = []
    for name in EXTRA:
        pattern = (r'(NODE:list\{GROUP:long\{)(\d+)'
            r'(\}\s*PLOTDEVICETYPE:long\{\d+\}\s*TYPE:long\{\d+\}\s*NAME:string\{'
            + re.escape(name) + r'\})')
        matches = list(re.finditer(pattern, revised))
        assert len(matches) == 1, name
        old = int(matches[0][2])
        assert not old & 256
        new = old | 768
        revised, count = re.subn(pattern, lambda m: m[1] + str(new) + m[3], revised)
        assert count == 1
        edits.append({'variable': name, 'old_group': old, 'new_group': new})
    revised, count = re.subn(r'PLOT_TITLE:string\{[^}]*\}',
        'PLOT_TITLE:string{5R REL001 U4 boundary observation 25ms}', revised)
    assert count == 1
    candidate = text.replace(tran, revised, 1).encode('ascii')
    assert candidate.decode('ascii').replace(revised, tran, 1).encode('ascii') == xml
    newroot = parse(candidate)
    assert components(newroot) == components(root)
    assert model_sources(newroot) == model_sources(root)
    assert analysis_options(candidate) == opts
    after = inspect(newroot)
    assert set(after['selected_outputs']) == set(before['selected_outputs']) | set(EXTRA)
    assert after == dict(before, selected_outputs=after['selected_outputs'])
    data = pack(candidate)
    verify_independent_decoder(data, candidate)
    dest = PROJECT / 'downloads/GBUCK_STEP02_5R_REL001_U4_TRACE_25ms.ms14'
    dest.write_bytes(data)
    result = {'date': '2026-10-25', 'baseline': str(source.relative_to(PROJECT)),
        'baseline_sha256': hashlib.sha256(raw).hexdigest(),
        'output': str(dest.relative_to(PROJECT)),
        'output_sha256': hashlib.sha256(data).hexdigest(),
        'only_changes': ['three output-selection flags', 'diagnostic plot title'],
        'output_flag_edits': edits, 'outputs': after['selected_outputs'],
        'settings': after['transient_settings'], 'options': opts,
        'U4_display_ref': 'U4', 'U4_database_internal_ref': by['U4']['internal_ref'],
        'U4_native_instance': 'xu4',
        'U4_model_sha256': hashlib.sha256(model.encode()).hexdigest(),
        'U2_and_U4_share_original_model': True,
        'all_parts_values_ports_models_controller_and_numeric_solver_options_preserved': True,
        'exact_inverse_XML_verified': True, 'two_DCL_decoders_verified': True,
        'native_run_performed': False, 'convergence_fix': False,
        'purpose': 'Observe IN+ L_RAW, IN- V_CAP, OUT IL_BI and existing supply VDDA; calculate actual common-mode and differential input before changing the model.'}
    (ROOT / 'results/data/u4_trace_build_checks.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
