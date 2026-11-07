"""Run prescribed forward cases and export trajectories/force budgets. No fitting."""
from __future__ import annotations
import argparse
import copy
import csv
import json
import os
from pathlib import Path
import numpy as np
from physics_model import (Ball, Air, DragLaw, LiftLaw, Aerodynamics, InitialState,
                           Goal, SolverSettings, PhysicsModel, make_ou_path, simulate)


def merge(base, overrides):
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        result[key] = merge(result.get(key, {}), value) if isinstance(value, dict) else copy.deepcopy(value)
    return result


def build_case(config):
    aero = config['aerodynamics']
    model = PhysicsModel(Ball(**config['ball']), Air(**config['air']),
                         Aerodynamics(DragLaw(**aero['drag']), LiftLaw(**aero['lift']),
                                      aero['spin_decay_per_s'], aero['include_buoyancy']))
    initial = InitialState(**config['initial'])
    settings = SolverSettings(**config['solver'])
    goal = Goal(**config['goal'])
    ou = dict(config.get('ou', {}))
    enabled = ou.pop('enabled', False)
    if not isinstance(enabled, bool): raise ValueError('ou.enabled must be boolean')
    forcing = make_ou_path(duration_s=settings.max_time_s, **ou) if enabled else None
    return model, initial, settings, goal, forcing


def export_csv(path, trajectory):
    axes = 'xyz'
    fieldnames = ['time_s'] + [f'{prefix}_{axis}_{unit}' for prefix, unit in
                 [('position', 'm'), ('velocity', 'm_s'), ('spin', 'rad_s')] for axis in axes]
    forces = ['gravity_N', 'buoyancy_N', 'drag_N', 'magnus_N', 'residual_N', 'net_N']
    fieldnames += [f'{name}_{axis}' for name in forces for axis in axes]
    fieldnames += ['airspeed_m_s', 'reynolds', 'Cd', 'Cl', 'perpendicular_spin_parameter']
    with path.open('w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow(fieldnames)
        for time, state in zip(trajectory.times_s, trajectory.states):
            latent = np.zeros(3) if trajectory.forcing is None else trajectory.forcing.at(time)
            f = trajectory.model.forces(state, latent)
            row = [time, *state, *[x for name in forces for x in f[name]],
                   *[f[k] for k in fieldnames[-5:]]]
            writer.writerow([f'{value:.12g}' for value in row])


def make_figures(output, trajectories):
    os.environ.setdefault('MPLCONFIGDIR', '/tmp/upc-b-v3-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout='constrained')
    for name, tr in trajectories.items():
        s = tr.states
        speeds = np.linalg.norm(s[:, 3:6] - np.asarray(tr.model.air.wind_m_s), axis=1)
        axes[0, 0].plot(s[:, 0], s[:, 2], label=name)
        axes[0, 1].plot(s[:, 0], s[:, 1], label=name)
        axes[1, 0].plot(tr.times_s, speeds, label=name)
        axes[1, 1].plot(tr.times_s, np.linalg.norm(s[:, 6:9], axis=1), label=name)
    for ax, xlabel, ylabel in zip(axes.flat, ['x (m)', 'x (m)', 'Time (s)', 'Time (s)'],
                                  ['Height z (m)', 'Lateral position y (m)', 'Airspeed (m/s)', 'Physical spin (rad/s)']):
        ax.set(xlabel=xlabel, ylabel=ylabel)
        ax.grid(alpha=.2)
    axes[0, 0].axvline(11, color='gray', linestyle=':', linewidth=1)
    axes[0, 0].legend(fontsize=8, ncol=2)
    fig.suptitle('Prescribed forward examples - not fitted to the contest observations', fontsize=12)
    for suffix in ['png', 'pdf']: fig.savefig(output / f'forward_trajectories.{suffix}', dpi=180)
    plt.close(fig)
    tr = trajectories.get('ou_example', next(iter(trajectories.values())))
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), layout='constrained')
    for key in ['gravity_N', 'buoyancy_N', 'drag_N', 'magnus_N', 'residual_N']:
        values = []
        for t, state in zip(tr.times_s, tr.states):
            b = np.zeros(3) if tr.forcing is None else tr.forcing.at(t)
            values.append(np.linalg.norm(tr.model.forces(state, b)[key]))
        axes[0].plot(tr.times_s, values, label=key.removesuffix('_N'))
    axes[0].set(xlabel='Time (s)', ylabel='Force magnitude (N)')
    axes[0].legend(fontsize=8)
    if tr.forcing is not None:
        for i, axis in enumerate('xyz'):
            mask = tr.forcing.times_s <= tr.times_s[-1]
            axes[1].plot(tr.forcing.times_s[mask], tr.forcing.values_m_s2[mask, i], label=f'latent b_{axis}')
        axes[1].legend(fontsize=8)
    axes[1].set(xlabel='Time (s)', ylabel='Latent acceleration (m/s^2)')
    for ax in axes: ax.grid(alpha=.2)
    fig.suptitle('One prescribed-seed forcing example; not a prediction interval', fontsize=11)
    for suffix in ['png', 'pdf']: fig.savefig(output / f'force_budget.{suffix}', dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).parent / 'configs/forward_examples.json')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent.parent / 'results')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    data_dir, figure_dir = args.output / 'data', args.output / 'figures'
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    trajectories, summaries = {}, []
    for case in config['cases']:
        name = case['name']
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in name) or name in trajectories:
            raise ValueError('case names must be unique safe lowercase filenames')
        prescribed = merge(config['base'], case.get('overrides', {}))
        model, initial, settings, goal, forcing = build_case(prescribed)
        tr = simulate(model, initial, settings, goal, forcing)
        export_csv(data_dir / f'{name}.csv', tr)
        if forcing is not None:
            np.savetxt(data_dir / f'{name}_latent_ou.csv', np.column_stack([forcing.times_s, forcing.values_m_s2]),
                       delimiter=',', header='time_s,b_x_m_s2,b_y_m_s2,b_z_m_s2', comments='')
        trajectories[name] = tr
        summaries.append({'case': name, 'prescribed_input': prescribed, **tr.summary()})
        print(f'{name}: {tr.status}, t={tr.times_s[-1]:.6f} s, position={tr.states[-1, :3].round(6).tolist()}')
    payload = {'purpose': config['purpose'], 'observation_data_used_for_fitting': False,
               'covariance_or_probability_calibrated': False, 'cases': summaries}
    (data_dir / 'forward_summary.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    make_figures(figure_dir, trajectories)


if __name__ == '__main__': main()
