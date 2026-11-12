# NEU-01-G06-P01 — Frozen public EEG source-lineage eligibility audit

**12 November 2026.** This is a RETROSPECTIVE public-source metadata audit. All G03–G05 outcomes and an initial exploratory upstream repository tree were inspected BEFORE this protocol. Only the exact executable G06 re-audit and public derivative HEAD feasibility probe are not yet run. This is NOT a blind neurophysiology study, independent EEG acquisition, original processing reconstruction, or new population sampling.

## Motivation: a necessary correction of prior wording

Some older project notes called the six BIDS .eeg original files "already processed originals". That processing stage had NOT been independently established. Upstream OpenNeuro ds004148 v1.0.0 metadata labels its root DatasetType as raw; the six original BIDS sidecars declare EEGReference FCz, SoftwareFilters n/a, EEGChannelCount 61 and SamplingFrequency 500. Separately derivatives/README calls its .set collection "pre-processed data", and says the two MATLAB scripts in derivatives/code reproduce figures 6 and 7. The 2022 paper discusses EEGLAB 2019_1 processing, common average re-reference, FIR filtering, interpolation and extra eyes-open ICA. These facts do NOT establish that the BIDS .eeg bytes have undergone exactly those operations. A BIDS raw label is not proof that amplifier-native bytes were never transformed, and an n/a SoftwareFilters sidecar is not a verified negative audit.

## Fixed source and naming contract

Publisher repository: OpenNeuroDatasets/ds004148; immutable Git commit **0c740d838a2c33feeec0b6e514aea323d0e65ca4**. Repository DOI in description: doi:10.18112/openneuro.ds004148.v1.0.0. Do not silently substitute mutable main or publication-linked version 1.0.1.

Six previously seen pair LABELS (not verified sample-level pairings): participants sub-02, sub-03, sub-04, session1; eyesclosed and eyesopen. Root BIDS BrainVision paths follow sub-XX/ses-session1/eeg/sub-XX_ses-session1_task-TASK_eeg.eeg with task sidecar _eeg.json. Corresponding derivative paths follow derivatives/preprocessed data/preprocessed_data/subXX_01_EC.set or subXX_01_EO.set. Each BIDS .eeg Git-annex pointer is expected to identify a 36,600,000-byte original with exact published MD5 already authenticated by G03. Each derivative .set pointer is expected to identify 73,824,136 bytes and supply its distinct published MD5. This size/name correspondence must not be misreported as aligned physical waveforms.

Before any source requests, run adversarial synthetic tests. Then query exactly the pinned public GitHub tree in recursive mode, fail closed if it is truncated, verify root dataset_description.json, derivatives/README and all six BIDS sidecars with fixed pinned revision. For every pair verify source and derivative tree entry path, type blob, mode 120000, Git-annex symlink text and frozen MD5/byte size. Count all derivative files with extension .set, and inventory all paths inside derivatives/code. The exploratory tree contained exactly 900 .set pointers and two figure-plot .m scripts; G06 is an executable audit of that frozen known observation, not an unseen prediction. A pointer is NOT the corresponding original .set byte stream; a missing upstream preprocessing script in derivatives/code does NOT prove one never existed elsewhere or is absent in EEG history.

## HEAD-only bounded derivative-access feasibility

For each six derivative .set publisher object URLs at https://s3.amazonaws.com/openneuro.org/ds004148/, issue HEAD with a 45-second request timeout and NO following redirects outside that exact publisher root, and never GET any EEG content. If Content-Length matches the expected 73,824,136 bytes, record DERIVATIVE_HEAD_SIZE_MATCH. Otherwise record DERIVATIVE_HEAD_NOT_VERIFIED or DERIVATIVE_HEAD_SIZE_MISMATCH, never assume an unreachable file does not exist. HEAD and ETag never establish sample authenticity, acquisition history, decoded layout or numerical matching. No alternate URL hunt, source replacement, channel names, sample values, or raw amplitude archiving is permitted.

## Frozen decisions and invariant limits

The top-level metadata verdict is NAMED_SOURCE_DERIVATIVE_POINTER_PAIRS_PRESENT only if all six pointers and sidecars, root labels and the complete published tree pass source metadata guards. Any source mismatch is UPSTREAM_METADATA_NOT_ELIGIBLE with the earliest exact failing field, no relaxed rules. Separately record SIX_DERIVATIVES_HEAD_SIZE_MATCHED only if all six HEAD requests verify the expected byte count; else SOME_DERIVATIVE_OBJECTS_UNVERIFIED with per-file HEAD reason. Keep both labels separate.

PREPROCESSING_STAGE_CAUSALLY_IDENTIFIED is permanently false for G06, and both NUMERIC_SAMPLE_ALIGNMENT_VERIFIED and DERIVATIVE_BODY_MD5_VERIFIED are also false. Merely finding six filenames and reachable files cannot prove matched before/after sample values, an ICA effect, identical channel definitions or real neural complexity. Even successful future raw/derivative comparisons isolate at most a composite pipeline unless the individual operations and parameters are documented and intervenable.

If metadata audit fails, no positive feasibility conclusion. Preserve first attempt and exact aggregate-only JSON, SHA-256, source commit and workflow evidence. Add any postfailure corrections in a separate dated addendum without changing the earlier protocol or recorded outcome.

## Sources, dictionary and prospective next gate

- Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei, 13 September 2022, A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, Scientific Data 9:566; DOI https://doi.org/10.1038/s41597-022-01607-9. The paper mentions OpenNeuro 1.0.1; we use pinned 1.0.0.
- OpenNeuroDatasets/ds004148, Git 0c740d838a2c33feeec0b6e514aea323d0e65ca4, root dataset_description.json, original BIDS sidecars and derivatives/README, public license CC0.
- Brain Products GmbH, BrainVision Core Data Format 1.0, representation and header metadata reference.

Dictionary: raw-labelled means marked raw by the BIDS dataset, not verified untreated amplifier samples; derivative-labelled means located in the pre-processed data directory, not a known one-operation transform; git-annex pointer means a symlink announcing size and MD5, not downloaded authenticated bytes; matched labels means corresponding subject/session/task filenames without proven numerical alignment; derivative HEAD means response metadata only, not content authentication; processing provenance means verified source-to-output mapping, code version, parameters, and source identity.

**Next falsifiable gate after G06:** if derivative bytes can be authenticated, inspect the six EEGLAB .set metadata structures and processing history under a separately frozen protocol, without making any neural inference. If lineage fails, explicitly mark the source-to-derivative comparison not identifiable.
