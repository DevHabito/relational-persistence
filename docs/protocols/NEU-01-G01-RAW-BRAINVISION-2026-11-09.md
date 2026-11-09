# NEU-01-G01 — Authenticate the first two original BrainVision resting-state files

**Date registered:** 9 November 2026. **Parent research branch:** `research/neu-01-lzc-validity-20261109` at `b2e716c1535ea21b4d420c88101aec566ecc05dd`. G01 is a separate, **stacked draft PR**, not a modification of the original NEU-01-G00 report. This protocol commits alone **before downloading or parsing original EEG header, marker, or voltage files**. The exact git-annex pointer keys and filenames were inspected beforehand, so this is a *pre-source-content* procedure, not a blind file selection.

## Objective and answer criteria

Resolve the narrow question raised by G00: does the `sub-01/ses-session1` **original BrainVision acquisition header and binary byte structure** support the 64-channel count in the eyes-closed BIDS JSON or the 61-row BIDS companion `channels.tsv`? Compare one **eyes-closed** and one **eyes-open** recording from the **same** participant and session, not any clinical diagnosis, neural LZ complexity, consciousness, thermodynamic entropy, physical time or the investigator's theoretical Self model.

A valid answer is **source-technical** only. The same binary data may be read by EEG software in different ways; a verified channel header/byte-layout agreement with TSV does not settle montage preprocessing, eye artifacts, sampling filters, physical channel origin, or suitability for a future LZc comparison. Real EEG signals have not been inspected in G00.

## First-party exact version and immutable expected source keys

Original OpenNeuro `ds004148` GitHub mirror `OpenNeuroDatasets/ds004148`, **tag `1.0.0` points to commit `0c740d838a2c33feeec0b6e514aea323d0e65ca4`**; this was independently checked via GitHub tag refs before this protocol. The OpenNeuro DOI is `10.18112/openneuro.ds004148.v1.0.0`, the publisher Wang et al. 2022 DOI is `10.1038/s41597-022-01607-9`. All six source objects have pinned git-annex `MD5E` object names and **nominal source byte lengths known before the actual source read**, confirmed by GitHub symlink text:

| Frozen file | Original annex MD5 | Original bytes |
|---|---|---:|
| eyesclosed `_eeg.vhdr` | `c5e313903936ef2fb9c1b3e0bfd61593` | 1,122 |
| eyesclosed `_eeg.vmrk` | `372402829a14249220eb8365f964d2de` | 5,960 |
| eyesclosed `_eeg.eeg` | `0fceeb9eb4163b86b815061f8fff80d7` | 36,600,000 |
| eyesopen `_eeg.vhdr` | `a5f9899c3cfa0c85f24c93c4eb83ef4c` | 1,118 |
| eyesopen `_eeg.vmrk` | `df580c077add7e4a840b46585cf8499e` | 5,958 |
| eyesopen `_eeg.eeg` | `75e12c6499540e3148316ef502ad03dd` | 36,600,000 |

Each pointer is relative to `sub-01/ses-session1/eeg/sub-01_ses-session1_task-{eyesclosed|eyesopen}_eeg`. No file with a different subject/session/task, different byte length or different MD5 is an acceptable substitute. Companion TSV text Git blob is already pinned at SHA `105960eb0ac14bae43bea73aa479a5c6d995c7a3` with 61 rows for both tasks, plus BIDS JSON Git blobs `e42057e3041f316388955e96c485dd073101a845` (eyesclosed, 64 declared) and `857311c71e3844e3842ad009ea77f457226fac0e` (eyesopen, 61 declared).

## Exact source route and fail-closed download

**Primary single route only:** the publisher-synchronized publicly accessible AWS OpenNeuro bucket `openneuro.org`, in `us-east-1`, using paths and file names identical to the tagged dataset tree:

`https://s3.amazonaws.com/openneuro.org/ds004148/sub-01/ses-session1/eeg/<exact_original_filename>`.

This source route is documented in [OpenNeuro Git/annex documentation](https://docs.openneuro.org/git.html) and in the [AWS Open Data Registry](https://registry.opendata.aws/openneuro/); no other third-party mirror/rename/reencoded Zarr representation is permitted in the **first** G01 run. Test with small headers first, but require all six original objects and companion channel TSVs before declaring `ORIGINAL_BRAINVISION_PAIR_AUTHENTICATED`. An access failure means `SOURCE_RETRIEVAL_BLOCKED`, not that EEG contains an error. The runner may be offline; do not substitute invented text.

Stream the two original `.eeg` bodies in bounded chunks (1 MiB maximum buffer), no more than 40 MiB per individual binary, total <=100 MiB; no original EEG, identifying metadata, markers, sample values, event positions, full channel lists or questionnaires may enter CI logs, repository or artifacts. Use a short-lived OS temporary directory and delete in cleanup. Retain only aggregate channel counts, exact SHA-256 for each original object, anonymized task labels, header codec, sample interval, sample count and pass/fail flags. Original per-file MD5 and byte length **must both match the frozen annex keys**, and new SHA-256 is recorded. MD5 is an existing git-annex identifier, **not** a novel stronger integrity claim.

Also download the 61-row `channels.tsv` companion for each task from the same publisher source, compare content Git blob SHA-1 via `SHA1("blob " + byte length + NUL + bytes)` to pinned SHA, parse original TSV channel names (without modifying) and compare ordered names against the **actual BrainVision `[Channel Infos]` section**. Never publish personally identifying values.

## Fixed mechanical BrainVision checks

Parse the actual `.vhdr` as original text, preserving byte hash and enforcing:
- `[Common Infos]` fields `DataFile`, `MarkerFile`, `DataFormat=BINARY`, `DataOrientation=MULTIPLEXED`, `NumberOfChannels` and `SamplingInterval`; require DataFile/MarkerFile to be exactly the matching current task files, not an absolute path or traversal.
- `[Binary Infos]` `BinaryFormat`: accept `IEEE_FLOAT_32` (4 bytes) or `INT_16` (2 bytes) only if unambiguously parsed; unrecognized types => `BRAINVISION_LAYOUT_NOT_VERIFIED`.
- `[Channel Infos]` exactly `Ch1…ChN`, ordered without duplicate ordinal/labels; compare ordered names to source TSV rows (case-sensitive, no truncation, no sorting or aliases). A channel name mismatch is a separate finding, not a silent fix.
- `SamplingInterval` is in microseconds; sample rate = `1,000,000 / SamplingInterval` exactly. Check source sidecar 500 Hz, 300-second declared duration and binary divisibility by `Nchannels × bytesPerSample`. Compute sample count as `file bytes / (Nchannels × bytesPerSample)` and duration from rate. Do not assume 64/61 from the file size **before reading the authentic original header**.
- Original `.vmrk` marker header has appropriate marker `[Marker Infos]`; require plausible same filename and no arbitrary relative path. Count marker entries without printing positions, codes or descriptions.
- Test that both task channels have a nonempty exact intersection and report **how many** common names. This verifies name matching only; not equivalent signal processing or independent channels.
- The exact three-way relationship of eyesclosed `EEGChannelCount=64` (BIDS JSON), eyesclosed `channels.tsv=61`, and verified original `.vhdr` channel count is a **first-result observation**. Report as such without any automatic BIDS correction.

Fail closed if original MD5/size, Git TSV SHA, binary length, marker/header required fields, sample interval, channel ordering, duration or basic exact identity checks fail. Distinguish failures: `SOURCE_RETRIEVAL_BLOCKED` (HTTP/network), `ORIGINAL_SOURCE_HASH_MISMATCH`, `BRAINVISION_LAYOUT_NOT_VERIFIED`, `SOURCE_CHANNEL_METADATA_DISAGREEMENT`, or `ORIGINAL_BRAINVISION_PAIR_AUTHENTICATED` if both source bodies verified and parsable. A metadata difference may coexist with an authenticated pair: never erase it.

## Pre-source controls and archival integrity

Before **any source request**, run synthetic-only tests for fake BrainVision headers, expected MD5/length, traversal and wrong file names, wrong units or rates, non-divisible stream size, extra/missing channel labels, duplicate channel ordinals, an invented 64-vs-61 discrepancy and `python -O` guard bypass. Also simulate HTTP download failure without a real request. No raw EEG generated for publication and no arbitrarily constructed simulated EEG used to proclaim a physiological result.

First run output: frozen numeric JSON with exact source original bytes, SHA-256 and flags (and original annex MD5 expected checks). Archive original JSON byte-for-byte on branch after first run with independently pinned SHA. Preserve initial failures if any; do not retroactively change this protocol. Python regressions must pass before and after.

## G02 / NEU-01-P01 are NOT authorized by this stage

No original LZc result, EEG statistical comparison, medical diagnostic validation or theoretical Self claim is permitted at G01. Only after the raw pair audit and channel/montage harmonization is resolved could a *new protocol* register fixed preprocessing, 10-second signal epochs, LZ76 implementation, phase-randomized surrogate baseline, power/spectral slope, paired subject-level and retest controls, expected negative and positive conditions, and leakage-free held-out inference. NEU-01-G01 has **no rule** for silently changing that later hypothesis to guarantee a positive effect.
