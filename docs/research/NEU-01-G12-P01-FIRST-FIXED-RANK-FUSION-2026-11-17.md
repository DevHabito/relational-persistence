# NEU-01-G12-P01 — Fixed alpha phase/power rank fusion in twelve previously unseen participants

**17 November 2026. Final original registered outcome: `G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT`.**

## Why G12 was needed

The earlier G11 study compared session1 and session3, eyesclosed, in 12 deliberately selected participants `sub-10`–`sub-21`. The same-person alpha phase-relational descriptor showed robust within-versus-between separation under its fixed label null, but both relational and spectral-only models identified exactly 7/12 people. Its preregistered verdict was **no confirmed incremental support**, not an entirely negative statement about repeatability.

G12 therefore asked a **narrower, genuinely prospective held-out-participant question:** could the *fixed* union of phase relationships with per-channel alpha power help identify more people than power alone? This is not a new biomarker or a test of psychological Self. The phase estimator and alpha band were carried over exactly from G11; the new rule was fixed before G12 EEG waveforms were accessed, with no fitted model, thresholds, channel selection or weight optimization.

## Chronology and registered inputs

- The **protocol-only commit `c6787a0a3186516ba1275e0e419fcfbd5b7d4b09`** was created on 17 November 2026. It registered sub-22 through sub-33, session1 and session3, eyesclosed only — **12 people and 24 distinct recordings**. Original OpenNeuro ds004148 v1.0.0 Git-annex EEG and BrainVision header pointer MD5s and claimed lengths were inspected beforehand, *without reading G12 source waveforms*. Cohort choice was deterministic/purposive **after knowing G11**, not blinded or randomly representative. These people were not in the G08–G11 sets, but they share the same publisher/dataset and recording/preprocessing environment.
- Synthetic-only ranking and negative-outcome code arrived in **`184235b7ce31d28fc731a83b1f6ede5e2649c73d`**. The repository regression passed Python 3.11 and 3.12 on that commit. `experiments/neu01_g12_rank_core.py` reused the G11 FFT, 61-sensor alpha-band and imaginary-coherency graph computations without modifying G11.
- The **first original G12 source implementation** is `8b7c3dff69a61d648b44fb5b9eae78b396924547`. Source workflow: [Actions #44096436611](https://github.com/DevHabito/relational-persistence/actions/runs/44096436611). It completed **19 targeted synthetic/antagonistic pre-source checks before any EEG source access**. All 24 declared original BrainVision 36,600,000-byte `.eeg` files and corresponding 1,122-byte `.vhdr` were downloaded from the fixed publisher URL, independently verified against the registered publisher MD5 pointer identities and hashed with SHA256. **All 24 source records passed the fixed 61-channel, 150,000 time samples and ordered montage criteria**; there were no selective exclusions or replacements.
- The complete source-implementation [regression run #44096436487](https://github.com/DevHabito/relational-persistence/actions/runs/44096436487) passed **1,042 tests in Python 3.11 and 1,042 in Python 3.12**. The true G12 source experiment is *separate* from these software regression counts.
- The **first original source JSON artifact #14333548990** was independently downloaded and its extracted archive `audit.json` checked. It contains **53,239 bytes**, SHA256 `9dfc38092c3440dc7e67e2a99caba97c32ff18493cdd20f3ea11861c50bad62a`, as independently reported by the original Actions source job. Its output is kept byte-for-byte in `docs/results/NEU-01-G12-P01-first-run/audit.json` along with a provenance index and automated checksum regression tests. Only source identity digests, numerical comparisons and outcome flags are retained, never raw EEG waveforms.

## Registered three-way and primary outcomes

The primary diagnostic used *within-row descending ranks* of the 12×12 session1/session3 similarity matrices, with tied ranks averaged. The untrained fusion used **50% power ranking + 50% phase-graph ranking**. The null fusion used **50% power ranking + 50% independently epoch-shuffled graph ranking**. One participant counts as identified only when the correct partner is the unique highest-scoring session3 record. This explicitly avoids treating differently scaled raw Pearson D contrasts as interchangeable effect sizes.

| Predeclared model | Unique correct matches / 12 | Purpose |
|---|---:|---|
| Power-only ranking | **4** | Fixed spectral baseline |
| Graph-only ranking | **7** | Individual phase-relational descriptor |
| Fixed 50:50 power + graph | **6** | **Primary combined model** |
| Fixed 50:50 power + shuffled graph | **4** | Negative-control combined model |
| Independently shuffled graph only | **2** | Descriptive diagnostic |

The fusion correctly identified **two participants who power alone missed**, and **lost no participant** whom power alone correctly identified. Thus the preregistered paired discordance counts were **`b=2`, `c=0`** and the net improvement was **2/12 people (16.7 percentage points)**. Its conventional one-sided exact paired-discordance reference was **`p=0.25`**. That exceeds the primary predeclared **0.05** cutoff. Neither the two-person net improvement nor this significance result should be relabeled after seeing the data.

The secondary joint-label permutation diagnostic (fixed seed 1202, **20,000** shuffled session3 identity assignments) returned **576** shuffled net improvements at least as large as the observed two-person gain; its corrected reference was **`(576+1)/(20,000+1) = 0.028848557572121392`**. This is *not* a conditional test of added information after power is held fixed; it tests a weaker joint-label exchangeability question. It cannot override the registered primary paired result.

The exact predeclared success rule required **all**: improvement of at least two participants, the one-sided exact paired p **below 0.05**, and improvement over null fusion. The first and third conditions were satisfied, the second **was not**. The correct result remains **`G12_COMPLETE_NO_CONFIRMED_FUSION_INCREMENT`**.

## What this does, and does not, support

The result supplies *descriptive* evidence that the fixed phase-relationship score can complement the spectral-only score for **some** participants in this held-out same-dataset cohort. This is more informative than simply rerunning G11's 12 participants. The phase descriptor alone identified 7/12 people, but this remains sensor-level fingerprinting under a common public acquisition/pipeline with repeated measurements; it is not new independent biophysical observation of a causal brain network or intervention-recovery process.

The 1,830 phase-edge and 61 spectral-power features can share spectral, reference, source mixing and electrode-sensor artifacts. Imaginary coherency suppresses some instantaneous linear mixing effects but does **not** guarantee rejection of real-world volume conduction or processing lineage. A subject's repeated sensor properties may be identifiable without persistent neural function. The conventional paired sign calculation treats subject outcomes symmetrically, but candidate pools are shared across subjects and its sample-level independence is **not established**. The secondary label permutation reference is not a full spectral-conditional null. These limitations bar a claim that the phase graph carries unique physiological information conditional on spectral power.

The file-based G11/G12 protocol does not apply a controlled disturbance and measure *functional recovery*. It therefore has not established relational persistence as defined in `docs/foundations/SCOPE.md` or contributed a new mathematics/physics theorem. Success and failure are restricted to this frozen recognition task.

## Consequences for the next study

The next step should not be choosing whichever weight wins on this cohort or ignoring the original no-confirmation classification. A stronger study would prespecify an **external dataset acquired separately**, matched spectral and sensor-artifact nulls, independent recording/reference calibration, and ideally a perturbation or clinical/behavioral endpoint measured independently of the EEG connectivity features. Without a functional outcome, subject identification is a useful calibration/measurement problem, not proof of recovery or persistence.

## Literature and source

- Wang, Y., Duan, W., Dong, D., Ding, L. and Lei, X. (2022), *A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states*, *Scientific Data* 9:566. https://doi.org/10.1038/s41597-022-01607-9.
- Vinck, M. et al. (2011), methodological treatment of lagged phase-synchrony under common-input effects. https://doi.org/10.1016/j.neuroimage.2011.01.055.
- Hardmeier, M. et al. (2014), prior PLI/wPLI retest reliability. https://doi.org/10.1371/journal.pone.0108648.
- *The effects of spatial leakage correction on the reliability of EEG-based functional connectivity networks* (2024). https://doi.org/10.1002/hbm.26747.
- The original G11 archived no-increment study: https://github.com/DevHabito/relational-persistence/pull/101.

**Final original verdict: full source eligibility and tested retrieval improvement of two participants, but not confirmed by the frozen primary significance rule; no new neural or physical persistence claim.**
