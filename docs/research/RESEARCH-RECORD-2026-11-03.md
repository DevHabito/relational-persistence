# Research record — 3 November 2026

**Research lead:** Felipe Gianini Romero  
**Repository:** [DevHabito/relational-persistence](https://github.com/DevHabito/relational-persistence)  
**Record type:** Dated scientific status and decision log. This is not an experiment, a preregistration, or a replacement for the frozen first-run reports.

## Why I keep this record

I am investigating when a system can preserve or recover a specified function after its components or relationships are disturbed. I began with a proposed scalar index, but I no longer treat that formula as an established law. A definition can be consistent without predicting anything, and a computer-checked theorem about a small model says nothing by itself about ecology, medicine, the physical universe, or a spacecraft.

I use AI assistance for some coding, formalization and technical review. I still distinguish source code from an executed test, GitHub Actions from independent peer review, a mathematical witness from physical evidence, and a hypothesis from a discovery. I will keep the failed results beside the successful ones. I do not want to change an experimental threshold because the result is disappointing.

This record summarizes **existing, inspectable work**, with emphasis on the November 3 provenance repair and fixed-graph Lean certificate. For the complete historical study list and the original evidence, see [Results Index](../RESULTS_INDEX.md), [Claim Ledger](../CLAIM_LEDGER.md), and [Formalization Status](../formalization/STATUS.md).

## Research questions and limits

Two different questions remain on the table:

1. **Scalar sufficiency (Q1).** Could capacity, noise and delay alone predict a declared persistence observable in a defined class of systems?
2. **Derivation (Q2).** Could a persistence observable be derived from independently justified relational dynamics, rather than from chosen inputs or fitted definitions?

[Research Scope](../foundations/SCOPE.md) explicitly leaves Q2 open. The original candidate C = B/(I × τ) has no validated universal physical interpretation. If B is measured as updates/second, τ in seconds, and I dimensionless, this quotient has units of seconds to the power −2. Comparing values between domains without unit conventions and calibration is not justified. Graph topology, spectral response, noise correlations and feedback delay are possible missing state variables; they are not excuses to retrofit a failed formula.

## What the existing studies actually show

| Work | What the repository reports | What I cannot conclude |
|---|---|---|
| [RP-001](../results/RP-001.md) | An explicitly registered scalar-sufficiency contrast failed in its declared linear network class. | A refutation of every possible relational model or a measured physical law. |
| [RP-E002-A01](../results/RP-E002-A01.md) | The proposed topology-informed advantage failed on held-out METR-LA traffic speed forecasts at 15, 30 and 60 minutes. | That all network-informed forecasting fails. |
| [RP-F003-A01](../results/RP-F003-A01.md) | Exhaustive labeled six-vertex graph computation found a degree-matched twenty-step squared-energy contrast; a separate one-step witness has a Lean certificate. | That Lean proved the exhaustive maximum or that a degree sequence is a physical state description. |
| [RP-F004-A01](../results/RP-F004-A01.md) | Two explicitly specified correlated-noise processes have distinct exact rational second-moment outcomes at matched scalar proxies; the fixed-point portion was formalized. | A Lean proof of process-level stationarity or an empirical noise law. |
| [RP-F005-A01](../results/RP-F005-A01.md) | A fixed delayed-feedback recurrence has an exact period-six obstruction, separately checked in Lean. | A theorem about every delayed controller or real measured latency. |
| [RP-E004-P01](../results/RP-E004-P01.md), [P02](../results/RP-E004-P02.md), [RP-E005-P01](../results/RP-E005-P01.md) | Local and hosted software instrumentation/replay feasibility results, with declared controls and limits. | Independent evidence for a physical persistence equation. |
| [RP-E006-P01](../results/RP-E006-P01.md) | The registered simple index-based recovery predictor failed. | A valid model that can be rehabilitated by changing the test after inspection. |
| [RP-E007-P01](../results/RP-E007-P01.md) | A two-sample queue-trend predictor beat the frozen static software baseline in a limited hosted-service setting. | A new queue theorem or general transfer to industry. |
| [RP-E008-S01](../results/RP-E008-S01.md) | A discrete-event simulation passed its aggregate transfer gate, **but lost in a preregistered early-burst subgroup**. | Unqualified superiority across arrival patterns. |
| [RP-E009-P01](../results/RP-E009-P01.md) | A distinct executable software service passed the declared held-out comparison and replay gates. | Field-general performance or a fundamental physical discovery. |
| [RP-E010-P01](../results/RP-E010-P01.md) | On a real archival HPC workload, the frozen trend forecast failed against classical alternatives; 49,995 chronological held-out waits were evaluated. | A negative to be erased by retuning this already-seen holdout. |
| [RP-E011-P01](../results/RP-E011-P01.md) | A second external, queue-aware workload comparison failed its registered gain criterion; the held-out set was concentrated in two queues. | Independent performance across all 13 historical queues or a direct test of C. |
| [RP-F006-A01](../results/RP-F006-A01.md), [RP-F007-A01](../results/RP-F007-A01.md) | Conditional finite queue identifiability and enforced-runtime-bound examples. | Proof of scheduler policy, available online features, or hard time limits in a real deployment. |
| [RP-E012-D01](../results/RP-E012-D01.md), [D02](../results/RP-E012-D02.md), [D03](../results/RP-E012-D03.md) | Audits of original Google Borg event-source metadata, bounded prefixes and one complete machine-events shard. | Complete time-causal machine/instance/collection histories, a new forecast, or an enforceable runtime-cap measurement. |
| [RP-U001-A01](../results/RP-U001-A01.md) | Finite graph tests show that retention of one terminal route depends on the topology and on the chosen definition of function. | Real forest recovery, functional ecological redundancy, or a new graph theorem. |
| [RP-U002-A01](../results/RP-U002-A01.md) | In selected finite graphs, replacing a lost identity can restore the component count before source-to-target connectivity returns. Zero-benefit cases remain included. | Actual plant succession, clinical recovery, or arbitrary dynamic-network behavior. |
| [RP-U003-A01](../results/RP-U003-A01.md) | The exhaustive **synthetic** equal-edge-budget experiment supported its registered comparison against ASC and DEGREE, **not** a strict F1 advantage over GREEDY1. | That the competitors have equal knowledge, equal CPU cost, or a generalizable reliability improvement. |

This table is a navigational summary. The result reports and frozen JSON archives, not this narrative, remain authoritative for exact time series, loss functions, exclusions and first-run checksums.

## RP-U003: the complete finite comparison

The frozen source family contains **684 labeled, connected, six-vertex, seven-edge graphs** with terminals 0 and 5, terminal degree two, and no direct terminal edge. Each graph undergoes four separate single-internal-vertex failures and six post-failure states. There are **2,736 failure scenarios and 16,416 scenario-time evaluations per policy**.

F1 means at least one path between terminals 0 and 5. F2 means at least two internally vertex-disjoint terminal paths. The original report gives these exact integer sums:

| Policy | F1 successful case-ticks / 16,416 | F2 successful case-ticks / 16,416 |
|---|---:|---:|
| ASC | 15,736 | 6,980 |
| DEGREE | 15,748 | 7,092 |
| GREEDY1 | 15,888 | 7,852 |
| LOOKAHEAD2 | 15,888 | 7,968 |

LOOKAHEAD2 beats ASC and DEGREE in total F1 under matched **restored-edge counts**. It does **not** beat GREEDY1 in aggregated F1. Its 116-case-tick F2 advantage over GREEDY1 is task-dependent, not a proof of universal improvement. All four policies see the fixed synthetic repair blueprint; they do not have equal computation costs, and naive label ordering is itself a weak comparator.

The original [RP-U003 preregistration](../preregistration/RP-U003-A01.md), [result](../results/RP-U003-A01.md), and [first-run manifest](../results/RP-U003-A01-first-run/archive-index.json) preserve the historical chronology, including the first-run verdict. These graphs are not a random sample of real networks and the 16,416 rows are not independent experimental subjects.

### The already-known F1/F2 separation

On 3 November I returned to a **known**, not blind, finite example. Its source edges are:

```text
(0,1), (0,2), (1,3), (1,4), (1,5), (2,3), (3,5)
```

Vertex 3 is lost, and the new replacement is vertex 9. At t=3, GREEDY1 has rebuilt 9–1 and 9–2, while LOOKAHEAD2 has rebuilt 9–2 and 9–5. Each state has six vertices and two rebuilt edges; both still connect 0 to 5. GREEDY1 does not preserve F2 because removing vertex 1 breaks every remaining terminal route. LOOKAHEAD2 has two routes, 0–1–5 and 0–2–9–5, with no shared internal vertex.

I froze the **retrospective** proof requirements in [RP-U003-F01](../preregistration/RP-U003-F01.md) before adding its formal Lean code. The source module [RepairStrategySeparation.lean](../../RelationalPersistence/RepairStrategySeparation.lean) checks the fixed graph by bounded reachability and two separate F2 encodings (simple-path pairs and single-vertex cut checks). It does not prove an arbitrary-policy theorem or reproduce the complete U003 benchmark inside Lean.

[PR #63](https://github.com/DevHabito/relational-persistence/pull/63) passed its [Lean 4 CI workflow](https://github.com/DevHabito/relational-persistence/actions/runs/41712984616), including the step forbidding admitted proofs, and the [Python regression workflow](https://github.com/DevHabito/relational-persistence/actions/runs/41712984635) reported **732 passing tests each** on 3.11 and 3.12. It was merged into main at `83ba20c3a27a3d0bff5dd848b5f977fb2143dfa4`. This is evidence that the declared finite propositions type-checked at the reviewed head; it is not independent peer review, a proof that every Python program is correct, or a physical validation.

## Provenance correction: what went wrong and what I changed

The descriptive [RP-U003 report](../results/RP-U003-A01.md) had printed a **truncated 54-hex-character** graph-family SHA-256 where the original immutable manifest held the full **64-character** value. This was a report-transcription discrepancy. It did not establish that the archived original dataset was corrupt.

[PR #62](https://github.com/DevHabito/relational-persistence/pull/62) corrected only the reported digest and added a regression test comparing the narrative digest with the original manifest. Python 3.11 and 3.12 each reported **730 tests passed**; [Lean 4 CI](https://github.com/DevHabito/relational-persistence/actions/runs/41711065769) passed. The PR was squash-merged at `1a72415aa02bf174383521323544f1df8de322aa`. The original report archive, experiment implementation, preregistration and source-family manifest were not rewritten.

A separate AI-assisted Python recheck during this review reported matching aggregate U003 scores and a matching full graph-family digest. I do **not** present that interactive check as third-party replication or as a byte-for-byte audit of the full historical case-trace file. The committed source and original archive remain the reproducible evidence.

## What I have not established

- No experimentally calibrated persistence observable common to ecology, healthcare, computing, aerospace engineering and physics.
- No measured mapping from the PMFF/RZS primitives to a unique dynamical operator or to the earlier scalar C.
- No physical derivation of spacetime, gravitation, particles, or a new fundamental law.
- No independent field validation of the RP-U003 repair policy or real recovery costs.
- No evidence that F1/F2 path connectivity is sufficient to define actual service delivery, ecological recovery or spacecraft fault tolerance.
- No fresh external held-out advantage after the negative RP-E010 and RP-E011 results.
- No proof that a full collection/instance/machine scheduler state was observable before each Borg event-time origin.
- No formal Lean proof of RP-U003's entire 684-graph exhaustive enumeration or global policy optimality.
- No systematic, exhaustive novelty review across all relevant mathematics and applied domains.

## Next work: gates before another experiment

1. **Finish the documentary audit.** Keep this record linked from the README, Results Index, Claim Ledger and formalization status. Do not alter historical first-run evidence to match a narrative.
2. **Study repair decisions under fair information and computation constraints.** A new RP-U004 protocol, if opened, must be committed before implementation, source selection or any outcome. It should specify a genuinely separate graph family, degree-sequence controls, equal information access, compute-work measurements, classical path-aware and F2-aware policies, full case-level losses, and clear invalidation criteria. The U003 family must be treated as previously seen.
3. **Test whether a defined network function means anything operational.** External domain data require independent functional outcomes and historical feature availability. For physical/aerospace applications, define physical units, conservation or control constraints, sensor limitations and a measurable target before proposing an interpretation.
4. **Continue source audits only under fixed cost and completeness gates.** No new scheduler forecasting claims on selective prefixes or reused revealed holdouts.
5. **Invite independent scrutiny.** Reproduce from pinned commits, preserve failures and document any unresolved ambiguity. Formal verification, reproducible simulation and empirical measurement remain different standards of evidence.

## Literature and authorship

I keep my work distinct from established graph connectivity, ecological resilience, network restoration, distributed control, queueing theory and workload measurement. The dated, author-checked reading list for this audit is [Literature Notes — 3 November 2026](../literature/REVIEW-2026-11-03.md); the broader bibliography is [Prior Work](../literature/PRIOR_WORK.md). These sources establish earlier ideas and methods, not priority for my research program.

This is a working research record, not a publication asserting discovery. Any later correction should be dated and linked to its own commit rather than silently changing an earlier experimental decision.

## Same-day addendum — completed RP-U004 original study

After this dated snapshot, I completed [RP-U004-P01](../results/RP-U004-P01.md). Its protocol was frozen **alone** at `186d6fc5`, reviewed code merged at `d6f927ca`, and the original positive finite result ran as [#41721533933](https://github.com/DevHabito/relational-persistence/actions/runs/41721533933), archived at `36996adb`. The H1 F2 total was 3,386 for two-step versus 3,286 for one-step greedy: 66 scenario wins, 2,784 ties and zero losses. The F1 secondary gain was six case-ticks. Only 142 of the 570 selected original graphs possessed F2 to begin with; 2,140 loss scenarios therefore offered no F2 preservation to compare.

I kept a decisive limitation in the result rather than hiding it: the frozen labels `GREEDY_F1`/`GREEDY_F2` and `LOOKAHEAD2_F1`/`LOOKAHEAD2_F2` always chose identical repair orders because F2 logically implies F1. The two directional results are not independent optimization discoveries. All results are synthetic, and the original external forecasting failures remain unchanged. I recorded complete independent replay, raw hashes, prior literature and next proof obligations in the new study report; this addendum does not rewrite the original diary or its original observations.
