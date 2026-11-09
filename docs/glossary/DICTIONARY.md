# Research dictionary (version 0.1)

Terms must carry units, observation rules, assumptions and identifying limitations. Similar-sounding concepts are not automatically interchangeable.

| Term | Symbol | Type / units in RP-001 | Operational meaning | Important limitation |
|---|---|---|---|---|
| Relational persistence | no canonical symbol | not yet universal | A family's capacity to preserve or recover a declared organization after disturbances | Must specify function and time horizon before measuring |
| Coordination recovery residual | `r_T` | dimensionless | Maximum relative mean-zero disagreement after T no-noise consensus steps | Smaller is better; is not a survival probability |
| Update capacity proxy | `B` | update / step | Fixed one local update cycle per time step | Distinct from physical bytes/sec or operations/sec |
| Noise variance | `I = s²` | square of signal units | Per-node centered, independent disturbance variance | Not Shannon entropy, not uncertainty in general |
| Response latency | `tau` | steps | A single-step response in RP-001 | Fixed to 1; this experiment does not identify delay effects |
| Scalar index | `C` | dependent on proxy conventions | `B/(I*tau)` | Proposed only; not calibrated to outcomes |
| Dynamic coupling | `alpha` | reciprocal of Laplacian scale | Fixed strength of consensus relaxation | Not to be inferred after seeing results |
| Adjacency | `A` | dimensionless for unweighted graph | Presence of a relation | Direction, sign, and edge weights omitted |
| Laplacian | `L` | dimensionless under graph convention | `D - A` | Not a physical spatial Laplacian without a bridge |
| Connectivity | `lambda_2` | dimensionless | Second-smallest eigenvalue of L | Meaningful only for defined L and symmetry assumptions |
| Worst-case contraction | `rho` | dimensionless | Largest absolute non-consensus eigenvalue of W | Model-specific and noise-free outcome |
| Stationary disagreement | `E||Pi*x||²` | square of signal units | Expected total centered square deviation under stationary innovations | Not independent real-world observation here |
| Transition kernel | `K` | probability map | PMFF operation, distinct from declaring W | A particular kernel requires explicit extra assumptions |
| Relational mark | `q` | unspecified | PMFF transition label/score | No physical scale or unique interpretation yet |
| Base structure | `R` | abstract relation | PMFF primitive relation | Not automatically a measured social/network edge |
| Measure | `mu` | unspecified | PMFF weighting/measure structure | Depends on representation and reference measure |
| Occupation measure | `pi` | unspecified | PMFF state/weight measure | Not interchangeable with stationary distribution in every model |
| Observed graph | karate topology | edge set | Zachary's measured club relationships via NetworkX | Hypothetical consensus dynamics are not measured |

## Dimension audit

For the earlier informal use, if `B` is updates/second, `I` dimensionless and `tau` seconds, `B/(I*tau)` has units `seconds^-2`. It is **not dimensionless** merely because of its quotient form. RP-001 fixes a discrete-time numerical convention; cross-domain comparisons need explicit reference scales `(B0,I0,tau0)` or a declared dimensional calibration factor.

## RP-E003 prospective measurement vocabulary

These are **candidate measurement conventions**, not new measurements or
retroactive definitions of RP-001. The METR-LA benchmark did not
identify them.

| RP-E003 candidate term | Proposed instrument and units | What is insufficient |
|---|---|---|
| Calibrated capacity B | Saturated work completions per second in an independent pre-trial run | Sensor count, configured threads, fitted post-recovery throughput |
| External disturbance intensity I | Injector-log excess work units per second, in the same work unit as B | Outcome standard deviation, a fault category, nominal requested rate |
| Measured reaction latency tau | Seconds between an externally logged onset and an independently observed controller action | Sample cadence, nominal programmed delay, actual recovery duration |
| Independently observed recovery Y | Sustained health criterion with right-censoring, evaluated after separately logged intervention end | Computing Y from B, I, tau or post hoc fault labels |
| Clock domain | Common monotonic nanosecond clock, or separately certified synchronization | Subtracting uncorrected wall and monotonic timestamps |
| Stream separation | Calibration, injector, controller and health-monitor data flows kept auditable | Four columns derived from a single outcome series |

Under the RP-E003 illustrative convention, both B and I are rates
(work/second), so B/(I*tau) has dimension inverse second. This differs
from the RP-001 discrete-time variance-like convention: the two
definitions must not be conflated. A dimensionless alternative requires
an independently justified reference timescale and new preregistration.

The structural source gate is implemented at
src/relational_persistence/measurement_gate.py, with synthetic fixtures
in tests/test_measurement_gate.py. Its acceptance is not a physical
measurement validation. See
[RP-E003-S01 source screening](../protocols/RP-E003-S01-SOURCE-SCREENING.md).

## RP-F004 temporal-correlation vocabulary

All entries below describe **dimensionless mathematical model values**,
not new real-world instrumentation.

| Item | Symbol | Definition | Explicit limitation |
|---|---|---|---|
| Binary noise sign stay probability | `p` | `P(eta[t+1]=eta[t] | eta[t])` for a symmetric two-state Markov process | Only `1/2` and `3/4` are allowed by RP-F004 |
| Lag-one noise correlation | `r` | `2p-1` | Not inferable from one-time variance |
| Marginal noise variance | `s²` | `E[eta[t]²]=1/100` with equal ±1/10 marginal probabilities | Not injection rate or Shannon entropy |
| State-noise cross-covariance | `c_t` | `E[x_t eta_t]` | Must not be dropped with colored noise |
| Output second moment | `v_t` | `E[x_t²]`, equal to variance here because mean is zero | Not measured failure rate or survival probability |
| Limiting output variance | `Y(p)` | `lim E[x_t²]`, conditional on stability of the declared recurrence | Not the RP-001 graph residual or RP-E004 recovery time |

The same symbol `I` has different declared operational meanings
across RP-001, RP-E004 and RP-F004. No cross-domain physical inference
is allowed without a new measurement bridge.

## RP-F005 actual discrete feedback-delay vocabulary

| Term | Symbol | Operational mathematical meaning | Scientific limit |
|---|---|---|---|
| Feedback gain | `k` | Gain multiplying the delayed prior state in `x[t+1]=x[t]-k*x[t-d]` | Not a measured control law fitted to actual equipment |
| Feedback delay | `d` | Exact nonnegative integer state lag (0 or 1 in RP-F005) | Different between compared treatments; cannot pretend `tau` is matched |
| Delayed prehistory | `x[-1]` | Additional initial datum mandatory for the `d=1` recurrence | Does not exist as an independent datum for the `d=0` scalar model |
| Augmented delay-one state | `s[t]` | Two-vector `(x[t], x[t-1])` with a `2×2` companion matrix | Not a two-node physical network |
| Six-step squared residual | `Y6` | `x[6]^2/x[0]^2`, initial current state fixed to one | Not continuous-time recovery, probability of survival or variance |
| Uniform strict contraction | `q<1` | Candidate coefficient bounding six-step squared augmented-state energy for every state | Failure at gain one does not imply failure for every gain |

RP-F005 does **not** estimate `B,I,tau`, so the original
proposed quotient `C` must not be evaluated or advertised
as confirmed or falsified by this comparison.

## Versioning

New meanings require a new protocol and documented migration, not retroactive edits to test inputs. A different operationalization can be scientifically legitimate, but it is a different hypothesis until a linking theorem is proved.

## RP-H001 — causal evidence and dynamic reliability eligibility

These expressions are **definitions for an audit of prior publications and possible data sources**, not evidence that the research's central physical hypothesis has been confirmed.

| Term | Operational meaning | Important limitation |
|---|---|---|
| Complete predecision relational state | The full function-relevant network edges, active operating conditions and network constraints that were actually available to an operator before a fixed decision origin `t0` | A static original drawing, feeder label, original outage completion time or spatial proxy is not enough |
| Disturbance history available by `t0` | Timestamped input/forcing observations already released before the decision, with any missingness and dependence made explicit | Retrospective start/end timestamps may be known only after restoration; avoid lookahead leakage |
| Functional persistence endpoint | A preregistered measurable system function `F` remaining true over a chosen post-origin horizon, or an independently measured recovery outcome | Not automatically customer counts, graph reachability or a universal physical quantity |
| Feasible action set | Permitted switching, reconfiguration or actual physical repair interventions at a given decision state, subject to system constraints | Available edge labels and simulated connectivity do not certify electrical feasibility or historic choices |
| Historical action trace | Time-indexed real decisions/interventions with contemporaneous observed state and known release times | Scheduled dates and inferred source-event matches are not necessarily intervention logs |
| Correct causal-time eligibility | All prediction features were observable before the registered decision, not backfilled from subsequent results | Ordinary event-time fields are not proof of time of information release |
| Original joint source audit | Whole required source tables jointly authenticated across the exact selected decision-time window with explicit completeness/censoring checks | Authenticating one event table or a first shard is not joint completeness |
| Proxy-only source evidence | Metadata or measurements that approximate the desired entity/field but do not directly establish it, e.g., sensor distance for true active topology | A proxy cannot be silently upgraded to an actual intervention, state or independently observed function |
| Real-world causal policy-ready | A verified observed-data source jointly establishing the eight fields frozen by RP-H001, with enough information to identify/evaluate interventions | `NOT_ESTABLISHED` within eight reviewed sources is not universal absence |
| Synthetic simulator candidate | A documented generated network with outage/scenario capabilities that **may** support an independently audited artificial intervention experiment | Not real field validation, a verified power-flow run or evidence of actual historical actions |
| Prior-art / originality gate | Comparison of a narrowly specified proposed claim to existing proven results, algorithms and prior empirical studies | Calling a classical dynamic fault-tree, MDP or spatio-temporal graph forecast “relational” does not make it novel |
| Incremental held-out predictive value | Properly evaluated score reduction beyond the **best appropriate prespecified baseline**, with leakage controls and uncertainty reporting | Beating a constant or weak model does not demonstrate novelty or policy causality |

The source-by-source evidence, fixed audit protocol and original conservative decision appear in [RP-H001 G0G1](../research/RP-H001-G0G1-LITERATURE-SOURCE-REVIEW-2026-11-09.md). Strong prior art includes Rubin and Du (2024), DOI 10.1002/qre.3693; Zhao and Luo (2024), DOI 10.20517/ces.2024.54; and existing physics-aware switching work, DOI 10.1109/TSG.2023.3310893. No new mathematical theorem was introduced in RP-H001.
