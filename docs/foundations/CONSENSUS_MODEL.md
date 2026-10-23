# A baseline dynamical witness: linear consensus

This section uses established graph-spectral results. It is included to give the new research program an honest, tractable starting point, not to claim original consensus theory.

## Declared setting

Let `G = (V,E)` be a finite, connected, simple, undirected graph on `n >= 2` vertices. Let `A` be its unweighted symmetric adjacency matrix, `D` the diagonal degree matrix, and `L = D - A` its combinatorial Laplacian. Define

\[
W=\mathrm{Id}-\alpha L,\qquad x_{t+1}=Wx_t+\xi_t.
\]

Assume `alpha > 0`, and independent innovations `xi_t` with zero mean and covariance `s^2 Id`; assume innovations are independent of the initial state. `s^2` is **per-coordinate variance** rather than entropy. The mean or consensus mode is projected out by `Pi = Id - (1/n)11^T`. `Pi W = W Pi` by Laplacian symmetry and `L1=0`.

## Classical spectral conclusion (conditional)

Write the ordered real Laplacian eigenvalues as `0 = lambda_1 < lambda_2 <= ... <= lambda_n`. The disagreement eigenvalues of `W` are `mu_j = 1-alpha*lambda_j`, `j>=2`. If `max_{j>=2} |mu_j| < 1`, the worst-case residual disagreement after `T` noise-free steps is

\[
r_T=\sup_{z\perp\mathbf{1},\,\|z\|_2=1}\|W^T z\|_2
=\left(\max_{j=2,\ldots,n}|1-\alpha\lambda_j|\right)^T.
\]

Here `W^T` denotes the *T-th matrix power*, not matrix transpose. For clarity in code this is `matrix_power(W, T)`.

**Proof:** orthogonally diagonalize `L`. The mean-zero subspace has eigenvectors `u_2,...,u_n`, and `W^T` multiplies the `j`th component by `mu_j^T`. Its operator 2-norm on that subspace is the largest absolute multiplier. This is elementary symmetric spectral theory.

If the innovations are as specified, then for `z_t = Pi x_t` the expected **total** stationary squared disagreement is

\[
E\|z_\infty\|_2^2
=s^2\sum_{j=2}^{n}\frac{1}{1-(1-\alpha\lambda_j)^2}.
\]

**Derivation:** each non-consensus eigenmode is an AR(1) recurrence driven by innovation variance `s^2`. Its stationary variance is `s^2/(1-mu_j^2)` if `|mu_j|<1`. Sum the modal variances. This is not the disagreement *per vertex*; that would divide the result by `n`.

These formulas depend on the **full** non-consensus spectrum. Fixing a scalar index and graph size does not fix this spectrum. RP-001 demonstrates this limitation in one deliberately simple case.

## Important negative cases

- `alpha >= 2/lambda_n`: some disagreement mode does not contract; the stationary expression is undefined/divergent.
- A disconnected graph has additional zero eigenvalues and no global consensus contraction.
- Signed or directed interactions need different analysis; the symmetric spectral proof cannot simply be reused.
- Delays greater than one step change the state dimension and characteristic equation; the no-delay formula cannot be reused silently.
- Temporally correlated or state-dependent noise invalidates the simple stationary covariance formula.
- A graph can maintain its existing pattern rather than converge to consensus. Consensus is just one declared operational version of relational persistence, not its universal definition.

## Independent arithmetical counterexample

Fix externally assigned proxy numbers `B=1`, `I=0.01`, `tau=1`. Consider `x[t+1] = a*x[t] + eta[t]` with i.i.d. noise variance `0.01`. At `a=0.5`, stationary variance is finite (`0.01/(1-0.5^2)`). At `a=1.1`, no finite stationary variance exists. Both are consistent with the same proxy triple. The missing property is the **dynamic gain `a`**. The counterexample is conditional on the specified interpretation; do not assert that it refutes all possible redefinitions of `B`, `I` or `tau`.

## Connection to other research

The PMFF's local operational kernels are not uniquely selected by relational locality or affine invariance alone. Its own Proposition 4.2 is an underdetermination warning, not a derivation of this graph dynamics. A bridge from PMFF `(R,q,mu,K,pi)` to `W` or to a measured persistence outcome must be supplied and tested separately.

## References

See `docs/literature/PRIOR_WORK.md`. The spectral method and network consensus relation are part of the existing literature, notably Olfati-Saber, Fax and Murray (2007). The AR(1) variance argument is classical time-series analysis.
