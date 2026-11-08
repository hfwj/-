# Complete new simulation, not a reconstruction of the unavailable old program

Linux/WSL with Python 3, numpy, scipy, matplotlib and g++ is sufficient to recompute all numerical outputs. XeLaTeX, latexmk and PyMuPDF (for PDF checks) are additionally needed to rebuild the PDF.

From the v25 project root:

```
python simulation/reproduce.py
python simulation/reproduce.py --latex
```

The default pipeline creates missing output directories, builds the C++ shared library, searches 90, 100, ... t until the first passing load is found, freezes that control vector, runs 0.02/0.01/0.005 s, runs three policies and fixed-control perturbations, checks vacuum invariants and other identities, and regenerates every numerical table/plot. `--latex` additionally compiles reports/latex/main.tex and copies reports/856A.pdf.

- `config.json`: every aerodynamic anchor, atmosphere continuation, wind node, physical/engine parameter, acceptance limit, control threshold and objective scale.
- `core.cpp`: complete dynamics, actuator/controller, all event guards and RK4 with event bisection. `config.h` is generated from JSON; the checked-in copy is also printed in the paper.
- `model.py`: compilation and ctypes interface; no previous manuscript data are loaded.
- `search.py`: deterministic grid, three-start bounded Powell and ordered neighbor refinement. Full statuses are retained; a finite search is not a global optimum proof.
- `analyze.py`: freezes the selected controls for all three step sizes and policy comparisons. The S2 trajectory is the same data file as the fine convergence run.
- `sensitivity.py`: changes one stated assumption at a time in clean child processes and restores the exact nominal config in a finally block. Vacuum tests use zero drag with entry disabled.
- `publish.py`: generates tables, plots, full-precision CSVs, verification records, software/source manifest, and printed code selections.
- `reproduce.py`: entry point invoking the entire pipeline.

The old 106.6 t consumption and 110–112 t recommendation are neither inputs nor fitting targets. All current values are model-specific, based on explicit H assumptions. Fixed axial drag and a kinematic thrust-axis lag are not calibrated six-degree-of-freedom physics. A nominal pass does not certify flight safety or capture at a fixed ship under uncertain wind.

The no-contact penalty is dimensionless. All seven soft residual scales and the separate hard screen are specified in config.json and the paper's Eq. (11)/penalty table. Engine shutdown is instantaneous; remaining engines retain actual throttle at count changes. A later engine-count reduction does not create a new ignition.

Full-precision JSON/CSV values, not rounded PDF table entries, define numerical comparisons. The small step differences measure numerical sensitivity only. The event-located hybrid solution is not assumed globally fourth order.

Configuration units are SI, except keys ending in _DEG (degrees). Heights and wind are m and m/s; thrust is N; masses and objective mass scales are kg. The run() load argument and load-search increment are tonnes; internal mass is kg. Axis state is radians.
