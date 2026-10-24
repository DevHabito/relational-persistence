# Observational data policy

No raw external performance-measurement dataset is committed to this
repository. The Zachary karate-club graph is an observed **topology**
used with synthetic linear-consensus dynamics in the exploratory study.

**RP-E002-A01 has now analyzed genuinely observed METR-LA traffic
speed trajectories**, in an ephemeral GitHub Actions runner. Only
the preregistered evaluation code, aggregate metrics, hashes and
negative experimental findings are in this Git repository.

- [Frozen observed-data protocol](../docs/preregistration/RP-E002-A01.md)
- [Source acquisition/rights and execution guide](RP-E002-A01-EXECUTION.md)
- [First observational outcome: H0_not_rejected](../docs/results/RP-E002-A01.md)
- [Reproducibility and aggregate metrics](../docs/results/RP-E002-A01.json)
- [Source-data and first evaluation run](https://github.com/DevHabito/relational-persistence/actions/runs/40043981617)

All external datasets require versioned sources, rights verification,
acquisition date, strong checksums, missingness policy, documented
units/time alignment, a frozen independent target, and a leakage
audit. Never replace unavailable observations with synthetic values
while reporting them as real measurements.

This observational benchmark does **not** independently measure
physical capacity `B`, noise `I`, latency `tau`, or causally
identified perturbation/recovery events. Its recorded failure is a
scientific result about one forecast comparison only.
