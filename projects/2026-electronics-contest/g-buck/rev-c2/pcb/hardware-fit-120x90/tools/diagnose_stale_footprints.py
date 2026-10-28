"""Reproduce the user's 27 clearance findings using old pads and current copper.

This controlled comparison does not claim to run the EDA application's DRC.
The uploaded original is preserved unchanged as diagnostic evidence.
"""
import argparse
from pcb_common import *


def reproduce(uploaded, output):
    meta, docs, _ = read_project(PATH)
    old_meta, old_docs, _ = read_project(uploaded)
    pcb = json.loads((ROOT / 'data/build_manifest.json').read_text())['pcb']
    parts, pads, _, tracks = copper_geometry(meta, docs, pcb)
    old_parts, old_pads, _, old_tracks = copper_geometry(old_meta, old_docs, pcb)
    fills = copper_fills(docs, pcb)
    old_fills = copper_fills(old_docs, pcb)
    def signature(p):
        return {'physical_pad_id': p['pid'], 'logical_pin': p['pin'], 'net': p['net'],
                'center_mm': [round(p['x'], 5), round(p['y'], 5)],
                'size_mm': [round(p['w'], 5), round(p['h'], 5)]}
    affected = ('F1', 'RS_L', 'C_A3')
    changes = {ref: {'uploaded': [signature(p) for p in old_pads if p['ref'] == ref],
                     'current': [signature(p) for p in pads if p['ref'] == ref]}
               for ref in affected}
    findings = []
    for f in fills:
        for p in old_pads:
            if p['ref'] not in affected or p['net'] == f['net'] or f['layer'] not in p['layers']:
                continue
            objects = [('fill/pad', p['geometry'], 6.)]
            if p['hole']:
                # A circumscribed round envelope also covers the old F1 slots.
                # All F1 slot violations below have actual zero distance.
                h = Point(p['x'], p['y']).buffer(max(p['hole']['width'], p['hole']['height']) * .0254 / 2)
                objects.append(('fill/drill', h, 6.9))
            for kind, geometry, minimum_mil in objects:
                distance = f['geometry'].distance(geometry)
                if distance < minimum_mil * .0254 - 1e-5:
                    findings.append({'kind': kind, 'ref': p['ref'], 'pin': p['pin'],
                                     'physical_pad_id': p['pid'], 'net': p['net'],
                                     'fill_id': f['id'], 'layer': f['layer'],
                                     'distance_mil': round(distance / .0254, 3),
                                     'minimum_mil': minimum_mil})
    # The source of this comparison must not be mistaken for a full saved copy
    # of the screenshot's current copper. Its branch still contains 71 tracks.
    report = {'canonical_baseline_commit': '94c495eef7ea6575df013086f031b1b6a7edf036',
              'canonical_sha256': sha(PATH), 'uploaded_original_sha256': sha(uploaded),
              'uploaded_tracks': len(old_tracks), 'uploaded_static_fills': len(old_fills),
              'canonical_tracks': len(tracks), 'canonical_static_fills': len(fills),
              'uploaded_F1_value': old_parts['F1'][1]['attrs']['Value'],
              'canonical_F1_value': parts['F1'][1]['attrs']['Value'],
              'affected_footprint_geometry': changes,
              'controlled_comparison': 'Current copper with uploaded F1, RS_L and C_A3 pad geometry',
              'reproduced_clearance_findings': findings,
              'reproduced_clearance_count': len(findings),
              'user_screenshot_counts': {'connection_errors': 9, 'clearance_errors': 27, 'total': 36},
              'conclusion': 'The 27 screenshot clearance findings match the old-footprint/current-copper combination. Exact client cache/import mechanism is not reproduced.',
              'native_DRC_executed_here': False,
              'manufacturing_release': False}
    assert len(findings) == 27, 'The controlled comparison must match the screenshot findings'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'uploaded_tracks': len(old_tracks), 'uploaded_static_fills': len(old_fills),
                      'reproduced_clearance_findings': len(findings),
                      'native_DRC_executed_here': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uploaded', type=Path, default=ROOT / 'references/client-drc-2026-10-28/GBUCK_RevC2_uploaded_old_71tracks.eprj2')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/client_DRC_footprint_mismatch.json')
    args = parser.parse_args()
    reproduce(args.uploaded, args.output)
