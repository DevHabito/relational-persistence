# NEU-01-G08-D02 — Projected EEG arrays have zero observed residual; direct sample identity remains untested

**12 November 2026; GitHub runner 13 November UTC. Explicitly post-result G08 numerical follow-up, one preselected earlier participant/state source pair.** The prior G08-P01 zero-lag channelwise Pearson r=1.0 and all historical EEG results were known *before* D02 registration. The D02 protocol-only commit was a5f5dd11d8ed95d618ca718bb7b9eec9ea32664a. This is source-file arithmetic, not independent human replication or a discovery in neural physiology.

## Actual chronology (retain the unsuccessful attempt)

The first G08-D02 workflow #43336398552 at source implementation cbda4f544493c90234a8b2ea9266ed2fb7282cd5 **failed its own synthetic pre-source test**. A hand-constructed synthetic derivative was 3x original plus an arbitrary same-frame common offset. The production residual code correctly computed fixed-gain-one relative residual **2/3**, but the test mistakenly asserted the ratio would exceed 1. This test failure occurred **BEFORE ANY ORIGINAL EEG WAS ACCESSED**. Full regression #43336398645 also failed; both runs were retained.

A dated standalone explanation, docs/research/NEU-01-G08-D02-R01-SYNTHETIC-ASSERTION-2026-11-12.md, was committed with exactly the synthetic assertion correction in commit 03cdc3e6083518996c6eb98602e23b126937b59b. The original protocol, source algorithm, historic outputs, cohort and criteria were not changed.

The first G08-D02 source-capable run **#43336512537**, same corrected head 03cdc3e6083518996c6eb98602e23b126937b59b, passed **seven synthetic tests before reading the original source**. It independently authenticated the previously fixed sub-02 session1 eyesclosed original BIDS BrainVision .eeg and derived EEGLAB sub02_01_EC.set. It read the two original arrays in their pre-registered order, without time shift, channel remapping or interpolation. The full source-commit repository regression #43336512543 passed **958 tests on Python 3.11 and 958 on Python 3.12**, according to inspected job logs.

## Exact first original source-level outcome

For each frame, independently subtract the across-61-channel mean from both source float32 (after exact float64 promotion) and derived double matrices: A=P(R), B=P(D). Then fit a *single global gain* a = inner(A,B)/inner(A,A) and examine the full 9,150,000-element Frobenius residuals. No per-channel gain, lag, permutation or filtering is fit.

| Predeclared quantity | Observed original G08-D02 output |
|---|---:|
| Best single gain a | **1.0** |
| Relative residual ||B-A||/||B|| **without any fitted gain** | **0.0** |
| Maximum absolute error |B-A| in native numerical units | **0.0** |
| Relative residual ||B-aA||/||B|| with shared gain | **0.0** |
| Maximum absolute error |B-aA| | **0.0** |
| Projected explained fraction 1 - residual^2 | **1.0** |
| Fixed 500-frame shifted derivative residual, SAME gain a | **0.4493749669080816** |
| Fixed reversed-channel derivative residual, SAME gain a | **1.5403313440617474** |

The 0.0 residual values are exactly what the float64 implementation returned after its per-frame mean projections, *not rounded nonzero values*. They establish **numerical equality of the projected arrays in this execution** at computed precision, but do **not yet test direct equality of the underlying unprojected sample arrays**. A time-varying across-channel common offset can be entirely removed by the chosen P operation. A zero residual is mathematically compatible with D=R+c[t] for all channels, and cannot on its own uniquely identify the publisher's past software operations.

The fixed negative controls have nonzero residuals and were not used to choose a best lag or reorder channels. A prior G08-P01 found all 61 channelwise zero-lag correlations 1.0 after the same projection; D02 independently strengthens that **projected** relationship by eliminating the ambiguity of per-channel affine gains within floating precision.

## Exact native zero, integer and repetition counts (one pair)

The source R independently reproduced every frozen G05 sub-02 session1 eyesclosed count, including 5,923 zero samples, 9,144,077 nonzero samples, 912,943 exact native nonzero integer samples, 130,491 equal adjacent pairs of which 187 zero-zero and 130,304 equal nonzero. Crucially, the newly audited derivative D also produced **the same totals for each of those integer and equality metrics**, including the split 13,008 integer-valued and 117,296 noninteger equal nonzero adjacent pairs. This strengthens the concern that the original and derivative stored numerics might be direct copies in different containers, rather than differently processed numeric signals; however a summary-count match cannot prove actual sample-by-sample identity.

No amplitude samples, per-frame fitted offsets, channel names or signal traces are published. The source binary objects were deleted from the ephemeral runner without being uploaded. The first real source audit was downloaded from original Actions artifact #13997710715, independently hashed and preserved byte-for-byte as **docs/results/NEU-01-G08-D02-first-run/audit.json** (2,332 bytes; SHA-256 **a0fe888346e76de66672b41aa5634d45a5798a56633f7fd551d06de5747ae0a8**), matching original job output. The archive index retains both the initial pre-source failure and the first successful original source run.

## Scientific correction and next decisive source test

The original BIDS channels.tsv declares uV for all 61 channels even though the original BrainVision headers omitted units. The derived EEGLAB metadata declares reference common and double precision, whereas BIDS reports FCz and original IEEE float32 storage. **The content of metadata labels is not itself a proof of a numerical reference operation**, especially when G08-D02 reports zero centered residual. The original authors' paper describes separate signal preprocessing, but the file-by-file lineage for this original/derivative pair is still under investigation.

The *next* registered step must compare **every unprojected sample**, not just centered projections and summary integer counts. Pre-register an exact float32→float64 widening comparison on all 9,150,000 aligned positions, differentiating IEEE numerical equality from bitwise equality (including signed zeros), with fixed negative time/channel controls. Only after that test can we claim whether the original and derivative matrices contain the **same native numeric samples** for this one pair. The step is unblinded and post-result by construction.

Sources: EEGLAB Data Structures, https://eeglab.org/tutorials/ConceptsGuide/Data_Structures.html; Brain Products BrainVision Core Data Format 1.0, https://www.brainproducts.com/support-resources/brainvision-core-data-format-1-0/; Wang, Yulin; Duan, Wei; Dong, Debo; Ding, Lihong; Lei, Xu (2022), Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9.

**Final D02 status: G08_D02_RESIDUAL_CENSUS_COMPLETE.** This is a strong digital equivalence observation for a single source pair, not yet a direct all-sample identity finding or evidence of neural/clinical physics.
