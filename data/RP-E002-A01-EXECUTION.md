# RP-E002-A01: reproducible execution and source-rights boundaries

The frozen scientific protocol is
[`docs/preregistration/RP-E002-A01.md`](../docs/preregistration/RP-E002-A01.md).
This page explains operational prerequisites; it is not a new
preregistration and must not change the registered acceptance rule.

## Why METR-LA can be used

The selected *version-specific* record is
[Zenodo 5146275](https://doi.org/10.5281/zenodo.5146275), attributed to
Semin Kwak, citing Li, Yu, Shahabi, and Liu (ICLR 2018, DCRNN).
On 2026-10-23/24 UTC, a **read-only GitHub Actions metadata audit**
[#40043820752](https://github.com/DevHabito/relational-persistence/actions/runs/40043820752)
reported:

- record ID: `5146275`
- DOI: `10.5281/zenodo.5146275`
- metadata license: `cc-by-4.0`
- access rights: `open`
- file: `METR-LA.csv`, 72,802,450 bytes
- expected checksum: `md5:d3adaa79856bf610f25558fc242c7190`

The DCRNN sensor IDs and road-distance graph belong to
[the original DCRNN research implementation](https://github.com/liyaguang/DCRNN).
They are not recomputed from the speed time series. The preprocessing
reproduces the source's Gaussian distance weighting and threshold 0.1,
then drops self-edges and normalizes the remaining observed neighbors
when forecasting.

The [Caltrans PeMS data-source page](https://dot.ca.gov/programs/traffic-operations/mpr/pems-source)
describes its historical traffic detector data. The
[Caltrans conditions of use](https://dot.ca.gov/conditions-of-use)
generally treat information provided on the department website as
public-domain unless noted otherwise, while cautioning about
third-party copyrights. This audit does **not** grant a blanket
redistribution license for every possible Caltrans-derived resource.

**No raw traffic speeds, spatial graph files, or proprietary pretrained
models may be checked into this repository.** GitHub Actions keeps raw
downloaded inputs inside its ephemeral runner and publishes only
small experimental result and provenance JSON summaries. Any downstream
reuse of raw files must independently respect source terms.

## Manually reproducing without changing the study

The frozen executable requires Python 3.11+, NumPy and the inputs
below:

```text
data/raw/METR-LA.csv
data/raw/graph_sensor_ids.txt
data/raw/distances_la_2012.csv
```

Download from the version-specific Zenodo record and the original
DCRNN `data/sensor_graph` directory after reviewing the relevant
rights. **Never** substitute a differently versioned speed file with
the same name: the pinned MD5 mismatch must terminate evaluation.

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m experiments.rp_e002_metadata --output provenance.json

python -m experiments.rp_e002_benchmark \
  --speeds data/raw/METR-LA.csv \
  --sensor-ids data/raw/graph_sensor_ids.txt \
  --distances data/raw/distances_la_2012.csv \
  --output results/rp-e002-a01.json
```

When available, use
[`RP-E002 Frozen Observational Run`](../.github/workflows/rp-e002-observational.yml)
in GitHub Actions to run this on a hosted runner, avoiding any
installation or data storage on a personal computer. The cloud workflow
must not publish raw input artifacts.

## Predeclared outcome interpretation

`H1_restricted_predictive_gain` means the one-hop graph model
meets **all six** frozen 1%-improvement comparisons on held-out
data, three horizons against the stronger temporal baseline and
three against the permuted graph. Any failure is recorded as
`H0_not_rejected`, not discarded. This is a descriptive
benchmark decision, not a formal statistical claim of
population-level significance.

The target mask excludes zero speeds as ambiguous reports; the
zero-inclusive alternative is recorded without refitting test
hyperparameters. A zero should **not** be asserted to be sensor
failure without supporting source metadata. The five-minute
sample interval cannot be treated as response latency.

The `capacity_noise_latency_identification` field must remain
`NOT_IDENTIFIED`. The model code and Lean 4 theorem modules have
different epistemic roles: Lean verifies stated mathematics;
it does not certify that traffic sensor observations or a
forecast model describe a physical persistence mechanism.
