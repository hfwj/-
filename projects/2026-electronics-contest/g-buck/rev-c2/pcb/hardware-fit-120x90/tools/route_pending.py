"""Continue the explicit local-pair queue using clearance-checked top copper.

This is a bounded shortest-path search, not power routing or native EDA DRC.
Never rebuild the board or move components. Repeated runs preserve the artifact
when every queued pair already has physical same-layer continuity.
"""
import heapq
import itertools
import numpy as np
from shapely import intersects_xy, union_all
from pcb_common import *

WIDTH = .25
CLEARANCE = .20
STEP = .25


def connected(a, b, pads, tracks, vias=()):
    """Follow physical copper across layers only at PTH pads or real vias."""
    nodes = [(p['geometry'], set(p['layers'])) for p in pads if p['net'] == a['net']]
    nodes += [(t['geometry'], {t['layer']}) for t in tracks if t['net'] == a['net']]
    nodes += [(v['geometry'], {1,2}) for v in vias if v['net'] == a['net']]
    visited = set()
    queue = [(a['geometry'], set(a['layers']))]
    while queue:
        g, layers = queue.pop()
        if layers & set(b['layers']) and g.distance(b['geometry']) < 1e-7:
            return True
        for i, (h, other_layers) in enumerate(nodes):
            if i not in visited and layers & other_layers and g.distance(h) < 1e-7:
                visited.add(i)
                queue.append((h, other_layers))
    return False


def find_path(a, b, obstacles, width=WIDTH):
    """A* on a 0.25mm local grid, checking the full width of every edge."""
    start, end = (a['x'], a['y']), (b['x'], b['y'])
    forbidden = union_all(obstacles).buffer(width / 2 + CLEARANCE + 1e-6)
    board = box(.5 + width / 2, .5 + width / 2,
                119.5 - width / 2, 89.5 - width / 2)

    def clear(p, q):
        line = LineString([p, q])
        return board.covers(line) and not forbidden.intersects(line)

    for margin in (3., 6.):
        xs = np.arange(max(1., math.floor((min(start[0], end[0]) - margin) / STEP) * STEP),
                       min(119., max(start[0], end[0]) + margin), STEP)
        ys = np.arange(max(1., math.floor((min(start[1], end[1]) - margin) / STEP) * STEP),
                       min(89., max(start[1], end[1]) + margin), STEP)
        xx, yy = np.meshgrid(xs, ys, indexing='ij')
        free = ~intersects_xy(forbidden, xx, yy)

        def point(node):
            return float(xs[node[0]]), float(ys[node[1]])

        def anchors(p):
            i, j = int(round((p[0] - xs[0]) / STEP)), int(round((p[1] - ys[0]) / STEP))
            return [(x, y) for x in range(max(0, i-3), min(len(xs), i+4))
                    for y in range(max(0, j-3), min(len(ys), j+4))
                    if free[x, y] and clear(p, point((x, y)))]

        targets = set(anchors(end))
        if not targets:
            continue
        cost, prev, queue = {}, {}, []
        serial = itertools.count()
        for node in anchors(start):
            g = math.dist(start, point(node))
            cost[node] = g
            prev[node] = None
            heapq.heappush(queue, (g + math.dist(point(node), end), next(serial), g, node))
        found = None
        while queue:
            _, _, g, node = heapq.heappop(queue)
            if g != cost[node]:
                continue
            if node in targets:
                found = node
                break
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nxt = node[0] + dx, node[1] + dy
                if not (0 <= nxt[0] < len(xs) and 0 <= nxt[1] < len(ys) and free[nxt]):
                    continue
                ng = g + STEP * math.hypot(dx, dy)
                if ng >= cost.get(nxt, float('inf')) or not clear(point(node), point(nxt)):
                    continue
                cost[nxt], prev[nxt] = ng, node
                heapq.heappush(queue, (ng + math.dist(point(nxt), end), next(serial), ng, nxt))
        if found is None:
            continue
        chain = [end]
        while found is not None:
            chain.append(point(found))
            found = prev[found]
        chain.append(start)
        chain.reverse()
        # Remove grid stair steps only where the resulting full-width copper
        # still clears every obstacle. Preserve exact physical pad endpoints.
        points = [chain[0]]
        i = 0
        while i < len(chain) - 1:
            j = len(chain) - 1
            while j > i + 1 and not clear(chain[i], chain[j]):
                j -= 1
            if math.dist(points[-1], chain[j]) > 1e-7:
                points.append(chain[j])
            i = j
        length = LineString(points).length
        if length <= 2 * math.dist(start, end) + 3:
            return points
    return None


def main():
    manifest = json.loads((ROOT / 'data/build_manifest.json').read_text())
    local = json.loads((ROOT / 'data/local_routing.json').read_text())
    meta, docs, _ = read_project(PATH)
    parts, pads, bodies, tracks = copper_geometry(meta, docs, manifest['pcb'])
    vias = copper_vias(docs, manifest['pcb'])
    ep = {p['ref'] + '.' + p['pin']: p for p in pads}
    holes = [Point(x,y).buffer(1.6) for x,y in manifest['mounting_holes_mm']]
    before = sha(PATH)
    routed, pending, existing = [], [], []
    for pair in local['pending_local_pairs']:
        a, b = ep[pair['from']], ep[pair['to']]
        assert a['net'] and a['net'] == b['net'] == pair['net']
        if connected(a, b, pads, tracks, vias):
            existing.append(pair)
            continue
        obstacles = [p['geometry'] for p in pads if p['net'] != a['net'] and 1 in p['layers']]
        obstacles += [t['geometry'] for t in tracks if t['net'] != a['net'] and t['layer'] == 1]
        obstacles += [v['geometry'] for v in vias if v['net'] != a['net']]
        points = find_path(a, b, obstacles + holes)
        if points is None:
            pending.append({**pair, 'reason': 'No bounded top path; layout/layer review required'})
            continue
        copper = LineString(points).buffer(WIDTH/2)
        assert box(.5,.5,119.5,89.5).covers(copper)
        assert all(copper.distance(g) >= CLEARANCE - 1e-7 for g in obstacles + holes)
        for n, (s,t) in enumerate(zip(points, points[1:])):
            lid = uuid.uuid5(uuid.NAMESPACE_URL, 'gbuck-pending-route:' + pair['from'] + ':' + pair['to'] + ':' + str(n)).hex[:16]
            assert ('LINE', lid) not in docs[manifest['pcb']]
            line = {'partitionId':'','groupId':0,'netName':a['net'],'layerId':1,
                    'startX':s[0]/.0254,'startY':s[1]/.0254,'endX':t[0]/.0254,'endY':t[1]/.0254,
                    'width':WIDTH/.0254,'locked':False,'zIndex':-1}
            docs[manifest['pcb']]['LINE',lid] = line
            tracks.append({'net':a['net'],'geometry':LineString([s,t]).buffer(WIDTH/2),'layer':1})
        assert connected(a, b, pads, tracks)
        routed.append({k:pair[k] for k in ('from','to','net')} | {
            'points_mm': points, 'length_mm': LineString(points).length,
            'width_mm': WIDTH, 'layer': 1})
    if not routed:
        print(json.dumps({'added_pairs':0,'already_connected':len(existing),'pending_pairs':len(pending)}))
        return
    label = 'local-continuation-' + hashlib.sha256(json.dumps(routed,sort_keys=True).encode()).hexdigest()[:16]
    append_history(PATH, meta, docs, {manifest['pcb']}, label)
    # Re-read persisted native records before claiming completed pair endpoints.
    rm, rd, _ = read_project(PATH)
    _, rp, _, rt = copper_geometry(rm, rd, manifest['pcb'])
    re = {p['ref'] + '.' + p['pin']: p for p in rp}
    for pair in routed:
        assert connected(re[pair['from']], re[pair['to']], rp, rt)
    report = {'status':'PARTIAL_LOCAL_ROUTING_CONTINUED', 'baseline_sha256':before,
              'delivered_sha256':sha(PATH), 'routed_pairs':routed,
              'already_connected':existing,'pending_local_pairs':pending,
              'trace_width_mm':WIDTH,'clearance_mm':CLEARANCE,
              'routing_complete':False,'native_DRC':'not_run','manufacturing_release':False}
    (ROOT/'data/routing_continuation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    manifest['routing'] = 'partial_local_continued'
    manifest['continued_local_pairs'] = len(routed)
    manifest['remaining_pending_local_pairs'] = len(pending)
    (ROOT/'data/build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({'added_pairs':len(routed),'pending_pairs':len(pending),'readback_continuity':'PASS'}))


if __name__ == '__main__':
    main()
