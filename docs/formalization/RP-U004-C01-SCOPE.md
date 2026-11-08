# RP-U004-C01 — Retrospective decision-cost boundary: proof scope

**Date:** 8 November 2026  
**Baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Status:** *after-result algebraic audit*. This is not a prospectively registered experiment, a previously unknown prediction, a new physical law, or a claim that lookup counts measure time or energy.

## Question

The previously published finite RP-U004 benchmark records more F2-successful case-ticks for two-step lookahead than for greedy, but it also records more instrumented truth-table lookups. Under an explicitly assumed, **fixed additive accounting price** per lookup, at what price does that known advantage disappear?

The numbers and the positive outcome are **already known**. This exercise only derives a conditional sensitivity boundary; it must never be described as a new blinded confirmation.

## Frozen inputs: original RP-U004-P01 first-run aggregate

Source of truth: `docs/results/RP-U004-P01-first-run/audit.json`, integrity manifest `docs/results/RP-U004-P01-first-run/archive-index.json`; first run `41721533933`, original archive commit `36996adb`. Original model: selected seven-vertex synthetic graph population, 2,850 failure scenarios, six post-failure ticks each, uniform edge-repair schedule.

| Objective | Greedy successful case-ticks | Lookahead successful case-ticks |
|---|---:|---:|
| F2 (two internally vertex-disjoint terminal routes) | 3,286 | 3,386 |
| F1 (at least one terminal route) | 16,046 | 16,052 |

The recorded modeled lookup totals are 28,450 for greedy and 53,410 for lookahead. These totals include the existing run's policy evaluation conventions and should not be misrepresented as physically measured CPU time or as the separate cost of constructing the common truth table.

## Definitions and dimensions

For a chosen Boolean objective `F`, define the **aggregate accounting score** of policy `p` as:

`J_F(p; λ) = U_F(p) - λ L(p)`.

- `U_F(p)`: total synthetic F-successful **scenario-ticks** summed over the frozen 2,850 scenarios. This is not a probability or physical duration.
- `L(p)`: the already instrumented **lookup count** for that policy. Not equal to total algorithm work, physical repair cost, wall-clock decision time, or information-acquisition cost.
- `λ ≥ 0`: a *hypothetical conversion factor* in **synthetic successful scenario-ticks per lookup**. No value of λ has been measured or identified in this project.
- `J_F`: an analytical post-hoc accounting index, not a calibrated utility, empirical service metric, causal outcome, or a newly optimized policy.

This sensitivity model assumes the price is constant per lookup and that adding the price does **not change** the originally recorded repair order, available information, repair speed, graph, outcome, or horizon. If computation delays physical repair, the formula may be wrong and must not be patched after seeing outcomes.

## Pre-proof obligations (already-visible totals)

1. Derive the difference `J_F(lookahead; λ) - J_F(greedy; λ)` by substituting the frozen counts without rounding.
2. Derive **necessary and sufficient** rational inequalities for positive advantage, exact tie, and negative advantage for F2; repeat for F1 as a descriptive secondary check.
3. State the thresholds as exact rationals. A calculator or floating-point approximation is **not** the authority for the exact theorem.
4. Formalize the finite rational arithmetic in the repository-pinned Lean 4 toolchain, and include the new module in the root `RelationalPersistence.lean` imports. Do not add axioms, `sorry`, or `admit`.
5. Independently recover the four original aggregate counts and two lookup totals from the byte-verified first-run JSON inside a Python regression. Check rational thresholds with `fractions.Fraction`, including exact tie and cases on either side.
6. Preserve every source file and original first-run artifact. Record CI IDs, proof SHA, failures and corrections in a separate dated report.

## Outcomes

- **Verified conditional arithmetic:** exact rational threshold and CI-checked Lean proof, with archive-backed Python arithmetic. This is reproducibility of a **post-hoc accounting identity**.
- **Computation failure:** original bytes/hashes disagree, the recorded aggregates do not equal the cited counts, or Python and Lean disagree. Stop; do not reinterpret the result.
- **No physical inference:** without independently measuring the actual cost and time-critical consequences of a policy decision, neither policy is empirically superior on net utility.

## Prior art and novelty restraint

Established restoration heuristics already weigh network function, repair sequence and computational resource use. Specific sources to inspect for this stage:

- Fuyu Hu, Chi Ho Yeung, Saini Yang, Weiping Wang and An Zeng (14 April 2016), *Recovery of infrastructure networks after localised attacks*, *Scientific Reports* 6:24522, DOI [10.1038/srep24522](https://doi.org/10.1038/srep24522).
- Fenghua Wang, Hale Cetinay, Zhidong He, Le Liu, Piet Van Mieghem and Robert E. Kooij (17 October 2023), *Recovering Power Grids Using Strategies Based on Network Metrics and Greedy Algorithms*, *Entropy* 25(10):1455, DOI [10.3390/e25101455](https://doi.org/10.3390/e25101455).
- Abigail J. Crocker and Stephen D. Boyles (23 April 2025 online), *Heuristic Selection in Disaster Recovery Sequencing*, *Journal of Infrastructure Systems* 31(3), DOI [10.1061/JITSE4.ISENG-2467](https://doi.org/10.1061/JITSE4.ISENG-2467).

The cited source records were independently checked on 8 November 2026. They concern different task definitions and do not validate this aggregate synthetic tradeoff. A threshold obtained by rearranging two linear expressions is elementary arithmetic, **not** a new optimization theorem or new domain law.

## Next *distinct* experimental gate

Only after this retrospective accounting audit, define an **independent** operational dataset with verified causal-time availability of graph, decision inputs and downstream outcomes, measured decision resources and actual repair costs. Register an objective, competing stronger published baseline, expected positive and negative outcomes, and stop conditions **before** acquiring the held-out outcome data. Do not recycle the already-known U004 outcomes as a fresh holdout.
