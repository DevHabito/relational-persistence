# NEU-01-G04-P01 — Independent source-level replay of six original G03 EEG files

**12 November 2026: protocol-only freeze, before G04 implementation/source replay.** This is a retrospective reproducibility study of **already examined** G03 source recordings; it is not a new blinded human study or independent acquisition. The previously published G03 aggregate results and D01 mathematical inequality were already known. The exact zero-zero / nonzero-nonzero decomposition from individual G03 source samples remains to be recomputed separately.

## Fixed question and cohort

Can a new Python standard-library IEEE float32 reader, without importing NumPy or any original G03/G02 data reader or counter, reproduce **every recorded G03 integer summary from independently re-downloaded original files**? Does an exactly measured decomposition of adjacent equalities into zero-zero and equal-nonzero pairs satisfy the D01 lower bound?

The six original file identities are fixed: OpenNeuro ds004148 v1.0.0, official https://s3.amazonaws.com/openneuro.org/ds004148 path, participants sub-02, sub-03, sub-04, each in session1, task eyesclosed and eyesopen. Files must not be substituted or omitted based on any outcome. Dataset original revision: 0c740d838a2c33feeec0b6e514aea323d0e65ca4. Each original multiplexed binary contains 150,000 frames x 61 channels x little-endian 32-bit float = **36,600,000 bytes**, so there are **9,150,000 numeric values** and **9,149,939 within-channel adjacent opportunities** per file. The first G03 audit is immutable at SHA256 b142e6b0b0d03e1bd6167fba1a3d265bf3d5efd485e8389474f882955bf8195c (10,117 bytes).

## Frozen source identities from the already-seen G03 original archives

These are **known existing checksums**, not predictions. Header length = 1,122 bytes eyesclosed, 1,118 bytes eyesopen.

| Participant | State | EEG MD5 | EEG SHA256 | Header MD5 |
|---|---|---|---|---|
| sub-02 | eyesclosed | afc315cd4fbd76f2788a67fe31be9d8d | 9c9f8c321482c71657047e99a1c259aaa753bb3b5fbe09e392a06b33d8d6dacd | 10a0033fdb6dfd1f72a6e37b8164a269 |
| sub-02 | eyesopen | 3ca243fb3ab6cabcac5a99b8939abcce | 0e27c11253da07a3f6e6a4eff4716327ac38fcf061e71fc16a501cabe979ca | 4eb149775baddc320f39fcd4fc6f79c6 |
| sub-03 | eyesclosed | 4ca2b5bab215101621ddf023f31ba042 | cb135f4e93d2a5a76ff04c791934f9a73fe050297e8bcc49cb0f7e04f27b0eb3 | 98a9f2d1fbffbab2ad2636c05f340531 |
| sub-03 | eyesopen | 099a4fdb6e0e5fe105f04f4c250bc0a4 | 7099f2df02407f316a445f3fc6fbad33407b841db0fc5abb4b951c6a22f84f45 | ae548d8a0b43dfea2e28d1111d50450c |
| sub-04 | eyesclosed | 8a7314e14dcaabc117de238ebec6841f | eaa0cffa47243b6c121e41fa9e2bde8fa2f99439a9e57b1bf3272a05210592cb | f79c52b469a3845d70a7877ad18e3e43 |
| sub-04 | eyesopen | 28079903eac38f9f8670a80f0dc766f1 | eb5bdd843f730e0e42d490840a542831b1c0e525cbfa2b20782f9c568c0032fd | 7d979ba2cfa1a97b092d2782f2138c4b |

Retrieve only the matching original .eeg and .vhdr. Before decoding, independently authenticate every EEG file by byte size, MD5 and SHA256 and header by size/MD5, verify declared multiplexed binary / 61 channels / sampling interval 2000 microseconds / IEEE_FLOAT_32 / named matching data and marker file / exactly Ch1..Ch61. Treat absent physical-unit declarations as MISSING; no microvolt conversion or amplifier clipping inference. Reject unrecognized or changed format. All source I/O on a hosted GitHub runner; never download to the user's PC.

## Frozen counting and comparison

Read each authenticated EEG as **150,000 successive frames of 61 little-endian float32 values** via Python standard-library struct; maintain 61 preceding-channel values. For each channel, record all finite numerical values, all samples numerically equal to zero (both signs), and equal consecutive pairs. Separately record E00 (zero-zero), Enn (equal nonzero-nonzero) and R0 (number of maximal within-channel zero runs). Require E=E00+Enn, R0=Z-E00 if Z>0 and R0=0 when Z=0. Record per-recording number of channels with at least one equality and median and maximum per-channel equality counts. Never compare interleaved neighboring channels.

Only **after** independently finishing all six original counts, open the immutable G03 audit as an oracle and check all recorded individual counts, source SHA256, aggregate source sizes, six original paired differences and reported source-declaration limitations. A mismatching known count is a reproduction failure, not a biological surprise. For each recording, check newly observed Enn >= max(0,E-max(0,Z-1)), and E00 <= max(0,Z-1). No rounding.

**Decision rule (all-or-nothing):** INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH only if all six files are byte-authenticated and every known G03 recorded integer and newly measured accounting identity matches. INDEPENDENT_REPLAY_MISMATCH if any numerical comparison fails; list which participant/state/field without exposing signals. SOURCE_NOT_ELIGIBLE for source access, original-file identity or instrument/layout failure. If one file fails, no claim about the remaining subset. All first-run outcomes, including negative ones, must remain immutable.

## Prior/source scope and adversarial checks

Source-body access is **after** the separate protocol-only commit and pre-source synthetic/adversarial tests. Test exact zeros, signed zero, nonzero plateaus, multi-run zero segments, channel interleaving, truncation, nonfinite values, wrong endian/size and tampered archived oracle; use independently enumerated hand counts. The decoding algorithm must import neither NumPy nor G03/G02 readers. Bound download lengths, requests and action runtime; log no raw EEG, names, per-channel values or sensitive metadata. Archive **only summary JSON**, its SHA-256, exact workflow head and outcome. Preserve earlier G03 source and D01 result unchanged. Successful code tests are not a raw-data verification; require a hosted source workflow outcome.

## Literature and dictionary

Wang Yulin, Duan Wei, Dong Debo, Ding Lihong, and Lei Xu, 13 September 2022, *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9. Known different condition preprocessing, including additional eyes-open ICA, remains a confound. Brain Products GmbH, *BrainVision Core Data Format 1.0*, documents native float32 samples, header resolution and unit fields. None of the digital arithmetic is a newly discovered statistical or neural law.

Definitions: independent decoder = separate standard-library implementation **on the same processed source files**; zero-run = maximal consecutive within-channel numerical zeros; E00 = within-channel zero-zero equalities; Enn = equal adjacent nonzero numerical values; original G03 oracle = previously published result used **only after** independent decoding; physical calibration = currently unverified. No Lempel–Ziv, neuronal complexity, entropy, psychiatric biomarker or human functional-persistence conclusion.

**At protocol freeze:** no G04 decoder, G04 tests, original re-read or G04 result had yet been added.
