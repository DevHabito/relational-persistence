# Lean 4: formal verification scope

This directory documents what Lean 4 can and cannot establish for Relational Persistence.

**Toolchain:** `leanprover/lean4:v4.20.0`, Mathlib tag `v4.20.0`. The GitHub Actions workflow must pass before the formalization is described as kernel-checked. The proofs may require correction after the first CI build; a written `.lean` file alone is not evidence of machine verification.

## Current formalization targets

| Claim | Lean declaration | What it certifies | What it does not certify |
|---|---|---|---|
| Positivity of the proposed index | `scalarIndex_pos` | Algebra under strictly positive inputs | Empirical relationship to stability |
| Bounds of the normalized transform | `normalizedIndex_bounds` | A mathematical interval property | A calibrated observable |
| Network topology changes one-step response | `equal_scalar_inputs_different_update` | Exact rational arithmetic on explicit six-vertex graph models | Twenty-step spectral RP-001 or field data |
| Different dynamic gains produce different 20-step scalars | `distinct_gains_twenty_steps` | A finite exact counterexample | AR(1) stochastic stationarity or a general theorem |

## Important limits

The registered RP-001 primary outcome is the **worst-case twenty-step residual** over the orthogonal-to-consensus subspace. The Lean one-step witness is related but *not equivalent*. We do not mark RP-001's full spectral theorem or numerical output as Lean-verified until formal proofs bridge those steps. None of the data acquisition, network provenance, metric calibration, physical interpretation, statistical inference, or methodological decisions are propositions that Lean can validate merely by compiling these lemmas.

## Reproduce

```sh
lake update
lake exe cache get
lake build
```

The project explicitly forbids `sorry`, `admit`, and newly declared unsupported axioms in its proof modules. Review the CI outcome and commit hash; never quote a green result from an unrelated branch.

## Next obligations

1. Formalize undirected adjacency, combinatorial Laplacians, and row-sum invariants.
2. Prove invariance of the mean-zero subspace and a norm contraction theorem for a declared spectral regime.
3. Certify the exact RP-001 twenty-step threshold with rational interval bounds or an equivalent symbolic proof, independently of the NumPy implementation.
4. Establish the precise relationship between finite-step persistence, stationary variance, and the proposed scalar index in any class where that relationship is asserted.
5. Maintain open counterexamples and non-theorems as first-class research artifacts.
