"""Read-only Rev C native-history audit; does not run EasyEDA or Multisim.

Run from any directory with Python and cryptography installed. Optional
--multisim also needs lxml and dclimplode. No design files are rewritten.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

REVC = Path(__file__).resolve().parents[2]
GBUCK = REVC.parent
sys.path.insert(0, str(GBUCK / 'rev-b/pcb/github-rework-120x90/tools'))
from read_native import read_project


def attributes(objects):
    result = collections.defaultdict(dict)
    for (kind, _), body in objects.items():
        if kind == 'ATTR':
            result[body.get('parentId')][body['key']] = body.get('value')
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--multisim', action='store_true')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    native = next((REVC / 'schematic/native').glob('*.eprj2'))
    before = digest(native)
    meta, docs, ticket = read_project(native)
    schematic = [u for u, d in docs.items() if meta[u]['docType'] == 'SCH'
                 and d.get(('META', 'META'), {}).get('title') == 'G题同步Buck Rev C 原理图']
    assert len(schematic) == 1, 'Expected exactly one Rev C schematic'
    pages = {u: d for u, d in docs.items() if meta[u]['docType'] == 'SCH_PAGE'
             and d.get(('META', 'META'), {}).get('schematic') == schematic[0]}
    pins, parts, errors = [], {}, []
    for page, objects in pages.items():
        attrs = attributes(objects)
        lines = [b for (kind, _), b in objects.items() if kind == 'LINE']
        for (kind, cid), component in objects.items():
            if kind != 'COMPONENT':
                continue
            attr = attrs[cid]
            ref = attr['Designator']
            assert ref not in parts, f'Duplicate reference: {ref}'
            # This audit intentionally refuses transforms not present in this snapshot.
            assert component.get('rotation', 0) == 0 and not component.get('isMirror'), ref
            parts[ref] = {'value': attr.get('Value'), 'symbol': attr['Symbol'],
                          'device': attr['Device'], 'footprint': attr.get('Footprint'),
                          'page_uuid': page, 'component_id': cid}
            symbol = docs[attr['Symbol']]
            sa = attributes(symbol)
            for (pkind, pid), pin in symbol.items():
                if pkind != 'PIN' or pin.get('partId') != component['partId']:
                    continue
                x = component['x'] + pin['x']
                y = component['y'] + pin['y']
                nets = set()
                for line in lines:
                    x0, y0, x1, y1 = (line[k] for k in ('startX', 'startY', 'endX', 'endY'))
                    if (abs((x-x0)*(y1-y0)-(y-y0)*(x1-x0)) < 1e-6
                            and min(x0, x1)-1e-6 <= x <= max(x0, x1)+1e-6
                            and min(y0, y1)-1e-6 <= y <= max(y0, y1)+1e-6):
                        net = attrs[line['lineGroup']].get('NET')
                        if net:
                            nets.add(net)
                if len(nets) > 1:
                    errors.append(f'Multiple net names at {ref}.{sa[pid]["Pin Number"]}: {nets}')
                pins.append({'ref': ref, 'pin': sa[pid]['Pin Number'],
                             'pin_name': sa[pid].get('Pin Name', ''),
                             'net': next(iter(nets)) if len(nets) == 1 else '',
                             'page_uuid': page, 'x': x, 'y': y})
    bypin = {r['ref']+'.'+r['pin']: r['net'] for r in pins}
    expected = {
        'QH.1':'G_H', 'QH.2':'VIN', 'QH.3':'SW',
        'QL.1':'G_L', 'QL.2':'SW', 'QL.3':'GND',
        'U1.1':'PWM_IN', 'U1.2':'DRV_EN', 'U1.3':'GND', 'U1.4':'LO',
        'U1.5':'+12V_DRV', 'U1.6':'SW', 'U1.7':'HO', 'U1.8':'VB',
        'D1.1':'V_SHUNT_IN', 'D1.2':'IN_PRE', 'D_FREE.1':'SW', 'D_FREE.2':'GND',
        'U9.1':'FAULT_N', 'U9.2':'VREF_NEG', 'U9.3':'IL_PROT', 'U9.4':'GND',
        'U9.5':'VREF_IOUT', 'U9.6':'IOUT_PROT', 'U9.7':'IOUT_OC_N', 'U9.8':'+5V',
        'U5.2':'IL_PROT', 'J_CTL.6':'IOUT_OC_N', 'J_CTL.11':'ADC_VIN',
        'R1.1':'VIN_EXT', 'R1.2':'VIN_DIV', 'R2.1':'VIN_DIV', 'R2.2':'GND',
        'F1.1':'VIN_EXT', 'F1.2':'FUSED', 'R_PRE.1':'FUSED', 'R_PRE.2':'IN_PRE',
        'J_BYP.1':'FUSED', 'J_BYP.2':'IN_PRE',
        'D_BOOT.1':'+12V_DRV', 'D_BOOT.2':'VB', 'C_BOOT.1':'VB', 'C_BOOT.2':'SW',
        'R_SD_PD.1':'DRV_EN', 'R_SD_PD.2':'GND',
        'R_IL_PROT.1':'IL_BI', 'R_IL_PROT.2':'IL_PROT',
        'C_IL_PROT.1':'IL_PROT', 'C_IL_PROT.2':'GND',
        'R_IOUT_PROT.1':'IOUT_RAW', 'R_IOUT_PROT.2':'IOUT_PROT',
        'C_IOUT_PROT.1':'IOUT_PROT', 'C_IOUT_PROT.2':'GND',
        'R_IOUT_TOP.1':'+3V3_A', 'R_IOUT_TOP.2':'VREF_IOUT',
        'R_IOUT_BOT.1':'VREF_IOUT', 'R_IOUT_BOT.2':'GND',
        'R_IOUT_PU.1':'+3V3', 'R_IOUT_PU.2':'IOUT_OC_N',
        'R9.1':'+3V3_A', 'R9.2':'VREF_POS', 'R10A.1':'VREF_POS',
        'R10A.2':'POS_MID', 'R10B.1':'POS_MID', 'R10B.2':'GND',
        'R15A.1':'+3V3_A', 'R15A.2':'NEG_MID', 'R15B.1':'NEG_MID',
        'R15B.2':'VREF_NEG', 'R16.1':'VREF_NEG', 'R16.2':'GND',
        'U4.1':'V_CAP', 'U4.3':'GND', 'U4.5':'IL_BI', 'U4.6':'+3V3_A',
        'U4.7':'+3V3_A', 'U4.8':'L_RAW', 'U3.1':'IOUT_RAW', 'U3.3':'V_CAP',
        'U3.4':'VOUT', 'U3.5':'GND', 'U3.6':'+3V3_A',
        'R_IL_ADC.1':'IL_BI', 'R_IL_ADC.2':'ADC_IL',
        'C_IL_ADC.1':'ADC_IL', 'C_IL_ADC.2':'GND',
        'R_VDDA.1':'+3V3', 'R_VDDA.2':'+3V3_A',
        'R_SN.1':'SW', 'R_SN.2':'SN_MID', 'C_SN.1':'SN_MID', 'C_SN.2':'GND',
        'TP11.1':'IOUT_RAW', 'TP12.1':'IL_PROT', 'TP13.1':'VREF_IOUT',
    }
    checks = {ep: {'expected': net, 'actual': bypin.get(ep),
                    'pass': bypin.get(ep) == net} for ep, net in expected.items()}
    for ep, check in checks.items():
        if not check['pass']:
            errors.append(f'Critical pin mismatch: {ep}')
    bompath = REVC / 'schematic/BOM_RevC.csv'
    with bompath.open(encoding='utf-8-sig', newline='') as stream:
        bom = {r['位号']: r for r in csv.DictReader(stream)}
    bom_mismatch = {ref: [parts.get(ref, {}).get('value'), bom.get(ref, {}).get('数值/型号')]
                    for ref in parts.keys() | bom.keys()
                    if parts.get(ref, {}).get('value') != bom.get(ref, {}).get('数值/型号')}
    if bom_mismatch:
        errors.append('BOM/reference/value mismatch')
    # Read the physical library pad numbering without claiming PCB connectivity.
    mos_library = {}
    for ref in ('QH', 'QL'):
        part = parts[ref]
        device = docs[part['device']][('META', 'META')]['attributes']
        pads = sorted(b['num'] for (kind, _), b in docs[part['footprint']].items() if kind == 'PAD')
        mos_library[ref] = {'pad_numbers': pads,
                            'device_symbol_matches': device['Symbol'] == part['symbol'],
                            'device_footprint_matches': device['Footprint'] == part['footprint']}
        if pads != ['1', '2', '3'] or not all(mos_library[ref][k] for k in
                ('device_symbol_matches', 'device_footprint_matches')):
            errors.append('MOS library association mismatch: '+ref)
    con = sqlite3.connect(native.as_uri()+'?mode=ro', uri=True)
    integrity = con.execute('pragma integrity_check').fetchone()[0]
    con.close()
    assert before == digest(native), 'Input native file changed'
    result = {
        'date_beijing':'2026-10-27',
        'status':'PASS_SCOPED_STATIC_CHECKS_WITH_OPEN_REVIEW_ITEMS' if not errors else 'FAIL',
        'source_native':str(native.relative_to(REVC)), 'source_sha256':before,
        'bom_sha256':digest(bompath), 'sqlite_integrity':integrity,
        'replayed_native_ticket':ticket, 'pages':len(pages), 'parts':len(parts),
        'connected_pins':sum(bool(p['net']) for p in pins),
        'net_count':len({p['net'] for p in pins if p['net']}),
        'unwired_pins':[p['ref']+'.'+p['pin'] for p in pins if not p['net']],
        'critical_pin_checks':checks, 'bom_mismatches':bom_mismatch,
        'mos_library':mos_library, 'parts_inventory':parts,
        'j_ctl_6_symbol_pin_name':next(p['pin_name'] for p in pins if p['ref']=='J_CTL' and p['pin']=='6'),
        'nominal_calculations':{
            'vref_pos_V':3.3*50000/60000, 'vref_neg_V':3.3*10000/60000,
            'il_trip_A':(3.3*50000/60000-1.65)/(20*0.025),
            'iout_trip_A':(3.3*10000/30000)/(20*0.05),
            'protection_RC_s':1000*1e-9, 'precharge_C_F':471e-6,
            'precharge_tau_s':22*471e-6, 'precharge_peak_A':(25-0.45)/(22+0.17),
            'precharge_capacitor_energy_J':0.5*471e-6*(25-0.45)**2,
            'short_0p1ohm_at_1A_V':0.1},
        'open_items':['PDF preview MOS orientation/network display mismatch',
                      'J_CTL.6 pin name still GND despite IOUT_OC_N net',
                      'Real firmware and load-step/short-circuit behavior unverified',
                      'IR2184 manufacturer logic/timing and physical outputs not measured',
                      'Precharge downstream voltage/bypass state not observed by ADC_VIN',
                      'Whole-system efficiency claim not independently reproduced',
                      'EasyEDA ERC/PCB DRC and native client opening not run'],
        'errors':errors, 'design_modified':False, 'native_erc_run':False,
        'pcb_drc_run':False, 'hardware_measurements':False,
    }
    if args.multisim:
        sys.path.insert(0, str(GBUCK / 'rev-b/simulation/multisim14/native-project-check'))
        from ms14_project import unpack, parse, components, clean
        simpath = REVC / 'downloads/GBUCK_REVC_FULL_25V_5R_100ms.ms14'
        root = parse(unpack(simpath.read_bytes())[0])
        rows = components(root)
        (out/'multisim_components.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n')
        models = {}
        for e in root.iter('CiModel'):
            name = clean(e.get('LocalName',''))
            texts = [clean(z.get('String','')) for z in e.findall('.//CiaCString')]
            if name.startswith('REVC_') and texts:
                models[name] = texts
        (out/'multisim_functional_models.json').write_text(json.dumps(models, ensure_ascii=False, indent=2)+'\n')
        result['multisim_readback'] = {'sha256':digest(simpath), 'parts_excluding_ground':len(rows),
                                      'native_execution_run':False, 'scope':'Decode and inspect only'}
    with (out/'native_pin_readback.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pins[0]))
        writer.writeheader()
        writer.writerows(pins)
    (out/'native_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','pages','parts','connected_pins','net_count',
                                          'unwired_pins','bom_mismatches','j_ctl_6_symbol_pin_name','errors')},
                     ensure_ascii=False, indent=2))
    if errors or integrity != 'ok':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
