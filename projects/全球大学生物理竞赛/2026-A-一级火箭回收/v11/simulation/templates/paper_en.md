Team @@TEAM@@

Problem A

# A Conditional Propellant Estimate for Shipboard Booster Recovery: Trajectory Optimization, Attitude Feasibility, and Safety Limits {.unnumbered .unlisted}

We develop a staged model for a first-stage booster separating at 70 km with a speed of 6,000 km/h and a dry mass of 130 t. Because the initial flight-path angle, propulsion performance, aerodynamics, and actuator limits are unspecified, the problem does not determine a unique propellant load. We examine an explicitly horizontal, wind-free reference case with spherical gravity, standard atmospheric density, variable mass, constant drag coefficient 0.5, and a virtual three-engine propulsion system with specific impulse 320 s. Direct multiple shooting finds a nominal trajectory carrying approximately 149 t of liquid oxygen and methane, consuming approximately 148 t before a center-of-gravity reference endpoint. The selected strategy coasts for 40 s, performs a three-engine entry burn, and restarts two engines for the final burn. Independent integration gives a flight time of 218 s, a nominal ship range of 206 km, peak dynamic pressure of 47.0 kPa, and a reference descent speed of 1.00 m/s. These are translational-model results, not verified foot-contact conditions. Attitude constraints reveal a required thrust-to-body deflection of at least 24.8 degrees at one high-pressure instant. Nine deterministic perturbations fail the unchanged open-loop plan. We therefore report the propellant value as a reproducible nominal research candidate, not a certified safe load or global minimum, and derive the attitude, contact, and safety checks needed to complete the landing model.

\newpage

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

# 1. Problem interpretation and approach

Recovering a booster requires more than reducing its center-of-gravity speed. The vehicle must survive atmospheric entry, reach a fixed finite deck, orient its body, control both feet or all deployed supports at first contact, and remain stable while its engines shut down. The problem specifies the separation altitude, speed, dry mass, dimensions, and propellant species, and allows the ship to be placed conveniently [1]. It does not specify the initial velocity direction, engine performance, aerodynamic coefficients, body orientation, landing-gear properties, or allowable heating and structural loads.

We address this underdetermination by separating three questions. First, what trajectories are possible in a transparent translational reference model? Second, how much initial propellant does a low-consumption candidate in a restricted strategy family carry? Third, can that candidate satisfy additional attitude and landing requirements? We call the translational model M0. A coupled rigid-body, actuator, and contact model is denoted M1; only its governing relations and necessary feasibility conditions are developed here, not a completed M1 landing simulation.

The principal result is conditional. Approximately 149 t is a reproducible M0 candidate under the stated assumptions. It is not an unconditional answer for an unspecified real booster. The safety analysis supplies concrete reasons for this distinction rather than assuming that attitude control will automatically realize a prescribed thrust vector.

# 2. Assumptions, parameters, and notation

## 2.1 Evidence and modeling choices

We use G for quantities given in the problem, L for literature constants or reference models, H for chosen modeling assumptions, and U for quantities not established by the available information. H values define a numerical scenario; they are not hardware specifications or confidence limits.

@@PARAMETERS@@

The engine family is deliberately virtual. No named production engine is claimed to have these combined properties. There are three installed engines, each with reference thrust 1 MN and steady normalized throttle between 0.3 and 1.1. The last continuous burn uses two engines as a reference scheduling choice, not an optimality theorem. One engine at maximum thrust cannot provide positive low-speed vertical acceleration against even the dry weight, since $1.1\,\mathrm{MN}<130000g_0\approx1.275\,\mathrm{MN}$. Two engines span 0.6--2.2 MN and have a dry-mass hovering throttle near 0.64. Three engines can also hover because their minimum total thrust, 0.9 MN, is below the dry weight; they are not excluded on that basis.

The baseline motion lies in a vertical great-circle plane. Earth is spherical and nonrotating, the atmosphere is at rest, and the ship is fixed after its nominal position is selected. The separation velocity is horizontal, so $v_{t,0}=1666.667\,\mathrm{m\,s^{-1}}$ and $v_{r,0}=0$. These are scenario assumptions, not consequences of the stated speed. An initially upward trajectory may exceed the 70 km density domain used here and requires an extended atmosphere model before further computation.

## 2.2 Notation

@@NOTATION@@

All displayed force equations use SI units. One tonne, written t, is 1,000 kg. The optimizer internally scales altitude, velocity, mass, and thrust to km, km/s, t, and MN; the verification programs use SI variables and independent coordinate formulations.

# 3. Physical scales and preliminary diagnostics

## 3.1 Why gravity, curvature, atmosphere, and variable mass are retained

At separation, $h_0/R=0.0110$ and $g(h_0)=9.61\,\mathrm{m\,s^{-2}}$, compared with $g(0)=9.82\,\mathrm{m\,s^{-2}}$. The curvature acceleration $V_0^2/(R+h_0)\approx0.431\,\mathrm{m\,s^{-2}}$ is not negligible for a trajectory extending roughly 200 km. The initial specific kinetic energy is $1.39\,\mathrm{MJ\,kg^{-1}}$, while the gravitational potential decrease to sea level is about $0.680\,\mathrm{MJ\,kg^{-1}}$. Thus gravity affects both the terminal velocity and the duration of powered braking. A constant-mass approximation is especially inappropriate once the candidate propellant mass is comparable to the dry mass.

A passive diagnostic is useful before optimization. For a dry 130 t body, no thrust, horizontal separation, and the same reference area, integration to the spherical surface gives the following results. These dry-body calculations are explanatory baselines, not predictions for the heavier fueled candidate.

@@PASSIVE@@

Even the higher-drag passive case reaches the surface at hundreds of meters per second and exceeds the assumed 50 kPa screening target. Atmospheric drag therefore helps but does not establish soft landing. These calculations also show why a sea-level terminal-velocity estimate is not a complete impact-speed prediction: the vehicle may not have enough path length to approach that asymptotic speed.

## 3.2 What freedom to position the ship does and does not provide

For a vacuum central-force trajectory, specific angular momentum is conserved:

$$ (R+h)v_t=(R+h_0)V_0. \qquad (1) $$

The horizontal component in the local tangent direction consequently rises to approximately 1,685 m/s at the surface in the horizontal-separation diagnostic. Gravity is conservative and does not dissipate the initial horizontal momentum. The convenient-ship provision avoids an imposed return-to-launch-site maneuver; it does not eliminate the need for terminal horizontal braking. Drag and engine thrust supply the actual dissipative or controlled changes.

We select the ship once at the nominal controlled downrange location. In perturbation tests the nominal ship is not moved to follow a changed endpoint. The approximately 199--202 km passive ranges above and the approximately 206 km controlled range need not agree, since thrust alters the trajectory.

# 4. Variable-mass translational model

## 4.1 Environment and force closure

We use the lower-atmosphere formulation of the U.S. Standard Atmosphere 1976 [2]. Geometric height is converted to geopotential height by

$$ H=\frac{R_a h}{R_a+h},\qquad R_a=6356766\,\mathrm{m}. \qquad (2) $$

Within each geopotential layer, $T_a=T_b+L_b(H-H_b)$. Pressure is obtained from the hydrostatic lapse-rate expression, or its exponential limit when $L_b=0$, and $\rho=p/(R_{\rm air}T_a)$ with $R_{\rm air}=8314.32/28.9644\,\mathrm{J\,kg^{-1}K^{-1}}$. The geometric validity interval of this implementation is 0--70 km. The geopotential conversion radius is not substituted for the gravitational Earth radius.

The reference force laws are

$$ g(h)=\frac{\mu}{(R+h)^2},\quad q=\frac12\rho V^2,\quad D=qC_DA_{\rm ref},\quad A_{\rm ref}=\frac{\pi d^2}{4}. \qquad (3) $$

Earth constants are supported by [3,4]. The constant $C_D=0.5$ and zero lift are scenario choices. Drag depends on shape, orientation, and flow conditions [6], so this closure is not a measured aerodynamic database. Retropropulsion experiments also demonstrate dependence on thrust and vehicle configuration [10]; their coefficients are not transferred to this different booster.

## 4.2 Equations of motion and propellant accounting

With thrust angle $\beta$ measured from the local upward radial direction, the equations are

$$
\begin{aligned}
\dot h &= v_r,\\
\dot v_t &= \frac{T\sin\beta-Dv_t/V}{m}-\frac{v_rv_t}{R+h},\\
\dot v_r &= \frac{T\cos\beta-Dv_r/V}{m}-\frac{\mu}{(R+h)^2}+\frac{v_t^2}{R+h},\\
\dot m &= -\frac{T}{I_{sp}g_0},\qquad \dot\phi=\frac{v_t}{R+h}.
\end{aligned}\qquad (4)
$$

The drag contribution is interpreted as zero when $V=0$. Here all active thrust vectors are parallel, so $T$ equals the sum of engine thrust magnitudes. Specific impulse relates thrust to total propellant mass flow [5]. In a later nonparallel allocation, the vector sum must be used for translation, whereas the sum of thrust magnitudes determines mass flow and the force budget.

Initial total propellant includes oxidizer and methane. With an unusable fraction $f_{\rm un}=0.005$ of the initial load, the usable mass is

$$ m_{\rm use}(t)=m(t)-m_d-f_{\rm un}m_{p,0},\qquad m(0)=m_d+m_{p,0}. \qquad (5) $$

Unusable residue is carried as mass and cannot be burned. The nominal usable reserve target is $m_{\rm res}=2.2\times10^6/(320g_0)=701.055$ kg, equivalent to one second of maximum two-engine thrust. A further 10 kg numerical buffer is imposed during optimization. This is an H reserve definition, not demonstrated disturbance tolerance.

## 4.3 Engine response

A point-mass solution must not exploit instantaneous full thrust. Ignition has a 0.5 s delay. After the delay, actual throttle follows a rate-limited first-order response with time constant 0.1 s and $|\dot u|\le1\,\mathrm{s^{-1}}$. For a full-throttle ignition command at time $t_c$, the modeled response is

$$
u(t)=\begin{cases}
0,&t-t_c\le0.5,\\
t-t_c-0.5,&0.5<t-t_c\le1.5,\\
1.1-0.1\exp[-(t-t_c-1.5)/0.1],&t-t_c>1.5.
\end{cases}\qquad (6)
$$

The symbol on the left is the actual throttle $u$, not a velocity. During controlled burn segments, actual throttle is piecewise linear. Its implied effective command is $u_{\rm cmd}=u+0.1\dot u$, constrained between 0.3 and 1.1 at both ends of each segment. Startup and shutdown may pass below 0.3; that bound applies to steady powered operation. Shutdown includes the corresponding rate-limited decrease and exponential tail. No extra shutdown-command delay has been established, so it is not silently assumed in the contact discussion.

# 5. Restricted low-consumption trajectory search

## 5.1 Objective, strategy, and constraints

We minimize initial carried propellant,

$$ \min m_{p,0}=m_0-m_d, \qquad (7) $$

over a specified schedule family: initial coast; three-engine entry burn; an off command; a two-engine restart command five seconds later; and a final two-engine burn. The five seconds separate commands and are not a full zero-thrust interval. Engine response accounts for the 0.5 s restart delay and subsequent buildup. The landing pair ignites twice, while the third engine ignites once, below the assumed three-ignition limit per engine.

Within each fixed initial ignition-time case, decision variables include $m_0$, entry shutdown time, final time, actual throttle nodes, and thrust-angle nodes. The searched cases use initial ignition times 0, 20, 40, 50, and 60 s. The 60 s run did not return a feasible solution from its tested initial guess. A separate continuously variable ignition-time search reached its iteration limit. Neither outcome proves physical infeasibility.

The optimized trajectories obey sampled/substep path targets $q\le47$ kPa and $n_\Sigma\le3.9$, leaving margins to the nominal verification thresholds 50 kPa and 4. The force budget is

$$ n_\Sigma=\frac{\sum_i|T_i|+|F_{\rm aero}|}{mg_0},\qquad n_{\rm proper}=\frac{|\sum_i\mathbf T_i+\mathbf F_{\rm aero}|}{mg_0}\le n_\Sigma. \qquad (8) $$

Thus dynamic pressure and force budget are coupled through the same instantaneous drag; they are not independent load certificates. Other search bounds are $m_0\in[131,400]$ t, $t_f\in[110,450]$ s, $h\in[32.5,70000]$ m, and $\beta\in[-90^\circ,90^\circ]$. Local thrust-angle rate is capped at 4.9 degrees/s, then the inertial direction rate is checked against 5 degrees/s in replay.

The endpoint is a center-of-gravity reference event, not actual foot contact:

$$ h_f=32.5\,\mathrm m,\quad v_{t,f}=0,\quad v_{r,f}=-1\,\mathrm{m\,s^{-1}},\quad\beta_f=0,\quad m_{{\rm use},f}\ge m_{\rm res}+10\,\mathrm{kg}. \qquad (9) $$

The optimized vertical endpoint thrust is at most 0.95 times local weight. Replay checks that vertical thrust at the independently detected reference event does not exceed weight. This does not prove support stability after contact.

## 5.2 Numerical method and independent acceptance

We use direct multiple shooting with CasADi [7] and the local interior-point solver IPOPT [8]. Each powered phase is divided into 80, 160, and then 320 control intervals, using four RK4 substeps per interval. Coast steps are no longer than 0.5 s; startup uses 64 steps of 0.025 s; the shutdown/restart transition uses 132 steps of 0.05 s with actual midpoint response values.

Optimization success alone is not acceptance. Some bounds are imposed only at control nodes or RK substeps; the initial coast/startup do not carry every path constraint in the optimizer. We therefore replay the complete schedule with independent SI Cartesian equations, DOP853, explicit control breakpoints, and a continuous reference-altitude event [9]. Maximum-step halving, 0.05 s sampling, and local peak refinement screen the nominal path. A separately written SI polar model and RK45 provide further checks. This is strong numerical evidence, not an analytic continuous-time safety proof or a global optimum certificate.

# 6. Nominal trajectory and propellant result

## 6.1 Schedule comparison

@@COMPARISON@@

The fixed 40 s initial coast provides the lowest accepted load among the tested cases. The 20, 40, and 50 s preliminary comparisons use 80 intervals per powered phase; the final 40 s candidate is refined to 320 intervals. The immediately ignited reference is also evaluated at 320 intervals. The refined 40 s candidate carries 1.56 t less than the immediate-ignition reference, approximately 1.04%. These comparisons are within the chosen model and schedule family. Failed fixed-load schedules or failed solver runs are not universal lower bounds on the required fuel.

@@PHASES@@

The second burn begins while substantial horizontal and vertical velocities remain. It is not a purely vertical final braking pulse. The nominal ship is selected at the computed surface arc range; no geographical coordinates can be inferred without a launch location and heading.

![Nominal controlled trajectory from independent SI replay. Shading marks the initial coast and shutdown/restart transition. Altitude and velocity refer to the CG; the endpoint is not a simulated foot-contact event.](../results/figures/trajectory.png){width=95%}

![Actual throttle and required thrust angle. The landing pair shares a throttle trace; the third engine is separate. Passing below the dotted steady-throttle level during startup or shutdown is permitted by the response model. The angle is a required thrust direction; body attitude is not simulated.](../results/figures/controls.png){width=92%}

## 6.2 Mass balance and characteristic thrust increment

@@RESULTS@@

The initial total mass is 279.30 t. The 149.30 t propellant load contains approximately 115.37 t oxygen and 33.93 t methane if the assumed oxidizer-to-fuel mass ratio is 3.4. At the reference endpoint, approximately 1.458 t of propellant remains: 0.746 t unusable residue and 0.711 t usable reserve. The actual consumed total, about 147.84 t, must not be confused with the initial load or methane alone.

The mass-flow equation supplies a useful closure:

$$ \Delta v_T\equiv\int_0^{t_f}\frac{T}{m}\,dt=I_{sp}g_0\ln\frac{m_0}{m_f}\approx2.36\,\mathrm{km\,s^{-1}}. \qquad (10) $$

This scalar thrust increment includes the effort required along the powered trajectory; it is not simply the passive impact speed. Finite burn duration, gravity, changing mass, and direction changes matter. A rocket-equation estimate that inserts a chosen terminal speed while fixing the acceleration at near-dry mass does not close this coupled problem. The relatively large load is consistent with a low-thrust, long-duration braking history constrained to avoid high dynamic pressure. It is not an established universal minimum.

# 7. Numerical verification and perturbation response

## 7.1 Verification evidence

@@CHECKS@@

The 160-to-320 interval propellant change is 0.0189%, and independent reference-speed differences are much smaller than the modeled physical uncertainties. Re-solving the 320-interval problem from the archived 160-interval initial guess reproduces the final mass, times, and state/control nodes. This tests the same local solution path, not multiple-basin or global optimality.

Input validation matters as well as integration accuracy. An earlier replay could accept raw thrust-angle values shifted by $2\pi$, because the forces are periodic and the raw angle bounds were not explicitly rechecked. The delivered nominal angles are within bounds. A stricter validator now rejects angle-range violations, nonfinite throttle values, wrong array shapes, and invalid timing before replay. This fixes an acceptance-interface gap without changing the nominal trajectory.

## 7.2 Deterministic tests of the unchanged open-loop plan

Each case below keeps the initial propellant mass and the full control schedule fixed and changes one parameter. The nominal ship location is fixed. Integration ends at reference contact, usable-propellant exhaustion, or the original planned final time; the control is not extended into an undefined landing maneuver. The reserve threshold remains its fixed nominal definition. The $I_{sp}$ test changes mass flow without inventing a simultaneous thrust-performance map.

@@SENSITIVITY@@

All nine tests fail the original reference plan, even before full attitude and contact safety are assessed. A 1 m/s decrease in initial tangential speed, only about 0.06% of the nominal speed, produces an 11.5 m/s reference descent speed. A 1% lower specific impulse exhausts usable propellant at a CG height near 300 m. The nominal reserve is only about 10 kg above its stated 701 kg threshold; satisfying that bookkeeping requirement does not establish robustness.

Failure to contact by the planned time does not mean that later controlled landing is impossible. Likewise, these results do not show that a redesigned feedback controller would fail. They demonstrate sensitivity of this fixed open-loop schedule. The nine cases are not random samples and provide neither a failure probability nor a propellant confidence interval. Selected drag, specific-impulse, and initial-speed cases were repeated with RK45; event categories agree and endpoint height/velocity differences are below 0.01 in the corresponding SI units.

# 8. Attitude feasibility and the M1 extension

## 8.1 Separating thrust angle, body angle, and deflection

Let $\theta$ be the body angle from local vertical, $\beta$ the required net-thrust angle, and $\delta$ the net thrust-to-body deflection. Then

$$ \beta=\theta+\delta,\qquad\psi=\theta+\phi,\qquad\omega=\dot\psi,\qquad\dot\theta=\omega-\frac{v_t}{R+h}. \qquad (11) $$

The high-pressure inflow screen requires the body axis to lie within 5 degrees of the direction opposite relative velocity when descending at $q\ge10$ kPa. The late descent screen requires body tilt within 5 degrees once the lowest deployed-foot clearance is at most 200 m. The assumed first-contact limits are 2 degrees body tilt and 0.5 degrees/s relative body angular rate. None is automatically enforced by a thrust-direction trace.

At $t\approx175.42$ s, $h\approx5.31$ km, and $q\approx47.0$ kPa, the required thrust direction is $\beta\approx-14.34^\circ$, while the opposite-velocity direction is $\chi\approx-44.12^\circ$. The body must lie in $[-49.12^\circ,-39.12^\circ]$ under the inflow requirement. Consequently,

$$ |\delta|\ge24.78^\circ\quad\text{at this instant}. \qquad (12) $$

This is a necessary lower bound for keeping the existing trajectory. If the available net deflection is at most 20 degrees, no body angle at that instant can satisfy both requirements. Near the ground, the analogous required relative deflection is about 15.28 degrees under the local-deck approximation. The actual actuator capability is unknown; the numbers are requirements, not specifications.

![Required thrust and attitude-angle compatibility. The shaded interval is an allowed body-angle interval, not an allowed thrust interval. The lower panel is a sampled necessary relative-deflection bound; passing a 25-degree line does not demonstrate dynamic attitude feasibility.](../results/figures/attitude.png){width=92%}

A sweep of assumed net deflection limits 3, 5, 10, 15, and 20 degrees finds incompatible instants. At 25 and 30 degrees, the samples have no instantaneous angle contradiction. Even then, torque, rate, initial orientation, and a continuous dynamically achievable body trajectory remain unverified.

## 8.2 Force and torque must be realized together

A first rigid-body extension adds $\psi$, $\omega$, mass properties, and actuator states. For a clearly identified locally frozen inertia approximation,

$$ \dot\psi=\omega,\qquad I\dot\omega=M_T+M_a+M_{\rm ctrl}. \qquad (13) $$

With clockwise angles as defined above, an engine mounted at $-\ell_i\mathbf e_b+a_i\mathbf e_\perp$ produces

$$ M_{T,i}=-\ell_iT_i\sin\delta_i-a_iT_i\cos\delta_i. \qquad (14) $$

This sign follows directly from the chosen coordinates. Aerodynamic moment may be represented by $qA_{\rm ref}LC_m$ or by a force applied at a pressure center. Both $C_m$ and pressure-center location are unknown. A changing center of mass and inertia require a consistent control-volume angular-momentum balance, including relevant mass-flow transport terms; an arbitrary time-varying inertia cannot be inserted while ignoring the corresponding terms.

For scale only, a uniform dry solid-cylinder surrogate has $I\approx4.62\times10^7\,\mathrm{kg\,m^2}$. Rest-to-rest rotation through $\Delta\psi$ with bounded net torque obeys $t\ge2\sqrt{I\Delta\psi/M_{\max}}$ in the ideal bang-bang limit. A 90-degree turn in 5 s would require about 11.6 MN m with this surrogate and no assisting torque. This is not a measured inertia or proof about the actual five-second command interval, which contains thrust response tails.

A guidance loop should request a force, an attitude loop a moment, and a constrained allocator should satisfy both using available engines, gimbals, differential thrust, and any reaction-control devices. In coast or low pressure, neither thrust-vector control at zero thrust nor weak aerodynamic surfaces supply guaranteed authority. Separate reaction-control propellant must also be included if used. A complete coupled solution must use consistent drag, lift, and moment coefficients for the same body attitude and flow, rather than adding a moment model to incompatible old aerodynamics. These data are not presently available.

# 9. Foot contact, deck coverage, and post-contact safety

## 9.1 First contact and the non-supporting envelope

Use a local deck frame with CG coordinates $(x_c,H_c)$ and body tilt $\theta_d$ relative to the deck normal. For the assumed deployed geometry, $\ell=32.5$ m and foot half-span $b=5$ m. Let $\mathbf e_b=(\sin\theta_d,\cos\theta_d)$ and $\mathbf e_\perp=(\cos\theta_d,-\sin\theta_d)$. The feet are

$$ \mathbf r_{f,\pm}=\mathbf r_{CG}-\ell\mathbf e_b\pm b\mathbf e_\perp,\qquad h_{f,\min}=H_c-\ell\cos\theta_d-b|\sin\theta_d|. \qquad (15) $$

Actual first contact is the earliest continuous zero of a deployed-foot clearance, provided the non-supporting envelope has not touched first. The assumed main cylinder uses axial coordinate $s\in[2,65]$ m and radius 3.5 m, sampled every 1 m on both sides and connected as a closed polygon. Its clearance at foot contact, for $|\theta_d|<90^\circ$, is $2\cos\theta_d+(b-3.5)|\sin\theta_d|>0$ under this particular geometry. That does not establish clearance for actual nozzles, legs, or protrusions, or for an inverted body. The two-meter basal clearance and deployed span are H choices.

At 2 degrees tilt, the lowest foot touches when $H_c\approx32.655$ m, and the feet differ in height by $2b|\sin2^\circ|\approx0.349$ m. Thus they generally do not begin carrying load simultaneously. Deployment timing, locking, the intermediate envelope, and aerodynamic deployment loads must be checked. The deployed-foot formula is not a model of the stowed configuration.

![Assumed deployed geometry at first foot contact with 2-degree body tilt. The right panel resolves the approximately 0.349 m height difference. This is a kinematic construction, not a real landing-leg design or a contact simulation.](../results/figures/contact_geometry.png){width=85%}

A spherical flight model also needs consistent local deck coordinates. Far from the ship, ocean clearance is measured from the spherical sea surface; an infinite extension of the ship's tangent plane is not the global ocean. Segment interiors must be tested for minimum distance to the sphere, not just vertices. Near the ship, finite deck and hull geometry replace the infinite-plane approximation.

## 9.2 Contact velocities and target coverage

For a stationary nominal deck, the foot velocities are

$$
\begin{aligned}
v_{f,x,\pm}&=v_{CG,x}-\ell\omega\cos\theta_d\mp b\omega\sin\theta_d,\\
v_{f,z,\pm}&=v_{CG,z}+\ell\omega\sin\theta_d\mp b\omega\cos\theta_d.
\end{aligned}\qquad (16)
$$

Moving or rotating decks require subtracting the local deck-point velocity. The assumed vertical interval $[-2,0]$ m/s and horizontal magnitude limit 0.5 m/s apply to feet actually in contact, not to the CG. For an upright conditional example with CG velocity $(0,-1)$ m/s, a body rate of 4.9 degrees/s gives foot horizontal speed about 2.78 m/s. A body rate of 0.5 degrees/s gives about 0.284 m/s. The M0 thrust rate cannot be substituted for body rate and then ignored in contact velocity.

Let $B$ denote the foot-plane center. The target screen is $|x_B-x_{\rm ship}|\le5$ m; the distinct support-coverage screen requires every foot within 18 m of the deck center, leaving 2 m margin to a nominal 20 m half-width. These are separate requirements, labeled C13a and C13b. A freely selected nominal ship position does not establish tracking accuracy, three-dimensional support, or performance under ship motion.

## 9.3 Absorption, shutdown, and stability

At reference mass 131.46 t, vertical kinetic energy is approximately 65.7 kJ at 1 m/s and 263 kJ at 2 m/s. For zero engine support and an ideal total stopping stroke $s$, the minimum average total normal force is $m[g+w^2/(2s)]$. Peak and single-leg forces may be much higher, especially during non-simultaneous contact. Leg stiffness, damping, stroke, friction, and ratings are unknown, so no gear design or post-contact acceptance follows from this energy scale.

Contact dynamics must impose unilateral normal force, friction/stick-slip behavior, finite compression stroke, and finite deck coverage. An equivalent spring-damper model may be a first approximation, but its deformation must represent a defined compliance, not permitted rigid-body penetration of the deck. At least two seconds after first contact should be checked for sliding, overturning, load, and compression under the assumed safety window.

A simple upright, rigid, non-sliding pivot model gives a static tipping angle $\arctan(b/\ell)\approx8.75^\circ$ and a zero-thrust energy barrier near 493 kJ. This screen requires its own assumptions and the initial rotational energy; it does not prove stability for a powered, compliant, moving-deck landing. The 2-degree contact limit alone is not a dynamic anti-tip certificate.

The candidate still has upward thrust near 0.950 times weight at its CG reference endpoint. Static normal support would then be only about 0.050 times weight if other forces were absent. Full $mg$ must not be assumed when estimating available friction or restoring support. Under the same immediate-shutdown response model, the two-engine tail has approximately 386 kN s impulse and consumes about 123 kg, excluding any additional off-command delay or plume/ground effects. Thrust and body angular rate cannot simply be reset to zero at contact.

## 9.4 Structural and thermal limits

Dynamic pressure and force budget are useful screens, not structural or thermal ratings. Bending moment, local stress, buckling, flexible response, and propellant slosh depend on load distribution and mass properties. A stagnation-point scaling of the form $\dot q_h\propto\sqrt{\rho/R_n}\,V^3$ illustrates the separate sensitivity of heating to speed [11], but no heating coefficient, effective engine-end radius, heat shield, wall temperature, or allowable heat load has been established. Retropropulsion changes the flow and cannot be treated as a passive-body thermal correction without evidence [10]. Neither structural integrity nor reuse readiness is certified by $q<50$ kPa.

# 10. Strengths, limitations, and a defensible completion path

The approach has three useful features: variable mass is coupled to the trajectory rather than attached after a guessed velocity budget; nominal solutions are checked by independent coordinate and integration implementations; and attitude/contact constraints are used to falsify overly strong safety claims. The most important unresolved data are the initial flight-path angle, actual thrust and specific-impulse maps, consistent drag/lift/moment data, center-of-mass and inertia histories, actuator torque and deflection limits, landing-leg and deck properties, and structural/thermal capacities.

The current study does not solve a robust closed-loop landing problem. It searches one schedule family through a limited initial-guess chain. It does not show that a different engine count, coast duration, aerodynamic design, or feedback strategy could not use less propellant. It also does not show that adding more propellant alone fixes the safety deficiencies: extra mass changes thrust-to-weight ratio and the trajectory.

A logical completion sequence is to fix a supportable actuator and mass-property scenario, jointly optimize translation and rotation with force/moment allocation, introduce guidance feedback or receding-horizon replanning, validate fixed-ship disturbances, detect true foot and envelope contact, and simulate at least two seconds of support dynamics with structural and thermal checks. Propellant should then be compared among candidates that pass the same full set of requirements. Until then, 149 t is neither a verified feasible upper bound nor a rigorous lower bound for the complete safe-landing problem.

# 11. Conclusions

The problem's given quantities do not uniquely determine the required real propellant because several decisive propulsion, trajectory, and safety specifications are absent. For an explicitly horizontal, wind-free, constant-drag, virtual-engine scenario, a reproducible M0 trajectory carries approximately 149 t of liquid oxygen and methane, consumes approximately 148 t, and reaches a CG reference endpoint after about 218 s at nominal downrange 206 km. Peak dynamic pressure is about 47.0 kPa, and the reference descent speed is approximately 1.00 m/s.

This result answers a conditional numerical question, not the full safety question. Keeping the same trajectory requires net thrust-to-body deflection of at least 24.8 degrees at one high-pressure instant; actual capability is unknown. Foot rotational velocities and non-simultaneous support matter, and nine deterministic perturbations fail the unchanged open-loop plan. The defensible outcome is a nominal propellant benchmark together with explicit conditions for a safe model, rather than an unsupported claim of safe recovery or minimum fuel.

# References {.unnumbered}

[1] University Physics Competition. *The 2026 University Physics Competition Problems*, Problem A. https://university-physics-competition.com/2026-competition. Accessed 7 November 2026.

[2] NOAA, NASA, and U.S. Air Force. *U.S. Standard Atmosphere, 1976*. NOAA-S/T-76-1562; NASA-TM-X-74335, 1976. https://ntrs.nasa.gov/citations/19770009539.

[3] NASA NSSDC. *Earth Fact Sheet*. Volumetric mean radius and standard gravitational acceleration. https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html. Accessed 7 November 2026.

[4] G. Petit and B. Luzum, eds. *IERS Conventions (2010)*. IERS Technical Note 36, numerical standards, 2010. https://iers-conventions.obspm.fr/conventions/content/tn36.pdf.

[5] NASA Glenn Research Center. *Specific Impulse*. https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/specific-impulse/. Accessed 7 November 2026.

[6] NASA Glenn Research Center. *Drag Coefficient*. https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-coefficient/. Accessed 7 November 2026.

[7] J. A. E. Andersson, J. Gillis, G. Horn, J. B. Rawlings, and M. Diehl. CasADi: A software framework for nonlinear optimization and optimal control. *Mathematical Programming Computation*, 11:1--36, 2019. https://doi.org/10.1007/s12532-018-0139-4.

[8] A. Wächter and L. T. Biegler. On the implementation of a primal-dual interior point filter line search algorithm for large-scale nonlinear programming. *Mathematical Programming*, 106:25--57, 2006. https://doi.org/10.1007/s10107-004-0559-y.

[9] SciPy developers. *solve_ivp: Initial-value problem solvers*. SciPy documentation. https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html. Accessed 7 November 2026; computations used SciPy 1.17.0.

[10] A. Marwege, D. Kirchheck, J. Klevanski, and A. Gülhan. Hypersonic retro propulsion for reusable launch vehicles tested in the H2K wind tunnel. *CEAS Space Journal*, 14:473--499, 2022. https://doi.org/10.1007/s12567-022-00457-w; author-institution record: https://elib.dlr.de/188153/.

[11] K. Sutton and R. A. Graves, Jr. *A General Stagnation-Point Convective Heating Equation for Arbitrary Gas Mixtures*. NASA-TR-R-376, 1971. https://ntrs.nasa.gov/citations/19720003329.

[12] University Physics Competition. *Contest Rules*, solution papers and generative AI provisions. https://university-physics-competition.com/contest-rules. Accessed 7 November 2026.

# Appendix A. Computational traceability and reproduction {.unnumbered}

The supplementary calculation record distinguishes physical assumptions, numerical verification, and missing safety models. Raw high-precision values are retained for regression checks, while the main scientific conclusions use rounded values appropriate to the H parameter uncertainty. No reported numerical tolerance is interpreted as an uncertainty bound for a real rocket.

The main artifacts are the final 320-interval control arrays; independent Cartesian and polar trajectories; engine-response and analytic-limit tests; the 160/320 grid comparison; optimizer reproduction records; nine perturbation cases; and angle/geometry diagnostics. The source files are provided with this draft's supplementary package under anonymous relative calculation paths. The manuscript contains no team-member or institution identifiers. Repository account names and machine paths are not needed for interpretation.

The optimizer uses CasADi 3.7.2 with IPOPT, NumPy 2.3.5, and ordinary Python execution. Verification uses SciPy 1.17.0. The nominal acceptance threshold for reference velocity is $-2\le v_r\le0$ m/s and $|v_t|\le0.5$ m/s; mass, pressure, force budget, steady commands, throttle slew, and inertial thrust-direction rate are also checked. A continuous CG-height event is deliberately labeled as a proxy. Full M1 and support dynamics have no pass flag.

The reproduction sequence is:

1. Check the lower-atmosphere implementation against layer-boundary and reference-density values; reject invalid controls before integration.
2. Solve the chosen initial-ignition case with 80, 160, and 320 intervals per powered phase, warm-starting only within this declared strategy family.
3. Replay actual engine response and mass flow at every control breakpoint, independently detect the CG reference event, and refine pressure/load peaks.
4. Cross-check coordinates, vacuum invariants, the ideal rocket equation, quadratic-drag decay, and an independently integrated actuator response.
5. Keep controls, initial carried mass, and nominal ship fixed for each one-parameter perturbation; terminate on first applicable event rather than burning unusable residue.
6. Evaluate attitude interval intersections and deployed-foot/envelope geometry without labeling these necessary checks as a solved rigid-body landing.

A generic frozen-inertia force/moment model is discussed in Section 8 but was not used to generate a fictitious successful attitude history. Unknown center-of-mass, inertia, aerodynamic moment, gimbal/reaction-control, deployment, leg, deck, and heat-shield inputs remain unknown. The complete physical problem requires those inputs before additional digits of a propellant requirement would be meaningful.

# Appendix B. Safety criteria and evidence boundaries {.unnumbered}

The criteria below are grouped into 18 classes with 19 records because target error and support coverage are the distinct subrecords C13a and C13b. Numerical limits are H study targets unless otherwise stated. A nominal M0 pass applies only to that implemented subset and scenario.

@@SAFETY@@

# Report on the Use of AI {.unnumbered}

**Draft disclosure status: incomplete; this manuscript is not submission-ready.** The contest rules require disclosure of the system, exact queries, and complete outputs when generative AI is used [12]. ChatGPT, through a Codex workspace assistant, was used in the associated modeling, code preparation, numerical checking, manuscript drafting, and formatting workflow. An exact underlying model release identifier has not been verified and is not invented here.

The exact user query for this manuscript-drafting step was:

> 写出最终论文初版

For readability only, its English translation is: “Write the first draft of the final paper.” The translation is not a substitute for the original query. Earlier relevant interactions include model construction, low-consumption search, verification, and attitude/safety analysis; they also require their exact queries and full AI outputs in the final disclosure.

The present manuscript is AI-assisted draft text, and the calculation/source files document much of the associated generated material. However, those artifacts are not a verbatim export of all previous interactions. Complete earlier queries and outputs were not available as a verified transcript when this draft was assembled. They must be appended verbatim in this final section from the actual session records before any submission. Selected examples, a bibliography, repository links, and this summary do not replace that requirement. The numerical checks reported in the paper were executed, but the manuscript and all AI-produced content still require the team's own review. No complete AI-disclosure record or final submission compliance is claimed by this draft.
