# RP-U004 — Retrospective degree-stratified audit of the first result

**Research record date:** 3 November 2026  
**Lead:** Felipe Gianini Romero  
**Classification:** post-result descriptive analysis, **not** a preregistered hypothesis or new independent experiment  
**Original experiment:** [RP-U004-P01](RP-U004-P01.md)  
**Immutable source:** [first-run JSON](RP-U004-P01-first-run/audit.json) and [archive manifest](RP-U004-P01-first-run/archive-index.json), run [#41721533933](https://github.com/DevHabito/relational-persistence/actions/runs/41721533933)

## Why I checked the individual cases

The first U004 result supported the registered aggregate H1 comparison: LOOKAHEAD2_F2 obtained 3,386 successful F2 case-ticks while GREEDY_F2 obtained 3,286, over 17,100 post-failure scenario-ticks per strategy. That difference is exact within the selected finite toy family.

A single sum can hide where the 100 extra successes actually came from. I therefore read the **already published** original case records and grouped them by two properties that are observable in the frozen archive: the failed component's original degree and whether the original graph possessed F2 before damage. This classification was chosen **after** the result; it must not be recast as another prospective success.

The separate [recount script](../../experiments/rp_u004_posthoc_diagnostics.py) uses standard-library Python, reads the archived JSON and verifies its bytes against the archived SHA-256. It does not import the original repair algorithm or modify the report. The [regression tests](../../tests/test_rp_u004_posthoc_strata.py) check every degree total, every gain-frequency bucket, the initial-F2 controls, the original policy-order identities and the offline-bound comparisons. They also reject one deliberate alteration of an individual archived score. These are archival checks, not new forecasts.

## How often did the difference appear?

| Extra F2-successful ticks for LOOKAHEAD2_F2 in a **single scenario** | Original scenarios |
|---|---:|
| 0 — tie | 2,784 |
| +1 | 39 |
| +2 | 20 |
| +3 | 7 |
| Negative — lookahead loss | 0 |
| **All scenarios** | **2,850** |

The 39 × 1 + 20 × 2 + 7 × 3 = **100** additional F2-successful scenario-ticks agree with the registered original aggregate. H1 remains supported under its original decision rule. The table does not supply a probability of benefit in future real networks.

The corresponding registered F1 comparison had 2,844 scenario ties and six scenarios with one extra F1-successful tick each. The F1-first and F2-first policy labels selected the same repair orders in all 2,850 original scenarios, an important objective-redundancy limitation already disclosed in the first report.

## Differences grouped by original degree of the failed vertex

The following bins use the original **pre-failure** degree of the vertex being removed. They do not use the dynamic degree of its replacement.

| Original degree | Scenarios | F2 winning scenarios | Additional F2-successful ticks |
|---|---:|---:|---:|
| 1 | 920 | 0 | 0 |
| 2 | 800 | 0 | 0 |
| 3 | 520 | 25 | 25 |
| 4 | 350 | 18 | 30 |
| 5 | 200 | 23 | 45 |
| 6 | 60 | 0 | 0 |
| **Total** | **2,850** | **66** | **100** |

All observed F2 improvements occurred after removal of a vertex with **three, four or five** original neighbors. That is a finite observation about the frozen selection rule. It is not a causal estimate, a new universal degree threshold, or proof that degree-six failures can never benefit from lookahead in another graph family.

An immediate reason to be careful: a one- or two-neighbor restoration has fewer possible repair orderings. For two remaining edges, the complete two-step future is independent of their order, so the immediate choice can determine the tie break. This offers a **candidate mathematical explanation** for the zero improvements at small degrees. I have not yet submitted or proved a separate general Lean theorem about every possible graph-repair scheduler satisfying these assumptions.

At degree six, none of the sampled original graphs possessed F2 before loss. That zero-win bin is therefore not an independent demonstration that large repair neighborhoods remove any lookahead benefit. The full degree distribution and label-specific graph-selection rules can confound naive comparisons.

## Original F2 function: an essential baseline

| F2 before failure | Scenarios | Lookahead wins | Ties | Losses | Extra F2-successful ticks |
|---|---:|---:|---:|---:|---:|
| Absent | 2,140 | 0 | 2,140 | 0 | 0 |
| Present | 710 | 66 | 644 | 0 | 100 |
| **Total** | **2,850** | **66** | **2,784** | **0** | **100** |

Only **142 of the 570 source graphs** had F2 before any damage. Each contributes five distinct internal-node-failure scenarios, giving the 710 F2-capable original-graph scenarios above. The remaining **428 graphs** could not exhibit a restored F2 function if restoring edges only recreates a subset of the original graph; that is an explicit limitation of this model.

I would therefore not quote the 66 winning cases out of 2,850 as an unconstrained effect size. Much of that denominator consists of F2-absent structural controls. Nor would I quote 66 out of 710 as a general physical probability: the cases are related by graph, degree and label, not independent random trials.

## Additional integrity checks

The post-result recount identified 2,850 unique original graph/loss pairs and 570 distinct selected graphs. All 2,850 archived comparisons had identical present-node and restored-edge trajectories between strategies. All greedy objective variants selected identical orders, and both lookahead objective variants did as well.

For all archived scenarios, the lookahead strategy's integrated F1 and F2 counts equaled the report's separate offline full-permutation maxima. **This does not establish global lookahead optimality**, because the source topology class, repair actions, information access and Boolean function are artificially restricted. An offline optimum for F1 and an offline optimum for F2 are two separate task-specific reference calculations.

The instrumented policy lookups reported in the original study were **28,450** per GREEDY variant and **53,410** per LOOKAHEAD2 variant, plus a common shared oracle precomputation. Equal model-edge budgets are not equal execution-time or computation budgets.

## What I know and what remains open

**Supported within this exact selected synthetic family:** H1's 100 additional F2-successful case-ticks; 66 winning scenarios; no observed F2 losses; concentration in the original-degree 3–5 bins; and perfect agreement between archived case-level sums and registered totals.

**Not supported by this analysis:** a preregistered degree-specific prediction, statistical generalization to an unselected population, ecological/clinical/aerospace reliability, a new network optimization theorem, a measured computation-time advantage, or a physical persistence law.

This analysis introduces no new graph or repair model and changes no original dataset, protocol, score, criterion or first-run hash. If I test a possible explanation in new graphs, I will preregister a different family and its failure conditions **before** scoring those graphs, and I will use established network-repair literature as a comparator rather than present greedy lookahead as an invention.

The next formal work is to verify the already-noted equivalence of nested Boolean F1/F2 rankings. That is a mathematical explanation sought **after** the first U004 result, separate from this post-result subgroup recount and from empirical validation.
