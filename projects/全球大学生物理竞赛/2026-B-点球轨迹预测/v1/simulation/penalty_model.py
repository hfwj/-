"""Illustrative effective drag/Magnus model, not a calibrated probabilistic predictor.

Omega is an effective aerodynamic rotation vector in 1/s, not measured ball spin.
Scenario values demonstrate non-unique parameter fits, not physical prior bounds.
"""
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares

R0 = np.array([0., 0., .11])
OBS = np.array([[1.50, .45, .44], [2.96, .86, .74]])
VBAR = (OBS[1] - R0) / .1
E = VBAR / np.linalg.norm(VBAR)
E1 = np.cross(E, [0., 0., 1.])
E1 /= np.linalg.norm(E1)
E2 = np.cross(E, E1)

def rhs(t, state, k, omega):
    v = state[3:]
    return np.r_[v, np.array([0., 0., -9.81]) - k*np.linalg.norm(v)*v + np.cross(omega, v)]

def observe(v0, k, omega):
    return solve_ivp(rhs, (0., .1), np.r_[R0, v0], args=(k, omega), t_eval=[.05, .1], rtol=2e-9, atol=1e-11).y[:3].T

def predict(v0, k, omega):
    def goal(t, s, *args): return s[0]-11.
    def ground(t, s, *args): return s[2]-.11
    goal.terminal = True
    goal.direction = 1
    ground.terminal = True
    ground.direction = -1
    sol = solve_ivp(rhs, (0., 2.), np.r_[R0, v0], args=(k, omega), events=[goal, ground], rtol=2e-9, atol=1e-11, max_step=.02)
    return {'goal_reached': bool(len(sol.t_events[0])), 'time': float(sol.t[-1]), 'position': sol.y[:3,-1].tolist()}

def canonical_fit(lam=0., start=None):
    def unpack(p): return p[:3], p[3], p[4]*E1+p[5]*E2+lam*E
    def residual(p):
        v0, k, omega = unpack(p)
        return (observe(v0, k, omega)-OBS).ravel()
    if start is None: start = [30.4,9.4,6.9,.02,0.,.35]
    fit = least_squares(residual, start, bounds=([1.,-40.,-20.,0.,-4.,-4.],[60.,40.,30.,.1,4.,4.]), x_scale='jac', ftol=1e-11, xtol=1e-11, gtol=1e-11)
    v0, k, omega = unpack(fit.x)
    return fit, v0, k, omega

def run():
    rows=[]
    for lam in [0.,-1.,1.,-2.,2.,-4.,4.]:
        fit,v0,k,omega=canonical_fit(lam)
        rows.append({'parallel_effective_spin_per_s':lam,'v0':v0.tolist(),'k_per_m':float(k),'Omega_per_s':omega.tolist(),'observation_RMSE_m':float(np.sqrt(np.mean(fit.fun**2))),**predict(v0,k,omega)})
    return rows

if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Reproduce illustrative UPC 2026 B scenarios; not a calibrated probabilistic predictor.')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(run(), indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result+'\n', encoding='utf-8')
        print(args.output)
    else:
        print(result)
