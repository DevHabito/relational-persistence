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

### RP-E010: first independent archival workload source

- Move beyond author-built software: audit the third-party HPC2N Seth
  operational trace, using the exact pinned Git mirror revision from
  preregistration `0aa03d6`; do not mistake the mirror for a verified
  bit-exact copy of the PWA original.
- **Original data gate PASSED** in hosted first-run #40143917458, metadata archived at `ecae2dd`: 202,871 records, 201,992 structurally eligible; two parser oracles agreed on the source SHA, IDs and field counts. **All 202,871 records lack a queue ID**, and 878 have missing status. No forecast was computed.
- **Do not** use NASA-iPSC-1993 SWF as real submission times:
  its original conversion substitutes start times because
  actual submission is absent.
- Only after E010-D01 proves a usable source should a fresh
  E010 observational forecast preregistration define real
  scheduler-specific states, causal cutoff, data partition,
  endpoints, classical controls, confounding and negative gates.

### RP-E010-P01 — external observational prediction test, after D01

- The source-only D01 gate passed on a version-pinned third-party mirror; that did **not** compute or validate forecasts. No per-queue identifiers were present and upstream filtering must remain disclosed.
- The [P01 protocol](../preregistration/RP-E010-P01.md) was frozen at `dfec155` **before** any predictive computations. It defines one aggregate reconstructed waiting proxy, two independent time-count oracles, a fixed 70%-of-time cutoff and three unfitted classical forecasts.
- The original, complete **RP-E010-P01 result was NO_REGISTERED_OBSERVATIONAL_GAIN** on run #40145857634, archived at `f8560cf`: 49,995 chronological heldout task waits, trend MAE 234,691.80 s versus static 227,534.07 s and historical mean wait 123,965.25 s. All source and double event-counter gates were valid. The trend failed to beat **either** classical comparator and was worse than static in all three registered processor groups. No retrospective trimming, split edits or coefficient tuning.
- The P01 target is *historical submission-to-start waiting time*, **not** the service-recovery target from RP-E007/009 and cannot be described as the same endpoint. It is not a new physical law.

### RP-E011-D01 — second independent official operational source gate

- Retain the negative RP-E010-P01 result (49,995 heldout tasks; trend was worse than both registered classical controls) as immutable evidence. No claim of universal generalization or retrospective holdout reuse.
- Freeze the official Argonne Leadership Computing Facility Polaris 2022 CSV **before** reading its job rows or computing any forecast (`0529649`). The publisher dictionary lists actual queue names, requested-node counts and two distinct wait definitions, but file-level availability is not yet verified.
- **First RP-E011-D01 source attempt #40148017404 was SOURCE_ACCESS_BLOCKED** by HTTPError retrieving the official Polaris resource. No CSV bytes, queues or predictor scores were observed. The original metadata are immutable at `4366736`.
- Only after verified D01 eligibility, preregister a separate queue/resource-aware observational prediction model with strong per-queue classical controls, correct held-time/eligible-time semantics, causal pre-arrival inputs and independent holdout.

### RP-E011-D02 — separately registered primary-source candidate after D01 blocked

- Freeze new candidate JSSPP 2017 CERIT-SC grid jobs original extended SWF at `e3a2d21`; this is **not** another D01 attempt or a change to the D01 outcome.
- **Original D02 run #40148759632 was DATASET_SCHEMA_REJECTED**: 59,430,886 bytes downloaded with verified source SHA, 472,400 valid numeric SWF prefixes and 13 actual extended queue names, but precisely ONE invalid job ID violated the preregistered zero-invalid requirement. Full original source summary archived at `b9b0f02`. No source gate may be retroactively passed by relaxing to `<=1` errors.
- No waiting-time forecasting, recovery experiment or Lean theorem is claimed by a source eligibility study. A separate predictive protocol is required after passing source availability.

### RP-E011-D03 — separately frozen original-source anomaly localization

- D03 was registered at `2df3d83` **after** D02's original source-rejection summary but **before** D03 implementation or per-row investigation. It is **known-anomaly forensics**, not independent confirmation of eligibility.
- First official source run #40181814358 **ANOMALY_LOCALIZED** the lone nonpositive ID: **integer 0 in the first physical line and first data row**. Two independent ID readers agreed on all 472,400 records. Exact source size/SHA and D02 schema counts matched. Original D03 metadata archived without replacement at `056fe32`.
- The original D02 `DATASET_SCHEMA_REJECTED` and original E010 negative 49,995-job forecast remain unchanged. Do not claim that knowing the first-line location proves a publisher fault or that dropping it retroactively validates D02.
- Before any new queue-aware observational forecast, separately define the prospective job population and disclosure for an initial ID 0, train/holdout chronology, prerecord available queue/processor state, and strong historical per-queue baselines. Do not use any new outcomes to choose inclusion or thresholds.

### RP-E011-D04 — conditional source temporal feasibility after known ID anomaly

- D04 preregistration at `c6e33b1` was frozen **before new D04 implementation/data** and explicitly allowed only the already-identified physical-line-one ID=0 as a new-source population exception. D02 remains definitively REJECTED.
- First original D04 source-only run #40183836342 passed **TEMPORAL_SOURCE_FEASIBLE**: 472,399 conditional candidate jobs, 303,210 diagnostic / 169,189 heldout, 13 real queues but only two meeting the prespecified >=100 cases on both sides. Data are timestamp-ordered with many ties. Original audit archived `1fef039`.
- D04's source feasibility is **not** a prediction test, and the later queue imbalance and MAE findings were not used to select its gates.

### RP-E011-P01 — first queue-aware primary-source wait-time forecast

- P01 protocol was separately frozen on `main` at `d6029a1` before predictor source or heldout results; implementation code at `7c556ca` passed 465 regressions per Python version and existing Lean 4 CI. It uses strictly causal pre-origin events, online historical starts, a fixed 70/30 clock cutoff, all 169,189 heldout jobs and two primary unfitted classical comparators. Original full prediction bytes were preserved temporarily, original SHA and summary permanently.
- First full original prediction run #40185076529 was **NO_REGISTERED_QUEUE_GAIN** with valid source/feature oracles: TREND MAE **45,328.01 s**, STATIC **43,953.98 s**, HISTORY **34,309.43 s**. TREND lost to both. Archived unchanged at `534720b`; no threshold edit or new source/holdout choice.
- **Strong concentration:** 149,760 and 18,880 of 169,189 heldout jobs belonged to just two queues (~99.68%); seven other original queues had zero heldout jobs. Do not claim independent performance across 13 queue policies. The medium requested-size subgroup was mildly favorable versus static, but the full frozen result is negative.
- Next work should be an independent research question or external source/year, not refitting on this original holdout and calling a second evaluation blind. Preserve both E010 and E011 external negative findings and clarify their distinct targets and source types. Do not interpret their software-engineering indicators as a physical `C=B/(I*tau)` test.

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
