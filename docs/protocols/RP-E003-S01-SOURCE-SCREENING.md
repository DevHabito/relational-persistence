# RP-E003-S01 — Source screening and measurement-identifiability gate

**Status:** PROSPECTIVE SOURCE SCREENING. No case labels have been used to
fit, rank, or evaluate the physical scalar conjecture. No instrumented
system has been deployed in this milestone.

**Question:** Is there a public source, or a feasible controlled
instrumented system, in which operational capacity `B`, externally
measured disturbance intensity `I`, measured event-to-response
latency `tau`, and an independently observed recovery endpoint `Y`
can all be established without circular proxy definitions?

The existing scalar `C = B/(I*tau)` is a candidate operational
index, **not** a derived physical law. The verified finite-graph
RP-001/RP-F002 theorems do not guarantee that any of these candidate
measurements track empirical persistence.

## Evidence levels

- **Documented:** the cited source explicitly describes that data
  field, fault intervention, or functionality.
- **Conditional:** the data *might* support the measurement after
  examining field definitions and synchronization; do not assign it
  an operational meaning from a filename alone.
- **Missing in published documentation:** we have not found a source
  description establishing the required independent instrument.
  This is not proof that the entire dataset lacks it.
- **Instrument proposal:** a facility supports future collection;
  no observations have been collected by this study.

These labels are intentionally different from verified/validated.
A dataset release is not itself a scientific result about `C`.

## Public candidate screening (before target-data analysis)

| Candidate | Evidence that exists | Main unverified or absent requirements | Direct `C` test now? |
|---|---|---|---|
| **RCAEval**, fault-injection microservice benchmark | Published 735 labeled failures across Online Boutique, Sock Shop and Train Ticket, with injected-fault timestamps, root-cause annotations and time-series telemetry. RE1 metric-only; RE2/RE3 may include traces and logs | Independent pre-fault *capacity calibration*, injected perturbation amplitude in fixed units, controller response-event timestamp distinct from injected delay and outcome, and externally confirmed end of recovery are **not established by the release description** | **NO — conditional exploration candidate** |
| **Google Cluster Data 2019** | Publicly documented task/resource requests, machine capacities, job events, five-minute CPU histograms across eight Borg cells (very large BigQuery release) | No controlled or independently measured exogenous disturbance intensity, controller-event latency and an independent standardized perturbation-recovery outcome in the published field guide; observational confounding | **NO — exploratory operational-data candidate** |
| **OpenTelemetry Demo** | Open-source instrumented microservices with telemetry and fault-injection feature flags (including delays, failure rates, lock contention, CPU load and queue throttling) | A *deployment*, preplanned interventions, independent capacity measurement, response-event timestamps, observed recovery criteria and raw clock-quality checks have not been performed for this project | **NO — controlled instrumentation candidate** |
| **DeathStarBench** | Classical open-source suite for microservice workload and QoS experiments, with prior published performance analysis | Application code and load generators alone provide none of the four measurements or independent recovery labels for this study; would require a separate measurement protocol and substantial resources | **NO — controlled benchmark candidate** |
| **RP-E002-A01 METR-LA** | 207 actual traffic detectors with observed five-minute speed trajectories; preregistered one-hop graph forecast test completed with a **negative** result | No independently measured physical `B`, `I`, `tau`, disturbance onset and recovery; five-minute cadence is not response latency | **NO — already rejected at identification gate** |

### Confirmable source references

- RCAEval repository (Pham et al.): https://github.com/phamquiluan/RCAEval
- RCAEval dataset/archive: https://doi.org/10.5281/zenodo.14590730
  (nine dataset suites; repository/Hugging Face distribution also documented
  at https://huggingface.co/datasets/phamquiluan/RCAEval).
  RCAEval evaluates **root-cause localization**, not the scalar `C`.
  Injected faults in running microservices are not equivalent to naturally
  occurring failures in independent production organizations.
- Google 2019 cluster trace documentation:
  https://github.com/google/cluster-data/blob/master/ClusterData2019.md
  (2019 logs described at the machine/task scheduling level, with the
  published BigQuery availability and release terms).
- OpenTelemetry Demo:
  https://opentelemetry.io/docs/demo/ and
  https://opentelemetry.io/docs/demo/feature-flags/
- DeathStarBench: https://github.com/delimitrou/DeathStarBench ;
  Gan et al., ASPLOS 2019, DOI
  https://doi.org/10.1145/3297858.3304013
- Prior **negative** observed benchmark:
  [RP-E002-A01](../results/RP-E002-A01.md).

**No source above has been accepted as an identified external test of
the four-variable physical conjecture.** This is a genuine methodological
stop, not a reason to silently substitute speed variance, detector
count or interval spacing as missing variables.

### RCAEval case-index field audit — explicit schema, not inspected outcomes

The publisher's pinned [case-index documentation at
afeacb11bcc94dadfd1c8f483ee4377b2b8b614e](https://huggingface.co/datasets/phamquiluan/RCAEval/commit/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e)
defines `cases.parquet` with 735 index rows and a fixed field set.
The published index includes identifiers, root-cause labels,
`fault`, `fault_description`, `repetition`, `inject_time`,
`n_metrics`, `n_timesteps`, `time_start`, `time_end`,
`duration_minutes`, `normal_timesteps`, `faulty_timesteps`,
and log/trace availability counters.

**These names do not encode the required observables:**

- `inject_time` is the fault-injection timestamp, **not** a
  separately observed controller-action timestamp. It cannot
  establish `tau` by itself.
- `duration_minutes` and `faulty_timesteps` describe the
  recorded case duration/coverage, **not** an independently
  monitored time of sustained recovery. They cannot establish `Y`.
- `n_metrics` counts telemetry fields; it cannot calibrate
  processing capacity `B`.
- A fault category or description is not a calibrated, continuous,
  externally observed disturbance rate/variance `I`.
- Per-case traces and metrics may be useful for further
  **field-level exploratory auditing**, but treating a trace
  duration as actual controller response requires identifying
  the action span and clock-correlation semantics first.

This is a **schema-based nonidentifiability result** concerning
the publisher's published *index*, not a blanket assertion that
no future per-case instrumentation could contain a needed field.
The Hugging Face dataset card currently labels the mirror
`mit`; original artifact rights and linked software/data
licenses should be reviewed before redistributing anything.
No RCAEval fault outcomes were used here for model fitting,
and no recovery targets were constructed.

## Typed measurement dictionary — mandatory fields

An admissible study record must specify the following in explicit
units and link every observation to an independently auditable
measurement channel.

| Field | Type / units | Acceptable operational origin | Prohibited shortcut |
|---|---|---|---|
| `system_id`, `trial_id` | unique immutable strings | Preassigned experimental identifiers | Joining post hoc on fitted outcome |
| `event_onset_ns` | monotonic clock nanoseconds | Externally logged disturbance-onset event | Timestamp inferred from the target response threshold |
| `event_end_ns` | same monotonic clock | Independently logged end of intervention | Declaring end because the system recovered |
| `B` | positive work units / second | Separate calibration run or instrumented server-side completed-work count **before** the target trial | Sensor count, model coefficient, outcome-fitted throughput |
| `I` | positive disturbance work units / second | External load generator's independently logged *excess arrival rate* or independently characterized stochastic intensity under a **single declared convention** | Raw outcome variance, residual standard deviation fitted using Y |
| `tau` | strictly positive seconds | Timestamp difference between logged event onset and an actual, independently observed controller response action | Logging cadence, forecast horizon, nominal configured sleep, Y recovery time |
| `Y` | seconds to sustained recovery / right-censored duration | Separate health-probe event stream after the **logged end** of the perturbation and predeclared recovery rule | Computing Y from B/I/tau or declaring an unlabeled trough a failure |
| `clock_domain` | enum/string | Declares common monotonic clock domain or validated cross-clock offset and uncertainty | Subtracting wall-clock timestamps from unsynchronized machines |
| `rights`, `provenance` | license/source/version/hash | Source metadata, raw SHA-256, instrument version | A GitHub star, headline, or public URL as presumed reuse rights |

The example convention for `I` above is an *excess arrival rate*, not
a universal interpretation of "noise"; a different convention would
constitute **another candidate model** requiring new dimensional
analysis and preregistration. A noise standard deviation and noise
variance are not dimensionally interchangeable.

### Dimensions and invariances

Under the illustrative work-rate convention
`[B]=work/time`, `[I]=work/time`,
`[tau]=time`, the scalar has dimension `[C]=1/time`.
This is **not a dimensionless physical constant**. Changing time
units changes its numerical representation even with the same
underlying system. Any comparison must disclose and hold the units
constant or separately specify a justified reference timescale
`t_ref` and preregister the dimensionless product
`C*t_ref` as an altogether *new* operational index.

If `I` is a variance, its dimensions change, and the same
normalization is invalid. The numerical range, calibration and
monotonicity of `C` are **not** established by algebraic positivity.

### Independent-channel separation requirement

The four data streams must not share an outcome-derived estimator.
For a controlled runtime experiment, at minimum:

- capacity `B`: independently executed calibration phase with a
  predeclared fixed processing workload and independent monotonic clock;
- intensity `I`: external injector counts arrivals and its own
  actual timestamps, without reading the system recovery trace;
- response latency `tau`: controller action and trigger timestamps
  recorded by an instrumentation channel, not nominal policy value;
- outcome `Y`: a separate monitor declares sustained recovery
  using the preregistered health signal and finite observation window;
- documented clock uncertainty and censoring, especially if a
  controller never responds or a system never recovers.

The instrumentation itself may affect the system. Calibration,
randomized order, idle baselines and independent instrumentation
audits are prerequisites; no measurements from these experiments
are claimed here.

## Consequences of censoring and zero values

- `I=0` or `tau=0` makes `C` undefined for the stated formula.
  No arbitrary `epsilon` can be introduced after the fact.
  Design a strictly positive intervention and positive temporal
  resolution **before** a comparison, or exclude this test model
  prospectively and disclose the invalid domain.
- Never discard runs that fail to recover: `Y` is right-censored.
  A fixed-time success flag may be preferable to an unbounded
  "recovery time" when censoring is common.
- Clock resolution/jitter and the workload unit must be reported.
  A preset controller pause is **not** an independently measured
  physical reaction latency merely because software was configured
  to wait.

## Adversarial tests before freezing a subsequent protocol

1. **Sensor-channel leakage:** verify that `B,I,tau` can be
   computed with the entire recovery channel withheld.
2. **Causal independence:** verify that the event and controller
   timestamps are not extracted from the definition of `Y`.
3. **Sham intervention:** retain randomized zero/idle conditions as
   *controls*, not divide by zero or assign them artificial `C`.
4. **Units perturbation:** rescaling time units must not alter
   qualitative ranking of physically identical trials.
5. **Classical baselines:** service-capacity/workload predictors,
   backlog conservation/queue-theory models, controller delay alone,
   intensity alone, and flexible multivariate controls.
6. **Topology negative control:** topology relabeling or rewiring
   only where a network topology is measured and valid, not a
   fabricated edge list.
7. **Held-out design:** randomize interventions, freeze the
   split before measuring target outcomes; publish failures and
   censoring rather than retuning inputs afterward.

## Decision and next experimental fork

**Gate RP-E003-G0: NOT IDENTIFIED FROM PUBLISHED DATA DESCRIPTIONS.**
No physical scalar test can be reported yet.

Two possible future paths, kept scientifically distinct:

1. **Dataset audit:** examine RCAEval's explicit case schema,
   independent fault-control timeline and field-level telemetry
   definitions. Admit it only if all four independent measurements
   can be recovered without target leakage; otherwise publish an
   explicit stop result.
2. **Controlled instrument pilot:** construct a modest,
   resource-bounded application with independent calibrator,
   load injector, controller-event logger and health monitor on a
   hosted runner. This may test measurement feasibility and
   classical queueing behavior, but it is not an independent
   observation of a universal law or a replacement for
   external-system replication.

Do not run a physical-law test until a distinct preregistration
defines `Y`, trial randomization, baseline models, held-out
scoring, failure thresholds, intervention range, data acquisition
permissions and maximum compute budget.

## Scope and attribution

All named benchmarks, microservice models, queueing baselines,
cluster traces, dataset schemas and spectral results are existing
literature or instrumentation practice. The project-original
contribution in this note is only the **explicit measurement
admissibility and stop protocol** tailored to the proposed index.
This note does not allege a priority claim or a new mathematical
theorem.
