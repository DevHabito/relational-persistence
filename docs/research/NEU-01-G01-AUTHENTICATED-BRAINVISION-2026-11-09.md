# NEU-01-G01 — Authenticating the original resting EEG files resolves the 64-versus-61 channel discrepancy

**9 November 2026** · First **original binary source** audit · **No Lempel–Ziv complexity on physiological samples computed**

The goal is narrow and falsifiable: establish which channel count is present in the **original raw BrainVision recordings** for `sub-01/ses-session1` of the published OpenNeuro `ds004148` collection, and whether the original channel labels, file layout, samples and acquisition rate support a reproducible paired eyes-open / eyes-closed signal study. It is **not** a test of a psychiatric biomarker, the investigator's theory of the Self, or thermodynamic entropy.

## Prior state and source chronology

In NEU-01-G00, the original BIDS text sidecars were authenticated at the **OpenNeuro Git tag `1.0.0`, commit `0c740d838a2c33feeec0b6e514aea323d0e65ca4`**. The eyes-closed `*_eeg.json` said **64 EEG channels**, but its companion `*_channels.tsv` listed **61**. Four other tasks' JSON/TSV pairs from the same session declared/listed 61. The source itself was not corrupted or corrected, and the difference was never presented as an EEG physiological discovery.

The G01 [protocol](../protocols/NEU-01-G01-RAW-BRAINVISION-2026-11-09.md) was committed separately at `aad92e9dbbc7518e1d0dac954683d024ee93d0f3`, **before retrieving or parsing any actual original .vhdr, .vmrk or .eeg contents**. The six original git-annex MD5E identifiers and nominal file sizes were already known and frozen in the protocol. GitHub mirror's `1.0.0` tag resolves to the frozen original Git commit, so the selection is version-specific. The first source used the public OpenNeuro S3 dataset path—not a synthetic re-encoding, altered dataset or NEMAR/Zarr substitute.

**Original public source:** `s3://openneuro.org/ds004148/sub-01/ses-session1/eeg/`. [OpenNeuro Git and annex documentation](https://docs.openneuro.org/git.html) and [AWS Open Data registration](https://registry.opendata.aws/openneuro/) describe this original versioned data distribution. [Wang et al. (2022)](https://doi.org/10.1038/s41597-022-01607-9) describe the original resting/cognitive dataset, not an independently validated psychiatric cohort.

## Actual first original source result

The exact first [GitHub Actions run #42628788400](https://github.com/DevHabito/relational-persistence/actions/runs/42628788400), source code/workflow head `1519960c8ea42692e98ac3ca3544274a27c2a19c`, ran **17 synthetic transport, strict parser, duplicate channel, invalid S3 name, failed download and hash-negative controls** before making any real source request. All passed. The task-specific source script then downloaded exactly **six genuine BrainVision objects** and the two channels TSVs. It verified each BrainVision file's **original git-annex MD5 and byte length**, computed a new whole-file SHA-256, and checked each TSV's original Git blob SHA. No original voltage arrays, personal data, marker values or per-sample information were committed, printed or uploaded.

**Verdict from the actual original JSON:** `ORIGINAL_BRAINVISION_PAIR_AUTHENTICATED`.

| Direct check on **original** published file | Eyes closed | Eyes open |
|---|---:|---:|
| BrainVision original header `NumberOfChannels` | **61** | **61** |
| Original ordered `[Channel Infos]` match corresponding TSV | **61 / 61 exact** | **61 / 61 exact** |
| BIDS `*_eeg.json` EEGChannelCount, by contrast | **64** | **61** |
| Original EEG binary size | **36,600,000 bytes** | **36,600,000 bytes** |
| Original source sampling interval | 2,000 μs | 2,000 μs |
| Original source sampling rate | 500 Hz | 500 Hz |
| Original source samples per channel | **150,000** | **150,000** |
| Original record duration from sample layout | **300 seconds** | **300 seconds** |
| Original binary format | IEEE float32 | IEEE float32 |
| Original marker-record entries | 151 | 151 |
| Original annex MD5, full file size, and new SHA-256 | Verified | Verified |

**All 61 original channel names are common to these two recordings**, and each original BrainVision channel list exactly matches its own source TSV ordered names. This is an observed name equality, **not** proof the eyes-closed/eyes-open signals have equivalent filtering, artifact removal, electrical references or physiological interpretation.

The original binary layout arithmetic is independently consistent: `61 channels × 150,000 samples/channel × 4 bytes/IEEE_float32 = 36,600,000 bytes`. A 500 Hz rate gives 300 seconds. Had the raw header said 64, or the data layout not supported the declared number, the registered parser would reject it; neither was silently adjusted.

### Source integrity examples

| File | SHA-256 computed from the **original retrieved object** |
|---|---|
| Eyes-closed `vhdr` | `b3f437f5e1cc95b3dbedb989d9c637c832ae4406b55782f8c8aeeb2fefc96061` |
| Eyes-closed `vmrk` | `c75c687404dd131319d45f76fe131af5bdbbe6d880ca2cf426a5fc1e99b5d1e4` |
| Eyes-closed `eeg` | `022b9f34914e4314f4d9e45d17bc367031c9d9d879ea983a8d6eb43f7affbc47` |
| Eyes-open `vhdr` | `7a02a0d6d25413ebc1600a737f2d30f33fc4fc608b25c03564f5918463c3845f` |
| Eyes-open `vmrk` | `d03aa7ccdd3a151ce58adbbc239be26d2dc2eb9ed3d8e134d2427b839f8e6852` |
| Eyes-open `eeg` | `d4c9357b8996fa8e989317d9c945b8e71adfe9e3564c96812689c9cf29e09ac9` |

All six source expected original git-annex MD5 identities and sizes were verified before accepting these new digest values. This is much stronger source identity evidence than the previous G00 textual sidecar-only audit, but it does **not** establish clinical suitability, lack of movement artifacts or completeness of the full dataset.

## What exactly has been resolved?

**For this one original paired session, the 64-channel eyes-closed BIDS JSON field is inconsistent with both the actual authenticated original 61-channel BrainVision header and the original 61-row TSV.** The one-to-one correspondence between actual original BrainVision electrode labels and the TSV provides a technically grounded answer to the G00 source question. The first 64-versus-61 discrepancy is **metadata-local**, not a verified variation in this original pair's binary channel dimension.

This should not be generalized to the other 59 participants, all sessions, other dataset versions or the mechanism of the original publisher's metadata construction. We have neither repaired the upstream dataset nor investigated why that JSON says 64. We have not compared the actual voltage amplitudes, removed artifacts, calculated LZc or estimated reliability across participants.

## Exact provenance and reproduction

The original hosted source report is archived unchanged at [`NEU-01-G01-first-run/audit.json`](../results/NEU-01-G01-first-run/audit.json), with first-run SHA-256 **`e43ccdb5523bcf14b07ec52ed28ef57200ce4ec2e8268d17f011b9bcd6f0e243`**, taken from the first job's logged `sha256sum`. Its [archive index](../results/NEU-01-G01-first-run/archive-index.json) preserves the protocol commit, workflow source head, six new source hashes, byte lengths, both original JSON/TSV/header counts, absence of signal analysis, and first source artifact ID. The job reported the artifact ZIP SHA-256 `ba08484c39326bf060ed36f9b2abedef4ec475724c11ca0bf09bc272a0e183d1`, but no independent second download-and-rehash of that ZIP is claimed. A later regression checks the archived first JSON against this fixed first-job SHA and verifies conservation of all file identities and dimensions.

The direct original source bodies were held in a temporary runner directory, then deleted. No original EEG voltage array, marker value or individual participant record is uploaded to the repository; only non-identifying task-level provenance is stored.

## Next research question: preparation and a *separate* EEG physiology protocol

The next technical gate is **signal usability**, not a premature new biomarker:

1. Independently check a **small, fixed** subset of original EEG amplitudes for nonfinite/saturated values and declared scaling/units, assess documented eyes-open artifact/ICA processing relative to eyes-closed, and predeclare quality rejection decisions; all QC thresholds must be recorded **before** computing LZ contrasts.
2. Choose the fixed channel intersection, epoch/window length and Lempel–Ziv sequence algorithm, with adversarial reference cases and normalization. Prior art has already established spectral/phase-randomized surrogate tests, so these must be **strong controls**, not a claim of invention. Compare spectral power and 1/f slopes, as in existing EEG complexity literature.
3. After the raw pilot, preregister a **different** NEU-01-P01 primary analysis on enough subjects and sessions, with subject-holdout and proper uncertainty, checking task-specific changes under spectral and artifact controls rather than clinical labels.
4. If raw EEG amplitude quality or preprocessing equivalence cannot be established, **stop** and record `SIGNAL_QC_NOT_ELIGIBLE`. Source authentication alone never justifies a neuroscience conclusion.

**Our goal is not a universal theory:** it is an accurate answer to a small question that must be answered correctly before testing how, or whether, neural complexity relates to functional flexibility or the subjective Self.
