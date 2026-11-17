# NEU-01-G11-P01 — Alpha phase relationships recur across visits, without the registered identification increment

**17 November 2026.** This is a strictly bounded public EEG test–retest finding from **12 participants × two eyes-closed sessions**, using fixed source files and a preregistered analysis. It is not an assay of consciousness, self-continuity, psychiatric disease, physical entropy or resilience to an imposed perturbation.

## Question and chronology

After G08–G10 had established that 14 published BrainVision/EEGLAB file pairs contained identical samples after float32-to-float64 widening, I needed an experiment using **distinct original recording sessions**, not copies of the same data. I therefore froze the question and all 24 OpenNeuro ds004148 v1.0.0 public annex-pointer EEG and header identities for subjects `sub-10` through `sub-21`, session1 and session3, eyesclosed, at publisher revision `0c740d838a2c33feeec0b6e514aea323d0e65ca4`. These people were not in the five-person G08–G10 cohort, but the source selection is **purposive**, not random or representative.

The protocol-only commit is **`3c86a3b89ffacfc27c5136a5d1a696a56404733d`**. No G11 EEG sample was read before that freeze. The protocol predeclared a 61-channel, 8–12 Hz, 150-epoch pooled absolute imaginary coherency descriptor of 1,830 pairwise sensor relations, a 61-channel log alpha-band-power comparator, a single independent per-sensor epoch-shuffle diagnostic and 20,000 fixed-seed subject-label permutations. It also fixed the all-or-nothing source exclusion rule and the outcome labels.

### Pre-source failures that remain part of this record

The first offline code commit `b3f85ecf7f1994652cd18ec1b117165c00fe3cd8` produced a **failed regression**, [GitHub Actions #44061839022](https://github.com/DevHabito/relational-persistence/actions/runs/44061839022): 2 failures and 1,014 passing tests. The errors resulted from incorrectly demanding bit-for-bit equality of floating-point sums taken in a different order after epoch permutation. The repair commit `d447ddb47f329f77eb6af1e9140699ae1ff5df05` changed only the power-conservation assertion to a strict 1e-12 relative tolerance, retaining the original statistic; original regressions then passed 1,016 tests on both Python 3.11 and 3.12.

The first G11 source-executor commit `62e8ebf7ece8f69a7f4ad5a76ced78121af268b3` also stopped **before any source download** because six synthetic tests found that the frozen manifest had been encoded as tuples rather than typed `Source` records. This is preserved in [GitHub Actions #44062472794](https://github.com/DevHabito/relational-persistence/actions/runs/44062472794). Investigation before G11 signal access additionally caught a **two-character transcription omission** in the `sub-18/session3/eyesclosed` original header pointer MD5. The original published pointer has `13913715b5f5e1fe671c0974a297609b`, not the incomplete 30-hex-digit value in the protocol. Both issues were recorded in the dated [G11 D01 pre-source correction](../protocols/NEU-01-G11-P01-D01-PRE-SOURCE-TRANSCRIPTION-2026-11-17.md) and fixed in `f81e9c68515a21cdff76f5c48306bed10f5f568b`, with no subject, signal, feature, null or outcome-rule replacement. The **original protocol and failed runs remain available**, not erased.

## First authentic G11 source result

The corrected first real-source [GitHub Actions run #44062800166](https://github.com/DevHabito/relational-persistence/actions/runs/44062800166) passed **21 focused pre-source synthetic/adversarial tests**. It then downloaded and authenticated **all 24** original 36,600,000-byte BrainVision .eeg and accompanying 1,122-byte .vhdr files against the previously frozen publisher IDs, checked the declared 500 Hz, 61-channel time grid and exact label order, and computed the three feature families without fitting to subject identity. **24/24 were eligible**; no session/source record was substituted or omitted. The source-head full regression passed **1,023 tests on Python 3.11 and 1,023 on Python 3.12**, as recorded in original [run #44062800053](https://github.com/DevHabito/relational-persistence/actions/runs/44062800053).

The first source JSON was downloaded independently from original Actions artifact **14317994151**. Its original length was **33,803 bytes**, and its independently checked SHA256 is **`0a7bc6785053c4da697f8d287245a6fa93a25ce1a69f945e447f0b3829b51537`**, matching the original workflow log. The archive is stored unchanged at `docs/results/NEU-01-G11-P01-first-run/audit.json`; no original EEG waveforms or spectral time-series are included.

## Predeclared primary, baseline and negative-control results

The primary 12×12 Pearson similarity matrices compare session1 feature vectors with session3 feature vectors. The descriptive `D` is the average same-person similarity minus the average off-diagonal, different-person similarity. Identification counts a row only when the true later-session record is the **unique** highest similarity.

| Feature family | Mean same-person similarity | Mean other-person similarity | D | Correct unique matches |
|---|---:|---:|---:|---:|
| Fixed alpha pooled imaginary-coherency graph (1,830 edges) | 0.6088978345 | 0.1351362857 | **0.4737615488** | **7/12** |
| Fixed alpha log-power vector (61 channels) | 0.9757334617 | 0.9549070475 | **0.0208264141** | **7/12** |
| Independently epoch-shuffled graph (one fixed surrogate per record) | 0.0203825952 | 0.0097625016 | **0.0106200936** | **3/12** |

The primary sensor-graph permutation reference (seed 1101, 20,000 uniform session3-label permutations) found **0 permuted contrasts equal to or larger than the observed `D_G`**. By the registered finite Monte Carlo correction, `p = (1+0)/(20,000+1) = 0.00004999750012499375`. This is a **Monte Carlo reference resolution**, not a population-independent exact tail probability, an EEG clinical p-value or evidence of causal connectivity.

The spectral-power comparator also recovered **7/12** identities. Therefore, although `D_G > D_power` and `D_G > D_shuffled`, the registered conjunctive condition `accuracy_G > accuracy_power` is **false**. The correct original decision is:

**`G11_COMPLETE_NO_INCREMENTAL_RELATIONAL_SUPPORT`**.

It would be scientifically misleading to advertise the low primary permutation reference or the larger raw D as having satisfied the *incremental* success rule. In particular, the 1,830-edge and 61-channel feature spaces have different correlation structures and magnitudes: their raw D values cannot automatically be compared as calibrated effect sizes. The shuffled control is a **single** deterministic disorganization diagnostic, not a phase-randomized reference distribution; it cannot eliminate common sensor or preprocessing artifacts.

## Interpretation relative to relational persistence

There is evidence **within this selected dataset** that the declared alpha sensor relationship descriptor carries *reproducible* between-visit organization: positive within-minus-between contrast, seven correct matches, and a lower surrogate contrast. It did **not** outperform a spectral-only descriptor in the registered identification metric. The result is consistent with ordinary existing EEG fingerprinting/retest findings; **no literature priority or new universal law is claimed**.

The two recordings per participant are repeated observations, not independent humans. Their differences can reflect changed state, shared processing, sensor montage, artifact structure, individual spectral properties and instrument configuration. Nonzero-lag coherency reduces one obvious zero-lag confound but does not prove cortical network connectivity. The source is labeled 'raw' by the dataset but the exact acquisition-to-release operation history remains uncertain.

This study **does not impose a perturbation and measure subsequent functional recovery**. It measures repeated descriptors across visits. A test of genuine relational persistence after disturbance must predefine a functional output independent of the EEG statistic and isolate perturbation/recovery from recording effects.

## Literature and next discriminating experiment

Established work preempts any first-to-identify claim: Vinck et al. (2011), https://doi.org/10.1016/j.neuroimage.2011.01.055; Hardmeier et al. (2014), https://doi.org/10.1371/journal.pone.0108648; *The effects of spatial leakage correction on the reliability of EEG-based functional connectivity networks* (2024), https://doi.org/10.1002/hbm.26747; Dominicus et al. (2025), https://doi.org/10.1038/s41598-025-23662-z; Graff et al. (2026), https://doi.org/10.1162/IMAG.a.1245. Dataset: Wang, Duan, Dong, Ding & Lei (2022), https://doi.org/10.1038/s41597-022-01607-9.

A separately registered follow-up would need an **independent cohort**, explicit measurement invariance and a properly controlled incremental model (e.g., test incremental predictive information over a power-matched null) rather than changing G11 thresholds or choosing only the seven successful identities. No G11 rerun should silently replace the present first outcome.

**Final G11 verdict: complete authentic source evaluation; no registered incremental relational identification support; promising but non-unique descriptive repeatability; no new biological or physical persistence claim.**
