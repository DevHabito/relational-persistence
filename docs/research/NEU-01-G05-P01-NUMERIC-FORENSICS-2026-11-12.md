# NEU-01-G05-P01 — Exact float32 repetition runs and native integer occupancy

**12 November 2026 · Original same-source technical measurement · No neural/clinical or physical-entropy claims**

## Why I ran this

G04 made the nonzero-equality contrast exact, but I could not yet say whether it involved long repeated plateaus or brief pairs, or whether all repetitions were simply native integer codes. I registered G05 to measure those two numeric questions without observing any new participants and without selecting run lengths after seeing them. This is a post-G04 question, not a blinded human experiment. The existing G04 totals and source-preparation differences were known.

The G05 protocol was committed **alone** at 1702cbb602d35efe8a4bc3cdc484f2ad2e5f9f7a, ahead of G05 code and source access. The original source workflow #43329558431 at 4fcc04c7aa4e786c823f7ac7d7d33d490786c3b4 passed seven dedicated synthetic/adversarial tests before any original EEG download, authenticated all six original OpenNeuro ds004148 v1.0.0 files, and analyzed the full 54.9 million decoded float32 values. The observed G05 outcome was **G05_EXACT_SOURCE_CENSUS_COMPLETE**, with every prior G04 original count and SHA-256 matching exactly. No failed first source attempt occurred in G05.

## What was counted

For every original channel, I partitioned 150,000 time-ordered numbers into maximal equal-valued runs under float32 numerical equality. Zeros (including signed zero) and nonzero values were kept separately; no run lengths were silently dropped. A constant-value run of k samples yields k-1 adjacent equal pairs. I separately counted the native values that are **exact integers** and the exact equal nonzero pairs whose value is an integer in the native uncalibrated scale.

All six original files were previously examined, three participants (sub-02, sub-03, sub-04) x eyesclosed and eyesopen, session1. This analysis uses the already verified G04 source retrieval, so it is **not a third independently implemented source acquisition**. Its run-counting algorithm is new and passed independently coded synthetic reference loops.

## Result 1 — Integer-valued native float32 occupancy

| Source | Eyesclosed integer nonzero samples / nonzero samples | Eyesopen integer nonzero samples / nonzero samples | Eyesclosed integer nonzero equal pairs / all equal nonzero pairs | Eyesopen integer nonzero equal pairs |
|---|---:|---:|---:|---:|
| sub-02 | 912,943 / 9,144,077 | 60 / 9,150,000 | 13,008 / 130,304 | 0 / 9 |
| sub-03 | 909,053 / 9,138,839 | 38 / 9,150,000 | 14,972 / 152,365 | 0 / 3 |
| sub-04 | 906,988 / 9,134,682 | 47 / 9,150,000 | 17,311 / 174,967 | 0 / 12 |
| **All three (descriptive sum only)** | **2,728,984 / 27,417,598** | **145 / 27,450,000** | **45,291 / 457,636** | **0 / 24** |

The closed-recording native exact-integer occupancy is **9.9534%** among nonzero values, versus **0.0005282%** of nonzero values in the selected eyes-open files. The contrast is large **in the numeric representations**. It does not identify the step or process that generated it, particularly because the original published dataset has different eyes-closed/eyes-open processing and the source headers omit physical channel units.

A useful control is internal to this same descriptive census: **9.8967%** of the eyesclosed *equal nonzero pair events* occur at integral native values, close to the **9.9534%** integral occupancy among all eyesclosed nonzero samples. Merely finding many integer-valued equal pairs is therefore not evidence that equal pairs are unusually enriched at integers. These percentages describe different denominators and are not independently sampled statistical estimates; no significance test was preregistered or run.

## Result 2 — Complete repeated nonzero-run lengths

Run length means consecutive **samples** with precisely equal nonzero numbers, inside the same channel. Each run of length k contributes k-1 equal adjacent pair events.

| Nonzero repeated run length | sub-02 closed | sub-03 closed | sub-04 closed | Total closed | Total open |
|---|---:|---:|---:|---:|---:|
| 2 | 125,230 | 145,450 | 165,853 | **436,533** | **24** |
| 3 | 2,456 | 3,306 | 4,333 | **10,095** | 0 |
| 4 | 50 | 97 | 140 | **287** | 0 |
| 5 | 3 | 3 | 7 | **13** | 0 |
| Other lengths >=2 | 0 | 0 | 0 | **0** | **0** |

Exact conservation: **436,533 + 2(10,095) + 3(287) + 4(13) = 457,636 nonzero equal pairs**, matching G04. The three eyesopen files show only 24 nonzero runs of length 2 and none longer. The closed-source maximum equal-nonzero run length was 5 original samples (at 500 Hz, a duration covering four intersample intervals, or 8 milliseconds between first and last observations), but this is a numerical plateau in processed data, **not** a neural persistence time or biological latency.

The full original zero-run histograms are retained in the original audit JSON rather than reduced to a selected bin. As another conservation check, the source run histograms reconstruct every one of the 1,258 previously verified zero-zero adjacent pairs.

## What this really establishes

- An unusually large **conditional numeric-encoding contrast** exists between the previously processed eyesclosed and eyesopen files; the fraction of numbers exactly integral on the native stored scale differs greatly.
- Repetition on eyesclosed is mostly **short nonzero plateaus**, primarily length-two runs, not long constant stretches. The G04 counts are reproduced by an independent run-boundary algorithm and its full histograms.
- The source-level pattern is consistent with multiple possible transformations, including finite-precision processing, rounding, quantization and interpolation. **No single mechanism has been established.** The source conditions differ in preprocessing; the publisher explicitly reports additional ICA for eyesopen. The no-unit metadata still prevents a calibrated-voltage claim.
- Native integrality is **not invariant under changing numerical units or scaling**, and all floating-point numbers are finitely represented. The term 'quantization evidence' would overstate this source-only test. It also cannot be interpreted as neural complexity, consciousness, mental health, or a biological rigidity biomarker.

The exact finite-sample run identities are elementary arithmetic, not new mathematics. I do not claim novelty of counting float32 integers or value runs. The project-specific contribution is an immutable, auditable **numerical source characterization** of this selected set with explicit negative biological claims.

## Prior research and attribution

- **Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei, 13 September 2022**, “A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states,” Scientific Data 9:566, DOI https://doi.org/10.1038/s41597-022-01607-9. This paper documents common-average re-reference, 0.3–45 Hz filtering, linear interpolation, manual epoch checks and additional eyes-open ICA. These steps could alter numeric properties; their causal effect on our specific counts is **unmeasured**.
- **Brain Products GmbH**, BrainVision Core Data Format 1.0, https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/. Technical record-layout and scaling reference; the original six recordings did not identify explicit physical sample units.
- **Project chronology:** G03 original source repetition, G04 separately decoded source equality and the G05 prospective *numerical diagnostic* protocol are separate scoped results. G05 must not be marketed as new human replication.

## Original source audit and verification

The first source output was uploaded as GitHub Actions artifact **13993594220**, then independently downloaded and checked. Original audit.json length **8,559 bytes**, SHA-256 **9dbf40942373aa5ec3fa9f7959b4442b9da96003c01090f76d5a4507639a21d4**, matching the first workflow's logged digest. The untouched JSON is stored in docs/results/NEU-01-G05-P01-first-run/audit.json, with a separately authored archival index. No EEG signal values, individual channel outputs or person-level covariates were archived.

- Protocol-only commit: **1702cbb602d35efe8a4bc3cdc484f2ad2e5f9f7a**
- Source implementation and original first run head: **4fcc04c7aa4e786c823f7ac7d7d33d490786c3b4**
- First actual G05 source workflow: https://github.com/DevHabito/relational-persistence/actions/runs/43329558431; original synthetic checks 7 passed before source access; source result complete
- Full existing regression at original G05 head: https://github.com/DevHabito/relational-persistence/actions/runs/43329558203; **895 tests passed on each Python 3.11 and 3.12**, per inspected logs
- Immutable original archived aggregate: docs/results/NEU-01-G05-P01-first-run/audit.json
- Retrospective archive-index provenance: docs/results/NEU-01-G05-P01-first-run/archive-index.json

## Next independent scientific gate

The data now compel a source-lineage question rather than more arbitrary formula fitting: **do the publishers retain clearly attributable pre-ICA or pre-interpolation material (and runnable version-pinned processing scripts) for these exact tasks?** A separate G06 source/derivative eligibility audit should first distinguish which copies represent original amplified samples, which copies are processed, and whether matched pre/post comparisons are legally, technically and statistically identifiable.

If this cannot be established, label the processing mechanism **not identified** and do not proceed to a physiological Lempel-Ziv interpretation. Nothing in G05 validates the overarching relational-persistence conjecture or any clinical model.

**Recorded G05 decision: G05_EXACT_SOURCE_CENSUS_COMPLETE, native numeric source characterization only.**
