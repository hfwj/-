"""RK4 for smooth substeps; touchdown event interpolation."""
import numpy as np
from .dynamics import rhs
from .environment import Constants


def rk4(fun, t, y, dt):
    k1 = fun(t, y)
    k2 = fun(t + dt/2, y + dt*k1/2)
    k3 = fun(t + dt/2, y + dt*k2/2)
    k4 = fun(t + dt, y + dt*k3)
    return y + dt*(k1 + 2*k2 + 2*k3 + k4)/6


def propagate(initial, policy, env, dt=0.02,
              stop_time=1000.0, constants=Constants()):
    t, y = 0.0, np.asarray(initial, dtype=float)
    if dt <= 0 or stop_time <= 0 or y[1] <= 0:
        raise ValueError("Invalid integration interval")
    history = [(t, *y)]
    while t < stop_time:
        command = np.asarray(policy(t, y, env), dtype=float)
        force = np.linalg.norm(command)
        step = min(dt, stop_time - t)
        if force:
            available = max(y[4] - constants.dry, 0.0)
            if available == 0.0:
                command = np.zeros(2)
            else:
                step = min(step, available * constants.isp
                           * constants.g0 / force)
        fun = lambda tt, yy: rhs(tt, yy, command, env,
                                  constants)
        trial = rk4(fun, t, y, step)
        if trial[1] <= 0.0:
            fraction = y[1] / (y[1] - trial[1])
            landing = y + fraction * (trial - y)
            landing[1] = 0.0
            history.append((t + fraction*step, *landing))
            return np.asarray(history), "touchdown"
        t, y = t + step, trial
        history.append((t, *y))
    return np.asarray(history), "timeout"
