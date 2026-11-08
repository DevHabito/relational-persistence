# RP-U005-D07 — Exact-key linkage census, original ANEEL 2026 sources

**Date:** 8 November 2026. **Source branch parent:** D06 review head `337daec55ad288fc3cd05b0a5a50066ec3c4b0dd`.  
**Status:** source-only linkage audit protocol frozen **after** the D06 structural scan disclosed 6,789,484 occurrence and 6,078,331 interruption CSV rows with substantial phase-duration missingness, but **before the first D07 original-key result**. This is not a prospective new prediction of real recovery or an independent sample. No causal, physical or optimization claim is authorized.

## Narrow question

What are the unambiguous counts of *literal candidate key* matches between exactly the two existing ANEEL 2026 ZIP snapshots when keyed by (14-digit distributor CNPJ, four-digit competence year, two-digit competence month, original occurrence code)? How many rows have invalid keys, repeated keys, or a corresponding key in the other file? A **textual cross-reference** is not proof that a match represents the same real-world action or incident, and even unique textual keys do not identify counterfactual repair choices.

The already verified 2026 interruption dictionary describes `CodOcorrencia` as a reference to the emergency-occurrence dataset's `CodOcorrenciaEmergencial`. That is our *candidate linkage*; we will not assume it yields complete one-to-one matches.

## Fixed original population — no substitution or post-hoc selection

Only official exact D06 resource IDs, URLs and metadata verification rules may be used. **Before any original row is inserted**, re-download both compressed originals within the unchanged 240-MiB per-object budget, and require exact match of D06's already known whole-file SHA-256 and byte length:

- Occurrences: `176074116` bytes; `7ed1050092342916bc6e797f4dd79577ac84683956963e1f2c3be652a7876c8c`.
- Interruptions: `202900063` bytes; `87dd5be92a0752bedfffaa80090022182db359538b2fd0518c26537a26576e4d`.

While reading the complete ZIP CSV streams to EOF, independently check CRC and all original uncompressed-byte SHA-256 values against first D06 `736602782af54abb82bc9a73070bd09b7bd51213daf3ec22bd3a7dbba64e0567` (occurrences) and `4f7112502bffc3028ba69784d77f6b678c9068eb58742a6d57b66991a47528ce` (interruptions). Require the exact previously recorded original row counts (6,789,484 and 6,078,331), all registered 2026 required columns, strict UTF-8 and complete consistent CSV row width. No sampling and no source-row omission to improve the matching rate.

## Fixed candidate key and invalid-row convention

The **primary exact candidate key** is the concatenation of four **original unmodified strings**, separated by a nonprinting delimiter that is forbidden inside inputs:

1. `NumCnpjDistribuidora` (occurrences) or `NumCNPJDistribuidora` (interruptions): exactly 14 ASCII decimal characters, preserving leading zeroes. Do not strip punctuation or zeroes.
2. `NumAnoCompetencia` or `AnoCompetencia`: exactly the literal ASCII string `2026`. A different year remains counted as invalid for this defined 2026 snapshot, not silently reassigned.
3. `NumMesCompetencia` or `MesCompetencia`: exactly two ASCII digits `01` through `12`. Do not infer equivalent one-digit representations or coerce a time zone.
4. `CodOcorrenciaEmergencial` or `CodOcorrencia`: nonempty ASCII text, length at most 10 and no leading/trailing whitespace or reserved separator. Do not parse as integer or remove leading zeroes.

Preserve **every** original row in the source denominator even if invalid for a candidate key. For each source report total rows, invalid candidate-key rows, and nonexclusive reason counters (invalid distributor, year, month, occurrence ID). A malformed field does not prove the event itself is false. No raw identifier may appear in logs, errors, artifacts, repo or response.

## Frozen relational census

Build counts by exact valid candidate key for each source, using a **temporary on-disk SQLite** table of (literal key, source row multiplicity), not a Python in-memory dictionary of millions of original IDs. No raw rows are committed or uploaded. The original sources and the SQLite file are ephemeral and deleted after computing **aggregate counts only**.

For each source report:
- valid original **rows**; unique valid **keys**; keys occurring exactly once, keys repeated twice or more; total original rows on repeated keys, surplus rows beyond the first.
- Invalid-row count and nonexclusive reasons; source-row count still counts all invalid rows.

For the **exact four-field key across sources**, report:
- matched distinct keys; unique occurrence keys unmatched; unique interruption keys unmatched;
- occurrence **rows** with a matched key, interruption **rows** with a matched key; their unmatched valid-row complements;
- matched-key cardinality categories: one-to-one (`occ n=1, int n=1`), one-to-many (`occ n=1, int n>1`), many-to-one, many-to-many.

**Do not** compute the multiplication of repeats as a "number of physical incidents". These are only textual-key group statistics, not established causal relationships.

All counts must satisfy explicit conservation identities: each source rows = valid + invalid; valid rows = matched + unmatched within that source; unique keys = matched + unmatched, and each matched key belongs to exactly one cardinality category. A failure returns `INSTRUMENT_FAILURE`, never a positive source result.

## Resource and ethics constraints

- Hosted Ubuntu GitHub Actions, Python 3.11, no paid API, external datasets, mirrors, private connectors, credential exports or writes to original source.
- 240 MiB compressed per original, 5 GiB decompressed per member, complete CRC+UTF-8+CSV to EOF (reuse D06 source decoder). A temporary SQLite database is capped at **6 GiB** with bounded cache and batch insertion; no in-memory load of all 12.9M keys. Runner timeout 35 minutes. Never publish SQLite, raw CSV, distributor CNPJ, incident IDs or sampled rows.
- Only report grouped **integers**, SHA digests, file sizes and failure codes. No per-company or small-group statistics.
- If any input download, digest, malformed-row, CSV or storage invariant fails, return explicit `SOURCE_BLOCKED`, `SOURCE_OBJECT_CHANGED`, `SOURCE_SCHEMA_REJECTED` or `INSTRUMENT_FAILURE` and **do not** publish any partially computed join statistics as a verified original result.
- Do not call a successful source-key join `semantic_linkage_proven`; original reports need temporal interval/feeder checks before any incident interpretation.

## First-run outcomes

- `BOTH_SOURCE_KEY_CENSUS_AUDITED`: both exact source objects and full CSV streams verified and all conservation checks pass; all counts reported, even if the matched fraction is zero.
- `SOURCE_GATE_NOT_PASSED`: at least one source fails source identity/budget/schema/read prerequisites; report failure and any independently verified source identities, not partial join totals.
- `INSTRUMENT_FAILURE`: implementation or calculation resource failure; no empirical positive claim.

Before first original replay, run synthetic SQLite fixture tests with one-to-one, one-to-many, duplicate occurrence keys, cross-year/month/company nonmatches, leading zeroes, invalid keys, conservation checks, incorrect digest and code execution under `python -O`. Store original JSON report and its hash immutably in an isolated branch and an Actions artifact. The protocol commits alone **before** original D07 result. Subsequent debugging cannot be represented as part of an original blinded forecast.

## Excluded conclusions

No complete national/annual reporting population, semantic equivalence of codes across distributors, physically identified separate failures, actual outage-action correspondence, valid operator-time observations, live energized feeder graph, specific repair actions, measured algorithm/crew decision overhead, F2 link-repair outcome, greedy/lookahead causal effect, or new relational-persistence physical law is established by this linkage census.
