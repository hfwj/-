"""Correct PCB-export metadata identified in the client's import-change CSV.

R_PRE is physically external, but its two board terminals must remain in PCB.
No schematic nets, values, component positions or copper shapes are changed.
"""
import argparse
import csv
import datetime
from pcb_common import *


def apply(csv_path):
    rows = list(csv.DictReader(csv_path.read_text(encoding='utf-16').splitlines(), delimiter='\t'))
    changes = [r for r in rows if r['动作']]
    channels = {}
    for r in changes:
        action, obj = r['动作'], r['对象']
        if action == '修改属性' and obj.endswith(':通道ID'):
            assert r['导入前'] == '' and r['导入后']
            channels[obj.split(':')[0]] = r['导入后']
        elif action == '移除元件':
            assert obj == 'R_PRE' and r['导入前'] == 'R_PRE' and r['导入后'] == ''
        else:
            assert action == '修改属性' and obj == 'C_IOUT_PROT:描述'
            assert r['导入前'] == '1kΩ+100nF，τ=100us；不替代软件持续判据' and r['导入后'] == ''
    assert len(channels) == 17 and len(changes) == 19
    meta, docs, _ = read_project(PATH)
    before_docs = copy.deepcopy(docs)
    before_sha = sha(PATH)
    manifest = json.loads((ROOT/'data/build_manifest.json').read_text())
    pcb = manifest['pcb']
    _, pages, parts, pins = inventory(meta, docs, 'G题同步Buck Rev C.2 原理图')
    pp, _, _, _ = copper_geometry(meta, docs, pcb)
    changed = set()
    events = []
    def attr(page, parent, key, value):
        for (kind, i), b in docs[page].items():
            if kind == 'ATTR' and b.get('parentId') == parent and b.get('key') == key:
                if b.get('value') != value:
                    b['value'] = value
                    changed.add(page)
                return
        i = uuid.uuid5(uuid.NAMESPACE_URL, 'gbuck-netlist-sync:' + page + parent + key).hex[:16]
        docs[page]['ATTR', i] = {'parentId': parent, 'key': key, 'value': value,
                               'x': None, 'y': None, 'keyVisible': False, 'valueVisible': False,
                               'rotation': 0, 'zIndex': 1}
        changed.add(page)
    # The client assigned missing channel IDs by sorted page order and component
    # order on each page. Source and isolated export have different identifiers;
    # use the previous export's order, actually seen by the client. Confirm all
    # 17 observed values before deriving R_PRE's channel ID.
    old_export = ROOT/'native/GBUCK_RevC2_DRC_syncfix_20261028.eprj2'
    em, ed, _ = read_project(old_export)
    _, epages, eparts, _ = inventory(em, ed, 'G题同步Buck Rev C.2 原理图')
    observed_order = {}
    for page_n, page in enumerate(sorted(epages), 1):
        cids = [i for (k, i) in ed[page] if k == 'COMPONENT']
        for ref, p in eparts.items():
            if p['page'] == page and not p['attrs'].get('Channel ID'):
                observed_order[ref] = f'${page_n}I{cids.index(p["id"]) + 1}'
    assert all(observed_order[r] == v for r, v in channels.items())
    assert set(observed_order) == set(channels) | {'R_PRE'}
    for ref, value in observed_order.items():
        p = parts[ref]
        attr(p['page'], p['id'], 'Channel ID', value)
        cid = pp[ref][0]
        old = docs[pcb]['COMPONENT', cid]['attrs'].get('Channel ID', '')
        if old != value:
            docs[pcb]['COMPONENT', cid]['attrs']['Channel ID'] = value
            changed.add(pcb)
        events.append({'ref': ref, 'property': 'Channel ID', 'before': old, 'after': value})
    p = parts['R_PRE']
    device = p['attrs']['Device']
    at = docs[device]['META', 'META']['attributes']
    assert at['Convert to PCB'] == 'no'
    at['Convert to PCB'] = 'yes'
    changed.add(device)
    attr(p['page'], p['id'], 'Convert to PCB', 'yes')
    events.append({'ref': 'R_PRE', 'property': 'Convert to PCB', 'before': 'no', 'after': 'yes',
                   'reason': 'Keep the external resistor board-side terminals in the PCB netlist'})
    p = parts['C_IOUT_PROT']
    note = docs[p['attrs']['Device']]['META', 'META']['attributes']['Description']
    assert note == '1kΩ+100nF，τ=100us；不替代软件持续判据'
    attr(p['page'], p['id'], 'Description', note)
    events.append({'ref': 'C_IOUT_PROT', 'property': 'Description', 'before': p['attrs']['Description'], 'after': note})
    stamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp()*1000)
    for u in changed:
        meta[u].update(updateTime=stamp, version=str(stamp))
    append_history(PATH, meta, docs, changed, 'netlist-sync-v1:' + before_sha)
    rm, rd, _ = read_project(PATH)
    _, _, rparts, rpins = inventory(rm, rd, 'G题同步Buck Rev C.2 原理图')
    rpp, pads, _, tracks = copper_geometry(rm, rd, pcb)
    assert {(p['ref'], p['pin'], p['net']) for p in pins} == {(p['ref'], p['pin'], p['net']) for p in rpins}
    for ref, p in rparts.items():
        dev = rd[p['attrs']['Device']]['META', 'META']['attributes']
        assert p['attrs'].get('Convert to PCB', dev.get('Convert to PCB')) == 'yes', ref
        assert rpp[ref][1]['attrs']['Channel ID'] == p['attrs']['Channel ID'], ref
        assert p['attrs']['Value'] == parts[ref]['attrs']['Value'], ref
    # Reject any change other than the explicitly enumerated property updates.
    differences = []
    for u in docs:
        for key in set(before_docs[u]) | set(rd[u]):
            old, new = before_docs[u].get(key), rd[u].get(key)
            if old == new:
                continue
            kind, i = key
            if u == pcb:
                assert kind == 'COMPONENT'
                expected = copy.deepcopy(old)
                expected['attrs']['Channel ID'] = new['attrs']['Channel ID']
                assert expected == new
            elif u == device:
                assert key == ('META', 'META')
                expected = copy.deepcopy(old)
                expected['attributes']['Convert to PCB'] = 'yes'
                assert expected == new
            else:
                assert kind == 'ATTR' and new['key'] in ('Channel ID', 'Convert to PCB', 'Description')
            differences.append({'document': u, 'type': kind, 'id': i})
    report = {'comparison_baseline': 'd68f3dd7f6f9e370f4e26f39c72e2d565cb69e9f',
              'baseline_native_sha256': before_sha, 'saved_native_sha256': sha(PATH),
              'client_import_csv_sha256': sha(csv_path), 'client_import_change_count': len(changes),
              'property_changes': events, 'changed_records': differences,
              'pcb_export_inventory': len(rparts), 'R_PRE_included_in_PCB_export': True,
              'missing_or_mismatched_channel_ids': [], 'schematic_pin_graph_preserved': True,
              'component_values_preserved': True, 'footprints_positions_and_copper_preserved': True,
              'tracks': len(tracks), 'physical_pads': len(pads),
              'simulation_firmware_changed': False, 'native_ERC_DRC': 'pending_client_recheck',
              'manufacturing_release': False}
    (ROOT/'data/netlist_sync_fix_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('property_changes', 'changed_records')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    apply(args.csv)
