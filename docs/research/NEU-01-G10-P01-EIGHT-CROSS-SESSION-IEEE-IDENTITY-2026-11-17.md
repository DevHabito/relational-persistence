# NEU-01-G10-P01 — Eight published EEG source/derivative pairs match exactly across later sessions

**17 November 2026.** This is an authenticated public-file provenance result. It is not an independent human acquisition, a measurement of neural persistence or a law about living systems.

## Why G10 was needed

The G08-D03/G09 result concerned six matched BIDS-root and EEGLAB-derivative records from three previously examined participants, all in session1. That did not tell us whether the exact numeric correspondence was confined to those records. On 17 November, after that result was known, I inspected **only GitHub pointer metadata** for another two participants, sub-05 and sub-37, at sessions 2 and 3 under both rest conditions. The eight pairs were purposively chosen, not randomized, and their file paths and advertised MD5 identifiers were frozen in the **protocol-only commit `9375cb3ccece0a431c136257f0feb43bd43721ab`** before any of the eight G10 source waveforms was downloaded.

G10 then added synthetic-only tests in commit `a00bf30da7be0040fd6073212637b0c210be7f65`. The separate original-data implementation was committed at `b4feb85a628fdeee81089877a376ba2964c2b7be`, with an Actions workflow requiring adversarial tests **before** any G10 source I/O. We did not rewrite the frozen study question, relax the 61-channel/fixed-grid rules or select additional candidates after seeing the comparison.

## Original first-source result

The **first G10 source run** [#44058156465](https://github.com/DevHabito/relational-persistence/actions/runs/44058156465) passed 32 targeted pre-source synthetic/adversarial pytest controls and then directly evaluated all eight frozen publisher pairs. Original BIDS .eeg binary objects, their corresponding .vhdr headers, original publisher channels TSV/JSON metadata and EEGLAB derivatives were authenticated against frozen publisher MD5 or pinned Git blob SHA1 identities, with independently computed full-source SHA256 records. The direct comparison followed the original G08-D03 IEEE criterion: original little-endian float32 sample values widened to float64 without signal processing, aligned with native float64 EEGLAB values in the fixed 61-channel × 150,000-sample grid, with no gain adjustment, re-referencing, lag fitting, channel matching search or other rescue transformation.

The first result is **`G10_EIGHT_PAIR_CENSUS_COMPLETE`**, with **eight of eight numerically and IEEE64-bit-identical** source/derivative matrices and zero unequal positions. Each pair contributed exactly 9,150,000 compared positions; all eight contributed **73,200,000 exact numerical and bit-pattern equalities**. Both canonical per-pair little-endian float64 SHA256 hashes agreed within every pair. The fixed one-second circular-shift and channel-reversal controls were computed, not optimized.

| Fixed pair | Original source body | Metadata alignment | Equal numeric/IEEE64 positions | Unequal IEEE64 positions |
|---|---|---|---:|---:|
| sub-05 / session2 / eyesclosed | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-05 / session2 / eyesopen | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-05 / session3 / eyesclosed | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-05 / session3 / eyesopen | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-37 / session2 / eyesclosed | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-37 / session2 / eyesopen | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-37 / session3 / eyesclosed | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |
| sub-37 / session3 / eyesopen | Publisher MD5 verified | Eligible | 9,150,000 / 9,150,000 | 0 |

This extends a strictly file-level audit from **6 pairs (G08/G09) to 14 distinct published pairs (G08/G09/G10)** across five selected participants and three session indices, though G10 has no session1 observations. These 14 pairs are **not 14 independent newly recorded people**; there are multiple conditions and sessions from repeated participants, and the numbers within each recording are strongly dependent.

## A separate metadata inconsistency, retained rather than repaired

The pinned BIDS `_eeg.json` sidecars for **sub-37/session2/eyesclosed** and **sub-37/session2/eyesopen** report `EEGChannelCount=60` and `MiscChannelCount=1`. Their fixed `channels.tsv` files identify **61 rows of type EEG**. Both original BrainVision headers and corresponding EEGLAB channel lists passed the previously fixed 61-channel numeric alignment gate; the direct 9,150,000-value identity therefore remains well-defined for those published arrays. The JSON-versus-TSV **classification disagreement was kept as a separate, explicit flag in the original G10 archive**. It was not changed, overwritten, treated as a discovered physiological effect, or silently used to exclude those pairs.

The cause of this metadata classification mismatch is **not known**. The publisher's article describes acquisition with either a 63- or 64-electrode cap and some reconstructed channels; that background does not uniquely explain this exact sub-37/session2 classification. A new source-to-export lineage audit would be needed to establish the actual origin.

## Exact evidence, validation and chronology

- Frozen G10 protocol: `docs/protocols/NEU-01-G10-P01-CROSS-SESSION-NATIVE-IDENTITY-2026-11-17.md`, protocol-only commit `9375cb3ccece0a431c136257f0feb43bd43721ab`.
- First complete source implementation: `b4feb85a628fdeee81089877a376ba2964c2b7be`. It uses no network during import or synthetic tests and reads binary source samples only after the earlier-source archives and fixed publisher metadata are authenticated.
- First original source workflow: https://github.com/DevHabito/relational-persistence/actions/runs/44058156465; pre-source adversarial tests **32 passed**. Archive upload: artifact **14316762957**, `neu01-g10-eight-pairs-first-original-aggregate-only`.
- Full source-commit regression: https://github.com/DevHabito/relational-persistence/actions/runs/44058154533, original logs **1,002 passing tests on Python 3.11 and 1,002 on Python 3.12**. These are software tests; the eight-source result comes separately from the G10 original workflow.
- Untouched first source `audit.json`: **36,006 bytes**; original workflow SHA256 **`5d7c239260da9d9d65cda652c617fdfe906affdff88f85be1a829877f49568c5`**. The original Actions artifact was independently downloaded; its extracted JSON had the same 36,006-byte size and SHA256. The contents archived here are reconstructed from the original job's JSON stdout, byte-length cross-checked against that downloaded original and checked against the published original digest; no amplitudes are included. See `docs/results/NEU-01-G10-P01-first-run/archive-index.json`.

The source format descriptions are not themselves proof of where or when preprocessing took place. The BIDS-root files are labelled `raw` and the EEGLAB directory `pre-processed`, but **all fourteen examined source/derivative pairs are numerically identical after direct format widening**. This means these specific pairs cannot support an explanation that relies on a numerical difference introduced *between* the two published representations. It does not show that either file is acquisition-native, or that the 2022 paper's eye-open ICA, interpolation, re-referencing, filtering and export steps were or were not performed earlier on a common ancestral signal. The study is **purposive and retrospective**, not blind dataset-wide sampling; 886 of the 900 pointer pairs remain outside the 14 directly examined pairs.

No result in this audit directly measures Lempel–Ziv complexity, entropy, physiological recovery, neural rigidity, clinical disease, persistence of self or relational persistence. Nor does an exact digital provenance finding prove or disprove the framework's broader mathematical claims.

## Next scientific gate

Preserve this first-source outcome as the fixed reference and **do not rerun G10 selectively**. A targeted respectful request to the dataset maintainers for acquisition-to-published-BIDS/EEGLAB lineage would be more informative than speculating about ICA causality. For actual relational-persistence research, the next study needs predefined organization-level observables, independent perturbation or repeat-test designs, measurement invariance checks and null models that cannot be passed merely because two public files contain the same samples.

## Attribution and sources

- Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (2022, 13 September), *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, **Scientific Data 9**, article 566. https://doi.org/10.1038/s41597-022-01607-9
- Original publisher source revision: https://github.com/OpenNeuroDatasets/ds004148/tree/0c740d838a2c33feeec0b6e514aea323d0e65ca4
- Original G10 first workflow and source evidence: https://github.com/DevHabito/relational-persistence/actions/runs/44058156465
- Earlier G09 source/derivative audit and its limitations: https://github.com/DevHabito/relational-persistence/pull/99
