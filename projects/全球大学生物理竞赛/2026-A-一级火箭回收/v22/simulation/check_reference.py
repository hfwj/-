"""Basic identities; does not validate any tabulated mission."""
import json
import numpy as np
from reference.environment import Constants, Environment
from reference.dynamics import rhs, air_load
from reference.integrator import rk4, propagate
from reference.guidance import TwoBurnPolicy
from reference.search import search, LOW, HIGH
from pathlib import Path

c = Constants()
env = Environment([0., 200000.], [1e-20, 1e-20],
                  [340., 340.], [0., 20.], [0., 0.],
                  lambda t, h: [0., 0.])
errors = []
for n in [4, 8, 16]:
    y = np.array([1.])
    for i in range(n):
        y = rk4(lambda t, y: y, i/n, y, 1/n)
    errors.append(float(abs(y[0] - np.e)))
assert 14 < errors[0]/errors[1] < 18
assert 14 < errors[1]/errors[2] < 18
state = np.array([0., 1000., 100., -50., 150000.])
force = np.array([0., 1e6])
out = rhs(0., state, force, env)
assert np.isclose(out[4], -1e6/(c.isp*c.g0))
dense = Environment([0., 200000.], [1.2, .001],
                    [340., 340.], [0., 20.], [.5, .5],
                    lambda t, h: [8., 0.])
drag, q, relative = air_load(0., state, dense)
assert drag @ relative < 0 and q > 0
initial = [0., 100., 0., 0., c.dry]
hist, event = propagate(initial, lambda *args: [0., 0.], env)
assert event == 'touchdown' and hist[-1, 2] == 0
assert np.all(hist[:, 5] >= c.dry - 1e-6)
powered, status = propagate([0., 10000., 0., 0., c.dry+100.],
    lambda *args: [0., 1e6], env, stop_time=1.)
assert np.isclose(powered[-1, 5], c.dry, atol=1e-6)
assert np.all(powered[:, 5] >= c.dry-1e-6)
policy = TwoBurnPolicy()
assert np.all(policy(0., [0., 70000., 1000., 1000., 240000.], env) == 0)
command = policy(1., [0., 75000., 1000., -1000., 240000.], env)
assert np.isclose(np.linalg.norm(command), c.thrust_max)
target = LOW + .4*(HIGH-LOW)
def evaluate(x):
    delta = (x-target)/(HIGH-LOW)
    return dict(event='touchdown', used_kg=100000.+1000.*float(delta@delta),
                touchdown_mps=1., qmax_pa=40000.)
x, result, value = search(evaluate, 200000.)
assert np.max(abs((x-target)/(HIGH-LOW))) < 1e-3
report = dict(rk4_smooth_error_ratios=[errors[0]/errors[1], errors[1]/errors[2]],
              thrust_mass_flow='PASS', drag_opposes_relative_flow='PASS',
              touchdown_event='PASS', dry_mass_bound='PASS', fuel_exhaustion_split='PASS',
              two_burn_coast_and_entry='PASS', bounded_toy_search='PASS',
              mission_table_reproduction=False)
root = Path(__file__).resolve().parents[1]
(root/'results/data').mkdir(parents=True, exist_ok=True)
(root/'results/data/reference_code_checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
