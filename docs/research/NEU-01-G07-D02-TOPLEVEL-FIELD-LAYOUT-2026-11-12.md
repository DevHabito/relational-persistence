# NEU-01-G07-D02 — Original derivative MAT field layout independently resolved

**12 November 2026 / 13 November UTC GitHub runner.** This is an explicitly **post-result structural audit** of the **same one** G07 derivative file, performed only after the original G07 parser reported that no top-level variable EEG existed. The first G07-P01 result remains an immutable, authentic but metadata-not-parsed outcome. No new participant, EEG recording or neurophysiological experiment was introduced.

## Why the first parser did not find EEG

The original G07 first-run read only a top-level MATLAB variable called EEG; it returned EEGLAB_STRUCT_MISSING. Instead of pretending this was a negative EEG result or silently changing the earlier code, we frozen-registered G07-D02 in a separate protocol-only commit **7bc2b1e73032a290748fdb38326974771a6f8244**, after observing the original parser result. This follow-up asked for **the actual top-level MATLAB variable layout**, not amplitudes or a biological effect.

The source was exactly the original public derivative sub02_01_EC.set from pinned OpenNeuro ds004148 v1.0.0, 73,824,136 bytes, Git-annex MD5 2ba3c01f752799634414e2142544fd9b and previously authenticated SHA256 **2aa539bdbc6f8061865c029ba7b6d069383c52c4a622254e0c3fa2dbb4f11359**. The code checks the immutable original G07 P01 JSON hash before a new source read.

The first original D02 workflow **#43333636930** at source head **49cb81125a212da5a6a01f482e7707ea1ae6d8fd** passed six synthetic/adversarial controls before the original source download, reauthenticated the same one publisher binary, then used scipy.io.whosmat to inspect MATLAB field names/dimensions/classes **without loading its EEG amplitude matrix**. A separate restricted loadmat call read only allowed scalar metadata variables and did not request the data variable.

## Exact observations from original derivative metadata

| Property | Observed original derivative .set | Prior root BIDS BrainVision metadata |
|---|---|---|
| Channel count | **61**, scalar nbchan | 61 |
| Samples per channel | **150,000**, scalar pnts | 150,000 |
| Trials | **1** | No asserted matching EEGLAB trial concept |
| Sampling rate | **500 Hz**, scalar srate | 500 Hz |
| Data matrix | MATLAB top-level variable **data**, shape **61 x 150,000** | Original frame-major 150,000 x 61 IEEE float32 |
| MATLAB numeric class | **double** for data matrix (normally 64-bit) | Native IEEE_FLOAT_32 |
| Reference field | **common** | BIDS sidecar EEGReference **FCz** |
| Channel metadata | chanlocs top-level struct, shape 1 x 61 | BIDS channel list and header separately verified |
| Time metadata | times variable, shape 1 x 150,000, class double | G03/G04 did not infer exact calibration/alignment |
| Processing history | history field is present but MATLAB char dimension **[0]**; no meaningful script content established | No independently documented per-recording processing history |

The original MAT file had **42 top-level variables**; **20** permitted standard EEGLAB field names were disclosed with their types and dimensions, with the remaining 22 names explicitly omitted. The MATLAB variable data was identified structurally but **no individual EEG amplitudes were read into an array for analysis, reported or archived**.

The source status was exactly **TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED**; this makes the earlier top-level EEG struct assumption a **software format mistake**, not a claim that the derivative was missing or corrupted.

The difference between original root metadata reference FCz and derivative metadata reference common is **consistent with** a changed reference representation, and the change from source float32 to derivative double is a confirmed change of numeric storage type. Neither independently establishes the full sequence of transformations or the source-to-derivative sample mapping. Equal dimensions and sampling rate are **necessary but insufficient** for a valid waveform-level comparison. We have not shown identical sample time origins, electrode order, scale or units.

## Original source chronology and engineering checks

- G07-P01 first source study, preserving the parser obstacle: https://github.com/DevHabito/relational-persistence/actions/runs/43332821093.
- G07 general-regression deficiency was traced to undeclared SciPy import. Original failures #43332820847 and #43333083443 were preserved. A transparent dependency-only correction was documented before this D02 branch and does not edit the first G07 data.
- G07-D02 protocol-only commit: **7bc2b1e73032a290748fdb38326974771a6f8244**.
- G07-D02 first original source workflow: https://github.com/DevHabito/relational-persistence/actions/runs/43333636930, with **six** pre-source tests passed and first field-layout result resolved.
- Full source-commit regression: https://github.com/DevHabito/relational-persistence/actions/runs/43333636782, **932 Python tests on 3.11 and 932 on 3.12**, based on original inspected job logs.
- Original first-run metadata JSON: docs/results/NEU-01-G07-D02-first-run/audit.json, **4,008 bytes**, independently verified SHA-256 **5bf3dd61678b267c4997ed56328ae1c8183389d44e1c21910b315d59f8e7cef9**, original Actions artifact **13996481794**.
- No original EEGLAB file, sample values, channel names, private MATLAB variables or history text was committed.

## Literature, glossary and next falsifiable gate

Source dataset and acquisition: Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (13 September 2022), A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9; original file tree https://github.com/OpenNeuroDatasets/ds004148/tree/0c740d838a2c33feeec0b6e514aea323d0e65ca4. Their methods include reference changes and filtering/ICA for processed signals, but our archival and source tests do not identify the precise operation responsible for the numeric repeat contrast.

Dictionary: top-level MATLAB variable means a named matrix/struct stored directly in the file, not nested inside EEG; data shape is matrix dimensionality only; double is the declared MATLAB numeric class, not a calibrated physical unit; common reference is a metadata value, not proof of the algorithm or its order; full source/derivative alignment needs independent sample, time and channel mapping.

**Next controlled step:** register a matched-pair eligibility test comparing the exact original source and derived sample grids and channel order with explicit scaling and time-axis checks, while prohibiting post-hoc waveform warping. Only if that succeeds may the earlier numeric-count differences be decomposed across source and derivative representations. Even then, comparing a single original/derived pair cannot isolate each individual preprocessing operation without intermediate authenticated stages.

**Outcome: TOPLEVEL_EEGLAB_FIELD_LAYOUT_RESOLVED.** No biological, thermodynamic, mathematical originality or clinical conclusion is inferred.
