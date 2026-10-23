# Lean 4: formal verification scope

Relational Persistence uses Lean 4 to check mathematical claims about declared
models. This is not a certification of empirical data, physical interpretation,
novelty or predictive performance.

**Toolchain:** Lean 4 v4.20.0 and Mathlib tag v4.20.0.

## The RP-001 formal certificate

The original [RP-001 protocol](../preregistration/RP-001.md) fixes six-vertex
path and star graphs, 20 synchronous graph-Laplacian updates at gain 1/10, and
a worst-case Euclidean residual on real zero-mean initial states.

[Successful Lean CI #40037215631](https://github.com/DevHabito/relational-persistence/actions/runs/40037215631)
at commit `f681b973a54eb13f7260f52ecf48a228340fc124`
proves the following mathematical statements:

| File | Main verified contribution |
|---|---|
| `FiniteWitness.lean` | Positivity and normalization of a scalar *definition*, plus one-step and elementary counterexamples |
| `TwentyStep.lean` | Exact rational twenty-step path witness and uniform star bound |
| `GraphBridge.lean` | Equivalence with the rational six-node graph updates |
| `RealTwentyStep.lean` | Squared-energy inequalities quantified over real states |
| `RealResidualNorm.lean` | Transfer to real Euclidean norm and lower/upper worst-case threshold reasoning |
| `RealGraphBridge.lean` | Equivalence with the real graph updates |
| `RealVectorBridge.lean` | Surjection of six-coordinate states onto all real graph vectors, exact norm identity and graph-level residual bounds |

The path admits a real zero-mean initial vector with a norm ratio above
`1/5` after 20 iterations. Every real zero-mean state in the star obeys
a norm ratio at most `3/20`. This gives a threshold separation strictly
above `1/20 = 0.05` for the declared models. It is a constructive,
classical graph-consensus counterexample to the sufficiency of the fixed
operational three-scalar proxies in this setting.

The explicit supremum expression is not separately formalized. The
proof checks **universal upper bounds** and an **explicit lower witness**,
which suffice for the threshold conclusion. It does not prove the exact
spectral residual values printed in `RP-001.json`, or independence of
noise, model calibration, physical emergence, data validity or generality
beyond the assumptions.

## Reproduce

```sh
lake update
lake exe cache get
lake build
```

Use the pinned GitHub Actions run and exact commit when reporting a
machine-checked result. The project does not use `sorry`, `admit`, or
new unsupported axioms in these modules. Failed builds and repair commits
remain in the repository history.

See [formalization status](STATUS.md), [RP-F001 certificate](RP-F001-TWENTY-STEP-CERTIFICATE.md)
and the [claim ledger](../CLAIM_LEDGER.md).

## Further obligations

1. Formally define the worst-case residual with `sSup` or a suitable
   operator norm, if that exact representation is needed in the manuscript.
2. Formalize spectral eigenvalues, and compare the exact spectral formula
   independently with the bounded-threshold certificate.
3. Formalize stochastic stationarity only under explicit moment and
   independence conditions.
4. Test quantitative predictions against independently observed trajectories
   with preregistered baselines. Lean does not replace empirical testing.
