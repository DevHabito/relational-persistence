# NEU-01-G11-P01 — Sensor-level alpha phase relationships across two resting EEG sessions

**Protocol-only registration — 17 November 2026. No G11 original waveform files have been downloaded or decoded as part of this study. No G11 connectivity or identification result exists at this registration.**

## Question and evidence level

Can a fixed, untrained, non-zero-lag **sensor-level** alpha-band phase-relationship descriptor of resting eyes-closed EEG recover participants across two published visits, and does its reproducibility exceed a separately specified, per-channel alpha-power descriptor?

This is an **exploratory file-based test–retest methodology study** using public EEG. The declared measure is one operational candidate for relational-pattern stability. It is **not** functional persistence after intervention, independent recording replication, a test of identity or consciousness, validated causal connectivity, entropy production, or physical emergence. Repeated digital arrays in the G08–G10 source/derivative audit must never be used as artificial test/retest observations.

## Why this is not a novelty or priority claim

Phase-based EEG connectivity and its test–retest reliability are well established. Existing articles include Vinck, Oostenveld, van Wingerden, Battaglia & Pennartz (2011), doi:10.1016/j.neuroimage.2011.01.055; Hardmeier, Hatz, Bousleiman, Schindler, Stam & Fuhr (2014), doi:10.1371/journal.pone.0108648; The effects of spatial leakage correction on the reliability of EEG-based functional connectivity networks (2024), doi:10.1002/hbm.26747; Dominicus et al. (2025), doi:10.1038/s41598-025-23662-z; Graff et al. (2026), doi:10.1162/IMAG.a.1245.

The 2024 spatial-leakage study explicitly warns that stable sensor/source artifacts can increase test–retest identification without improving biological validity. The 2026 dense-sampling study reports that reliability can depend strongly on the choice of measure and acquisition duration. The current public dataset's acquisition-to-publication preprocessing history remains uncertain for the examined representations, including differences previously described for eyes-open data. For that reason G11 uses **eyes-closed only** and does not interpret subject matching as a neural mechanism.

## Selection chronology and frozen source

The six G08/G09 and eight G10 source/derivative pairs were fully examined before G11 was designed. None of the 12 G11 participants (`sub-10` through `sub-21`) was part of that prior 5-person cohort. Their selection is **deterministic and purposive**, not randomly sampled. The OpenNeuro ds004148 v1.0.0 Git snapshot at `0c740d838a2c33feeec0b6e514aea323d0e65ca4` was inspected for these 24 BIDS-root `.eeg` and companion `.vhdr` Git-annex pointers **before this registration**. Each pointer advertises a 36,600,000-byte EEG binary or 1,122-byte header. The following hashes are publisher **annex pointer MD5 claims**, not independently downloaded file-body measurements at freeze time.

All 12 subjects are included, in the exact table order. Each contributes session1 and session3, **eyesclosed only**. Filename convention: `sub-SS/ses-sessionN/eeg/sub-SS_ses-sessionN_task-eyesclosed_eeg.eeg` and the matching `.vhdr`, with N=1 or 3. Do not substitute a different task, session, file, subject, source mirror or derivative object. No participant is eligible merely because a publisher pointer exists.

| Subject | Session1 EEG MD5 | Session1 header MD5 | Session3 EEG MD5 | Session3 header MD5 |
|---|---|---|---|---|
| sub-10 | 6b9da1894e9246ce2998c10e904bc14f | bb7197d07b96ca443b866e154442290b | 5febbf0f7d8c15456c317ef9a20d3d83 | ed7a2d3b1668ea19d9ccb3ac7a408d23 |
| sub-11 | 717a82a7548d09acd9cdbd83efe73160 | cfeb3b880318af39e62d5122e5fec26b | 2f899fd3527f9238229d4c0c271049d6 | 90a1aafa9a590103f67bb440b5fd0eee |
| sub-12 | 1c11a62afad771f104c210041c801bbe | 6fe144389930c9ea71d6aa799aa213eb | 5a08adc495eb376700265cc19bf9cc73 | cf4fb77536d837570dc4e78ab6655705 |
| sub-13 | 61c78afc952f892746c87f7d3d6d0947 | d26c2a4cb98b75c0b603346688eec734 | d5d2d5291bdd55cfeb0eaf280f5b1620 | e8ce7cdc00fb19740fe512a747ec4fb1 |
| sub-14 | 711d3ca94c501898331d6553bb81fa9c | 8a674c19d6f6dfa5fa405e107e9fa9ce | c0e46c2cb5036244dbc034a48b4700e1 | 543597cc3bd4d79c3ea3c7e4fe4feb6c |
| sub-15 | a82f3420a7a2298c8d12c3cfcb4895b9 | d7323b6025c212ff4b1ce3c93edb21ad | 4d94ced309530fa4ad1a472b6e618890 | d50ecbe6e2a11c68793746bd2f6cc737 |
| sub-16 | 7bbd12e66d8820b23fac8da9bd200adc | 711ee2872336808ea13dea98a3cd6e48 | b1215dbebb1aa8e4a305fc8efdf16cce | eb2dc175ce062071941a8c79897261a1 |
| sub-17 | 404476455862074e65e72ddd3c746522 | 311edadbbdb92075856848107b458acd | 78649972f0bcb66d1b441af040185453 | 1d94e8a249a6b88def1ce318fe5eb5bb |
| sub-18 | 7c572bd9eb0692fd7ef684c16cc9322f | cccb0d0a9d79a1719890ac1b20bb1da6 | 51eda67e8e011e5c84dc94d3e133e34a | 13913715b5f5e1fe671c0974a297609b |
| sub-19 | 5bde6724942dfe695c974d5f987fd975 | 075850b8e62a4c1e1d2d2a6a7d38c888 | e00faf74e8e98ee4f46df67c250f90b4 | 75eec84f86a2d3ef16c924e45bf56883 |
| sub-20 | 8207cb27f445156ad24c9e98a520386e | 3b07675b71ee970e0da20caee1ef16f7 | 7c1aa0dd7165b9315c054b866f894aad | e4dbffbd58b83852f419e7fa74369807 |
| sub-21 | fdd3cdff00b1b8b5d026e8dcabb313ba | aa6d7e1c3a083bb488fd197419cd7153 | 4c5f2b2aae18d426e728355dc3b24a94 | 267a8e017cabb08925ee5a242b2efc73 |

## Source and eligibility gates before signal analysis

1. Run synthetic/adversarial tests **before any G11 signal I/O**, including registered-pair/order rejection, changed hash or size, redirects, wrong header filename/session/montage, invalid dtype/shape, all-zero channel, NaN/Inf, noninteger epoch count, wrong FFT band, zero-variance fingerprint, cross-subject label swap, gain-invariance control and deterministic permutation labels.
2. Pin and verify existing G10 first-source archive checksum and G10 scope without interpreting its 14 digital duplicate pairs as new biological observations. Source-read implementation must commit separately after this protocol-only freeze.
3. Obtain only the 24 specific original published BIDS-root BrainVision headers and EEG binaries from `https://s3.amazonaws.com/openneuro.org/ds004148/`, with URL exactly derived from frozen paths. Reject redirected or different-URL responses; enforce 45-second per-request network timeouts, exact length bounds, and full-body MD5 against the frozen publisher pointer before using a file. Compute independent SHA256 of each downloaded file body and retain only digest/aggregate metadata. One record is processed and disposed before downloading the next; never upload original waveform arrays.
4. Require a header declaring `DataOrientation=MULTIPLEXED`, `DataFormat=BINARY`, `BinaryFormat=IEEE_FLOAT_32`, `SamplingInterval=2000`, `NumberOfChannels=61`, appropriate session-specific DataFile/MarkerFile and exactly ordered 61 unique channels. The 61 ordered normalized channel names must equal the previously observed fixed source label-list SHA256 `0eb9d03a6f1c62af87f95e8de05d9a39632529208c4e8c1be945f809f77d9b99`. All 150,000×61 native float32 values must be finite, and every channel must have positive alpha spectral energy. No floating-point calibration to physical microvolts is claimed.
5. Record all 24 source rows whether eligible or not. **A single inaccessible, unauthenticated or ineligible record makes the prespecified 12-person identification analysis INCOMPLETE.** Do not select the remaining participants, infer absent measurements or loosen gates. Source-specific metadata inconsistencies must be reported separately rather than repaired.

## Primary fixed alpha-band fingerprint

For each eligible original 300-second recording, decode `<f4` as exactly 150,000 time-ordered rows × 61 channels. Partition into **150 nonoverlapping 2-second epochs** of 1,000 samples (all data used). For each epoch and channel subtract that epoch's mean, multiply by the symmetric Hann window `np.hanning(1000)`, and compute real FFT with NumPy `rfft`. Frequencies are `rfftfreq(1000, 1/500)`, and select **8 ≤ f ≤ 12 Hz inclusive**, i.e. exactly nine bins at spacing 0.5 Hz.

Let `X[e,f,i]` be the complex Fourier coefficient for epoch e, selected bin f and channel i, in that fixed order. Let `P[i]=Σ[e,f]|X[e,f,i]|²` and `C[i,j]=Σ[e,f] X[e,f,i] conj(X[e,f,j])`, with sums over all 150 epochs and all nine selected bins. Define the **fixed pooled-band imaginary coherency magnitude**

[
G_{ij}=left|\operatorname{Im}\frac{C_{ij}}{\sqrt{P_i P_j}}\right|
quad (i<j).
]

This is a declared pooled-band imaginary-coherency **summary**, not an assertion of an original wPLI estimator, network directionality, phase delay or causal interaction. There are exactly 1,830 ordered upper-triangle entries for 61 sensors. No threshold, graph sparsification, sign selection, channel fitting, source localization or per-person parameter adaptation is permitted.

**Baseline (spectral only):** the ordered 61-vector `S_i=log(P_i)`. This shares the same epochs, FFT and 8–12 Hz bins, and represents each channel separately without pairwise phase relations. Do not normalize it with information from a different session.

**Negative surrogate:** independently permute the 150 epoch indices *for each sensor* of the saved complex EEG Fourier coefficients, using `numpy.random.default_rng(1101 + 10*participant_number + session)` and fixed channel iteration order. Recompute G exactly once per session from shuffled epochs, keeping each channel's full set of complex Fourier coefficients and power `P_i` identical, but disrupting synchronized cross-sensor epoch correspondence. This is a **single diagnostic** (not a distributional significance test) and does not remove persistent nonphysiological sensor artifacts or prove source interactions.

The absolute imaginary coherency is invariant under independently multiplying each sensor by any positive scalar when energy is nonzero; verify this on synthetic data before original I/O. This does not make the measure reference-invariant or immune to all forms of volume conduction.

## Prespecified comparison and null

Arrange session1 and session3 records in **exact subject order** sub-10, …, sub-21, without changing rows for signal or metadata quality. For each feature family (G, S and shuffled-G), form a **12×12 Pearson-correlation similarity matrix** between the session1 and session3 feature vectors. Reject a constant or nonfinite feature vector rather than arbitrarily define its correlation.

Primary descriptive contrast for G:
[
D_G=\frac{1}{12}\sum_{i=1}^{12}M^G_{ii}-
\frac{1}{132}\sum_{i\neq j}M^G_{ij}.
]
Also record exact per-row subject identification accuracy, counting a match only if the true paired session3 record is the unique highest similarity in its row; ties **do not** count as matches. Recompute the same D and accuracy for the spectral S and shuffled-G diagnostic, with no training or hyperparameter fit.

Permutation reference for the primary G statistic: use NumPy `default_rng(1101)` and 20,000 independent uniformly random permutations of the 12 session3 subject indices. For each permutation compute the corresponding mean diagonal-minus-offdiagonal D, with the 12×12 G similarity values otherwise fixed. Use the one-sided Monte Carlo reference `p=(1 + #permuted D >= observed D_G)/(20001)`, with exact comparison and no p-hacking. Fixed threshold p<0.05 is an exploratory evidence label, **not** proof of neuronal identity or generalization.

The only question asked of the per-channel spectral baseline is whether G supplies **any descriptive increment** in matching accuracy and D, i.e. whether `accuracy_G > accuracy_S` AND `D_G > D_S`. Do not call this contrast formally statistically significant: it compares metrics of unequal dimensionality and is not an independent spectral-equivalence null. The shuffled-G diagnostic asks whether aligned cross-sensor timing matters within this exact computation, not whether its source is biological.

**Interpretation gates:** `G11_COMPLETE_RELATIONAL_PATTERN_SUPPORT_WITHIN_SCOPE` may be reported only when all 24 records are eligible, the primary one-sided permutation p<0.05, both descriptive increments over the fixed spectral baseline hold, and `D_G > D_shuffledG`. Otherwise, if all are eligible, report `G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT`. If any are ineligible, report `G11_SOURCE_INCOMPLETE` with all 24 statuses and no invented 12×12 outcome. The outcome names indicate narrow operational support or failure only; they do not imply biological persistence.

No redefinition of band limits, window size, labels, frequency bins, threshold, null, participants, dropout policy or outcomes is allowed after source outcomes are seen. Any future modifications require a separately named study with explicit knowledge of G11 results.

## Provenance, reporting and nonclaims

The first source runner must retain its original aggregate-only JSON, SHA256 digest, workflow commit, source timestamps and failed attempts. Report each of the 24 source digest/eligibility results, anonymized fixed subject codes, all 12×12 similarity summaries or matrices, primary statistic and seed, baseline statistics and surrogate checks. Never commit original EEG samples, sensor traces, spectrograms or arrays. Each row represents a recorded **person/session**, not millions of independent physiological samples.

A result supporting G11 says only that **one fixed sensor-level relationship descriptor was reproducible and discriminative in this purposively selected published dataset under stated assumptions**, with comparison to a spectral-only baseline. It does not measure reaction to perturbation, persistent self, psychopathology, disease, independent cortical causal connectivity or any new universal law. Dataset provenance remains incomplete; preprocessing and sensor montage confounds must still be discussed.

## Prior literature

- Wang, Y.; Duan, W.; Dong, D.; Ding, L.; Lei, X. (2022), *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9.
- Vinck, M. et al. (2011), *An improved index of phase-synchronization for electrophysiological data in the presence of volume-conduction, noise and sample-size bias*, NeuroImage 55(4), 1548–1565, https://doi.org/10.1016/j.neuroimage.2011.01.055.
- Hardmeier, M. et al. (2014), *Reproducibility of Functional Connectivity and Graph Measures Based on the Phase Lag Index (PLI) and Weighted Phase Lag Index (wPLI) Derived from High Resolution EEG*, PLOS ONE, https://doi.org/10.1371/journal.pone.0108648.
- *The effects of spatial leakage correction on the reliability of EEG-based functional connectivity networks* (2024), Human Brain Mapping, https://doi.org/10.1002/hbm.26747.
- Dominicus, L. S. et al. (2025), *Reliability and state-dependency of EEG connectivity, complexity and network characteristics*, Scientific Reports, https://doi.org/10.1038/s41598-025-23662-z.
- Graff, K. et al. (2026), *Towards precision EEG connectomics: Evaluating the benefits of dense sampling*, Imaging Neuroscience, https://doi.org/10.1162/IMAG.a.1245.

**Status at freeze:** verified public Git-annex pointer metadata for 24 named records, not 24 downloaded source EEG waveforms. This is a preregistration of a small exploratory observational measurement, **not** source-test execution or a contribution-priority claim.
