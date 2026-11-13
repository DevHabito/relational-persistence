# NEU-01-G08-D03 — An original raw-labelled BrainVision / preprocessed-labelled EEGLAB pair is numerically identical

**12 November 2026, GitHub runner early 13 November UTC.** This is a **post-result source-audit** for one already examined participant/session/state, not novel mathematics, independent EEG acquisition, human-subject replication or physics. G08-D02's zero projected residual was already known and motivated this separately frozen direct-sample test.

## Why the extra test mattered

Earlier G08-P01 saw all 61 projected channel correlations reported as 1.0. G08-D02 measured zero residual after subtracting each frame's mean over the 61 channels, with a global gain fixed at 1. Correlation and equality after the common-mode projection **do not** prove that the actual original amplitudes are the same: an arbitrary shared value at each frame could be removed by that projection. G08-D03 therefore compared **all 9,150,000 original sample positions directly**, without channel-mean projection, gain fitting, source filtering, time shift, channel reordering or decimal rounding.

The G08-D03 protocol was frozen **alone** at commit **795f3227641e46c972ebcfaf6aedd000c667173e**, after seeing G08-P01 and D02 but before this source experiment. We fixed the only eligible pair: OpenNeuro ds004148 v1.0.0, sub-02 session1 eyesclosed, original 61-channel BrainVision .eeg and corresponding derivative sub02_01_EC.set.

## First exact source result

The first original workflow **#43337338166** at code head **9494ab39da2b4e6635147f5ae019b028968e4491** passed **six synthetic IEEE float32/float64 and adversarial controls BEFORE source access**. It reauthenticated both publisher binaries with the prior source MD5/SHA256 identities. Source BrainVision stored float32; the corresponding derivative MATLAB variable data stored float64/double. Every finite original float32 value can be represented exactly in float64; we applied this widening and nothing else.

We then compared each original widened float64 number against the corresponding native derivative float64 number, including its **canonical IEEE64 bits**, with no tolerance. The result was:

| Registered question | First original source output |
|---|---:|
| Original/derivative aligned positions examined | **9,150,000** |
| Values exactly numerically equal | **9,150,000** |
| Values numerically different | **0** |
| Canonical IEEE64 bit patterns equal | **9,150,000** |
| Canonical IEEE64 bit patterns different | **0** |
| Equal numerics with different IEEE bits, including signed zero | **0** |
| Maximum absolute native numeric difference | **0.0** |
| Source float32-widened canonical float64 SHA256 | e83eba922e8455659a8e477d31e2d76af490125cf1cc4e606e704e842365709f |
| Derivative native canonical float64 SHA256 | e83eba922e8455659a8e477d31e2d76af490125cf1cc4e606e704e842365709f |
| Predeclared +500-frame shift exact numeric matches | **18,659** |
| Predeclared reversed 61-channel order exact numeric matches | **154,674** |

The reversed-channel control inherently leaves the **center channel** in place because 61 is odd; this explains a minimum of 150,000 correspondences in that control, and makes its 154,674 matching count less surprising. It is a sensitivity control only, not a p-value or independence estimate.

**Registered decision:** EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL.

### Scientifically correct interpretation

For precisely **this one** authenticated source pair, the published arrays contain **the same 9,150,000 numbers after exact float32-to-float64 widening**, sample for sample and channel for channel. This is a much stronger data-provenance observation than correlation, equal histograms or equality after reference projection. The files' full bytes are **NOT** identical: one is a 36.6-MB BrainVision multiplexed float32 binary, and one is a 73.8-MB MATLAB EEGLAB container storing double and additional metadata. Their native IEEE samples are identical after the specified representational conversion.

The original BIDS source is labelled **raw**, with EEGReference **FCz**, and channels.tsv declares **uV**, while the EEGLAB derivative sits under a folder described as **pre-processed data** and has metadata ref **common**. The matching arrays show that **these two published versions do not differ in their numerical EEG matrix** despite these labels. They DO NOT establish that neither version was processed earlier, nor that the publisher mislabeled their entire dataset, nor that other states/sessions/subjects share this property. We did not inspect original acquisition and processing history. Intermediate transformations might have been applied before these published files were written, or metadata may reflect software bookkeeping rather than a measured change; their actual chronology is unknown. Do not infer deliberate misconduct, ICA effects, or physiology from this result.

This observation is meaningful for reproducibility: one must not count these two *representations of the same matrix* as independent datasets or treat their raw/derivative labels as evidence of different signal preprocessing without verifying numerical differences. It does not prove a biological signature of relational persistence, neural rigidity, information entropy, clinical diagnosis or a new physical law.

## Source and regression audit

- Original source and frozen G08-D03 protocol commit **795f3227641e46c972ebcfaf6aedd000c667173e**.
- First complete original source workflow https://github.com/DevHabito/relational-persistence/actions/runs/43337338166, source head **9494ab39da2b4e6635147f5ae019b028968e4491**; six pre-source tests passed.
- Source-commit full repository regression https://github.com/DevHabito/relational-persistence/actions/runs/43337338217, **968 passed on Python 3.11 and 968 passed on 3.12** according to actual original job logs.
- First original GitHub Actions result artifact ID **13997791342**. The original aggregate-only audit.json was independently downloaded, extracted and checked at **1,865 bytes SHA256 0a20ff8636afd7c90057fbd852c55864fd6192b9094dc7310680f40557e54e46**, matching its original workflow SHA. It is archived unchanged in docs/results/NEU-01-G08-D03-first-run/audit.json with source chronology and mutation-detecting tests.
- All earlier G03–G08-P01/D02 archives remain unchanged. No binary EEG samples were committed, exposed or retained after execution.

## Literature and next independent verification scope

The source data are by Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (2022, 13 September), Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9. EEGLAB Data Structures explicitly permits saving the EEG struct fields as top-level variables, https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html. BrainVision Core Data Format defines the float32 representation and metadata, https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/. Neither original data nor numeric conversion methods were invented in this repository; no literature-wide priority novelty claim has been established.

A next separately frozen study should compare the **other five** previously selected candidate pairs, still unseen at the derivative-body level, without adapting the original checks or selecting files based on outcomes. Even if those also match, that remains a bounded public-data provenance observation, not generalizable to all 900 pairs without systematic evidence. Conversely, a nonmatching pair would be valuable evidence about **condition/session/source processing heterogeneity**, not proof of a specific operation such as ICA. A separate source-author query may be needed to reconcile their processing pipeline and metadata labels before writing a formal source comment.

**Conclusion: EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL for one source/derivative EEG pair; exact historical processing stage remains unknown.**
