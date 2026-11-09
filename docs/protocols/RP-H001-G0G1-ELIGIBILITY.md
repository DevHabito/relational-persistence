# RP-H001-G0G1 — Is there a defensible original, testable conditional persistence claim?

**Date:** 9 November 2026. **Parent:** unchanged `main` commit `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Purpose:** source-checked prior-art and observational-data **eligibility gate** for the proposed central scientific hypothesis, not a new restoration-policy experiment. Existing RP-S001, RP-F003, RP-F004, RP-U004, RP-E002, RP-E012 and RP-U005 D06–D10 results were already known. Several publisher descriptions were **read before this protocol was written**. Therefore this is an *explicitly retrospective* G0/G1 feasibility appraisal, **not** blind preregistration of novelty or an independent empirical effect.

## Central question

Does **complete historically available relational structure**, together with the **observed pre-decision temporal history of external forcing** and the **documented feasible intervention/repair constraints**, predict the survival or recovery of a specified function at a fixed future horizon **better than** existing reliability, prognostic and time-series baselines, *after accounting for computing and action costs*?

Do not make this claim at G0/G1. The question has three different scientific targets:

1. **Mathematical sufficiency/identifiability**: is the functional future distribution determined by the proposed information set under stated dynamics? Proven counterexamples to coarse summaries do not imply a new universal law.
2. **Out-of-sample prediction**: do observable pre-decision features improve calibrated held-out forecasts relative to appropriate established baselines, not weak strawmen?
3. **Intervention efficacy**: do policy choices improve counterfactual recovery relative to competing feasible policies under actual constraints? Observational labels without recorded actions and identification assumptions cannot answer this.

The user-facing intuition about “time arising when relations cannot tolerate external noise” is **not established** by any current source or model. An externally chosen observation clock is not emergent physical time.

## Fixed evidence classes (never silently promote)

Each candidate source has `kind` in `OBSERVED`, `SYNTHETIC`, `MIXED`. Evidence levels are `PRIMARY_SOURCE_DESCRIPTION_ONLY`, `PARTIAL_ORIGINAL_SOURCE_AUDIT`, and `COMPLETE_JOINT_ORIGINAL_AUDIT`. **Documentation describing a dataset does not establish independently downloaded, causally complete original histories.**

Each required property takes one of:
- `EVIDENCED`: supported by an exact source or existing verified project audit, within the evidence level and boundary disclosed;
- `PROXY_ONLY`: a plausible proxy has documentation but is **not** the target variable (e.g., a distance-based sensor graph instead of an actual energized feeder network);
- `NOT_ESTABLISHED`: no relevant direct evidence obtained in this review. This is **not** a declaration that the data never exist;
- `CONTRADICTED`: source evidence directly conflicts with the claimed field or availability.

**Real-world policy-ready** requires **OBSERVED**, **COMPLETE_JOINT_ORIGINAL_AUDIT**, and `EVIDENCED` for every one of the following **eight** properties, simultaneously:
1. `predecision_topology`: complete function-relevant graph/state, actually observable at decision origin;
2. `predecision_disturbance_history`: exogenous forcing, event history, dependence measured only before origin;
3. `registered_functional_outcome`: independently measured and time-indexed functional loss/recovery;
4. `feasible_action_set`: feasible historical actions, constraints and availability at origin;
5. `observed_action_sequence`: timestamped actions actually chosen, or randomized assignments with auditable records;
6. `decision_time_availability`: rigorous data-release/observation timing, not merely retrospective event timestamps;
7. `cost_measurements`: compatible physical/operational action cost and computational decision costs with clear units, or a preregistered physically credible instrumentation route;
8. `joint_population_coverage`: bounded, independently auditable completeness across **all required joined tables** at the decision times.

A useful independent simulator path is separate: `SYNTHETIC` candidates may be marked `SIMULATOR_CANDIDATE_NOT_YET_VALIDATED` only if publishers document a network topology and failure/outage scenario capability. This is **not** equivalent to an implemented restoration environment or historical causal evidence. The source has to be independently materialized, validated and checked for physical feasibility before any simulation performance statement.

An ordinary **forecast-only historical dataset** is not an intervention-ready dataset: full topology, pre-observation history and outcome can be sufficient to test some predictive questions while action effects remain unidentifiable. Do not infer policy effects from forecast errors.

## Candidate source set fixed for this feasibility audit

Evaluate the following source families without selecting favorable cases post hoc:
- `ANEEL-2026`: the two authenticated original 2026 published emergency-occurrence and interruption files already audited in the separate D06–D10 stacked branches; 2026 source coverage is a **partial-year snapshot**, not full nationally complete time. Text-key match, temporal overlap and equipment-code equality are not historical topology or selected intervention logs.
- `EAGLE-I`: US county-level 15-minute customer outage observations in the ORNL 2024 product and EAGLE-I 2014–2022 public dataset paper. County outages are not a component-level network graph.
- `DOE-EOD`: event-correlated outages constructed from EAGLE-I and DOE-417 records at county geography; correlated/outage labels do not establish a complete feeder graph or switch-operation treatment trace.
- `SMART-DS`: publisher-described realistic **synthetic** OpenDSS feeder topology with scenario and outage generation; candidate for simulation feasibility, never natural field validation.
- `METR-LA`: observed traffic sensor speed time series with an external distance-weighted sensor graph; already held-out tested negatively in this repository at RP-E002-A01. Sensor graph adjacency is a model proxy, not a source-documented physical repair-action set.
- `GOOGLE-BORG-2019`: observed scheduler trace; the repo's D03 audit authenticated one **complete machine_events object only**, but no original instance/collection event bodies, joint resource allocation state, or causal release-time guarantees.
- `NASA-CMAPSS`: NASA's engine **simulation** run-to-failure sensor dataset with operating conditions; not a measured relational-network topology or timestamped actual operator repair-action dataset.
- `IEEE-OPENDSS-TEST-FEEDERS`: publicly distributed test circuit models; potential synthetic topology and restoration-model feasibility, not real operator interventions or a field-data replication.

No more original third-party files, large ZIPs or personal records will be downloaded in this G0/G1 study. **Publisher metadata plus existing audited repo data only.** Thus original source contents of candidates except previously audited ANEEL, Borg machine-only, and METR-LA will remain **unverified**.

## Output rules and fail-closed decision

Freeze a human-readable English bibliography and machine-readable evidence table with **explicit evidence paths/URLs and observation dates**. An evaluator must read only those recorded statuses, count failures by criterion and print a source-by-source audit with **no overall real-world policy-ready source unless ALL eight requirements and joint source quality pass**. If none qualifies, output exactly `NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED`. `NO SOURCE IDENTIFIED` is *not* proof that no such dataset exists globally.

For synthetic candidates, output `SIMULATOR_CANDIDATE_NOT_YET_VALIDATED` if (and only if) publisher metadata supports scenario capability and network topology. Do not assert that an OpenDSS simulation, power-flow solver or multi-agent algorithm ran. For all candidates record `original_joint_data_processed_in_this_study=false`.

Tests must deliberately reject (a) `PROXY_ONLY` promoting to `EVIDENCED`, (b) action logs missing from an apparently rich source, (c) `SYNTHETIC` masquerading as natural observation, (d) source audit grade below complete joint audit, (e) single missing causal-time criterion, (f) malformed or duplicate source IDs, (g) absent evidence URLs, (h) unknown status, and (i) Python `-O` bypasses. Include one explicitly **invented synthetic fixture** satisfying the logic to verify the gate is not hardcoded to always reject. No actual source field may be invented to flip a `NOT_ESTABLISHED` finding.

## Originality gate G0

Before any prediction modeling, compare the central hypothesis against:
- existing dynamic fault-tree and dependent failure work;
- dynamic reliability/Markov decision processes for sequential testing/maintenance;
- power restoration switching/DER reinforcement learning with physically feasible OpenDSS examples (including 2023/2026 studies);
- spatiotemporal graph/sequence forecasting on METR-LA and existing 2026 work;
- Menger/network reliability, graph dynamics and the project's own verified **negative forecasting results**.

In particular, the general idea of combining topology, temporal dependence and feasible repair actions is **not new**. A candidate contribution must explicitly state *which predictive or causal result is absent from* the named prior methods. This selective search does **not** settle originality against all worldwide literature.

## Next experiment gate G2 (conditional, NOT preregistered yet)

Only upon obtaining suitable and independently validated data:
- freeze a timestamped decision origin `t0`, function `F`, horizon `H`, outcome definitions, actual actions, censoring and leakage prevention, with data split **by system and date**;
- include strongest permitted **time-only**, static topology/mincut, complete-network conventional reliability, dynamic hazard/Markov, no-action and physically feasible greedy/lookahead models as appropriate; no weaker strawman baseline;
- block features recorded after `t0` (including end-of-outage or post-repair duration) and restrict topology to contemporaneously known topology;
- report ablations eliminating full topology, forcing history, repair constraints **one at a time**, calibrated proper forecast scores (Brier/log loss where defined), paired uncertainty intervals, subgroup failures, absolute/relative computation and intervention costs;
- if testing policy efficacy from observed records, require identification/assignment assumptions or interventions; a predictive improvement alone is not a causal effect;
- register sample size, split, primary comparator and a meaningful gain threshold **before held-out outcomes**, then preserve negative outcomes.

**STOP at G0/G1:** do not train a new model on ANEEL textual matches, claim any causal repair effect, mine new post-event variables for shortcuts or report a novel universal law from these feasibility records. A negative source eligibility result is valid scientific progress, not a reason to weaken the rubric after seeing it.
