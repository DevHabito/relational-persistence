# RP-F002 — Exact spectral identities and proof obligations

**Status:** classical algebraic derivation and independently checked symbolic
targets; this document is **not** a claim that the entire spectral theorem has
been formalized in Lean 4. The already verified RP-F001 real-vector
**threshold bounds** are a distinct result.

## Frozen model

Both graphs have six vertices and five unweighted undirected edges.
The discrete consensus update is

```text
x[t+1] = W x[t],        W = Id - (1/10)L,
L = D - A,             t = 0,...,19.
```

The primary deterministic outcome is the Euclidean operator norm of
`W^20` restricted to the real zero-sum subspace. The graph Laplacians
are symmetric, so the usual real spectral theorem applies. The consensus
eigenvector with Laplacian eigenvalue zero is excluded by the zero-sum
restriction. These are classical facts, not new mathematics.

## Exact characteristic polynomials

For the path `P6`, direct determinant expansion gives

```text
det(z Id - L_P6) =
  z (z - 1) (z - 2) (z - 3) (z^2 - 4z + 1).
```

The eigenvalues are therefore

```text
0, 2 - sqrt(3), 1, 2, 3, 2 + sqrt(3).
```

For the star `S6`,

```text
det(z Id - L_S6) = z (z - 6) (z - 1)^4.
```

Its eigenvalues are `0`, `1` (fourfold), and `6`.
The exact characteristic-polynomial factorizations are currently
checked by a separate standard-library Fraction determinant regression
test in [PR #7](https://github.com/DevHabito/relational-persistence/pull/7).
A passing regression test is not a kernel-checked Lean theorem.

## Consequent exact 20-step residuals

All non-consensus multipliers `1 - lambda/10` are nonnegative for
these two graphs. Their largest values give

```text
r20(P6) = ((8 + sqrt(3))/10)^20
r20(S6) = (9/10)^20
```

The approximations below are **derived values** supplied solely to
make the identities readable; they are not fitted model outputs:

| Quantity | Approximation |
|---|---:|
| `r20(P6)` | 0.5808812405283865 |
| `r20(S6)` | 0.1215766545905693 |
| `r20(P6) - r20(S6)` | 0.4593045859378172 |

The exact numerical difference is not a newly discovered physical
constant. It is a deterministic property of the chosen pair of graphs,
their gain and the fixed twenty-step horizon.

## Formal evidence and remaining work

- [RP-F001](https://github.com/DevHabito/relational-persistence/issues/1)
  is Lean-certified *in bounded-threshold form*: an explicit real path
  witness has a 20-step norm ratio >1/5, and the real star has a uniform
  bound ≤3/20. This already implies a separation >1/20 for the declared
  model, without relying on the spectral expressions above.
- [RP-F002](https://github.com/DevHabito/relational-persistence/issues/5)
  separately targets the exact operator norm or `sSup` object and
  its equality with the spectral formula.
- [PR #6](https://github.com/DevHabito/relational-persistence/pull/6)
  proved the star's sharp squared-energy bound, verified in Lean
  [#40038735921](https://github.com/DevHabito/relational-persistence/actions/runs/40038735921).
- [PR #7](https://github.com/DevHabito/relational-persistence/pull/7)
  independently checks both graph characteristic polynomials with
  exact fractions, rather than NumPy's eigenvalue implementation.
- [PR #9](https://github.com/DevHabito/relational-persistence/pull/9)
  verified an explicit nonzero mean-zero P6 eigenmode and its
  exact 20-step attained norm ratio in Lean
  [#40040392019](https://github.com/DevHabito/relational-persistence/actions/runs/40040392019).
  The path maximality was subsequently verified through PR #10; see the final certificate below.
- [PR #8](https://github.com/DevHabito/relational-persistence/pull/8)
  verified the exact S6 attainable-set norm-ratio supremum in Lean
  [#40041114514](https://github.com/DevHabito/relational-persistence/actions/runs/40041114514).

## Classical attribution

Olfati-Saber, R., Fax, J. A., & Murray, R. M. (2007).
*Consensus and Cooperation in Networked Multi-Agent Systems*.
Proceedings of the IEEE, 95(1), 215–233.
DOI: https://doi.org/10.1109/JPROC.2006.887293

The result belongs to classical graph Laplacian consensus and
finite-dimensional spectral theory. Neither the PMFF nor RZS has been
shown to derive these particular dynamics.

## Verified sharpness checkpoint

The star squared-energy bound is no longer merely a candidate: Lean 4
[run #40038735921](https://github.com/DevHabito/relational-persistence/actions/runs/40038735921)
accepted the exact proof in `StarSharpEnergy.lean`. The result is the
least uniform coefficient `(81/100)^20`, attained by a nonzero,
zero-sum leaf-disagreement mode. See merged [PR #6](https://github.com/DevHabito/relational-persistence/pull/6).

The independent characteristic-polynomial regression checks also passed
CI and were integrated in [PR #7](https://github.com/DevHabito/relational-persistence/pull/7).
These are numerical-free **exact computational checks**, but not Lean
kernel proofs of the characteristic-polynomial identities.

The **star** norm-ratio supremum is now separately verified in Lean:
`StarSharpNorm.lean` defines `starResidualRatios`, proves the sharp
upper bound on every nonzero mean-zero real graph vector and constructs
a nonzero state attaining it. Lean accepts
`sSup starResidualRatios = (9/10)^20`.
The **path** exact eigenmode has also been verified; its global
maximality and resulting exact path supremum remain distinct open
obligations. These results are classical spectral graph mathematics,
not independent empirical discoveries.

## RP-F002: exact two-graph result (verified)

The exact classical finite-graph worst-case residuals are now both
**machine-checked** on the original mean-zero real six-vector domains:

```text
sSup pathResidualRatios = ((8+sqrt(3))/10)^20
sSup starResidualRatios = (9/10)^20
```

For P6, the [Lean proof #40042195359](https://github.com/DevHabito/relational-persistence/actions/runs/40042195359)
certifies a universal squared-energy upper bound using an exact
sum-of-squares identity. Together with the previously verified slow
eigenmode, it certifies both the supremum and its attainment.
[PR #10](https://github.com/DevHabito/relational-persistence/pull/10)
was merged into main. The independent [PR #11](https://github.com/DevHabito/relational-persistence/pull/11)
evaluates the SOS identity as an exact matrix equation in
`Q(sqrt(3))`, rather than relying on floating-point eigensolvers.

For S6, `star_residual_supremum` is established by the previously
successful Lean [#40041114514](https://github.com/DevHabito/relational-persistence/actions/runs/40041114514),
with an attained leaf-disagreement mode.

**Interpretation:** the equality of these computed residues with the
classical eigenvalue formula is proved for this fixed pair of graphs
and this gain/horizon. The project has not formalized the full path-graph
spectral theorem for arbitrary graph sizes, established a novel physical
law, measured operational `B/I/tau` in an observed system, or validated
the persistence hypothesis empirically.
