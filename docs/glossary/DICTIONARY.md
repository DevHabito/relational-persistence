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


## RP-U005-D06 — actual third-party original source-file measurements (8 November 2026)

These are **observations of two precise 2026 ANEEL ZIP files**, identified by original complete compressed SHA-256. They are neither estimates of a fully observed real-world event population nor measures of a physical persistence law.

| Term | Defined observation/unit | Verified by | Limitation |
|---|---|---|---|
| Complete compressed original ZIP identity | Whole byte count and SHA-256 of one official CKAN resource ZIP | Sequential bounded first-party download, exact URL/resource and metadata identity; SHA must equal the D04 first-run value | The file represents the publisher's current 2026 resource revision, not necessarily all 2026 events |
| Complete decoded original CSV | SHA-256 and byte count of all decompressed member bytes | Strict UTF-8 stream and end-to-end ZIP member CRC/EOF, no silently omitted original data row | Format validity is not correctness or completeness of upstream reported incidents |
| Original file row count | Number of non-header CSV data records consumed to member EOF | Streaming CSV parser with strict column width; 6,789,484 occurrences and 6,078,331 interruptions in the two exact 2026 files | Not a count of unique physical events, all active customers or independent randomized observations |
| Required field empty-cell count | Number of literal `""` values in a particular CSV required column | Exact full-source scan, with no imputation or row exclusion | Does not count absent physical events, all missingness sentinels, distinct incomplete records, or missing-at-random processes |
| First source gate versus corrected source gate | D04 permanently rejected CSV instrumentation at a quoted header; D05 diagnosed the alternative delimiter bug; D06 independently retested the same exact ZIP bytes after one predefined correction | Separate frozen protocols, first-run JSON and independent ZIP fingerprints | D06 success **does not retroactively change** D04's negative first verdict; no real repair policy outcome was computed |
| Source schema coverage | Presence of registered ANEEL 2026 column *names* and valid row widths in whole original CSVs | Frozen required field list, CRC/EOF, exact header and row-width validation | No automatic validation of time zones, actual reference-link cardinalities, distribution switch status, repair action or decision-time access |

Primary audited source evidence: [RP-U005-D06 original source report](../results/RP-U005-D06.md). Before any new operational-effect comparison, the incidence key/time joins and field validity require a separately frozen protocol.

## RP-U005-D07 — literal candidate-key eligibility and empty comparison population

The following concepts are source/measurement terms for a **retrospective** ANEEL 2026 *candidate linkage*, not new graph-theoretic or causal observables.

| Term | Meaning | Unlicensed interpretation |
|---|---|---|
| Literal candidate key | Unmodified (14 ASCII-digit distributor CNPJ, literal year 2026, two-digit month 01–12, ASCII 1–10-character original occurrence ID) with a safe separator | Not proof that a matching code means the same physical incident, outage or repair |
| Eligible key row | An original CSV row passing **all** registered syntactic key conditions | Not an observed operational intervention, an accurately reported outage or a valid causal observation |
| Invalid-reason counter | Number of original rows failing a particular syntactic condition, even if the same row fails other conditions | Different reason counts are **not disjoint** and must not be summed as separate observations |
| Distinct matching candidate key | One literal string-key present in both fully audited source tables after validity filters | Not the number of distinct real emergencies, independently restored connections or assigned repair policies |
| Matched source row | One original record whose **valid** candidate key appears in the other source; repeated keys keep their full row multiplicities | Not a one-to-one join, a new outage observation, or evidence of causal effect |
| Empty admissible population | All original rows fail the predeclared key test; both valid-key tables are empty | **Zero key matches do not imply 0% real event correspondence.** A match rate with zero eligible denominator is undefined |

The original [RP-U005-D07](../results/RP-U005-D07.md) audit found zero eligible rows from 6,789,484 occurrence and 6,078,331 interruption records because the strict month representation failed for every row. A later format diagnosis may establish how the source actually spells month values, but it cannot retrospectively alter the first result.

## RP-U005-D08 — unpadded month and occurrence-code lexical representation

These are observations about **exact ANEEL 2026 source snapshot field spellings**, not new graph-theoretic functions or evidence of real incident correspondence.

| Term | Observed/operational meaning | Limit of inference |
|---|---|---|
| Original competence-month spelling | Literal source CSV `NumMesCompetencia` or `MesCompetencia`. The exact D08 originals use unpadded strings `1`–`8` for occurrence files and `1`–`7` for interruption files | A 2-character field-width declaration does **not** mean the source pads `1` to `01`. Do not back-edit the D07 strict `01`–`12` experiment |
| Code length outside dictionary width | Literal source occurrence reference `CodOcorrenciaEmergencial` / `CodOcorrencia` having more than 10 characters, which D07 excluded | Source-dictionary-width discrepancy, **not** proof of an invalid incident, bad event, or unusable full source code |
| Lexical format profile | Aggregated counts of allowlisted month spellings and nonidentifying syntax failure categories after exact original ZIP/CSV CRC/SHA checks | No original identifier, company-level statistic, individual event, verified join, action or policy outcome is exposed |
| Post-result format diagnostic | A separate, explicitly dated source study undertaken **after** D07 reported all keys ineligible | It can explain a previous measurement failure but cannot turn the earlier zero-key result into a successful preregistered event-linkage experiment |

The exact original counts, first-run hashes and historical sequence are recorded in [RP-U005-D08](../results/RP-U005-D08.md) and [its frozen protocol](../protocols/RP-U005-D08-ANEEL-LEXICAL-KEYS.md). Neither study has established a source-to-source actual incident match.

## RP-U005-D09 — parallel literal source key cohorts and multiplicity

These definitions describe **exact-field database correspondence**, not certified physical events or new scientific laws.

| Term | Registered meaning | What must not be inferred |
|---|---|---|
| Cohort S — dictionary width | Four-field literal (CNPJ, year, unpadded month, original code), with source code length 1–10. Longer codes are *ineligible*, not truncated | Does not assert that source codes longer than ten are invalid physical incidents |
| Cohort F — full source code | The same four-field literal key using the complete original code string, including lengths >10 within the original CSV bound | Does not resolve ANEEL dictionary-versus-source code-width mismatch or establish physical identity |
| Matched distinct literal key | Unique four-field string observed in **both** original files; source duplicates collapse only for the *key-count statistic* | Not number of distinct physical emergencies, independent repairs, or correctly paired causal cases |
| Matched original source row | A row with a valid candidate key present in the other file; multiplicities are retained | Not an independent incident or a one-to-one event pairing when a key repeats |
| One-to-many by key | One occurrence source row but multiple interruption source rows sharing a literal key | Not proof that the interruption rows are sequential field actions or that one repair caused multiple restorations |
| Long-code marginal matched cohort | The full F matched-key count minus the S matched-key count; D09 observed 641,058 additional matching **distinct textual keys** | Not proof that F is more accurate, or that more complex repair policy has a benefit |
| Linked-row fraction | Matched eligible source rows divided by **eligible** source rows within a fixed source and key convention | Conditional descriptive denominator, **not** sensitivity, match precision, physical event recovery rate or predictive model accuracy |

Original [RP-U005-D09 results](../results/RP-U005-D09.md) and its [frozen protocol](../protocols/RP-U005-D09-ANEEL-DUAL-KEY-CENSUS.md) preserve complete provenance. Foundational literature: Ivan P. Fellegi and Alan B. Sunter (1969), DOI [10.1080/01621459.1969.10501049](https://doi.org/10.1080/01621459.1969.10501049); Peter Christen (2012), DOI [10.1007/978-3-642-31164-2](https://doi.org/10.1007/978-3-642-31164-2). These precede the present deterministic source-key audit.
