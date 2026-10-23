# RP-E002: observational dataset screening — METR-LA

**Status:** candidate screening only. No observational prediction has been
run and no outcome is reported here. This record does not change the frozen
RP-001 protocol.

## Why this dataset is a candidate

METR-LA contains observed highway speeds from **207 loop detectors** in
Los Angeles County at a **five-minute sampling interval**, spanning
March–June 2012 (commonly reported as 34,272 steps). Unlike the
Zachary karate-club example, it provides **measured time trajectories**.

Primary prior work:

- Li, Y., Yu, R., Shahabi, C., & Liu, Y. (2018).
  *Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic
  Forecasting*. ICLR. https://arxiv.org/abs/1707.01926
- Original research implementation and data preparation:
  https://github.com/liyaguang/DCRNN
- Third-party archived CSV distribution (record, **not a verified license**
  to redistribute): https://doi.org/10.5281/zenodo.5146275
- Caltrans PeMS data-source and access conditions:
  https://dot.ca.gov/programs/traffic-operations/mpr/pems-source

The original DCRNN study treats roads as a **directed weighted network**.
That differs materially from RP-001's fixed **undirected, unweighted,
symmetric consensus** model. We must not reuse RP-001's spectral theorem as
a prediction model for these observations without new assumptions,
justification, and evidence.

## Crucial identifiability problem

METR-LA's five-minute **sampling cadence is not the physical delay
between an event and a system's response**. The sampling interval cannot
be renamed `tau` merely to make the scalar capacity-noise-latency index
computable.

Similarly:

- The number of sensors is not, without justification, operational
  update capacity `B`.
- The standard deviation of observed speeds is not automatically noise
  `I` (it contains real traffic signals and systematic variation).
- Physical response, sensor reporting latency, network communication
  delay and forecast horizon are different concepts.
- A road adjacency threshold or normalization fitted using test records
  would leak information into evaluation.

**Decision gate E002-G0:** A full empirical test of the old scalar index
must be marked **not identified** unless independently measured
`B`, `I`, `tau`, and an independent persistence outcome can be
operationalized. No proxy substitution is permitted after observing the
test-set results.

## Narrow benchmark possible with these observations

We can separately test a weaker *predictive* question, not the three-scalar
persistence formula:

> Does a preregistered road-network model improve short-horizon held-out
> speed forecasts over temporal-only models when the topology and data
> handling are fixed without using the held-out period?

This assesses observational relevance of **relational topology**, not
a new physical law and not causal recovery from perturbations.

### Candidate preregistration design (not yet frozen)

- **Primary outcome:** absolute error in measured road speed, in the
  original dataset units, at 15, 30 and 60 minutes ahead.
- **Primary metric:** MAE per horizon with a training-only missingness
  mask and disclosed sensor weighting. Report RMSE and sensor-level
  distributions as secondary metrics.
- **Comparison candidates:** last-observation persistence, training-only
  historical time-of-week mean, a regularized local autoregression, a
  topology-blind multivariate predictor and a classical fixed-graph
  diffusion model. Compare against the DCRNN baseline only if its
  original preprocessing and fair computational budget are reproducible.
- **Chronology:** one contiguous train/validation/test partition
  established before model fitting; no random cross-time mixing.
  Fit scalers, missingness policies, and hyperparameters without using
  the test interval. Evaluation starts after a documented embargo of
  the longest model lookback/forecast horizon.
- **Decision rule:** assess predeclared paired changes in error against
  baselines, not whether a narrative seems convincing. Failure to improve
  is a published negative result. The quantitative superiority threshold
  and evaluation period must be fixed in a later preregistration **before**
  reading test targets.
- **Leakage controls:** no full-series covariance, correlation-derived
  graph, imputation parameters, exogenous event segmentation or
  baseline estimates trained on test observations.
- **Robustness:** periods of low demand, rush-hour shifts, sensor outages,
  one-week block bootstrap where justifiable, sensor-level heterogeneity,
  ablation of topology and chronological sensitivity.

### Missingness and incident interpretation

Some distributions encode missing/outage records as **zero speeds**;
other zero speeds may represent genuine congestion. This status must be
audited from the actual files and original processing documentation.
Do not treat each zero as a measured physical stop, and do not silently
interpolate zeros using future readings.

METR-LA does not by itself provide independently validated labels for
the time at which a physical perturbation occurred or the time the
road network recovered. A *causal stability/recovery* endpoint therefore
requires additional, independently documented event data and predeclared
matching rules. It cannot be inferred from a downturn in speed alone.

## Acquisition gates before a result may be reported

1. Confirm source version, terms for scientific analysis and any
   redistribution restrictions; retain checksums for raw downloaded
   artifacts and never commit raw restricted data.
2. Verify timestamps, sampling uniformity, sensor IDs, network
   geography, units, missing/zero semantics and true temporal coverage.
3. Record the static directed weighted adjacency's provenance and
   construction; distinguish genuine road connectivity from
   distance-based surrogate graphs.
4. Freeze the forecast target, baseline specifications, split boundaries,
   masking, compute budget and acceptance threshold **before fitting**.
5. Report held-out performance, negative controls, uncertainty,
   effect sizes, data exclusions and failures without post-hoc changes.

## Evidence and ownership

This document is a prospective **dataset-screening memo**. It is not a
claim that data have already been downloaded, that the proposed protocol
has been preregistered, that the measurements establish `B/I/tau`, or
that a predictive advantage has been found. Classical traffic forecasting
and DCRNN remain the appropriate prior literature and comparisons.
