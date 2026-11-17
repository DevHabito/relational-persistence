# NEU-01-G10-P01 — Cross-participant and cross-session native EEG identity audit

**Protocol-only registration: 17 November 2026. No G10 EEG amplitudes or derivative waveform matrices have been read at this registration. No G10 original source workflow or numerical result exists yet.**

## Why this check is warranted

The earlier G08-D03 and G09 audits found exact IEEE64 sample identity, after widening the root BrainVision float32 samples without arithmetic transformation, in six matched OpenNeuro ds004148 v1.0.0 BIDS-root/EEGLAB-derivative pairs: sub-02, sub-03 and sub-04, all in session1, eyesclosed and eyesopen. That finding concerns the published files' numeric representations, not the acquisition-to-publication history or a brain-state effect.

A six-pair result restricted to session1 and three previously examined participants cannot establish whether this representational equivalence extends to later sessions or other participants. The next question is deliberately narrow:

**Do eight fixed root/derivative pairs from two previously unexamined participants and two other sessions preserve exact native numeric identity under the unchanged G08-D03 comparison rule?**

This is a public-file provenance check. It is not an independent human experiment, a random or statistically representative sample, a test of neural persistence, a discovery claim, or a Lempel–Ziv study.

## Chronology and selection disclosure

G10 was designed after the G08/G09 equality results were known. On 17 November 2026, before registering this protocol, I inspected **public GitHub metadata only** at the publisher's pinned source revision for sub-05 and sub-37, sessions 2 and 3, eyesclosed and eyesopen. I confirmed that the corresponding original BIDS directories contain the named `.eeg` symlink pointers and that the eight expected derivative `.set` symlink pointers exist. Their advertised byte lengths and MD5 strings below were visible in those metadata pointers. The selection is **purposive, not random**, and was not selected by comparing any of the eight EEG sample arrays. Earlier files for sub-02–04 were already numerically known; none is eligible as a G10 case.

This document freezes all eight cases and all acceptance/failure rules **before** any G10 EEG binary body, derivative `.set` body or source waveform is retrieved. The protocol freeze does not erase earlier exposure to public filenames, symlinks, article methods, or previous G08/G09 results.

Publisher source: `OpenNeuroDatasets/ds004148`, commit `0c740d838a2c33feeec0b6e514aea323d0e65ca4`, ds004148 v1.0.0. Read that immutable commit, not a moving default branch.

## Fixed eight-pair manifest

Every root path follows `sub-SS/ses-sessionN/eeg/sub-SS_ses-sessionN_task-CONDITION_eeg.eeg`; companion `.vhdr`, `_channels.tsv`, and `_eeg.json` paths use the same fixed subject/session/condition identifiers. Every derivative path follows `derivatives/preprocessed data/preprocessed_data/subSS_0N_STATE.set`, with `EC` for eyesclosed and `EO` for eyesopen.

The two MD5 columns below are **publisher Git-annex pointer claims**, not independently verified hashes of downloaded original or derivative binary bodies. The root `.eeg` pointer claims **36,600,000 bytes** for each case; the derivative `.set` pointer claims **73,824,136 bytes** for each case. Preserve this distinction in all later writing.

| Order | Subject | Session | State | Root .eeg pointer MD5 | Derivative .set pointer MD5 |
|---:|---|---:|---|---|---|
| 1 | sub-05 | 2 | eyesclosed | ac3d71157ac00b3f60dbac2c45e48c91 | b208c7195fc91d9e83c6dbe5db5dfa76 |
| 2 | sub-05 | 2 | eyesopen | 5a612f06d5c25a6f1398b2436038fbcf | f5ae47cd57b5797741585a050c6e60ec |
| 3 | sub-05 | 3 | eyesclosed | 71f9b8aa9dd2e0341a06653c9b7701d4 | a024c145499077c071aa0bc6763bcaee |
| 4 | sub-05 | 3 | eyesopen | 5567489fc66d9449eec4cbf982743ec7 | 772db180b5b4ba833355a8b5acb4e8f0 |
| 5 | sub-37 | 2 | eyesclosed | ecca3e6f5d73da15805837da46efbdf4 | b396eced4f25f43fcbff08406695b749 |
| 6 | sub-37 | 2 | eyesopen | 673a205c350f2f0b2df9357542e36998 | db6fc7bdfa73997886523a94704d0abd |
| 7 | sub-37 | 3 | eyesclosed | eca98d3bbdec4c87ad7514c2ead3c354 | 9f889bde521f4cda35f3b04d2598284d |
| 8 | sub-37 | 3 | eyesopen | a37e9beec644b0962bd36433ad70f06c | 3aaf285adf403e1319dabf83900d3722 |

The same frozen first-pass procedure must be applied in that order to **all eight rows**, whether the early outcomes agree or not. No replacements, selectively omitted rows, new participants or changed sessions are allowed inside G10.

## Predeclared eligibility and source procedure

1. **Archive and lineage gate.** Verify the original G08-D03 and G09 source archives and their documented SHA256 digests and source chronology before G10 source I/O. G09 reports 6/6 exact pairs, but those prior cases must not be recounted as independent G10 observations. Pin the actual G10 implementation commit and workflow run independently. If source lineage cannot be authenticated, halt without a source result.
2. **Pre-source tests.** Execute deterministic, independently specified synthetic/adversarial cases before attempting any of the eight original binary downloads: order/subject/session swaps; altered pointer MD5 and size; refused redirect; truncated response; channel-label permutation; invalid matrix shape or dtype; sample-grid offset; signed-zero numeric equality with changed IEEE bits; nonfinite samples; wrong fixed 500-frame shift; and a known non-identical root/derivative pair. Record failing tests; do not silently weaken gates.
3. **Publisher authentication.** For each row, fetch the exact pinned original source `.eeg` and `.vhdr` publisher objects and the matching pinned Git `_channels.tsv` and `_eeg.json` source metadata. Verify the original full binary's 36,600,000-byte length and advertised MD5; compute a new independent SHA256 for the actual source body. Independently fetch the exact derivative `.set` object, require 73,824,136 bytes and its advertised MD5, and compute its body SHA256. Enforce fixed maximum byte counts, finite HTTP timeouts and a hosted runner job timeout. No mirror substitution, adaptive search, URL fallback or silent redirect. Never confuse an annex pointer's hash with a downloaded file's independently checked hash.
4. **Eligibility before amplitude comparison.** Use the same G08/G09 strict alignment and metadata criteria: exactly 61 unique and identically ordered channels across BrainVision, BIDS channels.tsv and EEGLAB chanlocs; 500Hz; original multiplexed float32 layout of 61x150,000; derivative matrix of 61x150,000 native float64; precisely anchored 2ms relative time steps from 0 to 299,998ms; original `.vhdr` sampling interval 2000 microseconds; EEGLAB fields for 61 channels, 150,000 samples and one trial. Adopt the original G09 numerical tolerances for derivative time representation without search or re-alignment. Nonfinite or malformed data is ineligible unless already covered by the unchanged earlier accepted implementation; record it explicitly. If any gate fails, do **not** compare that pair's EEG amplitude arrays.
5. **Unmodified direct comparison.** For eligible pairs, widen original IEEE float32 values to float64 **without any signal operation**. Compare corresponding root-widened and derivative-native values directly in fixed channel/time order. Record numeric equality count, canonical IEEE64 bit-pattern equality count, maximum native absolute difference, counts of numeric-equal-but-bit-different positions, and separate canonical little-endian float64 SHA256 digests. Zero numeric difference and complete bit equality require all 9,150,000 matched positions per eligible pair. Keep the earlier fixed +500-frame circular temporal-shift and 61-channel reversal checks as negative controls; neither control is used to fit or rescue a mismatch. No projection, regression, gain adjustment, re-reference, per-channel interpolation or delay optimization.
6. **Cleanup and provenance.** Archive only original source identities/hashes, eligibility/status flags, counts, aggregate numerical diagnostics, synthetic-test results and exact software/workflow commits. Do not commit raw EEG amplitude arrays, sample traces or derivative binary objects. Clear original binary contents and temporary downloads after use. Preserve the **first** actual G10 source outcome, including failure logs and its JSON digest; any repaired rerun receives a dated addendum rather than overwriting the original result.

If a future implementation differs materially from G08/G09, document and independently check that difference *before* acquiring original G10 source values. This registration does not claim that such implementation or tests already exist.

## Outcome definitions and interpretation constraints

For each fixed row, assign one of: `SOURCE_UNAVAILABLE_OR_UNAUTHENTICATED`; `SOURCE_METADATA_NOT_ELIGIBLE`; `DIRECT_ARRAYS_IDENTICAL`; `NUMERIC_EQUAL_IEEE_BITS_DIFFER`; `AUTHENTICATED_ARRAYS_DIFFER`. Unexpected processing or test failures receive their own explicit error record and cannot be silently counted as mismatch or success.

The eight-row study status is `G10_EIGHT_PAIR_CENSUS_COMPLETE` **only if all eight source pairs were authenticated, eligible and directly compared**, regardless of whether they matched. Otherwise report `G10_EIGHT_PAIR_ELIGIBILITY_INCOMPLETE` with all row-level reasons. The decision rules are fixed, not revised after the first file.

- If any eligible G10 pair differs, the universal assertion "all examined root/derivative arrays agree" fails for the expanded tested set. Do not assign a biological cause to that discrepancy.
- If all eight pairs agree, report exactly eight further identity matches, spanning two newly selected participants and sessions 2/3, with no claim of dataset-wide identity, no statistically representative sampling inference and **no proof that acquisition-native data escaped preprocessing before the two published files**.
- If some files are unavailable or ineligible, report that limitation without estimating their missing equality results.
- Whether the arrays match or not, this audit **cannot identify the processing history shared before both published representations**, infer source-author intent, measure EEG complexity, estimate physiological recovery or demonstrate relational persistence, identity, psychiatric rigidity or entropy.

The 2022 data descriptor reports different processing for eyes-open EEG, including ICA/ICLabel eye-component removal before sharing. Consequently a BIDS-root `DatasetType: raw` label and a derivative `pre-processed` label are source classifications, not independently verified descriptions of the numeric acquisition lineage. This unresolved provenance must remain explicit.

## Literature and public records

- Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (13 September 2022), *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, *Scientific Data* **9**, article 566, https://doi.org/10.1038/s41597-022-01607-9.
- Original immutable OpenNeuro v1.0.0 source tree: https://github.com/OpenNeuroDatasets/ds004148/tree/0c740d838a2c33feeec0b6e514aea323d0e65ca4
- Prior G09 six-pair audit and its original protocol/result: https://github.com/DevHabito/relational-persistence/pull/99
- EEGLAB Data Structures: https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html
- BrainVision Core Data Format 1.0: https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/

**Registration state:** eight publisher pointer pairs verified as metadata; no G10 waveforms examined, no Python/Lean validation of a G10 source implementation, no new numerical data claim. The next permissible stage is implementation with pre-source adversarial controls, then a single bounded original source run. Separately, a respectful request for acquisition-to-export lineage documentation remains appropriate; its answer is not presumed.
