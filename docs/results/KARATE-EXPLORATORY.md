# Exploratory application to observed network topology

## Observation and model must not be confused

Zachary documented a real social network in 1977. NetworkX ships a graph representation of its karate club ties. We used the built-in `networkx.karate_club_graph()` to obtain an **observed topology** (34 vertices, 78 edges). Edge weights are ignored under our stated unweighted baseline.

Then we imposed an **artificial**, fixed, undelayed linear consensus evolution with `alpha=0.04`, 20 steps, and independent hypothetical noise variance `0.01` on every node. No real participant's consensus dynamics, response times, error rates, capacities, or recovery trajectories were measured.

## Model calculations

Results are in `KARATE-EXPLORATORY.json`:

- Algebraic connectivity (`lambda_2`): approximately `0.4685252267`.
- Worst-case contraction factor: approximately `0.9812589909`.
- Noise-free 20-step residual: approximately `0.6849722559`.
- Hypothetical stationary total disagreement energy: approximately `1.8210931918`.

These are a **structural case study on real relational data**, not empirical evidence that the original group obeys the Relational Persistence program's dynamics. The original Zachary paper [DOI: 10.1086/jar.33.4.3629752](https://doi.org/10.1086/jar.33.4.3629752) is the observational source. Dataset representation comes from NetworkX.

## Next step

Acquire measured system dynamics (independent outcome) rather than merely a measured network. Freeze the hypothesis and baseline ahead of target inspection. A real input dataset alone does not validate a theory about an unobserved output.
