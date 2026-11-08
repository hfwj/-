"""Reference interfaces; aerodynamic tables must be supplied."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Constants:
    dry: float = 130000.0
    radius: float = 6371000.0
    mu: float = 3.986e14
    g0: float = 9.80665
    isp: float = 330.0
    diameter: float = 7.0
    thrust_max: float = 7.0e6

    @property
    def area(self):
        return np.pi * self.diameter**2 / 4.0

class Environment:
    def __init__(self, heights, densities, sounds,
                 mach, drag, wind):
        self.h = np.asarray(heights, dtype=float)
        self.rho = np.asarray(densities, dtype=float)
        self.a = np.asarray(sounds, dtype=float)
        self.mach = np.asarray(mach, dtype=float)
        self.cd = np.asarray(drag, dtype=float)
        self.wind = wind
        assert len(self.h) == len(self.rho) == len(self.a)
        assert len(self.mach) == len(self.cd)
        assert len(self.h) >= 2 and len(self.mach) >= 2
        assert np.all(np.diff(self.h) > 0)
        assert np.all(np.diff(self.mach) > 0)
        assert np.all(self.rho > 0) and np.all(self.a > 0)
        assert np.all(self.cd >= 0)

    def sample(self, h, speed):
        if not self.h[0] <= h <= self.h[-1]:
            raise ValueError("Atmosphere does not cover altitude")
        rho = np.exp(np.interp(h, self.h, np.log(self.rho)))
        sound = np.interp(h, self.h, self.a)
        mach = speed / sound
        if not self.mach[0] <= mach <= self.mach[-1]:
            raise ValueError("Drag table does not cover Mach")
        return rho, np.interp(mach, self.mach, self.cd)
