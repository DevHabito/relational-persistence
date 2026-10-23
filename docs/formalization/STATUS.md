# Formal verification status

## Successful verified baseline

- **Date:** 2026-10-23.
- **Code commit:** `cafeb33b6b1b55e88cc5ada6cb88405b6903b8c2`.
- **Workflow run:** [Lean 4 proof checking #40032271293](https://github.com/DevHabito/relational-persistence/actions/runs/40032271293) — **completed successfully**.
- **Toolchain:** Lean 4 v4.20.0; pinned Mathlib `v4.20.0`.
- **Checks:** `lake build` succeeded; the no-`sorry`/`admit` check succeeded.
- **Lean declarations:** `scalarIndex_pos`, `normalizedIndex_bounds`,
  `path_update_vertex_zero`, `star_update_vertex_zero`,
  `equal_scalar_inputs_different_update`, `distinct_gains_twenty_steps`.
- **Interpretation:** These are mathematical proofs about a specific rational model and algebraic index, not empirical or physical verification.

## Corrections retained

- **First attempted run:** [#40032169328](https://github.com/DevHabito/relational-persistence/actions/runs/40032169328) **failed before type-checking** because a Lake manifest had not been generated. This was a CI configuration failure, not evidence about the truth or falsehood of any lemma.
- **Corrective commit:** `cafeb33b6b1b55e88cc5ada6cb88405b6903b8c2` generates the manifest before invoking the Lean action.

## Verified real graph-level RP-F001 certificate

- **Verified code commit:** `f681b973a54eb13f7260f52ecf48a228340fc124`.
- **Successful Lean build:** [#40037215631](https://github.com/DevHabito/relational-persistence/actions/runs/40037215631).
- **Same-commit Python regression:** [#40037215654](https://github.com/DevHabito/relational-persistence/actions/runs/40037215654).
- **Scope:** `RealTwentyStep.lean` proves twenty-step real squared-energy inequalities. `RealResidualNorm.lean` transports them to Euclidean norms. `RealGraphBridge.lean` matches the two graph Laplacian updates. `RealVectorBridge.lean` proves the coordinate representation is surjective and establishes norm correspondence for all `Fin 6 → ℝ` vectors.
- **Result:** an explicit mean-zero path graph vector has norm ratio >0.20, while every real mean-zero star graph vector has norm ratio ≤0.15. The threshold contrast >0.05 follows for any worst-case bound of the path versus this valid bound on the star.
- **Limit:** exact eigenvalues, equality with a separately defined `sSup`, stationary stochastic variance, and observed dynamics are not proved in Lean by these declarations.

## Open proof obligations

- If an explicit `sSup` or operator-norm object is introduced, prove its existence, exact meaning and consistency with the quantified upper-bound definition.
- The exact spectral eigenvalues, the reported floating-point residuals and the AR(1) stochastic stationarity criterion are not yet Lean-formalized.
- Units, identifiability, causal interpretation, measurement quality, observational validation and novelty are outside the scope of these finite graph proofs.

Track subsequent formal refinements at [RP-F001](https://github.com/DevHabito/relational-persistence/issues/1). A successful CI run only applies to its exact source commit and the propositions actually checked.

## Exact twenty-step rational certificate (verified partial RP-F001)

- **Verified code commit:** `9390e5657d6e6cd610ccbcb0a648bd8c27f11143`.
- **Successful Lean run:** [#40034508194](https://github.com/DevHabito/relational-persistence/actions/runs/40034508194).
- **Declaration:** `rp001_rational_twenty_step_certificate` in `RelationalPersistence/TwentyStep.lean`.
- **Content:** rational path witness norm ratio > 1/5; universal rational mean-zero star bound ≤ 3/20 after 20 iterations, using exact squared norms and explicit certificates.
- **At that historical commit:** the graph correspondence and real-state transport were unverified. They were subsequently verified in run #40037215631; see above.
- **Failed precursor:** [#40034212699](https://github.com/DevHabito/relational-persistence/actions/runs/40034212699), where `decide` failed to normalize rational equalities. The correction used `norm_num` and passed. This is a tooling/proof-script failure, not a changed numerical target.
