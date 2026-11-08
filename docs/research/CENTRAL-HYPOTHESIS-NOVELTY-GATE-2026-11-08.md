# Central scientific question and originality gate — 8 November 2026

## What the research is trying to explain

**Plain-language target:** Before an external disturbance happens, can the internal relations of an organized system, combined with what is genuinely known about the disturbance process and available repairs, predict whether a *declared function* will persist or recover for a *declared duration*?

A scientifically meaningful claim requires a **specified system**, a measurable function, disturbances with externally observable units, a time horizon, an admissible action/repair set, a source-specific outcome and comparisons with existing methods. None of these should be replaced by philosophical metaphor after an experiment runs.

The project's motivating intuition is valuable as a question, but **there is currently no theorem or empirical evidence in the project that physical time arises when relations fail to cope with external informational noise**. Artificial observation ticks do not derive time.

## What is not new

1. **Worst-case edge or vertex robustness** is classical graph connectivity/mincut and Menger/Ford–Fulkerson theory. This repo did not invent a minimum cut.
2. **Stochastic graph reliability** (two-terminal, all-terminal, dependent faults) already models survival under random failures. Brown, Kolokolnikov & Kooij (2024) explicitly analyze edge-removal processes and limitations of degree-only approximations, DOI [10.1002/net.22215](https://doi.org/10.1002/net.22215).
3. **Attack versus failure regime** was distinguished by Albert, Jeong & Barabási (2000), DOI [10.1038/35019019](https://doi.org/10.1038/35019019).
4. **Temporal dependence of stochastic disturbances** is a standard probability/dynamical-systems issue. Our **RP-F004-A01** previously showed a comparable scalar Markov-noise contrast; RP-S001's frozen-versus-resampled edge failure is not a discovery of new probability.
5. **Structure beyond degree sequences** already matters for graph spectra, reliability and consensus; the repo's **RP-F003-A01** previously provided a bounded six-node example.
6. **Greedy versus lookahead repair and computational effort** are existing optimization topics. RP-U004's 100 extra synthetic F2 scenario-ticks at extra lookups are a model-specific prior result, not a new general control theorem.

## What RP-S001 now establishes and does not

A preregistered finite exhaustive enumeration of **540** six-node source graphs identified a first lexicographically selected pair with identical complete labeled degree vector **(2,5,3,2,2,2)** and terminal minimum **edge** cut **2**, yet different random survival under two original-edge removals: **25/28** versus **26/28**. **31 of 79** degree classes vary internally in the exact numerator, with independent BFS, DFS, edge-cut and union–find checks.

On the same graph, same instantaneous two-edge-failure marginal distribution gives distinct **three-observation sustained** success under frozen versus independently renewed failures: on graph A **25/28** versus **15,625/21,952**. The original result is archived in [RP-S001-P01-first-run](../results/RP-S001-P01-first-run/archive-index.json); the fully scoped record is [RP-S001-P01](../results/RP-S001-P01.md).

**Scope:** These are exact finite facts refuting a **coarse structural sufficient-statistic** candidate and a **memory-insensitive** three-step outcome model. They are fully compatible with existing mathematical network reliability and are **not a new theorem of universal persistence or an empirical finding about physical time**. A later exact Lean 4 certificate for the selected pair is a retrospective finite certificate only, not an original general graph theorem.

## One central *open, falsifiable* scientific hypothesis worth testing next

**RP-CENTRAL-H1 (unproven, conditional):** For a pre-specified physical or operational function monitored across a fixed horizon, a predictor based only on static *coarse* network summaries may be insufficient; adding **genuinely pre-disturbance available complete relational information**, **measured temporal dependence of the external forcing**, and **available intervention/repair constraints** may yield calibrated and reproducible **out-of-sample predictive improvement** over strong domain-specific and conventional network-reliability baselines.

This is an investigation target, **not a novel theory established by these words**. Standard dynamic reliability, temporal-network analysis and control theory may already imply or implement its mechanism. A future originality claim requires a substantially broader source search and external scholarly review.

**It is logically possible that H1 will fail:** richer topology may be irrelevant when dominant drivers are unobserved; disturbances may have negligible temporal memory; static and temporal baselines may already be optimal; valid causal-time labels may not exist; or exact classical reliability methods may outperform every candidate model. Such failures must remain published.

## Critical distinction: finding a condition versus inventing a law

A real general theorem requires precisely defined mathematical objects, a nontrivial statement relative to existing literature, proof that does not assume the desired conclusion, genuine counterexample search and independent review.

A real empirical law requires identified physical observables, independent outcomes, properly separated training/selection/test data, fidelity to actual decision times, external validity and credible uncertainty. One cannot get these simply by substituting the words *Amazon forest*, *power distribution grid*, *health system* or *cosmic time* into a graph formula.

## Stop/go gates for any new experiment

**G0 — literature boundary.** Reconcile conditional reliability, autocorrelated failures, temporal networks and intervention/control models. Establish a precise bibliography and mark what is already solved. If the mechanism has been previously established, frame the work as replication or application, never a novel law.

**G1 — independent data eligibility.** Obtain sources with actual *pre-disturbance* relational structure, timestamped exogenous perturbations, observable failure and recovery functions, and true intervention/action histories with decision-relevant costs. The authenticated ANEEL source snapshot audits D06–D10 have **not** demonstrated historical operator repair-action logs or energized topology; **do not** use them as a causal restoration-policy benchmark yet.

**G2 — unbiased experimental design.** Specify endpoints, horizon, missingness, resource budgets, train/validation/test partition and minimum meaningful improvement **before** measuring future outcomes. Include static mincut/degree, full-topology classical stochastic reliability, established dynamic models, no-repair, simple reactive policy, lookahead and runtime/repair-cost baselines. Include disturbance-history permutation and feature-leakage controls.

**G3 — independent confirmation.** Replicate successful effects with at least one truly independent source or held-out system, then a different domain if a cross-domain generality claim is intended. Preserve subgroup failures, negative controls, error bars and all rejected hypotheses.

**G4 — mathematical distinctiveness.** Only after a robust result survives G0–G3, formulate the narrowest possible new statement; seek a formal proof or a constructive counterexample and external technical critique. Do not promote a finite case into an unlimited universal law.

If **any** gate fails, the corresponding claim must remain **OPEN / NOT ESTABLISHED**, not be softened by changing definitions.

## Near-term research recommendation

**Do not immediately build another ad hoc scalar “persistence index.”** The next best use of effort is a rigorous literature and real-source-eligibility review to determine whether RP-CENTRAL-H1 has a testable, **previously uncovered** conditional claim. If no such gap emerges, focus on useful reproducible reliability applications and publish the strong negative results honestly.

Our current original contribution is **the documented, reproducible research trail and several task-specific finite/observational results**, subject to literature comparison—not a confirmed new principle of nature.
