# Claim ledger

| ID | Statement | Status | Evidence | Do not claim |
|---|---|---|---|---|
| RP-D001 | `C=B/(I*tau)` defines a positive scalar index when all inputs are positive | Definition | Algebra | Empirically validated stability law |
| RP-T001 | For a connected symmetric graph with contracting consensus modes, worst-case finite-time disagreement is governed by nonzero Laplacian eigenvalues | Classical conditional theorem | Spectral decomposition, Olfati-Saber et al. (2007) | Novel theory or universal physics |
| RP-T002 | Independent zero-mean isotropic noise yields stationary total disagreement as a sum over contracting modes | Classical conditional derivation | AR(1) variance formula | Dynamics measured in the field |
| RP-P001 | Equal scalar input proxies imply equal persistence outcomes for the specified six-node contrast | REJECTED in RP-001 declared dynamical class | Frozen pretest protocol + independently computed outcome | Refutation of all RZS/PMFF |
| RP-C001 | Same scalar proxies permit finite-variance and divergent-variance AR(1) systems | Constructive illustrative counterexample | Exact coefficient criterion | Cross-domain measurement proof |
| RP-E001 | Zachary karate club observed topology can be used for an exploratory linear consensus calculation | Observed topology + simulated dynamics | NetworkX dataset and original 1977 article | Empirically observed recovery |
| RP-B001 | PMFF relational primitives derive the selected consensus dynamics | Open | No proof currently supplied | Established mathematical bridge |
| RP-F010 | The proposed scalar index is positive under strictly positive rational inputs | Lean 4 verified, scoped | `scalarIndex_pos`; CI #40032271293 | Empirical validation or a physical law |
| RP-F011 | Saturating normalized index lies in [0,1] under nonnegative capacity and positive other inputs | Lean 4 verified, scoped | `normalizedIndex_bounds`; CI #40032271293 | Calibrated dynamical stability |
| RP-F012 | P6 and S6 with the same scalar inputs have different one-step coordinate responses for an explicit perturbation | Lean 4 verified finite witness | `equal_scalar_inputs_different_update`; CI #40032271293 | Formal proof of registered 20-step RP-001 metric |
| RP-F013 | Two chosen rational response gains yield different scalar values after 20 powers | Lean 4 verified exact arithmetic | `distinct_gains_twenty_steps`; CI #40032271293 | Statistical variance or physical law |
| RP-N001 | Any project result is a novel general stability theorem | Not asserted | Dedicated novelty review missing | Priority or a law of nature |

| RP-F014 | An explicit mean-zero path witness exceeds a 0.20 twenty-step norm ratio, while every rational mean-zero star state is bounded by 0.15 under the declared six-coordinate maps | Lean 4 verified, partial RP-F001 | `rp001_rational_twenty_step_certificate`; CI #40034508194 at `9390e56` | Formal certificate for all real states or empirically observed persistence |
| RP-F015 | The six-coordinate maps agree with the Fin 6 combinatorial graph update for every time step | Candidate formal bridge; CI verification pending | `GraphBridge.lean` (updated after failed induction rewrite) | A verified theorem until its exact source commit passes CI |
