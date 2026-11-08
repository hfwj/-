"""USSA1976 lower-atmosphere helper copied unchanged in equations from v1.
Source: NASA-TM-X-74335. Used only over geometric 0--70 km.

Atmosphere: constant-composition lower-atmosphere equations of USSA 1976,
lower part used to geometric ~86 km. Above it, an explicitly H-class 7 km scale-height density extrapolation is used to 220 km.
"""
from pathlib import Path
import csv
import json
import math

G0 = 9.80665
R_AIR = 8314.32 / 28.9644
R_ATM = 6356766.0
R_E = 6371000.0
GM_E = 3.986004418e14
GAMMA = 1.4
HB = [0., 11000., 20000., 32000., 47000., 51000., 71000., 84852.]
LAPSE = [-.0065, 0., .001, .0028, 0., -.0028, -.002]


def layer_state(t_base, p_base, delta_h, lapse):
    t = t_base + lapse * delta_h
    if lapse == 0:
        p = p_base * math.exp(-G0 * delta_h / (R_AIR * t_base))
    else:
        p = p_base * (t_base / t) ** (G0 / (R_AIR * lapse))
    return t, p


BASES = [(288.15, 101325.)]
for i, lapse in enumerate(LAPSE):
    BASES.append(layer_state(*BASES[-1], HB[i + 1] - HB[i], lapse))


def atmosphere(h_m):
    if not math.isfinite(h_m) or not 0 <= h_m <= 220000:
        raise ValueError('This scenario implementation is restricted to geometric 0--220000 m.')
    ztop=R_ATM*HB[-1]/(R_ATM-HB[-1])
    if h_m>ztop:
        top=atmosphere(ztop-1e-6);rho=top['density_kg_m3']*math.exp(-(h_m-ztop)/7000.)
        return dict(h_geometric_m=h_m,H_geopotential_m=R_ATM*h_m/(R_ATM+h_m),temperature_K=top['temperature_K'],pressure_Pa=rho*R_AIR*top['temperature_K'],density_kg_m3=rho,sound_speed_m_s=top['sound_speed_m_s'])
    H = R_ATM * h_m / (R_ATM + h_m)
    i = max(i for i, hb in enumerate(HB[:-1]) if H >= hb)
    t, p = layer_state(*BASES[i], H - HB[i], LAPSE[i])
    return dict(h_geometric_m=h_m, H_geopotential_m=H,
                temperature_K=t, pressure_Pa=p,
                density_kg_m3=p / (R_AIR * t),
                sound_speed_m_s=math.sqrt(GAMMA * R_AIR * t),
                dynamic_viscosity_Pa_s=1.458e-6 * t ** 1.5 / (t + 110.4),
                gravity_m_s2=GM_E / (R_E + h_m) ** 2)
