"""Forward-only 3-D football model. SI units; no parameter estimation.

State = (position [m], velocity [m/s], physical spin [rad/s]).
Optional colored acceleration is prescribed by a separate, reproducible path.
Aerodynamic closures are configurable approximations, not calibrated ball data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
import numpy as np
from scipy.integrate import solve_ivp


def vector3(value, name: str) -> np.ndarray:
    a = np.asarray(value, dtype=float)
    if a.shape != (3,) or not np.all(np.isfinite(a)):
        raise ValueError(f'{name} must contain three finite numbers')
    return a


def scalar(value: float, name: str, positive: bool = False) -> None:
    if not np.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f'{name} must be finite and {"positive" if positive else "nonnegative"}')


@dataclass(frozen=True)
class Ball:
    mass_kg: float = 0.43
    radius_m: float = 0.11

    def __post_init__(self):
        scalar(self.mass_kg, 'mass_kg', True)
        scalar(self.radius_m, 'radius_m', True)

    @property
    def area_m2(self): return np.pi * self.radius_m ** 2

    @property
    def volume_m3(self): return 4 * np.pi * self.radius_m ** 3 / 3

    @property
    def shell_inertia_kg_m2(self): return 2 * self.mass_kg * self.radius_m ** 2 / 3


@dataclass(frozen=True)
class Air:
    density_kg_m3: float = 1.225
    dynamic_viscosity_pa_s: float = 1.8e-5
    gravity_m_s2: float = 9.81
    wind_m_s: tuple = (0., 0., 0.)

    def __post_init__(self):
        scalar(self.density_kg_m3, 'density_kg_m3')
        scalar(self.dynamic_viscosity_pa_s, 'dynamic_viscosity_pa_s', True)
        scalar(self.gravity_m_s2, 'gravity_m_s2')
        vector3(self.wind_m_s, 'wind_m_s')


@dataclass(frozen=True)
class DragLaw:
    kind: str = 'constant'
    coefficient: float = 0.25
    reynolds_nodes: tuple = ()
    coefficient_nodes: tuple = ()

    def __post_init__(self):
        if self.kind not in ('constant', 'table'):
            raise ValueError('drag kind must be constant or table')
        scalar(self.coefficient, 'drag coefficient')
        if self.kind == 'table':
            x = np.asarray(self.reynolds_nodes, float)
            y = np.asarray(self.coefficient_nodes, float)
            if (x.ndim != 1 or len(x) < 2 or y.shape != x.shape
                    or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y))
                    or np.any(x < 0) or np.any(y < 0) or np.any(np.diff(x) <= 0)):
                raise ValueError('drag table requires increasing Re and matching nonnegative Cd')

    def evaluate(self, reynolds: float) -> float:
        if self.kind == 'constant': return self.coefficient
        return float(np.interp(reynolds, self.reynolds_nodes, self.coefficient_nodes))


@dataclass(frozen=True)
class LiftLaw:
    kind: str = 'linear_spin'
    spin_slope: float = 0.6
    saturation_coefficient: float = 0.3

    def __post_init__(self):
        if self.kind not in ('none', 'linear_spin', 'saturating_spin'):
            raise ValueError('invalid lift kind')
        scalar(self.spin_slope, 'spin_slope')
        scalar(self.saturation_coefficient, 'saturation_coefficient', True)

    def evaluate(self, perpendicular_spin_parameter: float) -> float:
        if self.kind == 'none': return 0.
        linear = self.spin_slope * perpendicular_spin_parameter
        if self.kind == 'linear_spin': return linear
        return float(self.saturation_coefficient * np.tanh(linear / self.saturation_coefficient))


@dataclass(frozen=True)
class Aerodynamics:
    drag: DragLaw = field(default_factory=DragLaw)
    lift: LiftLaw = field(default_factory=LiftLaw)
    spin_decay_per_s: float = 0.
    include_buoyancy: bool = True

    def __post_init__(self):
        scalar(self.spin_decay_per_s, 'spin_decay_per_s')
        if not isinstance(self.include_buoyancy, bool):
            raise ValueError('include_buoyancy must be boolean')


@dataclass(frozen=True)
class InitialState:
    position_m: tuple = (0., 0., 0.11)
    velocity_m_s: tuple = (30., 9., 6.82)
    spin_rad_s: tuple = (0., 0., 0.)

    def array(self):
        return np.concatenate([vector3(self.position_m, 'position_m'),
                               vector3(self.velocity_m_s, 'velocity_m_s'),
                               vector3(self.spin_rad_s, 'spin_rad_s')])


@dataclass(frozen=True)
class Goal:
    plane_x_m: float = 11.
    width_m: float = 7.32
    height_m: float = 2.44

    def __post_init__(self):
        for name in ('plane_x_m', 'width_m', 'height_m'):
            scalar(getattr(self, name), name, True)


@dataclass(frozen=True)
class SolverSettings:
    max_time_s: float = 2.
    max_step_s: float = 0.01
    output_step_s: float = 0.002
    relative_tolerance: float = 1e-9
    absolute_tolerance: float = 1e-11

    def __post_init__(self):
        for name, value in vars(self).items(): scalar(value, name, True)


@dataclass
class ForcingPath:
    """Latent acceleration [m/s^2], linearly interpolated between saved nodes."""
    times_s: np.ndarray
    values_m_s2: np.ndarray

    def __post_init__(self):
        self.times_s = np.array(self.times_s, dtype=float, copy=True)
        self.values_m_s2 = np.array(self.values_m_s2, dtype=float, copy=True)
        if (self.times_s.ndim != 1 or len(self.times_s) < 2 or self.times_s[0] != 0
                or np.any(np.diff(self.times_s) <= 0)
                or self.values_m_s2.shape != (len(self.times_s), 3)
                or not np.all(np.isfinite(self.times_s))
                or not np.all(np.isfinite(self.values_m_s2))):
            raise ValueError('forcing path requires finite increasing times from zero and Nx3 values')

    def at(self, time_s: float) -> np.ndarray:
        if time_s < -1e-12 or time_s > self.times_s[-1] + 1e-12:
            raise ValueError('forcing requested outside its saved time domain')
        return np.array([np.interp(time_s, self.times_s, self.values_m_s2[:, i]) for i in range(3)])


def make_ou_path(duration_s: float, step_s: float, correlation_time_s: float,
                 covariance_m2_s4, seed: int, initial_m_s2=None) -> ForcingPath:
    """Exact OU node transitions; coupling/interpolation is still an approximation.

    covariance_m2_s4 is the stationary covariance of latent b, not position noise.
    initial_m_s2=None samples a stationary initial state; otherwise it is prescribed.
    """
    for name, value in [('duration_s', duration_s), ('step_s', step_s),
                        ('correlation_time_s', correlation_time_s)]: scalar(value, name, True)
    cov = np.asarray(covariance_m2_s4, float)
    if (cov.shape != (3, 3) or not np.all(np.isfinite(cov))
            or not np.allclose(cov, cov.T, atol=1e-12, rtol=0)):
        raise ValueError('OU covariance must be finite symmetric 3x3')
    eig, basis = np.linalg.eigh(cov)
    if eig.min() < -1e-12: raise ValueError('OU covariance must be positive semidefinite')
    root = basis @ np.diag(np.sqrt(np.maximum(eig, 0.)))
    count = int(np.ceil(duration_s / step_s))
    times = np.linspace(0., duration_s, count + 1)
    alpha = np.exp(-(duration_s / count) / correlation_time_s)
    rng = np.random.default_rng(seed)
    values = np.empty((count + 1, 3))
    values[0] = root @ rng.standard_normal(3) if initial_m_s2 is None else vector3(initial_m_s2, 'initial_m_s2')
    innovations = rng.standard_normal((count, 3)) @ root.T
    scale = np.sqrt(-np.expm1(-2 * (duration_s / count) / correlation_time_s))
    for k in range(count): values[k + 1] = alpha * values[k] + scale * innovations[k]
    return ForcingPath(times, values)


@dataclass(frozen=True)
class PhysicsModel:
    ball: Ball = field(default_factory=Ball)
    air: Air = field(default_factory=Air)
    aero: Aerodynamics = field(default_factory=Aerodynamics)

    def forces(self, state, latent_acceleration_m_s2=(0., 0., 0.)) -> dict:
        state = np.asarray(state, float)
        if state.shape != (9,) or not np.all(np.isfinite(state)):
            raise ValueError('state must be a finite vector of length 9')
        b = vector3(latent_acceleration_m_s2, 'latent_acceleration_m_s2')
        u = state[3:6] - np.asarray(self.air.wind_m_s)
        speed = float(np.linalg.norm(u))
        spin_cross_u = np.cross(state[6:9], u)
        cross_norm = float(np.linalg.norm(spin_cross_u))
        reynolds = self.air.density_kg_m3 * speed * 2 * self.ball.radius_m / self.air.dynamic_viscosity_pa_s
        cd = self.aero.drag.evaluate(reynolds)
        pressure_area = .5 * self.air.density_kg_m3 * self.ball.area_m2 * speed ** 2
        gravity = np.array([0., 0., -self.ball.mass_kg * self.air.gravity_m_s2])
        buoyancy = np.array([0., 0., self.air.density_kg_m3 * self.ball.volume_m3 * self.air.gravity_m_s2]) if self.aero.include_buoyancy else np.zeros(3)
        drag = np.zeros(3)
        magnus = np.zeros(3)
        residual = np.zeros(3)
        spin_parameter = 0.
        cl = 0.
        if speed > 1e-12:
            direction = u / speed
            drag = -pressure_area * cd * direction
            residual = self.ball.mass_kg * (b - direction * np.dot(direction, b))
            if cross_norm > 0.:
                spin_parameter = self.ball.radius_m * cross_norm / speed ** 2
                cl = self.aero.lift.evaluate(spin_parameter)
                magnus = pressure_area * cl * spin_cross_u / cross_norm
        # At exactly zero relative flow all aerodynamic forces are defined as zero.
        return {'gravity_N': gravity, 'buoyancy_N': buoyancy, 'drag_N': drag,
                'magnus_N': magnus, 'residual_N': residual,
                'net_N': gravity + buoyancy + drag + magnus + residual,
                'spin_torque_N_m': -self.ball.shell_inertia_kg_m2 * self.aero.spin_decay_per_s * state[6:9],
                'airspeed_m_s': speed, 'reynolds': reynolds, 'Cd': cd,
                'Cl': cl, 'perpendicular_spin_parameter': spin_parameter}

    def derivative(self, time_s: float, state: np.ndarray, forcing: ForcingPath | None = None):
        b = np.zeros(3) if forcing is None else forcing.at(time_s)
        force = self.forces(state, b)
        return np.r_[state[3:6], force['net_N'] / self.ball.mass_kg,
                     -self.aero.spin_decay_per_s * state[6:9]]


@dataclass
class Trajectory:
    times_s: np.ndarray
    states: np.ndarray
    status: str
    goal: Goal
    model: PhysicsModel
    forcing: ForcingPath | None
    _dense: Callable | None = field(repr=False, default=None)

    def sample_at(self, times_s):
        t = np.atleast_1d(np.asarray(times_s, float))
        if t.ndim != 1 or not np.all(np.isfinite(t)) or np.any(t < 0) or np.any(t > self.times_s[-1] + 1e-12):
            raise ValueError('sample times must lie within the integrated trajectory')
        return np.repeat(self.states[:1], len(t), axis=0) if self._dense is None else self._dense(t).T

    def summary(self):
        end = self.states[-1]
        reached = self.status == 'goal_plane'
        inside = bool(abs(end[1]) < self.goal.width_m / 2 and 0 < end[2] < self.goal.height_m) if reached else None
        margin = float(min(self.goal.width_m / 2 - abs(end[1]), end[2], self.goal.height_m - end[2]) - self.model.ball.radius_m) if reached else None
        re_values = [self.model.forces(s)['reynolds'] for s in self.states]
        drag = self.model.aero.drag
        outside_table = bool(drag.kind == 'table' and (min(re_values) < drag.reynolds_nodes[0] or max(re_values) > drag.reynolds_nodes[-1]))
        return {'status': self.status, 'time_s': float(self.times_s[-1]),
                'position_m': end[:3].tolist(), 'velocity_m_s': end[3:6].tolist(),
                'spin_rad_s': end[6:9].tolist(),
                'center_inside_goal_rectangle': inside,
                'ball_clearance_margin_at_center_plane_m': margin,
                'clearance_is_not_a_goalpost_collision_simulation': True,
                'minimum_reynolds': float(min(re_values)), 'maximum_reynolds': float(max(re_values)),
                'drag_table_outside_range_clamped': outside_table,
                'probability_estimated': False, 'parameters_fitted': False}


def simulate(model: PhysicsModel, initial: InitialState, settings: SolverSettings | None = None,
             goal: Goal | None = None, forcing: ForcingPath | None = None) -> Trajectory:
    settings = settings or SolverSettings()
    goal = goal or Goal()
    start = initial.array()
    if start[0] >= goal.plane_x_m: raise ValueError('initial x must be before the goal plane')
    if start[2] < model.ball.radius_m: raise ValueError('ball center starts below the ground contact height')
    if forcing is not None and forcing.times_s[-1] < settings.max_time_s:
        raise ValueError('forcing must cover max_time_s')
    initial_derivative = model.derivative(0., start, forcing)
    if start[2] == model.ball.radius_m and (start[5] < 0 or (start[5] == 0 and initial_derivative[5] <= 0)):
        return Trajectory(np.array([0.]), start[None, :], 'ground_contact', goal, model, forcing)

    def goal_event(time_s, state): return state[0] - goal.plane_x_m
    def ground_event(time_s, state): return state[2] - model.ball.radius_m
    goal_event.direction = 1
    goal_event.terminal = True
    ground_event.direction = -1
    ground_event.terminal = True
    solution = solve_ivp(lambda t, s: model.derivative(t, s, forcing),
                         (0., settings.max_time_s), start, method='DOP853', dense_output=True,
                         events=[goal_event, ground_event], max_step=settings.max_step_s,
                         rtol=settings.relative_tolerance, atol=settings.absolute_tolerance)
    if not solution.success: raise RuntimeError(solution.message)
    status = 'goal_plane' if len(solution.t_events[0]) else 'ground_contact' if len(solution.t_events[1]) else 'time_limit'
    end = float(solution.t[-1])
    times = np.r_[np.arange(0., end, settings.output_step_s), end]
    return Trajectory(times, solution.sol(times).T, status, goal, model, forcing, solution.sol)
