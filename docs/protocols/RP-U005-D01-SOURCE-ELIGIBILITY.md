# RP-U005-D01 — External source eligibility for observed relational repair

**Dated:** 8 November 2026  
**Baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8` (3 November 2026)  
**Status:** retrospective, **source-and-schema-only** eligibility review, not a preregistration of unseen outcomes. Source documentation, RP-E012-D03 observations and prospective cost question were already known at the time this note was written. No new external observations, downloads, forecasts or optimization runs are authorized in this gate.

## Narrow question

Can the *previously accessed* Google Borg 2019 cell-a material, in its verified RP-E012-D03 state and under the publisher's available schema, directly support an **observational** comparison of greedy versus two-step edge repair in the same F1/F2 terminal-path sense as the synthetic RP-U004? If not, identify which missing measurements prevent the comparison, and distinguish data incompleteness from a mismatch of target concepts.

A graph-theoretic repair policy requires **more** than an observed machine-removal time. Its intervention and outcome must refer to declared, physical or operational links, and the observation must exclude future state.

## Eligibility gates — all necessary for a direct U004 operational replication

1. **Original identity and provenance.** Original source bytes or authoritative backed snapshots must be authenticated, versioned and legally accessible; event meaning must be documented.
2. **Complete relevant pre-decision history.** An objective time window, joins across necessary tables, entity identities, missing-event treatment, censored states and tie rules must be certified. A file prefix or machine-only shard is not enough.
3. **Historical information availability.** Inputs used by the strategy must be demonstrably available *when* the real decision was made; event timestamp alone does not prove a scheduler's receipt time.
4. **Operational relation and graph topology.** Source must identify the actual relevant links, source/target terminals and the state of edge availability. A shared switch identifier, machine capacity or job dependency must not silently be substituted for physical network connectivity.
5. **Observed intervention and comparator.** Real repair choices, eligible alternatives, repair order, intervention time and feasible counterfactual comparator must be distinguished from naturally occurring machine changes. Historical data may not identify all counterfactual policy outcomes, even with perfect logging.
6. **Independent measured objective.** The source must support F1/F2 (or explicitly and prospectively redefine a different function), verified from observations independent of the policy scorer, with uncertainty and censoring preserved.
7. **Real resource/cost measurements.** Decision runtime/resource demands, information-acquisition cost, repair material/crew/time budget and resulting delay must be measured in declared physical units. The retrospective hypothetical `λ` in RP-U004-C01 is **not** a measured cost.

For a claim of *causal superiority*, observational coverage of actions and outcomes is still not enough by itself. It additionally requires a valid assignment or identification strategy; that is a later study design, not automatic eligibility.

## Nonconflation rules

- `AUTHENTICATED_MACHINE_EVENTS` is a valid positive **partial** evidence status; it is NOT `COMPLETE_SCHEDULER_STATE`.
- `UNKNOWN`/not yet verified is **not** the same as proven absent. `ABSENT_FROM_PUBLISHED_EVENT_SCHEMA` refers to the currently inspected **publicly described fields**, not hidden private Google logs.
- `EVENT_TIME` is not `ONLINE_RECEIPT_TIME`.
- `MACHINE_ADD` is not an observed policy-selected graph-edge repair; `MACHINE_REMOVE` is not an observed repair decision.
- A record of repair *duration* alone does not identify decision overhead or the causal effect of an alternative action.
- A synthetic benchmark can support method/solver regression but **cannot** provide independent empirical evidence.
- The discovery of a new dataset **after** seeing prior results is exploratory; any later preregistration must freeze a **new** source and holdout before consulting target values.

## Predeclared desk-audit actions

Read only original archived RP-E012-D03 `audit.json`, the associated `archive-index.json`, the existing report and the publisher's public documentation. Pin external schema versions by source Git commit and blob SHA. Extract no new Google raw events and perform no BigQuery or paid operations. Compare the source with other **named, clearly scoped** published datasets solely for suitability, without calling any uninspected data rows verified.

Implement a small independent read-only Python gate that (i) verifies the original archived report's SHA-256 against the original manifest; (ii) checks the internal consistency of the historical machine-event counts and two complete recorded snapshot partitions; (iii) requires truthful original negative metadata for cross-table/online-state coverage; (iv) issues a blocked verdict for the stated U004 empirical task; and (v) rejects corrupted bytes or contradictory metadata in negative-control tests. No test shall fabricate absence of unpublished source fields.

**Permitted conclusion:** `RP_U005_DIRECT_POLICY_SOURCE_BLOCKED` supported by the specific audited omissions and the published schema, without asserting that every historical dataset or every future protocol is impossible.

**Stop:** any archive-hash disagreement or internal metadata inconsistency invalidates this desk reconstruction; do not substitute the documented counts as if independently verified.

**Not an outcome test:** this gate cannot test greedy/lookahead efficiency, physical repair speed, or `C=B/(Iτ)`. A passed software test is evidence of source-gate implementation integrity, not a new observed recovery.

## Independently checkable references read on 8 November 2026

- Google [2019 trace repository](https://github.com/google/cluster-data/tree/48b12446464b0422abcc18e0ec5b0b13e2f3a90c) at commit `48b12446464b0422abcc18e0ec5b0b13e2f3a90c`; proto file Git blob SHA `83101ef12604a6c9ce4a44288791a17869c2caf1` and `ClusterData2019.md` blob SHA `22a38cab107ce8dedf18c86c1c2b25607980cf26`. Its v3 `MachineEvent` describes ADD, REMOVE, UPDATE, time, machine ID, obfuscated switch, capacity, platform and missingness: no explicit selected network-edge repair action, actual intervention duration or decision-resource measurement field in that message.
- Nan Deng, [Google cluster trace v3 JSON/GCS change notice](https://groups.google.com/g/googleclusterdata-discuss/c/WuRDhbI8YzA), **10 August 2020**: five sharded gzip JSON table families. JSON output does not establish historical online release ordering.
- Original project [RP-E012-D03 report](../results/RP-E012-D03.md), first run `40425342721`, archive `docs/results/RP-E012-D03-first-run/`. The separately frozen D03 source is a single complete machine table, not complete instance/collection tables.
- Alibaba [2017 cluster trace schema](https://github.com/alibaba/clusterdata/blob/3858992ca41bf92082e6d6522ddf0bebd14e838b/cluster-trace-v2017/trace_201708.md) at published repository commit `3858992ca41bf92082e6d6522ddf0bebd14e838b`, file blob `9e5147641b0f4ab1b943b6bf0c0d2b2ff6e8863c`: server ADD, soft/hard errors and capacities, not independently checked U004 repair decisions.
- Stephen Platt, Andrew Coburn, Farnaz Mahdavian and Oliver Carpenter (published **9 January 2026**), [Disaster recovery – evidence from 100 natural disasters](https://doi.org/10.5061/dryad.d7wm37qc0), Dryad. Published macro-level societal/economic recovery measures; an external observational candidate for **another** question, not a measured edge-repair action dataset.
- Qiao Pan (published **12 October 2026**), [Data and Code for Post-Disaster Collaborative Road Restoration with Heterogeneous Repair Teams](https://doi.org/10.17632/89pktc22t7.1), Mendeley Data. The publisher explicitly classifies its 51 main instances and 54 sensitivity inputs as **synthetic**; not field observations.

The first four project/source checks may be audited mechanically; the schema/identification judgment is explicitly a source interpretation and remains reviewable rather than being treated as a computed theorem.
