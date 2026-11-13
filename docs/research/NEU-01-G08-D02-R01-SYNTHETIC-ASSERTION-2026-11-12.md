# NEU-01-G08-D02-R01 — Synthetic unit-test assertion correction before source access

**12 November 2026.** The first G08-D02 source-intended workflow **#43336398552** at implementation commit cbda4f544493c90234a8b2ea9266ed2fb7282cd5 was stopped by a failing synthetic test BEFORE ANY ORIGINAL EEG SOURCE ACCESS. Its first source step was skipped; no G08-D02 original source JSON was created.

The failing fixture had 4 frames x 3 channels, synthetic derivative D=3R+c[t] with arbitrary known common additive offset per frame. Under the prior frozen G08-D02 definition P(X)=X-channel_mean_per_frame, the model with fixed gain one has:

P(D)=3P(R).
||P(D)-P(R)||_F / ||P(D)||_F = ||2P(R)||_F / ||3P(R)||_F = **2/3**.

The algorithm correctly returned 0.6666666666666666. The **test** incorrectly asserted that the ratio must exceed 1. The independent slow-loop oracle and fitted-gain=3 assertions were not contradicted, and no genuine source-derived statistic was computed.

The only code change here corrects that exact expected synthetic assertion to abs(actual - 2/3)<1e-12. The original protocol, original G08 first source report, G08-D02 algorithm and all source identities remain untouched. This dated separate note is written before repeating pre-source tests and before ANY actual G08-D02 source read.

Preserve the failed CI run and do not hide it or recast it as a negative neuroscience observation. A successful later source run must be separately archived with its real job ID/SHA and post-archive regression. No new physics or physiology is claimed.

Original failed run: https://github.com/DevHabito/relational-persistence/actions/runs/43336398552 .
