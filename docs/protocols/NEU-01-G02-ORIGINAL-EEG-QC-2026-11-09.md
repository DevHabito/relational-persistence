# NEU-01-G02 — Pre-registered within-recording EEG sample integrity and epoch QC

**Registered:** 9 November 2026, **before reading original EEG sample values** in G02.  
**Parent:** draft G01 source-identity PR #87 at `e0ae41d78fdbf6c4e434a820e81d47f21c50fa89`, stacked without modifying G01 first-run evidence.  
**Scope:** original OpenNeuro ds004148 `1.0.0`, git `0c740d838a2c33feeec0b6e514aea323d0e65ca4`, subject `sub-01`, `ses-session1`, paired `eyesclosed` and `eyesopen` recordings. **Source selection was already informed by G00/G01; this is a source-amplitude first-run check, not an independent participant sample or original statistical discovery.**

## Motivating scientific boundary

Question: are the *unfiltered decoded original* samples and basic epochwise signal properties valid for further controlled analysis of Lempel–Ziv complexity? An EEG complexity contrast is **not** computed at this stage. We do not assert a measure of the Self, mental health, entropy production, biological flexibility or clinical diagnostic performance.

**Publisher prior art:** Wang, Duan, Dong, Ding and Lei (2022), `A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states`, *Scientific Data* 9:566, DOI `10.1038/s41597-022-01607-9`, documents channel reconstruction, average-reference processing, 4-second epoch screening, and an **additional ICA procedure for eyes-open data**, with on average 0.978 ± 0.146 removed components/session. Consequently, raw source records cannot be assumed to have the same processing history merely because channels, sample rate and duration match. The G02 QC is not a replacement for source authors' artifact methods.

**BrainVision prior art:** [BrainVision Core Data Format 1.0](https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/) and the publisher specification for `[Channel Infos]` resolution and units. Numerical raw float32 samples alone do not establish physical units, actual amplifier saturation thresholds, or independent neural generators.

## Exact authenticated source objects and source strategy

**Only publisher official source:** `https://s3.amazonaws.com/openneuro.org/ds004148/sub-01/ses-session1/eeg/`.

For `eyesclosed`, require source `.eeg` **36,600,000 bytes**, git-annex MD5 `0fceeb9eb4163b86b815061f8fff80d7`, *independently SHA-pinned in first G01 hosted source run* `022b9f34914e4314f4d9e45d17bc367031c9d9d879ea983a8d6eb43f7affbc47`; exact source `.vhdr` **1,122 bytes**, MD5 `c5e313903936ef2fb9c1b3e0bfd61593`, SHA-256 `b3f437f5e1cc95b3dbedb989d9c637c832ae4406b55782f8c8aeeb2fefc96061`.

For `eyesopen`, require source `.eeg` **36,600,000 bytes**, MD5 `75e12c6499540e3148316ef502ad03dd`, SHA-256 `d4c9357b8996fa8e989317d9c945b8e71adfe9e3564c96812689c9cf29e09ac9`; exact `.vhdr` **1,118 bytes**, MD5 `a5f9899c3cfa0c85f24c93c4eb83ef4c`, SHA-256 `7a02a0d6d25413ebc1600a737f2d30f33fc4fc608b25c03564f5918463c3845f`.

These six identity checks were completed in G01, and no G02 original sample may be accepted unless the corresponding current `.eeg/.vhdr` bytes match **both** source MD5/size and independent G01 SHA-256. Original marker objects and TSVs were authenticated in G01; only `.eeg` + `.vhdr` content is required for this independent sample-integrity gate. **Do not substitute NEMAR/Zarr or locally regenerated data.**

The original header must independently parse as exactly **61 channels, 500 Hz, multiplexed little-endian IEEE_FLOAT_32, 150,000 frames/channel and 300 seconds**; source headers/TSV channel-name equality was already demonstrated in G01. Verify again the source header's `[Channel Infos]` ordinal contiguity and inspect its declared `resolution` and `unit` for **all 61 channels**; report **only aggregated distributions/counts of unit/resolution declarations**, no electrode labels or individual values.

Streaming retrieval buffers at most 1 MiB for each object into a short-lived temporary directory. Each EEG binary must remain under 40 MiB with its strict exact length and hashes, including SHA-256 from first G01. Read it as little-endian `<f4`, memmapped in shape `(150000, 61)`, **without re-referencing, filtering, ICA, scaling or replacing invalid samples**. Do not print, archive, upload or commit any voltage values, marker content or individualized channel names; only task-level aggregate counts and bounded numerical summaries.

## Frozen metrics and denominator conservation

**Mandatory all 61 channels, both tasks; no selection from observed result.** Inspect the entire **150,000 × 61 = 9,150,000 values per task** and **18,300,000 total**, not a convenience initial snippet. All 61 channels must be retained in the QC denominator, even if an entire channel is invalid.

1. `nan_count`, `positive_infinity_count`, `negative_infinity_count`, `finite_count` as exact integers (total must equal 9,150,000 for each original task). `exact_zero_count` (not automatically an error), `exact_adjacent_equal_count` across 61×149,999 within-channel time transitions (not automatically an error). Count `channels_with_any_nonfinite` and `channels_fully_finite`.
2. **Epoch size:** exactly **10 seconds = 5,000 samples** per 500-Hz channel. Non-overlapping 30 whole epochs per task × 61 channels = **1,830 channel-epochs** per task. Count `channel_epochs_with_nonfinite`, `channel_epochs_exactly_constant` (only when all 5,000 samples are finite and max==min), `channels_constant_entire_recording`, `channels_with_at_least_one_constant_epoch`, `channels_with_any_nonfinite`. No visual/manual epoch dropping and no imputation. A strictly non-finite channel-epoch is excluded only from amplitude summary, not denominator.
3. For each fully finite channel-epoch, define **native-stored-value peak-to-peak** `PTP=max-min`, finite-sample standard deviation `std` and RMS `sqrt(mean(x²))`, calculated with 64-bit accumulation and stable handling of zeros. Report **task-level** medians of the 1,830 epoch PTP/std/RMS values (unless some are nonfinite, then median among eligible epochs with eligible denominator), **not channel-level vectors**. This is a technical description, not an estimate of physiological brain-state effect.
4. **Within-channel extreme variation heuristic (exploratory flag, not exclusion):** for each channel, compute median of its 30 **finite** epoch PTP values. Count epochs with PTP strictly **>10×** this positive within-channel median. Channels with zero/undefined reference median are marked `extreme_threshold_undefined_channels`, not assigned a normal result. Report exact `relative_extreme_channel_epochs` count across eligible 1,830 and the fixed >10 rule; do not tune factor after seeing data. Differences across tasks are descriptive only and may reflect legitimate EEG state changes, preprocessing, residual artifacts or noise.
5. The task-level `raw_exact_value_min`, `max`, `percentiles` and per-channel amplitude or sample values are **not** required and MUST NOT be published. Amplitude RMS/std/PTP **medians in native stored numeric units** are allowed but do not interpret as microvolts until the original header unit/resolution values are separately authenticated. Report nonfinite, flat, threshold counts alongside technical summary.
6. Compare G01 source header sample/channel layout, whole-file digest, total counts and 10-second epoch conservation exactly. If source unresponsive return `SOURCE_RETRIEVAL_BLOCKED`; if identity mismatch `ORIGINAL_SOURCE_HASH_MISMATCH`; if format/channel/rate mismatch `RAW_LAYOUT_UNVERIFIED`; if numerical or conservation check fails `INSTRUMENT_FAILURE`. A complete and internally consistent QC audit returns `SOURCE_SIGNAL_QC_CENSUS_COMPLETE` with **separate red flags**; if any NaN/Inf or flat whole-channel/epoch exists, label `SOURCE_SIGNAL_QC_REVIEW_REQUIRED` without automatically declaring data clinically invalid.

**Important:** This is a quality-*screening* descriptive census, not a defensible automatic "artifact-free" test. **Amplifier clipping cannot be concluded** without calibrated ADC range and corresponding pre-processed physical units. Large PTP does not itself demonstrate a defect.

## Synthetic negative controls and original chronology

Before the first original EEG sample is loaded, execute synthetic tests of:
- 61×5,000 fixed float32 value blocks with all finite values; NaN and both signs of infinity; constant/flatline and near-zero nonzero variations; long identical neighbours; exact 10× PTP boundary versus >10×; undercounted and malformed shape; invalid original source SHA, wrong sample count, and `python -O` guard;
- a **fake authorized source** with invented values passing source identity injection for test purposes, never labeled original EEG and never used to claim neural effects;
- a network-offline synthetic failure.

The original first run must print **only aggregate QC result JSON** with two task labels and six source-identification hashes and full denominators. Preserve its first SHA-256 unchanged and original workflow logs; audit all failed attempts. A successor G03 must register *separately*, with explicit eyes-open additional ICA and spectrum/binarization controls, before any LZc is computed.

## Interpreting negative and positive outcomes

- **If no technical flags**: we have source-level numeric integrity only, not equal EEG preprocessing, physiological/clinical usefulness, or proof for all 900 recordings.
- **If technical flags**: document exact source metrics, do not remove the bad epochs in retrospect, and **do not compute a favored LZ contrast** from selectively clean windows without a new registered rule.
- **If source inaccessible**: admit the access limitation. Do not invent EEG samples or retroactively change the endpoint or original source route.

**No universal law, clinical claim or article validation is a success condition.** Only an accurate, reproducible signal-quality description is.
