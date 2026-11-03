# RP-U004-F01 — Retrospective Boolean-score ordering lemma

**Date:** 3 November 2026.  
**Type:** formalization plan after an already observed result; **not preregistered prediction**.  
**Source of the question:** [RP-U004-P01 original result](../results/RP-U004-P01.md), archived unchanged at `docs/results/RP-U004-P01-first-run/`.  
**Research lead:** Felipe Gianini Romero.

## What I discovered only after reading the original outcome

The U004 protocol compared policies whose decision scores were labeled F1-first and F2-first. In the first report, their repair orders were identical across the 2,850 examined failure scenarios. The [post-result report](../results/RP-U004-P01.md) correctly explains the likely reason: the two Boolean functions are nested. A graph cannot have two internally vertex-disjoint terminal routes without having at least one.

The admissible Boolean pairs (F1,F2) are precisely `(false,false)`, `(true,false)`, and `(true,true)`. Both lexicographic rankings order those pairs identically:

```text
(F1,F2)        F1-first ordinal    F2-first ordinal
(false,false)          0                   0
(true,false)           2                   1
(true,true)            3                   3
```

This is a small finite fact about a **nested pair of Boolean functions**. It is not an original graph-theoretic theorem, independent experimental support, new physical law, or proof that either policy is optimal on arbitrary networks.

## Frozen proof obligations before introducing the new module

1. Define a Boolean outcome pair and the explicit admissibility condition `F2 -> F1`.
2. Encode exactly the two lexicographic score priorities, with numeric scores used only to order Boolean values.
3. Prove that for **any two admissible outcomes**, strict preference and score ties agree between the two priorities. Do not rely on the original numerical graph outcomes to establish the theorem.
4. Prove that the same preference holds when candidates have a deterministic **lower-label tie breaker**. Include the lookahead pairwise preference which ranks the best future function score before its immediate function score, again using the same deterministic label tie breaker.
5. Demonstrate that the admissibility assumption is necessary: the invalid `(false,true)` outcome can reverse the two rankings when compared against `(true,false)`.
6. Verify the new declarations using the repository-pinned Lean 4 toolchain and no-admitted-proofs CI gate on the exact reviewed PR head. Existing Python regression CI must also pass.
7. Keep the original experiment archive, original preregistration and all previously observed H1/H2 numbers unchanged.

## Failure conditions

A Lean type-checking or build failure means **not formally verified**. Any need to weaken the statement or modify the Boolean function definition must be disclosed in a new dated note rather than silently called a successful proof.

This lemma can explain why the two *named objective priorities* collapse in the U004 Boolean scoring mechanism. It does not, by itself, verify the Python search code, all repair state transitions, the original case enumeration, the offline full-horizon maxima, or the external validity of the model. Those are separate computation and empirical questions.

The next prospective experiment, if one is eventually justified, needs genuinely **non-nested** operational objectives and independent outcomes. It must not be tested retroactively on RP-U004 as though the question were frozen before its answers were known.
