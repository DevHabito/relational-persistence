# Prior work and provenance

This is a starting bibliography, not a completed novelty review. Citations identify existing results; they do not demonstrate priority for any proposal here.

## Established literature (not our discoveries)

1. **Olfati-Saber, R., Fax, J. A., and Murray, R. M. (2007).** "Consensus and Cooperation in Networked Multi-Agent Systems." *Proceedings of the IEEE*, 95(1), 215–233. DOI: [10.1109/JPROC.2006.887293](https://doi.org/10.1109/JPROC.2006.887293). Graph structure, connectivity, delays and consensus dynamics provide the immediate mathematical background to RP-001.
2. **Nair, G. N., and Evans, R. J. (2004).** "Stabilizability of Stochastic Linear Systems with Finite Feedback Data Rates." *SIAM Journal on Control and Optimization*, 43(2), 413–436. DOI: [10.1137/S0363012902402116](https://doi.org/10.1137/S0363012902402116). Information/data-rate restrictions and control stability are already classical study topics; capacity and stability cannot be claimed as a new association.
3. **Zachary, W. W. (1977).** "An Information Flow Model for Conflict and Fission in Small Groups." *Journal of Anthropological Research*, 33(4), 452–473. DOI: [10.1086/jar.33.4.3629752](https://doi.org/10.1086/jar.33.4.3629752). Source of the observed karate club relations; network data alone do not measure our proposed persistence observable.
4. **OECD / European Union / EC-JRC (2008).** *Handbook on Constructing Composite Indicators: Methodology and User Guide.* OECD Publishing. DOI: [10.1787/9789264043466-en](https://doi.org/10.1787/9789264043466-en). Operational and statistical cautions in index construction, scale choices and sensitivity analyses.
5. **Luce, R. D. (1959).** *Individual Choice Behavior: A Theoretical Analysis*. Wiley. Classic context for stochastic choice representations; relevant to local operational kernels, not evidence for the scalar index.

6. **Weisstein, E. W.**, ["Connected Graph"](https://mathworld.wolfram.com/ConnectedGraph.html), *MathWorld*. Reports the established labeled connected-graph count sequence (OEIS A001187), including 26,704 at six vertices. Used as an independent count sanity check for RP-F003, not an endorsement of the model.
7. **Liu, M., Yuan, Y., You, L., and Chen, Z. (2018).** ["Which cospectral graphs have same degree sequences"](https://doi.org/10.1016/j.disc.2018.07.017), *Discrete Mathematics* 341(11), 2969–2976. Existing research on degree sequences and Laplacian cospectrality; not claimed to prove RP-F003's particular energy difference.

8. **The Pennsylvania State University**, [STAT 510 Lesson 1: Time Series Basics](https://online.stat.psu.edu/stat510/Lesson01), time-series lecture materials on weak stationarity, white-noise assumptions and AR(1) variance. The independent-white-noise formula used as RP-F004's negative control is established textbook mathematics.
9. **Arellano, M.**, [*Time Series*](https://www.cemfi.es/~arellano/Time-Series.pdf), lecture notes, CEMFI. Documents autocorrelation and stationarity of AR(1)-style sequences; general time-series background to RP-F004. The repository's binary Markov-input comparison is a separately specified toy example and is **not** claimed to originate this theory.

10. **Shin, J. S., Miyazaki, R. and Kim, D. (2023)**. ["Stability regions of discrete linear periodic systems with delayed feedback controls"](https://doi.org/10.1186/s13662-023-03781-5), *Advances in Continuous and Discrete Models* (2023), article 35. Prior work on delayed discrete feedback and stability regions. RP-F005's six-step special-case identity is classical finite-dimensional recurrence algebra, not claimed as original theory.

11. **Little, J. D. C. (1961).** ["A Proof for the Queuing Formula: L = λW"](https://doi.org/10.1287/opre.9.3.383), *Operations Research* **9**(3), 383–387. The stationary average work-in-system relation is well-established. The RP-E006 finite observed-backlog/(postaction throughput) **heuristic is not Little's law**; it is a deliberately simple competing engineering approximation.
12. **Scikit-learn developers**, [TimeSeriesSplit documentation](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html). Forward-ordered validation motivates separating training and future test labels. RP-E006 uses a single frozen, sequential two-job split rather than claiming statistical performance from a full time-series cross-validation study.

## Project history and primary records (no novelty inferred)

1. **Romero, F. G. (2026).** *The Romero Law of Relational Stability (RZS): A Closed-Form Statement, Cross-Domain Operationalization, and Computational Verification.* Historical formulation. Retained for provenance, not adopted as a validated law. The archived document calculates the putative outcome from its input quotient, so its algebraic consistency check does not count as external physical confirmation.
2. **Romero, F. G.** [*Precategorical Modal Field Framework*](https://github.com/DevHabito/precategorical-modal-field-framework), living public research archive, particularly `manuscripts/foundational/draft/04_operational_kernels.md`, `docs/RESULT_CLASSIFICATION.md` and `docs/SCIENTIFIC_STATUS.md`. Mathematically relevant but not yet linked by a derivation to the present dynamics.
3. **Relational Persistence research program (2026).** `docs/preregistration/RP-001.md` and its subsequent results. A research protocol and a case study, not a new theorem of graph theory.

## Novelty check remains open

A genuine novelty review requires claim-by-claim searches in network control, stochastic stability, graph spectra, inference, delay differential equations, critical transitions, and information theory. The existence of a new label does not imply the underlying mathematical content is new. Do not assert new physics on the basis of either a composite index or a classical spectral counterexample.

## Additional established queue-monitoring literature for RP-E007

- Ross, J. V., Taimre, T., and Pollett, P. K. (2007), [Estimation for queues from queue length data](https://doi.org/10.1007/s11134-006-9009-2), Queueing Systems 55:131-138. Prior research on rates inferred from sampled queues. The new two-sample RP-E007 forecast is a much simpler engineering extrapolation and not a novel theory of queues.
- Bhaskara, A., Gollapudi, S., Im, S., Kollias, K., and Munagala, K. (2025), [Online Distributed Queue Length Estimation](https://research.google/pubs/online-distributed-queue-length-estimation/), ACDA 2025. Contemporary work on monitored queue length; contextual rather than an equivalent experiment.

## Established discrete-event verification context for RP-E008

- [Improving performances of the emergency department using discrete event simulation, DEA and the MADM methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6001262/), Section 4.3 (2018). Distinguishes verifying a simulator's behavior against its assumed model from validating the model against real-world behavior. RP-E008 verifies a second queue software model only; it does not provide that independent empirical validation.
- [Reproducible analytical pipelines for healthcare discrete-event simulation: an open guide and worked examples](https://pmc.ncbi.nlm.nih.gov/articles/PMC13675625/) (2026), describes scenario and sensitivity analysis as standard reproducible simulation practice. No novelty in using a discrete-event simulation or a fixed sensitivity grid is claimed.
 
## RP-E009 prior technology: independent executable queue and monitoring

- [Python documentation, asyncio streams](https://docs.python.org/3/library/asyncio-stream.html) and [asyncio FIFO queues](https://docs.python.org/3/library/asyncio-queue.html): standard network and asynchronous scheduling mechanisms; implementing a TCP/asyncio queue is not new computer science.
- [Kleijnen, Bettonvil and Van Groenendaal (1998), Validation of Trace-Driven Simulation Models](https://doi.org/10.1287/mnsc.44.6.812): classical context for trace-based model comparisons. Comparing two software systems is not a substitute for verifying general transfer to real-world systems.
 
## RP-E010 external production workload provenance

- [Parallel Workloads Archive, HPC2N Seth log](https://www.cs.huji.ac.il/labs/parallel/workload/l_hpc2n/): a real Swedish HPC production cluster run under Maui, with archived submission, wait and runtime fields, known conversion anomalies, and extensive upstream filtering of dominant users and bursts. **Ake Sandgren** is credited for original logs. The RP-E010 mirror is separately version-pinned; PWA original compressed-file equality is NOT established by that fact.
- [SWF 2.2 official column specification](https://www.cs.huji.ac.il/labs/parallel/workload/swf.html): 18-field job records, missing=-1 conventions, submit, wait, runtime, allocated processors, status and queue meaning.
- [Parallel Workloads Archive, NASA-iPSC 1993 conversion notes](https://www.cs.huji.ac.il/labs/parallel/workload/l_nasa_ipsc/): no real job submission timestamps were recorded; converted SWF substituted job starts for missing submit times. **Excluded as an independent observed queue-arrival dataset.**
- D. G. Feitelson, D. Tsafrir and D. Krakov (2014), [Experience with using the Parallel Workloads Archive](https://doi.org/10.1016/j.jpdc.2014.06.013), *Journal of Parallel and Distributed Computing*, 74(10), 2967–2982: source curation, cleanup and anomalies are methodological issues requiring disclosure, not evidence of a newly discovered physical mechanism.

## RP-E011 official ALCF Polaris scheduler data provenance (not a new result)

- [ALCF Polaris DIM_JOB_COMPOSITE catalog](https://reports.alcf.anl.gov/data/polaris.html), Aug–Dec 2022 CSV, catalog original size 27,825,794 bytes. Resource page https://reports.alcf.anl.gov/data/ANL-ALCF-DJC-POLARIS_20220809_20221231.html. The official catalog is NOT a content-addressed repository and does not provide a preregistered SHA.
- [Official ALCF job data dictionary](https://reports.alcf.anl.gov/data/datadictionary/datadictionary_dim_job_composite.html): `QUEUE_NAME`, node requests/allocations, chronological queued/start/end, and distinct `QUEUED_WAIT_SECONDS` (includes holds) versus `ELIGIBLE_WAIT_SECONDS` (excludes holds). Future allocation outcomes and termination codes must not become ex-ante predictors.
- Required acknowledgment: "This data was generated from resources of the Argonne Leadership Computing Facility, which is a DOE Office of Science User Facility supported under Contract DE-AC02-06CH11357."
- Standard-library Python CSV parsing is existing technology; parser/source eligibility checks are not novel physics or forecasting evidence.

## RP-F006 prior queue-state identifiability and residual work — established, NOT novel

- Ward Whitt (1999), [*Predicting Queueing Delays*](https://doi.org/10.1287/mnsc.45.6.870), *Management Science* 45(6):870–888. Queue length and service-class observations alone do not generally encode remaining work: additional information about elapsed services and conditional residual-service distributions improves queue delay inference.
- [*Queueing Systems* lecture notes](https://iadan.win.tue.nl/queueing.pdf), chapter on residual service time and Pollaczek–Khinchin relations. Even a single-server waiting-time calculation depends on residual workload, not solely a sampled number of waiting jobs.
- HPC @ LLNL, [*Batch System Primer*](https://hpc.llnl.gov/banks-jobs/running-jobs/batch-system-primer). FCFS versus backfilling and service availability are established operational scheduling choices; an exact finite one-server witness is NOT a model of all real HPC scheduling policies.
- RP-F006-A01's real-valued sharp 99/2 lower bound is **ordinary triangle inequality** conditional on a specifically frozen two-world observation, not an original general queue theorem. The registered model does NOT assert the scheduler is globally work conserving during the two recorded 1-second idle dispatch delays; it proves a separate finite FCFS-compatible existence witness.
- The registered original external negatives RP-E010-P01 and RP-E011-P01 cannot be retroactively explained causally by RP-F006's SYNTHETIC example. Scheduler data may require residual service, active resource use, priority and policy information not identified by the earlier proxy; that is motivation for NEW source validation only.

## Existing queue waiting-time prediction methods (not project discoveries)

- P. Murali and S. Vadhiyar (2016), [Qespera: an adaptive framework for prediction of queue waiting times in supercomputer systems](https://doi.org/10.1002/cpe.3735), *Concurrency and Computation: Practice and Experience*. Queue-specific historical prediction and adaptive scheduling are well established.
- [Predicting queue wait time probabilities for multi-scale computing](https://pmc.ncbi.nlm.nih.gov/articles/PMC6388012/) (2019). Historical/job-attribute-based probabilistic wait prediction preceded RP-E011-P01. The present work does not propose an original algorithm for probabilistic queue forecasting.
- [Queue congestion prediction for large-scale HPC systems using a hidden Markov model](https://doi.org/10.1007/s11227-022-04356-z) (2022). Time-varying queue congestion and historical scheduler records were studied independently of the present project.
- RP-E011-P01's queue-specific historical median, waiting-count ratio and two-snapshot trend are **classical operational benchmarks**. Their preregistered comparison on one external source is a study of empirical incremental value, not a claim of mathematical priority. Status: original negative, no >=10% joint improvement. Extremely imbalanced queues and shared system policies limit generalization.

## RP-E011-D02 external mixed-workload source after original ALCF block

- [JSSPP, CERIT-SC 2017 workload archive](https://jsspp.org/workload/index.php?page=cerit), original [extended SWF grid-jobs trace](https://jsspp.org/workload/logs/2017/cerit/grid-jobs.swf). Source documentation adds the execution node, queue name, qsub submitted command-line arguments and requested GPUs to standard 18-field SWF. Documented capabilities are **not** measured coverage in the file until D02 passes.
- Klusáček, D. and Parák, B. (2017), *Analysis of Mixed Workloads from Shared Cloud Infrastructure*, Job Scheduling Strategies for Parallel Processing. Acknowledge CERIT-SC and the Czech National Distributed Infrastructure MetaCentrum, as the publisher requests.
- [Parallel Workloads Archive standard 18-column SWF definitions](https://www.cs.huji.ac.il/labs/parallel/workload/swf.html). Original JSSPP server response may carry a nonsemantic Content-Type; byte contents, not filename/MIME, determine whether the file is SWF text.
- Original RP-E011-D01 ALCF attempt remained `SOURCE_ACCESS_BLOCKED`; it is not scientifically equivalent to a failed predictor, nor is this JSSPP source a retry of its frozen experiment.
