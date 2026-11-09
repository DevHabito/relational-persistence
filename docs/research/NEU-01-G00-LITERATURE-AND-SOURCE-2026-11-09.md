# NEU-01-G00 — Original EEG metadata and the limits of the Lempel–Ziv interpretation

**Research date:** 9 November 2026  
**Status:** metadata-only source readiness audit, **not** a human EEG LZc experiment  
**Frozen retrospective protocol-only commit:** `b0267de1c20362dc38bda0ef32d09f3d97f240a9`  
**First machine evaluation:** [GitHub Actions #42613113888](https://github.com/DevHabito/relational-persistence/actions/runs/42613113888), source head `87b6d04f35d37dad1e8b83449ec6242afa0f7f6d`  
**Original decision:** `SOURCE_SIDECAR_DISAGREEMENT_PRESENT`.

## Why we started here

The broader motivation is the investigator's *The Thermodynamics of Self*: can observations of neural complexity support a rigorously measured idea of flexible but persistent brain function? Before testing that claim, we need to answer a smaller one:

> How much of an EEG Lempel–Ziv complexity contrast between eyes-open and eyes-closed rest survives fixed window length, a validated binary encoding, artifact and recording-montage controls, and competing explanations from the power spectrum?

This question has substantial prior art and should **not** be presented as an undiscovered idea. A well-designed replication could still be useful, particularly if it exposes which measurement decisions make published LZ effects unstable. Neither a positive nor a negative scalp EEG contrast would by itself demonstrate subjective Self continuity, psychiatric diagnosis, dissipative thermodynamics or physical time emergence.

## Verified external sources and nearest relevant prior art

**Wang, Yulin; Duan, Wei; Dong, Debo; Ding, Lihong; Lei, Xu (2022).** “A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states.” *Scientific Data* 9:566, published **13 September 2022**, DOI [10.1038/s41597-022-01607-9](https://doi.org/10.1038/s41597-022-01607-9), PMID 36100589. Their source describes 60 healthy participants, three visits/session observations per participant (two roughly 90 minutes apart, the last about one month later), two rest conditions (eyes open and eyes closed), three self-driven cognitive conditions, and EEG at 500 Hz. It documents reconstruction and **different eye-artifact processing for eyes-open recordings**. Therefore EO-versus-EC is not a clean brain-state contrast until preprocessing is considered.

Public source record: [OpenNeuro ds004148](https://openneuro.org/datasets/ds004148), dataset DOI [10.18112/openneuro.ds004148.v1.0.0](https://doi.org/10.18112/openneuro.ds004148.v1.0.0), and [NEMAR on004148 v1.0.0](https://nemar.org/dataset/on004148), NEMAR DOI [10.82901/nemar.on004148](https://doi.org/10.82901/nemar.on004148). NEMAR displays **900 recordings** over 60 people, 3 sessions and 5 tasks; this audit **did not independently enumerate or decode all 900 raw signals**. The publisher release is CC0, and the NEMAR mirror lists large source storage (approximately 93.2 GB in its storage description), so a whole-dataset transfer is not required to begin.

**Classical LZ/spectral controls are not new.** “Multiscale Lempel–Ziv complexity for EEG measures” (2015), *Clinical Neurophysiology* 126(3), pp. 541–548, DOI [10.1016/j.clinph.2014.07.012](https://doi.org/10.1016/j.clinph.2014.07.012), already showed that a standard median-quantized LZ calculation can miss faster EEG components under stronger slow rhythms. The method proposed multiple scale-sensitive encodings; this directly preempts a claim of first discovering such a limitation.

**Pal, Dinesh; Li, Duan; Dean, Jon G.; Brito, Michael A.; Liu, Tiecheng; Fryzel, Anna M.; Hudetz, Anthony G.; Mashour, George A. (2020).** “Level of Consciousness Is Dissociable from Electroencephalographic Measures of Cortical Connectivity, Slow Oscillations, and Complexity.” *Journal of Neuroscience* 40(3), pp. 605–618, DOI [10.1523/JNEUROSCI.1910-19.2019](https://doi.org/10.1523/JNEUROSCI.1910-19.2019). This rat/anaesthesia analysis used **phase-randomized surrogate time series preserving spectral profiles** to separate features of complexity from spectral change. It also found that EEG complexity and some physiological activation can dissociate from behavioral recovery of wakefulness. This is important: complexity cannot simply be relabeled consciousness or subjective identity.

**Höhn, Christopher; Hahn, Michael A.; Lendner, Janna D.; Hoedlmoser, Kerstin (2024).** “Spectral Slope and Lempel–Ziv Complexity as Robust Markers of Brain States during Sleep and Wakefulness.” *eNeuro* 11(3), published 12 March 2024, DOI [10.1523/ENEURO.0259-23.2024](https://doi.org/10.1523/ENEURO.0259-23.2024). A source for spectral slope and LZc as **competing or complementary pre-existing features**, not an invention of the current project.

**2022 network complexity literature** also notes that mean/median binarization can overweight slower frequency components. See [Neural complexity is a common denominator of human consciousness across diverse regimes of cortical dynamics](https://doi.org/10.1038/s42003-022-04331-7). This reinforces the need to fix the binarization method and sample duration.

**G0 originality decision:** The general idea that LZc depends on signal processing, spectral structure or binarization **is established prior art**. Any future distinct contribution must concern a narrowly defined reproducibility finding, new data condition, rigorous mathematical limitation, or independently validated performance beyond these studies. **No originality priority is established now.**

## Actual first source audit: five verified GitHub text sidecar pairs

We inspected the **current GitHub `main`** of `OpenNeuroDatasets/ds004148`, at repository commit `0c740d838a2c33feeec0b6e514aea323d0e65ca4`, and read the five BIDS `*_eeg.json` and companion `*_channels.tsv` files at:

`sub-01/ses-session1/eeg/`

The associated original Git blob SHA for each of the ten text files and the exact paths are in [`NEU-01-G00-FIVE-SIDECAR-MANIFEST.json`](NEU-01-G00-FIVE-SIDECAR-MANIFEST.json). These are data-structure metadata, **not** electrode voltage samples. The source files were accessed and the discrepancy was **already known** before the G00 protocol was frozen. The first-run script therefore verifies a pre-inspected, pinned manifest; it is not an independent discovery on unseen data.

| Task | `EEGChannelCount` stated in original BIDS JSON | Rows in original companion `channels.tsv` | `SamplingFrequency` | `EEGReference` |
|---|---:|---:|---:|---|
| Eyes closed | **64** | **61** | 500 Hz | FCz |
| Eyes open | 61 | 61 | 500 Hz | FCz |
| Mathematical subtraction | 61 | 61 | 500 Hz | FCz |
| Memory | 61 | 61 | 500 Hz | FCz |
| Music imagery | 61 | 61 | 500 Hz | FCz |

The five sidecars report five-minute observation duration. The five channel TSVs share exactly the same Git blob SHA, but the eyes-closed EEG JSON source sidecar declares three additional EEG channels relative to the 61 listed. It is a **real text-metadata disagreement within this narrowly pinned subset**. We have **not verified** whether this represents different reconstruction stages, channels absent from the TSV, a BIDS descriptor error, or an actual difference in raw binary data. Do **not** label it corrupt EEG or repair the original file.

A second literature-versus-metadata distinction matters: the 2022 paper describes reconstructing 62 channels for 180 visit-level recordings before state segmentation. That publication-level description cannot settle the 61-versus-64 difference in the specific git text sidecars without examining actual file headers and EEG channels. No invented conversion from 64 to 61 is permitted.

## First hosted check, testing and original result

The protocol was committed alone at `b0267de1c20362dc38bda0ef32d09f3d97f240a9`. The manifest and executable deterministic metadata gate were added after it. Initial [source workflow #42613113888](https://github.com/DevHabito/relational-persistence/actions/runs/42613113888) executed **19 synthetic and corruption-guard tests** before evaluating the recorded five sidecar summaries. It reported:

`SOURCE_SIDECAR_DISAGREEMENT_PRESENT`

The reported metadata difference was **one in five task sidecars**, eyes closed **64 declared versus 61 listed**. The original first audit JSON is stored unchanged in [`NEU-01-G00-first-run/audit.json`](../results/NEU-01-G00-first-run/audit.json); its GitHub Actions SHA-256 is `cec3cd2e71c70740ed272cc383ceca53f1ebdf3a854d86932ef50702338b21d6`. The first hosted artifact ZIP digest is recorded in the separately committed [archive index](../results/NEU-01-G00-first-run/archive-index.json). The source outcome is a **metadata gate result**, not a neuronal complexity result.

The controls reject invalid source IDs, changed source commit, malformed task/path/sha, impossible or inconsistent sample frequency, altered reference and duration, and false claims that full EEG signals or all 900 recordings were audited. A separate invented correction fixture returns `FIVE_SIDECARS_SELF_CONSISTENT`, demonstrating the gate is not hardcoded to reject. Optimized Python does not bypass guards. Full repository regressions are evaluated after the final documentation and provenance commits; no Lean mathematics was introduced here.

## Next smallest independently useful stage: the raw one-recording audit

**NEU-01-G01**, requiring a **separately registered** procedure before raw-result inspection:

1. Pick a fixed original subject/session and **both resting conditions**, eyes closed and eyes open, with their exact repository source revision and paths. Retrieve the true source BrainVision `*.vhdr`, marker file and `*.eeg` payload through a verified data-provider route, not the little git-annex/symlink text entry as if it were voltage samples.
2. Record original file byte lengths and SHA-256, signal sampling frequency, real channel names/count, reference, units, recording duration, format/endianness, clipping/nonfinite values and allowed usable periods. Test whether the 64-versus-61 source-sidecar disagreement can be explained **without changing original data**.
3. Compare the **intersection of verified original electrode names**, not channel number alone. Examine reported eyes-open ICA processing separately; do not treat eyes-open and eyes-closed sensor construction as identical if documentation shows otherwise.
4. If this cannot be verified, stop with `RAW_EEG_SOURCE_NOT_YET_ELIGIBLE`, rather than publish a physiological effect from unverified files.

Only after G01 should a distinct **NEU-01-P01** define the exact LZ76 algorithm/reference implementation, median vs amplitude threshold, precise window length and rejection rules, pre-registered phase-randomized spectral null, time-scale/power/spectral-slope baselines, paired participant and retest splits, primary outcome, uncertainty and null criteria **before any EEG contrast is computed**. The first real test could use one verified recording for feasibility, but subject-level inference would require sufficiently many independently held-out individuals and repeated sessions.

## Scientific interpretation

This source gate discovered nothing about a particular person's identity, pathology, thermodynamic entropy or psychological rigidity. It did establish a **specific reproducibility prerequisite** that is easy to ignore when software blindly combines channels from two conditions. The prior methods for complexity normalization are established, so claiming an original LZ index today would be premature.

The scientific value here is modest but real: we now know an explicit data-quality question, its exact immutable provenance, a testable failure condition and a carefully bounded next step. **The research goal remains accurate domain-specific answers, not a universal law.**
