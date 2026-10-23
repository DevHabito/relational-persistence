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
  attempts to formally prove the star's *sharp* squared-energy bound
  from an attained eigenmode. An attempted proof is not verified
  until the pinned Lean CI passes.
- [PR #7](https://github.com/DevHabito/relational-persistence/pull/7)
  independently checks both graph characteristic polynomials with
  exact fractions, rather than NumPy's eigenvalue implementation.
- A complete Lean certificate of the path's algebraic eigenvalue
  `2 - sqrt(3)`, its eigenspace, maximality and the exact `sSup`
  equality **has not yet been produced**.

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

A formal proof of the precise **norm-ratio supremum** is being developed
separately in [PR #8](https://github.com/DevHabito/relational-persistence/pull/8).
Do not conflate the squared-energy result with a verified supremum
declaration before its own pinned CI succeeds.
