# NEU-01-G04-P01 — A separate reader reproduces G03 and counts zero/nonzero repetitions exactly

**12 November 2026** · Research record, original processed OpenNeuro ds004148 v1.0.0 files · Same three already examined participants and session 1 · **Reproducibility of stored digital numbers, not biological validation**

## Why I did this

G03 had a vectorized NumPy reader and an immutable result showing a striking difference in exact adjacent equality between eyes-closed and eyes-open files. My later D01 arithmetic deduction proved that not all those equalities could arise from identical zero samples. But D01 only gave a lower bound: the original aggregates did not say exactly how many repetitions occurred at zero.

I wanted a second decoder that did not import the original EEG reader or its counting functions. A mathematical argument applied to published summaries cannot discover a software error in the original sample counting. This re-read deliberately uses the **same** six previously inspected processed original source files; it cannot produce a new independent population or establish physiological causation.

The protocol was committed **alone** at 6449070c5b95e1d4bbddd2243549593d4ed85f46, before implementation. Its source identity table accidentally omitted two hexadecimal characters from one *already archived* SHA-256. I retained the failure and wrote the addendum described below, rather than silently replacing the old protocol.

## Exact first-run chronology, including the failures

1. **First attempted source workflow #43327245478**, code head d8df3af9: failed preflight because the clean hosted runner did not have pytest. No actual EEG source read occurred. I then added a hosted-only pytest installation; neither source endpoints nor mathematical decision rules changed.
2. **First source-capable workflow #43327371558**, code head 0216077c: **11** synthetic tests passed, but the run stopped at SOURCE_SHA256_MISMATCH before all six records were processed. Read-only comparison with immutable G03 metadata found one manually transcribed wrong source SHA for sub-02 eyesopen (omitted the two characters 01). No scientific verdict was published. This first partial source attempt is not a successful source replay.
3. **Correction addendum commit 4b66545**, written **before retry**, disclosed the error, its precise origin and a required prevention test. The unchanged original G03 archive already contained the correct exact hash. A new test now checks all six expected EEG SHA-256 literals against that immutable archived oracle prior to any source download.
4. **First successful complete workflow #43327626650**, exact source head dd51387cdeae6a19eed4c42eb74a9bf9d463a3a6: **12** synthetic/adversarial tests passed before accessing source bytes, all six original files were acquired with independent MD5 and SHA-256 checks, and a fresh Python standard-library struct reader decoded **54,900,000** stored float32 values. Original G03 sample counters, per-channel count summaries and six source identities matched exactly. Final declared verdict: INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH. The job also archived the aggregate-only JSON and completed successfully.
5. The full repository regression workflow **#43327626617** at the same source commit passed **884 tests in Python 3.11 and 884 in Python 3.12**, based on inspected job logs. These are software regressions, not human observations or an independently replicated clinical experiment.

The original first complete G04 output was downloaded from the original GitHub Actions artifact **13992304540**, not freshly recomputed for this report. Its extracted 6,022 bytes have **SHA-256 7b32e1e0fc31d82ec2d1a3c509b0304bbbb4219db2145788d05d90d87140dc00**. The official original ZIP digest reported by GitHub is **3b39aab300c62a102cd6e5b022d326e14e100cfc85171e5e413d91c0a6e02b06**. The original aggregate JSON is now archived as NEU-01-G04-P01-first-run/audit.json, with a separate archive index and an immutable checksum guard.

## New exact source counts — numbers are not independent human replicates

E is the total within-channel exact adjacent equal pairs. E00 consists of zero-zero pairs. Enn consists of equal adjacent nonzero pairs. Z is the total exact zero values; R0 is the number of separate within-channel zero runs. The independent reader checked, for each original file, that **E = E00 + Enn** and **Z = E00 + R0**.

| Original participant | State | E total equal | E00 zero-zero | Enn nonzero equal | Z exact zeros | R0 zero runs |
|---|---|---:|---:|---:|---:|---:|
| sub-02 | closed | 130,491 | **187** | **130,304** | 5,923 | 5,736 |
| sub-02 | open | 9 | **0** | **9** | 0 | 0 |
| sub-03 | closed | 152,796 | **431** | **152,365** | 11,161 | 10,730 |
| sub-03 | open | 3 | **0** | **3** | 0 | 0 |
| sub-04 | closed | 175,607 | **640** | **174,967** | 15,318 | 14,678 |
| sub-04 | open | 12 | **0** | **12** | 0 | 0 |

Across these **three selected closed recordings**, E totals **458,894**, with E00 **1,258** and Enn **457,636**. Thus **99.7259%** of *equal-adjacent-pair events* in closed files are between nonzero native numbers. These are **not** 99.7259% of the entire EEG signal, of neural state samples or of the population. In open files, the original E counts were 9, 3 and 12, with no exact zeros, hence 24 nonzero equal pairs in total. These digital values are not calibrated microvolts.

The earlier D01 result proved only **Enn >= 426,495** across the three closed files; the independent source read now gives Enn **457,636** exactly, a stronger descriptive count. No physical hypothesis or neural-entropy mechanism follows from this number. We have simply moved from an aggregate mathematical lower bound to a direct source-level count of the same digital object.

## What this can and cannot exclude

**Excluded:** an accounting explanation under which the large exact adjacent-equality counts consist exclusively of zero-zero pairs. A second independently implemented decoder reproducing the known G03 totals reduces the risk that those original totals were created by one specific vectorized counting-code defect.

**Not excluded or resolved:** interpolation or reconstruction, quantization, rounding or finite-precision effects, filtering/resampling, reference transformations, unequal preprocessing, or other source conversion stages. A single shared processing mechanism could produce both repeated zeros and nonzero repeated values. Condition-specific preprocessing from the publisher, including additional eyes-open ICA, is a substantive confound. Reusing six files neither removes that confound nor supplies an independent neural outcome.

The original BrainVision headers omit explicit physical units for all channels examined. No exact amplifier calibration or clipping threshold was established. The human sample is three purposively chosen IDs already seen in G03; 54.9 million native digital values are not 54.9 million statistically independent human observations.

## Literature and attribution

- **Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (13 September 2022)**, “A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states,” Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9. The acquisition, participant design, processing history and shared EEG data predate our project. Their dataset has multiple repeated sessions and documents condition-specific EEG processing; our G04 re-read does **not** equate the two conditions' source pipelines.
- **Brain Products GmbH, BrainVision Core Data Format 1.0**, https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/. Technical definitions of format and channel metadata; no new neuroscience result.
- **Previous project results:** frozen G03 first original archive and the retrospective D01 mathematical bound. Both informed the design and must not be recast as unseen predictions.

There is no claim of discovery of new EEG, Lempel–Ziv, information theory, number-theoretic or graph-theoretic principles. The contribution is a traceable source-level digital reproducibility check and precise integer decomposition **for these original files**, with unsuccessful runs disclosed.

## Reproducibility and claim ledger

- Protocol-only commit: 6449070c5b95e1d4bbddd2243549593d4ed85f46
- Postfailure amendment: 4b66545aa5d69bdb727b7a383c2198ec70f2f439
- Exact first fully successful source implementation: dd51387cdeae6a19eed4c42eb74a9bf9d463a3a6
- Original successful source workflow: https://github.com/DevHabito/relational-persistence/actions/runs/43327626650
- Full Python 3.11/3.12 regression: https://github.com/DevHabito/relational-persistence/actions/runs/43327626617
- Original first complete aggregate: docs/results/NEU-01-G04-P01-first-run/audit.json (6,022 bytes, SHA-256 7b32e1e0fc31d82ec2d1a3c509b0304bbbb4219db2145788d05d90d87140dc00)
- Original archive provenance: docs/results/NEU-01-G04-P01-first-run/archive-index.json

Next honest gate: a separately frozen **digital process-forensics** protocol testing nonzero repeated-value lattice/spacing, run-length clustering and condition-specific acquisition/preparation provenance, with appropriate negative synthetic controls. Even if it confirms a digital processing signature, that would **not** validate a biological rigidity theory, neural entropy or mental-health biomarker. If the source pipeline cannot be resolved, the biological interpretation stays blocked.

**Final G04 status:** INDEPENDENT_SIX_FILE_SOURCE_REPLAY_MATCH — retrospective exact-value source verification only.
