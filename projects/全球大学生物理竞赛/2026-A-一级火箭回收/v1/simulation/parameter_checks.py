"""Parameter arithmetic only; no booster trajectory or fuel optimization.

Atmosphere: constant-composition lower-atmosphere equations of USSA 1976,
limited here to geometric altitudes 0--70 km. All outputs are reproducible.
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
    if not math.isfinite(h_m) or not 0 <= h_m <= 70000:
        raise ValueError('This implementation is restricted to geometric 0--70000 m.')
    H = R_ATM * h_m / (R_ATM + h_m)
    i = max(i for i, hb in enumerate(HB[:-1]) if H >= hb)
    t, p = layer_state(*BASES[i], H - HB[i], LAPSE[i])
    return dict(h_geometric_m=h_m, H_geopotential_m=H,
                temperature_K=t, pressure_Pa=p,
                density_kg_m3=p / (R_AIR * t),
                sound_speed_m_s=math.sqrt(GAMMA * R_AIR * t),
                dynamic_viscosity_Pa_s=1.458e-6 * t ** 1.5 / (t + 110.4),
                gravity_m_s2=GM_E / (R_E + h_m) ** 2)


def derive():
    a70 = atmosphere(70000.)
    v = 6000 / 3.6
    return dict(speed_m_s=v, area_ref_m2=math.pi * 7 ** 2 / 4,
                geometric_side_area_m2=65 * 7,
                dry_weight_standard_N=130000 * G0,
                gravity_sea_model_m_s2=GM_E / R_E ** 2,
                gravity_70km_m_s2=GM_E / (R_E + 70000) ** 2,
                mach_initial_no_wind=v / a70['sound_speed_m_s'],
                dynamic_pressure_initial_no_wind_Pa=.5 * a70['density_kg_m3'] * v ** 2,
                virtual_nominal_mass_flow_one_engine_kg_s=1e6 / (320 * G0),
                virtual_one_engine_max_dry_TWR=1.1e6 / (130000 * G0),
                virtual_two_engine_max_dry_TWR=2.2e6 / (130000 * G0),
                virtual_two_engine_max_support_mass_kg=2.2e6 / G0,
                methane_fraction_at_OF_3p4=1 / 4.4,
                oxygen_fraction_at_OF_3p4=3.4 / 4.4)


def check():
    sea = atmosphere(0)
    assert sea['temperature_K'] == 288.15
    assert sea['pressure_Pa'] == 101325
    assert abs(sea['density_kg_m3'] - 1.225) < 1e-6
    assert abs(sea['sound_speed_m_s'] - 340.294) < .001
    continuity = []
    for i in range(1, 6):
        left = layer_state(*BASES[i-1], HB[i] - HB[i-1], LAPSE[i-1])
        right = layer_state(*BASES[i], 0., LAPSE[i])
        assert all(abs(x-y) < 1e-10 for x, y in zip(left, right))
        continuity.append(HB[i])
    samples = [atmosphere(h) for h in range(0, 70001, 100)]
    assert all(a['pressure_Pa'] > b['pressure_Pa'] for a, b in zip(samples, samples[1:]))
    d = derive()
    assert 0 < d['virtual_one_engine_max_dry_TWR'] < 1
    assert d['virtual_two_engine_max_dry_TWR'] > 1
    assert abs(d['methane_fraction_at_OF_3p4'] + d['oxygen_fraction_at_OF_3p4'] - 1) < 1e-12
    rejected = []
    for value in [-1., 70001., float('nan')]:
        try:
            atmosphere(value)
        except ValueError:
            rejected.append(str(value))
    assert len(rejected) == 3
    return dict(status='PASS', checks=['sea-level T/p/rho/a benchmark',
                'layer-boundary T/p continuity', 'pressure decreases on 100 m grid',
                'virtual thrust feasibility and mixture mass balance', 'out-of-domain rejection'],
                internal_geopotential_boundaries_checked_m=continuity,
                limits='Arithmetic checks only. No real booster calibration, trajectory, safety certification, or fuel solution.',
                geometric_70km=atmosphere(70000), derived=derive())


def main():
    root = Path(__file__).resolve().parents[1]
    data = root / 'results/data'
    logs = root / 'results/logs'
    data.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    rows = [atmosphere(float(h)) for h in range(0, 70001, 10000)]
    with (data / 'standard_atmosphere_0_70km.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (data / 'derived_parameters.json').write_text(json.dumps(derive(), ensure_ascii=False, indent=2) + '\n')
    result = check()
    (logs / 'parameter_checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
