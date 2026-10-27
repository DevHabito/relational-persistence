# Research roadmap and stop conditions

## RP-U002-A01 — temporal replacement and relational repair (finished finite study)

- Separately registered **BEFORE implementation/first run** alone on main `fa7f9d0`; fixed original six-vertex seven-edge A/B graphs, each original single-internal-node loss, and all t=0..5 snapshots.
- A new identity replaces the failed component at t2; at most ONE old-neighbor link reappears per step, predetermined ascending numeric order using a publicly assumed graph blueprint. Controls undergo exactly the same original failure but no replacement or links. No adaptive tuning or ecological regrowth.
- Original first run #40499618845 `FINITE_TURNOVER_REPAIR_CONTRAST_VERIFIED`, archived `07c07e6`; reviewed code PR #57 `e0929d6` passed Python 3.11+3.12 (691 regressions each) and Lean 4. Registered B bottleneck node2 has six present components at t2 yet no F1 path until t4. The original F1 20 case-tick sums A 20 repair/20 no-repair, B 17 repair/15 no-repair. F2 sums A 11 repair/0 no-repair, B0/0. All negative/zero effects preserved.
- Next falsifiable gate: compare baseline vertex-connectivity, calibrated repair costs, randomized/frozen topology families or exhaustively degree-matched small graphs; test alternative local vs path-informed repair rules under truly equalized budgets and temporal observability. New source/experimental protocol required BEFORE selecting graphs or results. Ecological/medical observation requires actual domain data and domain-appropriate recovery definitions.
- Do not claim a new universal law, Menger theorem, plant dynamics, general system behavior, stochastic confidence interval or observable meaning for the historical scalar C from this exact toy model.

## New track: Functional Continuity (RP-U001)

- Motivation: can a specified functional output persist even when individual system components are lost? Amazon canopy gaps are ONLY an analogy. Do not rename existing ecological resilience/functional redundancy or graph connectivity as new theory.
- RP-U001-A01 separate prospective protocol committed ALONE on main `81ce6d1` before code/first result. Two fixed undirected graphs, 6 nodes and 7 links each, match source/target degrees; exhaust ALL 16 removable-internal-node subsets each; compare independently implemented BFS vs simple DFS, exact relabeling case checks, stronger two-path function and frozen k=2 tie negative control.
- Original first #40490582350: **FINITE_FUNCTION_CONTINUITY_CONTRAST_VERIFIED**, archive `f54c784`; k0..4 retained-path counts A=[1,4,2,0,0], B=[1,3,2,0,0]. k=1 contrast 4/4 vs 3/4, k=2 BOTH 2/6. Initial two-disjoint-route function differs; k=1 ZERO for both under stronger function definition. Python 658 per version, Lean finite Bool single-deletion certificate pass. This is known graph theory with disclosed toy networks.
- NOT YET DONE: a separately registered dynamic component-turnover / repair / rewiring model with temporal performance, controls and independently fixed costs; then real/ecological/health data, nontrivial baseline comparisons, pre-origin measurement validity and true heldout predictions. Strong universal claims may be false and MUST be exposed by negative controls.

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

### RP-F006-A01 — finite pre-origin identifiability obstruction (SYNTHETIC ONLY)

- Protocol frozen at `3670d7d` before any RP-F006 simulator implementation or Lean proof. Use known negative external forecasting evidence only for motivation, not for tuning synthetic contrast or reframing prior heldout.
- Original first synthetic run #40205665104 was `FINITE_NONIDENTIFIABILITY_VERIFIED`: the SAME entire pre-origin event history, two queue snapshots, resource requests, running service age and history-start indicators are compatible with observed target waits **1 and 100 s** in distinct FCFS-compatible worlds. All registered controls, exact rational oracles and dispatch replays passed.
- Exact sharp bound from existing triangle inequality: any deterministic predictor using only the common observed input has max two-world absolute error >=**99/2**; midpoint prediction **101/2** attains equality. Lean 4 CI `40205365501`, reviewed PR #45 merged `406e923`, original synthetic report frozen `caab6ad`.
- State limits accurately: earlier work is NOT asserted to have globally work-conserving immediate dispatch (the original H/R waits are 1 second); no empirical HPC scheduler or probabilistic population inference; no newly discovered theorem; no universal physical law and no scalar C test.
- **Next distinct question:** identify causally *measurable before submission* scheduler capacity, actual running occupation, elapsed times, requested resource/walltimes, policy reservations and priority. Only then justify new empirical evaluations on a truly independent source/year. Do not recycle the seen 169,189-task CERIT-SC holdout as untouched.

### RP-F007-A01 — guaranteed-cap versus merely requested runtime (SYNTHETIC ONLY)

- The protocol was frozen on main at `93d5dc4`, *before* implementation and results. Reviewed code at `4023bb1` passed Python 3.11/3.12 and Lean 4 CI on exact PR head; original first synthetic run #40229910510 was `BOUNDED_STATE_MINIMAX_VERIFIED`, archived without replacement at `6d0d794`.
- R is already executing at age 30 in the original single-server FCFS-compatible model, which does not claim global work conservation before target arrival. A **guaranteed and enforced** runtime maximum of 500 yields the exact positive integer residual wait set 1..470 (sharp minimax 469/2 s), and a guaranteed maximum of 90 yields 1..60 (sharp minimax 59/2 s).
- The explicit 205-second mathematical worst-case error bound decrease is conditional on TWO DIFFERENT public-cap regimes, not same-information treatment or observed real-world forecast improvement. Endpoints and full interval containment are Lean-checked; independent Python simulates all 530 finite worlds, pre-origin histories and dispatch.
- Negative advertised-only control: an actual 501-second runtime under requested walltime 500 violates a true bound. Real schedulers' effective limits and possible overrides must be verified before using such a bound. The earlier RP-F006 nonidentifiability theorem still applies: knowing an upper bound does not reveal the exact future residual.
- **Next practical stop gate:** source/time-stamped configuration and whether assigned limits are enforceable at submission, plus historically recorded running age, requests, current occupancy, missing/censored jobs and scheduling policy. A new source/year and fully preregistered temporal design are required before another independent heldout predictive claim. Keep E010 and E011 negatives unchanged.

### RP-E012-D01 — original external Borg v3 causal-schema feasibility (SOURCE ONLY)

- NEW independent provider Google `google/cluster-data` pinned to publisher commit `48b1244`. Public schema was consulted **before** registration; protocol `a024612` explicitly discloses informed triage rather than blind field discovery.
- Original first official two-file Git-blob-verified run #40234431456 was **SCHEMA_EVENT_METADATA_PRESENT_RUNTIME_CAP_UNVERIFIED**, archived `e68202a`: two parsers concurred on timestamped events, requests, priorities, machine capacity, missing-event flags and window utilization schema.
- Not yet observed: a provider-enforced **wallclock execution-duration cap** or reliable before-origin row availability. `assigned_memory` is a MEMORY bound. `SCHEDULE` is placement rather than guaranteed actual process start. A usage measurement window closing after origin cannot enter that origin's causal feature set; reconstructed/missing events cannot be treated as exact historical transitions.
- No original Google production trace rows were read, no BigQuery spend was incurred, no new forecast or Lean theorem was attempted, and no RP-F007 practical validation was claimed. E010/E011 original external forecast negatives remain final.
- **Next gate:** preregister a minimal provider-authentic raw-event subset (exact machine/cell/time provenance and a zero/low-cost access plan), inspect missingness/synthetic-event prevalence and timestamp alignment WITHOUT scoring any predictor. Stop and archive if source access or historical feature releases cannot be established. Full hard-cap transfer needs a different verified field/provider or independently verified policy-level enforcement records.

### RP-E012-D02 — bounded ORIGINAL real event prefixes, not forecasts

- [Original protocol](../preregistration/RP-E012-D02.md) frozen on main `e5efc724` before any E012-D02 metadata/row read. The zero-cost anonymous source and deterministic first 100-listed-shard choice were public-documentation-informed, not blind.
- First original provider GCS source run #40421367613 **SOURCE_PREFIX_AUDITED**, original archived `a6051fc`: cell `a`, first compressed machine/instance shards, verified provider generation and 16,384-byte actual compressed SHA-256 prefix each, no full gzip CRC/whole-object data. 500 machine ADD; 495 instance SUBMIT + 5 LOST, five nonzero missing-event flags. Adversarial Python + existing Lean regressions passed before initial source access.
- Both file prefix streams contain **many temporal inversions** (258 machine, 183 instance), so neither filename nor row ordinal identifies a chronological holdout. The 1000 original rows are NONRANDOM and NOT representative. They do not establish source completeness, trace-wide missingness, actual placement/start equivalence, hard enforced runtime caps or real forecast gains.
- **Next proposed independent feasibility gate:** can bounded access to all required original shards for a fixed actual event-time subwindow establish event-history coverage and a sound tie/missingness reconstruction? Select exact range/sources and budget BEFORE access; prohibit target-label inspection and any parameter refitting on prior E010/E011 revealed holdouts.

### RP-E012-D03 — COMPLETE machine original source with bounded cross-table coverage

- Informed, new source-only preregistration at `41befcd` BEFORE D03 source access or code; D02's machine vs instance compressed-size contrast was already public and acknowledged. Reviewed original code merged `5d05d53` after 636 Python regression tests per runtime (3.11 and 3.12) and existing Lean 4 CI.
- First original Google GCS source audit #40425342721 was **MACHINE_EVENTS_COMPLETE_OBJECT_AUDITED_JOINT_UNCERTIFIED**, archived permanently at `d1c0f25`: one sole unpaginated cell-a machine shard, complete original 651,854 bytes verified with GCS generation, full provider MD5, independent entire-file SHA256 and gzip trailer/CRC; 46,219 real events, 10,001 machine identifiers, 18,274 adjacent original timestamp inversions.
- Event-implied machine category snapshots at 1e12 / 2e12 microseconds: latest ADD/UPDATE 9,841 / 9,825; latest REMOVE 63 / 121; no earlier machine event 97 / 55. These are NOT certified live scheduler machine capacity or real-time publication.
- Other tables metadata only: first `collection_events` object advertised 133,462,892 compressed bytes (10 matching objects no pagination), first `instance_events` object 465,101,721 bytes (50 matching in first page WITH pagination; not total count). **JOINT_CAUSAL_HISTORY_NOT_CERTIFIED** must remain true. No raw collection/instance rows read D03.
- Next source challenge: register cost/coverage-credible independent ways to guarantee cross-shard time completeness and event receipt timing for a selected interval, including all instance/collection shards, without claiming a prefix is chronological. Any future forecast requires an entirely separate protocol and heldout design.
- Preserve unchanged RP-E010/E011 original negative results and RP-F006/F007 conditional formal examples.

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
