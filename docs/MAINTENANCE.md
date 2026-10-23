# Maintenance and verification policy

## Repository preparation

The first local commit contains only the RP-001 preregistration and was tagged `rp-001-preregistered` before scientific code was added. Publication to GitHub is a separate operation: an exported zip is not a published repository and GitHub topics require repository settings access.

## Source control

- Small, descriptive commits. Preserve failed results.
- Never rewrite preregistered definitions to make a result pass; create a new protocol with a new ID instead.
- Keep scripts in `experiments/`, production math routines in `src/`, unit/adversarial tests in `tests/`, and provenance reports in `docs/`.
- Every generated output gets a source script and declared assumptions.
- Run tests in CI after GitHub publication. CI configuration being present does not mean cloud CI has already run.

## Publication audit checklist

- Git tag points to the preregistration-only commit.
- Inputs and decision threshold match the original frozen protocol.
- Running the code yields values within fixed numerical tolerance.
- Cite original graph-theory and control literature.
- GitHub repository is explicitly **public** and has the agreed description/topics.
- The repository URL is checked after publication; do not claim publication based on a prepared folder.

## Corrective release note

`rp-v0.1.1` includes an explicit full-text software license, a corrected claim-ledger status after executing RP-001, and a cleaned unused import. The preregistration tag and experiment parameters are unchanged. The previous local `rp-v0.1.0` tag remains in history.
