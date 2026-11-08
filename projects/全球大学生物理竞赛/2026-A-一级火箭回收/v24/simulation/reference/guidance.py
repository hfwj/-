"""Illustrative two-burn policy, with no third ignition.
Baseline uses a 55 km entry cutoff. Parameterized search
instead terminates entry at a specified cutoff speed.
Engine lag, minimum throttle, and staging are not included.
"""
import numpy as np
from .dynamics import air_load
from .environment import Constants

class TwoBurnPolicy:
    def __init__(self, ignition=75000., cutoff=None,
                 multiplier=1.1, target=1.5):
        self.he, self.vcut = ignition, cutoff
        self.k, self.target = multiplier, target
        self.phase = 0
        self.c = Constants()

    def __call__(self, t, y, env):
        _, h, u, w, mass = y
        drag, q, relative = air_load(t, y, env, self.c)
        speed = np.hypot(u, w)
        if mass <= self.c.dry:
            return np.zeros(2)
        if self.phase == 0 and w < 0 and h <= self.he:
            self.phase = 1
        if self.phase == 1:
            done = (h <= 55000.) if self.vcut is None else (
                np.linalg.norm(relative) <= self.vcut)
            if done:
                self.phase = 2
            else:
                return -self.c.thrust_max * relative / max(
                    np.linalg.norm(relative), 1e-12)
        gravity = self.c.mu / (self.c.radius + h)**2
        net = self.c.thrust_max / mass - gravity
        distance = max(speed**2-self.target**2, 0.) / (
            2 * max(net, 1e-12))
        if self.phase == 2 and h <= self.k * distance:
            self.phase = 3
        if self.phase == 3:
            force = mass * ((speed**2-self.target**2)
                / (2*max(h, 1.)) + gravity*abs(w)
                / max(speed, 1e-12)) - np.linalg.norm(drag)
            if q > 47500.:
                force = self.c.thrust_max
            return -np.clip(force, 0., self.c.thrust_max) * (
                np.array([u, w]) / max(speed, 1e-12))
        return np.zeros(2)
