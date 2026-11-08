"""Approximate planar closure used in the displayed equations.
No local-basis curvature, rotation, lift, or attitude dynamics.
This module is not a reproduction of the tabulated results.
"""
import numpy as np
from .environment import Constants


def air_load(t, state, env, constants=Constants()):
    _, h, u, w, _ = state
    wind = np.asarray(env.wind(t, max(h, 0.0)), dtype=float)
    relative = np.array([u, w]) - wind
    speed = np.linalg.norm(relative)
    rho, cd = env.sample(max(h, 0.0), speed)
    q = 0.5 * rho * speed**2
    if speed == 0.0:
        return np.zeros(2), q, relative
    force = -q * cd * constants.area * relative / speed
    return force, q, relative


def rhs(t, state, command, env, constants=Constants()):
    # command is a fixed force vector for this substep.
    _, h, u, w, mass = state
    if mass < constants.dry - 1e-6:
        raise ValueError("Dry-mass boundary crossed")
    thrust = np.asarray(command, dtype=float)
    magnitude = np.linalg.norm(thrust)
    if magnitude > constants.thrust_max * (1 + 1e-12):
        raise ValueError("Requested thrust exceeds limit")
    drag, _, _ = air_load(t, state, env, constants)
    gravity = constants.mu / (constants.radius + h)**2
    accel = (thrust + drag) / mass
    return np.array([
        constants.radius * u / (constants.radius + h),
        w,
        accel[0],
        accel[1] - gravity,
        -magnitude / (constants.isp * constants.g0)
    ])
