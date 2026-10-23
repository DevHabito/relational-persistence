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

## Open proof obligations

- The registered RP-001 **worst-case twenty-step residual gap** remains computationally verified but **not yet formally proved in Lean 4**.
- The AR(1) stochastic stationarity criterion and consensus spectral decomposition have not yet been formalized in this repository.
- Real-data validity, model selection, units, identifiability, causal interpretation and physical relevance cannot be conferred by compilation.

Track the complete RP-001 theorem at [RP-F001](https://github.com/DevHabito/relational-persistence/issues/1). A successful CI run only applies to its exact source commit and the propositions actually checked.
