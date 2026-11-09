# NEU-01-G02 — Original two-condition EEG sample integrity: complete native-value census, unresolved calibration

**9 November 2026** · Source-level descriptive analysis of **one participant, one session**, original OpenNeuro `ds004148` **v1.0.0** · **Not EEG complexity, a clinical biomarker, or physical entropy**

## Why this narrow experiment matters

The next stage of NEU-01 seeks to determine whether Lempel–Ziv complexity (LZc) provides meaningful information about changes in brain function beyond differences in measurement, preprocessing and conventional spectral features. That question cannot be answered by calculating LZc immediately. First we must know whether the original EEG samples are even numerically intact and how they were prepared.

**Prior art matters.** Wang, Yulin; Duan, Wei; Dong, Debo; Ding, Lihong; Lei, Xu (2022), “A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states,” *Scientific Data* 9:566, DOI [10.1038/s41597-022-01607-9](https://doi.org/10.1038/s41597-022-01607-9), describes visual inspection, reconstruction/interpolation, common-average reference and separately applied **eyes-open ICA for eye blinks and eye movements**. The paper reports about 0.978 (±0.146) components marked as artifact per eyes-open session and prior 4-s epoch inspection. These documented preprocessing differences can affect exact digital values and complexity even when recording duration and the channel label set are matched. The present research **does not independently quantify the authors' ICA effect**.

The [BrainVision format specification](https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/) distinguishes header channel metadata, sample representations and physical unit scaling. **Native stored IEEE float32 numbers are not automatically verified microvolts.** Clipping requires known instrument range and provenance.

## Frozen original protocol, failed first run, and revision before amplitude reading

The original G02 [protocol](../protocols/NEU-01-G02-ORIGINAL-EEG-QC-2026-11-09.md) was committed **alone** at `8afd08353216c0afc3a58a13e2132de2f8c62e67` before examining original G02 EEG samples. It pinned the same G01-authenticated `sub-01/ses-session1` original eyesclosed and eyesopen objects, 61 channels, 150,000 samples/channel, 500 Hz, 300 s, entire 18,300,000-number universe, 10-second/5,000-sample nonoverlapping epochs, and exact zero, NaN, Inf, flat-channel, flat-epoch, repeated-adjacent and strictly >10× within-channel median PTP metrics. It required explicit original header resolution **and** physical unit on every channel.

**The actual FIRST attempted run failed; this is not concealed.** [GitHub Actions #42637541779](https://github.com/DevHabito/relational-persistence/actions/runs/42637541779), source head `d0b2119dc2b434c6a140755931b7488155781b4a`, first passed **16 synthetic checks**, downloaded and verified the first original source header, then stopped **BEFORE any EEG original amplitude sample was read**. The cause was `CHANNEL_SCALING_OR_UNIT_UNSPECIFIED`: at least one source header did not provide the four comma-separated name/reference/resolution/unit fields the G02 parser demanded. The first attempt returned `INSTRUMENT_FAILURE`; its original JSON remains verbatim at [`NEU-01-G02-first-attempt/audit.json`](../results/NEU-01-G02-first-attempt/audit.json) with SHA256 `1b14fb32bce882c737350260a70dcfade14086e0cc29ec3dd042dd19d8ece59d`. No “first try success” claim is permitted.

**The revision was registered before first amplitude reading.** [G02-R02 explicit addendum](../protocols/NEU-01-G02-R02-MISSING-UNIT-ADDENDUM.md) at commit `b4671dd92236d88edde55fa72a0fb587c36bbae5` allowed **only the weaker, still valid question of native-stored-value integrity**, reporting missing original channel physical units as `MISSING` rather than inventing `µV` or recalibrating. It retained all source identities, samples, window size, endpoint formulas, denominators, non-omission rules and the >10× threshold. No sample-dependent choice entered this revision because no EEG samples were decoded in the first attempt. The amplitude/physical interpretation was deliberately **downgraded, not salvaged by assumption**.

## Full original first-success sample source run

The first source-amplitude run under the registered revision [#42638326092](https://github.com/DevHabito/relational-persistence/actions/runs/42638326092), source code/workflow head `7db18d3f8915d6181d8682a4b38904bf3f043a8c`, completed successfully. **16 synthetic/negative controls** passed prior to source access. It independently re-downloaded the authenticated original `.vhdr` and `.eeg` files for each state from the **official OpenNeuro S3 bucket**, reverified original git-annex MD5 and exact size, and matched **new SHA-256 to the G01 first original run**. Only after all identity checks did it memmap the true binary body as little-endian, interleaved `IEEE_FLOAT_32`, and inspect all `150000×61` stored values per task. The original signal contents were in a temporary directory and **were not committed or printed**.

Its authoritative decision was `SOURCE_NATIVE_NUMERIC_QC_CENSUS_COMPLETE_CALIBRATION_UNVERIFIED`. The word **native** is critical: this code never applies the unit scaling, reference correction, ICA or artifact rejection required for a meaningful physiological signal interpretation.

### Exact full recording counts

| Registered original stored-value QC measure | Eyes closed | Eyes open |
|---|---:|---:|
| Source channels | **61** | **61** |
| Original float32 samples/channel | **150,000** | **150,000** |
| Original individual float32 values | **9,150,000** | **9,150,000** |
| Finite original values | **9,150,000** | **9,150,000** |
| NaNs | **0** | **0** |
| Positive infinity | **0** | **0** |
| Negative infinity | **0** | **0** |
| Exactly zero original numerical values | **23,558** | **0** |
| Exactly equal adjacent values, within each channel | **195,420** | **7** |
| Possible adjacent pairs in each task | 9,149,939 | 9,149,939 |
| 10-second non-overlapping epochs per channel | 30 | 30 |
| Channel-epochs inspected | **1,830** | **1,830** |
| Channel-epochs containing nonfinite values | **0** | **0** |
| Channel-epochs exactly constant | **0** | **0** |
| Entire channels exactly constant | **0** | **0** |
| Channel-epochs PTP >10× own channel median PTP | **0** | **0** |
| Undefined per-channel PTP reference medians | **0** | **0** |
| Median 10-second channel-epoch peak-to-peak (stored numerical unit) | 61.5 | 57.717540741 |
| Median 10-second channel-epoch standard deviation (stored numerical unit) | 10.3965268194 | 9.3724256661 |
| Median 10-second channel-epoch RMS (stored numerical unit) | 22.9430919198 | 23.0842290601 |

Conservation conditions checked in the actual source run: **18,300,000** original sample values, **3,660** channel-epochs, **both** 61-channel recordings, every sample either finite/NaN/±Inf, every channel-epoch either all finite or containing nonfinite, exact one-to-one source hashes and shape. No values, channels or entire epochs were silently dropped.

### Physical calibration is genuinely unresolved, not “corrected”

Both original authenticated `.vhdr` files have **61 channels each declaring resolution value `1`**, but **all 61 entries in each file omit an explicit physical unit field**. This corresponds to 122 channels without directly specified physical unit metadata. The G02-R02 result therefore records `header_unit_counts: {MISSING:61}` per task and `calibrated_physical_amplitude_ready=false`; the numeric PTP, standard deviation and RMS are left in **native stored values**, never labeled microvolts. In particular, an amplitude-based clipping diagnosis cannot be made from this material alone.

An earlier source-data paper and common formats may suggest units, but transferring that convention to an original measurement without validating the actual calibration would be a source error. No such transfer is made here.

### What the surprising asymmetry does and does not suggest

The eyes-closed recording contains **23,558 exact zeros** and **195,420 equal consecutive within-channel pairs** among 9.15 million values, while the corresponding eyes-open recording has **zero exact zeros** and only **seven identical adjacent pairs**. These are **exact digital representation counts**, not spectral effects, arousal metrics, clinical biomarkers or a measure of rigidity. Some **possible** explanations are quantized/discrete values in one pipeline, digital interpolation, different signal-processing histories or file-conversion details. The published **additional eyes-open ICA** supplies a plausible technical confound, but we **have not identified causation**: no intermediate/pre-ICA copies or source processing provenance were reconstructed in G02.

The absence of NaN/Inf and strictly constant full epochs is useful numeric-integrity information. It does **not** prove the signals are artifact-free, electrically calibrated, equally preprocessed, or suitable for a cross-condition LZc claim. The within-channel >10× PTP screen is a deliberately crude descriptive threshold; a zero count is **not** an absence-of-artifact certificate. The exact zeros may be algorithm-dependent and should not be treated as an independent count of damaged data.

The sample is **one participant, one session**. There is no statistical participant-level inferential sample here, no predeclared null comparison across participants, and no basis for mental-health, consciousness or Self claims.

## Source authenticity, independent tests, immutable first-run evidence

- G02 original protocol-only commit: `8afd08353216c0afc3a58a13e2132de2f8c62e67`.
- First failed run and cause: [#42637541779](https://github.com/DevHabito/relational-persistence/actions/runs/42637541779) — calibration-header precondition not met, original EEG amplitude universe **not processed**; first negative JSON hash `1b14fb32bce882c737350260a70dcfade14086e0cc29ec3dd042dd19d8ece59d`.
- Separate amendment committed **before first amplitude samples**: `b4671dd92236d88edde55fa72a0fb587c36bbae5`.
- First original full native-number QC [#42638326092](https://github.com/DevHabito/relational-persistence/actions/runs/42638326092): 16 synthetic tests passed, full first output SHA256 `2b72a36e7692533130c890a28294ab8b8b5bc739b566697c9fa946bf26528ff2`. Original [first complete signal JSON](../results/NEU-01-G02-R02-first-signal/audit.json) is committed byte-for-byte, with the separate provenance [archive index](../results/NEU-01-G02-R02-first-signal/archive-index.json), including the earlier failed attempt and both original source job details.
- The first failed source artifact ZIP SHA-256 reported by GitHub is `9990d1f96dc39642ecef493eaf2cff3573fb12857aa335eeb1674b8dc3654dea`; the second first-success artifact ZIP SHA-256 as reported is `8123212dcf497774a6bc46a320b069e126470ec1067b434916580bd1ee776e1e`. **Neither ZIP was independently re-downloaded and rehashed**. The sample/first-source JSON files themselves are rechecked in subsequent regression against independently pinned original SHA.
- The final project regression verifies the synthetic counterexamples and refuses changed first-run JSON or source-counter records. No new Lean 4 statement or theorem is introduced by G02; the previous Lean library is unchanged.

## Proposed next registered research question

**NEU-01-G03:** Is the excess exact-zero / identical-adjacent-pair structure in the original eyes-closed source **a stable source-format / preprocessing signature** across other original subjects and sessions, or a peculiarity of one person/session?

Before opening additional samples, freeze a *different* held-out participant/session selection and the exact **per-channel/per-epoch** repetition/zero metrics and sample counts, as well as the null hypothesis and a comparison with independently documented acquisition/ICA history. The next experiment may need to inspect BIDS JSON/BrainVision metadata and supplemental source-processing methods. **Do not conclude “artifact”, “ADC clipping” or “neural complexity difference” merely because repeated-value counts differ.**

Only after preprocessing differences and source physical units are resolved (or rigorously constrained in the actual numerical analysis) could a **separate original EEG LZc protocol** be responsibly registered with phase-surrogate, spectral-power, 1/f, same-subject, held-out-person and retest baselines. The user is looking for **truthful limited findings useful to humanity, not a universal law**. Negative replication or an unusable source is a valid result.
