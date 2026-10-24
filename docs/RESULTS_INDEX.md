# Results index

| Study | Inputs | Outcome | Evidence level |
|---|---|---|---|
| RP-001 | Two mathematical graphs with fixed dynamics | Different contraction despite equal scalar proxies | Mathematical counterexample and numerical checks |
| RP-AR1 | Two specified linear stochastic recurrences | Finite vs unbounded variance | Classical illustrative counterexample |
| KARATE-EXPLORATORY | An observed network topology, synthetic dynamics | Calculated model predictions only | Real topology + synthetic model; not empirical stability validation |
| RP-E002-A01 | Observed METR-LA speed trajectories; fixed DCRNN road-distance graph | Preregistered topology-forecast superiority **failed** at 15, 30 and 60 minutes | Genuine held-out observations; negative **model-comparison** result, not a physical-persistence test |
| RP-E004-P01 | Measured timings of a locally instrumented FIFO HTTP software service; two positive workload interventions and one sham | Preregistered software structural feasibility check passed; full sampled health trace was not archived | Controlled hosted software event measurements; **not** physical persistence or a predictive validation |
| RP-E004-P02 | Timestamped queue observations and server-side controller events in a four-trial local HTTP service pilot | Full-sample instrument audit passed: controller-on, controller-off and zero-load sham cases; historical records replayable | Controlled software experiment with independent log replay; **not** a test of a physical persistence law |
| RP-F003-A01 | Exhaustive enumeration of 32,768 labeled six-vertex graphs with identical degree-sequence pair controls | Exact normalized twenty-step squared-energy contrast 0.04207868 (> registered 0.01) | Deterministic exact computation and 121 passing regressions; separate Lean-verified one-step witness, not a Lean proof of the exhaustive maximum |
| RP-F004-A01 | A dimensionless scalar AR(1) state driven by two symmetric binary Markov noise chains, each with noise variance 1/100 | Exact stationary output variances 1/75 versus 1/45 under identical scalar proxies | Independent 4096-history exact-rational oracle (Python CI #40120059073) and Lean-verified rational fixed-point uniqueness (#40120059074), no empirical trajectories or Lean convergence theorem |
| RP-F005-A01 | Actual zero/one-step feedback delay, gain-one scalar difference equation; two additional prespecified gains | Exact six-step squared residual 0 versus 1; exact 25-step traces for six delay/gain combinations | 180 passing Python 3.11/3.12 regressions and Lean-verified real period-six identity (#40121843255); no measured physical latency |
| RP-E005-P01 | First prospective repetition of RP-E004-P02 on two fresh GitHub-hosted Ubuntu VMs (eight measured software trials) | **Registered full-sample replay gate passed**; 8/8 trials, 48/48 raw files; original records archived at `d48d041` | True hosted-software observations and two replay algorithms; no physical-law inference, independent hardware or predictor validation |

A claim may be mathematically proved and still be false as a physical interpretation; an observed topology is not an observed trajectory.
