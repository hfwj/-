"""Only tighten RELTOL on the existing 25ms switching-observation project."""
import hashlib
import json
import re
from build_diagnostics import PROJECT, ROOT, unpack, pack, parse, inspect, components, model_sources, analysis_options, verify_independent_decoder, block


def main():
    source = PROJECT / 'downloads/GBUCK_STEP02_5R_TRAP_ITL300_25ms_TRACE.ms14'
    raw = source.read_bytes()
    xml, _ = unpack(raw)
    root = parse(xml)
    opts = analysis_options(xml)
    assert opts['reltol'] == {'enabled': True, 'value': '0.003'}
    assert opts['method'] == {'enabled': True, 'value': 'trapezoidal'}
    assert opts['itl4'] == {'enabled': True, 'value': '300'}
    text = xml.decode('ascii')
    tran = block(text, 'TRAN')
    opttext = block(tran, 'ASYS_OPT')
    pattern = r'(\d+:list\{IsEnabled:long\{1\}\s+reltol:double\{)0\.003(\}\s*\})'
    revised_options, count = re.subn(pattern, lambda m: m[1] + '0.001' + m[2], opttext)
    assert count == 1
    revised_tran = tran.replace(opttext, revised_options, 1)
    revised = text.replace(tran, revised_tran, 1)
    assert revised.replace(revised_tran, tran, 1).encode('ascii') == xml
    newroot = parse(revised.encode('ascii'))
    assert components(newroot) == components(root)
    assert model_sources(newroot) == model_sources(root)
    assert inspect(newroot) == inspect(root)
    assert analysis_options(revised.encode('ascii')) == dict(opts, reltol={'enabled': True, 'value': '0.001'})
    data = pack(revised.encode('ascii'))
    verify_independent_decoder(data, revised.encode('ascii'))
    dest = PROJECT / 'downloads/GBUCK_STEP02_5R_TRAP_ITL300_REL001_25ms_DIAG.ms14'
    dest.write_bytes(data)
    result = {'date': '2026-10-25', 'source': str(source.relative_to(PROJECT)),
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'output': str(dest.relative_to(PROJECT)),
        'output_sha256': hashlib.sha256(data).hexdigest(),
        'only_change': 'active transient RELTOL 0.003 -> 0.001; tighter, not relaxed',
        'settings_preserved': inspect(root)['transient_settings'],
        'all_parts_connections_values_layout_models_controller_outputs_preserved': True,
        'other_solver_options_preserved': True, 'exact_inverse_XML_verified': True,
        'two_independent_DCL_decoders_verified': True,
        'native_25ms_run_performed': False, 'full_buck_convergence_verified': False,
        'justification': 'unchanged Q2 imposed-pin replay completes at RELTOL=.001 and .0001, but not .003; this does not establish native full-circuit success'}
    (ROOT / 'results/data/rel001_build_checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
