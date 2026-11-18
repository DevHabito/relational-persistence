# RP-U009-P02 — A declared post-source representation-corrected secondary analysis

**17 November 2026. This is NOT the first preregistered P01 result and must never be labelled such.**

P01's original hosted source run #44212185197 produced an invalid result `RP_U009_SOURCE_OR_WINDOWS_INVALID` due to a strict textual parser for LPS. The unmodified first original audit is 1,170 bytes, SHA256 `0b74889ed609a43d8924880e702d93fb8e723fd517fd718734463125991c13e3`.

The subsequent, **post-failure** diagnostic D01 (source run #44212728803), restricted to timestamp and literal LPS tokens, established that the official UCI MetroPT-3 CSV contains exactly two original LPS representations, `0.0` (1,511,760 records) and `1.0` (5,188 records), including both fixed windows for the two published maintenance anchors. Original UCI ZIP is 218,381,995 bytes, SHA256 `aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a`. Original archived CSV is 218,300,507 bytes, SHA256 `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`, exactly 1,516,948 rows. The archived D01 JSON is 2,674 bytes, SHA256 `8020c11a460a97552777e75ac3be0c31c02cc535a3c5eaba8d8cdc376c5e5ee0`.

D01 did not examine reservoir pressure, motor current or functional outcomes. **However, the original diagnostic did reveal how often the LPS switch was active in each pre/post window**, so P02 is not fully blind to even the secondary physical signal. P02 must be treated as a **post-source technical salvage and exploratory descriptive comparison**, not as a clean independent preregistered confirmation.

## Single permitted amendment

Retain the complete P01 mathematical and chronological protocol untouched: same UCI source, same two eligible maintenance dates (June 8 at 16:00 and July 16 at 00:00), same four [−24,−2) and [+2,+24) hour windows, same 30-row and six-hour-bucket window gates, same Reservoirs less-than-7-bar threshold, same motor-current above-5-A and LPS controls, same no-imputation rule, same positive/nonpositive two-event criterion.

**Change only representation parsing**: accept an LPS raw string of `0.0` as integer state 0 and `1.0` as integer state 1, in addition to the original literal strings `0` and `1`. Every other token, including `0.5`, `2.0`, empty, `NaN`, `None`, signed alternative spellings or custom coercions is invalid. The original P01 source parser should remain strict by default; the new path must have an explicit opt-in `allow_decimal_lps=True`. A negative test verifies that the same original decimal token is **still rejected** by strict P01 mode, and an invalid token is rejected in both modes. No smoothing, fitting, imputation or post-outcome selection is permitted.

Before original secondary execution: run synthetic/adversarial tests for both P01 and P02 modes, verify the immutable P01 and D01 SHA256 archives, and run full repo Python 3.11/3.12 regressions. Source must be official UCI release with exact ZIP and extracted CSV hashes above. If source/window eligibility fails (including the 600-row June prewindow not spanning six distinct clock hours), preserve a negative P02 result and do not change windows. If all four windows pass, compute only the frozen P01 descriptive comparisons and mark final result as *P02 post-source reanalysis*. The first P01 result remains invalid irrespective of what P02 finds.

No causal maintenance effect, precise time-zone alignment, delivered air demand, generalizable network/physical resilience law, biological effect or formal Lean proof follows. Report the difference between 1-Hz descriptions and actual median 10-second sampling. Report the first failed attempt and the D01 correction trail in any publication or correspondence.

**P02 status before secondary reservoir-pressure access:** post-source schema correction registered; two publicly reported maintenance dates, D01 LPS counts and timestamp spacing known; pressure and motor-current results not yet calculated.
