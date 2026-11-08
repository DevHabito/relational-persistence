# RP-U004-C01 — Decision cost sensitivity: retrospective analysis

**Research lead:** Felipe Gianini Romero  
**Record:** 8 November 2026  
**Classification:** after-result algebraic sensitivity audit; neither a new preregistered experiment nor a fresh held-out prediction  
**Source model:** RP-U004-P01, first original run `41721533933`, frozen first-run archive at `36996adb`  
**Before-proof scope:** [RP-U004-C01-SCOPE.md](../formalization/RP-U004-C01-SCOPE.md), separately committed as `dd2a3c7efa33d889c85d0d49e0da8eba98c05018`

## The question

I wanted to know what the earlier U004 result permits me to say **after accounting for its extra measured-in-the-program work**. The original finite study recorded 100 additional F2-successful scenario-ticks for two-step lookahead. It also counted substantially more truth-table lookups. I cannot call the two strategies equally costly just because they saw the same precomputed information.

The first study was already finished, and I already knew its favorable aggregate result before defining this calculation. I am not treating the following threshold as a new prediction, a new experiment, or a discovery about physical recovery.

## Exact inputs and definitions

The original model was a selected, fixed synthetic family of 570 labeled seven-vertex graphs with 2,850 related failure scenarios, six post-failure ticks each. F1 meant one surviving terminal path, F2 meant two internally vertex-disjoint terminal paths. These scores are binary graph predicates; ticks are not calibrated seconds.

| Outcome or operation | One-step greedy | Two-step lookahead |
|---|---:|---:|
| F1-successful scenario-ticks | 16,046 | 16,052 |
| F2-successful scenario-ticks | 3,286 | 3,386 |
| Instrumented truth-table lookups | 28,450 | 53,410 |

The reported lookup count is the instrumented **policy-evaluation count**, not the whole cost of acquiring or constructing the common truth table and not actual runtime. Both policies used the same repaired-edge schedule and full graph knowledge, which does not establish information availability in a physical intervention.

Let `U_F(p)` be the already recorded successful case-tick total for function F and policy p. Let `L(p)` be the recorded lookup count. I define only for **retrospective accounting**:

```text
J_F(p; λ) = U_F(p) - λ · L(p)
```

Here `λ ≥ 0` is a *hypothetical price* with dimensions **synthetic successful scenario-ticks per instrumented lookup**. No λ has been estimated, and no change in policy decisions, time spent repairing, damaged graph or function outcome is allowed when changing λ in this toy calculation. A constant additive price is a mathematical assumption, not a description of the real world.

## F2: complete conditional sensitivity result

For the published F2 numbers:

```text
J_F2(lookahead; λ) - J_F2(greedy; λ)
  = (3386 - 3286) - λ(53410 - 28450)
  = 100 - 24960λ.
```

The exact break-even price is `100/24960 = 5/1248`. Over nonnegative rational λ, lookahead has the higher **defined accounting score** if and only if `λ < 5/1248`; the scores tie at `λ = 5/1248`; greedy has the higher score above that threshold. Approximately, the threshold is 0.004006410256410256 synthetic successful F2 case-ticks per extra lookup. I retain the exact fraction in the source and proof; the decimal is only a display aid.

At zero lookup price the extra F2 ticks still total 100; at a sufficiently large price, the extra 24,960 lookups outweigh them. This calculation cannot tell me which price nature, a scheduler or a maintenance crew would actually pay.

## F1: descriptive secondary result, not independent support

For F1, the corresponding difference is `6 - 24960λ`; its exact break-even price is `6/24960 = 1/4160`. The positive advantage is much smaller under this separate Boolean success count. Importantly, F1-first and F2-first priority labels were mathematically redundant in the original graph model: F2 implies F1. The Lean certificate for that preexisting ranking fact is in `RelationalPersistence/BooleanRepairRank.lean`. The F1 arithmetic is **not** an independent replication of H1.

## What the code proves or checks

The new `RelationalPersistence/RepairDecisionCost.lean` states exact inequalities and equality of rational functions of λ; it does not assume any real hardware or invoke a graph oracle. The new `experiments/rp_u004_cost_sensitivity.py` independently reads the **original archive** and rejects a whole-file SHA-256 disagreement before extracting recorded aggregate counts. Python tests use `fractions.Fraction` to check the exact thresholds and prices on both sides, plus a deliberately corrupted manifest and a no-denominator case.

A successful Lean build would certify only arithmetic after the numerical source constants are assumed. The Python archive checks connect those constants to the frozen JSON. Neither proves that physical costs are constant, that an observed service is preserved, that two-step lookahead has the best real-time policy, or that no better published optimizer exists.

## Earlier research that constrains claims

The following bibliography was checked again against publisher, archival or indexing records on 8 November 2026. It is targeted prior work, not an exhaustive priority search.

- **Fuyu Hu, Chi Ho Yeung, Saini Yang, Weiping Wang and An Zeng (14 April 2016)**, “Recovery of infrastructure networks after localised attacks”, *Scientific Reports* 6:24522, DOI [10.1038/srep24522](https://doi.org/10.1038/srep24522). It discusses greedy restoration, its incomplete view of future sequences and computational complexity. These considerations predate this project's lookahead comparisons.
- **Fenghua Wang, Hale Cetinay, Zhidong He, Le Liu, Piet Van Mieghem and Robert E. Kooij (17 October 2023)**, “Recovering Power Grids Using Strategies Based on Network Metrics and Greedy Algorithms”, *Entropy* 25(10):1455, DOI [10.3390/e25101455](https://doi.org/10.3390/e25101455). It includes greedy and two-step greedy recovery in DC power-flow simulations. The studied physical-model proxy and cost metrics are not interchangeable with Boolean F2 graph ticks.
- **Abigail J. Crocker and Stephen D. Boyles (23 April 2025 online; September 2025 issue)**, “Heuristic Selection in Disaster Recovery Sequencing”, *Journal of Infrastructure Systems* 31(3), DOI [10.1061/JITSE4.ISENG-2467](https://doi.org/10.1061/JITSE4.ISENG-2467). It compares recovery sequencing algorithms on larger transportation network instances, including beam-search and simulated annealing heuristics; these are established competitors rather than unclaimed inventions of this project.

I have not independently reproduced their experimental calculations, and none of those papers verifies the additive λ model above. The break-even result here is elementary rational algebra over a **known synthetic benchmark**, not a new mathematical method.

## Limitations and stop decisions

No real cost, resource budget or duration has been measured for these policies. The additive score could fail to represent even a software service: real decision time may vary by platform and input, and extra computation may delay restoration itself, changing the successful ticks rather than merely subtracting a fixed price. Information acquisition, CPU use, scheduler state, network repair and associated physical units also have different costs.

In particular, **equal repaired edges do not imply equal total work**. The 24,960 extra instrumented lookups, plus any unmeasured preparation cost, are material. The known graph selection and original U004 results cannot be presented as a fresh independent validation sample.

The next practical question must first ask whether a primary data source provides **historically available pre-decision information, a real outcome and actual measurable decision/repair costs**. If that source cannot be certified complete and causal-time eligible, a registered source-gate experiment must stop without generating predictive claims. If eligible, a new prospectively frozen outcome and stronger prior-art comparators are required before any effectiveness claim.

## Reproducibility and chronology

This document is a later interpretation of frozen first-run results, not an edit to the original. The proof scope was committed before the new Lean module, but the **original graph outcomes were already known**. New scripts, regressions and proof changes live only on branch `research/u004-cost-sensitivity-20261108` until reviewed. The original `audit.json`, preregistration, results and the original standalone proofs remain unchanged.

**Formal CI and Python regression status:** to be recorded against the final exact PR head after execution. Do not infer a pass merely from the existence of source code.
