# Research roadmap and stop conditions

## Stage 0 — methodological baseline (this commit)

- Register RP-001 before computation, preserve immutable tag and Git history.
- Execute an independent dynamical outcome calculation, negative controls, and a counterexample.
- Publish the known mathematical source of every result. Make failed cases first-class artifacts.
- Report dataset provenance and be explicit where the dynamics are synthetic.

## Stage 1 — derivations, bounds, and obstructions

- Classify the exact assumptions that make the quotient index predict a chosen persistence observable.
- Construct minimal graph families with identical proxy triples but divergent persistence outcomes.
- Study delay and noise correlation; compare models with matched degree sequences and alternative spectra.
- Validate analytical derivations with independent implementations, interval bounds where appropriate, and limited Lean 4 formalization of clean lemmas.

### Stage 1 progression — exact audits, not empirical validation

- RP-F003 established, by exhaustive six-node integer computation, that
  a fixed degree sequence does not determine the chosen twenty-step
  disagreement observable. Its separate one-step rational witness
  passed Lean 4 (not the exhaustive maximum).
- RP-F004 registers an exact scalar AR(1) model with two binary Markov
  noise sources. Their marginal distributions are identical but temporal
  correlations differ. The planned exact moment and full-path
  checks test a distinct missing parameter, with no field data.
- Next structural concern: response delay cannot be represented merely
  by a declared one-step `tau`; an actual delayed state equation,
  stability boundaries, and noncircular measurement definitions
  require separate registration and control experiments.

- RP-F005 preregisters real one-step *state-feedback delay* versus zero delay with a fixed gain and prehistory. An exact six-step periodicity witness and negative/contrast gain controls are evaluated with two independent rational implementations. Unlike a matched-proxy study, this comparison **must not** be claimed to keep measured `tau` equal; it does not test the scalar index.

## Stage 2 — real-world performance measurements

- Choose a public dataset with observed capacity/update rates, measured noise/uncertainty, response delays, and an independently observed failure/recovery target.
- Freeze proxies, exclusions, preprocessing, temporal split, baselines, error measures, primary effect size, and falsification thresholds before target evaluation.
- Estimate parameters only on training windows. Use held-out or time-forward test windows, calibration plots, uncertainty intervals, permutation/negative controls, and sensitivity analyses.
- Compare index-only predictors against constant, single-variable, simple linear, topology-aware and domain-standard baselines.
- Do not equate real graph edges with real measured stability outcomes.

### Measurement feasibility checkpoint: RP-E005-P01

- Frozen two-runner replay protocol before new measurement at `20d9262`.
  First hosted execution #40124159620 completed; 8/8 software trials
  and 48/48 source files passed independent replay, archived at `d48d041`.
- Independently replay all source logs, record cross-run measurement
  variation only descriptively, and archive every original trial,
  including runs stopped by preregistered gates.
- Do **not** represent reproducible hosted instrumentation as external
  field replication or a confirmation of the quotient C. A distinct
  held-out predictive protocol is required after this feasibility gate,
  and must include meaningful independent variation of measured
  disturbance, actual response time and a classical queueing baseline.

### Prospective forecast checkpoint: RP-E006-P01

- Frozen forward train/test design **before** results at `2aeabc6`;
  first run #40126290924 passed 27/27 software instrumentation trials,
  with source bytes and the original **negative** prediction result
  archived at `0fa7ad2`. No historical RP-E005 labels entered the fit.
- Use **actual service-applied** timestamps and pre-end queue
  observations. Replay recovery from raw health samples,
  with an independent second algorithm, before scoring.
- Preregistered comparison returned **NO_REGISTERED_PREDICTIVE_GAIN**:
  68.19 ms index-only held-out MAE vs 11.12 ms finite queue baseline
  and 72.50 ms constant baseline. The 10% criterion against both
  was **not** met. Do not retune on those nine holdout targets.
- This is a restricted hosted FIFO benchmark, not a claim
  about unrelated physical systems. Subsequent study
  should target truly independent environments and
  adequate inferential power.

### Prospective incremental temporal-state audit: RP-E007-P01

The prior RP-E006 holdout may not be used to adjust or validate a subsequent hypothesis as though it remained unseen. RP-E007 prospectively tests a two-sample temporal backlog prediction on new held-out data against the classical static queue baseline. The 10% MAE threshold, source replay and STOP gates were frozen in commit 150dd5f. The first hosted run #40129313787 produced **PASS_TREND_INCREMENT**: 13.617 ms trend MAE versus 23.227 ms static MAE on nine new held-out trials, archived unmodified at dd718df. This is a classical software queue forecasting result, not a proof of new physics. Any future proposed relational state model must demonstrate incremental utility beyond established queue and control alternatives.

### RP-E008: conservative simulation-transfer stress test

- Do not interpret RP-E007's positive result as transfer to independent service implementations. Freeze a new 72-case deterministic discrete-event FCFS model with irregular arrival and job-duration variability **before** generating its outputs; protocol at `2ca6d8e`.
- The first source run #40131416314 passed exact 72-case FCFS oracle equality and the frozen >=10% aggregate MAE-gain gate, showing a 59.43% improvement across 36 held-out simulation cases. All source and event traces were permanently archived at `8a2c11a`.
- Preserve the important adverse findings: trend lost 16/36 individual holdouts, and **early-burst** arrivals favored static backlog (5.000 vs 12.125 ms MAE). No regime may be retrospectively excluded or its results described as a universal positive effect.
- Any later real-service, hardware or physical validation needs another experimental protocol. An in-silico model can expose engineering failures, but it is not external empirical confirmation of a law.

### RP-E009: first cross-implementation executable software test

- Following the positive RP-E008 in-silico result with a negative early-burst subgroup, freeze **before measurements** an operationally different TCP/asyncio single-worker FIFO implementation (`61674d0`).
- Measure own accepted/start/completed task events, calibration throughput, pre-end queue samples and independently replayed recovery. Nine new diagnostic and nine new heldout trials are collected on sequential hosted jobs.
- **First RP-E009 run #40134924622 PASSED** the frozen >=10% heldout MAE gate: trend 10.527 ms versus static 20.201 ms (47.89% lower), nine diagnostic plus nine new heldout cases and 126/126 raw role/event files independently replayed. Original source bytes and outcome archived at `7cca290` without replacement.
- This is still hosted Python software, not independent industrial deployment, sensor validation or evidence of a physical persistence law.

## Stage 3 — relationship to RZS and PMFF

- Demand a typed and dimensionally consistent mapping from `(R,q,mu,K,pi)` to observed quantities.
- Test invariance under relabeling and admissible gauge changes. Search for nonidentifiability and nonclosure counterexamples.
- Separate abstract theorems, empirically supported restricted models, and physical conjectures.

## Stage 4 — external review

- Short stand-alone papers; independent reproduction; explicit adversarial review and rejection criteria; archived versions; no premature universal claims.

## Non-negotiable stop conditions

- A core equation becomes undefined for ordinary admissible inputs without a declared limit.
- A target metric was computed from the candidate index rather than observed independently.
- A parameter is chosen using test outcomes without disclosure.
- An assumption is added only after observing a failed result and then presented as preregistered.
- Public source data are missing, ambiguous, or contradictory and cannot be resolved.
