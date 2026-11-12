# NEU-01-G06-P01 — Public source lineage: two distinct EEG collections, six candidate pairs

**12 November 2026.** This is a retrospective public-data metadata audit. It does NOT measure new EEG values or independently replicate a physiological observation. All earlier G03–G05 numeric results were known before designing the G06 audit.

## Verified findings

Upstream dataset: OpenNeuro ds004148 v1.0.0, immutable repository revision 0c740d838a2c33feeec0b6e514aea323d0e65ca4, not a moving branch and not the paper's separately linked version 1.0.1. The original publisher root dataset_description.json labels the dataset as **DatasetType raw**. The six BIDS sidecars for sub-02, sub-03, sub-04, session1, eyesclosed/eyesopen say **EEGReference FCz, SoftwareFilters n/a, EEGChannelCount 61, SamplingFrequency 500**.

The Git tree contains **900 BIDS root BrainVision .eeg entries** and **900 separate derivative EEGLAB .set entries**. The derivative README explicitly calls these files "pre-processed data". Its code directory contains only two entries, **figure6_plotSpectrum.m** and **figure7_topo.m**, described as code for reproducing the two paper figures; an end-to-end EEG preprocessing script is NOT established in that specific public directory. This does not prove no pipeline existed elsewhere or is absent from EEGLAB internal history.

Six exact participant/session/task **candidate filename pairs** were identified in that immutable revision. All six original .eeg Git-annex pointers announce **36,600,000 bytes** and previously independently authenticated G03 MD5 keys. All six derivative .set pointers announce **73,824,136 bytes**, each with distinct public Git-annex MD5. These symlinks are pointers, **not the actual full derivative contents**; G06 did not hash a derivative body.

## Original hosted source audit

The G06 protocol was frozen in a separate standalone commit **4dba6178e2d2092ef15cf0f55f5641996a95896c** after initial exploratory metadata inspection but before G06 executable source review. New software and the GitHub Actions workflow were added at **bee40dbc0431da00bcb0c178988550dc1caaf3cf**. Its first public metadata workflow **#43331670355** passed **11 synthetic/adversarial tests** before network access and then reproduced the exact original pinned upstream tree, blob SHA-1, sidecar values, derivative code inventory and all six Git-annex identity claims.

First original metadata verdict: **NAMED_SOURCE_DERIVATIVE_POINTER_PAIRS_PRESENT**.

G06 independently issued HTTP **HEAD only** to each of the six derivative .set objects hosted by the original OpenNeuro S3 source. **All six returned Content-Length 73,824,136 bytes**, producing the separate feasibility status **SIX_DERIVATIVES_HEAD_SIZE_MATCHED**. This establishes advertised public source-object availability at that moment, not byte-level file integrity, EEG data layout, processing provenance, a known signal transform or sample correspondence.

The source job read **zero original EEG sample values**. All metadata and HEAD results are in the original immutable aggregate-only archive. First successful audit artifact: GitHub Actions id **13994129065**, the extracted **8,826-byte audit.json** has independently checked SHA-256 **0634b51a93e93587e840190a0ab4990e18a585f91e2054c4016815f59915e962**, matching the original job SHA256 log. The initial workflow and output are preserved without rewriting.

## Correction to prior project interpretations

The older G03–G05 work repeatedly described the six BIDS BrainVision EEG recordings as processed originals. **The actual sequence of processing stages applied to those BIDS source files had not been proven.** The paper by Wang et al. (2022) describes EEGLAB 2019_1 re-reference, filtering, interpolation and extra eyes-open ICA. But the upstream Git snapshot clearly distinguishes root files marked raw from a separate derivatives directory marked pre-processed. This makes attribution of the G05 numeric integrality contrast to ICA, re-referencing or filtering **unverified**.

A raw label and the sidecar value SoftwareFilters n/a do **not** prove acquisition-native untouched samples. Conversely, the existence of distinct preprocessed derivative files does **not** prove whether the root BIDS .eeg files underwent earlier conversion or transformation. This correction affects **causal interpretation only**; the previously authenticated exact float32 counts and histogram arithmetic remain as recorded. The mechanism responsible for differing numeric representations remains unidentified.

| Question | G06 evidence status |
|---|---|
| Six name-paired BIDS originals and EEGLAB derivatives | VERIFIED AS PUBLIC GIT POINTERS |
| Six derivative publisher HEAD responses and advertised byte counts | VERIFIED BY HEAD |
| Six full derivative binaries authenticated by their original MD5 | NOT YET |
| Derivative EEGLAB histories, dimensions, channels and sample ordering | NOT YET |
| Exact matching time/sample/channel correspondence | NOT YET |
| Specific processing operation explaining native repetitions/integer values | NOT IDENTIFIED |
| Neural complexity, brain rigidity, entropy or a clinical biomarker | NOT SUPPORTED |

## Traceability and prior literature

- Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei, 13 September 2022, A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, Scientific Data 9:566. DOI https://doi.org/10.1038/s41597-022-01607-9.
- Upstream pinned repository: https://github.com/OpenNeuroDatasets/ds004148/tree/0c740d838a2c33feeec0b6e514aea323d0e65ca4
- Upstream dataset description: https://github.com/OpenNeuroDatasets/ds004148/blob/0c740d838a2c33feeec0b6e514aea323d0e65ca4/dataset_description.json
- Upstream derivative description: https://github.com/OpenNeuroDatasets/ds004148/blob/0c740d838a2c33feeec0b6e514aea323d0e65ca4/derivatives/README
- First G06 source audit: https://github.com/DevHabito/relational-persistence/actions/runs/43331670355
- Immutable original G06 source archive: docs/results/NEU-01-G06-P01-first-run/audit.json, 8,826 bytes, SHA-256 0634b51a93e93587e840190a0ab4990e18a585f91e2054c4016815f59915e962.

Definitions: raw-labelled is a BIDS dataset metadata field, not amplifier-origin certification; derivative-labelled is a separately published preprocessed collection; Git-annex identity is a pointer-level size/MD5 claim; HEAD confirms HTTP-reported object availability only; naming match is not signal alignment; pipeline lineage requires authenticated inputs, operations, parameters and output mapping.

**Next source-first gate:** independently download/authenticate the six derivative .set files or a narrowly registered pilot subset, inspect EEGLAB metadata/history and confirm source-to-derivative sample mapping BEFORE any numeric before/after analysis. No biological inference can yet be made.

**Final G06 decision:** NAMED_SOURCE_DERIVATIVE_POINTER_PAIRS_PRESENT; SIX_DERIVATIVES_HEAD_SIZE_MATCHED; preprocessing_stage_causally_identified=false.
