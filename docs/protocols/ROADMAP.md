# Research roadmap and stop conditions

## Stage 0 — methodological baseline (this commit)

- Register RP-001 before computation, preserve immutable tag and Git history.
- Execute an independent dynamical outcome calculation, negative controls, and a counterexample.
- Publish the known mathematical source of every result. Make failed cases first-class artifacts.
- Report dataset provenance and be explicit where the dynamics are synthetic.

## Stage 1 — derivations, bounds, and obstructions

- Classify the exact assumptions that make the quotient index predict a chosen persistence observable.
- Construct minimal graph families with identical proxy triples but divergent persistence outcomes.
- Study delay and noise correlation; compare models with matched degree sequences and alternative spectra.
- Validate analytical derivations with independent implementations, interval bounds where appropriate, and limited Lean 4 formalization of clean lemmas.

## Stage 2 — real-world performance measurements

- Choose a public dataset with observed capacity/update rates, measured noise/uncertainty, response delays, and an independently observed failure/recovery target.
- Freeze proxies, exclusions, preprocessing, temporal split, baselines, error measures, primary effect size, and falsification thresholds before target evaluation.
- Estimate parameters only on training windows. Use held-out or time-forward test windows, calibration plots, uncertainty intervals, permutation/negative controls, and sensitivity analyses.
- Compare index-only predictors against constant, single-variable, simple linear, topology-aware and domain-standard baselines.
- Do not equate real graph edges with real measured stability outcomes.

## Stage 3 — relationship to RZS and PMFF

- Demand a typed and dimensionally consistent mapping from `(R,q,mu,K,pi)` to observed quantities.
- Test invariance under relabeling and admissible gauge changes. Search for nonidentifiability and nonclosure counterexamples.
- Separate abstract theorems, empirically supported restricted models, and physical conjectures.

## Stage 4 — external review

- Short stand-alone papers; independent reproduction; explicit adversarial review and rejection criteria; archived versions; no premature universal claims.

## Non-negotiable stop conditions

- A core equation becomes undefined for ordinary admissible inputs without a declared limit.
- A target metric was computed from the candidate index rather than observed independently.
- A parameter is chosen using test outcomes without disclosure.
- An assumption is added only after observing a failed result and then presented as preregistered.
- Public source data are missing, ambiguous, or contradictory and cannot be resolved.
