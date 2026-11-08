# RP-U004 — Independent retrospective audit, 8 November 2026

**Research lead:** Felipe Gianini Romero  
**Audit classification:** implementation-level reproduction after the original outcomes were known  
**Baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8` (3 November 2026)  
**First study:** RP-U004-P01, preregistered at `186d6fc5d8cc6451fca63abb5f6ef4f2029a3d7b`; original run [#41721533933](https://github.com/DevHabito/relational-persistence/actions/runs/41721533933); first archive at `36996adb456c3d628de1634cb2a57edadc315ebd`  
**New audit code:** `experiments/rp_u004_recompute_20261108.py`  
**New checks:** `tests/test_rp_u004_recompute_20261108.py` and `tests/test_rp_u004_20261108_relabel_stress.py`

## What I asked

Can I independently reconstruct the source selection, graph functions, policy decisions, resource counters, and offline bounds reported by the original finite RP-U004 study, without importing its scoring implementation or reading the old outcomes as inputs?

This is a question about *computational reproducibility*. The first RP-U004 outcome, including the favorable lookahead difference, had already been published when this audit started. Reproducing it now does not create new blinded evidence, a second natural-system sample, a Lean proof of the whole model, or a discovery of a physical law.

## Evidence and chronology

I inspected the GitHub repository tree and the original U004 preregistration, results, first-run archive manifest, Python scoring/replay code, post-result report, Lean Boolean-order proof, and Python/Lean workflow definitions.

Direct container access to GitHub by `git ls-remote` failed because the execution container could not resolve `github.com`. I did not bypass that failure by claiming a local repository checkout. I read the versioned sources and original hashes through the connected GitHub repository tool, and ran a self-contained alternative implementation locally with Python 3.13.5.

The local prototype, which does not import the original program or read its result JSON, matched the exact population and scores below. A separately committed, cleaned version was then executed as part of the repository's Python regression jobs, with the full original result archive available in CI. See [PR #71](https://github.com/DevHabito/relational-persistence/pull/71).

- Commit `fe6859c875eb8e27b026d4caf6490431d5b8676b`: [Python CI #42498807515](https://github.com/DevHabito/relational-persistence/actions/runs/42498807515) **passed 776 tests under Python 3.11 and 776 under Python 3.12**. The run included the new recomputation tests, source/manifest SHA checks, full original archive SHA check, deliberately corrupted F1 oracle, and 68,400-relabelling stress test. Both job logs were inspected.
- The 8 November local source-and-score reproduction ran directly, outside GitHub CI, on Python 3.13.5. This is an additional execution environment, not an independent physical dataset. Its measured wall-clock duration is not treated as a controlled algorithm-performance benchmark.
- The original U004 first-run archive was **not modified**, replaced or rerun as a fresh preregistered experiment.

## Graph family — independently reconstructed

Instead of copying the original combination-over-all-edges source enumerator, the independent implementation constructs each possible graph from exactly two source neighbors, exactly two destination neighbors, and four internal edges. A disjoint-set (union-find) implementation rejects disconnected candidates. The surviving labeled graphs are sorted, grouped by their full seven-entry degree vector, and the first and last member of every nonsingleton degree group are selected.

| Quantity | Independent result |
|---|---:|
| Accepted connected labeled graphs with seven nodes/eight edges | 18,140 |
| Distinct degree-vector strata | 305 |
| Singleton strata excluded | 20 |
| Paired strata | 285 |
| Selected source graphs | 570 |
| Single-internal-node failure scenarios | 2,850 |
| Selected source graphs with F2 before damage | 142 |
| Original-case subset-function entries | 25,040 |

The independent sorted accepted-family SHA-256 is

```text
bcc1b5ae2d05482277486e401fbc5918d51a75ffcc5df09ceea5b98c6f57427c
```

The independent first/last selected-family SHA-256 is

```text
46eda52afa56de2830b869112a7569cc9bb72780bac82a6943872c91cef83e94
```

Both reproduce the values frozen in `docs/results/RP-U004-P01-first-run/archive-index.json`. These digests bind the full ordered finite populations rather than merely their sizes.

The full original archive is also checked directly in the new CI regression against its separate byte-level SHA-256:

```text
172603ff933cc269372afa55d2a67163586604a561839a237c2be3d17ce67f09
```

That archival test only confirms byte integrity of the old JSON. The reconstruction of the source graph family is a separate algorithmic check.

## Functions and repair decisions — independently reconstructed

The audit rebuilds post-removal/replacement graph states from their declared topology, not the original cached Boolean truth tables. It checks F1 with graph reachability and path enumeration, and F2 with pairs of internally vertex-disjoint paths and removal of each nonterminal vertex. Any F1/F2 oracle disagreement stops execution.

It then independently executes ascending-label, degree-based, F1/F2 greedy, and F1/F2 two-step lookahead rules with the original declared deterministic label tie breakers. Complete permutations of each eligible repair-neighbor list provide the finite offline maxima. The implementation records modeled truth-table queries and candidate comparisons separately. These are *not* actual CPU-time equalization.

Each policy has 17,100 synthetic post-failure case-ticks. The reproduced policy totals are:

| Policy | F1 case-ticks | F2 case-ticks | Table lookups | Candidate comparisons |
|---|---:|---:|---:|---:|
| ASC | 15,695 | 2,877 | 14,250 | 0 |
| DEGREE | 15,825 | 3,106 | 14,250 | 0 |
| GREEDY_F1 | 16,046 | 3,286 | 28,450 | 14,200 |
| GREEDY_F2 | 16,046 | 3,286 | 28,450 | 14,200 |
| LOOKAHEAD2_F1 | 16,052 | 3,386 | 53,410 | 14,200 |
| LOOKAHEAD2_F2 | 16,052 | 3,386 | 53,410 | 14,200 |

Independent sums of the per-case offline maxima are **16,052 F1** and **3,386 F2** case-ticks. Thus the two-step rule reaches both of these finite maxima on this *particular selected dataset*. There is no conclusion of universal algorithm optimality.

F2 scenario-level contrasts against GREEDY_F2: **2,784 ties**, **39 gains of one tick**, **20 gains of two ticks**, **7 gains of three ticks**, and **zero losses**. That produces **66 winning scenarios** and **100 additional F2 case-ticks**. The F1 comparison gives 2,844 ties and six gains of one tick, with zero losses.

The positive F2 scenarios occur after failure of original-degree-three, -four, or -five nodes: **25, 18, and 23 wins**, respectively. This is a retrospective subgroup description, not a new registered threshold. None of the 2,140 scenarios arising from an original graph without F2 contributes a positive F2 difference.

The F1-first and F2-first policies again choose identical orders within their greedy and lookahead classes. As previously explained by `RelationalPersistence/BooleanRepairRank.lean`, nested Boolean functions do not provide two independent priority-order controls. There are six labels but four distinct decision rules here.

## Adversarial and stress tests

A test deliberately replaces the path enumeration oracle with an empty iterator on a graph that has two terminal paths. The independent F1 reachability check must contradict that defective oracle, and the computation must fail visibly. The new test passed in the recorded Python CI. The existing first-run suite also contains immutable-archive and corruption-rejection tests; those are not relabeled as new blind experiments.

For a broader deterministically exhaustive **label-permutation stress check**, I evaluated F1/F2 for every selected original graph under every permutation of its five internal vertex labels. This is 570 × 120 = **68,400** structural comparisons. All agreed locally. The same check is committed as a new regression, and passed in CI at the commit recorded above.

This invariance concerns *the graph functions* F1/F2, not the selected actions of the repair policies. Repair decisions can legitimately differ under labels because their explicit tie rules depend on vertex numbers. Equating the two invariances would be a methodological error.

## What passed, what did not, and what remains open

**Passed in the local independent implementation and the Python CI:** finite family counts, both family hashes, F1/F2 function oracle agreement, policy totals, the complete F2 gain/tie/loss distribution, the small F1 difference, modeled operation counters, and offline maxima. Byte-level archive identity passed in CI. The corruption-rejection test and structural relabeling stress check passed.

**Known access limitation:** I could not clone the repository into the local execution container due to DNS resolution failure. The connected GitHub source and the hosted regression jobs provided alternative, explicitly documented access paths. No local build of the complete repository or local Lean check is claimed.

**Not tested by this new independent module:** byte-for-byte reproduction of every field of every archived case object, which is handled by the repository's previously committed independent case-level replay and its tests; operational CPU time under a fixed budget; real repair time or material costs; randomized samples from new network populations; prospective external holdouts; physical, ecological, medical or chemical mechanisms.

**Scientific result:** `RERUN_AGREED` for the finite retrospective computation. The original H1 is still **SUPPORTED WITHIN FINITE SYNTHETIC SCOPE** and nothing broader. There is no new empirical or mathematical priority claim.

## Next gate

Before any second experiment:

1. Keep all source data and original first-run verdicts frozen.
2. Review the known code/claim boundary, especially the nested-objective redundancy and the higher lookahead function-evaluation cost.
3. Conduct a separate source and literature audit for any proposed practical recovery task. Use real, fully sourced operational data only after measuring historical feature availability and defining a task-specific independent outcome.
4. Preregister a **new** and narrowly discriminating question, with a stronger baseline, equivalent operational resource budgets, and a clear rejection decision. Do not recycle this already seen family as an unseen validation set.

No new experiment was run or preregistered in this audit, and no universal relational-persistence or physical law was established.
