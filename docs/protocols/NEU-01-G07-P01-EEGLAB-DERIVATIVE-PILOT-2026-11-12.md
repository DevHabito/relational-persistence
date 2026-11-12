# NEU-01-G07-P01 — Authenticate a single original EEGLAB derivative and inspect metadata only

**12 November 2026. Frozen before any G07 derivative body download.** G03–G06 outcomes, G06 HEAD availability, Git-annex MD5 pointer and exact byte length were already known. This is an unblinded SAME-DATA digital provenance pilot, not new participant evidence, a matched-sample analysis, physiology, or a discovered processing cause.

## One fixed candidate: no substitutions or expansion after seeing results

Original OpenNeuro ds004148 v1.0.0 pinned Git revision 0c740d838a2c33feeec0b6e514aea323d0e65ca4. Use precisely ONE original EEGLAB derivative object:

derivatives/preprocessed data/preprocessed_data/sub02_01_EC.set

Its published Git-annex pointer announces **73,824,136 bytes**, MD5 **2ba3c01f752799634414e2142544fd9b**. Original official source: https://s3.amazonaws.com/openneuro.org/ds004148/ followed by this path with spaces URL-encoded. No fallback host, no new participants, no state chosen based on source content. The associated previously verified root BIDS-labelled raw object is sub-02 session1 eyesclosed, BrainVision .eeg, 36,600,000 bytes and published MD5 afc315cd4fbd76f2788a67fe31be9d8d. G07 does NOT download or decode the root .eeg again.

## Frozen outcomes and guards

1. Before derivative network access, pass independent synthetic/adversarial tests for a valid small MATLAB v5 EEG struct, invalid hash/size, unsupported format, non-finite or missing metadata fields, invalid URLs and zero signal upload. A locked original source-object path and a no-follow-redirect rule protect source identity. Download the one publisher .set with a hard 73,824,136-byte bound to a temporary hosted runner file, computing full-file MD5 and SHA-256 while streaming. **Never report or retain source signal numbers, channel names, participant covariates, absolute sample timestamps or private processing-history text.**
2. Fail closed on download failure, wrong size or wrong MD5. Report SOURCE_NOT_ELIGIBLE, not a negative finding about the dataset or brain. If successful, report verified exact **SHA-256** for derivative bytes (new technical outcome) and the actual recognized MATLAB container family (MATLAB v5, MATLAB v7.3/HDF5, unknown). The source format must not be guessed before opening it.
3. If MATLAB v5 is detected, use SciPy to load only the EEGLAB EEG variable into temporary memory and report **only** metadata: whether it is a struct, the scalar numerical values nbchan, pnts, trials and srate when present and finite, sanitized short reference label, EEG.data shape and dtype, whether EEG.history is present, its text length and SHA-256 when safely extractable. DO NOT publish raw EEG history or any sampled/aggregate EEG amplitudes. If MATLAB v7.3/HDF5 or otherwise unsupported, classify FORMAT_NOT_PARSED; do not coerce.
4. Valid original bytes with a structurally parsed EEGLAB record yield DERIVATIVE_BYTES_AUTHENTICATED_METADATA_PARSED. Valid bytes with unsupported/unparseable struct yield DERIVATIVE_BYTES_AUTHENTICATED_METADATA_NOT_PARSED, preserving the software failure as a limitation. Neither establishes exact sample alignment, history reliability or stage-specific causal attribution. A float32-vs-double classification alone cannot explain the previously observed integrality contrast.
5. Successful hash authentication of this one derivative is NOT a successful census of the other five .set files. Never selectively replace the pilot or generalize across participants.

## Provenance and interpretation

The publisher paper Wang, Yulin; Duan, Wei; Dong, Debo; Ding, Lihong; Lei, Xu (13 September 2022), A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9, documents EEGLAB 2019_1 processing including distinct eyesopen ICA. Our selected eyesclosed pilot does not estimate an ICA difference. G06 established that upstream BIDS root is labelled raw and derivatives are separately labelled preprocessed, not that the original samples are acquisition-native or derivative processing is attributable to one operation.

An authenticated EEGLAB binary with matching names, rates or dimensions is not a verified matched before/after waveform. The required later independent experiment must prove channel, sample/time and content alignment, and separate preprocessing effects only with true intervention or authenticated full history. No Lean theorem, LZ complexity, physical entropy, brain rigidity, or mental-health inference is permitted.

Freeze this protocol ALONE before code, tests, first source run and original SHA archive. Preserve failures and correct errors via separate dated addenda without erasing earlier source outcomes. Record only aggregate-safe metadata and the original GitHub Actions run ID and SHA-256.

Dictionary: derivative bytes authenticated means full publisher file passes size/MD5; MAT container type is header classification, not EEG semantics; EEG.history hash attests available text identity without exposing it; candidate pair means matching publisher naming, not numerical sample pairing. **G07 is a technical object-integrity and metadata pilot only.**
