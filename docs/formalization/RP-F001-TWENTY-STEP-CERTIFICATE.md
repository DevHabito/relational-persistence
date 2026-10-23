# RP-F001: exact twenty-step certificate and its limits

**Status:** RP-F001 bounded-threshold result verified by Lean 4; see [CI #40037215631](https://github.com/DevHabito/relational-persistence/actions/runs/40037215631) at `f681b973a54eb13f7260f52ecf48a228340fc124`. This document remains separate from the frozen RP-001 preregistration.

## Model

Both networks have six labeled vertices, five edges, update gain `alpha = 1/10`,
and the synchronous unweighted graph-Laplacian update `W = Id - alpha L`.
The comparison uses the mean-zero disagreement subspace and the **same**
twenty-step horizon. The deterministic contrast does not depend on the
innovation variance, although the declared RP-001 operational proxy does.

The exact six-coordinate implementations `pathStep` and `starStep` are in
`RelationalPersistence/TwentyStep.lean`. The correspondence to the graph
adjacency update is a separate proof obligation in
`RelationalPersistence/GraphBridge.lean`.

## Exact inequality for the star

For a six-coordinate state `x`, let

`E(x) = x0^2 + x1^2 + x2^2 + x3^2 + x4^2 + x5^2`,
and `S(x) = x0 + x1 + x2 + x3 + x4 + x5`.

A polynomial identity, which does not assume `S(x)=0`, is

```text
(81/100) E(x) - E(starStep(x)) - (39/50) x0^2
  = -S(x) (26*x0 + S(x)) / 100.
```

The star update preserves `S`. Therefore, under `S(x)=0`,

```text
E(starStep(x)) = (81/100) E(x) - (39/50) x0^2
               <= (81/100) E(x).
```

Iteration yields `E(starStep^20(x)) <= (81/100)^20 E(x)`.
An exact rational comparison proves `(81/100)^20 < (3/20)^2`.
Thus the Euclidean disagreement norm contracts by at most `3/20`
after twenty iterations for this model. This bound is conservative; the
star's exact non-consensus operator norm is `(9/10)^20` by classical
spectral analysis.

## Explicit path witness

Choose `v = (1, 1, 1, -1, -1, -1)`, with `S(v)=0`, `E(v)=6`.
The exact rational twenty-step recurrence gives:

```text
(pathStep^20(v))_0 = 17969771336684377939/25000000000000000000
E(pathStep^20(v)) =
  209891050218350271828970842260119600319
  / 125000000000000000000000000000000000000
```

Hence `E(pathStep^20(v)) / E(v) > (1/5)^2`.
This particular path witness therefore has a norm ratio greater than
`1/5`; the **worst-case** ratio cannot be smaller.

Combining the path lower bound and the uniform star upper bound gives
a separation strictly greater than `1/5 - 3/20 = 1/20 = 0.05`.
The argument is an elementary exact certificate, not a spectral
diagonalization, statistical test, or physical prediction.

## Real graph-level verification

The rational argument was extended to real states and formally linked to
all graph vectors on `Fin 6`. In `RealVectorBridge.lean`, an explicit
inverse maps any vector of six real coordinates to `RealSixState`.
The sum and squared-energy identities preserve the mean-zero condition
and Euclidean norm. `RealGraphBridge.lean` proves the real graph updates
coincide with the coordinate recurrence. `RealResidualNorm.lean` proves
the squared-energy bounds imply the corresponding Euclidean norm bounds.

The path lower witness and the universal star upper bound therefore apply
to the **real graph-state space** named in RP-001, not only rational tuples.
Lean checks the comparison with any valid path uniform upper bound; it
does not separately construct a `sSup` or certify the reported exact
spectral eigenvalues.

## Historical certification obligations (now resolved in bounds form)

1. Exact arithmetic and star bound: checked.
2. Agreement with the six-vertex Laplacian graph update: checked.
3. Transfer to all six-component real vectors and their Euclidean norm: checked.
4. A separately defined supremum or operator-norm equality: **not formalized**.
5. Physical interpretation and observed-data validity: **not established**.

An early CI run failed because `decide` could not reduce the rational
certificates. That is a **formalization failure**, not a contradiction
with the independent exact-rational arithmetic. The history is preserved.

## Previous literature and provenance

The model and operator-norm comparison are within classical symmetric
consensus dynamics; see Olfati-Saber, Fax and Murray (2007), as cited in
`docs/literature/PRIOR_WORK.md`. The numerical threshold is from the
pre-registered RP-001 research protocol. No new universal law is claimed.
