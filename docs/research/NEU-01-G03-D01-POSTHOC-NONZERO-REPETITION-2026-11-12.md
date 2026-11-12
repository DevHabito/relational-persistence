# NEU-01-G03-D01 — A post-result lower bound on nonzero EEG repetitions

**12 November 2026.** This is a retrospective mathematical audit of the **original G03 aggregate counts**, not a preregistered prediction, a new experiment on human EEG, or an independent download of raw signals. The source G03 report, its protocol and its immutable first-run JSON are unchanged.

## Question and simple proof

After seeing the G03 result, I asked if its high exact-adjacent-equality counts could be fully accounted for by its exact zero-valued samples. This is an unblinded question, and should never be presented as a second prospective confirmation.

Let Z be the total number of numerically zero samples (including signed zero), E the number of equal-adjacent sample pairs within channels, E00 the number of zero-zero pairs and Enn the number of equal nonzero-nonzero pairs. Across finite channel sequences, if Z>0 there is at least one maximal nonempty zero run. A run containing k zeros generates k-1 zero-zero pairs. With R such runs, E00=Z-R, so E00<=Z-1. If Z=0 then E00=0. Hence

    E00 <= max(0,Z-1)
    Enn = E-E00 >= max(0,E-max(0,Z-1)).

The identity is elementary finite-sequence counting, not a new theorem. It assumes neither independent samples nor a model of the EEG. It uses exact **numerical** equality in decoded native float32 values, not bitwise identity or calibrated voltage.

## Immutable-archive-derived bounds

| Participant | Closed equal pairs E | Closed zeros Z | Max possible closed zero-zero pairs | Min closed nonzero equal pairs | Exact open nonzero equal pairs (Z=0) | Min closed-minus-open nonzero pairs |
|---|---:|---:|---:|---:|---:|---:|
| sub-02 | 130,491 | 5,923 | 5,922 | **124,569** | 9 | **124,560** |
| sub-03 | 152,796 | 11,161 | 11,160 | **141,636** | 3 | **141,633** |
| sub-04 | 175,607 | 15,318 | 15,317 | **160,290** | 12 | **160,278** |
| Total, not independent human observations | 458,894 | 32,402 | 32,399 | **426,495** | 24 | **426,471** |

Thus at least 95.46%, 92.70% and 91.28%, respectively, of the eyes-closed exact-adjacent equalities involve **nonzero values**. These are conservative bounds, not a newly measured full sample-level breakdown. The digital equality contrast therefore cannot consist solely of repeated zeros. A **common processing mechanism** could nevertheless create both repeated zeros and repeated nonzeros; its cause is wholly unresolved.

## Traceability, code and tests

The read-only analysis in experiments/neu01_g03_posthoc_nonzero_bounds.py refuses the source JSON unless its exact 10,117 bytes hash to SHA-256 b142e6b0b0d03e1bd6167fba1a3d265bf3d5efd485e8389474f882955bf8195c, the archived index matches, and the recorded sample counts and paired differences remain consistent. This is a re-analysis of six G03 summary records, not an independent re-count of 54.9 million individual samples.

The separate tests/test_neu01_g03_posthoc_nonzero_bounds.py checks every single-channel sequence of lengths 1–6 and every two-channel sequence of length 3 per channel on {-1,0,1}. It guards signed zeros, malformed integer inputs, nonzero plateaus, archive mutation and channel boundaries. Python regressions and Lean 4 CI status must only be claimed after checking actual runs. No new Lean theorem is asserted here.

Command: python -m experiments.neu01_g03_posthoc_nonzero_bounds

## Literature and scientific limit

Yulin Wang, Wei Duan, Debo Dong, Lihong Ding and Xu Lei (13 September 2022), “A test-retest resting, and cognitive state EEG dataset during multiple subject-driven states,” Scientific Data 9:566, https://doi.org/10.1038/s41597-022-01607-9, describes the source recordings and **additional ICA applied for eyes-open data**. The publication precedes and constrains our interpretation; it does not establish which operation caused these particular equalities.

Brain Products GmbH, BrainVision Core Data Format 1.0, specification document version 2.5 (12 December 2019), https://www.brainproducts.com/download/specification-of-brainvision-core-data-format-1-0/, describes stored IEEE_FLOAT_32 numbers and channel scaling metadata. The original G03 source headers omit explicit physical units; they cannot be silently treated as calibrated voltage amplitudes.

Dictionary: **zero run** is a maximal nonempty within-channel series of numerical zeros; **nonzero equal pair** is an adjacent equal pair with both values nonzero; **lower bound** is a mathematical guarantee, not a new sample count; **retrospective** means derived after inspecting the G03 results.

**Decision:** RETROSPECTIVE_DETERMINISTIC_BOUND_NOT_NEW_SOURCE_EXPERIMENT. Neither Lempel–Ziv complexity, neuronal entropy, neural rigidity, disease, subjective identity nor processing causality has been measured here. Next falsifiable source-level gate: prospectively specify the complete nonzero value/repeat-run histogram and matched preprocessing source lineage **before** opening those additional measurements. Independent original G03 re-downloading and re-counting remains outstanding.
