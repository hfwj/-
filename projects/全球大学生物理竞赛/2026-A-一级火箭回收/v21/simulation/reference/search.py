"""Bounded Powell plus local grid; requires a case evaluator.
The normalized penalty below is a reference implementation,
not a claim to recover the manuscript's numerical optima.
"""
from itertools import product
import numpy as np
from scipy.optimize import minimize

LOW = np.array([35000., 450., .95, .5])
HIGH = np.array([82000., 1150., 1.60, 3.0])


def physical(z):
    return LOW + np.asarray(z) * (HIGH - LOW)


def objective(z, evaluate, initial_propellant):
    # evaluate(parameters) returns independent terminal metrics.
    result = evaluate(physical(z))
    if result["event"] != "touchdown":
        return 1.e6
    used = result["used_kg"]
    speed = result["touchdown_mps"]
    pressure = result["qmax_pa"]
    excess = (max(speed/2.5 - 1., 0.)**2
              + max(pressure/50000. - 1., 0.)**2
              + max(used/initial_propellant - 1., 0.)**2)
    return used/initial_propellant + 1000. * excess


def search(evaluate, initial_propellant):
    candidates = []
    for start in [.25, .5, .75]:
        fit = minimize(objective, np.full(4, start),
            args=(evaluate, initial_propellant),
            method="Powell", bounds=[(0., 1.)]*4,
            options={"maxiter": 200, "xtol": 1e-5})
        candidates.append((float(fit.fun), fit.x))
    _, center = min(candidates, key=lambda row: row[0])
    for delta in product([-.02, 0., .02], repeat=4):
        z = np.clip(center + delta, 0., 1.)
        value = objective(z, evaluate, initial_propellant)
        candidates.append((float(value), z))
    value, z = min(candidates, key=lambda row: row[0])
    # Penalties do not replace strict acceptance or replay.
    parameters = physical(z)
    return parameters, evaluate(parameters), value
