# RP-U009-P01-D01 — Post-failure source representation diagnostic, not the original preregistered result

**17 November 2026, written AFTER first authentic source failure.**

The frozen P01 protocol (commit `2c36bd9b84ac664798e544f24b3617c1f7b5a258`) required a binary `LPS` low-pressure signal and two complete event windows from the official UCI MetroPT-3 archive. Its first original hosted study, workflow [#44212185197](https://github.com/DevHabito/relational-persistence/actions/runs/44212185197), ran only after 17 targeted synthetic controls and 852 full Python 3.12 regressions passed. The original download from UCI dataset 791 completed with **218,381,995 bytes**, SHA256 **`aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a`**, but the parser rejected the original source with `LOW_PRESSURE_SWITCH_MUST_BE_BINARY` while reading the selected windows. The first original result is conclusively **`RP_U009_SOURCE_OR_WINDOWS_INVALID`**. This exact 1,170-byte JSON is archived unchanged at `docs/results/RP-U009-P01-first-run/audit.json`, SHA256 `0b74889ed609a43d8924880e702d93fb8e723fd517fd718734463125991c13e3`; the original Actions artifact ID is 14386602132.

This addendum **does not** retrospectively make P01 valid, change source selection, alter repair times, pick different windows, modify pressure thresholds, or authorize a claimed P01 preregistered success.

## Diagnostic restricted to source coding, with no pressure outcomes

A second, clearly labeled hosted run **D01** may download the same *official* UCI ZIP and require **exact** ZIP byte length and original SHA256 already observed above. It may list the distinct **literal text tokens in the `LPS` column**, with per-token counts separately in each of the same four frozen P01 windows and across all source rows. It may check the original `timestamp` for parseability and monotonicity and enforce the original 1,516,948-row count and expected header. It must **not read, report, compute, print, plot or infer any `Reservoirs`, motor-current, pressure occupancy, maintenance recovery or other functional result**. The diagnostic may report only the first and last timestamp labels and observed sampling interval distribution; the source data cannot be copied into the research repository.

The diagnostic has an objective classification:
- `RP_U009_D01_BINARY_TEXT_ENCODING_ONLY` if all window LPS values are a subset of the literal set **`{"0","1","0.0","1.0"}`**, and all original source IDs/counts pass.
- `RP_U009_D01_UNEXPECTED_LPS_SEMANTIC_VALUES` if any other literal value appears, reporting counts and lexemes without silently assigning meanings.
- `RP_U009_D01_SOURCE_INCOMPLETE` if source identity or row/timestamp census fails.

If the first case holds, a *future separate secondary study P02*, explicitly marked **post-failure schema correction**, may accept precisely numeric 0.0 and 1.0 as the binary 0 and 1 while preserving P01's event selection, summaries and mathematical decision. The secondary result can be called a **post-source salvage/reanalysis**, never the first preregistered P01 result. No use of outcome metrics to adjust the parser is permitted.

The purpose is to distinguish a formatting mismatch from a physically nonbinary measurement. Negative findings have equal evidentiary value. This document is transparent about having been prepared **after** encountering original source data.
