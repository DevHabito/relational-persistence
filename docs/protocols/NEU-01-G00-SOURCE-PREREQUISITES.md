# NEU-01-G00 — EEG Lempel–Ziv validity: source and prior-art eligibility gate

**Registered:** 9 November 2026. **Base:** unchanged `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8`.  
**Status:** this is an **informed, retrospective metadata-readiness protocol**: the investigator's question, 2022 publisher data description, established LZ-surrogate literature and a first 5-condition/sub-01/session1 sidecar inspection were all known before registration. Do not call the source-metadata mismatch a blind prediction or a novel finding from a preregistered experiment.

## Actual question and exclusions

Is the **within-participant difference** in scalp EEG Lempel–Ziv sequence complexity between fixed eyes-closed and eyes-open observations robust to documented signal processing, recording duration, EEG power spectrum and other confounding influences? A change in the scalar **LZc** does **not** by itself measure self-continuity, psychosis, depression, neural rigidity, information entropy production or actual thermodynamic entropy.

Existing literature already describes LZ complexity and confounding due to slow oscillations, amplitude thresholding and spectra. In particular:
- Schartner et al. (2015), DOI `10.1371/journal.pone.0133532` studies raw versus surrogate-normalized complexity in anesthesia (bibliographic identity to be separately verified before citation);
- Schartner et al. (2017), *Neuroscience of Consciousness*, DOI to be verified, and the 2019 `Level of Consciousness Is Dissociable ...` article explicitly use amplitude threshold and phase-randomised surrogates preserving spectral power;
- `Multiscale Lempel–Ziv complexity for EEG measures`, *Clinical Neurophysiology* 126(3), 2015, DOI `10.1016/j.clinph.2014.07.012`, reports a slow-frequency limitation;
- Höhn, Hahn, Lendner and Hoedlmoser (2024), `Spectral Slope and Lempel–Ziv Complexity as Robust Markers of Brain States during Sleep and Wakefulness`, DOI `10.1523/ENEURO.0259-23.2024`.
Any research claim that “phase surrogates, time normalization, and spectral confounds have never been studied” is **false**.

## Frozen P00 source and metadata scope

Primary public resource: **Wang, Yulin; Duan, Wei; Dong, Debo; Ding, Lihong; Lei, Xu (2022)**, `A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states`, *Scientific Data* 9:566, DOI `10.1038/s41597-022-01607-9`. OpenNeuro `ds004148`, original resource DOI `10.18112/openneuro.ds004148.v1.0.0`. NEMAR `on004148 v1.0.0`, dataset DOI `10.82901/nemar.on004148`. The repository `OpenNeuroDatasets/ds004148` was inspected at **`0c740d838a2c33feeec0b6e514aea323d0e65ca4`** (GitHub branch head during the 2026-11-09 review). Publisher reports 60 adults, 3 sessions, five tasks per session and 500 Hz; NEMAR catalog states **900 recordings**. This count is a **catalog statement**, not a full independently re-counted set of raw EEG files. Publisher study participants were healthy adults: do not make clinical-group claims.

Already observed before this protocol on `sub-01/ses-session1/eeg`:
- Each of five task channel TSVs lists **61 channel rows**;
- `eyesclosed_eeg.json` declares `EEGChannelCount=64`, whereas eyesopen, mathematic, memory and music EEG sidecars each declare `61`;
- sidecars report 500 Hz, `FCz` reference and five-minute recording duration; the first EEG sidecar header has a *metadata-only* discrepancy.
These are **GitHub text sidecar observations**. Actual original binary EEG bodies were **not downloaded or decoded**. The study should **not** infer that the archived EEG data have 64/61 channels until the raw BrainVision headers and sample matrices are independently checked and reconciled. The 2022 paper describes electrode reconstruction and additional ICA cleaning for eyes-open signals; compare only after provenance is understood.

Dataset full download is large (NEMAR catalog displays 93.2 GiB uncompressed, archive download approx 44.4 GiB), and source EEG binary files are git-annex/git-link style GitHub entries. P00 must not claim GitHub file listing or a text symlink establishes full raw source authentication or any full-record EEG result.

## P00 outcomes and stop rules

Audit a **fixed set of five sidecar summaries**, not all participants. Preserve the source repository commit, path, sidecar Git blob SHA and TSV blob SHA for each. Build a machine-readable summary containing only task identifiers, per-task declared EEG channel counts, channel table row counts, sampling rate, reference and duration. No raw participant EEG values, questionnaires or original recordings in the repository.

A deterministic validator reports:
- `SOURCE_SIDECAR_DISAGREEMENT_PRESENT` when any declared EEG channel count differs from companion TSV rows;
- `FIVE_SIDECARS_SELF_CONSISTENT` when they agree;
- `INSTRUMENT_FAILURE` for malformed or unexpected datasets, task sets, negative counts, impossible sample rates, duplicate tasks, inconsistent source commit or unregistered source/path provenance.
One known sidecar mismatch **must remain in the denominator**, even if another source path later reconciles it. This outcome is a **bounded metadata finding**, not a direct physiological hypothesis test.

Use synthetic negative controls for a forged full-EEG availability flag, source-commit change, duplicate task, missing task, inconsistent channel count, impossible sampling frequency, no sidecar SHA, and a `python -O` guard.

## Separate later P01 (NOT REGISTERED YET)

Only after verifying downloadable raw **one or two small selected recordings** and checking raw channel labels/sampling/duration against source metadata, register a new source-and-method protocol **before looking at any actual EEG LZc comparison outcomes**.

A candidate P01 pre-specified plan (subject to an explicit later registration): 10-second non-overlapping windows (5,000 samples at 500 Hz), one fixed EEG channel present in both tasks and all selected sessions, sensor quality/artifact and spectral matching checks, strict LZ parsing convention verified against a separate reference implementation, fixed amplitude/median threshold, phase-randomized spectrum-preserving surrogate controls with independent seeds and correct handling of reference and power spectrum, 1/f slope and theta/alpha power baselines, no leakage between sessions/subjects, fixed analysis horizon, paired confidence intervals and held-out repetition across sessions. Compare uncorrected and adjusted **same-participant** eyes-open vs eyes-closed signal features; a source issue that prevents harmonized comparison yields **SOURCE_GATE_NOT_PASSED**.

**Do not** infer that resting EEG is a psychopathy biomarker, clinical mental disorder, personal identity or thermodynamic entropy. Investigating those requires distinct independent clinical and physiological validation. The pre-existing LZ controls must be treated as strong baselines, not our discovery.

## Advancement threshold

G00 is successful when source metadata are precisely documented and their **discrepancy is neither hidden nor upgraded to signal failure**. P01 only proceeds after a separate pilot verifies real EEG bytes, reproducible channel matching and data-processing definitions. Results can be positive, null, negative or blocked. No universal scientific law is being sought.
