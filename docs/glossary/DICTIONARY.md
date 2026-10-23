# Research dictionary (version 0.1)

Terms must carry units, observation rules, assumptions and identifying limitations. Similar-sounding concepts are not automatically interchangeable.

| Term | Symbol | Type / units in RP-001 | Operational meaning | Important limitation |
|---|---|---|---|---|
| Relational persistence | no canonical symbol | not yet universal | A family's capacity to preserve or recover a declared organization after disturbances | Must specify function and time horizon before measuring |
| Coordination recovery residual | `r_T` | dimensionless | Maximum relative mean-zero disagreement after T no-noise consensus steps | Smaller is better; is not a survival probability |
| Update capacity proxy | `B` | update / step | Fixed one local update cycle per time step | Distinct from physical bytes/sec or operations/sec |
| Noise variance | `I = s²` | square of signal units | Per-node centered, independent disturbance variance | Not Shannon entropy, not uncertainty in general |
| Response latency | `tau` | steps | A single-step response in RP-001 | Fixed to 1; this experiment does not identify delay effects |
| Scalar index | `C` | dependent on proxy conventions | `B/(I*tau)` | Proposed only; not calibrated to outcomes |
| Dynamic coupling | `alpha` | reciprocal of Laplacian scale | Fixed strength of consensus relaxation | Not to be inferred after seeing results |
| Adjacency | `A` | dimensionless for unweighted graph | Presence of a relation | Direction, sign, and edge weights omitted |
| Laplacian | `L` | dimensionless under graph convention | `D - A` | Not a physical spatial Laplacian without a bridge |
| Connectivity | `lambda_2` | dimensionless | Second-smallest eigenvalue of L | Meaningful only for defined L and symmetry assumptions |
| Worst-case contraction | `rho` | dimensionless | Largest absolute non-consensus eigenvalue of W | Model-specific and noise-free outcome |
| Stationary disagreement | `E||Pi*x||²` | square of signal units | Expected total centered square deviation under stationary innovations | Not independent real-world observation here |
| Transition kernel | `K` | probability map | PMFF operation, distinct from declaring W | A particular kernel requires explicit extra assumptions |
| Relational mark | `q` | unspecified | PMFF transition label/score | No physical scale or unique interpretation yet |
| Base structure | `R` | abstract relation | PMFF primitive relation | Not automatically a measured social/network edge |
| Measure | `mu` | unspecified | PMFF weighting/measure structure | Depends on representation and reference measure |
| Occupation measure | `pi` | unspecified | PMFF state/weight measure | Not interchangeable with stationary distribution in every model |
| Observed graph | karate topology | edge set | Zachary's measured club relationships via NetworkX | Hypothetical consensus dynamics are not measured |

## Dimension audit

For the earlier informal use, if `B` is updates/second, `I` dimensionless and `tau` seconds, `B/(I*tau)` has units `seconds^-2`. It is **not dimensionless** merely because of its quotient form. RP-001 fixes a discrete-time numerical convention; cross-domain comparisons need explicit reference scales `(B0,I0,tau0)` or a declared dimensional calibration factor.

## Versioning

New meanings require a new protocol and documented migration, not retroactive edits to test inputs. A different operationalization can be scientifically legitimate, but it is a different hypothesis until a linking theorem is proved.
