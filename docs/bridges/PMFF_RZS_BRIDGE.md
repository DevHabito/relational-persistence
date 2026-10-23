# Potential bridge to RZS and the precategorical archive

This document is a **list of unproved interface obligations**, not a unification result.

## Proposed interface

- Select a measurable finite relational structure from the PMFF base relation `R`.
- Determine what aspects of `q` are observable and invariant under the declared gauge transformations.
- Explain how `mu` and `pi` are measured or normalized, and whether coarse-graining commutes with model evolution.
- Derive or explicitly choose a transition kernel `K`, giving all assumptions. Do not pretend locality or equivariance uniquely forces its exponential/logit form.
- Derive any interpretation of capacity, noise and latency from the declared dynamics with dimensional bookkeeping.
- Derive an independently observable persistence outcome; do not define it to be the candidate index.

## Current obstruction

PMFF's local kernel analysis admits multiple different kernels under the same symmetry and invariance constraints (Proposition 4.2 in its foundational draft). Distinct kernels can produce different spectra and hence different persistence outcomes on the same static relation. Any claimed universal map from bare relational primitives to dynamics requires additional structure.

## Proposed formalization

Lean 4 may be used for small theorems once the mathematical statement is fully fixed, such as the invariance of the scalar index under relabeling of vertices only when the proxy extraction is relabeling-invariant. We do not claim any current Lean 4 proof, because none was executed in this repository baseline. Real-number spectral theorems should not be presented as verified merely because a Python test passed.
