"""Minimal, reversible V3-template patch of the user's hand-wired Multisim file.

No GUI execution. Requires dclimplode and lxml. Never serializes the XML back
through a parser, because saved SPICE attributes contain literal newlines.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import sys

import dclimplode
from lxml import etree as ET

ROOT = Path(__file__).resolve().parent
REV_C = ROOT.parents[2]
BASELINE = REV_C / 'references/user-projects/2026-10-27_GBUCK_REVC_DRIVER_手工搭建基准.ms14'
DEST = REV_C / 'downloads/GBUCK_REVC_DRIVER_30k.ms14'
MAGIC = b'MSMCompressedElectronicsWorkbenchXML'
OLD_SAW = 'V_SAW SAW COM PULSE(0 1 0 9.98u 20n 0 10u)'
NEW_SAW = 'V_SAW SAW COM PULSE(0 1 0 33.313333u 20n 0 33.333333u)'
OLD_CALL = 'XCTRL %t1 %t2 VOUT V_CAP 7 L_RAW GBUCK_CTRL_EQ'
NEW_CALL = 'XCTRL %t1 %t2 VOUT V_CAP VIN L_RAW GBUCK_CTRL_EQ'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(data, independent=False):
    assert data.startswith(MAGIC)
    expected, = struct.unpack_from('<Q', data, len(MAGIC))
    pos = len(MAGIC) + 8
    pieces = []
    while pos < len(data):
        n, size = struct.unpack_from('<II', data, pos)
        assert 0 < n <= 900000 and pos + 8 + size <= len(data)
        decoder = (dclimplode.decompressobj_pklib() if independent
                   else dclimplode.decompressobj())
        part = decoder.decompress(data[pos+8:pos+8+size])
        for _ in range(10):
            if decoder.eof:
                break
            part += decoder.decompress(b'')
        assert decoder.eof and len(part) == n
        pieces.append(part)
        pos += 8 + size
    result = b''.join(pieces)
    assert pos == len(data) and len(result) == expected
    return result


def pack(xml):
    data = MAGIC + struct.pack('<Q', len(xml))
    for start in range(0, len(xml), 900000):
        part = xml[start:start+900000]
        encoder = dclimplode.compressobj(dclimplode.CMP_ASCII, 4096)
        compressed = encoder.compress(part) + encoder.flush()
        data += struct.pack('<II', len(part), len(compressed)) + compressed
    return data


def parse(xml):
    text = xml.decode('ascii')
    text = re.sub(r'"[^"<>]*"', lambda m: m[0].replace('\n', '&#10;')
                  .replace('\r', '&#13;').replace('\t', '&#9;'), text)
    return ET.fromstring(text.encode('ascii'),
                         ET.XMLParser(resolve_entities=False, no_network=True))


def clean(s):
    return s.removeprefix('&ASC').removeprefix('&UNI')


def elements(root, tag):
    return {e.getparent().get('CiID'): e for e in root.iter(tag)
            if e.get('LocalName')}


def alias_evidence(root):
    out = {}
    for wire in root.iter('CIITLinkComp'):
        for item in wire.findall('.//Element[@NetModifier="&ASCNI_EWB_NET_NAME"]/Item'):
            name = clean(item.get('Value'))
            if name in ('VIN', 'VOUT', 'V_CAP', 'L_RAW'):
                assert name not in out or out[name] == wire.get('Node')
                out[name] = wire.get('Node')
    cs, ps, ns = (elements(root, tag) for tag in ('CiComponent', 'CiPort', 'CiNode'))
    q1 = next(c for c in cs.values() if clean(c.get('LocalName')) == 'Q1')
    drain = next(ps[p.get('CiID')] for p in q1.findall('Ports/Item')
                 if clean(ps[p.get('CiID')].get('LocalName')) == 'D')
    drain_node = drain.find('Nodes/Item').get('CiID')
    assert out['VIN'] == drain_node
    assert clean(ns[drain_node].get('LocalName')) == '7'
    assert set(out) == {'VIN', 'VOUT', 'V_CAP', 'L_RAW'}
    return {'schematic_named_nodes': out, 'q1_drain_node': drain_node,
            'cached_vin_numeric_name': '7',
            'reason': 'Use the existing explicit schematic name VIN rather than a numeric cached name.'}


def fingerprints(root):
    tags = ('CIITLinkComp', 'CIITSymbolComp', 'CIITConComp', 'CSchDesignNetLabel',
            'CiPort', 'CiNode', 'CiaParamList', 'CiModel', 'CIITDiagram')
    result = {}
    for tag in tags:
        nodes = list(root.iter(tag))
        # CIITDiagram owns the entire circuit tree, including the intentionally
        # changed templates. Its attributes contain the simulation configuration.
        payload = (json.dumps([dict(n.attrib) for n in nodes], sort_keys=True).encode()
                   if tag == 'CIITDiagram' else
                   b''.join(ET.tostring(n, method='c14n') for n in nodes))
        result[tag] = {'count': len(nodes), 'sha256': sha(payload),
                       'scope': 'attributes only' if tag == 'CIITDiagram' else 'complete elements'}
    return result


def frequency_checks(root, ngspice):
    comp = next(c for c in root.iter('CiComponent') if c.get('LocalName') == '&ASCV3')
    template = clean(comp.find('.//CiaSpiceTmpltExprt').get('String'))
    saw = next(line for line in template.splitlines() if line.startswith('V_SAW '))
    pwm = next(line for line in template.splitlines() if line.startswith('E_PWM '))
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    # Fixed duty fixtures test the saved PWM carrier/output equations only.
    # They do not simulate the user's entire digital or power-stage circuit.
    (out / '.spiceinit').write_text('set ngbehavior=psa\n')
    cases = []
    for duty in (.2, .5, .8):
        name = f'pwm_duty_{int(duty*100)}'
        deck = f'''Saved V3 PWM stage; fixed-duty test {duty}
VCOM COM 0 0
VDUTY DUTY COM {duty}
{saw}
{pwm}
RLOAD PWM COM 100k
.tran 5n 2.3m 0 5n
.measure tran period TRIG v(PWM) VAL=1.65 RISE=1 TD=2.1m TARG v(PWM) VAL=1.65 RISE=2 TD=2.1m
.measure tran width TRIG v(PWM) VAL=1.65 RISE=1 TD=2.1m TARG v(PWM) VAL=1.65 FALL=2 TD=2.1m
.end
'''
        path = out / f'{name}.cir'
        path.write_text(deck)
        run = subprocess.run([ngspice, '-b', str(path)], cwd=out,
                             capture_output=True, text=True, timeout=45)
        log = '\n'.join(line.rstrip() for line in (run.stdout + run.stderr).splitlines()) + '\n'
        (out / f'{name}.log').write_text(log)
        assert run.returncode == 0, log
        period = float(re.search(r'(?m)^period\s*=\s*([\deE+.-]+)', log)[1])
        width = float(re.search(r'(?m)^width\s*=\s*([\deE+.-]+)', log)[1])
        freq = 1 / period
        assert abs(freq-30000) < 10, freq
        assert abs(width / period - duty) < .005, (width, period, duty)
        cases.append({'fixed_duty': duty, 'period_s': period, 'frequency_Hz': freq,
                      'pulse_width_s': width, 'measured_duty': width / period})
    return {'scope': 'Isolated saved PWM equations, not full Multisim/client/closed-loop validation',
            'engine': 'ngspice 44.2, PSpice compatibility', 'cases': cases}


def main():
    source = BASELINE.read_bytes()
    old = unpack(source)
    before = parse(old)
    evidence = alias_evidence(before)
    for value in (OLD_SAW, OLD_CALL):
        assert old.count(value.encode('ascii')) == 2
    candidate = old.replace(OLD_SAW.encode(), NEW_SAW.encode()).replace(OLD_CALL.encode(), NEW_CALL.encode())
    # Exact inverse proves preservation of every other XML byte, including wires,
    # native graphics, physical values, digital power mapping and solver settings.
    inverse = candidate.replace(NEW_SAW.encode(), OLD_SAW.encode()).replace(NEW_CALL.encode(), OLD_CALL.encode())
    assert inverse == old
    after = parse(candidate)
    assert fingerprints(before) == fingerprints(after)
    changed_attrs = []
    old_nodes, new_nodes = list(before.iter()), list(after.iter())
    assert len(old_nodes) == len(new_nodes)
    for i, (a, b) in enumerate(zip(old_nodes, new_nodes)):
        assert a.tag == b.tag and a.text == b.text and a.tail == b.tail
        assert set(a.attrib) == set(b.attrib)
        for key in a.attrib:
            if a.get(key) != b.get(key):
                assert a.get(key).count(OLD_SAW) == 1 and a.get(key).count(OLD_CALL) == 1
                changed_attrs.append({'element_index': i, 'tag': a.tag, 'attribute': key})
    assert len(changed_attrs) == 2
    data = pack(candidate)
    assert unpack(data) == candidate
    assert unpack(data, independent=True) == candidate
    DEST.write_bytes(data)
    assert BASELINE.read_bytes() == source
    report = {'baseline': BASELINE.name, 'baseline_sha256': sha(source),
              'output': DEST.name, 'output_sha256': sha(data),
              'baseline_xml_sha256': sha(old), 'output_xml_sha256': sha(candidate),
              'xml_changes': [{'before': OLD_SAW, 'after': NEW_SAW, 'copies': 2},
                              {'before': OLD_CALL, 'after': NEW_CALL, 'copies': 2}],
              'changed_attributes': changed_attrs,
              'exact_inverse_xml_verified': True, 'two_independent_decoders_verified': True,
              'unchanged_fingerprints': fingerprints(before), 'vin_reference_evidence': evidence,
              'source_bytes_preserved': True, 'physical_BOM_changed': False,
              'schematic_wires_layout_values_changed': False,
              'model_scope': 'V3 equivalent controller carrier and VIN reference only',
              'windows_multisim_open_verified': False, 'windows_multisim_run_verified': False,
              'power_stage_or_efficiency_validated': False}
    if len(sys.argv) > 1:
        report['pwm_stage_check'] = frequency_checks(after, sys.argv[1])
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results/patch_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'output': str(DEST), 'changes': report['xml_changes'],
                      'changed_attributes': len(changed_attrs),
                      'pwm': report.get('pwm_stage_check')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
