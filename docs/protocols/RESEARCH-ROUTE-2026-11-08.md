# Research route and decision gates — 8 November 2026

**Repository:** DevHabito/relational-persistence  
**Baseline:** `main` at `214133c5eb33f68cb55f2e10f4b8008097d8d4e8` (3 November 2026).  
**Status:** methodology and work plan only. This document is **not** a preregistration, new experiment, executed test, independent replication, or claim of novelty.

## Purpose

The question is whether a precisely stated function of a relational system can persist or recover after a disturbance, and whether the mechanism has predictive content beyond existing theory and operational baselines. There is no reason to expect one scalar or one mechanism to describe all biological, chemical, physical and computational systems. That possibility must be tested, not assumed.

The foundational questions remain distinct:

1. **Scalar sufficiency:** within a stated domain, can a proposed small set of observables adequately predict a defined persistence outcome?
2. **Derivation:** can a proposed relation be derived from independently justified dynamics, without selecting assumptions to fit a desired outcome?

Neither question is settled by a finite graph witness or a passing Lean build. The status definitions in `docs/foundations/SCOPE.md` remain binding.

## Initial read-only reconnaissance (8 November 2026)

The repository metadata, the complete tree listing, selected scientific reports and source files, and GitHub Actions metadata were inspected through the connected GitHub API. The tree endpoint returned 1,024 files and was not truncated. The latest inspected `main` commit was `214133c5`.

- GitHub Actions reported **success** for the research regression workflow `41729820069` and Lean workflow `41729820054` on that exact commit. The tests were **not rerun independently** during this reconnaissance. Neither outcome verifies external scientific validity.
- The original RP-U004 report records a finite, synthetic, preregistered F2 comparison of 3,386 lookahead versus 3,286 greedy successful case-ticks, with 66 scenario wins, 2,784 ties and no losses. These are *reported archived results*, not recomputed values from this session.
- The same report records 53,410 function-table lookups for each lookahead variant against 28,450 for each greedy variant. Common information does not imply equal computational cost.
- A subsequent retrospective Lean certificate establishes equivalence of the two lexicographic priority rankings for nested Boolean objectives with F2 implying F1. The original six policy labels therefore include redundant objective-order variants. This is not independent support for a distinct policy effect.
- **Documentation inconsistency to fix separately:** the first RP-U004 section of `docs/protocols/ROADMAP.md` still calls the Boolean ranking proof a future task, whereas `docs/formalization/STATUS.md` records the completed proof, PR #68 and successful Lean run `41726943161`. Preserve both historical dates and the original preregistration; make a narrowly scoped correction in a later change.
- The RP-E012-D03 record authenticates one complete original machine-event object but explicitly does **not** certify a complete causal scheduler state spanning machine, instance and collection events. It is inappropriate to treat the existing prefixes as a chronological or complete held-out population.

No evidence of failed tests, altered archived bytes, or new empirical validation is claimed by this initial read.

## Working rule: one question, one gate, one outcome

For each new study, write and review the following **before** obtaining the designated target outcomes:

- Exact question and the most important competing explanation.
- Domain, population, units, time origin, observation availability and one primary outcome.
- Published prior methods and an explicit established baseline; neither ordinary graph connectivity nor two-step lookahead is novel.
- Hypotheses H0/H1 and their operational predictions, including a negative or null result.
- Selection rule, exclusions, missingness policy, controls, effect size, tolerance, work budget and stopping rules.
- Data provenance (publisher, license, acquisition date, version, checksums), stable input identifiers and holdout boundary.
- Independent oracle or implementation, adversarial counterexample search, regression and stress-test plan.
- The expected status on failure: computation defect, model falsification, underidentification, inconclusive evidence, or supported-within-scope.
- Frozen protocol commit, first-run archive and follow-up chronology. Exploratory work is clearly labeled and never retrospectively called preregistered.

A test passing its own implementation checks cannot validate a scientific model whose measured target is defined by that same code.

## Route 0 — Verify the evidence chain before expanding the model

**Small question:** can an independent implementation reproduce the exact archived RP-U004 outputs from frozen input records without using the production scorer?

1. Record the exact parent commit, repository tree and the SHA-256 of every input under test.
2. Review first-run manifests, source acquisition rules and the immutable first report. Do not edit them.
3. Execute the available unit/regression suite under the pinned dependency environment, record both pass and fail outputs, and check current Python 3.11/3.12 and Lean 4 coverage.
4. Run the already committed independent U004 replay and diagnostics, comparing every case, oracle, score, offline envelope, tie and operation counter, not just aggregate totals.
5. Introduce **temporary** controlled corruptions on separate copies (score flip, case omission, changed source hash, false F2 on an F2-absent graph) and verify that guards reject them. Restore originals; never commit corrupted data as results.
6. Identify any assumptions about label order, source selection, cache behavior and computational cost that remain untested.

**Pass:** complete byte identity, source invariants, case-level replay and expected corruption rejections.  
**Fail:** any mismatch is a computation/provenance failure pending diagnosis; do not interpret the physical model.  
**Output:** dated English audit and a concise list of independently reproduced versus merely reported claims.

## Route 1 — Literature, novelty boundaries and dictionary

Build a source-checked bibliography by *claim*, not a loose list of adjacent papers. Capture authors, original publication date, journal/version, DOI, corrections, methods, domain and exact relationship to our claims. Inspect original publisher or institutional records; separately record the actual verification date. Search older graph connectivity, reliability theory, network repair, temporal graphs, control/feedback, ecological resilience, chemical reaction networks, molecular biology, statistics and observational research methods. Do not claim an exhaustive priority search without one.

Two useful cross-checks at planning time:

- Hu, Yeung, Yang, Wang and Zeng, **14 April 2016**, “Recovery of infrastructure networks after localised attacks,” *Scientific Reports* 6, 24522, DOI [10.1038/srep24522](https://doi.org/10.1038/srep24522).
- Wang, Cetinay, He, Liu, Van Mieghem and Kooij, **17 October 2023**, “Recovering Power Grids Using Strategies Based on Network Metrics and Greedy Algorithms,” *Entropy* 25(10), 1455, DOI [10.3390/e25101455](https://doi.org/10.3390/e25101455). The paper explicitly includes greedy and two-step greedy repair strategies.

Both sources predate the repository's U004 study. They should constrain novelty claims, not be treated as validation of our model.

Every glossary entry must specify symbol, mathematical type, units, measuring instrument or oracle, time of availability, assumptions, known synonyms, failure cases and whether it is established literature or an internal definition. New meanings require a versioned change, not a silent rewrite of prior methods.

**Pass:** each active claim maps to verified prior work and an operational definition.  
**Fail:** an undefined observable, unclear units, or an uncited novelty assertion blocks further inference.

## Route 2 — Small mathematical propositions and exact certificates

Only formalize one precise statement at a time. For each, supply the assumptions and a counterexample to at least one removed assumption where feasible. Prove the statement in the pinned Lean 4 toolchain (`leanprover/lean4:v4.20.0` at this baseline), retain the exact declaration names and CI commit, and reject `sorry`, `admit`, hidden axioms, or changing the proposition to evade a failed proof.

Use exact rational/integer enumeration where practical; numerical tests serve as additional checks, not replacements for proofs. Distinguish a theorem about Boolean rankings from proofs about graph oracles, scheduling code, and physical observations. If another prover or SMT solver is introduced, record its version, axioms, encoding and trust boundary.

**Pass:** a checked conditional statement and documented statement-to-code limits.  
**Fail:** proof failure or a counterexample is preserved, with no unjustified weakening.

## Route 3 — Computational engineering, regression and stress

Use small, pure, typed functions and separate acquisition, parsing, model definitions, experimental policy, independent oracle and reporting. Prefer reproducible pinned versions, deterministic fixtures, CI on clean environments, and logs that include seeds and resource limits.

Test ordinary, boundary, invalid and deliberately adversarial inputs. Include exact oracle agreement; exhaustive small-instance enumeration; random or property-based tests **with fixed seeds and recorded generators**; metamorphic/relabeling checks with explicit label-dependent tie rules; large-input CPU/memory profiling; numerical stability; and failure injection. Compare independent implementations where feasible. Make trial count and explored space explicit: millions of tests do not prove a universal theorem.

For policy comparisons, log real wall time and CPU work separately from modeled repair steps and truth-table lookups. Equal input information is not equal information-acquisition cost, algorithmic work or real repair cost. All policy budgets and metrics must be frozen before the next primary outcome is observed.

**Pass:** independent agreement within declared tolerances and known resource bounds.  
**Fail:** report the input and first divergence, without substituting a more flattering seed or threshold.

## Route 4 — Real source feasibility before a prediction trial

**First prospective question (source-only):** can a primary-source dataset provide a complete, independently checkable historical state that was *actually available before each decision*, together with an independent later recovery or service outcome?

**If yes:** define a new protocol for a small chronological held-out prediction/intervention comparison, with costs, meaningful baselines and a predeclared loss. A later positive result must beat the stronger baseline under the registered decision rule; a tie or negative result stays in the archive.  
**If no:** terminate with `SOURCE_NOT_CAUSALLY_CERTIFIED` or a more specific preregistered status. No predictive scores, post hoc data substitution or causal interpretation are allowed.

The official [Google Borg cluster-data documentation](https://github.com/google/cluster-data) is a primary-source candidate, not automatically an eligible prediction corpus. Its 2019 trace is real operational data but the repository's E012 work does **not** yet establish cross-table completeness and historically available online scheduler state. Before choosing a practical experiment, review data access, size, license, missingness, original event timestamps versus receipt time, true intervention cost and the availability of an independent outcome. Do not silently reuse revealed E010/E011 holdouts as blind evidence.

Any external test must clearly distinguish observational association, out-of-sample forecasting and causal intervention. Real biological, chemical and physical systems require domain-specific observables; a computer trace cannot verify a universal natural law.

## Route 5 — Cross-domain transfer and external replication

Consider a second domain only after the first has survived its own prospective external test. Freeze any proposed mapping between observables, units, mechanism and timescale. Test structural equivalences against counterexamples and negative controls. Publish a short stand-alone claim, code, provenance, negative results and unresolved assumptions for independent review.

A general physical or biological interpretation remains a conjecture unless independently justified by those measurements and discriminating predictions.

## Order of execution and stop conditions

1. **Now:** publish this planning document separately from `main`. It changes no experiments, data, thresholds or theoretical claims.
2. **Next:** Route 0 audit of U004 provenance, first-run replay and CI. Correct the stale ROADMAP sentence only in a separate reviewed documentation change.
3. **Then:** Route 1 dictionary/prior-art audit focused on the exact next question; Route 2 and Route 3 only for needed propositions and algorithms.
4. **Before any new primary outcomes:** freeze a separate, self-contained prospective protocol with falsification gates.
5. **Only after eligibility:** Route 4 external source acquisition and a first chronological prediction test. Route 5 is conditional on independent support.

Stop and disclose immediately if source completeness fails, calculations disagree, the primary outcome is mechanically circular, historical pre-decision availability is uncertified, an unsupported assumption is added after looking at outcomes, or the physical interpretation outruns the evidence.

## Evidence log conventions

Use the categories `REPORTED_NOT_RERUN`, `RERUN_AGREED`, `RERUN_DISAGREED`, `LEAN_CHECKED_ON_EXACT_SHA`, `MODEL_FALSIFIED`, `SOURCE_REJECTED`, `INCONCLUSIVE` and `SUPPORTED_WITHIN_SCOPE`. Record exact date, source/commit SHA, toolchain, command, test count, failed tests, resource budget, and links. No green status is inferred from an unexecuted test.

Do not modify frozen first-run output or replace a failed first run with a later successful run.
