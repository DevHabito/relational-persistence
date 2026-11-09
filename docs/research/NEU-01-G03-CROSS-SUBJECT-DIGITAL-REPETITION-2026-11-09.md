# NEU-01-G03 — Three additional original EEG pairs reproduce the digital-equality direction

**Date:** 9 November 2026  
**Scope:** OpenNeuro ds004148 v1.0.0, session 1; original stored IEEE float32 numbers only  
**Evidence level:** Complete descriptive source-file census in three deliberately selected new participants, not an EEG biomarker or population effect

## Question and prospective record

G02 previously found a large excess of exactly equal adjacent digital samples in the original eyes-closed versus eyes-open recordings for subject 01. I asked whether this *source-file numerical representation pattern* recurred in the next three participant IDs. The older G02 result and publisher information about condition-dependent processing were known before this study; this is not a blind clinical study.

The [G03 protocol](../protocols/NEU-01-G03-CROSS-SUBJECT-DIGITAL-REPETITION-2026-11-09.md) was committed on its own as **ed0d77e5a3812ec1931ec6b7e3dbdcc0e87777b3**, before any new G03 participant EEG amplitudes were decoded. It fixed sub-02, sub-03, sub-04; session 1; eyesclosed/eyesopen; 61 channels, 150,000 samples/channel; all six original annex keys and byte lengths; and a strict all-three-positive *descriptive* sign rule. The manuscript and code cannot redefine the source population after seeing outcomes.

After that protocol commit, I implemented the reader and synthetic tests. A hand-counted synthetic fixture contained six equal adjacent pairs rather than the expected five; its test expectation was corrected in **e937c9dede5956ce1f79a184daa12ad52a30f08e before any G03 EEG amplitude reading**. This was a test-oracle transcription error, not a source-result change.

## Original execution and provenance

[First source workflow #42657980659](https://github.com/DevHabito/relational-persistence/actions/runs/42657980659) ran at exact head **f8ab6bd59e4b1cbe26e6322a4f83a4c08212df04**. The workflow proved the protocol was an ancestor of its implementation, passed **19 synthetic/adversarial tests before accessing original G03 EEG data**, authenticated all six original source records, and completed aggregate output and archive upload. Both original header and binary objects were checked against the source's recorded git-annex MD5E keys and exact lengths. The six ordered channel TSV companions matched the published Git blob.

The original first-run JSON was downloaded from the actual hosted artifact ZIP, extracted and separately SHA-256-checked. Its **10,117 bytes** have SHA-256 **b142e6b0b0d03e1bd6167fba1a3d265bf3d5efd485e8389474f882955bf8195c**. That original JSON is preserved unchanged at [first-run audit.json](../results/NEU-01-G03-first-run/audit.json). The original GitHub Actions artifact ID is **13692862537**; GitHub reports its distinct ZIP digest as **9967077b76c2386ac9e5d6ade68ce7e0541dacf4ae67db1f51167f468c5e1478**. The [archive index](../results/NEU-01-G03-first-run/archive-index.json) records chronology and limitations.

[Full regression #42658104122](https://github.com/DevHabito/relational-persistence/actions/runs/42658104122) on the original implementation/workflow head reported **851 passing tests in Python 3.11 and 851 in Python 3.12**. The later archive hash check is retrospective and not counted among the pre-source 19 tests.

## Six complete original signal censuses

Each original recording contained 9,150,000 float32 values, of which all were finite; no values, channels, or recordings were discarded. The exact within-channel adjacent denominator was 9,149,939 per recording, and 54,899,634 across all six. These are not independent biological replicates.

| Participant | Eyesclosed equal pairs | Eyesopen equal pairs | Closed minus open | Eyesclosed exact zeros | Eyesopen exact zeros |
|---|---:|---:|---:|---:|---:|
| sub-02 | 130,491 | 9 | +130,482 | 5,923 | 0 |
| sub-03 | 152,796 | 3 | +152,793 | 11,161 | 0 |
| sub-04 | 175,607 | 12 | +175,595 | 15,318 | 0 |

The primary preregistered verdict was **DESCRIPTIVE_DIRECTION_REPLICATED_IN_ALL_THREE**: 3 positive signs, zero ties, zero reversals. Secondary exact-zero differences also had 3 positive signs, but they are *not independent biological corroboration*.

The three equal-pair rate differences were **1.426, 1.670 and 1.919 percentage points** of eligible native-number transitions, respectively. This is not a confidence interval. All 61 channels of each eyes-closed recording had at least one repeat, versus 7, 3 and 10 channels in the corresponding eyes-open recordings. Eyes-closed median per-channel equal-pair counts were 2,048, 2,275 and 2,828, versus median zero in each eyes-open recording. The source representation pattern is distributed across the eyes-closed channels rather than coming from a single channel.

All six original headers declare numeric resolution 1 but omit a physical unit on each of 61 channels, for **366 missing physical-unit declarations**. The source does not independently validate a conversion to microvolts, amplifier clipping, EEG artifact freedom, or physiological amplitude.

## Scientific interpretation — strictly limited

This answers a small *technical replication* question. The same direction of native float32 repetition recurs in three additional selected participant pairs. The data **do not establish** whether this is caused by interpolation, ICA, acquisition software, file conversion, reference handling, other preprocessing, or physiology. The publisher describes additional ICA processing for eyes-open recordings; that fact is a potential confound, **not a mechanism proved by G03**. The files are processed source records, not independently authenticated equivalent unprocessed amplifier outputs.

I have not computed Lempel–Ziv complexity, frequency spectrum, phase surrogates, aperiodic slope, neural entropy, an independent functional brain outcome, psychiatric diagnosis, the subjective Self, or physical entropy production. There is no confirmatory population-level p-value: only **three selected new participant pairs** were tested, and millions of within-subject samples cannot be counted as millions of human replicates. A large ratio in digitally repeated values is not itself biological rigidity or a discovery about consciousness.

An independent simple-loop oracle checked synthetic fixture counting against the production vectorized NumPy method. **A second implementation has not yet independently re-downloaded and counted the complete original six EEG signals.** Archive integrity tests prove preserved file identity, not source-level independent replication. This is an explicit next gate.

## Established literature and scientific originality boundary

- **Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (13 September 2022).** “A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states.” *Scientific Data* 9:566. [DOI 10.1038/s41597-022-01607-9](https://doi.org/10.1038/s41597-022-01607-9). The original dataset and its condition-dependent processing, including additional eyes-open ICA, precede G03.
- **Brain Products GmbH (18 February 2022, documentation updated 4 June 2025).** [BrainVision Core Data Format 1.0](https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/). Establishes the distinction between stored EEG data and original channel metadata.
- **Dinesh Pal and colleagues (2020).** “Level of Consciousness Is Dissociable from Electroencephalographic Measures of Cortical Connectivity, Slow Oscillations, and Complexity.” *Journal of Neuroscience* 40:605–618. [DOI 10.1523/JNEUROSCI.1910-19.2019](https://doi.org/10.1523/JNEUROSCI.1910-19.2019). An earlier cautionary neuroscience comparison; not an explanation of our source-file counts.

This is a targeted literature check, not a comprehensive novelty audit. I make **no claim** that exact-equality analysis, ICA confounding or spectral-complexity controls were discovered here. The G03 contribution is a bounded archived technical census with a predeclared directional test, not a new physiological theory.

## Decision and next gate

**Observed:** three new preselected pairs reproduce the direction seen in the already-known first participant. All 54.9 million native stored numbers passed the finite-value census, and frozen file identities matched. The protocol's descriptive criterion passed.

**Unknown:** whether the source-file representation difference originates at acquisition, filtering, reconstruction, ICA or conversion; whether it persists across sessions under independently frozen selection; and whether any properly calibrated, spectrally controlled LZc metric predicts an independently measured brain-function endpoint.

**Next scientific gate:** independently recount the identical authenticated original G03 source using a separately written reader and investigate the publisher's preprocessing provenance. This first replication population is now seen; a new human-population inference needs a new prospective source selection. Do not treat the present result as a clinical biomarker, a physical entropy observation or proof of an underlying theory of identity.

No G00/G01/G02 original artifact or main-branch result was rewritten.
