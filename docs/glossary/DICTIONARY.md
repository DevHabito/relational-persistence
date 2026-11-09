# Research dictionary (version 0.1)

Terms must carry units, observation rules, assumptions and identifying limitations. Similar-sounding concepts are not automatically interchangeable.

| Term | Symbol | Type / units in RP-001 | Operational meaning | Important limitation |
|---|---|---|---|---|
| Relational persistence | no canonical symbol | not yet universal | A family's capacity to preserve or recover a declared organization after disturbances | Must specify function and time horizon before measuring |
| Coordination recovery residual | `r_T` | dimensionless | Maximum relative mean-zero disagreement after T no-noise consensus steps | Smaller is better; is not a survival probability |
| Update capacity proxy | `B` | update / step | Fixed one local update cycle per time step | Distinct from physical bytes/sec or operations/sec |
| Noise variance | `I = s²` | square of signal units | Per-node centered, independent disturbance variance | Not Shannon entropy, not uncertainty in general |
| Response latency | `tau` | steps | A single-step response in RP-001 | Fixed to 1; this experiment does not identify delay effects |
| Scalar index | `C` | dependent on proxy conventions | `B/(I*tau)` | Proposed only; not calibrated to outcomes |
| Dynamic coupling | `alpha` | reciprocal of Laplacian scale | Fixed strength of consensus relaxation | Not to be inferred after seeing results |
| Adjacency | `A` | dimensionless for unweighted graph | Presence of a relation | Direction, sign, and edge weights omitted |
| Laplacian | `L` | dimensionless under graph convention | `D - A` | Not a physical spatial Laplacian without a bridge |
| Connectivity | `lambda_2` | dimensionless | Second-smallest eigenvalue of L | Meaningful only for defined L and symmetry assumptions |
| Worst-case contraction | `rho` | dimensionless | Largest absolute non-consensus eigenvalue of W | Model-specific and noise-free outcome |
| Stationary disagreement | `E||Pi*x||²` | square of signal units | Expected total centered square deviation under stationary innovations | Not independent real-world observation here |
| Transition kernel | `K` | probability map | PMFF operation, distinct from declaring W | A particular kernel requires explicit extra assumptions |
| Relational mark | `q` | unspecified | PMFF transition label/score | No physical scale or unique interpretation yet |
| Base structure | `R` | abstract relation | PMFF primitive relation | Not automatically a measured social/network edge |
| Measure | `mu` | unspecified | PMFF weighting/measure structure | Depends on representation and reference measure |
| Occupation measure | `pi` | unspecified | PMFF state/weight measure | Not interchangeable with stationary distribution in every model |
| Observed graph | karate topology | edge set | Zachary's measured club relationships via NetworkX | Hypothetical consensus dynamics are not measured |

## Dimension audit

For the earlier informal use, if `B` is updates/second, `I` dimensionless and `tau` seconds, `B/(I*tau)` has units `seconds^-2`. It is **not dimensionless** merely because of its quotient form. RP-001 fixes a discrete-time numerical convention; cross-domain comparisons need explicit reference scales `(B0,I0,tau0)` or a declared dimensional calibration factor.

## RP-E003 prospective measurement vocabulary

These are **candidate measurement conventions**, not new measurements or
retroactive definitions of RP-001. The METR-LA benchmark did not
identify them.

| RP-E003 candidate term | Proposed instrument and units | What is insufficient |
|---|---|---|
| Calibrated capacity B | Saturated work completions per second in an independent pre-trial run | Sensor count, configured threads, fitted post-recovery throughput |
| External disturbance intensity I | Injector-log excess work units per second, in the same work unit as B | Outcome standard deviation, a fault category, nominal requested rate |
| Measured reaction latency tau | Seconds between an externally logged onset and an independently observed controller action | Sample cadence, nominal programmed delay, actual recovery duration |
| Independently observed recovery Y | Sustained health criterion with right-censoring, evaluated after separately logged intervention end | Computing Y from B, I, tau or post hoc fault labels |
| Clock domain | Common monotonic nanosecond clock, or separately certified synchronization | Subtracting uncorrected wall and monotonic timestamps |
| Stream separation | Calibration, injector, controller and health-monitor data flows kept auditable | Four columns derived from a single outcome series |

Under the RP-E003 illustrative convention, both B and I are rates
(work/second), so B/(I*tau) has dimension inverse second. This differs
from the RP-001 discrete-time variance-like convention: the two
definitions must not be conflated. A dimensionless alternative requires
an independently justified reference timescale and new preregistration.

The structural source gate is implemented at
src/relational_persistence/measurement_gate.py, with synthetic fixtures
in tests/test_measurement_gate.py. Its acceptance is not a physical
measurement validation. See
[RP-E003-S01 source screening](../protocols/RP-E003-S01-SOURCE-SCREENING.md).

## RP-F004 temporal-correlation vocabulary

All entries below describe **dimensionless mathematical model values**,
not new real-world instrumentation.

| Item | Symbol | Definition | Explicit limitation |
|---|---|---|---|
| Binary noise sign stay probability | `p` | `P(eta[t+1]=eta[t] | eta[t])` for a symmetric two-state Markov process | Only `1/2` and `3/4` are allowed by RP-F004 |
| Lag-one noise correlation | `r` | `2p-1` | Not inferable from one-time variance |
| Marginal noise variance | `s²` | `E[eta[t]²]=1/100` with equal ±1/10 marginal probabilities | Not injection rate or Shannon entropy |
| State-noise cross-covariance | `c_t` | `E[x_t eta_t]` | Must not be dropped with colored noise |
| Output second moment | `v_t` | `E[x_t²]`, equal to variance here because mean is zero | Not measured failure rate or survival probability |
| Limiting output variance | `Y(p)` | `lim E[x_t²]`, conditional on stability of the declared recurrence | Not the RP-001 graph residual or RP-E004 recovery time |

The same symbol `I` has different declared operational meanings
across RP-001, RP-E004 and RP-F004. No cross-domain physical inference
is allowed without a new measurement bridge.

## RP-F005 actual discrete feedback-delay vocabulary

| Term | Symbol | Operational mathematical meaning | Scientific limit |
|---|---|---|---|
| Feedback gain | `k` | Gain multiplying the delayed prior state in `x[t+1]=x[t]-k*x[t-d]` | Not a measured control law fitted to actual equipment |
| Feedback delay | `d` | Exact nonnegative integer state lag (0 or 1 in RP-F005) | Different between compared treatments; cannot pretend `tau` is matched |
| Delayed prehistory | `x[-1]` | Additional initial datum mandatory for the `d=1` recurrence | Does not exist as an independent datum for the `d=0` scalar model |
| Augmented delay-one state | `s[t]` | Two-vector `(x[t], x[t-1])` with a `2×2` companion matrix | Not a two-node physical network |
| Six-step squared residual | `Y6` | `x[6]^2/x[0]^2`, initial current state fixed to one | Not continuous-time recovery, probability of survival or variance |
| Uniform strict contraction | `q<1` | Candidate coefficient bounding six-step squared augmented-state energy for every state | Failure at gain one does not imply failure for every gain |

RP-F005 does **not** estimate `B,I,tau`, so the original
proposed quotient `C` must not be evaluated or advertised
as confirmed or falsified by this comparison.

## Versioning

New meanings require a new protocol and documented migration, not retroactive edits to test inputs. A different operationalization can be scientifically legitimate, but it is a different hypothesis until a linking theorem is proved.

## NEU-01-G00 — metadata versus neural signal and theoretical Self

| Term | Bounded operational meaning | Not established by it |
|---|---|---|
| Lempel–Ziv complexity (LZc) | A specified finite-sequence/compression-parsing statistic on **a fixed, binarized and length-controlled EEG signal** | A direct measure of energy, free energy, psychological rigidity or identity |
| Spectral null / phase-randomized surrogate | A synthetic time series designed to retain specified Fourier spectral amplitudes while perturbing phase organization under declared constraints | An independently recorded brain or a complete null for all neural signal structure |
| Dataset source-sidecar disagreement | One original EEG BIDS `*_eeg.json` declares a count different from its companion `*_channels.tsv` row count, at explicitly pinned file revisions | Defective binary signal or evidence that biological channel counts really differ |
| Sensor montage harmonization | Verify identical actual source electrode names, sample units, reference, filtering and available time windows across conditions before comparing EEG measures | Follows automatically from equal numeric channel counts or publisher metadata |
| Original EEG body | Binary EEG sample array and its real channel/header/marker records, separately downloaded and authenticated | Represented by git-annex/symlink listing or a text JSON metadata file |
| Subjective Self continuity | Independently obtained relevant first-person/behavioral continuity or agency measurement, not a generic resting-state EEG condition | EEG LZc, task label or complexity value without independent construct validation |
| Sample/epoch window control | Fixed recording duration, sampling rate, nonoverlapping windowing and artifact rejection rules before outcome inspection | Proof that a LZc contrast has neuronal rather than artefactual cause |

The [NEU-01-G00 audit](../research/NEU-01-G00-LITERATURE-AND-SOURCE-2026-11-09.md) verified one sidecar-only discrepancy among five pinned task records and **did not calculate LZc on EEG recordings**. See Wang et al. (2022), DOI 10.1038/s41597-022-01607-9; Pal et al. (2020), DOI 10.1523/JNEUROSCI.1910-19.2019; Höhn et al. (2024), DOI 10.1523/ENEURO.0259-23.2024. These are established methods and prior source descriptions, not original discoveries here.

## NEU-01-G01 — original BrainVision identity and BIDS-source agreement

| Term | Verified operational meaning | Not established by it |
|---|---|---|
| Original BrainVision header `.vhdr` | Retrieved and authenticated publisher's source header, including `NumberOfChannels`, `SamplingInterval`, binary format and 61 ordered channel names in each of the first two paired resting recordings | A physiologically artifact-free EEG, equivalent processing between tasks or a clinical observation |
| Original BrainVision marker `.vmrk` | Retrieved publisher's annex-key-matched marker object; 151 marker records by source header parse in each task | Mechanism, stimulus or EEG signal interpretation from marker contents; no original marker values published |
| Original BrainVision binary `.eeg` | Genuine 36,600,000-byte tagged publisher source object with pre-registered annex MD5 and freshly measured SHA-256; layout matches 61 × 150,000 × 4-byte float32 | Direct analysis of physiological voltages, amplitude quality or any Lempel–Ziv measure |
| Channel identity agreement | 61 source `[Channel Infos]` names match 61 source `channels.tsv` names in original order for both eyes-open and eyes-closed; all 61 name labels intersect | Equivalent filtering, independent neural generators, exact anatomical location or raw signal homogeneity |
| BIDS JSON 64-channel discrepancy | In sub-01/session1 eyesclosed only, the BIDS `*_eeg.json` count of 64 differs from **authenticated** original 61-channel `.vhdr` and 61-row TSV | A different number of underlying acquired raw sensors, defect in every participant's data or incorrect interpretation of every EEG recording |
| Source integrity gate | Whole-file object MD5/byte-size matching the frozen annex version, whole-file SHA256, strict header/marker format and matching actual source TSV | Verified biological effect, clinical biomarker, thermodynamic entropy or subjective identity |
| Physiological QC gate | A **later** registered and tested source-level process for nonfinite/clipped amplitudes, per-channel variation, artifact handling and task preprocessing | Already satisfied by G01 merely because source bytes are authentic |

First original source evidence and bounds are recorded in [NEU-01-G01](../research/NEU-01-G01-AUTHENTICATED-BRAINVISION-2026-11-09.md). G01 did not calculate EEG LZc or validate the theory of the Self.
