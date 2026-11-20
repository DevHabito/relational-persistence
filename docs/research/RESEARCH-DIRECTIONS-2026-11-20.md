# Research directions: perturbation, functional loss, and recovery

**Date:** 20 November 2026  
**Record type:** Methodological reasoning note, not an experiment, preregistration, observation, or collaboration record.

## Why separate these events?

A disturbance can alter a system without disabling its declared function. Other disturbances cause a genuine functional loss, perhaps requiring a shutdown, repair, rearm sequence, or explicit restart. Removing the external cause does not by itself prove that the function has returned.

This suggests three distinct observables:

1. **Perturbation:** an intervention or change in external conditions occurred.
2. **Functional status:** an independently defined operational criterion is met or violated.
3. **Recovery:** that criterion is restored and sustained as required by a declared recovery rule.

Anomaly is not synonymous with failure. Component restoration is not necessarily system-level functional restoration. These distinctions belong to established reliability and control practice; they are not presented here as an original law.

## A candidate event timeline

For a future observational study, consider the following timestamps only if they can be independently identified:

- `t_inject`: start of a controlled perturbation.
- `t_function_lost`: the declared function first fails, if it fails.
- `t_cause_removed`: the perturbation ends, if that event is observed.
- `t_function_restored`: the declared function again meets its threshold for the required observation interval, if recovery occurs.

The candidate recovery lag `t_function_restored - t_cause_removed` must not be computed from guessed timestamps. It may be undefined for a tolerated perturbation without functional loss, or censored when recovery is not observed. Sampling cadence, timestamp precision, asynchronous records, controller rearm operations, and unobserved intermediate states matter. A measured positive lag would not establish that positive lags are universal.

## Questions worth testing

**RP-RQ-01 — Tolerance without functional loss.** How often does a recorded perturbation change measured behavior without crossing a predetermined failure threshold?

**RP-RQ-02 — Disturbance removal versus recovery.** After actual functional loss, how frequently is restoration delayed relative to the removal of the initiating condition? What role do shutdown and reset sequences play?

**RP-RQ-03 — Component and system function.** Can a component report a normal state while the required end-to-end system function remains unavailable?

**RP-RQ-04 — Observation error.** Can missing records, timestamp resolution, or sensor/reporting delays create an apparent recovery interval or hide one that exists?

**RP-RQ-05 — Baseline comparison.** Can ordinary state-machine, reliability, or industrial-control models explain observed transitions as well as or better than a proposed relational predictor?

## Possible independent observational source

The public DAYPSCI dataset concerns event-based controlled fault injection in PLC-controlled industrial cyber-physical systems and describes process states and recovery phases. It is a **candidate source for inspection**, not data already processed in this repository for these questions.

- Public dataset identifier: https://doi.org/10.71486/2DRF-1G53
- Published dataset description: https://doi.org/10.1016/j.dib.2026.113146

Before writing a prospective protocol, verify access and licensing, event schema, time synchronization, actual measurement of functional output, sampling resolution, recovery-state definitions, and which features were available at each decision time. If the required timestamps or outcome measurements do not exist, record the study as underidentified. Do not replace unavailable observations with inferred events.

## Connection to existing Relational Persistence work

Existing finite graph studies specify functions such as F1 source-to-target connectivity and F2 redundant paths. Existing software service experiments use separately declared operational recovery outcomes. Those results have their own scopes and original protocols.

No retrospective reinterpretation is permitted: a simulated repair edge is not an industrial repair event, and a software queue becoming idle is not evidence that a physical production process recovered. This document does not validate the historical scalar index `C=B/(I*tau)`, establish a cross-domain physical quantity, or derive the dynamics from PMFF.

Consult the [research scope](../foundations/SCOPE.md), [claim ledger](../CLAIM_LEDGER.md), [dated research record](RESEARCH-RECORD-2026-11-03.md), and [research roadmap](../protocols/ROADMAP.md).

## Criteria for continuing

- Distinguish tolerance from actual functional loss before selecting the study population.
- Define the function independently of the candidate predictor and record reset/rearm actions explicitly.
- Freeze thresholds, exclusions, baselines, and negative controls before outcome inspection.
- Preserve unsuccessful, zero-effect, and inconclusive cases.
- Avoid a claim of external validation, peer review, universal persistence, or agreement from outside researchers.

**Status:** a documented line of reasoning only. No DAYPSCI observations were analyzed, no tests were run, and no prior experimental results or claims were changed.
