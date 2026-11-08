# RP-U005-D01 — When is a real trace enough to test relational repair?

**Research lead:** Felipe Gianini Romero  
**Date of source review:** 8 November 2026  
**Class:** retrospective, read-only source-eligibility audit  
**Baseline examined:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`  
**Review scope frozen before the new gate implementation:** [RP-U005-D01-SOURCE-ELIGIBILITY.md](../protocols/RP-U005-D01-SOURCE-ELIGIBILITY.md) at `3f280219daf14a089b00e763a008c0d6afa4750c`. This was **not** an outcome preregistration: I already knew the prior Google D03 report and had inspected the publisher schemas.

## Why this gate matters

The RP-U004 finite experiment distinguishes preserving *some* terminal route (F1) from preserving *two internally disjoint* routes (F2), while one eligible link at a time is restored to a replacement node. In a retrospective computational cost audit, a two-step policy preserved 100 additional F2 scenario-ticks but used 24,960 additional instrumented table lookups. None of those totals measures a natural system's physical repairs or the time cost of an actual decision.

The data problem is therefore not merely to find a large public record of failures. I need to be able to identify **a particular topology and function, the information available before a repair decision, the actual action, the downstream outcome, and the operative costs**. Otherwise I could manufacture a resemblance between an event and the synthetic model without testing the claim.

## Source record I can actually audit

The existing [RP-E012-D03 original run #40425342721](https://github.com/DevHabito/relational-persistence/actions/runs/40425342721) had already authenticated the complete Google Borg 2019 cell-a `machine_events` object in GCS, generation `1596844153688368`. The original full compressed object SHA-256 was

```text
b04455f48e57c303fc8987b41e35911d89f3aa31e5a6d3997f07e27749dc1791
```

Its original immutable **summary JSON**, distinct from the raw compressed machine events, has SHA-256

```text
393ed949a3aec3e4cd27f6e6ca8f617102b855a5e0934021d3b6909be31b6f0a
```

The already completed D03 audit reported 651,854 full compressed source bytes, 46,219 valid event rows, 10,001 distinct machine identifiers, 27,777 additions, 17,941 removals, 501 updates and 18,274 descending adjacent timestamps in source-file order. A person reading the event-file prefix as if it were a chronological slice would be mistaken.

My new Python source gate checks the **already committed summary bytes** against the original fixed digest, rechecks the machine event-count accounting, the snapshot partitions, original source size/hash metadata and the negative cross-table coverage flags. It does **not** download and rehash the original 651,854-byte GCS machine object in this session. The source-object authentication remains an observation reported by the previous preregistered D03 run; the new check authenticates its archived summary and checks internal consistency.

The original D03 source contained **zero raw `collection_events` or `instance_events` rows**. The first metadata page listed 50 matching instance shards but was explicitly paginated. The listed first instance shard was 465,101,721 compressed bytes, much larger than the previous 2 MiB raw machine budget. The original joint scheduler state was not reconstructed, and the event timestamp was not proved to be the time an online decision-maker first received the information.

The original D03 snapshots at strictly earlier trace-time cutoffs were *event-implied machine categories*, not observed full machine occupancy. At one time cutoff the recorded partition was 9,841 active-implied, 63 removed-implied and 97 without a prior event; at the other it was 9,825, 121 and 55. The new source gate tests that these partitions cover the previously observed set of 10,001 machine identities; it never assigns the 97 or 55 unknowns an invented physical state.

## Why the public Google schema cannot answer the RP-U004 repair question

The publisher's [v3 Protobuf schema](https://github.com/google/cluster-data/blob/48b12446464b0422abcc18e0ec5b0b13e2f3a90c/clusterdata_trace_format_v3.proto) describes `MachineEvent` as an ADD, REMOVE or UPDATE, with trace-relative time, machine ID, obfuscated top-of-rack switch ID, capacity, platform and a possible missing-data reason. It documents REMOVE as usually related to failure **or repairs**. Such an event is not a record of an intentionally selected graph edge with its feasible alternatives and the resource cost of choosing it.

The separately described instance/collection tables can contain scheduling state, identifiers, requests, machine placements and missing-event flags. They are valuable for a different scheduler question; they cannot be silently interpreted as a physical two-terminal connectivity graph or as the controller's repair-action log. The publication does not establish a full historical decision-time release record or instrumented compute cost for each candidate repair decision. Published field names also do not demonstrate which counterfactual repair orders *would have* worked.

I classify this specific public trace as **not eligible for direct observational replication of U004's physical graph-edge repair policy**. This is a narrower claim than saying that the Borg dataset is bad, that its full tables can never be used, or that private Google logs contain no such information. Reconstructing complete scheduling history, for example, would still require an independent source-window and causal-time audit, and it would change the research question.

## Alternative primary sources screened, not used as fresh outcomes

| Candidate and dated original source | What the publisher actually describes | Honest status for a *direct* U004 policy test |
|---|---|---|
| **Google Borg 2019 cell a** — Google schema pinned to commit `48b1244`, publication format notice by Nan Deng, 10 August 2020 | Machine changes, task/collection scheduling events, requests and usage; prior complete machine shard only | **BLOCKED:** cross-table completeness unproven, no observed chosen physical edge-repair action/decision-cost fields in inspected public schema |
| **Alibaba cluster trace 2017** — [publisher schema](https://github.com/alibaba/clusterdata/blob/3858992ca41bf92082e6d6522ddf0bebd14e838b/cluster-trace-v2017/trace_201708.md), reviewed repo revision 13 October 2026 | Server ADD, temporary software errors and hardware errors with resource capacities, and service/task observations | **SCHEMA REVIEW ONLY; NOT ESTABLISHED:** failures and resource effects are not the same as recorded edge-repair choice and associated costs; original rows not inspected here |
| **100 natural disasters** — Stephen Platt, Andrew Coburn, Farnaz Mahdavian and Oliver Carpenter, [Dryad dataset](https://doi.org/10.5061/dryad.d7wm37qc0), published 9 January 2026 | Observed/discussed economy and society recovery across disasters; indicator definitions, bibliographic support and outcomes on months/years scale | **POTENTIAL FOR A SEPARATE RECOVERY-OUTCOME STUDY**, not U004 edge policy; row-level workbooks were not downloaded or audited here |
| **Road restoration with heterogeneous teams** — Qiao Pan, [Mendeley Data v1](https://doi.org/10.17632/89pktc22t7.1), published 12 October 2026 | 51 synthetic optimization benchmarks plus 54 modified inputs, generated repair durations, route/solver summaries, 381 recorded optimization runs | **SIMULATION/ALGORITHM BASELINE ONLY:** not independent real-disaster repair observations; no field efficacy claim is justified by simulated costs |

No candidate in this table has passed all required checks for **this** direct policy comparison. The entries are descriptions of *publisher-documented scope*, not independent row-level audits of four datasets. A genuine dataset may still be useful under a different scientific question after a separate protocol is written.

## Separate failure classes — do not blur them

**Partial source coverage** occurs when data could in principle contain relevant state, but the project has not authenticated enough of it. This explains the Borg joint scheduler-history gap.

**Target mismatch** occurs when the real source describes machine addition/removal but the hypothesis demands restoration of selected network links and a two-path functionality predicate. More rows do not repair a missing measurement definition.

**Decision-time ambiguity** occurs when the published record supplies event time but not provable observation/receipt time; giving a model all retrospectively reconstructed information at an earlier decision time would leak future information.

**Causal nonidentifiability** occurs even if every actual chosen repair and outcome is observed. A single realized historical order does not reveal what every alternative greedy/lookahead order would have caused, absent appropriate intervention design or causal assumptions.

**Unmeasured resource costs** occur when repairs or algorithm outputs are recorded but decision runtime, energy, wages, intervention delay or data-acquisition resources are not. The hypothetical λ from the separate U004-C01 accounting exercise is **not** an acceptable substitute.

This study does not estimate a counterfactual, restore service, or fit a predictive model.

## Implemented evidence gate and negative controls

`experiments/rp_u005_source_eligibility.py` reads only the already frozen `RP-E012-D03-first-run` archive. It pins the original report and machine-object SHA values, enforces the original counts and snapshot partitions, demands that unverified joint/online history remains unverified, and issues the deliberately narrow decision `RP_U005_DIRECT_POLICY_SOURCE_BLOCKED`.

`tests/test_rp_u005_source_eligibility.py` contains adversarial cases that edit a copy of the original summary bytes, forge a replacement manifest digest, alter event counters and attempt to promote incomplete source coverage to certified history. A separate `python -O` subprocess verifies that scientific guards cannot be erased by interpreter optimization. Every originally reported favorable and adverse source result is left untouched.

**Validation status:** the exact new code commit, Python 3.11/3.12 logs and any failures must be recorded here after the current GitHub Actions workflow finishes. No new Lean theorem is warranted: source completeness and absence of a measured field are data-provenance and identification questions, not consequences of algebra.

## Decision and what follows

**Current decision:** `RP_U005_DIRECT_POLICY_SOURCE_BLOCKED` for an observational U004 physical-edge-repair policy claim on the archived Google machine-only evidence and inspected public field schema.

This does **not** reverse the registered RP-E012-D03 verdict, does not alter the negative E010/E011 observational forecasts, does not contradict the synthetic RP-U004 result, and cannot settle the underlying search for a universal relational-persistence law.

A next study can proceed along one of two explicitly separate directions:

1. **New real-source search, before outcomes.** Find and preregister a public original event/action dataset containing a timestamped graph state, declared function, real ordered link-repair interventions, measured decision and restoration costs, and credible historically available inputs. Demand original-row and causality audits before any comparison. If it cannot be found, report the identification limit rather than fabricate its existence.
2. **A different eligible outcome question.** Treat the Dryad disaster recovery data or Alibaba server events as potential sources for an *observational association* question whose units, temporal scale and baseline are defined anew. They cannot directly validate U004's specific link-repair intervention.

For the direct U004 empirical claim, no new measured effect has been established. Source screening is a necessary result in itself when it prevents a wrong inference.
