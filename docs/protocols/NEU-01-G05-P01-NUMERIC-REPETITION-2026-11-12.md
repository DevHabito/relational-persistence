# NEU-01-G05-P01 — Native float32 repetition runs and integer occupancy

**Protocol-only freeze: 12 November 2026, before G05 implementation or new source read.** This is an unblinded technical follow-up of already observed G02–G04 results, not new people, independent acquisition, a blind human experiment, or a neurophysiology test.

## Bounded source question

G04 archived a byte-authenticated independent recount of six EEG files, consisting of 54,900,000 original native IEEE float32 numbers. It found 457,636 nonzero equal-adjacent pairs and 1,258 zero-zero pairs in the three eyes-closed files. **What are the lengths of the corresponding maximal constant-value runs, and which exact nonzero sample/repeated values happen to be integers in native stored units?**

These data are already processed. Exactly integer-valued native numbers depend on uncalibrated numerical scaling and cannot identify physical quantization, ADC resolution, interpolation, neural physiology, or preprocessing causality.

## Frozen source and integrity checks

Re-read precisely the same six files, no substitutions: OpenNeuro ds004148 v1.0.0, original source Git revision 0c740d838a2c33feeec0b6e514aea323d0e65ca4, official S3 objects; sub-02, sub-03, sub-04, session1, eyesclosed and eyesopen. Each recording contains 150,000 x 61 little-endian float32 numbers and 36,600,000 original binary bytes. Reuse the byte-size, MD5, SHA256 and BrainVision header gates already fixed in G04, including 61 channels, 500 Hz, missing physical unit and no rescaling. Authentication failure is SOURCE_NOT_ELIGIBLE, not a scientific negative.

The existing G04 audit must be read only after validating exact 6,022-byte length and SHA-256 7b32e1e0fc31d82ec2d1a3c509b0304bbbb4219db2145788d05d90d87140dc00; it serves as **already-known comparison**, not a blind prediction.

## Exact endpoints (frozen before computing G05)

For each original participant/condition, operate on every channel separately, with all 150,000 frames:

1. Partition samples into **maximal within-channel runs of exactly equal decoded numerical float32 values** (signed zero considered equal). Count the full exact integer-length histogram for ALL repeated zero runs of length k>=2, and separately for ALL repeated nonzero runs of length k>=2. Do not cap, select or coarsen any run length. Publish the maximum repeat-run length for zero and nonzero (0 if none). No channel names, timestamps or actual stored values.
2. Count all *nonzero* samples exactly equal to a mathematical integer in their stored uncalibrated units, numerator native_integer_nonzero_samples, denominator native_nonzero_samples. Integers include negatives, while zeros are explicitly excluded.
3. For each adjacent equal nonzero pair, count whether its common numeric value is exactly integer, numerator native_integer_nonzero_equal_pairs and denominator nonzero_equal_adjacent. Publish fractions only as exact numerators and denominators; no undocumented rounding.
4. Recount zero values Z, zero-zero adjacent equal pairs E00, nonzero equal pairs Enn, all equal pairs E, number of zero runs R0, all 61 within-channel adjacency boundaries, and nonfinite counts. Check E=E00+Enn, Z=R0+E00, and sum_over_nonzero_runs (k-1) = Enn, sum_over_zero_runs (k-1)=E00. Count all samples, never silently omit any.
5. Only **after** source-derived G05 counts are calculated, compare the G05-recounted G04 source aggregates exactly against the frozen G04 original archive. Compare six original SHA256s, all E/E00/Enn/Z/R0 and dimensions; reject mismatches. The G05 run-length and integer rates must not be chosen or tuned based on seeing their results.

The sole pass label is G05_EXACT_SOURCE_CENSUS_COMPLETE if six original files are authenticated, source totals match G04 and all accounting identities pass. G05_RECOUNT_MISMATCH if authenticated source totals disagree with archived G04 values. SOURCE_NOT_ELIGIBLE if original byte identity, layout, instrument or nonfinite guards fail. There is no biological outcome threshold, p-value, new population inference or claim that integer occupancy proves a particular source mechanism.

## Tests and chronology

Before source access, synthetic tests must use a **separate loop reference** to verify maximal runs and exact integer numerators on short two-channel sequences, signed zeros, negative integers, -1.25 and 0.5, all-zero and all-fractional runs, alternating values, channel boundaries, NaNs, wrong length and corrupted G04 checksum. Use a hosted GitHub runner only, with bounded source bytes and runtime. Print/archive **aggregated JSON alone**, never original EEG bytes, source sample values, channels or per-channel identities. Preserve first source result and all failures. Commit this protocol alone first; code, tests, workflow and actual source execution follow in separate commits. Any post-source repair must be disclosed separately before retry.

## Prior literature and limits

**Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (2022, 13 September)**, A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, *Scientific Data* 9:566, DOI https://doi.org/10.1038/s41597-022-01607-9, reports preprocessing including common-average reference, filtering, interpolation and additional eyes-open ICA. **Brain Products, BrainVision Core Data Format 1.0**, defines original numeric encoding and channel metadata. Neither these pre-existing methods nor elementary run counting were invented by this project.

Dictionary: numeric float32 equality is decoded numerical equality rather than identical bytes; maximal run is the longest contiguous constant-valued segment inside one channel; integer-valued means exactly integral in native stored, uncalibrated numeric units; repeat-run histogram is full integer-length counts with no arbitrary binning; same-source replay is not a new human replicate. No entropy production, Lempel-Ziv complexity, psychological rigidity, neural-state mechanism, clinical biomarker or physical theory is claimed.

**At registration:** G05 source-derived run histograms and integer counts have not been inspected. G02–G04 source outcomes and their limitations were already known.
