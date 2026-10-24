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

## RP-F002: optimal star squared-energy bound (verified)

- **Proof:** `StarSharpEnergy.lean` proves `star_twenty_squared_energy_optimal`.
- **Exact value:** `(81/100)^20` is the least *uniform squared-energy* coefficient for the mean-zero six-node star model, attained by the nonzero leaf-disagreement vector.
- **Successful Lean CI:** [#40038735921](https://github.com/DevHabito/relational-persistence/actions/runs/40038735921), proof commit `9c6318214927b745b3e5166491f4783731464077`; merged through [PR #6](https://github.com/DevHabito/relational-persistence/pull/6).
- **Independent check:** [PR #7](https://github.com/DevHabito/relational-persistence/pull/7) computes exact Laplacian characteristic polynomials with rational determinant arithmetic; CI #40038774188 passed. This test is **not** a Lean proof of spectral identities.
- **Subsequent progress:** the star ratio supremum was verified in Lean #40041114514 and merged through PR #8; the exact P6 eigenmode was verified in Lean #40040392019 and merged through PR #9. The P6 **maximality** theorem, full formal spectral decomposition and empirical interpretation remain open.

## RP-F002: exact star norm supremum and attained path mode (verified)

- **Star graph:** `StarSharpNorm.lean` proves `star_residual_supremum`, namely `sSup starResidualRatios = (9/10)^20`. The supremum is **attained** by a nonzero mean-zero real graph state; all real graph states satisfy the proved upper bound.
- **Star verification:** [Lean #40040591471](https://github.com/DevHabito/relational-persistence/actions/runs/40040591471) passed the proof branch, and [combined Lean #40041114514](https://github.com/DevHabito/relational-persistence/actions/runs/40041114514) passed after reconciling the imports with the P6 module. [PR #8](https://github.com/DevHabito/relational-persistence/pull/8) merged at `817d3dbf32511cda923c05f91f6ba4a8b7d2dcf7`.
- **Path graph:** `PathSlowEigenmode.lean` proves an explicit mean-zero real eigenmode, gain `(8+sqrt(3))/10`, its 20-step iterate, and that the resulting ratio is **attained** by a nonzero graph vector. [Lean #40040392019](https://github.com/DevHabito/relational-persistence/actions/runs/40040392019) passed. [PR #9](https://github.com/DevHabito/relational-persistence/pull/9) merged at `d71aa20ae56e6fc7542c257c06fe683cb7d30179`.
- **Still open:** exact maximality of the path eigenmode, formalization of the full symmetric Laplacian spectrum and numerical equality with the reported floating-point metrics. Classical prior attribution remains required.
- **CI repair history:** the star supremum proof initially failed over square-root algebra and a calc target mismatch; all failed runs remain accessible in the PR history. No `sorry`, `admit` or unsupported axioms were used in the accepted proofs. Compilation is mathematical validation of a declared model, not empirical verification.

## RP-F002: exact real path supremum — formal certificate verified

- **Result:** `PathSharpSOS.lean` proves `path_residual_supremum`:
  `sSup pathResidualRatios = ((8+sqrt(3))/10)^20`. Every nonzero
  mean-zero real P6 graph vector satisfies the sharp upper bound;
  the eigenmode in `PathSlowEigenmode.lean` attains it.
- **Proof technique:** an exact polynomial identity writes the one-step
  squared-energy contraction defect as a sum of four nonnegative squares,
  after imposing the zero-mean condition. The single algebraic identity
  `sqrt(3)^2 = 3` is handled explicitly. The upper bound is propagated
  through exactly 20 synchronous steps, transported to graph vectors,
  and combined with an attained witness to establish the supremum.
- **Successful formal run:** [Lean #40042195359](https://github.com/DevHabito/relational-persistence/actions/runs/40042195359);
  exact proof commit `62bfe03e9bebd3f26ff107f206587f18c4b21e76`.
  [PR #10](https://github.com/DevHabito/relational-persistence/pull/10)
  merged into `main` at `563bab0e4cfe47c6440b479cf7cc104f22a9555a`.
- **Independent arithmetic regression:** [PR #11](https://github.com/DevHabito/relational-persistence/pull/11)
  merged at `5832de51ad4d3b1914eeb22cf02a8bd8d3d700ae`; Python and Lean
  CI passed at [#40042154236](https://github.com/DevHabito/relational-persistence/actions/runs/40042154236).
  The tests compare 36 matrix entries in exact `Q(sqrt(3))` arithmetic,
  verify zero-sum eigenmode and check coefficients without float rounding.
- **Exact residual pair now proved in Lean:** `r20(P6) =
  ((8+sqrt(3))/10)^20` and `r20(S6)=(9/10)^20`, with ratio
  sets defined over all nonzero mean-zero real six-node graph states.
- **Scope:** these results are conditional instances of classical finite
  graph spectral theory. The full graph-family spectral theorem, any
  newly proposed physical law, PMFF derivation and observational
  identification of `B`, `I` and `tau` are **not** established.
- **Failed attempt retained:** CI #40041966015 initially rejected a
  real-valued executable definition; the type-correct noncomputable
  declaration compiled successfully without weakening the theorem.

## RP-F003: matched-degree one-step finite witness — Lean verified

- **Frozen protocol:** RP-F003-A01, preregistered at commit `96965042` before exhaustive graph computation.
- **Theorem:** `matched_degree_graphs_have_distinct_updates` in
  `RelationalPersistence/DegreeMatchedWitness.lean`, supported by
  `matched_degrees_at_every_vertex`, `matched_initial_zero_mean`,
  `matched_cycle_first_component` and `matched_triangle_first_component`.
  For two explicit connected six-vertex graphs whose degree at each labeled
  vertex is the same, the same mean-zero rational state gives one-step
  values `7/10` and `3/5` at vertex zero.
- **Accepted verification:** [Lean 4 workflow #40118067207](https://github.com/DevHabito/relational-persistence/actions/runs/40118067207),
  **completed successfully** for proof commit `ecb807a5306b6180b46599c20dd6dceda11a8265`;
  [PR #20](https://github.com/DevHabito/relational-persistence/pull/20)
  merged at `725bc9aba12887a623b449e3b3ff3ca20fd5f63a`.
- **Failure preserved:** initial [Lean workflow #40117482503](https://github.com/DevHabito/relational-persistence/actions/runs/40117482503)
  failed because four finite cardinality proof obligations remained
  unsolved. The correction discharged these finite goals with `decide`,
  without changing the hypotheses, preregistration or result.
- **Separate computation:** exact 20-step maximum `Q20` difference on all
  degree-matched connected six-vertex graph pairs was found by integer
  enumeration and checked by hosted Python regression
  [#40118067163](https://github.com/DevHabito/relational-persistence/actions/runs/40118067163).
  **It is not a theorem formalized in Lean 4.**
- **No inferred physics:** neither the finite graph algebra nor successful
  CI demonstrates a fundamental stability law or a physical observable.

## RP-F004: correlated-noise moment fixed points — Lean verified

- **Preregistered model:** `docs/preregistration/RP-F004-A01.md`;
  frozen before implementing F004 at `1ef43702931de3498d8cd9218563fa276b3dc3aa`.
- **Proposed Lean scope:** `RelationalPersistence/ColoredNoiseMoments.lean`
  checks two rational second-moment fixed points, proves uniqueness
  **over rational moment pairs** for two specified correlation
  parameters, and their exact variance separation `2/225`.
- **Not formalized:** construction of the Markov noise process on a
  probability space, conditional-expectation identity, convergence to
  the stationary second moment, empirical measurements, PMFF bridges,
  and any universal physical relationship.
- **Formal verification status:** [Lean 4 CI #40120059074](https://github.com/DevHabito/relational-persistence/actions/runs/40120059074) **passed** on exact PR head `4601bbdcccfee8e12a97a56835073498a7f5b820`; [PR #21](https://github.com/DevHabito/relational-persistence/pull/21) was merged at `8382ac0ba85c640323db1942efc817458adf9fbf`.
- **Independent numerical-method check:** RP-F004's separate 4096-path
  exact rational enumerator compares the twelve-step outcome with the
  moment recurrence; Python 3.11/3.12 [CI #40120059073](https://github.com/DevHabito/relational-persistence/actions/runs/40120059073) passed **148 regression tests** per runtime. This finite check is not a Lean proof of an infinite-time limit.

## RP-F005: real feedback-delay period-six obstruction — awaiting new Lean CI

- **Preregistration:** RP-F005-A01, commit `1e4addb833e12eca487cdfce7ad61ad5029213b5`, registered before implementation and results.
- **Submitted scope:** `DelayedFeedback.lean` encodes a real two-state delayed feedback map at gain one. Statements include a cube-equals-negative-identity component identity, sixth-iterate identity for **every real two-state initial condition**, one-step undelayed extinction, the registered squared-residual separation, and an explicit obstruction to uniform strict six-step squared-energy contraction.
- **Formal status:** source added; these RP-F005 declarations require **successful pinned Lean CI** before they can be reported as machine verified.
- **Separate arithmetic:** an exact rational scalar-history iterator and an independent companion-matrix power implementation compare the six registered gain/delay cases for all 25 times, with primary decision checked against frozen threshold 1/2. This does **not** prove arbitrary delayed systems stable or unstable.
- **Not proved:** real measured response latency, the general Schur stability region, PMFF/RZS connection, stochastic or empirical response outcomes.
