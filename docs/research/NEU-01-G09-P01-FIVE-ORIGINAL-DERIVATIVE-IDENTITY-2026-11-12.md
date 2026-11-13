# NEU-01-G09-P01 — All six examined BIDS-root / EEGLAB-derivative matrices are numerically identical

**12 November 2026; original GitHub runner early 13 November UTC.** This is a bounded, retrospectively motivated **public EEG file-provenance audit**, not an independent biological replication. G08-D03 had already proved exact IEEE float32-to-float64 sample identity for the first sub-02 session1 eyesclosed source/derivative pair before G09 was designed. G09's original protocol-only commit **090efb85c4869ded1b968c9af883662a7eb0902d** preselected **all five remaining** candidate pairs and fixed identical source checks and equality criteria before any of their derivative binary bodies were read.

## Source question and result

Do the five published OpenNeuro ds004148 v1.0.0 derivative .set objects that correspond to the five other previously examined G03/G04 source recordings actually contain the same numeric array after exact widening of the original BrainVision float32 values?

**Yes, for all five.** The first source workflow **#43338356181** authenticated each original BIDS .eeg/.vhdr and BIDS channels.tsv against fixed source identities, and independently downloaded and authenticated each formerly unexamined derivative .set against its original Git-annex 73,824,136-byte size and known MD5. Each original/derivative pair passed the exact same 61-label order, 500-Hz sampling, 150,000 relative time-coordinate grid (0–299,998 ms) and 61x150,000 matrix layout gates, **without fuzzy channel match, time shift, re-reference, gain scaling or metadata substitution**.

A previously frozen G08-D03 direct IEEE comparison was then applied to every original sample in each five-pair set. All **45,750,000 newly compared positions** were exactly numerically equal **and** equal in canonical IEEE64 bit patterns after widening source float32 samples. No numeric or 64-bit pattern mismatches occurred. Including the previously independently audited first sub-02 eyesclosed pair, **54,900,000 of 54,900,000 original/derivative positions** in the six previously selected participant/state recordings have identical native numeric content across the two published representations.

| Original participant | State | Exact numeric matches / positions | Canonical IEEE64 mismatch | First-verified derivative .set SHA256 |
|---|---|---:|---:|---|
| sub-02 | eyesclosed (prior G08-D03) | 9,150,000 / 9,150,000 | 0 | 2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359 |
| sub-02 | eyesopen (G09) | 9,150,000 / 9,150,000 | 0 | 946165038f5d86fd3542a8aff15c5321db25b29d831b48fa1e21c2dde9b31a9a |
| sub-03 | eyesclosed (G09) | 9,150,000 / 9,150,000 | 0 | 9962d36ce0e1693a1c0386cb50a3ced4a50b70c53f7527ed5d6b7ea25926de2e |
| sub-03 | eyesopen (G09) | 9,150,000 / 9,150,000 | 0 | 37ac0b3e7135172f25ecc9c382e94bbda475f26fcd6ecd7177a948dbc72c86f9 |
| sub-04 | eyesclosed (G09) | 9,150,000 / 9,150,000 | 0 | 61864e29228defe57bd9c6ba1a11fc525dc4518fdc4bae8af23edc5eda24c657 |
| sub-04 | eyesopen (G09) | 9,150,000 / 9,150,000 | 0 | bdbdd5a823caacf444971d309376f994d7365a98df0096c52e9b7f25efc62696 |

The canonical double SHA256 content hashes for each BIDS-widened and derived data array also agreed within each pair. These are **not** SHA-256s of the original entire .eeg and .set files; those native container bytes and formats differ. We did not upload or commit any original signal array.

## Valid fixed negative controls

The same prespecified one-second circular-shift and reversed-channel controls were executed without optimizing them. Their exact numeric match counts were:

| Pair | +500-frame shift | Reversed 61 channels |
|---|---:|---:|
| sub-02 eyesopen | 1 | 150,000 |
| sub-03 eyesclosed | 17,436 | 155,582 |
| sub-03 eyesopen | 2 | 150,000 |
| sub-04 eyesclosed | 17,233 | 156,356 |
| sub-04 eyesopen | 1 | 150,000 |

The reversed-order control leaves the middle of 61 channels unmoved; its minimum 150,000 matches are therefore expected and **must not** be described as accidental correspondence. Differences between shifted conditions in this control reflect original numeric time-series properties but are not tests of neuronal state, independent samples or statistical significance.

## What we can now exclude, and what we cannot

Across exactly these six fixed source/derivative pairs, the substantial native integer/repetition differences between eyesclosed and eyesopen seen in G03–G05 **did not arise from any change in the numerical EEG matrices between these published BIDS-root files and their matched EEGLAB-derived representations**. The arrays are numerically identical after the specified type widening. This excludes a causal explanation that depends on a numerical operation being performed **solely during the transition between these two published arrays**. It does **not** identify whether different recording, conversion, preprocessing or ICA stages occurred **before either file was published**.

The publisher's BIDS root dataset is labelled raw and uses EEGReference FCz metadata; original BIDS channels.tsv declares uV (despite blank per-channel unit slots in original BrainVision headers). The separate derivative directory is described as pre-processed data, with individual MATLAB metadata declaring reference common and double storage. Those metadata descriptions are not evidence that corresponding published sample numbers differ. G09 does not resolve the exact history that produced the labels, nor imply authors knowingly labeled anything incorrectly. Exporting an already processed intermediary into two containers, reusing a common prior signal, or bookkeeping conventions are among several possibilities, not established explanations.

There are **900** original BrainVision root files and **900** derivative .set pointers in the pinned OpenNeuro source tree. This audit checked exactly six pairs, **not all 900**: **894 pairs remain untested**, and the three subject IDs were already used in original G03 research. We must not treat these 54.9 million digital sample values as 54.9 million independent human observations, or interpret the dataset-file equivalence as a physiological brain rigidity effect, a new statistical/thermodynamic law, Lempel-Ziv complexity or a clinical diagnostic biomarker.

The defensible research contribution is a **reproducible, byte-authenticated, exact-value dataset provenance result for these six selected pairs**. Whether this specific identity observation is novel to the published literature has not been established by a systematic priority search. We should not claim discovery precedence merely because we independently checked the source.

## Honest chronology, source references and next gate

- Original G08-D03 one-pair result: https://github.com/DevHabito/relational-persistence/actions/runs/43337338166 (prior known result before G09 frozen protocol).
- Standalone G09 protocol commit: **090efb85c4869ded1b968c9af883662a7eb0902d**.
- G09 original implementation commit and first source run head: **926a2665d9f9fffffe98fad752496572cdd9fc0f**.
- First G09 source workflow: https://github.com/DevHabito/relational-persistence/actions/runs/43338356181, **eight targeted synthetic/adversarial checks passed before source access**. Every one of the five fixed source/derivative pairs was eligible and completed; no source pair was omitted.
- Full G09 source-commit regression: https://github.com/DevHabito/relational-persistence/actions/runs/43338356082, **980 passing tests on Python 3.11 and 980 passing tests on Python 3.12**, as verified from the original job logs.
- Original G09 first aggregate-only Actions artifact: **13997394683**. Its independently recovered untouched audit.json was **15,338 bytes**, SHA256 **bb3350806c1b86a886f2e79a47b52f967fc34176d598c60742b4b4d1be9dfdba**, matching original job SHA log, and is archived with an index and integrity tests in docs/results/NEU-01-G09-P01-first-run/.
- Upstream fixed public source: https://github.com/OpenNeuroDatasets/ds004148/tree/0c740d838a2c33feeec0b6e514aea323d0e65ca4

Data origin: Yulin Wang, Wei Duan, Debo Dong, Lihong Ding, Xu Lei (2022, 13 September), A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9. Format and pipeline context: EEGLAB Consortium, Data Structures https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html; Brain Products GmbH, BrainVision Core Data Format 1.0 https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/.

Definitions: root/derivative pair = two published format representations sharing subject/session/condition labels; direct identity = numerical and IEEE64 bitwise sample equality after root float32->float64 widening, NOT identical original container bytes; reference metadata = a source-field value, NOT confirmed numerical transform; nonselective fixed-source audit = all five prospectively listed as files-to-check after the prior one-pair observation, not an independent recruited cohort. No central relational-persistence theory, physical time emergence or disease inference has been validated.

**Recommended next step:** a focused, respectful source-data provenance clarification with dataset maintainers, supported by the six exact pairs, plus a broader **pre-registered selection across other sessions/participants** if scientific replication warrants it. Do not uncritically scale to all 900 without a source question and controls, and do not interpret conditional numeric preprocessing differences as biological until recording-to-file lineage is documented.

**Recorded G09 status: FIVE_PAIR_DIRECT_IDENTITY_CENSUS_COMPLETE, 5/5 exact new pairs; combined G08/G09 6/6 exact pairs.**
