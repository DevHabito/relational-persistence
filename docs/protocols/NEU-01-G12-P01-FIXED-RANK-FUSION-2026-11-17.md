# NEU-01-G12-P01 — Out-of-cohort rank-fusion retest: do alpha phase relations improve subject matching beyond alpha power?

**Protocol-only registered on 17 November 2026. No G12 EEG original binary or waveform has been read in this study. No G12 source run or empirical result exists at this registration.**

## Context, hypothesis and what G11 actually showed

The earlier G11 study used sub-10 through sub-21 in session1 and session3, eyesclosed, with a predeclared 61-channel 8–12 Hz pooled absolute imaginary coherency matrix and per-channel log alpha-power comparator. The two descriptors **both matched 7 of 12** people correctly, even though the relational descriptor gave greater raw within-minus-between Pearson similarity contrast. Its original result was correctly reported as `G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT`. The original G11 archive must remain immutable. This G12 proposal is motivated by that already-known result, and therefore is **not blinded hypothesis development**.

The G12 question is deliberately different and falsifiable: **does a fixed, untrained fusion of alpha-power and phase-relation rankings recover more people across two visits than power rankings alone**, in a set of participants not used in G11? This is an incremental *classification* question about published scalp EEG, **not** an inference about neural self, functional resilience to disturbance, causal connectivity or physical entropy.

## Prospective cohort and transparent source-selection chronology

The publisher is OpenNeuro `ds004148`, GitHub source tree `OpenNeuroDatasets/ds004148` at immutable commit `0c740d838a2c33feeec0b6e514aea323d0e65ca4`. I inspected **only original .eeg and .vhdr Git-annex pointer strings** for sub-22 to sub-33, session1 and session3, task eyesclosed, on 17 November 2026, after learning G11's result but before registering this protocol. No new source waveforms, root binary objects, header bodies, or session-level features were examined. This selection is deterministic and purposive, not random. These 12 people were not used in the earlier selected G08/G09/G10/G11 cohorts, but they share the same publisher, dataset, collection environment and possibly preparation pipeline; **this is a participant-held-out same-dataset evaluation, not an independent laboratory replication**.

The declared cohort has exactly **12 people, 24 original BrainVision source recordings**, with one session1 and one session3 eyesclosed record per person. Root path is `sub-SS/ses-sessionN/eeg/sub-SS_ses-sessionN_task-eyesclosed_eeg.eeg`; each row's header uses the same stem with extension `.vhdr`. Files are ordered by increasing numeric participant number, session1 first, session3 second. Every published `.eeg` pointer claims **36,600,000 bytes** and every `.vhdr` pointer **1,122 bytes**. The MD5 values below are authenticated only as **publisher Git-annex pointer claims at protocol freeze**, not hashes recomputed from original downloaded bodies.

| Person | Session1 .eeg MD5 | Session1 .vhdr MD5 | Session3 .eeg MD5 | Session3 .vhdr MD5 |
|---|---|---|---|---|
| sub-22 | f89ea26bb161ca03d869b10573fda363 | 77f7941653b599ab6d482be0f70d90c5 | df135b5ae0d2c895c5bf23b257fddfd0 | 00592256f0a3e9a1918c484052a909c1 |
| sub-23 | 42bb7772ecc065d2e032d523e9ac83bc | 3c3466b1158957da70b8ad9d638f1111 | 81e3a9f9a2f7b9649949912ac9f465c2 | 25fba0fe9bfb6a46f4174b0313a9a75f |
| sub-24 | a7106065c3adc1d1e17d0a63a32729cc | a889320c38c1d69cb56a5e6516c6e9bb | 72a3a97f6cc61008d76e2bb76a96ffbf | 98719d8765f1ec913052f3befeb10457 |
| sub-25 | f1b709a298ae97561f82e91c68308243 | 8be92f6def05b8ddc5250f25f4047daa | d490023deff57a6e7621d3ba24664eee | b75b1d06352ffb35454782e209d2dc6f |
| sub-26 | d7179c72805a129a26c916e04728fb53 | 42c6700ce6f848c0602932f23d5d9044 | 32b58bc047412ad794c038b17052da09 | b4329687e7099645b498ca48119ff9b7 |
| sub-27 | 48193873e5564fd149f2645e8f139f40 | 63e3ca31aac44ba77ab69f903a425cae | 124c3d6fdd1f1c45b8741d2187f0a199 | 93cdb6f039dc713a0ba97ced5b6688ce |
| sub-28 | b6bb527ea5eab3639016c58a2ec2270a | dc52f21e98143e196d9103248c2f6c47 | 7623bbb4fc2598e5691ff533c8595aef | 06c5409076ea4b345884b571d90d50c6 |
| sub-29 | 968982df0a291a522935ebd16b7c2f09 | 1259d1ead25109fba8f59fe73f180d98 | 1d8723cea510b10941230d2cebfa63f3 | 49a1f166b1f7c8a4d7069e1785506754 |
| sub-30 | 2554e778ff4891dd1d14aa23caa6adc6 | 81e01326461ccedd4a89c35ff0d8a606 | 87afe810e99bd4cf11c8e6f06438e61f | 5824fddd857c0f372435a46bad18c218 |
| sub-31 | bfa6bbc41205e3c99bacbdad6bbff9a6 | 78a324a661797faf098386ebaa9bfe43 | 279aabaa7d5b14daa5d9fd136b6f8b93 | 2a418e2450ec83fc32d17d9cd1163653 |
| sub-32 | 136c98ebf145aa9828e25b760252a910 | 08a09c9ee8b7fa3df43c7192a2cfa41c | b5e65d9ce396d14925bd52e4fb6e651b | 82a3eb15fa3e62e95a133d35be6ba3f0 |
| sub-33 | 09f8fe16392654af50844aa0c112221a | 685452fc788735e7fe8eca8c3dba7996 | 2b731a165c0ef7d66b6503c878cecd08 | fac66203876ae74161107ef330dbc4ca |

No replacement participant, task, session, derivative copy, extra selected candidate or metadata-dependent cherry picking is allowed in G12. If any of the 24 is source-ineligible, **there is no completed 12-person primary claim**; record all 24 outcomes and `G12_SOURCE_INCOMPLETE`.

## Data admission and strict implementation lineage

1. Before source access, require the unchanged original G11 first archive `docs/results/NEU-01-G11-P01-first-run/audit.json`, **33,803 bytes** and SHA256 `0a7bc6785053c4da697f8d287245a6fa93a25ce1a69f945e447f0b3829b51537`. Its 7/12-versus-7/12 outcome is a known design dependency, not retest evidence for G12. Record the G12 protocol-only commit separately from the later Python source implementation commit.
2. Run synthetic and adversarial checks **before any of the 24 original EEG bodies is downloaded**, including all subject/session swaps; pointer identity/byte-count corruption; redirect and truncation refusal; per-file BrainVision identity, sample rate and exact ordered 61-channel labels; nonfinite signals; invalid Fourier shape/complex dtype; constant feature rows; tied top scores; fixed combination coefficients; sign-test directionality; failure of gain invariance; and a true negative case where adding a graph harms spectral identification.
3. On a bounded GitHub runner (max 45 minutes, per-request timeouts 45 seconds, maximum source bytes), fetch only registered original BIDS `.vhdr` and `.eeg` publisher URLs from `https://s3.amazonaws.com/openneuro.org/ds004148/` without redirection or fallback. Independently verify each downloaded original against the publisher pointer MD5 and byte length, compute body SHA256, and require BrainVision `IEEE_FLOAT_32` `MULTIPLEXED`, 61 unique channels in exact order with ordered-label SHA256 `0eb9d03a6f1c62af87f95e8de05d9a39632529208c4e8c1be945f809f77d9b99`, 500 Hz (2000 microseconds) and 150,000 finite samples per channel. Do not impute physical microvolts or repair source metadata.
4. Calculate **unchanged G11** first-stage descriptors using `experiments/neu01_g11_alpha_core.py`: 150 nonoverlapping two-second mean-centered Hann-windowed epochs, 500 Hz, nine FFT bins from 8 to 12 Hz inclusive, complex cross-spectrum, 1,830 upper-triangle `abs(imag(coherency))` edges; spectral-only 61-vector of `log(sum|FFT|²)` over the same epochs/bins. Use a single independent per-sensor epoch shuffle with seed `1202 + 10*subject_number + session` for a nuisance diagnostic. No subject-conditioned model, electrode search, threshold choice, alternate band or fitted lag.
5. For **each** family separately, form a 12×12 Pearson similarity matrix across session1 and session3: `M_graph`, `M_power`, `M_shuffle`. Nonfinite or constant features are ineligible; any ineligible source or descriptor blocks the **entire** registered primary census. A session3 subject has exactly one true session1 partner, fixed by the source name and visit. Do not use original source sample values in the final archive.

## The new primary comparison: *rank fusion*, not incomparable raw D values

For each row independently, transform each of the 12 similarities into **descending ranks from 1 (largest) to 12 (smallest)**, with exact ties assigned their *average rank*. Set `q = (12-rank)/11`, an explicitly **dimensionless within-row rank score**, not a probability. No cross-row or cross-session calibration is fitted.

Declare the three retrieval models:

- `P` = power-only: rank each row by `M_power` (the first maximum is not broken arbitrarily; **a tied maximum counts as failure**).
- `F` = untrained two-family fusion: `0.5*q_power + 0.5*q_graph`.
- `Fnull` = **negative control**: `0.5*q_power + 0.5*q_shuffle`.

Also report the graph-only and shuffled-graph-only accuracy as descriptive diagnostics. Each model's total correct identification count is exactly 0–12; each subject contributes **one** primary binary outcome. The first visit's correct later-session partner is the same diagonal column in every model. For every participant record the fixed power-only, fusion, and fusion-null success/failure flags. No alternate weighting is searched on G11 or G12.

Let `b` be the number of participants whose true partner is the **unique top choice under F but not P**; let `c` be the reverse count (**P correct, F wrong**); the primary gain is `b-c`. Under the conventional *paired-discordance symmetry model*, the one-sided exact paired sign probability is `sum_{k=b}^{b+c} binom(b+c,k) / 2**(b+c)`; take `p=1` for `b+c=0`. This nominal model is **limited**: different rows share the same 12-person candidate set, so it is not a rigorous population-independent causal or biological test.

To assess label exchangeability as a **secondary** diagnostic, freeze `numpy.random.default_rng(1202)` and 20,000 uniformly randomized permutations of all 12 true session3 partner columns. For each, evaluate `T_perm=accuracy_F_perm - accuracy_P_perm` with the two fixed retrieval predictions; report `(1 + number(T_perm >= b-c))/(20001)`. This tests a *joint label-association null*, **not** the stronger conditional hypothesis that phase relations add information once alpha power is fixed.

**Only if ALL 24 source files are authentic/eligible**, the following **conjunctive** operational claim can be reported:

`G12_COMPLETE_FIXED_FUSION_INCREMENT_WITHIN_SCOPE` iff `b-c >= 2`, `p_one_sided_exact < 0.05`, and `accuracy_F > accuracy_Fnull`. Otherwise report **`G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT`** with all components, including any negative gain. Do not change the decision after observing the first run or convert an unpersuasive p-value into proof.

Report the 12×12 matrices and rank scores and any ties, b/c, accuracies, both p references, source digest census, and failures. Strict direct IEEE array duplication in G08–G10 has no independent-person evidential weight for this study.

## What success and failure would mean

A passing G12 result means only that the **fixed 50:50 rank-fusion retrieval rule** improved recognition relative to power alone in these 12 new selected subjects, under registered, limited statistical assumptions. It does not prove that the imaginary coherency relations contain physiological information *conditioned on* the complete spectrum or on source mixing; the graph statistic still depends on spectral and instrument properties. A failure would not disprove every possible relational measure or support a reweighted score after seeing outcomes. G12 does **not** impose a controlled perturbation or measure recovery, so it does not directly test the full framework definition of relational persistence.

An independent test with more participants, an external acquisition system, verified preprocessing lineage, a proper power-matched multivariate null, and independent functional outcome would remain necessary. The previous G11 no-increment result is never rewritten. Original first-run artifacts, including errors, are to be preserved immutably with their exact bytes/digests and executable code, without copying EEG waveforms to the repo.

## Prior-art anchors, not originality claims

- Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (2022), *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, *Scientific Data* 9:566, https://doi.org/10.1038/s41597-022-01607-9.
- Vinck et al. (2011), volume-conduction-conscious phase measures, https://doi.org/10.1016/j.neuroimage.2011.01.055.
- Hardmeier et al. (2014), PLI/wPLI retest reproducibility, https://doi.org/10.1371/journal.pone.0108648.
- *The effects of spatial leakage correction on the reliability of EEG-based functional connectivity networks* (2024), https://doi.org/10.1002/hbm.26747.
- Dominicus et al. (2025), connectivity, complexity and network reliability, https://doi.org/10.1038/s41598-025-23662-z.

**Freeze status:** publisher pointer metadata checked for all 24 selected source files and 24 headers; no G12 original waveform read; no G12 empirical outcome. Next permissible stage is synthetic-only rank-fusion implementation, adversarial tests, then one unmodified first original source run.
