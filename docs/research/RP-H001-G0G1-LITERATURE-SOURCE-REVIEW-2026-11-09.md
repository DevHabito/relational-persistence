# RP-H001-G0G1 — The central hypothesis meets its first literature and data eligibility gate

**9 November 2026** · Selective publisher-source review and fixed evidence-catalogue check  
**Classification:** `NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED` among the eight reviewed sources.  
**This is not a physics experiment, a predictive model result or a global claim that no suitable source exists.**

## What question was evaluated?

Our question is now specific enough to expose false confidence:

> Does a predecision description of the relational state, the historical dependence of external disturbances, and the set of genuinely feasible repairs contain **incremental predictive information** about a future, independently measured function of the system, once appropriate dynamic reliability, forecasting and decision baselines — including costs — are taken seriously?

This contains **three different claims**. Identifying a model's conditional distribution is mathematics. Improving held-out prediction is statistical evidence. Showing that one intervention is better than another is a **causal** claim, often requiring randomized assignment, justified identification or an explicitly artificial simulation. None follows solely from matching two sets of outage records.

The broad intuition that internal organization, disturbance memory and response capacity jointly matter is already present in the literature. It is **not new merely because we call it relational persistence**. An empirical contribution would need to identify precisely **which additional prediction** is absent from strong existing methods; a mathematical contribution would require a nontrivial original theorem with independent proof and prior-art checking.

The previously proposed explanation of **emergent physical time** is still an unanswered philosophical/physical conjecture. Setting a three-step horizon in a graph model does not derive time from relational noise.

## Actual research chronology and integrity boundary

This source gate was designed after earlier negative and positive results were known: RP-E002 (METR-LA held-out negative), RP-E006 (index-only recovery prediction negative), RP-F003/F004 (coarse topology and correlated-noise finite contrasts), RP-U004 (finite synthetic lookahead advantage but extra computation) and RP-S001 (exact finite graph degree/cut insufficiency). Several academic and dataset publisher descriptions were **also examined before** protocol [RP-H001-G0G1](../protocols/RP-H001-G0G1-ELIGIBILITY.md) was registered, by a standalone commit `2291d499583e594211e703c997ac3743f55dddcc` on a branch based on unmodified `main`.

This is therefore an **informed, retrospective and selective evidence audit**. It is **not a prospective independent test** of the research hypothesis. We did not download original source rows from any new candidate in this study, estimate an unknown statistical parameter, update earlier archives, train a model or manipulate the values of outcomes.

The fixed [source evidence register](RP-H001-G0G1-SOURCE-EVIDENCE.json) distinguishes three source classes (observed, synthetic, mixed); description-only, partial audited and complete joint original evidence; and four field statuses (`EVIDENCED`, `PROXY_ONLY`, `NOT_ESTABLISHED`, `CONTRADICTED`). `NOT_ESTABLISHED` means **not demonstrated with the sources we examined**, not proven absent from the world.

A separate fail-closed checker `experiments/rp_h001_source_eligibility.py` read those documented assessments against eight required criteria. It cannot substitute for independent source-row verification; its principal purpose is to make assumptions and erroneous eligibility promotions detectable.

## G0 — Literature: why the broad mechanism is not novel

### Dynamic reliability already includes time and resource decisions

**Michael Rubin and Dongping Du**, “A Review of Dynamic Fault Tree Analysis and Capacity Degradation for Complex Redundant Systems,” *Quality and Reliability Engineering International* 41(3), pp. 1161–1181, first published **28 November 2024**, DOI [10.1002/qre.3693](https://doi.org/10.1002/qre.3693). The review explicitly covers time-dependent failures, partial capacity degradation, remaining-useful-life estimates, fault-management gates and applications to multiple kinds of infrastructure. The authors describe scaling difficulties for previously unknown failure modes and limitations of partial-failure representations. This is **existing work**, not our discovered gap.

**Xiujie Zhao and Yi Luo**, “Dynamic reliability decision-making frameworks: trends and opportunities,” *Complex Engineering Systems* 4:22, published **29–30 November 2024** according to article page metadata, DOI [10.20517/ces.2024.54](https://doi.org/10.20517/ces.2024.54). Sequential reliability decisions, maintenance optimization and Markov decision-process frameworks are expressly identified. Combining a changing reliability state with a decision rule therefore cannot, by itself, be claimed as a new mathematical or engineering idea.

### Distribution-system restoration already optimizes actions subject to physics

**“Multi-Agent Deep Reinforcement Learning for Distributed Load Restoration,”** *IEEE Transactions on Smart Grid* 15(2), pp. 1749–1760, published online **31 August 2023** (March 2024 issue), DOI [10.1109/TSG.2023.3310893](https://doi.org/10.1109/TSG.2023.3310893). The publisher describes switch-sequence decisions with breaker constraints, invalid action masks, OpenDSS/Python simulations and IEEE 13-, 123- and 8500-node feeders.

**“Heterogeneous Multi-Agent Proximal Policy Optimization for Power Distribution System Restoration,”** *2026 IEEE Texas Power and Energy Conference*, published in IEEE Xplore **15 May 2026**, DOI [10.1109/TPEC67884.2026.11513130](https://doi.org/10.1109/TPEC67884.2026.11513130). The publisher describes sequential switching, DER coordination, physically constrained OpenDSS environments, and performance comparisons with existing reinforcement-learning approaches. We did **not** reproduce either paper's numerical findings or retrieve their source implementations. These publications are nevertheless direct prior art: a proposed graph-aware restoration policy cannot be presented as new merely because it considers downstream consequences or topology.

### Network forecasts already incorporate temporal dependence and graph information

**“Sensor-Driven Short-Term Forecasting on the Metropolitan LA Traffic Dataset: A Comparative Study for Multi-Step Prediction,”** *Sensors* 26(12), article 3917, **2026**, [publisher article](https://www.mdpi.com/1424-8220/26/12/3917). The paper describes a controlled comparison of Transformer, graph-based and temporal models, and a graph-enhanced hybrid under a common protocol. The reported errors are specific to that study and not verified by our implementation. This is another reason that combining graph and time representations is **a baseline family, not an original principle**.

The repository's own [RP-E002-A01](../results/RP-E002-A01.md) had already evaluated real 2012 METR-LA traffic observations and reported **failure** of its preregistered graph advantage at 15-, 30- and 60-minute horizons. The registered [RP-E006-P01](../results/RP-E006-P01.md) index-only predictor reported **68.186 ms** held-out recovery MAE versus **11.118 ms** for an already available finite-backlog comparator in its software service benchmark. Those negative outcomes directly refute any narrative that the project already established a universally useful new persistence index.

**G0 verdict: `BROAD_MECHANISM_ALREADY_REPRESENTED_IN_PRIOR_ART`.** No distinct new general theorem, new method or experimentally demonstrated advantage has been identified by this selective review. This does not rule out a **more narrowly stated contribution**, but that claim must be independently located and tested, not invented in advance of evidence.

## G1 — Is any presently reviewed real-world dataset sufficient for a causal policy comparison?

The test requires all of the following **at once**: (1) complete historical function-relevant topology known at origin, (2) predecision forcing history, (3) an independently observed functional outcome, (4) feasible actions and constraints, (5) actual timestamped chosen actions, (6) true causal-time observation/release availability, (7) measured action/computation costs, and (8) full original coverage across all required joined tables at selected origins.

The fixed catalogue contains **eight** candidate source families. Its source and evidence classifications are transparent:

| Source family | Observation class / evidence actually examined | What is grounded | Critical missing or unverified information | Gate |
|---|---|---|---|---|
| **ANEEL 2026** | Real publication; previous original occurrence/interruption files authenticated, but no joint operational-action record | Exact source bytes, millions of textual keys, civil-time and feeder-string agreement in D06–D10 | Energized feeder graph at decisions, chronological operator decisions, available alternatives, independently released predecision state, costs | **Not eligible** |
| **EAGLE-I** | Real county outage series, publisher paper/documentation only in this gate | Utility-map-derived 15-minute customer outage observations, 2014–2022; documented source coverage and quality issues | Individual feeder network, switch actions and field repair costs | **Not eligible** |
| **DOE event-correlated outages** | Derived observation, federal catalog description only | County outage estimates linked to DOE-417 events using event time/geography | Predecision switching topology, independent operator action log and costs; original source files were not opened | **Not eligible** |
| **SMART-DS** | Synthetic network; publisher documentation only | Detailed simulated electric equipment and feeder topology, load/time-series and outage scenario capabilities | Not a natural historical source; no specific model ZIP has been downloaded/replayed here; no verified live action log or physics-feasible tested controller | **Simulator candidate only** |
| **METR-LA** | Real traffic readings; prior original source and model-graph audit | 207 sensor trajectories, 5-minute speeds and external sensor-distance graph; original negative RP-E002 result | Graph proxy is not a historical electrical connectivity state; no fault/repair action truth | **Not eligible for real repair policy** |
| **Google Borg 2019 cell-a** | Real operations; partial original audit only | Whole `machine_events` table audited, 46,219 original events | No original collection/instance row bodies jointly audited, incomplete feasible state and action release times | **Not eligible** |
| **NASA C-MAPSS** | Synthetic turbofan-degradation trajectories, NASA dataset description | Simulated sensor, operational settings, failure progression | No explicit full relational network or real timestamped maintenance choices and costs | **Not eligible** |
| **IEEE OpenDSS test feeders** | Synthetic circuit-model assets, EPRI documentation | Distribution feeder examples and simulation tools | No selected, audited source outage/action-history study with physical incident outcomes | **Model assets, not an independently validated study** |

**ANEEL sources:** publisher dataset [interruptions](https://dadosabertos.aneel.gov.br/dataset/interrupcoes-de-energia-eletrica-nas-redes-de-distribuicao); prior project [RP-U005 D10 source result](https://github.com/DevHabito/relational-persistence/pull/82) remains on a **separate unmerged draft research branch**. ANEEL labels and timestamps should not be misrepresented as a complete before-decision graph or operator history.

**EAGLE-I sources:** **Christina M. Brelsford and colleagues (2024)**, “A dataset of recorded electricity outages by United States county 2014–2022,” *Scientific Data* 11, DOI [10.1038/s41597-024-03095-5](https://doi.org/10.1038/s41597-024-03095-5); [ORNL dataset DOI 10.13139/ORNLNCCS/1975202](https://doi.org/10.13139/ORNLNCCS/1975202). The publication explicitly explains that zero-outage rows are not stored and missing collection intervals cannot always be distinguished from zeros. It describes county estimates, not original feeder switching logs. This is a **published-data limitation, not a guessed absence of every possible auxiliary file**.

**Event-correlated source:** [U.S. DOE/PNNL catalog description](https://catalog.data.gov/dataset/event-correlated-outage-dataset-in-america), indexed with metadata checked in 2026. Direct opening of the catalog URL was inconsistent in this research session; **no original source file was retrieved**. This is accordingly only a description-level candidate, not a verified data product.

**SMART-DS:** [U.S. National Laboratory SMART-DS description](https://nrel.sitefinity.cloud/grid/smart-ds) and [Open Energy Data Initiative record](https://data.openei.org/submissions/2981). The publisher explicitly calls the networks **“realistic but not real”** and describes outage scenario support. It is a good candidate for a subsequent **synthetic** power-flow/action-feasibility study; source metadata are not a successful experiment.

**METR-LA:** [previous original negative experimental record](../results/RP-E002-A01.md). **Borg:** [previous original machine-only coverage gate](../results/RP-E012-D03.md). **NASA C-MAPSS:** [NASA prognostics repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/). **Test feeder models:** [EPRI OpenDSS examples and IEEE test circuits](https://opendss.epri.com/ExamplesDocsandTestCases.html).

The source-gate code evaluated eight fixed fields per source using a **fail-closed rubric**. **No** source had jointly verified actual action logs, decision-time availability, action/computation costs, or complete cross-table population coverage; those **four criteria were not established for all eight**. Six of the eight lacked proven predecision full topology. These are **counts of missing evidence in the register**, not physical measurements or assertions of datasets' permanent nonexistence.

**G1 verdict: `NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED` among these eight sources.** The program separately recorded **SMART-DS as `SIMULATOR_CANDIDATE_NOT_YET_VALIDATED`**. Five catalogued candidates were tagged as observed-data families, three as synthetic. None were promoted from publisher metadata to independently verified original rows within this review.

## Engineering verification and first-run source integrity

The frozen protocol precedes the machine-readable [source evidence file](RP-H001-G0G1-SOURCE-EVIDENCE.json), gate code and synthetic tests. The first isolated hosted execution [GitHub Actions #42593200510](https://github.com/DevHabito/relational-persistence/actions/runs/42593200510) ran **24 synthetic/adversarial controls successfully** then evaluated the eight reviewed candidates **without downloading any original third-party records**. The original reported decision was `NO_END_TO_END_REAL_WORLD_CAUSAL_SOURCE_IDENTIFIED`.

The evidence checker rejects a source that substitutes a `PROXY_ONLY` feature for real historical topology, contains unknown status, has missing criterion or reference, duplicates a source ID, alters the original eight-source set or claims this metadata review downloaded joint source rows. It also rejects an “observed” conclusion from a synthetic scenario and cannot be bypassed with Python `-O`. A completely evidenced **invented fixture** must be accepted, so the negative outcome is not hardcoded.

The original first-run JSON is preserved unchanged in [`RP-H001-G0G1-source-gate.json`](../results/RP-H001-G0G1-source-gate.json). Its first source-job SHA-256 was `e68eeef1d665e22c34e4adee1407a9613d707e0e1cd2313e32bd45282660c6f0`. The hosted workflow also retained a JSON-only artifact; its ZIP SHA was reported as `86be5ded3a46c66a98a378b945f204104ca75419aaff603a543d21d8476fbd3c`. No large source data or private operational identifiers entered the report.

This suite is an **internal consistency test of manual evidence classifications**. It cannot independently verify the semantics of the bibliography or discover omitted third-party source files. Human evaluation of each original source remains essential. Any future qualifying source requires a separate protocol and source-byte audit.

## The next meaningful experiment, rather than another ad hoc scalar

The next defensible action is a **source and simulator feasibility gate** for **one small, independently materialized SMART-DS feeder** with original source SHA and clear OpenDSS version, reconfiguration actions, synthetic outage process, power-flow constraints and operator/compute-cost conventions. Before any lookahead optimization, reproduce a standard simulator and verify independent feasibility, including radiality, voltage, branch limits, islanding policy and power balance. Graph reachability alone is **not** enough for electrical service restoration.

Only once these checks pass should a predeclared G2 benchmark compare:
- strong no-repair, fixed-priority and conventional switching/restoration baselines, not only a weak greedy heuristic;
- classical static/dynamic reliability models and models with predecision forcing history;
- full graph versus coarse graph versus shuffled/ablated topology, plus short/long forcing-memory ablations;
- prediction quality, restored **electrical load** and safety violations, actual solver/decision compute costs and modeled operational switching costs, all under the same constraints and decision information;
- held-out **different feeder families / synthetic generators**, with configuration and random seed split specified before evaluating outcomes.

If a candidate fails to improve a properly specified baseline, the correct result is **no demonstrated added value**. If it improves only on source-specific simulator data, that establishes **synthetic predictive utility in that scope**, not a universal relation law or causal field effect. Real-world validation would require independently logged operational histories and outcomes.

### Where the project now stands

**Demonstrated:** carefully controlled finite counterexamples and exact source-data consistency audits; source provenance and a falsifiable eligibility criterion; negative forecasts preserved.

**Not demonstrated:** an original theorem joining topology, disturbance memory and repair constraints; incremental external predictive benefit beyond modern dynamic reliability; real causal repair-policy efficacy; physical time emergence.

**Decision:** G0/G1 is complete as an evidence review, but the central scientific hypothesis is **OPEN / NOT YET EMPIRICALLY TESTABLE WITH THE REVIEWED REAL-WORLD SOURCES**. We should move to an explicitly synthetic, electrically constrained feasibility exercise only after verified source materialization. If that is infeasible, stop rather than announce a favorable result from an invented model.
