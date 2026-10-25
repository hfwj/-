"""Read actual Multisim text, align four channels, and export last-cycle evidence.

Usage: python analyze_export.py unpacked.txt --cache /workspace/work/trace.npz
The RAR is preserved separately; unpack it with a RAR-capable application.
"""
from array import array
from pathlib import Path
import argparse
import hashlib
import json
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]


def parse_text(path):
    traces = {}
    buffer = None
    name = None
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            match = re.match(r'---- Trace: \d+ LEFT BOTTOM "([^"]+)"', line)
            if match:
                assert buffer is None
                name, buffer = match[1], array('d')
            elif line.startswith('---- End Trace:'):
                traces[name] = np.asarray(buffer).reshape(-1, 2).copy()
                buffer = None
            elif buffer is not None and line.strip():
                pair = line.split()
                assert len(pair) == 2
                buffer.extend(map(float, pair))
    assert buffer is None
    assert set(traces) == {'V(g_h)', 'V(g_l)', 'V(sw)', 'I(L1)'}
    return traces


def overlap_intervals(t, a, b, threshold, start):
    """Piecewise-linear external-VGS comparison; not channel conduction timing."""
    result = []
    candidates = np.flatnonzero((t[:-1] >= start) &
        (np.minimum(np.maximum(a[:-1], a[1:]), np.maximum(b[:-1], b[1:])) > threshold))
    for i in candidates:
        dt = t[i + 1] - t[i]
        if dt <= 0:
            continue
        left, right = 0., 1.
        for y in (a, b):
            v0, v1 = y[i], y[i + 1]
            if v1 == v0:
                if v0 <= threshold:
                    left, right = 1., 0.
            elif v1 > v0:
                left = max(left, (threshold - v0) / (v1 - v0))
            else:
                right = min(right, (threshold - v0) / (v1 - v0))
        if right > left:
            u, v = t[i] + max(0., left) * dt, t[i] + min(1., right) * dt
            if result and u - result[-1][1] < 1e-14:
                result[-1][1] = float(v)
            else:
                result.append([float(u), float(v)])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('text', type=Path)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    traces = parse_text(args.text)
    t = traces['V(g_h)'][:, 0]
    assert all(np.array_equal(a[:, 0], t) for a in traces.values())
    assert all(np.isfinite(a).all() for a in traces.values())
    assert np.all(np.diff(t) >= 0)
    high = traces['V(g_h)'][:, 1] - traces['V(sw)'][:, 1]
    low, sw, il = (traces[n][:, 1] for n in ['V(g_l)', 'V(sw)', 'I(L1)'])
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.cache, time=t, GH=traces['V(g_h)'][:, 1], GL=low, SW=sw, IL=il)
    tail = t >= .02274
    rows = np.column_stack([t[tail], traces['V(g_h)'][tail, 1], low[tail], sw[tail], il[tail], high[tail]])
    np.savetxt(ROOT / 'results/data/native_last_cycles.csv', rows, delimiter=',',
        header='time_s,GH_V,GL_V,SW_V,IL_A,VGS_H_V', comments='', fmt='%.14e')
    limits = lambda y: {'min': float(y.min()), 'max': float(y.max()), 'last': float(y[-1])}
    i = np.flatnonzero(tail)[np.argmax(np.minimum(high[tail], low[tail]))]
    comparisons = {}
    for threshold in [2., 3., 3.5613, 4., 5.]:
        intervals = overlap_intervals(t, high, low, threshold, .02274)
        comparisons[str(threshold)] = {'native_points_both_above': int(np.sum(tail & (high > threshold) & (low > threshold))),
            'linear_interpolated_intervals_s': intervals,
            'linear_interpolated_total_ns': sum(v - u for u, v in intervals) * 1e9}
    archive = PROJECT / 'references/user-waveforms/2026-10-25_STEP02_5R_native_four_traces.rar'
    summary = {
        'date': '2026-10-25', 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'text_sha256': hashlib.sha256(args.text.read_bytes()).hexdigest(),
        'rows_per_trace': len(t), 'traces': list(traces), 'time_axes_exactly_equal': True,
        'duplicate_formatted_times': int(np.sum(np.diff(t) == 0)),
        'start_s': float(t[0]), 'actual_end_s': float(t[-1]), 'requested_25ms_completed': False,
        'full_ranges': {n: limits(y) for n, y in [('VGS_H_V', high), ('VGS_L_V', low), ('SW_V', sw), ('IL_A', il)]},
        'window_start_s': .02274, 'window_rows': int(tail.sum()),
        'last_cycles': {n: limits(y[tail]) for n, y in [('VGS_H_V', high), ('VGS_L_V', low), ('SW_V', sw), ('IL_A', il)]},
        'representative_simultaneous_external_VGS_sample': {
            'time_s': float(t[i]), 'VGS_H_V': float(high[i]), 'VGS_L_V': float(low[i]), 'SW_V': float(sw[i]), 'IL_A': float(il[i])},
        'external_VGS_threshold_comparisons': comparisons,
        'caveat': 'VTO=3.5613 is the embedded intrinsic model parameter; external pin threshold comparisons and interpolated ns intervals are not proof of actual channel current, driver deadtime, or hardware shoot-through. Exported timestamps merge the final two times. Failed transient remains incomplete.'}
    (ROOT / 'results/data/native_export_analysis.json').write_text(json.dumps(summary, indent=2) + '\n')
    figdir = ROOT / 'results/figures'
    figdir.mkdir(exist_ok=True)
    x = (t[tail] - .02274) * 1e6
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    axes[0].plot(x, high[tail], label='High-side VGS = GH - SW', lw=1)
    axes[0].plot(x, low[tail], label='Low-side VGS = GL', lw=1)
    axes[0].axhline(3.5613, color='gray', ls='--', lw=.7, label='Embedded VTO (reference only)')
    axes[0].set_ylabel('VGS / V'); axes[0].legend(fontsize=8, loc='upper right')
    axes[1].plot(x, sw[tail], color='darkgoldenrod', lw=1);axes[1].set_ylabel('SW / V')
    axes[2].plot(x, il[tail], color='firebrick', lw=1);axes[2].set_ylabel('Inductor current / A')
    axes[2].set_xlabel('Time after 22.740 ms / us')
    for ax in axes:
        ax.grid(alpha=.25)
    fig.suptitle('Actual Multisim export: final recorded switching cycles (run incomplete)')
    fig.tight_layout();fig.savefig(figdir / 'native_last_cycles.png', dpi=170);plt.close(fig)
    fig, axes = plt.subplots(2, 1, figsize=(10, 7))
    for ax, center, title in [(axes[0], .0227608, 'SW rising edge: low-gate excursion'),
                               (axes[1], float(t[-1]), 'Final recorded turn-off transition')]:
        m = (t >= center - 180e-9) & (t <= center + 220e-9)
        tx = (t[m] - center) * 1e9
        ax.plot(tx, high[m], label='High-side VGS', lw=1.2)
        ax.plot(tx, low[m], label='Low-side VGS', lw=1.2)
        ax.axhline(3.5613, color='gray', ls='--', lw=.7)
        ax.set_title(title);ax.set_ylabel('VGS / V');ax.set_xlabel('Relative time / ns')
        ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(figdir / 'native_gate_edges.png', dpi=170);plt.close(fig)
    print(json.dumps({k: v for k, v in summary.items() if k != 'external_VGS_threshold_comparisons'}, indent=2))


if __name__ == '__main__':
    main()
