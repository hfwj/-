"""Export the current board under fresh project/document/library identities.

The canonical engineering history stays intact. The import copy contains only
the current board and its complete library closure, to prevent an older imported
project/library from being combined with current copper. This is not native DRC.
"""
import argparse
import datetime
from shapely import STRtree
from pcb_common import *


TITLE = 'G题同步Buck Rev C.2 原理图'


def remap(value, mapping):
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [remap(v, mapping) for v in value]
    if isinstance(value, dict):
        return {mapping.get(k, k): remap(v, mapping) for k, v in value.items()}
    return value


def current_documents(meta, docs, pcb):
    scheme, pages, parts, _ = inventory(meta, docs, TITLE)
    selected = {'CONFIG', pcb, scheme, docs[pcb]['META', 'META']['board']} | set(pages)
    # Follow actual document references, including all device/symbol/footprint
    # dependencies. Do not accidentally include unrelated historical boards.
    def references(value):
        if isinstance(value, str) and value in docs:
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from references(v)
        elif isinstance(value, list):
            for v in value:
                yield from references(v)
    while True:
        extra = {r for u in selected for b in docs[u].values() for r in references(b)}
        if extra <= selected:
            return selected, scheme, pages, parts
        selected |= extra


def contact_groups(pads, tracks, vias, fills):
    nodes = []
    for p in pads:
        if p['net']:
            nodes.append((p['net'], p['geometry'], set(p['layers']), 'pad:' + p['ref'] + '.' + p['pin']))
    nodes += [(t['net'], t['geometry'], {t['layer']}, 'trace:' + t['id']) for t in tracks]
    nodes += [(v['net'], v['geometry'], {1, 2}, 'via:' + v['id']) for v in vias]
    nodes += [(f['net'], f['geometry'], {f['layer']}, 'fill:' + f['id']) for f in fills]
    parent = list(range(len(nodes)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    tree = STRtree([n[1] for n in nodes])
    clearance_errors = []
    for i, (net, g, layers, name) in enumerate(nodes):
        for j in tree.query(g.buffer(.20001)):
            j = int(j)
            if j <= i or not layers & nodes[j][2]:
                continue
            distance = g.distance(nodes[j][1])
            if net == nodes[j][0] and distance < 1e-5:
                parent[find(j)] = find(i)
            elif net != nodes[j][0] and distance < .2 - 1e-5:
                clearance_errors.append([name, nodes[j][3], distance])
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for i, node in enumerate(nodes):
        groups[node[0]][find(i)].append(node[3])
    unfinished = {net: list(gs.values()) for net, gs in groups.items() if len(gs) > 1}
    orphans = [names for gs in groups.values() for names in gs.values()
               if not any(n.startswith('pad:') for n in names)]
    return {'networks': len(groups), 'unfinished_networks': unfinished,
            'orphan_copper_groups': orphans, 'foreign_copper_clearance_errors': clearance_errors}


def export(source, dest, manifest_path, audit_path):
    meta, docs, _ = read_project(source)
    manifest = json.loads(manifest_path.read_text())
    pcb = manifest['pcb']
    selected, scheme, pages, parts = current_documents(meta, docs, pcb)
    source_hash = sha(source)
    namespace = 'gbuck-isolated-import-v1:' + source_hash
    uid = lambda label: uuid.uuid5(uuid.NAMESPACE_URL, namespace + ':' + label).hex
    mapping = {u: uid('document:' + u)[:16] for u in selected if u != 'CONFIG'}
    assert not set(mapping.values()) & set(docs), 'Import identifiers must be new'
    stamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    out_docs = {mapping.get(u, u): {k: remap(b, mapping) for k, b in docs[u].items()}
                for u in selected}
    out_meta = {mapping.get(u, u): remap(meta[u], mapping) for u in selected}
    for head in out_meta.values():
        head.update(updateTime=stamp, version=str(stamp), client=uid('client')[:16])
    board = docs[pcb]['META', 'META']['board']
    out_docs[mapping[pcb]]['META', 'META']['title'] = 'Rev C2 120x90 — DRC封装同步复验版'
    out_docs[mapping[board]]['META', 'META']['title'] = 'G题 Rev C.2 — 独立导入复验工程'
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.resolve() == source.resolve():
        raise ValueError('The engineering history must not be overwritten')
    # Copy SQLite with its original schema. Replace only this disposable import
    # copy's project/branch/history/cache records, not the source database.
    src = sqlite3.connect('file:' + str(source) + '?mode=ro', uri=True)
    con = sqlite3.connect(dest)
    src.backup(con)
    src.close()
    old_project, old_branch = con.execute('select uuid,branch_uuid from projects').fetchone()
    original_structure = json.loads(con.execute('select structure from project_structures order by id desc limit 1').fetchone()[0])
    old_start = con.execute('select parent_uuid from branches where uuid=?', (old_branch,)).fetchone()[0]
    project = hashlib.sha256((namespace + ':project').encode()).hexdigest()
    branch, start, history = uid('branch'), uid('start'), uid('history')
    table = 'project_history_' + old_branch
    for name in ('history_data', table, 'project_structures', 'backups', 'editor_caches',
                 'project_logs', 'notifications', 'broadcast_messages'):
        con.execute('DELETE FROM "' + name + '"')
    # Foreign project/branch selectors in the retained schema must agree.
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
    for name in tables:
        columns = {r[1] for r in con.execute('PRAGMA table_info("' + name + '")')}
        if 'project_uuid' in columns:
            con.execute('UPDATE "' + name + '" SET project_uuid=? WHERE project_uuid=?', (project, old_project))
        if 'branch_uuid' in columns:
            con.execute('UPDATE "' + name + '" SET branch_uuid=? WHERE branch_uuid=?', (branch, old_branch))
    con.execute('UPDATE branches SET uuid=?,parent_uuid=?,history_uuid=? WHERE uuid=?',
                (branch, start, history, old_branch))
    con.execute('UPDATE branches SET uuid=?,history_uuid=NULL WHERE uuid=?', (start, old_start))
    con.execute('ALTER TABLE "' + table + '" RENAME TO "project_history_' + branch + '"')
    chunks, ticket = [], 0
    for u in sorted(out_docs):
        ticket += 1
        chunks.append(json.dumps({'type': 'DOCHEAD', 'ticket': ticket}) + '||' + json.dumps(out_meta[u], ensure_ascii=False) + '|')
        for (kind, i), body in out_docs[u].items():
            ticket += 1
            chunks.append(json.dumps({'type': kind, 'id': i, 'ticket': ticket}) + '||' + json.dumps(body, ensure_ascii=False) + '|')
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = hashlib.sha256((namespace + ':history-key').encode()).digest()[:16]
    raw = ('\n'.join(chunks) + '\n').encode()
    encrypted = base64.b64encode(AESGCM(key).encrypt(bytes.fromhex(history), gzip.compress(raw, mtime=0), None)).decode()
    con.execute('INSERT INTO project_history_' + branch + ' (uuid,parent,key,num,snapshot_num) VALUES (?,?,?,0,0)',
                (history, None, key.hex()))
    con.execute('INSERT INTO history_data (uuid,history_uuid,dataStr) VALUES (?,?,?)', (history, history, encrypted))
    con.execute('UPDATE projects SET uuid=?,name=?,ticket=?,g_ticket=?,branch_uuid=?,default_sheet=?',
                (project, 'GBUCK RevC2 DRC封装同步复验 20261028', ticket, ticket, branch, mapping[pcb]))
    # The navigation structure contains only this revision, with matching current
    # document timestamps. Older boards remain in the canonical source file.
    structure = {'boards': {}, 'schematics': {}, 'sheets': {}, 'pcbs': {}, 'panels': {}, 'blockSymbols': {}}
    if 'owner' in original_structure:
        structure['owner'] = original_structure['owner']
    for u in (board, scheme, *pages, pcb):
        kind = meta[u]['docType']
        group = {'BOARD': 'boards', 'SCH': 'schematics', 'SCH_PAGE': 'sheets', 'PCB': 'pcbs'}[kind]
        body = out_docs[mapping[u]]['META', 'META']
        entry = {'uuid': mapping[u], 'title': body.get('title', ''), 'version': str(stamp),
                 'updateTime': stamp, 'source': '', 'zIndex': body.get('zIndex', 0)}
        if kind in ('SCH', 'PCB'):
            entry.update(board=mapping[board], parent_uuid='')
        if kind == 'SCH':
            entry['name'] = body['title']
        if kind == 'SCH_PAGE':
            entry['schematic_uuid'] = mapping[scheme]
        structure[group][mapping[u]] = entry
    con.execute('INSERT INTO project_structures (ticket,project_uuid,branch_uuid,structure) VALUES (?,?,?,?)',
                (ticket, project, branch, json.dumps(structure, ensure_ascii=False)))
    con.commit()
    assert con.execute('pragma integrity_check').fetchone()[0] == 'ok'
    con.execute('VACUUM')
    con.close()
    # Read saved bytes rather than trusting the generator's in-memory geometry.
    rm, rd, _ = read_project(dest)
    assert {h['docType'] for h in rm.values()} == {'CONFIG', 'BOARD', 'SCH', 'SCH_PAGE', 'PCB', 'DEVICE', 'FOOTPRINT', 'SYMBOL'}
    assert sum(h['docType'] == 'PCB' for h in rm.values()) == 1
    inverse = {v: k for k, v in mapping.items()}
    for u in selected:
        recovered = {k: remap(b, inverse) for k, b in rd[mapping.get(u, u)].items()}
        if u in (board, pcb):
            recovered['META', 'META']['title'] = docs[u]['META', 'META']['title']
        assert recovered == docs[u], 'Document body changed: ' + u
    _, _, actual_parts, actual_pins = inventory(rm, rd, TITLE)
    pp, pads, bodies, tracks = copper_geometry(rm, rd, mapping[pcb])
    vias, fills = copper_vias(rd, mapping[pcb]), copper_fills(rd, mapping[pcb])
    contacts = contact_groups(pads, tracks, vias, fills)
    assert not contacts['unfinished_networks'] and not contacts['orphan_copper_groups']
    assert not contacts['foreign_copper_clearance_errors']
    # A second contact audit shrinks native ellipses inside the real boundary;
    # circumscribed clearance envelopes must not create a false connection.
    inner_pads = copy.deepcopy(pads)
    for p in inner_pads:
        if p['body']['defaultPad']['padType'] == 'ELLIPSE':
            factor = math.cos(math.pi / 128) ** 2
            p['geometry'] = affinity.scale(p['geometry'], factor, factor, origin=(p['x'], p['y']))
    inner_contacts = contact_groups(inner_pads, tracks, vias, fills)
    assert not inner_contacts['unfinished_networks'] and not inner_contacts['orphan_copper_groups']
    assert len(pp) == len(actual_parts) == 120
    expected = {(p['ref'], p['pin']): p['net'] for p in actual_pins}
    assert {(p['ref'], p['pin']): p['net'] for p in pads} == expected
    a = attrs(rd[mapping[pcb]])
    for ref, (cid, c, at) in pp.items():
        dev = rd[at['Device']]['META', 'META']['attributes']
        assert dev['Footprint'] == at['Footprint'] == actual_parts[ref]['attrs']['Footprint']
        assert dev['Symbol'] == actual_parts[ref]['attrs']['Symbol']
        assert c['attrs']['Unique ID'] == actual_parts[ref]['id']
    assert sha(source) == source_hash
    report = {'comparison_baseline': '94c495eef7ea6575df013086f031b1b6a7edf036',
              'source_sha256': source_hash, 'export_sha256': sha(dest), 'export_file': dest.name,
              'project_uuid': project, 'branch_uuid': branch, 'pcb_uuid': mapping[pcb],
              'document_uuid_map': mapping, 'library_and_document_identity_overlap': False,
              'metadata_version': str(stamp), 'normalized_document_bodies_equal_source': True,
              'excluded_legacy_boards': True, 'included_documents': len(rd),
              'components': len(pp), 'physical_component_pads': len(pads),
              'track_segments': len(tracks), 'vias': len(vias), 'static_copper_regions': len(fills),
              'schematic_pin_graph_and_library_associations_preserved': True,
              'geometry_contact_audit': contacts, 'native_desktop_open': 'not_run',
              'inscribed_ellipse_contact_audit': inner_contacts,
              'native_DRC_of_export': 'not_run', 'manufacturing_release': False,
              'impact': {'schematic_topology_values_pins': 'unchanged from 94c495e',
                         'components_BOM_copper_positions_and_shapes': 'unchanged from 94c495e',
                         'simulation_firmware': 'unchanged',
                         'changes': 'Independent project/document/library identities, current metadata, single-revision navigation'}}
    audit_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('document_uuid_map', 'geometry_contact_audit')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=PATH)
    parser.add_argument('--output', type=Path, default=ROOT / 'native/GBUCK_RevC2_DRC_syncfix_20261028.eprj2')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'data/build_manifest.json')
    parser.add_argument('--audit', type=Path, default=ROOT / 'data/isolated_import_audit.json')
    args = parser.parse_args()
    export(args.source, args.output, args.manifest, args.audit)
