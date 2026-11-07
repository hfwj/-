"""Analytical limits, force invariants, event handling and OU numerical checks."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest
import numpy as np
from physics_model import (Ball, Air, DragLaw, LiftLaw, Aerodynamics, InitialState,
                           PhysicsModel, SolverSettings, ForcingPath, make_ou_path, simulate)


class PhysicsChecks(unittest.TestCase):
    metrics = {}

    def test_ballistic_limit(self):
        model = PhysicsModel(aero=Aerodynamics(DragLaw(coefficient=0), LiftLaw(kind='none'), include_buoyancy=False))
        initial = InitialState()
        tr = simulate(model, initial)
        t = 11 / 30
        expected = np.array([11, 9*t, .11 + 6.82*t - .5*9.81*t*t])
        error = float(np.max(np.abs(tr.states[-1, :3]-expected)))
        self.assertEqual(tr.status, 'goal_plane')
        self.assertLess(error, 1e-9)
        self.metrics['ballistic_goal_error_m'] = error

    def test_buoyancy_limit(self):
        model = PhysicsModel(aero=Aerodynamics(DragLaw(coefficient=0), LiftLaw(kind='none')))
        tr = simulate(model, InitialState())
        t = 11/30
        reduced_g = 9.81*(1-model.air.density_kg_m3*model.ball.volume_m3/model.ball.mass_kg)
        self.assertAlmostEqual(tr.states[-1, 2], .11+6.82*t-.5*reduced_g*t*t, places=9)
        self.metrics['buoyancy_weight_ratio'] = model.air.density_kg_m3*model.ball.volume_m3/model.ball.mass_kg

    def test_zero_flow_and_zero_spin_are_finite(self):
        model = PhysicsModel(air=Air(wind_m_s=(4, 2, 1)))
        state = np.r_[[0, 0, .2], [4, 2, 1], [2, 5, 10]]
        f = model.forces(state, (1, 2, 3))
        for name in ['drag_N', 'magnus_N', 'residual_N']:
            np.testing.assert_array_equal(f[name], np.zeros(3))
        state[3:6] = [30, 9, 6]
        state[6:9] = 0
        np.testing.assert_array_equal(model.forces(state)['magnus_N'], np.zeros(3))

    def test_magnus_closure_and_orthogonality(self):
        model = PhysicsModel()
        state = np.r_[[0, 0, .11], [30., 9., 6.], [2., -7., -10.]]
        f = model.forces(state, (1, -2, 3))
        u = state[3:6]
        gain = .5*model.air.density_kg_m3*model.ball.area_m2*model.aero.lift.spin_slope*model.ball.radius_m
        np.testing.assert_allclose(f['magnus_N'], gain*np.cross(state[6:9], u), rtol=1e-13)
        self.assertLess(abs(float(f['magnus_N']@u)), 1e-12)
        self.assertLess(abs(float(f['residual_N']@u)), 1e-12)
        doubled = state.copy(); doubled[3:6] *= 2
        np.testing.assert_allclose(model.forces(doubled)['magnus_N'], 2*f['magnus_N'], rtol=1e-13)
        self.metrics['magnus_dot_relative_velocity_N_m_s'] = float(f['magnus_N']@u)

    def test_saturating_lift_bound(self):
        model = PhysicsModel(aero=Aerodynamics(lift=LiftLaw(kind='saturating_spin')))
        state = np.r_[[0, 0, .11], [30., 0, 0], [0, 0, 10000.]]
        f = model.forces(state)
        limit = .5*model.air.density_kg_m3*model.ball.area_m2*30**2*.3
        self.assertLessEqual(np.linalg.norm(f['magnus_N']), limit*(1+1e-14))

    def test_relative_wind_and_drag_dissipation(self):
        state = np.r_[[0, 0, .11], [30., 9., 6.], [1., -2., -10.]]
        first = PhysicsModel()
        wind = np.array([4., 3., -1.])
        shifted = state.copy(); shifted[3:6] += wind
        second = PhysicsModel(air=Air(wind_m_s=tuple(wind)))
        np.testing.assert_allclose(first.forces(state)['net_N'], second.forces(shifted)['net_N'])
        self.assertLess(float(first.forces(state)['drag_N']@state[3:6]), 0)

    def test_spin_decay(self):
        model = PhysicsModel(aero=Aerodynamics(spin_decay_per_s=.5))
        initial = InitialState(spin_rad_s=(2, -10, -8))
        tr = simulate(model, initial)
        expected = np.asarray(initial.spin_rad_s)*np.exp(-.5*tr.times_s[-1])
        np.testing.assert_allclose(tr.states[-1, 6:9], expected, rtol=1e-11)

    def test_reflection_symmetry(self):
        model = PhysicsModel()
        a = simulate(model, InitialState(velocity_m_s=(30, 0, 6.82), spin_rad_s=(0, 0, 10)))
        b = simulate(model, InitialState(velocity_m_s=(30, 0, 6.82), spin_rad_s=(0, 0, -10)))
        np.testing.assert_allclose(a.states[-1, :3]*[1, -1, 1], b.states[-1, :3], atol=1e-10)
        self.assertAlmostEqual(a.times_s[-1], b.times_s[-1], places=10)

    def test_drag_only_horizontal_direction(self):
        tr = simulate(PhysicsModel(), InitialState())
        self.assertLess(np.max(np.abs(tr.states[:, 1]-.3*tr.states[:, 0])), 1e-11)

    def test_no_wind_translational_energy(self):
        model = PhysicsModel(aero=Aerodynamics(spin_decay_per_s=.5))
        tr = simulate(model, InitialState(spin_rad_s=(0, -10, -10)))
        potential_mass = model.ball.mass_kg-model.air.density_kg_m3*model.ball.volume_m3
        energy = .5*model.ball.mass_kg*np.sum(tr.states[:, 3:6]**2, axis=1) + potential_mass*9.81*tr.states[:, 2]
        self.assertLessEqual(float(np.diff(energy).max()), 1e-8)
        self.metrics['no_wind_energy_drop_J'] = float(energy[0]-energy[-1])

    def test_ground_and_time_limit_events(self):
        model = PhysicsModel(aero=Aerodynamics(DragLaw(coefficient=0), LiftLaw(kind='none'), include_buoyancy=False))
        ground = simulate(model, InitialState(velocity_m_s=(5, 0, .1)))
        self.assertEqual(ground.status, 'ground_contact')
        self.assertAlmostEqual(ground.times_s[-1], 2*.1/9.81, places=10)
        initial_ground = simulate(model, InitialState(velocity_m_s=(5, 0, 0)))
        self.assertEqual(initial_ground.times_s[-1], 0.)
        limit = simulate(model, InitialState(velocity_m_s=(1, 0, 20)), SolverSettings(max_time_s=.05))
        self.assertEqual(limit.status, 'time_limit')
        with self.assertRaises(ValueError): limit.sample_at([.1])
        with self.assertRaises(ValueError): simulate(model, InitialState(position_m=(0, 0, .10)))

    def test_drag_table_and_invalid_inputs(self):
        table = DragLaw(kind='table', reynolds_nodes=(0, 1e5, 5e5), coefficient_nodes=(.5, .4, .2))
        self.assertAlmostEqual(table.evaluate(3e5), .3)
        self.assertAlmostEqual(table.evaluate(8e5), .2)
        limited = DragLaw(kind='table', reynolds_nodes=(1e5, 2e5), coefficient_nodes=(.4, .2))
        tr = simulate(PhysicsModel(aero=Aerodynamics(drag=limited)), InitialState())
        self.assertTrue(tr.summary()['drag_table_outside_range_clamped'])
        for builder in [lambda: Ball(mass_kg=-1), lambda: Air(wind_m_s=(0, np.nan, 0)),
                        lambda: DragLaw(coefficient=-.1),
                        lambda: DragLaw(kind='table', reynolds_nodes=(2, 1), coefficient_nodes=(.2, .3)),
                        lambda: make_ou_path(1, .01, 0, np.eye(3), 1),
                        lambda: make_ou_path(1, .01, .1, np.diag([1, -1, 1]), 1)]:
            with self.subTest(builder=builder):
                with self.assertRaises(ValueError): builder()

    def test_deterministic_step_convergence(self):
        initial = InitialState(spin_rad_s=(0, -10, -10))
        positions = []
        for step in [.02, .01, .005]:
            tr = simulate(PhysicsModel(), initial, SolverSettings(max_step_s=step))
            positions.append(tr.states[-1, :3])
        spread = float(np.max(np.ptp(np.array(positions), axis=0)))
        self.assertLess(spread, 1e-7)
        self.metrics['deterministic_step_goal_spread_m'] = spread

    def test_ou_stationary_moments_and_correlation(self):
        cov = np.array([[.16, .06, 0], [.06, .36, 0], [0, 0, .09]])
        path = make_ou_path(1000., .01, .05, cov, 9182)
        observed = np.cov(path.values_m_s2.T)
        relative = float(np.linalg.norm(observed-cov)/np.linalg.norm(cov))
        corr = float(np.corrcoef(path.values_m_s2[:-1, 1], path.values_m_s2[1:, 1])[0, 1])
        self.assertLess(relative, .06)
        self.assertLess(abs(corr-np.exp(-.2)), .02)
        self.assertLess(np.max(np.abs(path.values_m_s2.mean(axis=0))/np.sqrt(np.diag(cov))), .04)
        self.metrics['ou_empirical_covariance_relative_error'] = relative
        self.metrics['ou_empirical_lag1_correlation'] = corr
        self.metrics['ou_theoretical_lag1_correlation'] = float(np.exp(-.2))

    def test_ou_coupling_refinement_same_underlying_nodes(self):
        fine = make_ou_path(.6, .0005, .08, np.diag([0., .25, .09]), 1234, [0, 0, 0])
        settings = SolverSettings(max_time_s=.6, max_step_s=.001, relative_tolerance=1e-8, absolute_tolerance=1e-10)
        model = PhysicsModel()
        initial = InitialState(spin_rad_s=(0, -10, -10))
        reference = simulate(model, initial, settings, forcing=fine).states[-1, :3]
        errors = []
        for stride in [8, 4, 2]:
            coarse = ForcingPath(fine.times_s[::stride], fine.values_m_s2[::stride])
            tr = simulate(model, initial, settings, forcing=coarse)
            errors.append(float(np.linalg.norm(tr.states[-1, :3]-reference)))
        self.assertLess(errors[-1], .002)
        self.assertLess(errors[-1], errors[0])
        self.metrics['ou_same_nodes_refinement_goal_errors_m'] = errors


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PhysicsChecks)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    report = {'scope': 'Analytical/numerical model checks, not observed-ball calibration or experimental validation.',
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'passed': result.wasSuccessful(), 'metrics': PhysicsChecks.metrics,
              'parameter_inference_performed': False, 'experimental_validation_performed': False}
    path = Path(__file__).parent.parent/'results/logs/physics_validation.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
