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

- Freeze the design and independent train/test temporal ordering
  **before** acquiring any new results. Three intended loads,
  three scheduled action delays, 18 training and nine
  future held-out software trials; no historical RP-E005
  labels enter the new model.
- Use **actual service-applied** timestamps and pre-end queue
  observations. Replay recovery from raw health samples,
  with an independent second algorithm, before scoring.
- Compare the fitted index-only prediction to a constant and
  a classical finite backlog/throughput approximation,
  requiring >=10% held-out MAE improvement against both.
  Report NO_GAIN when measurements are valid but the
  threshold is not met; preserve STOP for bad data.
- This is a restricted hosted FIFO benchmark, not a claim
  about unrelated physical systems. Subsequent study
  should target truly independent environments and
  adequate inferential power.

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
