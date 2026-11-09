# NEU-01-G03 — Prospective cross-subject test of exact digital repetition in original EEG files

**Registered:** 9 November 2026, before decoding or inspecting ANY EEG sample amplitude from the three new participants selected below.  
**Parent:** draft PR #88 at commit `9997c5efddaa5fac99bdc296b2553129aff7b716`, itself stacked on G01 #87 and G00 #86. This new work does not alter the G00/G01/G02 original reports.  
**Dataset:** Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (2022), *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, *Scientific Data* 9:566, DOI [10.1038/s41597-022-01607-9](https://doi.org/10.1038/s41597-022-01607-9). Original OpenNeuro `ds004148`, tag `1.0.0`, published Git revision `0c740d838a2c33feeec0b6e514aea323d0e65ca4`. Official source: `https://s3.amazonaws.com/openneuro.org/ds004148/`.

## 1. What is known, and what remains unknown

The **already-seen** G02 source report, for `sub-01/ses-session1`, counted 195,420 exact within-channel adjacent equal float32 pairs and 23,558 exact zeros with eyes closed, versus 7 adjacent equal pairs and zero exact zeros with eyes open. The authors report additional ICA artifact processing for eyes-open data. Both G02 original BrainVision headers omit explicit physical channel units. These facts motivated G03; they are **not independent discoveries made by G03** and cannot establish brain-state differences, artifact mechanisms, or physical amplitude calibration.

**Bounded question:** does the *direction* of that exact digital-repetition contrast recur in independently selected original files from other participant IDs under the same session/task pairing?

This is a study of **native stored-number representation**, not neuronal complexity, neural rigidity, EEG artifacts, mental health, subjective identity, physical entropy, or causality of ICA. The outcome cannot demonstrate which preprocessing operation generated any repeated values. Published source metadata and the G02 outcome were known before this protocol. This is not a blind, randomly sampled clinical study.

## 2. Frozen selection and authenticated sources

Select the **next three numerically ordered participant IDs after the previously inspected sub-01**: `sub-02`, `sub-03`, and `sub-04`. For each use only `ses-session1` and the complete original `task-eyesclosed` and `task-eyesopen` records. **No substitutions, exclusions or extensions based on digital counts.** This choice was fixed before viewing any new participant EEG samples. No other session/task enters G03.

The Git-annex symlink references below were inspected as **source identity metadata before registration**, not decoded EEG signals. Each expected MD5E key and length derives from the frozen upstream Git revision, and the exact file must pass *both* tests on download. TSVs must match the published Git blob `105960eb0ac14bae43bea73aa479a5c6d995c7a3` and channel lists must agree with original headers, without writing electrode names to reports.

| Participant | Condition | Original `.eeg` MD5 | EEG bytes | Original `.vhdr` MD5 | Header bytes |
|---|---|---|---:|---|---:|
| sub-02 | eyesclosed | `afc315cd4fbd76f2788a67fe31be9d8d` | 36,600,000 | `10a0033fdb6dfd1f72a6e37b8164a269` | 1,122 |
| sub-02 | eyesopen | `3ca243fb3ab6cabcac5a99b8939abcce` | 36,600,000 | `4eb149775baddc320f39fcd4fc6f79c6` | 1,118 |
| sub-03 | eyesclosed | `4ca2b5bab215101621ddf023f31ba042` | 36,600,000 | `98a9f2d1fbffbab2ad2636c05f340531` | 1,122 |
| sub-03 | eyesopen | `099a4fdb6e0e5fe105f04f4c250bc0a4` | 36,600,000 | `ae548d8a0b43dfea2e28d1111d50450c` | 1,118 |
| sub-04 | eyesclosed | `8a7314e14dcaabc117de238ebec6841f` | 36,600,000 | `f79c52b469a3845d70a7877ad18e3e43` | 1,122 |
| sub-04 | eyesopen | `28079903eac38f9f8670a80f0dc766f1` | 36,600,000 | `7d979ba2cfa1a97b092d2782f2138c4b` | 1,118 |

Filename contract: `sub-XX/ses-session1/eeg/sub-XX_ses-session1_task-TASK_eeg.eeg`, corresponding `_eeg.vhdr` and `_channels.tsv`; only official OpenNeuro S3 objects. Independently compute and publish only file SHA-256 hashes and aggregate data counts. Never log EEG samples, full channel lists, behavioral responses or identifying subject records.

## 3. Mandatory source-layout and integrity checks

Fail closed unless each file matches its frozen expected MD5, size and source name; the 61 channels match exactly and in order between header and original BIDS TSV; the BrainVision header specifies binary, multiplexed, IEEE_FLOAT_32, 2,000-microsecond intervals (500 Hz) and exactly 150,000 frames per channel. Retain all 61 channels. The expected source universe is exactly **3 people × 2 conditions × 61 channels × 150,000 native float32 numbers = 54,900,000 values** and **54,899,634 within-channel adjacent pairs**.

Parse all declared header channel resolutions and physical units. Record missing values explicitly, not as assumed `µV`; missing unit alone is not a reason to suppress *native-number* identity counts. An unexpected format, nonfinite values, bytes mismatch, header/TSV disagreement or incomplete download is a **source-integrity stop**, not a negative or positive neurophysiological result. No repair, interpolation, filtering, ICA, re-referencing, sample rescaling, or data replacement is permitted.

## 4. Frozen numerical outcomes and primary decision

For each of the six full original matrices, decode little-endian interleaved float32 shape `(150000,61)` and evaluate:

- `N_zero`: sum of exact numeric `x == 0` over the entire matrix, with denominator 9,150,000 (includes -0.0);
- `N_equal`: sum of exact numeric `x[t,c] == x[t-1,c]` for `t=1..149999` and all 61 channels, denominator 9,149,939, **never across channel boundaries**;
- `N_channels_with_equal`: number of channels with at least one adjacent exact equality; report per-recording median and maximum *counts* of adjacent equalities across the 61 channels, **not individual channel names**;
- `N_finite`, `N_nan`, `N_pos_inf`, `N_neg_inf`, and physical-unit declaration completeness; count all source values, no post-hoc removal.

**Primary outcome:** for each new participant `i`, let `d_i = N_equal(i, eyesclosed)/9149939 - N_equal(i, eyesopen)/9149939`. Report each paired difference and the three exact counts of `d_i>0`, `d_i=0`, and `d_i<0`. **DESCRIPTIVE_DIRECTION_REPLICATED_IN_ALL_THREE** only if all three `d_i>0` and all source guards pass. Otherwise report `DIRECTION_NOT_UNIFORMLY_REPLICATED` with the complete signs, including ties and reversals. If source guards fail, report `SOURCE_NOT_ELIGIBLE`, not either scientific verdict.

**Secondary outcome (not a second independent confirmation):** repeat the paired-sign census for `N_zero/9150000`. Report numerical magnitudes, the 61-channel distribution summaries, and any unexpected discrepancies. Do **not** select channels/windows/participants after reading outcomes, change zero/repeat definitions, introduce a numerical effect threshold after seeing data, or treat all individual float32 values as independent biological replicates.

There is **no confirmatory population-level p-value** or physiological hypothesis test at n=3. Even three positive signs would establish only a repeatable source-file representation pattern in these three selected subjects, not that eyes-closed neural dynamics generate exact repeats. Source processing history (including documented condition-specific ICA) remains confounded.

## 5. Adversarial checks before the original source read

Before fetching any original new-subject EEG body: tests must independently check zero and exact-pair counts against small hand-coded arrays, preservation under within-channel time reversal, correct adjacent boundaries when channels are interleaved, full shape and dtype validation, nonfinite fail-closed, altered hash and truncated source rejection, malformed header failure, and no invented units. Use a separate simple reference counter (no shared vectorized comparison code) on deterministic synthetic fixtures. Exhaust all six original source identities regardless of outcome; a missing file stops the whole result, never leads to a substitute subject.

The first successful original G03 result must be archived with its protocol commit, complete six-object SHA-256 census, source run URL/commit, exact aggregate output checksum and all negative attempts retained. Any source amendment after a blocked run must use a separate dated commit, identify what original signals (if any) were decoded, and never rewrite the primary outcome.

## 6. Literature, interpretation, and next gate

Known earlier work: Wang et al. (2022) describe acquisition and differing source processing; the BrainVision Core Data Format 1.0 describes channel scaling/units; prior EEG Lempel–Ziv and spectral-surrogate papers already address frequency confounds. Exact float32 equality is a software property, **not** an entropy-production measure. This study makes **no novelty claim** about quantitative EEG, graph dynamics, statistical complexity or biological identity.

After G03: investigate source preprocessing and digital-value formation using independently authenticated pipeline provenance, or register a separate **calibrated, spectrally controlled LZc** experiment with held-out participants and explicit null baselines. A positive G03 cannot authorize that jump by itself.

**Chronology:** source pointer metadata and prior G02 findings known; new G03 participant EEG amplitudes NOT read at protocol freeze. Preserve failures and adverse cases. No new Lean theorem is claimed or necessary for these exact finite integer counts.
